const formEl = document.getElementById('form');
const frontPreview = document.getElementById('frontPreview');
const overlayCanvas = document.getElementById('overlayCanvas');
const resultDiv = document.getElementById('result');

function hidePreview() {
  frontPreview.style.display = 'none';
  overlayCanvas.style.display = 'none';
}

function setCanvasSizeToImage() {
  overlayCanvas.width = frontPreview.naturalWidth;
  overlayCanvas.height = frontPreview.naturalHeight;
  overlayCanvas.style.width = frontPreview.width + 'px';
  overlayCanvas.style.height = frontPreview.height + 'px';
  overlayCanvas.style.left = frontPreview.offsetLeft + 'px';
  overlayCanvas.style.top = frontPreview.offsetTop + 'px';
  overlayCanvas.style.display = 'block';
}

document.querySelector('input[name="front"]').addEventListener('change', (ev) => {
  const file = ev.target.files[0];
  if (!file) { hidePreview(); return; }
  const url = URL.createObjectURL(file);
  frontPreview.onload = () => {
    frontPreview.style.display = 'block';
    // ensure canvas matches displayed image size
    setCanvasSizeToImage();
    URL.revokeObjectURL(url);
  };
  frontPreview.src = url;
});

formEl.addEventListener('submit', async (e) => {
  e.preventDefault();
  const form = e.target;
  const data = new FormData(form);

  resultDiv.textContent = 'Measuring...';

  try {
    const res = await fetch('/measure', { method: 'POST', body: data });
    const json = await res.json();
    if (!res.ok) {
      resultDiv.textContent = 'Error: ' + (json.error || res.statusText);
      return;
    }

    // show results
    let out = '';
    out += `Width (m): ${json.width_m}\n`;
    out += `Height (m): ${json.height_m}\n`;
    if (json.depth_m !== null) out += `Depth (m): ${json.depth_m}\n`;
    out += `Area (m^2): ${json.area_m2}\n`;
    out += `Estimated paint: ${json.litres} L\n`;
    resultDiv.textContent = out;

    // show AI result if present
    const aiCard = document.getElementById('aiCard');
    const aiResult = document.getElementById('aiResult');
    if (json.ai && json.ai.trim()) {
      aiCard.style.display = 'block';
      aiResult.textContent = json.ai;
    } else {
      aiCard.style.display = 'none';
      aiResult.textContent = '';
    }

    // draw bbox if present
    if (json.bbox && frontPreview.naturalWidth) {
      const bbox = json.bbox;
      // compute scale from original image px to displayed image px
      const scaleX = frontPreview.width / bbox.image_w_px;
      const scaleY = frontPreview.height / bbox.image_h_px;
      const sx = scaleX;
      const sy = scaleY;

      // position and size for drawing on overlay canvas CSS-sized to match displayed image
      overlayCanvas.width = bbox.image_w_px;
      overlayCanvas.height = bbox.image_h_px;
      overlayCanvas.style.width = frontPreview.width + 'px';
      overlayCanvas.style.height = frontPreview.height + 'px';

      const ctx = overlayCanvas.getContext('2d');
      // clear and draw
      ctx.clearRect(0, 0, overlayCanvas.width, overlayCanvas.height);
      ctx.lineWidth = Math.max(2, Math.round(2 / ((sx + sy) / 2)));
      ctx.strokeStyle = 'rgba(255,0,0,0.9)';
      ctx.fillStyle = 'rgba(255,0,0,0.2)';
      ctx.strokeRect(bbox.x_px, bbox.y_px, bbox.w_px, bbox.h_px);
      ctx.fillRect(bbox.x_px, bbox.y_px, bbox.w_px, bbox.h_px);
      overlayCanvas.style.display = 'block';
    }

  } catch (err) {
    resultDiv.textContent = 'Request failed: ' + err;
  }
});
