# SOL EMA50/200 — test symulowany na nowych danych

To repozytorium testuje oprogramowanie na publicznych danych Hyperliquid. Nie ma portfela, kluczy ani wysyłania prawdziwych zleceń. Nie jest to hosting bota do prawdziwego handlu ani obietnica zarobku.

## Co robi serwer

Raz na godzinę pobiera brakujące minuty i odtwarza je chronologicznie według zamrożonych zasad. Zapisuje stan w repozytorium, więc komputer użytkownika może być wyłączony. Uruchomienia GitHub Actions mogą być opóźnione; to test przybliżonego wykonania na świecach, nie reakcja na rynek w czasie rzeczywistym.

Wynik jest w [STATUS.md](STATUS.md). Szczegóły są w `paper-sol-ema50-200-result.json`; publiczne świece i stan w `paper-sol-ema50-200-state.json`. Te pliki powstaną po pierwszym uruchomieniu. Repozytorium publiczne oznacza, że kod i wyniki są widoczne dla innych. Nie dodawaj tu żadnych kluczy, haseł ani danych portfela.

## Uruchomienie przez stronę GitHub

1. Utwórz nowe **publiczne** repozytorium, np. `sol-paper-test`, na własnym koncie GitHub. Standardowe uruchomienia Actions w publicznych repozytoriach są bezpłatne; prywatne mają odrębne limity. Nie wybieraj płatnego serwera, dużego runnera ani Codespaces.
2. Wgraj zawartość tej paczki do głównego katalogu repozytorium, nie sam plik ZIP. Muszą być widoczne pliki Python oraz `.github/workflows/paper-test.yml`. Jeżeli wgrywasz przez stronę i folder `.github` zostanie pominięty, użyj Add file → Create new file, wpisz dokładnie `.github/workflows/paper-test.yml` i wklej treść załączonego pliku.
3. Wejdź w Settings → Actions → General → Workflow permissions. Zezwól na zapis wyników w tym repozytorium (Read and write permissions), jeśli ustawienie konta tego wymaga. Automatyczny token służy wyłącznie zapisaniu stanu; nie dodajesz żadnego klucza portfela ani osobistego tokenu.
4. W zakładce Actions wybierz „Test symulowany SOL EMA50-200” i kliknij Run workflow na domyślnej gałęzi. Poczekaj na zielony wynik. Następnie otwórz STATUS.md.
5. Kolejne uruchomienia są planowane raz na godzinę. Możesz wyłączyć komputer. Pierwszy wynik zero jest normalny; wcześniejsza historia służy tylko do wskaźników.

Wgrywaj tylko tę niewielką paczkę, nie całą lokalną kolekcję badań i archiwów. Nie dodaje ona wcześniejszych transakcji do nowego testu.

## Zasady

Wirtualne saldo 6,18 USD, docelowy nominał 11 USD zaokrąglany w dół do 0,01 SOL, symulowane 10×. SOL1h wybija maksimum/minimum poprzednich 20 godzin. Long tylko gdy cena i EMA50 są ponad EMA200; short odwrotnie. Jedna pozycja, SL2%, TP4%, hold24h, dwie próby dziennie UTC. Limit 0,02% od zamknięcia sygnału, ważny 5 minut, wymagane przejście ceny o dodatkowe 0,01%. Prowizje modelu: 0,015% wejście, 0,045% wyjście; poślizg wyjścia 0,06%; funding wliczony. Bez zwiększania pozycji po zysku i bez automatycznego zatrzymania po 1 USD straty.

## Ograniczenia i zatrzymanie

GitHub nie gwarantuje dokładnej pory uruchomienia. Krótsze przerwy uzupełnia się dostępnymi minutami. Jeśli brak danych albo przerwa przekroczy około 4900 minut, test wstrzymuje się z błędem zamiast dopisywać fikcyjne transakcje. Sprawdzaj czas aktualizacji w STATUS.md i czerwone uruchomienia Actions. Zapis stanu wymaga możliwości zapisu na domyślnej gałęzi; ochrona tej gałęzi może go zablokować.

Pierwszy przegląd po co najmniej 4 tygodniach i 30 zamkniętych transakcjach; może to potrwać dłużej. Nie ma automatycznego przełączenia na prawdziwy handel. Aby zatrzymać test, Actions → wybrany workflow → menu → Disable workflow. W razie bezczynności repozytorium GitHub może wyłączyć harmonogram.

Nie odtworzono kolejki, pełnej ścieżki ceny wewnątrz minuty i likwidacji. Zysk historyczny nie potwierdza przyszłej rentowności. Actions służy tutaj rozwojowi i testowaniu tego projektu; nie należy zamieniać tej paczki w usługę do prawdziwego tradingu.

Źródła: [rozliczenia GitHub Actions](https://docs.github.com/en/billing/concepts/product-billing/github-actions), [opóźnienia harmonogramu](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule), [zasady wykorzystania Actions do testowania](https://docs.github.com/en/site-policy/github-terms/github-terms-for-additional-products-and-features#actions).
