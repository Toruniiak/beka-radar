# Automatyzacja BekaWpigułce (Make.com) — darmowa i odporna na awarie

Pipeline postów na fanpage **BekaWpigułce** (Page ID `1282869891751448`).
Scenariusze żyją w Make (team „My Team” `1978767`, strefa `eu1.make.com`);
ten folder trzyma ich kopie i dokumentację, żeby zmiany były wersjonowane.

```
Google News RSS (codzienność)    ┌──────────────┐  czeka      ┌──────────────────┐
 pogoda/ceny/PKP/urlop/remont ─▶ │ Beka Fabryka │ ──────────▶ │  Beka Kolejka    │
                                 │ 10:00, AI    │  odrzucony  │  (data store     │
                                 └──────────────┘ ─(log)────▶ │   145060)        │
 generator/karta.py + zapas.json ─────────────────  zapas ──▶ │                  │
                                                              └────────┬─────────┘
                    ┌─────────────────────────────────────────────────┘
                    ▼ 18:00
         ┌───────────────────┐  świeży „czeka” (≤3 dni)?
         │ Beka Publikator   │──tak──▶ grafika AI OK? ──tak──▶ post ze zdjęciem
         │                   │                        └─nie──▶ post tekstowy
         │                   │──nie──▶ najstarszy „zapas” ──▶ post z kartą marki
         └───────────────────┘          (karta z GitHuba; gdy brak → post tekstowy)
                    każdy opublikowany rekord → status „opublikowane”
```

**Efekt: 1 post dziennie, nawet gdy darmowe AI nie działa.** Nic nie kosztuje:
Make (plan darmowy), Pollinations (anonimowo), GitHub (publiczne repo), lokalny generator kart.

| Element | Gdzie | Plik |
|---|---|---|
| Beka Fabryka (ID 6508676) — wyłączona | Make | `fabryka.json` |
| Beka Publikator wieczór (ID 6510968), 19:00 | Make | `publikator.json` |
| Beka Publikator południe (ID 7971251), 12:00 | Make | `publikator-poludnie.json` |
| Generator kart graficznych (Python + Pillow) | repo | `../generator/karta.py` |
| Zapas oryginalnych postów | repo + data store (status `zapas`) | `../generator/zapas.json` |
| Gotowe karty | repo (raw.githubusercontent, link przypięty do commita) | `../karty/*.png` |
| Kopie sprzed naprawy | repo | `backup/*-2026-10-14.json` |

## Statusy w kolejce (data store „Beka Kolejka”)

| status | znaczenie |
|---|---|
| `czeka` | świeży post AI, przeszedł strażnika jakości |
| `zapas` | post z banku evergreen (publikowany, gdy brak świeżego AI) |
| `opublikowane` | już wrzucony na FB |
| `odrzucony` | log: odpowiedź AI, którą strażnik odrzucił (z kodem HTTP) — do podglądu |

## Generator kart — użycie

```bash
pip install pillow
python3 generator/karta.py "Hook posta" karta.png             # jedna karta
python3 generator/karta.py --zapas generator/zapas.json karty  # cały zapas
```
Karta 1080×1350 (4:5), tło `#0E0E0E`, hook żółty `#FFD400`, akcent `#FF3B30`,
auto-dopasowanie rozmiaru, polska typografia (bez „wiszących” spójników).

**Dodawanie nowych postów do zapasu:** dopisz wpis do `generator/zapas.json`
(1. linia = hook na kartę), wygeneruj karty, commit + push, potem dodaj rekord
do data store ze statusem `zapas`, `url_grafiki` =
`https://raw.githubusercontent.com/Toruniiak/beka-radar/<SHA commita>/karty/<id>.png`
i `publikuj_o` późniejszym niż ostatni zapas (Publikator bierze najstarszy).

## Naprawy 2026-10-14

