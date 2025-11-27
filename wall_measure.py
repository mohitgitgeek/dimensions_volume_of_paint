#!/usr/bin/env python3
"""
Simple CLI tool to estimate wall dimensions and paint required from images.

Notes:
- Absolute scaling requires either a known reference object (real-world length and its pixel length in the image)
  or a provided `--scale` value (meters per pixel) for the front view.
- The script attempts to locate the wall bounding box using simple edge/contour heuristics on the front image.
  For best accuracy provide a clean, roughly frontal image with visible wall edges.

Usage examples are in README.md
"""
from __future__ import annotations
import math
import argparse
from typing import Optional, Tuple

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Estimate wall dimensions and paint needed from images")
    p.add_argument("--front", required=True, help="Path to front view image (required)")
    p.add_argument("--top", required=False, help="Path to top view image (optional, helps depth)")
    p.add_argument("--side", required=False, help="Path to side view image (optional, helps depth)")
    scale = p.add_mutually_exclusive_group(required=False)
    scale.add_argument("--scale", type=float, help="Direct scale in meters per pixel for the front image (preferred)")
    scale.add_argument("--ref", nargs=2, metavar=("REAL_M", "PX"),
                       help="Provide reference real-world length (meters) and its pixel length in the front image: e.g. --ref 1.0 120")
    p.add_argument("--coverage", type=float, default=10.0,
                   help="Paint coverage in m^2 per litre (default: 10 m^2/L)")
    p.add_argument("--coats", type=float, default=2.0, help="Number of coats (default: 2)")
    p.add_argument("--no-round", dest="round_up", action="store_false",
                   help="Do not round liters up to whole litres (default is to round up)")
    return p.parse_args()


def load_image_cv(path: str):
    # Import locally to avoid failing module import at top-level if cv2 not installed
    import cv2
    img = cv2.imread(path)
    if img is None:
        raise FileNotFoundError(f"Cannot open image: {path}")
    return img


def find_wall_bbox_front(img) -> Tuple[int, int, int, int]:
    """Return bounding rectangle (x, y, w, h) of the detected largest wall-like contour.
    Uses simple Canny + contour area heuristic.
    """
    import cv2
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # blur then Canny
    gray = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(gray, 50, 150)
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        # fallback to whole image
        h, w = img.shape[:2]
        return 0, 0, w, h
    # pick contour with largest area
    c = max(contours, key=cv2.contourArea)
    x, y, w, h = cv2.boundingRect(c)
    return x, y, w, h


def px_to_meters(px: float, scale: Optional[float], ref: Optional[Tuple[float, float]]) -> float:
    """Convert pixels to meters using either direct scale (m per px) or reference (meters, px)."""
    if scale is not None:
        return px * scale
    if ref is not None:
        real_m, px_len = ref
        return px * (real_m / px_len)
    raise ValueError("Either scale or ref must be provided to convert pixels to meters")


def estimate_paint_litres(area_m2: float, coverage_m2_per_l: float, coats: float, round_up: bool = True) -> float:
    litres = (area_m2 * coats) / coverage_m2_per_l
    if round_up:
        return math.ceil(litres)
    return round(litres, 2)


def main():
    args = parse_args()
    # Prepare conversion inputs
    scale = args.scale
    ref = None
    if args.ref:
        real_m = float(args.ref[0])
        px_len = float(args.ref[1])
        ref = (real_m, px_len)

    # lazy-import cv2 to allow syntax checks without having opencv installed
    try:
        import cv2  # noqa: F401
    except Exception:
        print("ERROR: This tool requires OpenCV (cv2). Install with: pip install opencv-python")
        return

    front_img = load_image_cv(args.front)
    x, y, w_px, h_px = find_wall_bbox_front(front_img)

    # compute sizes
    try:
        width_m = px_to_meters(w_px, scale, ref)
        height_m = px_to_meters(h_px, scale, ref)
    except ValueError as e:
        print("ERROR:", e)
        print("Provide either --scale or --ref to convert pixels to meters.")
        return

    depth_m = None
    # optional: use top view width as depth
    if args.top:
        try:
            top_img = load_image_cv(args.top)
            _, _, top_w_px, top_h_px = find_wall_bbox_front(top_img)
            # assume top view's bounding width corresponds to wall depth in px
            depth_m = px_to_meters(top_w_px, scale, ref)
        except Exception as ex:
            print("Warning: couldn't measure depth from top image:", ex)

    area_m2 = width_m * height_m
    litres = estimate_paint_litres(area_m2, args.coverage, args.coats, args.round_up)

    print("Wall measurement results:")
    print(f" - Width (m): {width_m:.3f}")
    print(f" - Height (m): {height_m:.3f}")
    if depth_m is not None:
        print(f" - Depth (m, from top view): {depth_m:.3f}")
    print(f" - Area (m^2): {area_m2:.3f}")
    print(f" - Paint coverage: {args.coverage} m^2/L, Coats: {args.coats}")
    print(f" - Estimated paint required: {litres} L")

    print("\nNotes:")
    print(" - For accurate absolute sizes provide --scale (meters per pixel) or --ref REAL_M PX")
    print(" - The automatic detection is heuristic — for best results crop/present clear frontal images")


if __name__ == '__main__':
    main()
