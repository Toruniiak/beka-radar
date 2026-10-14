# Automatyzacja BekaWpigułce (Make.com)

Pipeline postów na fanpage **BekaWpigułce** (Page ID `1282869891751448`).
Scenariusze żyją w Make (team „My Team” `1978767`, strefa `eu1.make.com`);
ten folder trzyma ich kopie i dokumentację, żeby zmiany były wersjonowane.

```
Google News RSS (codzienność)      ┌──────────────┐        ┌───────────────┐
 pogoda/ceny/PKP/urlop/remont ──▶  │ Beka Fabryka │ ─────▶ │ Beka Kolejka  │
                                   │  10:00 daily │ status │ (data store   │
                                   └──────────────┘ czeka  │  145060)      │
                                                           └──────┬────────┘
                                   ┌────────────────┐             │ najświeższy „czeka”
                     Facebook ◀─── │ Beka Publikator│ ◀───────────┘ z ostatnich 3 dni
                   BekaWpigułce    │  18:00 daily   │ ─▶ status „opublikowane”
                                   └────────────────┘
```

| Scenariusz | ID | Harmonogram | Plik |
|---|---|---|---|
| Beka Fabryka — trendy → oryginalne posty (AI) | 6508676 | codziennie 10:00 | `fabryka.json` |
| Beka Publikator — kolejka → Facebook (18:00) | 6510968 | codziennie 18:00 | `publikator.json` |

Kopie stanu sprzed naprawy: `backup/*-2026-10-14.json`.

## Naprawa 2026-10-14

**Fabryka** (od 13.09 padała codziennie, Make ją wyłączył):
- błąd `Function 'random' not found` w seedzie grafiki → seed z `formatDate(now; "X")`;
- źródło tematów: zamiast czołówki Google News (głównie polityka i tragedie,
  które prompt i tak odrzucał) — wyszukiwanie tematów codziennych z ostatniej doby;
- nowy prompt: hook ≤ 80 znaków, puste linie między akapitami, konkretny szczegół,
  puenta, **otwarte pytanie zachęcające do własnej historii**; zakaz polityki,
  nazwisk, wulgaryzmów i „engagement baitu” (polub/udostępnij/oznacz — Meta obcina za to zasięg);
- strażnik jakości: HTTP 200, 120–700 znaków, musi zawierać `?`, bez `#`, linków,
  „Oto post”, „jako AI”, bez odpowiedzi JSON/HTML;
- jeden stały hashtag marki `#BekaWpigułce` dopisywany automatycznie;
- grafika: scena budowana z hooka posta (spójna z tekstem), bez celebrytów,
  polityków, logo i napisów; `private=true` dla tekstu (nie trafia do publicznego feedu Pollinations).

**Publikator** (nigdy się nie uruchomił):
- uzupełnione puste `page_id` → `1282869891751448`;
- wybiera **najświeższy** post z ostatnich 3 dni (wcześniej najstarszy — newsowe tematy by się przeterminowały,
  a jeden zepsuty rekord blokowałby kolejkę na zawsze).
- ⚠ **Połączenie „Facebook — BekaWpigułce” (8898172) wygasło 28.09.2026** — trzeba je
  odnowić ręcznie w Make (Connections → Reauthorize). Dopiero potem włączyć Publikatora.

## Zasady treści (dla automatu i postów ręcznych)

1. **Regularność > ilość**: 1–2 posty dziennie, nigdy serie po kilka naraz.
2. **Każdy post kończy się pytaniem**, na które da się odpowiedzieć własną historią.
   Odpowiadaj na komentarze w pierwszej godzinie — to najmocniejszy sygnał dla algorytmu.
3. **Bez engagement baitu** („polub jeśli”, „udostępnij”, „oznacz kogoś”).
4. **Oryginalne treści** — Beka Radar służy do łapania TEMATÓW, nie do kopiowania memów.
   Reuploady cudzych filmików Meta karze niższym zasięgiem i brakiem monetyzacji.
5. **Jeden hashtag marki**: `#BekaWpigułce` (+ maks. 2–3 tematyczne przy postach ręcznych).
6. **Bez polityki, tragedii i wulgaryzmów seksualnych** — dzielą widownię i blokują monetyzację.
7. Zagadki: odpowiedź publikuj obiecanego dnia (np. przez `odpowiedzi.html` na stronie).
8. Filmiki/memy też z podpisem i pytaniem — nie samo „🤷”.

## Przywracanie kopii

W Make: scenariusz → `…` → Import Blueprint → wklej zawartość pola `blueprint`
z pliku w `backup/`. Albo przez API/MCP `scenarios_update` z tym blueprintem.