**Fabryka** (od 13.09 padała codziennie, a wcześniej „udane” przebiegi nic nie dawały):
- błąd `Function 'random' not found` → seed z `formatDate(now; "X")`;
- **główna przyczyna pustej kolejki:** model `openai` w Pollinations zwraca JSON
  `{"role","reasoning","content"}` zamiast tekstu → strażnik odrzucał wszystko.
  Teraz `parseResponse: true` + moduł `util:ComposeTransformer` (id 8) wyciąga `content`;
- źródło tematów: wyszukiwanie codziennych tematów z ostatniej doby zamiast czołówki newsów;
- nowy prompt pod komentarze (hook ≤ 80 znaków, akapity, puenta, otwarte pytanie;
  zakaz polityki, nazwisk, wulgaryzmów i engagement baitu);
- strażnik jakości + router z logiem odrzuceń; stały hashtag `#BekaWpigułce`.

**Publikator** (nigdy się nie uruchomił):
- uzupełnione puste `page_id`; najświeższy post z 3 dni zamiast najstarszego;
- grafikę pobiera Make i wysyła jako plik; gdy się nie pobierze → post tekstowy;
- fallback na zapas, gdy brak świeżego posta AI;
- **błąd od początku istnienia scenariusza:** moduł kolejki zwraca pola w obiekcie `data`
  (`{{1.data.tekst_posta}}`, `{{1.data.url_grafiki}}`), a scenariusz mapował `{{1.tekst_posta}}`
  → pusty URL → `BundleValidationError`. Poprawione;
- filtr rozgałęzienia `ifempty(1.key; "BRAK")` (pusty wynik wyszukiwania daje pusty `key`, nie brak pola);
- połączenie „Facebook — BekaWpigułce” (8898172) działa mimo daty `expire` 28.09
  (sprawdzone RPC `Pages`).
- **Test na żywo 2026-10-14 22:58:** opublikowany `zapas-01` z kartą (post `1282869891751448_1549135587255224`).

## Znane ograniczenia

- Generator tekstu AI (Pollinations, model `openai`) w teście 14.10 zwracał JSON bez pola `content`
  (tylko `reasoning`) → posty AI trafiają do `odrzucony`; publikacja idzie z zapasu.
- Pollinations (anonimowo) nie daje gwarancji: grafika AI może zwracać 401 —
  wtedy post AI idzie jako tekstowy (świadomie: stabilność > obrazek).
- Zapas starcza na ~21 dni bez AI; dopisuj nowe posty co jakiś czas.
- Plan darmowy Make: ~1000 operacji/mies.; Fabryka ≈ 16 op./dzień, Publikator ≈ 5 op./dzień.

## Zasady treści (dla automatu i postów ręcznych)

1. **Regularność > ilość**: 1–2 posty dziennie, nigdy serie po kilka naraz.
2. **Każdy post kończy się pytaniem**, na które da się odpowiedzieć własną historią.
   Odpowiadaj na komentarze w pierwszej godzinie — to najmocniejszy sygnał dla algorytmu.
3. **Bez engagement baitu** („polub jeśli”, „udostępnij”, „oznacz kogoś”).
4. **Oryginalne treści** — Beka Radar służy do łapania TEMATÓW, nie do kopiowania memów.
5. **Jeden hashtag marki**: `#BekaWpigułce` (+ maks. 2–3 tematyczne przy postach ręcznych).
6. **Bez polityki, tragedii i wulgaryzmów seksualnych**.
7. Zagadki: odpowiedź publikuj obiecanego dnia.
8. Filmiki/memy też z podpisem i pytaniem — nie samo „🤷”.

## Przywracanie kopii

W Make: scenariusz → `…` → Import Blueprint → wklej zawartość pola `blueprint`
z pliku w `backup/`. Albo przez API/MCP `scenarios_update` z tym blueprintem.


## Stan na 2026-10-15 (wersja produkcyjna) — plan roczny, 2 posty dziennie

