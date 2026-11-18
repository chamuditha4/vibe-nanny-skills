#!/usr/bin/env python3
"""Tile images into one preview so you can review many assets in a single Read.

  contact_sheet.py OUT.png IMG_OR_DIR [...] [--cols 6] [--tile 300] [--bg "#FFCF86,#03174C"] [--labels]

Transparent art is shown on every --bg color (one row per color), which is the
fastest way to spot green fringes or halos on light and dark grounds.
"""
import argparse
import os

from PIL import Image, ImageDraw


def collect(paths):
    files = []
    for p in paths:
        if os.path.isdir(p):
            files += [os.path.join(p, f) for f in sorted(os.listdir(p)) if f.lower().endswith((".png", ".jpg", ".jpeg", ".webp"))]
        else:
            files.append(p)
    return files


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("inputs", nargs="+")
    ap.add_argument("--cols", type=int, default=6)
    ap.add_argument("--tile", type=int, default=300)
    ap.add_argument("--bg", default="#FFFFFF")
    ap.add_argument("--labels", action="store_true")
    args = ap.parse_args()

    files = collect(args.inputs)
    bgs = [c.strip() for c in args.bg.split(",")]
    t, cols = args.tile, min(args.cols, max(1, len(files)))
    rows = (len(files) + cols - 1) // cols
    label_h = 18 if args.labels else 0
    band = t * len(bgs) + label_h
    sheet = Image.new("RGB", (cols * t, rows * band), "#BBBBBB")
    draw = ImageDraw.Draw(sheet)
    for i, path in enumerate(files):
        im = Image.open(path).convert("RGBA")
        im.thumbnail((t - 12, t - 12))
        x, y0 = (i % cols) * t, (i // cols) * band
        for j, bg in enumerate(bgs):
            tile = Image.new("RGBA", (t, t), bg)
            tile.alpha_composite(im, ((t - im.width) // 2, (t - im.height) // 2))
            sheet.paste(tile.convert("RGB"), (x, y0 + j * t))
        if args.labels:
            draw.text((x + 4, y0 + len(bgs) * t + 3), os.path.basename(path)[:40], fill="black")
    sheet.save(args.out)
    print("wrote", args.out, sheet.size)


if __name__ == "__main__":
    main()
