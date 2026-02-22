import os
import sys
import json
import logging
from datetime import datetime
import pandas as pd

# Add src to path
sys.path.insert(0, os.path.dirname(__file__))

from src.market_data import MStockAPI
from src.trading_config import config
from src.indicators import TechnicalIndicators
from src.utils import setup_logging, now_ist
from src.persistence import StateManager

# Setup basic logging to console
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("Audit")

def run_audit():
    print("\n" + "="*60)
    print("      SENTINEL TRADING BOT - SYSTEM AUDIT REPORT")
    print("      Generated: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("="*60 + "\n")

    # 1. Configuration Check
    print("[1] CONFIGURATION AUDIT")
    print(f"  Live Trading: {config.live_trading}")
    print(f"  RSI Limits: {config.rsi_min} - {config.rsi_max}")
    print(f"  Daily ADX Min: {config.adx_daily_min}")
    print(f"  VIX Threshold: {config.vix_min_threshold}")
    print("-" * 30)

    # 2. Broker Connection Check
    print("[2] BROKER CONNECTIVITY")
    api = MStockAPI()
    try:
        positions = api.get_positions()
        if positions is not None:
            print(f"  API Connection: [OK]")
            print(f"  Broker Positions: {len(positions)}")
        else:
            print(f"  API Connection: [FAILED - HTTP 500 or Auth Error]")
    except Exception as e:
        print(f"  API Connection Error: {e}")
    print("-" * 30)

    # 3. Market Data & Indicators Audit
    print("[3] MARKET TRENDS & INDICATORS (15m Intraday)")
    symbols = {
        "NIFTY 50": ("NSE", "26000"),
        "NIFTY BANK": ("NSE", "26009"),
        "NIFTY FIN SERVICE": ("NSE", "26037"),
        "SENSEX": ("BSE", "51")
    }

    for name, (exchange, token) in symbols.items():
        try:
            # Fetch intraday data - using 10 days for better convergence
            df = api.get_hybrid_history(name, exchange, token, "15minute", days=10)
            
            # Fetch daily data for ADX
            daily_df = api.get_historical_data(name, exchange, token, "day", days=60)
            
            if df is not None and not df.empty:
                # Calculate indicators
                df['RSI'] = TechnicalIndicators.calculate_rsi(df['close'])
                df['MACD'], df['MACD_Signal'], _ = TechnicalIndicators.calculate_macd(df['close'])
                
                last_row = df.iloc[-1]
                rsi = last_row['RSI']
                macd = last_row['MACD']
                signal = last_row['MACD_Signal']
                
                # Daily ADX
                daily_adx = 0
                if daily_df is not None and not daily_df.empty:
                     d_adx, _, _ = TechnicalIndicators.calculate_adx(daily_df['high'], daily_df['low'], daily_df['close'])
                     daily_adx = d_adx.iloc[-1]

                status = "OK" if config.rsi_min <= rsi <= config.rsi_max else "RSI BLOCKED"
                if daily_adx <= config.adx_daily_min:
                     status = "ADX BLOCKED"
                
                trend = "BULLISH" if macd > signal else "BEARISH"
                
                print(f"  {name:20} | RSI: {rsi:5.2f} | D-ADX: {daily_adx:5.2f} | Trend: {trend:8} | Status: {status}")
                print(f"    (MACD: {macd:.2f} | Signal: {signal:.2f} | Result: {'OK' if status=='OK' else 'WAITING'})")
            else:
                print(f"  {name:20} | [DATA FETCH FAILED]")
        except Exception as e:
            print(f"  {name:20} | Error: {e}")
    print("-" * 30)

    # 4. Local State Audit
    print("[4] LOCAL SYSTEM STATE")
    active_pos = StateManager.load_positions()
    history = StateManager.load_history()
    
    print(f"  Active Positions (Local): {len(active_pos) if active_pos else 0}")
    print(f"  Total Trades (History): {len(history) if history else 0}")
    
    if active_pos:
        for und, pos in active_pos.items():
            print(f"    - Monitoring {und}: {pos.option_symbol} (Entry: {pos.entry_price})")
    
    print("\n" + "="*60)
    print("      AUDIT COMPLETE - CHECK LOGS FOR DETAILS")
    print("="*60 + "\n")

if __name__ == "__main__":
    run_audit()
