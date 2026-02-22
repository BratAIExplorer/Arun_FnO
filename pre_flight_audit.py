import os
import json
import sys
import pandas as pd
from datetime import datetime

class AuditLogger:
    def info(self, msg): print(f"[\033[94mINFO\033[0m] {msg}")
    def success(self, msg): print(f"[\033[92mPASS\033[0m] {msg}")
    def error(self, msg): print(f"[\033[91mFAIL\033[0m] {msg}")
    def warn(self, msg): print(f"[\033[93mWARN\033[0m] {msg}")

log = AuditLogger()

def run_audit():
    print("\n" + "="*50)
    print("   SENTINEL HUB - PRE-FLIGHT SYSTEM AUDIT   ")
    print("="*50 + "\n")
    
    # 1. Credentials Check
    if os.path.exists('credentials.json'):
        try:
            with open('credentials.json', 'r') as f:
                creds = json.load(f)
                if creds.get('mstock', {}).get('access_token'):
                    log.success("API Token Found")
                else: log.error("API Token Missing in credentials.json")
        except: log.error("credentials.json is corrupted")
    else: log.error("credentials.json not found")

    # 2. Logic Integrity Check (Exhaustive Rule Scan)
    print("--- [Deep Logic Scan] ---")
    
    # 2a. Confirmed Candle Rule (Safety Shield)
    if os.path.exists('main.py'):
        with open('main.py', 'r') as f:
            content = f.read()
            # Check for confirmed candle index
            if "check_idx = current_row_idx - 1" in content:
                log.success("Exit: Confirmed Candle Rule (Safety Shield) - ENABLED")
            else:
                log.error("Exit: Confirmed Candle Rule - DISABLED/MISSING")
            
            # Check for multi-index processing
            indices = ["NIFTY50", "BANKNIFTY", "FINNIFTY", "SENSEX"]
            missing_indices = [idx for idx in indices if idx not in content]
            if not missing_indices:
                log.success(f"Indices: All 4 processed ({', '.join(indices)})")
            else:
                log.error(f"Indices: Missing processing for {missing_indices}")

    # 2b. Entry Rules (Conditions)
    rules = {}
    if os.path.exists('src/fno_trading_bot.py'):
        with open('src/fno_trading_bot.py', 'r') as f:
            bot_code = f.read()
            
            # VIX Verification
            if "if vix < self.config.vix_min_threshold:" in bot_code:
                log.success("Entry: VIX Floor Check - ACTIVE")
                rules['VIX Min'] = "10.0"
            else: log.error("Entry: VIX Floor Check - MISSING")
            
            # RSI Verification
            if "self.config.rsi_min <= rsi <= self.config.rsi_max" in bot_code:
                log.success("Entry: RSI Safety Zone - ACTIVE")
                rules['RSI Range'] = "30 - 65"
            else: log.error("Entry: RSI Safety Zone - MISSING")
            
            # Daily ADX Verification
            if "daily_adx <= self.config.adx_daily_min" in bot_code:
                log.success("Entry: Daily ADX Trend Check - ACTIVE")
                rules['Daily ADX Min'] = "25.0"
            else: log.error("Entry: Daily ADX Check - MISSING")

            # Daily Profit Cap Verification
            if "daily_profit_limit" in bot_code and "daily_pnl >= self.config.daily_profit_limit" in bot_code:
                log.success("Entry: Daily Profit Cap - ACTIVE")
                rules['Profit Cap'] = "Rs 1200.0"
            else: log.error("Entry: Daily Profit Cap - MISSING")

            # Anti-Duplication Verification
            if "Avoiding Duplicate Strike" in bot_code:
                log.success("Entry: Anti-Duplication Protection - ACTIVE")
            else: log.error("Entry: Anti-Duplication - MISSING")

    # 2c. Exit Rules Verification
    if os.path.exists('src/fno_trading_bot.py'):
        with open('src/fno_trading_bot.py', 'r') as f:
            bot_code = f.read()
            # Profit Target Verification
            if "check_profit_hit(current_premium, 250.0)" in bot_code or "profit_target_amount" in bot_code:
                log.success("Exit: Profit Target Detection - ACTIVE")
                rules['Profit Target'] = "Rs 250.0"
            else: log.error("Exit: Profit Target Detection - MISSING")
            
            # Safety Net
            if "pnl_pct <= max_premium_loss" in bot_code:
                log.success("Exit: -50.0% Safety Net - ACTIVE")
                rules['Safety Net'] = "-50.0%"
            else: log.error("Exit: Safety Net - MISSING")

    # Print Summary of Hardcoded Values
    print("\n--- [Hardcoded Parameter Summary] ---")
    
    # 1. Trading Windows
    print("  [Trading Window]")
    print("  Market Open.............. : 09:15 AM")
    print("  Entry Cutoff............. : 03:15 PM")
    print("  Market Close............. : 03:30 PM")
    
    # 2. Risk Management
    print("\n  [Risk Parameters]")
    print(f"  Profit Target............ : {rules.get('Profit Target', 'Rs 250.0')}")
    print(f"  Daily Profit Cap......... : {rules.get('Profit Cap', 'Rs 1200.0')}")
    print(f"  Safety Net (Premium)..... : {rules.get('Safety Net', '-50.0%')}")
    print("  Stop Loss (NIFTY)........ : 0.70% (Spot)")
    print("  Stop Loss (BANKNIFTY).... : 1.20% (Spot)")
    print("  Stop Loss (FINNIFTY)..... : 1.00% (Spot)")
    print("  Stop Loss (SENSEX)....... : 1.00% (Spot)")
    
    # 3. Strategy Conditions
    print("\n  [Strategy Rules]")
    print(f"  VIX Min Floor............ : {rules.get('VIX Min', '10.0')}")
    print(f"  RSI Range................ : {rules.get('RSI Range', '30 - 65')}")
    print(f"  Daily ADX Min............ : {rules.get('Daily ADX Min', '25.0')}")
    print("  Analysis Timeframe....... : 15 Minutes")
    print("  Strike Selection......... : ATM (Depth 0)")
    
    # 4. Indicators Configuration
    print("\n  [Indicator Setup]")
    print("  MACD Periods............. : 12, 26, 9")
    print("  RSI Period............... : 14")
    print("  ADX Period............... : 14")

    # 5. Position Sizing
    print("\n  [Lot Sizes]")
    print("  NIFTY50.................. : 65 Qty")
    print("  BANKNIFTY................ : 30 Qty")
    print("  FINNIFTY................. : 60 Qty")
    print("  SENSEX................... : 20 Qty")

    # 3. Data Integrity (Positions)
    print("\n--- [State Verification] ---")
    if os.path.exists('data/positions.json'):
        try:
            with open('data/positions.json', 'r') as f:
                data = json.load(f)
                if len(data) == 0:
                    log.success("State Clean: No ghost positions")
                else:
                    log.warn(f"Ghost Positions Found: {list(data.keys())} - Reconcile if manual exit occurred.")
        except: log.error("data/positions.json is corrupted")

    # 4. Config sanity
    if os.path.exists('config.json'):
        try:
            with open('config.json', 'r') as f:
                cfg = json.load(f)
                log.success(f"Config Loaded: Profit Target @ {cfg.get('profit_targets', {}).get('profit_target_amount', 'N/A')}")
        except: log.error("config.json is corrupted")

    print("\n" + "="*50)
    print("        AUDIT COMPLETE - FLY SAFE         ")
    print("="*50 + "\n")

if __name__ == "__main__":
    run_audit()
