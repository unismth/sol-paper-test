"""Forward-only public Hyperliquid paper tracker. No keys, SDK, signing or orders."""
import argparse,json,time
from pathlib import Path
from datetime import datetime,timezone
from public_data import info,MAINNET
from execution_paper import simulate

ROOT=Path(__file__).resolve().parent
VERSION='sol1h-ema50-200-fixed11-v1'
STATE=ROOT/'paper-sol-ema50-200-state.json'
RESULT=ROOT/'paper-sol-ema50-200-result.json'

def trend_filter(hours):
    e50=e200=float(hours[0]['c']);values={}
    for r in hours:
        close=float(r['c']);e50+=2/51*(close-e50);e200+=2/201*(close-e200)
        values[r['T']]=(close,e50,e200)
    def allow(side,visible):
        if len(visible)<200:return False
        close,fast,slow=values[visible[-1]['T']]
        return side*(close-slow)>0 and side*(fast-slow)>0
    return allow

def write(path,data):
    tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8');tmp.replace(path)

def merge(old,new):return sorted({r['t']:r for r in old+new}.values(),key=lambda r:r['t'])

def candle(interval,start,now):
    return [r for r in info(MAINNET,{'type':'candleSnapshot','req':{'coin':'SOL','interval':interval,'startTime':start,'endTime':now}}) if r['T']<now]

def once():
    now=int(time.time()*1000)
    state=json.loads(STATE.read_text(encoding='utf-8')) if STATE.exists() else {
        'strategy_version':VERSION,'started_ms':(now//60000+1)*60000,'initial_balance':6.18,'minutes':[],'hours':[],'funding':[]}
    if state.get('strategy_version')!=VERSION:raise RuntimeError('Stan innej wersji strategii; nie przeliczono jego transakcji.')
    start=state['minutes'][-1]['t'] if state['minutes'] else state['started_ms']
    if now-start>4900*60000:raise RuntimeError('Przerwa przekracza dostepna historie minutowa. Wstrzymano test; nie uzupelniono luk fikcyjnymi cenami.')
    hours=candle('1h',now-288*3600000,now)
    state['hours']=merge(state['hours'],hours)
    if len(state['hours'])<200 or any(b['t']-a['t']!=3600000 for a,b in zip(state['hours'],state['hours'][1:])):
        raise RuntimeError('Brak ciaglej historii do EMA200; nie otwarto pozycji symulowanej.')
    if now>=start+60000:state['minutes']=merge(state['minutes'],candle('1m',start,now))
    if state['minutes']:
        rows=state['minutes']
        if rows[0]['t']!=state['started_ms'] or any(b['t']-a['t']!=60000 for a,b in zip(rows,rows[1:])):
            raise RuntimeError('Niekompletne dane minutowe; test wstrzymany.')
        funds=info(MAINNET,{'type':'fundingHistory','coin':'SOL','startTime':start-3600000,'endTime':now})
        state['funding']=sorted({f['time']:f for f in state['funding']+funds}.values(),key=lambda f:f['time'])
        r=simulate(rows,state['hours'],state['funding'],mode='maker',slip=.0006,initial=6.18,start_ms=state['started_ms'],close_end=False,
            position_notional=11,entry_filter=trend_filter(state['hours']))
    else:r={'balance':6.18,'net':0,'trades':0,'open_position':None,'pending_limit':None}
    r.update({'paper_only':True,'strategy_version':VERSION,'entry_filter':'close and EMA50 both on the side of EMA200 matching the trade',
        'target_position_notional':11,'leverage_assumption':10,'updated_utc':datetime.fromtimestamp(now/1000,timezone.utc).isoformat(),
        'started_utc':datetime.fromtimestamp(state['started_ms']/1000,timezone.utc).isoformat(),
        'limitations':'Limit fills inferred from1m trade-through, not actual queue. Fee assumptions not account-specific. No liquidation reconstruction. No orders or wallet access. No real-money profitability claim.'})
    write(STATE,state);write(RESULT,r)
    print('SYMULACJA SOL1h EMA50/200 | saldo %.4f USD | wynik zamkniety %+.4f USD | transakcje %d'%(r['balance'],r['net'],r['trades']),flush=True)
    print('Szacowana wartosc po zamknieciu pozycji: %.4f USD'%r.get('equity_if_closed_now',r['balance']),flush=True)
    print('Pozycja symulowana: '+('otwarta' if r['open_position'] else 'brak')+'; oczekujacy limit: '+('tak' if r['pending_limit'] else 'nie'),flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--watch',action='store_true',help='Odswiezanie co60sekund dopoki proces jest uruchomiony')
    args=parser.parse_args()
    while True:
        once()
        if not args.watch:break
        time.sleep(60)
