#!/usr/bin/env python3
"""Generator Rolek (Reels) BekaWpigułce — darmowy, lokalny (Pillow + ffmpeg).

Z tekstu posta robi pionowy film 1080x1920 (~12 s) w barwach marki:
  scena 1: ilustracja (emoji) + hook        — „zaczepka”, która zatrzymuje kciuk
  scena 2: puenta posta                     — nagroda za obejrzenie
  scena 3: pytanie + „Napisz w komentarzu”  — wezwanie do rozmowy
Na dole pasek postępu (ludzie oglądają do końca, gdy widzą, ile zostało).
Ścieżka dźwiękowa: cisza (bez problemów z prawami do muzyki).

Użycie:
  python3 generator/rolka.py plan/2026-10-16-wieczor.txt rolki/2026-10-16-wieczor.mp4
"""
import os
import re
import subprocess
import sys
import tempfile

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import karta  # noqa: E402

W, H = 1080, 1920
M = 90
CZASY = (4.0, 4.5, 3.5)          # długości scen w sekundach
PRZEJSCIE = 0.4


def podziel(tekst):
    """Zwraca (hook, puenta, pytanie, emoji) z treści posta z planu."""
    t = re.split(r"\n\n(?:🧩 Rozwiązanie|🧠 \w+ quiz:)", tekst)[0]
    t = t.replace("#BekaWpigułce", "").strip()
    akapity = [a.strip() for a in t.split("\n\n") if a.strip()]
    hook = akapity[0]
    pytanie = akapity[-1] if len(akapity) > 1 else ""
    puenta = akapity[-2] if len(akapity) >= 4 else (akapity[1] if len(akapity) == 3 else "")
    return hook, puenta, pytanie, karta.wybierz_emoji(t)


def _kadr(font_path, akcent=karta.YELLOW):
    img = Image.new("RGB", (W, H), karta.BG)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 22], fill=akcent)
    f = ImageFont.truetype(font_path, 44)
    d.ellipse([M, 150, M + 32, 182], fill=karta.RED)
    d.text((M + 52, 141), karta.BRAND, font=f, fill=karta.WHITE)
    return img, d


def _tekst(d, tekst, font_path, top, bottom, kolor, start=104):
    font, lines, lh = karta.fit(d, karta.czysc(tekst), font_path, W - 2 * M, bottom - top, start=start, stop=43)
    y = top + ((bottom - top) - lh * len(lines)) // 2
    for line in lines:
        d.text((M, y), line, font=font, fill=kolor)
        y += lh


def sceny(tekst, katalog, font_path):
    hook, puenta, pytanie, emoji = podziel(tekst)
    pliki = []
    # 1. hook + ilustracja
    img, d = _kadr(font_path)
    top = 330
    if emoji and karta._ilustracja(img, d, emoji, W // 2, 560, 330, (36, 33, 18)):
        top = 830
    _tekst(d, hook, font_path, top, H - 300, karta.YELLOW)
    pliki.append(img)
    # 2. puenta
    img, d = _kadr(font_path)
    _tekst(d, puenta or hook, font_path, 330, H - 300, karta.WHITE, start=96)
    pliki.append(img)
    # 3. pytanie + wezwanie
    img, d = _kadr(font_path, karta.RED)
    _tekst(d, pytanie or "A jak jest u Ciebie?", font_path, 330, H - 560, karta.YELLOW, start=96)
    f = ImageFont.truetype(font_path, 58)
    napis = "Napisz w komentarzu"
    szer = d.textlength(napis, font=f) + 120
    x0 = (W - szer) // 2
    d.rounded_rectangle([x0, H - 470, x0 + szer, H - 360], radius=55, fill=karta.RED)
    d.text((x0 + 60, H - 452), napis, font=f, fill=karta.WHITE)
    strzalka = karta.emoji_obraz("👇", 120)
    if strzalka:
        img.paste(strzalka, (W // 2 - strzalka.width // 2, H - 330), strzalka)
    pliki.append(img)
    sciezki = []
    for i, im in enumerate(pliki):
        p = os.path.join(katalog, f"s{i}.png")
        im.save(p)
        sciezki.append(p)
    return sciezki


def render(tekst, out_path, font_path=None):
    font_path = font_path or karta.find_font()
    calosc = sum(CZASY) - PRZEJSCIE * (len(CZASY) - 1)
    with tempfile.TemporaryDirectory() as tmp:
        s = sceny(tekst, tmp, font_path)
        wej = []
        for p, t in zip(s, CZASY):
            wej += ["-loop", "1", "-framerate", "30", "-t", f"{t}", "-i", p]
        off1 = CZASY[0] - PRZEJSCIE
        off2 = off1 + CZASY[1] - PRZEJSCIE
        filtr = (
            f"[0][1]xfade=transition=fade:duration={PRZEJSCIE}:offset={off1}[a];"
            f"[a][2]xfade=transition=fade:duration={PRZEJSCIE}:offset={off2}[b];"
            f"[b]drawbox=x=0:y={H - 18}:w='iw*t/{calosc:.2f}':h=18:color=0xFFD400:t=fill,format=yuv420p[v]"
        )
        os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
        cmd = ["ffmpeg", "-y", "-loglevel", "error", *wej,
               "-f", "lavfi", "-t", f"{calosc:.2f}", "-i", "anullsrc=r=44100:cl=stereo",
               "-filter_complex", filtr, "-map", "[v]", "-map", "3:a",
               "-c:v", "libx264", "-preset", "slow", "-crf", "30", "-r", "30",
               "-c:a", "aac", "-b:a", "32k", "-shortest", "-movflags", "+faststart", out_path]
        subprocess.run(cmd, check=True)
    return out_path


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    print(render(open(sys.argv[1], encoding="utf-8").read(), sys.argv[2]))
