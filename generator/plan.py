#!/usr/bin/env python3
"""Buduje roczny plan postów BekaWpigułce: plan/RRRR-MM-DD-{poludnie|wieczor}.txt

Źródła:
  generator/zapas.json            — posty zapasu (zapas-04..50 idą na pierwsze terminy)
  generator/rok/RRRR-MM.json      — {"specials": {"RRRR-MM-DD/slot": tekst},
                                     "poludnie": [...], "wieczor": [...]}
Terminy: codziennie 12:00 (poludnie) i 19:00 (wieczor); daty w PRZERWY są pomijane.
Plik „POMIN” w planie oznacza świadomą przerwę (Publikator nic nie publikuje).

Użycie:
  python3 generator/plan.py --sprawdz      # tylko walidacja
  python3 generator/plan.py                # walidacja + zapis plan/*.txt + karty/plan/*.png
"""
import argparse, datetime as dt, glob, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
START = dt.date(2026, 10, 16)
END = dt.date(2027, 10, 15)
SLOTS = ("poludnie", "wieczor")
PRZERWY = {dt.date(2026, 11, 1)}           # Wszystkich Świętych — bez publikacji
ZAPAS_OD = 3                               # zapas-01..02 opublikowane, zapas-03 wyszedł 15.10 wieczorem
HASHTAG = "#BekaWpigułce"
ZAKAZANE = ["lidl", "biedronk", "polub", "udostępnij", "oznacz znajom", "oznacz kogoś", "#", "http", "kurw", "jeb"]


def sloty():
    d = START
    while d <= END:
        if d not in PRZERWY:
            for s in SLOTS:
                yield d, s
        d += dt.timedelta(days=1)


def lint(klucz, t):
    bledy = []
    hook = t.split("\n", 1)[0]
    if "?" not in t:
        bledy.append("brak pytania")
    if len(hook) > 110:
        bledy.append(f"hook {len(hook)} zn.")
    if len(t) > 700:
        bledy.append(f"za długi {len(t)} zn.")
    low = t.lower()
    for z in ZAKAZANE:
        if z in low:
            bledy.append(f"zakazane: {z}")
    if "\n\n\n" in t:
        bledy.append("potrójny enter")
    return [f"{klucz}: {b}" for b in bledy]


def zbuduj():
    zapas = json.load(open(os.path.join(ROOT, "generator/zapas.json"), encoding="utf-8"))
    kolejka_zapasu = [p["tekst"] for p in zapas if int(p["id"].split("-")[1]) > ZAPAS_OD]
    miesiace = {}
    for f in sorted(glob.glob(os.path.join(ROOT, "generator/rok/[0-9]*.json"))):
        miesiace[os.path.basename(f)[:7]] = json.load(open(f, encoding="utf-8"))

    plan, bledy, uzyte = {}, [], {m: {"poludnie": 0, "wieczor": 0} for m in miesiace}
    for d, s in sloty():
        klucz = f"{d.isoformat()}-{s}"
        if kolejka_zapasu:
            plan[klucz] = kolejka_zapasu.pop(0)
            continue
        m = d.strftime("%Y-%m")
        if m not in miesiace:
            bledy.append(f"{klucz}: brak pliku generator/rok/{m}.json")
            continue
        spec = miesiace[m].get("specials", {}).get(f"{d.isoformat()}/{s}")
        if spec:
            plan[klucz] = spec
            continue
        lista = miesiace[m].get(s, [])
        i = uzyte[m][s]
        if i >= len(lista):
            bledy.append(f"{klucz}: zabrakło postów w {m} / {s}")
            continue
        plan[klucz] = lista[i]
        uzyte[m][s] += 1

    for m, u in uzyte.items():
        for s in SLOTS:
            nadmiar = len(miesiace[m].get(s, [])) - u[s]
            if nadmiar > 0:
                bledy.append(f"{m}/{s}: {nadmiar} niewykorzystanych postów")
    for k, t in plan.items():
        bledy += lint(k, t)
    hooki = {}
    for k, t in plan.items():
        h = re.sub(r"\W+", " ", t.split("\n", 1)[0].lower()).strip()
        if h in hooki:
            bledy.append(f"{k}: duplikat hooka z {hooki[h]}")
        hooki[h] = k
    return plan, bledy


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--sprawdz", action="store_true")
    a.add_argument("--bez-kart", action="store_true")
    args = a.parse_args()
    plan, bledy = zbuduj()
    total = len(list(sloty()))
    print(f"terminy: {total}, wypełnione: {len(plan)}, błędy: {len(bledy)}")
    for b in bledy[:80]:
        print("  -", b)
    if args.sprawdz or bledy:
        sys.exit(1 if bledy else 0)

    out = os.path.join(ROOT, "plan")
    os.makedirs(out, exist_ok=True)
    for k, t in plan.items():
        with open(os.path.join(out, k + ".txt"), "w", encoding="utf-8") as f:
            f.write(t.strip() + "\n\n" + HASHTAG)
    for d in PRZERWY:
        for s in SLOTS:
            with open(os.path.join(out, f"{d.isoformat()}-{s}.txt"), "w", encoding="utf-8") as f:
                f.write("POMIN")
    print(f"zapisano {len(plan)} plików w plan/")
    if not args.bez_kart:
        sys.path.insert(0, os.path.join(ROOT, "generator"))
        import karta
        font = karta.find_font()
        kdir = os.path.join(ROOT, "karty", "plan")
        for k, t in plan.items():
            karta.render(t.split("\n", 1)[0].strip(), os.path.join(kdir, k + ".png"), font)
        print(f"wygenerowano {len(plan)} kart w karty/plan/")


if __name__ == "__main__":
    main()
