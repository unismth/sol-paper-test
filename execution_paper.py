"""Minute execution model for frozen SOL1h breakout. No wallet or orders."""
import bisect, math
from decimal import Decimal, ROUND_CEILING, ROUND_FLOOR

def closed_signal(hours):
    if len(hours)<21:return 0
    last=hours[-1];previous=hours[-21:-1]
    c=float(last['c'])
    return 1 if c>max(float(r['h']) for r in previous) else -1 if c<min(float(r['l']) for r in previous) else 0

def make_pending(side,reference,opening,when,mode):
    limit=reference*(1-side*.0002)
    if mode=='maker' and (limit>=opening if side==1 else limit<=opening):return None
    return {'side':side,'limit':limit,'start':when,'expires':when+5*60000,'mode':mode}

def attempt_fill(pending,row,slip):
    side=pending['side'];limit=pending['limit'];t=row['t']
    if t>=pending['expires']:return None
    if pending['mode']=='taker':return float(row['o'])*(1+side*slip)
    # Require trading through the limit by1bp; touching alone is insufficient.
    crossed=float(row['l'])<=limit*(1-.0001) if side==1 else float(row['h'])>=limit*(1+.0001)
    return limit if crossed else None

def simulate(minutes,hours,funding,mode='maker',slip=.0003,initial=6.18,start_ms=None,close_end=True,audit=None,position_notional=None,loss_limit=None,entry_filter=None):
    # The strategy sees hours only after they close. Advance its clock one minute
    # at a time; OHLC for the current minute is execution feedback, not a signal.
    visible_hours=[];hour_cursor=0
    funding_map={}
    for f in funding:
        # Funding timestamps may be milliseconds after a minute boundary.
        minute=f['time']//60000*60000
        funding_map[minute]=funding_map.get(minute,0.)+float(f['fundingRate'])
    start_ms=start_ms or hours[20]['T']+1
    balance=initial;peak=initial;dd=0;pending=None;position=None;ledger=[];day=None;attempts_today=0
    signals=missed=filled=skipped_cash=below_minimum=0;fees=0;funding_total=0;min_cash=initial;min_equity=initial
    for r in minutes:
        t=r['t']
        while hour_cursor<len(hours) and hours[hour_cursor]['T']<t:
            visible_hours.append(hours[hour_cursor]);hour_cursor+=1
        if t<start_ms:continue
        if day!=t//86400000:day=t//86400000;attempts_today=0
        opening,high,low,close=[float(r[k]) for k in ('o','h','l','c')]
        entries_allowed=loss_limit is None or balance>initial-loss_limit
        if not entries_allowed and pending is not None:missed+=1;pending=None
        if pending and t>=pending['expires']:missed+=1;pending=None
        decision_hour=visible_hours[-1] if len(visible_hours)>=21 and visible_hours[-1]['T']+1==t else None
        if entries_allowed and decision_hour is not None and position is None and pending is None and attempts_today<2:
            side=closed_signal(visible_hours[-21:]);ref=float(decision_hour['c'])
            if side and entry_filter is not None and not entry_filter(side,visible_hours):side=0
            if audit is not None:audit({'clock_ms':t,'latest_visible_hour_close_ms':decision_hour['T'],
                'visible_hour_count':len(visible_hours),'side':side,'reference':ref,'current_open':opening})
            if side:
                attempts_today+=1;signals+=1;pending=make_pending(side,ref,opening,t,mode)
                if pending is None:missed+=1
        just_filled=False
        if pending and position is None:
            entry=attempt_fill(pending,r,slip)
            if entry is not None:
                side=pending['side'];entry_fee=.00015 if mode=='maker' else .00045
                step=Decimal('.01')
                if position_notional is None:
                    qty=float((Decimal('10.01')/Decimal(str(entry))/step).to_integral_value(rounding=ROUND_CEILING)*step)
                else:
                    qty=float((Decimal(str(position_notional))/Decimal(str(entry))/step).to_integral_value(rounding=ROUND_FLOOR)*step)
                margin=qty*entry/10
                if qty*entry<10.01:below_minimum+=1
                elif margin+qty*entry*entry_fee>min(1.2,balance):skipped_cash+=1
                else:
                    position={'side':side,'entry':entry,'qty':qty,'fee':qty*entry*entry_fee,'funding':0.,'start':t,'margin':margin,'notional':qty*entry}
                    filled+=1;just_filled=True
                pending=None
        if position:
            p=position;side=p['side'];entry=p['entry'];qty=p['qty']
            stop=entry*(1-side*.02);target=entry*(1+side*.04)
            stopped=low<=stop if side==1 else high>=stop
            # Targets on maker-fill minute cannot be assumed to occur after filling.
            target_hit=(high>=target if side==1 else low<=target) and not (just_filled and mode=='maker')
            timed=t+60000>=p['start']+24*3600000
            closing=stopped or target_hit or timed or (close_end and r is minutes[-1])
            rate=funding_map.get(t)
            if rate is not None:
                payment=side*qty*close*rate
                if payment>0 or (not just_filled and not closing):p['funding']+=payment
            mark=balance+side*qty*(close-entry)-p['fee']-p['funding']
            # No liquidation reconstruction; this model reports execution sensitivity only.
            if closing:
                raw_exit=(min(opening,stop) if side==1 else max(opening,stop)) if stopped else target if target_hit else close
                exit_price=raw_exit*(1-side*slip)
                total_fee=p['fee']+qty*exit_price*.00045
                pnl=side*qty*(exit_price-entry)-total_fee-p['funding'];balance+=pnl
                fees+=total_fee;funding_total+=p['funding']
                ledger.append({'start_ms':p['start'],'end_ms':r['T'],'net_pnl':pnl,'reason':'stop' if stopped else 'target' if target_hit else 'time_or_end',
                    'entry_notional':p['notional'],'qty':qty,'side':side,'fees':total_fee,'funding':p['funding']})
                position=None;mark=balance
            peak=max(peak,mark);dd=max(dd,peak-mark);min_cash=min(min_cash,balance);min_equity=min(min_equity,mark)
    wins=sum(max(0,x['net_pnl']) for x in ledger);losses=sum(max(0,-x['net_pnl']) for x in ledger)
    elapsed=(minutes[-1]['T']-start_ms+1)/(7*86400000)
    open_pnl=0.
    if position:
        hypothetical_exit=float(minutes[-1]['c'])*(1-position['side']*slip)
        open_pnl=position['side']*position['qty']*(hypothetical_exit-position['entry'])-position['fee']-position['qty']*hypothetical_exit*.00045-position['funding']
    return {'mode':mode,'initial':initial,'balance':balance,'net':balance-initial,'trades':len(ledger),'signals':signals,
            'unfilled_or_nonpassive':missed,'insufficient_cash':skipped_cash,'below_minimum_after_rounding':below_minimum,'fees':fees,'funding':funding_total,
            'profit_factor':wins/losses if losses else None,'drawdown_minute_close':dd,'minimum_realized_balance':min_cash,'minimum_equity_at_minute_close':min_equity,
            'calendar_weeks':elapsed,'net_per_week':(balance-initial)/elapsed,'trade_ledger':ledger,
            'open_position':position,'pending_limit':pending,
            'open_position_pnl_if_closed_now':open_pnl,'equity_if_closed_now':balance+open_pnl,
            'total_net_if_closed_now':balance+open_pnl-initial}

