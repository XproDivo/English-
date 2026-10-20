# Gramly — angielski, który ma sens

Polskojęzyczna, responsywna strona do nauki gramatyki angielskiej. Działa bez konta, kluczy API, bazy danych i płatnych usług. Zależności oraz fonty są lokalne; postęp jest przechowywany w `localStorage` tej przeglądarki.

## Uruchomienie

Wymagane: Node.js 24 (wersja środowiska: **24.19.0**) i npm.

```bash
cd /workspace/English-
npm ci
npm run dev -- --port 5173
```

`.npmrc` umieszcza cache npm w zapisywalnym `/tmp/english-npm-cache`. Repozytorium zawiera lockfile. Korzystaj z istniejącego checkoutu: zadania chmurowe są izolowane i nie wymagają tworzenia dodatkowego worktree.

```bash
npm test          # testy logiki nauki i spójności zadań
npm run build    # TypeScript i produkcyjny katalog dist/
npm run preview  # lokalne sprawdzenie zbudowanej strony
```

Do publikacji wystarczy hosting statyczny obsługujący katalog `dist/`. Projekt nie jest automatycznie wysyłany na GitHub ani wdrażany przez te polecenia.

## Zakres

- **12 czasów**: Simple, Continuous, Perfect i Perfect Continuous w Present, Past i Future.
- **24 konstrukcje**: podstawy zdania, pytania i przeczenia, przedimki, określenia ilości, stopniowanie, be going to, tryby warunkowe 0/I/II/III i mieszane, strona bierna, forma kauzatywna, czasowniki modalne i modale o przeszłości, wish / if only (w tym Past Perfect i would), would rather / would prefer / had better, used to / be used to / get used to, mowa zależna, pytania pośrednie, question tags, proponowanie, bezokolicznik / -ing i zdania względne.
- **168 ćwiczeń**: wybór i samodzielne wpisywanie, wyjaśnienie po każdej odpowiedzi, podsumowanie wszystkich prób.
- **24 czasowniki B2–C2** z tłumaczeniem i kontekstem. Poziomy są orientacyjne; nowy czasownik w zadaniu ma podane polskie znaczenie.
- Filtrowanie według poziomu, wyszukiwanie, sugerowana ścieżka, trening mieszany, dzienny cel, seria dni, powtórki, archiwum postępu JSON i reset z potwierdzeniem.

Każda lekcja ma trzy kroki: **zastosowanie → budowa → porównanie i pułapki**. Przykłady są tłumaczone na polski. Lekcje i ćwiczenia są dostępne od razu, bez blokowania użytkownika poziomem.

## Jak działa nauka

Wynik liczy pierwsze odpowiedzi. Minimum **80%** oznacza zaliczenie zestawu; nie jest certyfikatem CEFR ani gwarancją trwałego opanowania. Aplikacja zapamiętuje najlepszy wynik, a ostatni wynik aktualizuje harmonogram powtórek.

Po udanych powtórkach odstępy rosną: **1, 3, 7, 14, 30, 60 dni**. Wynik poniżej 80% przywraca temat za godzinę. Udane ponowne ćwiczenie przed terminem nie wydłuża odstępu: natychmiastowy sukces nie dowodzi pamiętania po przerwie. Zapisane słowa trafiają od razu do pierwszego ćwiczenia przypominającego.

Trening mieszany losuje po dwa zadania z maksymalnie czterech zaliczonych tematów. Przed zaliczeniem dwóch tematów korzysta z podstaw A1. Nie zalicza całej lekcji na podstawie pojedynczego zadania i nie wydłuża harmonogramu pełnych lekcji.

Ogólne zasady dydaktyczne opisano w widoku „Jak się tutaj uczysz?”:

- Dunlosky i in. (2013), *Improving Students’ Learning With Effective Learning Techniques*, DOI: [10.1177/1529100612453266](https://doi.org/10.1177/1529100612453266).
- Roediger i Karpicke (2006), *Test-Enhanced Learning*, DOI: [10.1111/j.1467-9280.2006.01693.x](https://doi.org/10.1111/j.1467-9280.2006.01693.x).
- Cepeda i in. (2006), *Distributed practice in verbal recall tasks*, DOI: [10.1037/0033-2909.132.3.354](https://doi.org/10.1037/0033-2909.132.3.354).
- Renkl i Atkinson (2003), *Structuring the Transition From Example Study to Problem Solving in Cognitive Skill Acquisition*, DOI: [10.1207/S15326985EP3801_3](https://doi.org/10.1207/S15326985EP3801_3).

To odniesienia do istniejącej literatury i jej ogólnych wniosków, nie wyniki badania tej aplikacji. Próby pobrania publikacji z SAGE, PubMed oraz materiałów British Council i Learning Scientists zostały zablokowane przez politykę sieci środowiska (HTTP 403). Nie weryfikowano tu pełnych tekstów. Dodano domeny tych źródeł do projektu konfiguracji środowiska; zapis projektu sam nie zmienia bieżącej polityki sieci. Zastosowane odstępy i próg 80% są decyzjami projektowymi, a nie harmonogramem udowodnionym przez wymienione badania.

## Dane i ograniczenia

Postęp nie synchronizuje się między urządzeniami. Usunięcie danych strony usuwa postęp. Przycisk w ustawieniach pobiera kopię JSON; import nie jest obecnie częścią interfejsu. Aplikacja nie ocenia swobodnych wypowiedzi, wymowy ani dłuższych własnych tekstów. Przykłady i ćwiczenia stanowią skończony program, a nie pełny kurs wszystkich umiejętności do C2.

Wymowa słów korzysta z opcjonalnego systemowego `speechSynthesis`. Dostępność angielskiego głosu zależy od przeglądarki i systemu; błąd jest zgłaszany w interfejsie i nie blokuje nauki.

## Sprawdzanie w przeglądarce

Środowisko chmurowe zawiera Python Playwright i Chromium. Przy uruchomionym serwerze deweloperskim:

```bash
python3 tests/browser_smoke.py
```

Na innej maszynie można przygotować osobne środowisko Python i zainstalować `playwright`; Chromium wskaż przez `CHROMIUM_PATH`. `BASE_URL` pozwala zmienić adres testowanego serwera deweloperskiego. Test używa jego modułu danych, więc uruchamiaj go z `npm run dev`, nie `npm run preview`.

Test sprawdza wszystkie 36 zestawów i 168 odpowiedzi przez interfejs, błędną próbę, ponowne otwarcie strony, odstępy powtórek, słownictwo, trening mieszany, eksport, reset, nawigację mobilną i automatyczne reguły dostępności axe. Uruchamia się w izolowanym kontekście przeglądarki i nie usuwa danych użytkownika.

## Pliki

- `src/curriculum.ts` — treść lekcji, ćwiczenia i słownik.
- `src/learning.ts` — dopasowanie odpowiedzi, zapis/odczyt postępu, seria dni i harmonogram powtórek.
- `src/App.tsx` — widoki i interakcje.
- `src/styles.css` — responsywny interfejs, stany fokusu i ograniczenie animacji.
- `tests/` — testy logiki i przeglądarki.
