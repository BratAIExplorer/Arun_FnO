import sys
import os
import pandas as pd
from datetime import datetime, timedelta
import pytz
from urllib.parse import quote

# Add src to path
sys.path.insert(0, os.path.dirname(__file__))

from src.market_data import MStockAPI
from src.utils import setup_logging

logger = setup_logging()

def probe_api_formats():
    api = MStockAPI()
    symbol = "NIFTY 50"
    token = "26000"
    exchange = "NSE"
    
    ist = pytz.timezone("Asia/Kolkata")
    now = datetime.now(ist)
    
    # Variations to try
    variations = [
        ("typea", "15minute", "Type A Intraday 15m"),
        ("typea", "1minute", "Type A Intraday 1m"),
    ]
    
    for base, tf, desc in variations:
        print(f"\n--- Probimg Variation: {desc} ---")
        from_dt = now.replace(hour=9, minute=15, second=0, microsecond=0)
        to_dt = now.replace(hour=15, minute=30, second=0, microsecond=0)
        
        from_str = from_dt.strftime("%Y-%m-%d %H:%M:%S")
        to_str = to_dt.strftime("%Y-%m-%d %H:%M:%S")
        ist = pytz.timezone("Asia/Kolkata")
        
        url = (
            f"https://api.mstock.trade/openapi/{base}/instruments/intraday/"
            f"{exchange.upper()}/{token}/{tf}"
        )
        
        print(f"URL: {url}")
        try:
            resp = api.requests.get(url, headers=api.get_headers(), timeout=10)
            print(f"Status: {resp.status_code}")
            if resp.status_code == 200:
                data = resp.json()
                candles = data.get("data", {}).get("candles", [])
                print(f"Candles returned: {len(candles)}")
                if candles:
                    print(f"First candle: {candles[0][0]}")
                    print(f"Last candle: {candles[-1][0]}")
            else:
                print(f"Body: {resp.text}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    # Add requests to api object for easy access in probe
    import requests
    MStockAPI.requests = requests
    probe_api_formats()