if __name__=='__main__':
    import json
    import weeks_research as w
    minutes,funding=w.load_archive('SOL');hours=w.aggregate(minutes,60)
    results=[]
    for slip in (.0003,.0006):
        for mode in ('taker','maker'):
            r=simulate(minutes,hours,funding,mode,slip);r['slippage_per_taker_side']=slip
            r['weekly_realized']=w.weekly(r.pop('trade_ledger'),hours[20]['T']+1,minutes[-1]['T']);results.append(r)
    out={'source':'Binance SOL futures minute prices/funding Aug-Sep2026; hypothetical Hyperliquid fee/quantity/margin assumptions',
         'limitations':'OHLC trade-through proxy, not historical queue or actual maker fills. No live liquidation reconstruction. Previously inspected prices, exploratory comparison. No wallet access or orders.',
         'rules':'Frozen SOL1h20bar breakout; SL2%,TP4%,hold24h,max2attempts/day;6.18USD,10x,min10.01USD notional,1.20USD margin+entryfee cap. Maker2bp away from signalclose,trade-through1bp,expires5minutes. Entry maker.015%,exit taker.045%;no favorable funding credit on uncertain entry/exit minutes.',
         'results':results}
    w.m.p.engine.save(w.ROOT/'execution-paper-result.json',out)
    print(json.dumps([{k:v for k,v in r.items() if k!='weekly_realized'} for r in results]))
