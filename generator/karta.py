#!/usr/bin/env python3
"""Generator kart graficznych BekaWpigułce (darmowy, lokalny, bez API).

Rysuje kartę 1080x1350 (format 4:5 — najwięcej miejsca w feedzie FB)
w barwach marki: tło #0E0E0E, hook żółty #FFD400, akcent #FF3B30.

Szablony:
  render()         — zwykły post: kolorowa ilustracja (emoji Noto) + hook
  render_quiz()    — QUIZ: pytanie + 4 kafelki odpowiedzi A–D
  render_zagadka() — ZAGADKA: treść zagadki + zapowiedź rozwiązania

Użycie:
  python3 generator/karta.py "Tekst hooka" wyjscie.png [--emoji 🚗]
  python3 generator/karta.py --zapas generator/zapas.json karty/

Wymaga tylko Pillow (pip install pillow) i fontu TTF z polskimi znakami
(szukany automatycznie: DejaVu Sans Bold / Liberation Sans Bold / Arial Bold,
albo podany przez --font). Ilustracje: font Noto Color Emoji (OFL) — gdy go
brak, karta powstaje bez ilustracji (nic się nie wywraca).
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
TILE = (32, 32, 32)
QUIZ_ACCENT = (64, 170, 255)
ZAGADKA_ACCENT = (186, 120, 255)
BRAND = "BekaWpigułce"

FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
    "/Library/Fonts/Arial Bold.ttf",
    "C:\\Windows\\Fonts\\arialbd.ttf",
]
EMOJI_FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf",
    "/usr/share/fonts/noto/NotoColorEmoji.ttf",
    "/usr/share/fonts/google-noto-emoji/NotoColorEmoji.ttf",
]

# emoji nie ma w DejaVu (rysowałyby się „kwadraty”) — z tekstu na karcie je usuwamy,
# a jako ilustrację rysujemy osobno fontem Noto Color Emoji
EMOJI = re.compile("[\U0001F000-\U0001FFFF\u2300-\u23FF\u2600-\u27BF\u2B00-\u2BFF\uFE0F\u200D]+")
EMOJI_1 = re.compile("[\U0001F300-\U0001FAFF\u2600-\u27BF\u2300-\u23FF]")
# emoji „reakcji” nic nie ilustrują — na karcie szukamy emoji tematycznego
OGOLNE = set("👇👆👉😂😅🤔😉👀🙂😄🤣😁😆🙃😎🤷😏😬🙈💬😊😃🥲😜🤭🫣😮😱🤯🥹❤")


def find_font(explicit=None):
    for path in ([explicit] if explicit else []) + FONT_CANDIDATES:
        if path and os.path.exists(path):
            return path
    sys.exit("Nie znaleziono fontu TTF z polskimi znakami — podaj --font ŚCIEŻKA")


def find_emoji_font():
    for path in EMOJI_FONT_CANDIDATES:
        if os.path.exists(path):
            return path
    return None


def wybierz_emoji(tekst):
    """Pierwsze tematyczne emoji z treści posta (np. 🚗, ☕) albo None."""
    for e in EMOJI_1.findall(tekst):
        if e not in OGOLNE:
            return e
    return None


def emoji_obraz(znak, rozmiar):
    """Kolorowe emoji jako obraz RGBA o boku `rozmiar` (None, gdy brak fontu/glifu)."""
    path = find_emoji_font()
    if not path or not znak:
        return None
    font = ImageFont.truetype(path, 109)          # Noto Color Emoji ma bitmapy tylko 109 px
    im = Image.new("RGBA", (160, 160), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((8, 8), znak, font=font, embedded_color=True)
    box = im.getbbox()
    if not box:
        return None
    im = im.crop(box)
    skala = rozmiar / max(im.size)
    return im.resize((max(1, int(im.width * skala)), max(1, int(im.height * skala))), Image.LANCZOS)


def czysc(tekst):
    return re.sub(r"[ \t]{2,}", " ", EMOJI.sub("", tekst)).strip()


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


def fit(draw, text, font_path, max_width, max_height, start=110, stop=39):
    """Największy rozmiar fontu, przy którym tekst mieści się w ramce."""
    for size in range(start, stop, -4):
        font = ImageFont.truetype(font_path, size)
        lines = wrap(draw, text, font, max_width)
        line_h = int(size * 1.22)
        widest = max(draw.textlength(l, font=font) for l in lines)
        if widest <= max_width and line_h * len(lines) <= max_height:
            return font, lines, line_h
    size = stop + 1
    font = ImageFont.truetype(font_path, size)
    return font, wrap(draw, text, font, max_width), int(size * 1.22)


def _tlo(font_path, akcent=YELLOW):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 18], fill=akcent)
    small = ImageFont.truetype(font_path, 34)
    d.ellipse([MARGIN, 92, MARGIN + 26, 118], fill=RED)
    d.text((MARGIN + 44, 86), BRAND, font=small, fill=WHITE)
    return img, d


def _stopka(d, font_path, lewa, kolor_lewej=MUTED):
    foot = ImageFont.truetype(font_path, 36)
    d.line([MARGIN, H - 150, W - MARGIN, H - 150], fill=(46, 46, 46), width=3)
    d.text((MARGIN, H - 122), lewa, font=foot, fill=kolor_lewej)
    tag = "#" + BRAND
    d.text((W - MARGIN - d.textlength(tag, font=foot), H - 122), tag, font=foot, fill=RED)


def _plakietka(d, font_path, napis, akcent, y=160):
    f = ImageFont.truetype(font_path, 40)
    w = d.textlength(napis, font=f)
    d.rounded_rectangle([MARGIN, y, MARGIN + w + 56, y + 72], radius=36, fill=akcent)
    d.text((MARGIN + 28, y + 13), napis, font=f, fill=BG)
    return y + 72


def _ilustracja(img, d, znak, cx, cy, rozmiar, poswiata):
    em = emoji_obraz(znak, rozmiar)
    if not em:
        return False
    r = int(rozmiar * 0.78)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=poswiata)
    img.paste(em, (cx - em.width // 2, cy - em.height // 2), em)
    return True


def _zapisz(img, out_path):
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    img.save(out_path, "PNG", optimize=True)
    return out_path


def render(hook, out_path, font_path, ilustracja=None):
    """Zwykły post. `ilustracja` — emoji tematyczne (np. wybierz_emoji(tekst_posta))."""
    hook = czysc(hook)
    img, d = _tlo(font_path)
    top, bottom = 200, H - 200
    if ilustracja and _ilustracja(img, d, ilustracja, W // 2, 370, 250, (36, 33, 18)):
        top = 590
    font, lines, line_h = fit(d, hook, font_path, W - 2 * MARGIN, bottom - top,
                              start=110 if top == 200 else 84)
    y = top + ((bottom - top) - line_h * len(lines)) // 2
    for line in lines:
        d.text((MARGIN, y), line, font=font, fill=YELLOW)
        y += line_h
    _stopka(d, font_path, "A jak jest u Ciebie?")
    return _zapisz(img, out_path)


def render_quiz(pytanie, opcje, out_path, font_path, zapowiedz="Odpowiedź jutro o 12:00"):
    """QUIZ: pytanie + 4 kafelki A–D (bez zaznaczania poprawnej — to ma być zagadka)."""
    img, d = _tlo(font_path, QUIZ_ACCENT)
    y0 = _plakietka(d, font_path, "QUIZ", QUIZ_ACCENT)
    _ilustracja(img, d, "🧠", W - MARGIN - 70, 196, 110, (16, 34, 52))
    kafel_h, odstep = 118, 24
    dol_pytania = H - 190 - 4 * kafel_h - 3 * odstep - 50
    font, lines, line_h = fit(d, czysc(pytanie), font_path, W - 2 * MARGIN,
                              dol_pytania - (y0 + 40), start=76, stop=39)
    y = y0 + 40 + ((dol_pytania - (y0 + 40)) - line_h * len(lines)) // 2
    for line in lines:
        d.text((MARGIN, y), line, font=font, fill=WHITE)
        y += line_h
    y = dol_pytania + 50
    lit_f = ImageFont.truetype(font_path, 46)
    for litera, tekst in zip("ABCD", opcje):
        d.rounded_rectangle([MARGIN, y, W - MARGIN, y + kafel_h], radius=28, fill=TILE)
        cx, cy = MARGIN + 62, y + kafel_h // 2
        d.ellipse([cx - 38, cy - 38, cx + 38, cy + 38], fill=QUIZ_ACCENT)
        d.text((cx - d.textlength(litera, font=lit_f) / 2, cy - 28), litera, font=lit_f, fill=BG)
        of, ol, olh = fit(d, czysc(tekst), font_path, W - 2 * MARGIN - 150, kafel_h - 20, start=48, stop=27)
        ty = y + (kafel_h - olh * len(ol)) // 2
        for l in ol:
            d.text((MARGIN + 124, ty), l, font=of, fill=YELLOW)
            ty += olh
        y += kafel_h + odstep
    _stopka(d, font_path, zapowiedz, QUIZ_ACCENT)
    return _zapisz(img, out_path)


def render_zagadka(tekst, out_path, font_path, zapowiedz="Rozwiązanie jutro o 12:00", ilustracja="🧩"):
    """ZAGADKA: treść + ilustracja + zapowiedź rozwiązania w stopce."""
    img, d = _tlo(font_path, ZAGADKA_ACCENT)
    y0 = _plakietka(d, font_path, "ZAGADKA", ZAGADKA_ACCENT)
    _ilustracja(img, d, ilustracja or "🧩", W // 2, y0 + 190, 200, (34, 24, 48))
    top, bottom = y0 + 360, H - 200
    font, lines, line_h = fit(d, czysc(tekst), font_path, W - 2 * MARGIN, bottom - top, start=80, stop=39)
    y = top + ((bottom - top) - line_h * len(lines)) // 2
    for line in lines:
        d.text((MARGIN, y), line, font=font, fill=WHITE)
        y += line_h
    _stopka(d, font_path, zapowiedz, ZAGADKA_ACCENT)
    return _zapisz(img, out_path)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("hook", nargs="?", help="tekst na kartę")
    p.add_argument("out", nargs="?", help="plik PNG lub (z --zapas) katalog")
    p.add_argument("--zapas", help="plik JSON z listą postów {id, tekst}; hook = 1. linia")
    p.add_argument("--emoji", help="emoji-ilustracja dla pojedynczej karty")
    p.add_argument("--font", help="ścieżka do fontu TTF")
    a = p.parse_args()
    font = find_font(a.font)

    if a.zapas:
        posts = json.load(open(a.zapas, encoding="utf-8"))
        outdir = a.out or "karty"
        for post in posts:
            hook = post["tekst"].split("\n", 1)[0].strip()
            path = render(hook, os.path.join(outdir, f"{post['id']}.png"), font, wybierz_emoji(post["tekst"]))
            print(path)
        return
    if not (a.hook and a.out):
        p.error("podaj HOOK i OUT albo --zapas PLIK")
    print(render(a.hook, a.out, font, a.emoji))


if __name__ == "__main__":
    main()
