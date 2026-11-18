#!/usr/bin/env python3
"""Compose poster-style store screenshots from real app captures.

  compose_store_screenshots.py screenshots.config.json [--only 01-name.png]

Layout per shot: oversized headline (one phrase on a colored pill), subtitle,
a large tilted phone with status bar + Dynamic Island around a real capture,
decorative blobs, a brand mark top-right and a mascot peeking in from an edge.
All paths in the config are relative to the config file. See
templates/screenshots.config.example.json for every option.
"""
import argparse
import json
import os
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont


def hex_rgb(value):
    value = value.lstrip("#")
    return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))


class Composer:
    def __init__(self, cfg, base):
        self.cfg = cfg
        self.base = base
        self.W, self.H = cfg.get("size", [1242, 2688])
        fonts = cfg["fonts"]
        self.font_head = self.path(fonts["headline"])
        self.font_body = self.path(fonts["body"])
        self.body_weight = fonts.get("bodyWeight")
        self.themes = {k: {kk: hex_rgb(vv) for kk, vv in v.items()} for k, v in cfg["themes"].items()}
        self.phone_cfg = {"width": 860, "bezel": 34, "captureScale": 3, "statusBarTime": "9:41", "minTop": 860, **cfg.get("phone", {})}
        self.layout = {"marginX": 84, "headlineTop": 290, "headlineMaxWidth": 1080, "headlineStart": 150, "subtitleSize": 50, **cfg.get("layout", {})}

    def path(self, p):
        return p if os.path.isabs(p) else os.path.join(self.base, p)

    def font(self, file, size, weight=None):
        f = ImageFont.truetype(file, size)
        if weight:
            try:
                f.set_variation_by_axes([weight])
            except Exception:
                pass
        return f

    # ---------- text ----------
    def parse_lines(self, lines):
        parsed = []
        for line in lines:
            hl = line.startswith("*") and line.endswith("*") and len(line) > 1
            parsed.append((line.strip("*") if hl else line, hl))
        return parsed

    def headline(self, img, lines, theme):
        x, y = self.layout["marginX"], self.layout["headlineTop"]
        size = self.layout["headlineStart"]
        while size > 70:
            f = self.font(self.font_head, size)
            if max(f.getbbox(t)[2] + (70 if hl else 0) for t, hl in lines) <= self.layout["headlineMaxWidth"]:
                break
            size -= 4
        f = self.font(self.font_head, size)
        d = ImageDraw.Draw(img)
        line_h = int(size * 1.02)
        for text, hl in lines:
            if hl:
                bbox = f.getbbox(text)
                pad_x, pad_top = 34, int(size * 0.10)
                pill = Image.new("RGBA", (bbox[2] + pad_x * 2, line_h + pad_top), (0, 0, 0, 0))
                ImageDraw.Draw(pill).rounded_rectangle(
                    (0, pad_top, pill.width - 1, pill.height - 1), radius=int(size * 0.34), fill=theme["pill"] + (255,)
                )
                pill = pill.rotate(self.layout.get("pillTilt", -1.6), resample=Image.BICUBIC, expand=True)
                img.alpha_composite(pill, (x - pad_x + 6, y - int(size * 0.02)))
                d.text((x + 6, y), text, font=f, fill=theme["pillInk"])
                y += line_h + int(size * 0.16)
            else:
                d.text((x, y), text, font=f, fill=theme["ink"])
                y += line_h
        return y

    def subtitle(self, img, text, theme, y):
        if not text:
            return y
        f = self.font(self.font_body, self.layout["subtitleSize"], self.body_weight)
        d = ImageDraw.Draw(img)
        x, max_w = self.layout["marginX"] + 6, self.W - 2 * self.layout["marginX"] - 20
        words, line, lines = text.split(), "", []
        for word in words:
            trial = (line + " " + word).strip()
            if f.getbbox(trial)[2] > max_w and line:
                lines.append(line)
                line = word
            else:
                line = trial
        lines.append(line)
        for ln in lines:
            d.text((x, y), ln, font=f, fill=theme["sub"])
            y += int(self.layout["subtitleSize"] * 1.28)
        return y

    # ---------- decoration ----------
    def blobs(self, img, theme, variant):
        d = ImageDraw.Draw(img)
        c = theme.get("blob", theme["bg"])
        W, H = self.W, self.H
        if variant % 2:
            d.ellipse((-260, int(H * 0.56), int(W * 0.56), int(H * 0.92)), fill=c)
            d.ellipse((int(W * 0.66), int(H * 0.23), W + 260, int(H * 0.48)), fill=c)
        else:
            d.ellipse((int(W * 0.52), int(H * 0.52), W + 400, int(H * 0.89)), fill=c)
            d.ellipse((-300, int(H * 0.26), int(W * 0.29), int(H * 0.51)), fill=c)

    def brand(self, img, theme):
        b = self.cfg.get("brand")
        if not b:
            return
        f = self.font(self.font_head, b.get("size", 54))
        text = b.get("text", "")
        tw = f.getbbox(text)[2] if text else 0
        x_text = self.W - 80 - tw
        if b.get("icon"):
            size = int(b.get("size", 54) * 1.78)
            disc_color = hex_rgb(b.get("disc", "#8E97FD"))
            if disc_color == theme["bg"] and b.get("discAlt"):
                disc_color = hex_rgb(b["discAlt"])
            icon = Image.open(self.path(b["icon"])).convert("RGBA")
            icon.thumbnail((size - 6, size - 6), Image.LANCZOS)
            layer = Image.new("RGBA", (size, size), (0, 0, 0, 0))
            ImageDraw.Draw(layer).ellipse((0, 0, size - 1, size - 1), fill=disc_color + (255,))
            art = Image.new("RGBA", (size, size), (0, 0, 0, 0))
            art.alpha_composite(icon, ((size - icon.width) // 2, size - icon.height + 4))
            mask = Image.new("L", (size, size), 0)
            ImageDraw.Draw(mask).ellipse((0, 0, size - 1, size - 1), fill=255)
            art.putalpha(Image.composite(art.getchannel("A"), Image.new("L", (size, size), 0), mask))
            layer.alpha_composite(art)
            img.alpha_composite(layer, (x_text - size - 18, 128))
        if text:
            ImageDraw.Draw(img).text((x_text, 146), text, font=f, fill=theme["ink"])

    # ---------- phone ----------
    def status_bar(self, width, color, dark_text):
        s = self.phone_cfg["captureScale"]
        h = int(47 * s)
        sb = Image.new("RGBA", (width, h), color + (255,))
        d = ImageDraw.Draw(sb)
        ink = (20, 20, 30, 255) if dark_text else (255, 255, 255, 255)
        f = self.font(self.font_body, int(16.7 * s), 800)
        d.text((int(50 * s), int(14.7 * s)), self.phone_cfg["statusBarTime"], font=f, fill=ink)
        d.rounded_rectangle((width // 2 - int(63 * s), int(10 * s), width // 2 + int(63 * s), int(45 * s)), radius=int(18 * s), fill=(0, 0, 0, 255))
        bx = width - int(110 * s)
        for i, bar in enumerate([5, 8, 11, 13]):
            x0 = bx + int(i * 5.7 * s)
            d.rounded_rectangle((x0, int(32 * s) - int(bar * s), x0 + int(3.7 * s), int(32 * s)), radius=int(s), fill=ink)
        x0 = width - int(67 * s)
        d.rounded_rectangle((x0, int(19 * s), x0 + int(26 * s), int(32 * s)), radius=int(3.7 * s), outline=ink, width=max(2, int(1.3 * s)))
        d.rounded_rectangle((x0 + int(2.7 * s), int(22 * s), x0 + int(22 * s), int(29 * s)), radius=int(2 * s), fill=ink)
        return sb

    def phone(self, capture, trim_top=0):
        cap = Image.open(self.path(os.path.join(self.cfg["captureDir"], capture + ".png"))).convert("RGBA")
        if trim_top:
            fill = cap.getpixel((cap.width // 2, cap.height - 2))
            trimmed = Image.new("RGBA", cap.size, fill)
            trimmed.alpha_composite(cap.crop((0, trim_top, cap.width, cap.height)), (0, 0))
            cap = trimmed
        lum = lambda c: 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]
        top = cap.getpixel((6, 6))[:3]  # page background at the edge, not a card
        sb = self.status_bar(cap.width, top, lum(top) > 140)
        screen = Image.new("RGBA", (cap.width, cap.height + sb.height), (0, 0, 0, 255))
        screen.alpha_composite(sb, (0, 0))
        screen.alpha_composite(cap, (0, sb.height))
        bottom = cap.getpixel((cap.width // 2, cap.height - 3))[:3]
        s = self.phone_cfg["captureScale"]
        ImageDraw.Draw(screen).rounded_rectangle(
            (cap.width // 2 - int(67 * s), screen.height - int(10 * s), cap.width // 2 + int(67 * s), screen.height - int(5 * s)),
            radius=int(3 * s),
            fill=(20, 20, 30, 255) if lum(bottom) > 140 else (255, 255, 255, 230),
        )
        width, bezel = self.phone_cfg["width"], self.phone_cfg["bezel"]
        inner_w = width - bezel * 2
        screen = screen.resize((inner_w, int(screen.height * inner_w / screen.width)), Image.LANCZOS)
        radius = int(inner_w * 0.135)
        mask = Image.new("L", screen.size, 0)
        ImageDraw.Draw(mask).rounded_rectangle((0, 0, screen.width - 1, screen.height - 1), radius=radius, fill=255)
        body = Image.new("RGBA", (width, screen.height + bezel * 2), (0, 0, 0, 0))
        bd = ImageDraw.Draw(body)
        bd.rounded_rectangle((0, 0, body.width - 1, body.height - 1), radius=radius + bezel, fill=(24, 24, 30, 255))
        bd.rounded_rectangle((6, 6, body.width - 7, body.height - 7), radius=radius + bezel - 6, outline=(70, 72, 84, 255), width=4)
        body.paste(screen, (bezel, bezel), mask)
        full = Image.new("RGBA", (body.width + 16, body.height), (0, 0, 0, 0))
        fd = ImageDraw.Draw(full)
        for y0, y1 in [(330, 440), (480, 590)]:
            fd.rounded_rectangle((0, y0, 14, y1), radius=6, fill=(40, 40, 48, 255))
        fd.rounded_rectangle((body.width + 2, 420, body.width + 15, 600), radius=6, fill=(40, 40, 48, 255))
        full.alpha_composite(body, (8, 0))
        return full

    @staticmethod
    def shadowed(layer, offset=(0, 40), blur=46, alpha=0.32, color=(16, 21, 74)):
        sh = Image.new("RGBA", layer.size, color + (0,))
        sh.putalpha(layer.getchannel("A").point(lambda v: int(v * alpha)))
        pad = blur * 3
        canvas = Image.new("RGBA", (layer.width + pad * 2, layer.height + pad * 2), (0, 0, 0, 0))
        canvas.alpha_composite(sh, (pad + offset[0], pad + offset[1]))
        canvas = canvas.filter(ImageFilter.GaussianBlur(blur))
        canvas.alpha_composite(layer, (pad, pad))
        return canvas, pad

    def mascot(self, img, m):
        art = Image.open(self.path(m["image"])).convert("RGBA")
        if m.get("flip"):
            art = art.transpose(Image.FLIP_LEFT_RIGHT)
        height = m.get("height", 700)
        w = int(art.width * height / art.height)
        art = art.resize((w, height), Image.LANCZOS)
        layer, pad = self.shadowed(art, offset=(0, 18), blur=26, alpha=0.18)
        overhang = m.get("overhang", 150)
        left = -overhang if m.get("edge", "right") == "left" else self.W + overhang - w
        bottom = self.H + m.get("bottomOverhang", 20)
        img.alpha_composite(layer, (left - pad, bottom - height - pad))

    # ---------- shot ----------
    def render(self, shot, idx):
        theme = self.themes[shot["theme"]]
        img = Image.new("RGBA", (self.W, self.H), theme["bg"] + (255,))
        self.blobs(img, theme, idx)
        self.brand(img, theme)
        y = self.headline(img, self.parse_lines(shot["headline"]), theme)
        y = self.subtitle(img, shot.get("subtitle", ""), theme, y + 26)
        ph = self.phone(shot["capture"], shot.get("trimTop", 0)).rotate(shot.get("tilt", 0), resample=Image.BICUBIC, expand=True)
        layer, pad = self.shadowed(ph)
        top = max(y + 64, self.phone_cfg["minTop"])
        img.alpha_composite(layer, ((self.W - ph.width) // 2 + shot.get("shift", 0) - pad, top - pad))
        if shot.get("mascot"):
            self.mascot(img, shot["mascot"])
        return img.convert("RGB")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("config")
    ap.add_argument("--only", help="render just this output file name")
    args = ap.parse_args()
    base = os.path.dirname(os.path.abspath(args.config))
    with open(args.config) as fh:
        cfg = json.load(fh)
    comp = Composer(cfg, base)
    out_dir = comp.path(cfg.get("outDir", "store-screenshots"))
    os.makedirs(out_dir, exist_ok=True)

    thumbs = []
    for idx, shot in enumerate(cfg["shots"]):
        if args.only and shot["file"] != args.only:
            continue
        try:
            im = comp.render(shot, idx)
        except FileNotFoundError as err:
            sys.exit(f"{shot['file']}: missing file {err.filename}")
        im.save(os.path.join(out_dir, shot["file"]), optimize=True)
        thumbs.append(im.resize((comp.W // 4, comp.H // 4), Image.LANCZOS))
        print("wrote", shot["file"])

    if thumbs and not args.only:
        cols = min(4, len(thumbs))
        rows = (len(thumbs) + cols - 1) // cols
        tw, th = thumbs[0].size
        sheet = Image.new("RGB", (cols * (tw + 24) + 24, rows * (th + 24) + 24), (240, 240, 244))
        for i, t in enumerate(thumbs):
            sheet.paste(t, (24 + (i % cols) * (tw + 24), 24 + (i // cols) * (th + 24)))
        sheet.save(os.path.join(out_dir, "contact-sheet.png"), optimize=True)
        print("wrote contact-sheet.png")


if __name__ == "__main__":
    main()
