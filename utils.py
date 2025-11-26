import numpy as np
import requests
import time

def get_last_traded_price(symbols: str, timeout: float = 180.0) -> float:
    """
    Fetch the last traded price for a given symbol from an API endpoint.
    By default, uses NSE India equity quote API. Returns the price as float, or None on error.
    Example usage:
        price = get_last_traded_price('SETFGOLD')
    """
    session = requests.Session()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://www.nseindia.com/",
        "Connection": "keep-alive",
    }
    session.headers.update(headers)

    base_url = "https://nse-api-khaki.vercel.app/"
    api_url = base_url + f"stock/list?symbols={symbols}"
    ltp = []
    try:
        # # Warm up cookies/session
        # session.get(base_url, timeout=timeout)
        # resp = session.get(api_url, timeout=timeout)
        # resp.raise_for_status()
        # data = resp.json()
        with open('x.json','r') as f:
            import json
            data = json.load(f)
        for item in data['stocks']:
            price = item.get("last_price", {}).get("value")
            if price is None:
                nse_api_url = "https://www.nseindia.com/api/quote-equity?symbol={symbol}".format(symbol=item.get("symbol"))
                nse_resp = session.get(nse_api_url, timeout=timeout)
                nse_resp.raise_for_status()
                nse_data = nse_resp.json()
                price = nse_data.get("priceInfo", {}).get("lastPrice")
            # Remove commas and convert to float if needed
            if isinstance(price, str):
                price = float(price.replace(",", ""))
            ltp.append(float(price))
    except Exception as e:
        print(f"Error fetching last traded price: {e}")
    return ltp


def get_symbol_info(session: requests.Session,base_url: str, symbol: str, timeout: float = 25.0) -> dict:
    retries = 5
        
    inav_target_url = base_url + "/quote-equity?symbol={symbol}".format(symbol=symbol)

    for attempt in range(retries):
        try:
            resp = session.get(inav_target_url, timeout=timeout)
            resp.raise_for_status()
            inav = resp.json()["priceInfo"]["iNavValue"]
            break
        except (KeyError, ValueError) as e:
            if attempt<retries-1:
                time.sleep(1)  # wait before retrying
            else:
                print(f"Error fetching iNav for symbol {symbol}: {e}")
                inav = None
    
    aum_target_url = base_url + "/quote-equity?symbol={symbol}&section=trade_info".format(symbol=symbol)
    
    for attempt in range(retries):
        try:
            resp = session.get(aum_target_url, timeout=timeout)
            resp.raise_for_status()
            aum = resp.json()['marketDeptOrderBook']["tradeInfo"]["totalMarketCap"]
            break
        except (KeyError, ValueError) as e:
            if attempt<retries-1:
                time.sleep(1)  # wait before retrying
            else:
                print(f"Error fetching AUM for symbol {symbol}: {e}")
                aum = None
    return {"inav": inav, "aum": aum}

def _check_url(url: str, timeout: float = 5.0) -> dict:
    """Perform a lightweight GET to a URL and return a small result dict.

    This is used for optional 'full' health checks. The function never
    raises; it returns an object describing success or error.
    """
    headers = {
        "User-Agent": "health-check/1.0 (+https://example.com)"
    }
    try:
        resp = requests.get(url, timeout=timeout, headers=headers)
        return {
            "ok": resp.status_code == 200,
            "status_code": resp.status_code,
            "elapsed_ms": int(resp.elapsed.total_seconds() * 1000),
        }
    except Exception as exc:
        return {"ok": False, "error": str(exc)}

def format_uptime(seconds: float) -> str:
    """Format a duration in seconds into a human-readable string.

    Examples:
      45 -> "45s"
      125 -> "2m 5s"
      3725 -> "1h 2m 5s"
      90000 -> "1d 1h"
    """
    secs = int(seconds)
    days, rem = divmod(secs, 86400)
    hours, rem = divmod(rem, 3600)
    minutes, secs = divmod(rem, 60)
    parts = []
    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    # Always show seconds if there are no larger units, otherwise show seconds when non-zero
    if secs or not parts:
        parts.append(f"{secs}s")
    return " ".join(parts)

def calculate_discount_percentage(inav: float, ltp: float) -> float:
    """Calculate the discount percentage between LTP and iNAV."""
    if inav == 0 or inav is None or ltp is None:
        return 0.0
    discount = ((inav - ltp) / inav) * 100
    return round(discount, 2)

def fetch_and_update_aum_and_inav(df):
    inav_list = []
    aum_list = []
    session = requests.Session()
    # Typical browser headers - important for nseindia which blocks non-browser UA often
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.nseindia.com/",
        "Connection": "keep-alive",
    }
    session.headers.update(headers)

    base_url = "https://www.nseindia.com/api"

    session.get(base_url, timeout=10)
    for _, row in df.iterrows():
        symbol = row.get("symbol")
        # if not symbol:
        #     return row  # No symbol to process

        info = get_symbol_info(session, base_url, symbol)
        inav = info.get("inav")
        aum = info.get("aum")
        if isinstance(inav, str):
            inav = float(inav.replace(",", ""))
        if isinstance(aum, str):
            aum = float(aum.replace(",", ""))
        print(_,'----'+symbol+'----',inav,type(inav),aum,type(aum))
        inav_list.append(inav if inav is not None else np.nan)
        aum_list.append(aum if aum is not None else np.nan)
    df['inav'] = inav_list
    df['aum'] = aum_list
    return df

def fetch_and_update_ltp(df):
    symbols = df['symbol'].astype(str).str.strip().str.cat(sep=',')

    ltp = get_last_traded_price(symbols=symbols)
    print('LTP fetched:', ltp)
    if ltp is not None:
        df["ltp"] = ltp
    df['discount'] = df.apply(lambda row: calculate_discount_percentage(row['inav'], row['ltp']), axis=1)
    return df