"""Readable project-test report; virtual balances only."""
import json,os
from pathlib import Path
from datetime import datetime

ROOT=Path(__file__).resolve().parent
def main():
    r=json.loads((ROOT/'paper-sol-ema50-200-result.json').read_text(encoding='utf-8'))
    equity=r.get('equity_if_closed_now',r['balance'])
    days=max(0,(datetime.fromisoformat(r['updated_utc'])-datetime.fromisoformat(r['started_utc'])).total_seconds()/86400)
    text=f'''# Wyniki testu symulowanego SOL 1h

**To symulacja. Nie ma prawdziwych zlecen ani polaczenia z portfelem.**

| Informacja | Wynik |
|---|---:|
| Aktualizacja UTC | {r['updated_utc']} |
| Poczatek testu UTC | {r['started_utc']} |
| Dni zbierania nowych danych | {days:.2f} |
| Wirtualne saldo poczatkowe | 6.18 USD |
| Saldo zrealizowane | {r['balance']:.4f} USD |
| Zysk/strata zamknietych transakcji | {r['net']:+.4f} USD |
| Wycena po szacowanym zamknieciu pozycji | {equity:.4f} USD |
| Zysk/strata z otwarta pozycja i kosztami | {equity-6.18:+.4f} USD |
| Zamkniete transakcje | {r['trades']} |
| Otwarta pozycja symulowana | {'tak' if r['open_position'] else 'nie'} |
| Oczekujacy limit | {'tak' if r['pending_limit'] else 'nie'} |

Filtr EMA50/200, nominał docelowy 11 USD zaokraglany w dol, symulowane 10x.
Serwer odtwarza brakujace minuty raz na godzine; GitHub moze opoznic uruchomienie.
Wynik nie dowodzi przyszlej rentownosci. Model nie odtwarza kolejki zlecen ani likwidacji.
Jesli data aktualizacji stoi w miejscu, sprawdz bledy w zakladce Actions.
'''
    (ROOT/'STATUS.md').write_text(text,encoding='utf-8')
    summary=os.environ.get('GITHUB_STEP_SUMMARY')
    if summary:Path(summary).write_text(text,encoding='utf-8')
    print('Saved STATUS.md')

if __name__=='__main__':main()
