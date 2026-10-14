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

- router na końcu: post, który przejdzie strażnika → `czeka`; odrzucony → `odrzucony`
  (z kodem HTTP i surową odpowiedzią — podgląd, co psuje generator). Publikator bierze tylko `czeka`.

**Publikator** (nigdy się nie uruchomił) — **aktywny od 2026-10-14**, pierwszy przebieg 15.10 o 18:00:
- uzupełnione puste `page_id` → `1282869891751448`;
- wybiera **najświeższy** post z ostatnich 3 dni (wcześniej najstarszy — newsowe tematy by się przeterminowały,
  a jeden zepsuty rekord blokowałby kolejkę na zawsze);
- grafikę pobiera najpierw Make (timeout 180 s) i wysyła ją jako plik — Facebook nie musi czekać
  na generator obrazków; gdy pobranie się nie uda, post nie wychodzi, rekord zostaje w kolejce.
- Połączenie „Facebook — BekaWpigułce” (8898172) mimo daty `expire` 28.09 **działa**
  (test RPC `Pages` zwraca stronę BekaWpigułce).

## ⚠ Otwarty problem: generator tekstu (Pollinations)

Test 2026-10-14: wszystkie 3 odpowiedzi odrzucone. Model `openai` w `text.pollinations.ai`
jest teraz modelem „rozumującym” i zwraca JSON
`{"role":"assistant","reasoning":"…","content":"…"}` zamiast czystego tekstu
(to samo najpewniej działo się 11–12.09 — przebiegi „udane”, kolejka pusta).

Gotowa poprawka (NIE wgrana — odrzucona przy zatwierdzaniu): w module HTTP
`parseResponse: true` + moduł `util:ComposeTransformer` (id 8) z
`{{trim(ifempty(4.data.content; if(4.data.role; emptystring; 4.data)))}}`,
a w filtrach i mapowaniu `{{8.value}}` zamiast `{{4.data}}`.
Alternatywa: moduł OpenAI z istniejącym połączeniem „My OpenAI connection” (płatne, stabilniejsze).

Dopóki to nie jest naprawione, Fabryka nie dodaje postów `czeka`, więc Publikator nie ma czego publikować.

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
