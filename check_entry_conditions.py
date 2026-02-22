"""
Diagnostic Script: Check Current Entry Conditions
Helps identify which specific conditions are blocking entry signals
"""

import sys
import os
import json
sys.path.insert(0, os.path.dirname(__file__))

from src.market_data import MStockAPI
from src.indicators import TechnicalIndicators
from src.trading_config import config
from src.utils import now_ist
import pandas as pd

def load_symbols():
    """Load symbols from config.json"""
    try:
        with open('config.json', 'r') as f:
            cfg = json.load(f)
        
        symbols = {}
        if 'symbols' in cfg:
            for symbol_name, symbol_data in cfg['symbols'].items():
                if symbol_name == 'comment':
                    continue
                symbols[symbol_name] = (symbol_data['exchange'], symbol_data['token'])
        return symbols
    except Exception as e:
        print(f"Error loading config: {e}")
        return {
            "NIFTY 50": ("NSE", "26000"),
            "NIFTY BANK": ("NSE", "26009")
        }

def check_entry_diagnostics():
    """Check all entry conditions and show which ones pass/fail"""
    
    api = MStockAPI()
    symbols_config = load_symbols()
    
    print("\n" + "="*80)
    print("ENTRY CONDITION DIAGNOSTIC REPORT")
    print(f"Time: {now_ist().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80 + "\n")
    
    for symbol, (exchange, instrument_token) in symbols_config.items():
        underlying = symbol.replace(" ", "")
        
        print(f"\n{'='*80}")
        print(f"{underlying}")
        print(f"{'='*80}\n")
        
        try:
            # Fetch data
            daily_df = api.get_historical_data(symbol, exchange, instrument_token, "day", days=60)
            intraday_df = api.get_historical_data(symbol, exchange, instrument_token, "15minute", days=10)
            
            if daily_df is None or intraday_df is None:
                print(f"Could not fetch data for {underlying}")
                continue
                
            if len(daily_df) < 2 or len(intraday_df) < 2:
                print(f"Insufficient data for {underlying}")
                continue
            
            # Get current spot
            quote = api.get_quote(symbol, exchange)
            current_spot = quote.get('last_price', 0) if quote else 0
            
            # Create live candle
            if current_spot > 0:
                last_close = intraday_df.iloc[-1]['close']
                live_candle = pd.DataFrame({
                    'open': [last_close],
                    'high': [max(last_close, current_spot)],
                    'low': [min(last_close, current_spot)],
                    'close': [current_spot]
                }, index=[now_ist()])
                intraday_df = pd.concat([intraday_df, live_candle])
            
            # Calculate indicators
            daily_df['MACD'], daily_df['MACD_Signal'], _ = TechnicalIndicators.calculate_macd(daily_df['close'])
            daily_df['RSI'] = TechnicalIndicators.calculate_rsi(daily_df['close'])
            
            intraday_df['MACD'], intraday_df['MACD_Signal'], _ = TechnicalIndicators.calculate_macd(intraday_df['close'])
            intraday_df['RSI'] = TechnicalIndicators.calculate_rsi(intraday_df['close'])
            intraday_df['ADX'], _, _ = TechnicalIndicators.calculate_adx(intraday_df['high'], intraday_df['low'], intraday_df['close'])
            
            # Get VIX
            vix_quote = api.get_quote("INDIA VIX", "NSE")
            vix = vix_quote.get('last_price', 15.0) if vix_quote else 15.0
            
            # Get current values
            daily_row = daily_df.iloc[-1]
            current_row = intraday_df.iloc[-1]
            prev_row = intraday_df.iloc[-2]
            
            current_time_dt = now_ist()
            current_time = current_time_dt.time()
            
            print(f"Spot Price: Rs {current_spot:,.2f}")
            print(f"VIX: {vix:.2f}\n")
            
            # Check each condition for CE (CALL)
            print("CALL (CE) ENTRY CONDITIONS:")
            print("-" * 80)
            
            conditions_ce = []
            
            # 1. Trading hours
            entry_allowed = config.can_enter_new_position(current_time)
            status = "PASS" if entry_allowed else "FAIL"
            conditions_ce.append(entry_allowed)
            print(f"1. Trading Hours (9:25-14:30): {status}")
            print(f"   Current time: {current_time}")
            
            # 2. VIX filter
            vix_pass = vix >= config.vix_min_threshold
            status = "PASS" if vix_pass else "FAIL"
            conditions_ce.append(vix_pass)
            print(f"2. VIX > {config.vix_min_threshold}: {status}")
            print(f"   VIX = {vix:.2f}")
            
            # 3. Daily MACD bullish
            daily_macd_bullish = daily_row['MACD'] > daily_row['MACD_Signal']
            status = "PASS" if daily_macd_bullish else "FAIL"
            conditions_ce.append(daily_macd_bullish)
            print(f"3. Daily MACD Bullish: {status}")
            print(f"   MACD = {daily_row['MACD']:.2f}, Signal = {daily_row['MACD_Signal']:.2f}")
            
            # 4. Daily candle green
            daily_green = daily_row['close'] > daily_row['open']
            status = "PASS" if daily_green else "FAIL"
            conditions_ce.append(daily_green)
            print(f"4. Daily Candle Green: {status}")
            print(f"   Open = {daily_row['open']:.2f}, Close = {daily_row['close']:.2f}")
            
            # 5. 15m MACD crossover bullish
            macd_crossover_bullish = (
                current_row['MACD'] > current_row['MACD_Signal'] and
                prev_row['MACD'] <= prev_row['MACD_Signal']
            )
            status = "PASS" if macd_crossover_bullish else "FAIL"
            conditions_ce.append(macd_crossover_bullish)
            print(f"5. 15m MACD Bullish Crossover: {status}")
            print(f"   Current: MACD = {current_row['MACD']:.2f}, Signal = {current_row['MACD_Signal']:.2f}")
            print(f"   Previous: MACD = {prev_row['MACD']:.2f}, Signal = {prev_row['MACD_Signal']:.2f}")
            
            # 6. 15m RSI in range
            rsi = current_row['RSI']
            rsi_ok = config.rsi_min <= rsi <= config.rsi_max
            status = "PASS" if rsi_ok else "FAIL"
            conditions_ce.append(rsi_ok)
            print(f"6. 15m RSI in Range ({config.rsi_min}-{config.rsi_max}): {status}")
            print(f"   RSI = {rsi:.2f}")
            
            # 7. 15m ADX > 25
            adx = current_row['ADX']
            adx_ok = adx > config.adx_min
            status = "PASS" if adx_ok else "FAIL"
            conditions_ce.append(adx_ok)
            print(f"7. 15m ADX > {config.adx_min}: {status}")
            print(f"   ADX = {adx:.2f}")
            
            # Summary
            print("\n" + "-" * 80)
            all_pass_ce = all(conditions_ce)
            if all_pass_ce:
                print("RESULT: ALL CONDITIONS MET - CALL ENTRY SIGNAL!")
            else:
                failed_count = sum(1 for c in conditions_ce if not c)
                print(f"RESULT: {failed_count} condition(s) failed - NO ENTRY SIGNAL")
            
            # Check each condition for PE (PUT)
            print("\n" + "="*80)
            print("PUT (PE) ENTRY CONDITIONS:")
            print("-" * 80)
            
            conditions_pe = []
            
            # Same for PE but opposite MACD/candle direction
            conditions_pe.append(entry_allowed)
            conditions_pe.append(vix_pass)
            
            # Daily MACD bearish
            daily_macd_bearish = daily_row['MACD'] < daily_row['MACD_Signal']
            status = "PASS" if daily_macd_bearish else "FAIL"
            conditions_pe.append(daily_macd_bearish)
            print(f"3. Daily MACD Bearish: {status}")
            print(f"   MACD = {daily_row['MACD']:.2f}, Signal = {daily_row['MACD_Signal']:.2f}")
            
            # Daily candle red
            daily_red = daily_row['close'] < daily_row['open']
            status = "PASS" if daily_red else "FAIL"
            conditions_pe.append(daily_red)
            print(f"4. Daily Candle Red: {status}")
            print(f"   Open = {daily_row['open']:.2f}, Close = {daily_row['close']:.2f}")
            
            # 15m MACD crossover bearish
            macd_crossover_bearish = (
                current_row['MACD'] < current_row['MACD_Signal'] and
                prev_row['MACD'] >= prev_row['MACD_Signal']
            )
            status = "PASS" if macd_crossover_bearish else "FAIL"
            conditions_pe.append(macd_crossover_bearish)
            print(f"5. 15m MACD Bearish Crossover: {status}")
            print(f"   Current: MACD = {current_row['MACD']:.2f}, Signal = {current_row['MACD_Signal']:.2f}")
            print(f"   Previous: MACD = {prev_row['MACD']:.2f}, Signal = {prev_row['MACD_Signal']:.2f}")
            
            conditions_pe.append(rsi_ok)
            conditions_pe.append(adx_ok)
            
            # Summary
            print("\n" + "-" * 80)
            all_pass_pe = all(conditions_pe)
            if all_pass_pe:
                print("RESULT: ALL CONDITIONS MET - PUT ENTRY SIGNAL!")
            else:
                failed_count = sum(1 for c in conditions_pe if not c)
                print(f"RESULT: {failed_count} condition(s) failed - NO ENTRY SIGNAL")
                
        except Exception as e:
            print(f"Error processing {underlying}: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*80)
    print("END OF DIAGNOSTIC REPORT")
    print("="*80 + "\n")

if __name__ == "__main__":
    check_entry_diagnostics()