**Publikacja (aktywne 2 scenariusze — limit planu Free):**

| Scenariusz | Godzina | Co robi |
|---|---|---|
| Beka Publikator — południe (ID 7971251) | 12:00 | `plan/RRRR-MM-DD-poludnie.txt` + `karty/plan/…png` → post ze zdjęciem (bez karty → tekstowy) |
| Beka Publikator — wieczór (ID 6510968) | 19:00 | zatwierdzony post AI (`czeka`, ≤3 dni) > `plan/…-wieczor.txt` + karta > gdy brak pliku planu: najstarszy `zapas` |
| Beka Fabryka (ID 6508676) | — | **wyłączona** (limit 2 aktywnych scenariuszy; AI i tak pisało nierówno) |

- Pliki planu czyta Make z `raw.githubusercontent.com/Toruniiak/beka-radar/ccr-8750d6fc-oi48wv/…`
  — **gałąź `ccr-8750d6fc-oi48wv` musi istnieć** (nie usuwać po scaleniu PR-a, albo zmienić URL w obu scenariuszach).
- Plik `POMIN` = świadoma przerwa (1.11.2026 — Wszystkich Świętych).
- **Blokada duplikatów:** przed publikacją scenariusz zapisuje w kolejce rekord `plan-RRRR-MM-DD-slot`
  (status `plan`); gdy taki rekord już jest, kolejne uruchomienie tego dnia nic nie publikuje (koszt: 1 operacja).
- Rekordy `zapas-04…50` mają status `w_planie` (są już w plikach planu, żeby awaryjna ścieżka ich nie powtórzyła);
  wyjątek: `zapas-44` został `zapas` (zmiana odrzucona w oknie zgody) — przy awarii GitHuba może wyjść drugi raz.
- Koszt: ~6 operacji / post → ~360 operacji / miesiąc (limit Free: 1000).

**Treść (generator/plan.py, 728 terminów 16.10.2026 – 15.10.2027):**
- święta i okazje (`generator/rok/RRRR-MM.json` → `specials`) mają pierwszeństwo;
- **wtorek i sobota 12:00 — ZAGADKA**, **czwartek 12:00 — QUIZ A/B/C/D** (`generator/interaktywne.json`,
  101 zagadek + 50 quizów); rozwiązanie jest dopisywane na końcu najbliższego posta z 12:00
  („🧩 Rozwiązanie wczorajszej zagadki: …”);
- dalej zapas (`generator/zapas.json`), potem listy miesięcy; nadmiar zostaje w plikach jako rezerwa.

**Grafiki (generator/karta.py, darmowe, lokalne):** Pillow + DejaVu Sans Bold + **Noto Color Emoji** (OFL):
- post — kolorowa ilustracja z tematycznego emoji posta (🚗, ☕, 🎄 …) + hook;
- QUIZ — niebieska plakietka, pytanie i 4 kafelki A–D;
- ZAGADKA — fioletowa plakietka, ilustracja, treść i „Rozwiązanie jutro o 12:00”.

```bash
python3 generator/plan.py --sprawdz   # walidacja (pytanie w każdym poście, długość, zakazane słowa, duplikaty)
python3 generator/plan.py             # zapis plan/*.txt + karty/plan/*.png (≈1,5 min)
```
Zmiana treści = edycja plików w `generator/`, ponowne uruchomienie, commit + push na gałąź — Make
pobiera pliki w dniu publikacji, więc nie trzeba niczego zmieniać w scenariuszach.

### Ręczne sterowanie
- opublikuj propozycję AI: w kolejce zmień `status` na `czeka` (wyjdzie o 19:00 zamiast posta z planu);
- wstrzymaj konkretny termin: podmień treść pliku `plan/RRRR-MM-DD-slot.txt` na `POMIN` i wypchnij;
- awaryjnie: wyłącz scenariusz w Make (Scenarios → przełącznik).
