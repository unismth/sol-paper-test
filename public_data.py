"""Only public Hyperliquid market data. No account, keys or order endpoints."""
import json,time,urllib.request,urllib.error

MAINNET='https://api.hyperliquid.xyz'
def info(base,payload):
    if base!=MAINNET or payload.get('type') not in ('candleSnapshot','fundingHistory'):
        raise ValueError('Only public candles and funding are supported')
    request=urllib.request.Request(MAINNET+'/info',json.dumps(payload).encode(),{'Content-Type':'application/json'})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request,timeout=25) as response:return json.load(response)
        except urllib.error.HTTPError as error:
            if error.code not in (429,500,502,503,504) or attempt==2:raise
            time.sleep(2*(attempt+1))
        except (TimeoutError,urllib.error.URLError):
            if attempt==2:raise
            time.sleep(2*(attempt+1))
