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

def check_history():
    api = MStockAPI()
    
    # Nifty 50 tokens
    symbol = "NIFTY 50"
    exchange = "NSE"
    token = "26000"
    
    print(f"Fetching 15min history for {symbol}...")
    df = api.get_historical_data(symbol, exchange, token, "15minute", days=5)
    
    if df is not None:
        print("\nLast 5 candles from API:")
        print(df.tail(5))
        
        ist = pytz.timezone("Asia/Kolkata")
        now = datetime.now(ist)
        print(f"\nCurrent Time (IST): {now}")
        
        last_candle_time = df.index[-1]
        print(f"Last candle timestamp: {last_candle_time}")
        
        # Check if last candle is the current 15min bar
        current_bar_start = now.replace(minute=now.minute - now.minute % 15, second=0, microsecond=0)
        print(f"Current 15min bar should start at: {current_bar_start}")
        
        if last_candle_time == current_bar_start:
            print(">>> API ALREADY RETURNS THE CURRENT FORMING CANDLE.")
        else:
            print(">>> API ONLY RETURNS CLOSED CANDLES.")
            
if __name__ == "__main__":
    check_history()
