#!/usr/bin/env python3
"""Buduje roczny plan postów BekaWpigułce: plan/RRRR-MM-DD-{poludnie|wieczor}.txt

Źródła:
  generator/zapas.json            — posty zapasu (zapas-04..50 idą na pierwsze terminy)
  generator/rok/RRRR-MM.json      — {"specials": {"RRRR-MM-DD/slot": tekst},
                                     "poludnie": [...], "wieczor": [...]}
  generator/interaktywne.json     — zagadki i quizy (wt./sob. zagadka, czw. quiz, 12:00);
                                     rozwiązanie dopisywane do kolejnego posta z 12:00
Terminy: codziennie 12:00 (poludnie) i 19:00 (wieczor); daty w PRZERWY są pomijane.
Pierwszeństwo: święto (specials) > zagadka/quiz > zapas > lista miesiąca.
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
INTERAKTYWNE = {1: "zagadka", 3: "quiz", 5: "zagadka"}   # dzień tygodnia (pon=0) → typ, slot 12:00
DNI = ["w poniedziałek", "we wtorek", "w środę", "w czwartek", "w piątek", "w sobotę", "w niedzielę"]
PRZYM_ZAGADKA = {1: "wtorkowej", 5: "sobotniej"}
ILUSTRACJE_ZAGADEK = ["🧩", "🤔", "🔍", "💡", "❓"]
ZAKAZANE = ["lidl", "biedronk", "polub", "udostępnij", "oznacz znajom", "oznacz kogoś", "#", "http", "kurw", "jeb"]


def sloty():
    d = START
    while d <= END:
        if d not in PRZERWY:
            for s in SLOTS:
                yield d, s
        d += dt.timedelta(days=1)


def lint(klucz, t, dlugosc=700):
    bledy = []
    hook = t.split("\n", 1)[0]
    if "?" not in t:
        bledy.append("brak pytania")
    if len(hook) > 110:
        bledy.append(f"hook {len(hook)} zn.")
    if len(t) > dlugosc:
        bledy.append(f"za długi {len(t)} zn.")
    low = t.lower()
    for z in ZAKAZANE:
        if z in low:
            bledy.append(f"zakazane: {z}")
    if "\n\n\n" in t:
        bledy.append("potrójny enter")
    return [f"{klucz}: {b}" for b in bledy]


def tekst_zagadki(z, kiedy):
    return (f"🧩 ZAGADKA DNIA\n\n{z['tekst']}\n\n"
            f"Znasz odpowiedź? Napisz w komentarzu, tylko nie podpowiadaj innym 😉 Rozwiązanie {kiedy} o 12:00.")


def tekst_quizu(q, kiedy):
    opcje = "\n".join(f"{l}) {o}" for l, o in zip("ABCD", q["opcje"]))
    return (f"🧠 QUIZ: {q['pytanie']}\n\n{opcje}\n\n"
            f"Która odpowiedź jest poprawna? Wpiszcie literę w komentarzu. Rozwiązanie {kiedy} o 12:00 👇")


def zbuduj():
    zapas = json.load(open(os.path.join(ROOT, "generator/zapas.json"), encoding="utf-8"))
    kolejka_zapasu = [p["tekst"] for p in zapas if int(p["id"].split("-")[1]) > ZAPAS_OD]
    bank = json.load(open(os.path.join(ROOT, "generator/interaktywne.json"), encoding="utf-8"))
    zagadki, quizy = list(bank["zagadki"]), list(bank["quizy"])
    miesiace = {}
    for f in sorted(glob.glob(os.path.join(ROOT, "generator/rok/[0-9]*.json"))):
        miesiace[os.path.basename(f)[:7]] = json.load(open(f, encoding="utf-8"))

    plan, typy, bledy, uwagi = {}, {}, [], []
    uzyte = {m: {"poludnie": 0, "wieczor": 0} for m in miesiace}
    interaktywne = []                                   # (data, typ, element)
    for d, s in sloty():
        klucz = f"{d.isoformat()}-{s}"
        m = d.strftime("%Y-%m")
        spec = miesiace.get(m, {}).get("specials", {}).get(f"{d.isoformat()}/{s}")
        if spec:
            plan[klucz], typy[klucz] = spec, {"typ": "post"}
            continue
        typ = INTERAKTYWNE.get(d.weekday()) if s == "poludnie" else None
        if typ:
            zrodlo = zagadki if typ == "zagadka" else quizy
            if not zrodlo:
                bledy.append(f"{klucz}: zabrakło pozycji typu {typ} w generator/interaktywne.json")
                continue
            el = zrodlo.pop(0)
            interaktywne.append((d, typ, el))
            plan[klucz], typy[klucz] = None, {"typ": typ, "el": el}   # tekst po wyznaczeniu terminu rozwiązania
            continue
        if kolejka_zapasu:
            plan[klucz], typy[klucz] = kolejka_zapasu.pop(0), {"typ": "post"}
            continue
        if m not in miesiace:
            bledy.append(f"{klucz}: brak pliku generator/rok/{m}.json")
            continue
        lista = miesiace[m].get(s, [])
        i = uzyte[m][s]
        if i >= len(lista):
            bledy.append(f"{klucz}: zabrakło postów w {m} / {s}")
            continue
        plan[klucz], typy[klucz] = lista[i], {"typ": "post"}
        uzyte[m][s] += 1

    # rozwiązanie zagadki/quizu → dopisek do najbliższego posta z 12:00
    for d, typ, el in interaktywne:
        klucz = f"{d.isoformat()}-poludnie"
        cel = d + dt.timedelta(days=1)
        while cel <= END and (cel in PRZERWY or typy.get(f"{cel.isoformat()}-poludnie", {}).get("typ") != "post"):
            cel += dt.timedelta(days=1)
        ckey = f"{cel.isoformat()}-poludnie"
        if cel > END or plan.get(ckey) is None:
            bledy.append(f"{klucz}: brak posta z 12:00 na rozwiązanie")
            continue
        jutro = (cel - d).days == 1
        kiedy = "jutro" if jutro else DNI[cel.weekday()]
        if typ == "zagadka":
            plan[klucz] = tekst_zagadki(el, kiedy)
            kto = "wczorajszej" if jutro else PRZYM_ZAGADKA.get(d.weekday(), "ostatniej")
            dopisek = f"🧩 Rozwiązanie {kto} zagadki: {el['odpowiedz']}. Kto zgadł? 😉"
        else:
            plan[klucz] = tekst_quizu(el, kiedy)
            kto = "Wczorajszy" if jutro else "Czwartkowy"
            poprawna = el["opcje"]["ABCD".index(el["poprawna"])]
            dopisek = f"🧠 {kto} quiz: poprawna odpowiedź to {el['poprawna']}) {poprawna}. Kto trafił? 😉"
        typy[klucz]["kiedy"] = kiedy
        plan[ckey] = plan[ckey].rstrip() + "\n\n" + dopisek

    for m, u in uzyte.items():
        for s in SLOTS:
            nadmiar = len(miesiace[m].get(s, [])) - u[s]
            if nadmiar > 0:
                uwagi.append(f"{m}/{s}: {nadmiar} postów w rezerwie (nie zmieściły się w planie)")
    uwagi.append(f"bank: zostało {len(zagadki)} zagadek i {len(quizy)} quizów")
    for k, t in plan.items():
        if t is None:
            continue
        bledy += lint(k, t, dlugosc=900 if "Rozwiązanie" in t or "quiz:" in t else 700)
    hooki = {}
    for k, t in plan.items():
        if t is None or typy[k]["typ"] != "post":
            continue
        h = re.sub(r"\W+", " ", t.split("\n", 1)[0].lower()).strip()
        if h in hooki:
            bledy.append(f"{k}: duplikat hooka z {hooki[h]}")
        hooki[h] = k
    return plan, typy, bledy, uwagi


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--sprawdz", action="store_true")
    a.add_argument("--bez-kart", action="store_true")
    args = a.parse_args()
    plan, typy, bledy, uwagi = zbuduj()
    total = len(list(sloty()))
    print(f"terminy: {total}, wypełnione: {len(plan)}, błędy: {len(bledy)}")
    for b in bledy[:80]:
        print("  -", b)
    for u in uwagi:
        print("  i", u)
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
        for i, (k, t) in enumerate(sorted(plan.items())):
            out_png, info = os.path.join(kdir, k + ".png"), typy[k]
            if info["typ"] == "zagadka":
                karta.render_zagadka(info["el"]["tekst"], out_png, font, f"Rozwiązanie {info['kiedy']} o 12:00",
                                     ILUSTRACJE_ZAGADEK[i % len(ILUSTRACJE_ZAGADEK)])
            elif info["typ"] == "quiz":
                karta.render_quiz(info["el"]["pytanie"], info["el"]["opcje"], out_png, font,
                                  f"Odpowiedź {info['kiedy']} o 12:00")
            else:
                bazowy = re.split(r"\n\n(?:🧩 Rozwiązanie|🧠 \w+ quiz:)", t)[0]   # bez dopisku z rozwiązaniem
                karta.render(t.split("\n", 1)[0].strip(), out_png, font, karta.wybierz_emoji(bazowy))
        print(f"wygenerowano {len(plan)} kart w karty/plan/")


if __name__ == "__main__":
    main()
