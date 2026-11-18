#!/usr/bin/env python3
"""Compose app icons from a keyed mascot bust (and optional badge).

  compose_app_icon.py --art bust.png --bg "#8E97FD" --out-dir assets/brand \
      [--badge badge.png] [--no-decor] [--bleed 70] [--art-width 0.86]

Writes:
  app-icon-1024.png            full-bleed, opaque (iOS / App Store / Expo "icon")
  app-icon-512.png             Google Play listing icon
  adaptive-icon-foreground.png transparent, content inside Android's 66% safe zone
  splash-icon.png              circular mark with transparent corners (light + dark splash)
  icon-preview.png             rounded/circle masks at 300/120/60/40 px for review
"""
import argparse
import os

from PIL import Image, ImageDraw, ImageFilter

S = 1024


def hex_rgb(value):
    value = value.lstrip("#")
    return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))


def arcs(img, cx, cy, radii, alpha):
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    for r in radii:
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(255, 255, 255, alpha))
    return Image.alpha_composite(img, overlay)


def place(canvas, art, width, cx, bottom):
    a = art.resize((width, int(art.height * width / art.width)), Image.LANCZOS)
    canvas.alpha_composite(a, (int(cx - width / 2), int(bottom - a.height)))


def badge_layer(canvas, badge, width, x, y, angle=-8):
    b = badge.resize((width, int(badge.height * width / badge.width)), Image.LANCZOS).rotate(angle, resample=Image.BICUBIC, expand=True)
    shadow = Image.new("RGBA", b.size, (16, 21, 74, 0))
    shadow.putalpha(b.getchannel("A").point(lambda v: int(v * 0.22)))
    canvas.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(10)), (x + 6, y + 14))
    canvas.alpha_composite(b, (x, y))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--art", required=True, help="transparent mascot bust (keyed)")
    ap.add_argument("--badge", help="optional transparent badge (e.g. calendar check)")
    ap.add_argument("--bg", default="#8E97FD")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--no-decor", action="store_true")
    ap.add_argument("--bleed", type=int, default=70, help="px the bust extends past the bottom edge")
    ap.add_argument("--art-width", type=float, default=0.86)
    args = ap.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)
    bg = hex_rgb(args.bg)
    art = Image.open(args.art).convert("RGBA")
    badge = Image.open(args.badge).convert("RGBA") if args.badge else None

    icon = Image.new("RGBA", (S, S), bg + (255,))
    if not args.no_decor:
        icon = arcs(icon, S // 2, int(S * 1.02), [int(S * 0.78), int(S * 0.62), int(S * 0.46)], 26)
        icon = arcs(icon, int(S * 0.9), int(S * 0.08), [int(S * 0.26)], 30)
    place(icon, art, int(S * args.art_width), S // 2, S + args.bleed)
    if badge:
        badge_layer(icon, badge, int(S * 0.27), int(S * 0.68), int(S * 0.60))
    icon = icon.convert("RGB")
    icon.save(os.path.join(args.out_dir, "app-icon-1024.png"), optimize=True)
    icon.resize((512, 512), Image.LANCZOS).save(os.path.join(args.out_dir, "app-icon-512.png"), optimize=True)

    fg = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    place(fg, art, int(S * 0.62), S // 2, S * 0.83)
    if badge:
        badge_layer(fg, badge, int(S * 0.19), int(S * 0.60), int(S * 0.56))
    fg.save(os.path.join(args.out_dir, "adaptive-icon-foreground.png"), optimize=True)

    disc = Image.new("RGBA", (S, S), bg + (255,))
    if not args.no_decor:
        disc = arcs(disc, S // 2, int(S * 1.02), [int(S * 0.62), int(S * 0.46)], 26)
    place(disc, art, int(S * 0.80), S // 2, S + 40)
    mask = Image.new("L", (S, S), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, S - 1, S - 1), fill=255)
    splash = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    splash.paste(disc, (0, 0), mask)
    splash.resize((512, 512), Image.LANCZOS).save(os.path.join(args.out_dir, "splash-icon.png"), optimize=True)

    preview = Image.new("RGB", (1260, 360), "#DDDDDD")
    for j, size in enumerate([300, 120, 60, 40]):
        tile = icon.resize((size, size), Image.LANCZOS)
        m = Image.new("L", (size, size), 0)
        ImageDraw.Draw(m).rounded_rectangle((0, 0, size - 1, size - 1), radius=int(size * 0.22), fill=255)
        preview.paste(tile, (20 + [0, 340, 480, 560][j], 30), m)
    adaptive = Image.new("RGBA", (300, 300), bg + (255,))
    adaptive.alpha_composite(fg.resize((300, 300), Image.LANCZOS))
    m = Image.new("L", (300, 300), 0)
    ImageDraw.Draw(m).ellipse((0, 0, 299, 299), fill=255)
    preview.paste(adaptive.convert("RGB"), (640, 30), m)
    for k, color in enumerate(["#FFFFFF", "#03174C"]):
        t = Image.new("RGB", (140, 140), color)
        sp = splash.resize((100, 100), Image.LANCZOS)
        t.paste(sp, (20, 20), sp)
        preview.paste(t, (980 + k * 140, 30))
    preview.save(os.path.join(args.out_dir, "icon-preview.png"))
    print("wrote app-icon-1024.png, app-icon-512.png, adaptive-icon-foreground.png, splash-icon.png, icon-preview.png to", args.out_dir)


if __name__ == "__main__":
    main()
