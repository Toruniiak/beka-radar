#!/usr/bin/env python3
"""Generator kart graficznych BekaWpigułce (darmowy, lokalny, bez API).

Rysuje kartę 1080x1350 (format 4:5 — najwięcej miejsca w feedzie FB)
w barwach marki: tło #0E0E0E, hook żółty #FFD400, akcent #FF3B30.

Użycie:
  python3 generator/karta.py "Tekst hooka" wyjscie.png
  python3 generator/karta.py --zapas generator/zapas.json karty/

Wymaga tylko Pillow (pip install pillow) i fontu TTF z polskimi znakami
(szukany automatycznie: DejaVu Sans Bold / Liberation Sans Bold / Arial Bold,
albo podany przez --font).
"""
import argparse
import json
import os
import re
import sys

from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1350
MARGIN = 96
BG = (14, 14, 14)
YELLOW = (255, 212, 0)
RED = (255, 59, 48)
WHITE = (245, 245, 240)
MUTED = (150, 150, 150)
BRAND = "BekaWpigułce"

FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
    "/Library/Fonts/Arial Bold.ttf",
    "C:\\Windows\\Fonts\\arialbd.ttf",
]


def find_font(explicit=None):
    for path in ([explicit] if explicit else []) + FONT_CANDIDATES:
        if path and os.path.exists(path):
            return path
    sys.exit("Nie znaleziono fontu TTF z polskimi znakami — podaj --font ŚCIEŻKA")


def wrap(draw, text, font, max_width):
    """Łamie tekst na linie mieszczące się w max_width (zachowuje \\n)."""
    # polska typografia: jednoliterowe słowa (w, z, i, a, o, u) nie zostają na końcu linii
    text = re.sub(r"(?<!\S)([aiouwzAIOUWZ]) +", "\\1\u00a0", text)
    lines = []
    for para in text.split("\n"):
        words, line = [w for w in para.split(" ") if w], ""
        for word in words:
            test = (line + " " + word).strip()
            if draw.textlength(test, font=font) <= max_width:
                line = test
            else:
                if line:
                    lines.append(line)
                line = word
        lines.append(line)
    return lines


def fit(draw, text, font_path, max_width, max_height):
    """Największy rozmiar fontu, przy którym tekst mieści się w ramce."""
    for size in range(110, 39, -4):
        font = ImageFont.truetype(font_path, size)
        lines = wrap(draw, text, font, max_width)
        line_h = int(size * 1.22)
        widest = max(draw.textlength(l, font=font) for l in lines)
        if widest <= max_width and line_h * len(lines) <= max_height:
            return font, lines, line_h
    font = ImageFont.truetype(font_path, 40)
    return font, wrap(draw, text, font, max_width), int(40 * 1.22)


def render(hook, out_path, font_path):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    # górny pasek marki
    d.rectangle([0, 0, W, 18], fill=YELLOW)
    small = ImageFont.truetype(font_path, 34)
    d.ellipse([MARGIN, 92, MARGIN + 26, 118], fill=RED)
    d.text((MARGIN + 44, 86), BRAND, font=small, fill=WHITE)

    # hook — wyśrodkowany w pionie w obszarze treści
    top, bottom = 200, H - 200
    font, lines, line_h = fit(d, hook, font_path, W - 2 * MARGIN, bottom - top)
    y = top + ((bottom - top) - line_h * len(lines)) // 2
    for line in lines:
        d.text((MARGIN, y), line, font=font, fill=YELLOW)
        y += line_h

    # stopka: zachęta do komentarza + podpis
    foot = ImageFont.truetype(font_path, 36)
    d.line([MARGIN, H - 150, W - MARGIN, H - 150], fill=(46, 46, 46), width=3)
    d.text((MARGIN, H - 122), "A jak jest u Ciebie?", font=foot, fill=MUTED)
    tag = "#" + BRAND
    d.text((W - MARGIN - d.textlength(tag, font=foot), H - 122), tag, font=foot, fill=RED)

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    img.save(out_path, "PNG", optimize=True)
    return out_path


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("hook", nargs="?", help="tekst na kartę")
    p.add_argument("out", nargs="?", help="plik PNG lub (z --zapas) katalog")
    p.add_argument("--zapas", help="plik JSON z listą postów {id, tekst}; hook = 1. linia")
    p.add_argument("--font", help="ścieżka do fontu TTF")
    a = p.parse_args()
    font = find_font(a.font)

    if a.zapas:
        posts = json.load(open(a.zapas, encoding="utf-8"))
        outdir = a.out or "karty"
        for post in posts:
            hook = post["tekst"].split("\n", 1)[0].strip()
            path = render(hook, os.path.join(outdir, f"{post['id']}.png"), font)
            print(path)
        return
    if not (a.hook and a.out):
        p.error("podaj HOOK i OUT albo --zapas PLIK")
    print(render(a.hook, a.out, font))


if __name__ == "__main__":
    main()
