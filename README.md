# Wall Measurement & Paint Estimator

This small CLI tool estimates wall dimensions (width, height, optional depth) from images and calculates how much paint you need.

Requirements
- Python 3.8+
- Install dependencies:

```powershell
pip install -r requirements.txt
```

Quick usage

- If you know the scale (meters per pixel) for the front image:

```powershell
python wall_measure.py --front path\to\front.jpg --scale 0.005
```

- Or provide a reference object in the front image: real-world length and pixel length:

```powershell
python wall_measure.py --front front.jpg --ref 1.0 120
```

Options
- `--top` / `--side`: optional views to help estimate depth.
- `--coverage`: m^2 per litre (default 10).
- `--coats`: number of coats (default 2).

Notes
- Absolute sizes require scale information. The automatic bounding detection is heuristic — for best results provide clear frontal images or supply reference scale.
