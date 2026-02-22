import sys
import os
import pandas as pd
import numpy as np

# Add src to path
sys.path.insert(0, os.path.dirname(__file__))

from src.market_data import MStockAPI
from src.indicators import TechnicalIndicators

def diagnostic():
    api = MStockAPI()
    symbols = {
        "NIFTY 50": ("NSE", "26000"),
        "NIFTY BANK": ("NSE", "26009"),
        "NIFTY FIN SERVICE": ("NSE", "26037"),
        "SENSEX": ("BSE", "51")
    }
    
    print(f"--- RSI HYBRID DIAGNOSTIC ---")
    
    for name, (exch, token) in symbols.items():
        try:
            # Fetch 10 days of 15min data (Using HYBRID to get today's bars)
            df = api.get_hybrid_history(name, exch, token, "15minute", days=10)
            if df is None:
                print(f"{name}: Failed to fetch data")
                continue
            
            print(f"\n{name} (LTP: {df['close'].iloc[-1]:.2f}):")
            print(f"  Total bars:        {len(df)}")
            print(f"  Last Candle Time:  {df.index[-1]}")
            
            # Current Bot RSI calculation (on the hybrid data)
            rsi_live = TechnicalIndicators.calculate_rsi(df['close'], period=14)
            print(f"  Hybrid RSI: {rsi_live.iloc[-1]:.2f}")
            
        except Exception as e:
            print(f"{name}: Error {e}")

if __name__ == "__main__":
    diagnostic()
