#!/usr/bin/env python3
"""Turn green-screen renders into transparent, trimmed PNGs.

Image models never produce a true #00FF00 background — the "green" drifts to a
different pastel per image — so the key color is sampled from each image's own
border and pixels are keyed by color distance. Semi-transparent edges are
un-mixed from the key color (no green fringe), and ground shadows that share the
key's hue direction are removed while teal/blue artwork is kept.

  chroma_key.py IN (file or dir) OUT_DIR [--max-size 900] [--quantize] [--keep-shadows]
                [--lo 28 --hi 80] [--pad 16] [--only name1,name2]

--quantize reduces to a 256-color palette (flat art: ~10x smaller, visually identical).
"""
import argparse
import os
import sys

import numpy as np
from PIL import Image


def key_image(path, lo, hi, keep_shadows, pad):
    rgb = np.asarray(Image.open(path).convert("RGB")).astype(np.float32)
    ring = np.concatenate(
        [rgb[:12].reshape(-1, 3), rgb[-12:].reshape(-1, 3), rgb[:, :12].reshape(-1, 3), rgb[:, -12:].reshape(-1, 3)]
    )
    key = np.median(ring, axis=0)
    dist = np.sqrt(((rgb - key) ** 2).sum(axis=-1))
    alpha = np.clip((dist - lo) / (hi - lo), 0.0, 1.0)

    # observed = a*fg + (1-a)*key  ->  fg = (observed - (1-a)*key) / a
    a3 = np.maximum(alpha, 1e-3)[..., None]
    fg = np.where(alpha[..., None] < 1, (rgb - (1 - a3) * key) / a3, rgb)

    if not keep_shadows:
        v = rgb - rgb.mean(axis=-1, keepdims=True)
        k = key - key.mean()
        cos = (v * k).sum(axis=-1) / (np.linalg.norm(v, axis=-1) * np.linalg.norm(k) + 1e-6)
        alpha = np.where((cos > 0.93) & (np.linalg.norm(v, axis=-1) > 12), 0.0, alpha)

    out = np.dstack([fg.clip(0, 255), alpha * 255]).clip(0, 255).astype(np.uint8)
    out[..., 3][out[..., 3] < 8] = 0
    im = Image.fromarray(out, "RGBA")
    bbox = im.getchannel("A").point(lambda a: 255 if a > 24 else 0).getbbox()
    if bbox:
        x0, y0, x1, y1 = bbox
        im = im.crop((max(0, x0 - pad), max(0, y0 - pad), min(im.width, x1 + pad), min(im.height, y1 + pad)))
    return im, tuple(int(c) for c in key)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input")
    ap.add_argument("out_dir")
    ap.add_argument("--max-size", type=int, default=900)
    ap.add_argument("--quantize", action="store_true")
    ap.add_argument("--keep-shadows", action="store_true")
    ap.add_argument("--lo", type=float, default=28.0, help="distance below which pixels are fully transparent")
    ap.add_argument("--hi", type=float, default=80.0, help="distance above which pixels are fully opaque")
    ap.add_argument("--pad", type=int, default=16)
    ap.add_argument("--only", help="comma-separated base names to process")
    args = ap.parse_args()

    if os.path.isdir(args.input):
        files = [os.path.join(args.input, f) for f in sorted(os.listdir(args.input)) if f.lower().endswith((".png", ".jpg", ".jpeg", ".webp"))]
    elif os.path.isfile(args.input):
        files = [args.input]
    else:
        sys.exit(f"not found: {args.input}")
    only = set(args.only.split(",")) if args.only else None
    os.makedirs(args.out_dir, exist_ok=True)

    for path in files:
        name = os.path.splitext(os.path.basename(path))[0]
        if only and name not in only:
            continue
        im, key = key_image(path, args.lo, args.hi, args.keep_shadows, args.pad)
        im.thumbnail((args.max_size, args.max_size), Image.LANCZOS)
        if args.quantize:
            im = im.quantize(colors=256, method=Image.Quantize.FASTOCTREE, dither=Image.Dither.NONE)
        dest = os.path.join(args.out_dir, name + ".png")
        im.save(dest, optimize=True)
        print(f"keyed {name} {im.size} key=rgb{key}")


if __name__ == "__main__":
    main()
