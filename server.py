from flask import Flask, request, jsonify, send_from_directory, render_template
import numpy as np
import cv2
import os
from typing import Optional, Tuple

import wall_measure as wm

# Optional OpenAI integration
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
OPENAI_MODEL = os.environ.get('OPENAI_MODEL', 'gpt-4o-mini')

def call_openai_summary(result: dict) -> Optional[str]:
    """Call OpenAI to get a concise summary/advice for the measurement.
    Returns the assistant text or None if OpenAI not configured.
    """
    if not OPENAI_API_KEY:
        return None
    try:
        import openai
        openai.api_key = OPENAI_API_KEY
        prompt = (
            "You are an expert building estimator. Provide a concise (3-6 lines) human-friendly summary of the wall measurement, "
            "and 3 short practical painting tips (bulleted).\n\n"
            f"Measurements: width_m={result.get('width_m')}, height_m={result.get('height_m')}, "
            f"area_m2={result.get('area_m2')}, depth_m={result.get('depth_m')}\n"
            f"Paint estimate: {result.get('litres')} L, coverage {result.get('coverage_m2_per_l')} m^2/L, coats {result.get('coats')}\n\n"
            "Output a friendly summary and short tips."
        )

        # Use ChatCompletion style
        resp = openai.ChatCompletion.create(
            model=OPENAI_MODEL,
            messages=[{"role": "system", "content": "You are a helpful construction assistant."},
                      {"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=300,
        )
        # Extract assistant reply text
        text = resp['choices'][0]['message']['content']
        return text
    except Exception as e:
        # Do not fail the measurement if AI call fails — return none
        return None

app = Flask(__name__, static_folder='static', template_folder='templates')


def read_image_file_storage(fs) -> np.ndarray:
    data = fs.read()
    arr = np.frombuffer(data, np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError('Uploaded image could not be decoded')
    return img


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/measure', methods=['POST'])
def measure():
    try:
        if 'front' not in request.files:
            return jsonify({'error': 'front image is required'}), 400

        front_fs = request.files['front']
        front_img = read_image_file_storage(front_fs)

        # detect bounding box
        x, y, w_px, h_px = wm.find_wall_bbox_front(front_img)
        front_h, front_w = front_img.shape[:2]

        # parse scale/ref
        scale = request.form.get('scale')
        ref_real = request.form.get('ref_real')
        ref_px = request.form.get('ref_px')
        ref = None
        if scale:
            scale_val = float(scale)
        else:
            scale_val = None
            if ref_real and ref_px:
                ref = (float(ref_real), float(ref_px))

        # compute meters
        try:
            width_m = wm.px_to_meters(w_px, scale_val, ref)
            height_m = wm.px_to_meters(h_px, scale_val, ref)
        except ValueError as e:
            return jsonify({'error': str(e)}), 400

        depth_m = None
        if 'top' in request.files and request.files['top'].filename:
            top_fs = request.files['top']
            try:
                top_img = read_image_file_storage(top_fs)
                _, _, top_w_px, _ = wm.find_wall_bbox_front(top_img)
                depth_m = wm.px_to_meters(top_w_px, scale_val, ref)
            except Exception as ex:
                # non-fatal
                depth_m = None

        area_m2 = width_m * height_m

        coverage = float(request.form.get('coverage', 10.0))
        coats = float(request.form.get('coats', 2.0))
        no_round = request.form.get('no_round', 'false').lower() in ('1', 'true', 'yes', 'on')

        litres = wm.estimate_paint_litres(area_m2, coverage, coats, not no_round)

        result = {
            'width_m': round(width_m, 3),
            'height_m': round(height_m, 3),
            'depth_m': round(depth_m, 3) if depth_m is not None else None,
            'area_m2': round(area_m2, 3),
            'coverage_m2_per_l': coverage,
            'coats': coats,
            'litres': litres,
            'bbox': {
                'x_px': int(x),
                'y_px': int(y),
                'w_px': int(w_px),
                'h_px': int(h_px),
                'image_w_px': int(front_w),
                'image_h_px': int(front_h),
            }
        }

        # If client requested AI summary, try to call OpenAI (optional)
        use_ai = request.form.get('use_ai', '').lower() in ('1', 'true', 'yes', 'on')
        if use_ai:
            ai_text = call_openai_summary(result)
            result['ai'] = ai_text
        else:
            result['ai'] = None
        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
