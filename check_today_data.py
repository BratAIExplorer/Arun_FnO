import sys
import os
import pandas as pd
from datetime import datetime
import pytz

# Add src to path
sys.path.insert(0, os.path.dirname(__file__))

from src.market_data import MStockAPI
from src.utils import setup_logging

logger = setup_logging()

def check_today_data():
    api = MStockAPI()
    symbol = "NIFTY 50"
    token = "26000"
    
    ist = pytz.timezone("Asia/Kolkata")
    now = datetime.now(ist)
    print(f"Current Time (IST): {now}")
    
    # Try fetching 1minute data for multiple days (including today)
    print(f"\nFetching multi-day 1minute data (days=5) for {symbol}...")
    df_1m = api.get_historical_data(symbol, "NSE", token, "1minute", days=5)
    
    if df_1m is not None and len(df_1m) > 0:
        print(f"Returned {len(df_1m)} 1-minute candles.")
        print(f"First candle: {df_1m.index[0]}")
        print(f"Last candle: {df_1m.index[-1]}")
        
        # Check if today is present
        today_data = df_1m[df_1m.index.date == now.date()]
        print(f"Candles for today ({now.date()}): {len(today_data)}")
        
    # Check Daily data
    print(f"\nFetching daily data for {symbol}...")
    df_day = api.get_historical_data(symbol, "NSE", token, "day", days=5)
    if df_day is not None:
         print("Daily candles:")
         print(df_day.tail(3))

if __name__ == "__main__":
    check_today_data()
