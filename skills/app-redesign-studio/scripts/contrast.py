#!/usr/bin/env python3
"""WCAG 2.x contrast checker for palette decisions.

  contrast.py "#FFFFFF on #8E97FD" "#3F414E on #FFC97E" ...
  contrast.py --suggest "#FFFFFF" "#8E97FD"   # darken/lighten bg until AA 4.5:1

Prints the ratio and AA / AA-large verdicts. UI kits often use pastel buttons
with white text that fail AA; use --suggest to find the nearest passing shade.
"""
import sys


def lum(hex_color):
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i : i + 2], 16) / 255 for i in (0, 2, 4))
    f = lambda c: c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)


def ratio(a, b):
    x, y = sorted([lum(a), lum(b)], reverse=True)
    return (x + 0.05) / (y + 0.05)


def shade(hex_color, factor):
    h = hex_color.lstrip("#")
    rgb = [int(h[i : i + 2], 16) for i in (0, 2, 4)]
    if factor < 1:
        rgb = [round(c * factor) for c in rgb]
    else:
        rgb = [round(c + (255 - c) * (factor - 1)) for c in rgb]
    return "#" + "".join(f"{max(0, min(255, c)):02X}" for c in rgb)


def main(argv):
    if not argv:
        print(__doc__)
        return
    if argv[0] == "--suggest" and len(argv) == 3:
        fg, bg = argv[1], argv[2]
        darker = lum(fg) > lum(bg)
        for step in range(0, 101):
            factor = 1 - step / 100 if darker else 1 + step / 100
            cand = shade(bg, factor)
            if ratio(fg, cand) >= 4.5:
                print(f"{fg} on {cand}: {ratio(fg, cand):.2f} (AA) — adjusted from {bg}")
                return
        print("no passing shade found")
        return
    for pair in argv:
        fg, _, bg = pair.partition(" on ")
        r = ratio(fg.strip(), bg.strip())
        verdict = "AA" if r >= 4.5 else "AA-large only (>=18.66px bold / 24px)" if r >= 3 else "FAIL"
        print(f"{fg.strip()} on {bg.strip()}: {r:.2f}  {verdict}")


if __name__ == "__main__":
    main(sys.argv[1:])
