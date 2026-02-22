import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz

# Add src to path
sys.path.insert(0, os.path.dirname(__file__))

from src.indicators import TechnicalIndicators

def test_rsi_precision():
    print("Testing RSI Precision (Wilder's Smoothing)...")
    
    # Sample data (15 points to check smoothing after first 14)
    data = pd.Series([
        44.34, 44.09, 44.15, 43.61, 44.33, 44.83, 45.10, 
        45.42, 45.84, 46.08, 45.89, 46.03, 45.61, 46.28, 46.28
    ])
    
    rsi = TechnicalIndicators.calculate_rsi(data, period=14)
    
    print(f"RSI Values (Last 5):\n{rsi.tail(5)}")
    
    # Check if we have values (no more blocked by min_periods)
    if not rsi.isna().all():
        print("PASS: RSI calculation producing values.")
    else:
        print("FAIL: RSI calculation producing only NaNs.")

def test_live_candle_effect():
    print("\nTesting Live Candle Indicator Updates...")
    
    # Mock history (mostly flat)
    history = pd.Series([100] * 50)
    
    # Calculate RSI on history
    rsi_hist = TechnicalIndicators.calculate_rsi(history, period=14)
    
    # Append a significant move (live candle)
    live_move = pd.Series([110], index=[50])
    combined = pd.concat([history, live_move])
    
    rsi_combined = TechnicalIndicators.calculate_rsi(combined, period=14)
    
    print(f"RSI before live move: {rsi_hist.iloc[-1]:.2f}")
    print(f"RSI after live move: {rsi_combined.iloc[-1]:.2f}")
    
    if rsi_combined.iloc[-1] > rsi_hist.iloc[-1]:
        print("PASS: RSI correctly reflects live candle update.")
    else:
        print("FAIL: RSI did not react to live candle.")

if __name__ == "__main__":
    test_rsi_precision()
    test_live_candle_effect()
