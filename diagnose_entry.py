"""
Entry Condition Diagnostic Tool
Shows which conditions PASS or FAIL for each symbol
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from src.market_data import MStockAPI
from src.indicators import TechnicalIndicators
from src.trading_config import config
from src.utils import now_ist
import pandas as pd
from datetime import datetime

def check_conditions():
    """Check entry conditions for all symbols"""
    
    api = MStockAPI()
    
    # Load symbols from config
    import json
    with open('config.json', 'r') as f:
        cfg = json.load(f)
    
    symbols_to_check = {}
    for symbol_name, symbol_data in cfg['symbols'].items():
        if symbol_name != 'comment':
            symbols_to_check[symbol_name] = (symbol_data['exchange'], symbol_data['token'], symbol_data['key'])
    
    output = []
    output.append("=" * 80)
    output.append("ENTRY CONDITION DIAGNOSTIC")
    output.append(f"Time: {now_ist().strftime('%Y-%m-%d %H:%M:%S')}")
    output.append("=" * 80)
    output.append("")
    
    for symbol_name, (exchange, token, key) in symbols_to_check.items():
        output.append("=" * 80)
        output.append(f"SYMBOL: {key}")
        output.append("=" * 80)
        output.append("")
        
        try:
            # Fetch data
            daily_df = api.get_historical_data(symbol_name, exchange, token, "day", days=60)
            intraday_df = api.get_historical_data(symbol_name, exchange, token, "15minute", days=10)
            
            if daily_df is None or intraday_df is None or len(daily_df) < 30 or len(intraday_df) < 30:
                output.append(f"ERROR: Insufficient data for {key}")
                output.append("")
                continue
            
            # Get spot price
            quote = api.get_quote(symbol_name, exchange)
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
            intraday_df['MACD'], intraday_df['MACD_Signal'], _ = TechnicalIndicators.calculate_macd(intraday_df['close'])
            intraday_df['RSI'] = TechnicalIndicators.calculate_rsi(intraday_df['close'])
            intraday_df['ADX'], _, _ = TechnicalIndicators.calculate_adx(intraday_df['high'], intraday_df['low'], intraday_df['close'])
            
            # Get VIX
            vix_quote = api.get_quote("INDIA VIX", "NSE")
            vix = vix_quote.get('last_price', 15.0) if vix_quote else 15.0
            
            # Current values
            daily_row = daily_df.iloc[-1]
            current_row = intraday_df.iloc[-1]
            prev_row = intraday_df.iloc[-2]
            
            current_time_dt = now_ist()
            current_hour = current_time_dt.hour
            current_minute = current_time_dt.minute
            
            output.append(f"Spot: Rs {current_spot:,.2f}")
            output.append(f"VIX: {vix:.2f}")
            output.append("")
            
            # Check CALL conditions
            output.append("-" * 80)
            output.append("CALL (CE) ENTRY CONDITIONS:")
            output.append("-" * 80)
            
            # 1. Trading hours (9:25 - 14:30)
            time_in_minutes = current_hour * 60 + current_minute
            entry_window_start = 9 * 60 + 25  # 9:25 AM
            entry_window_end = 14 * 60 + 30   # 2:30 PM
            entry_allowed = entry_window_start <= time_in_minutes < entry_window_end
            status = "PASS" if entry_allowed else "FAIL"
            output.append(f"1. Trading Hours (9:25-14:30): [{status}]")
            output.append(f"   Current time: {current_time_dt.strftime('%H:%M:%S')}")
            
            # 2. VIX
            vix_pass = vix >= config.vix_min_threshold
            status = "PASS" if vix_pass else "FAIL"
            output.append(f"2. VIX > {config.vix_min_threshold}: [{status}]")
            output.append(f"   VIX = {vix:.2f}")
            
            # 3. Daily MACD bullish
            daily_macd_bullish = daily_row['MACD'] > daily_row['MACD_Signal']
            status = "PASS" if daily_macd_bullish else "FAIL"
            output.append(f"3. Daily MACD Bullish: [{status}]")
            output.append(f"   MACD = {daily_row['MACD']:.2f}, Signal = {daily_row['MACD_Signal']:.2f}")
            
            # 4. Daily candle green
            daily_green = daily_row['close'] > daily_row['open']
            status = "PASS" if daily_green else "FAIL"
            output.append(f"4. Daily Candle Green: [{status}]")
            output.append(f"   Open = {daily_row['open']:.2f}, Close = {daily_row['close']:.2f}")
            
            # 5. 15m MACD crossover
            macd_cross_bullish = (current_row['MACD'] > current_row['MACD_Signal'] and 
                                 prev_row['MACD'] <= prev_row['MACD_Signal'])
            status = "PASS" if macd_cross_bullish else "FAIL"
            output.append(f"5. 15m MACD Bullish Crossover: [{status}]")
            output.append(f"   Current: MACD={current_row['MACD']:.2f}, Signal={current_row['MACD_Signal']:.2f}")
            output.append(f"   Previous: MACD={prev_row['MACD']:.2f}, Signal={prev_row['MACD_Signal']:.2f}")
            
            # 6. RSI
            rsi = current_row['RSI']
            rsi_ok = config.rsi_min <= rsi <= config.rsi_max
            status = "PASS" if rsi_ok else "FAIL"
            output.append(f"6. 15m RSI in Range ({config.rsi_min}-{config.rsi_max}): [{status}]")
            output.append(f"   RSI = {rsi:.2f}")
            
            # 7. ADX
            adx = current_row['ADX']
            adx_ok = adx > config.adx_min
            status = "PASS" if adx_ok else "FAIL"
            output.append(f"7. 15m ADX > {config.adx_min}: [{status}]")
            output.append(f"   ADX = {adx:.2f}")
            
            # Summary
            ce_conditions = [entry_allowed, vix_pass, daily_macd_bullish, daily_green, 
                           macd_cross_bullish, rsi_ok, adx_ok]
            output.append("")
            if all(ce_conditions):
                output.append(">>> RESULT: ALL CONDITIONS MET - CALL ENTRY SIGNAL! <<<")
            else:
                failed = sum(1 for c in ce_conditions if not c)
                output.append(f">>> RESULT: {failed} condition(s) failed - NO CALL SIGNAL <<<")
            
            output.append("")
            output.append("-" * 80)
            output.append("PUT (PE) ENTRY CONDITIONS:")
            output.append("-" * 80)
            
            # PUT conditions (opposite MACD/candle)
            daily_macd_bearish = daily_row['MACD'] < daily_row['MACD_Signal']
            status = "PASS" if daily_macd_bearish else "FAIL"
            output.append(f"3. Daily MACD Bearish: [{status}]")
            output.append(f"   MACD = {daily_row['MACD']:.2f}, Signal = {daily_row['MACD_Signal']:.2f}")
            
            daily_red = daily_row['close'] < daily_row['open']
            status = "PASS" if daily_red else "FAIL"
            output.append(f"4. Daily Candle Red: [{status}]")
            output.append(f"   Open = {daily_row['open']:.2f}, Close = {daily_row['close']:.2f}")
            
            macd_cross_bearish = (current_row['MACD'] < current_row['MACD_Signal'] and 
                                 prev_row['MACD'] >= prev_row['MACD_Signal'])
            status = "PASS" if macd_cross_bearish else "FAIL"
            output.append(f"5. 15m MACD Bearish Crossover: [{status}]")
            output.append(f"   Current: MACD={current_row['MACD']:.2f}, Signal={current_row['MACD_Signal']:.2f}")
            
            # Summary
            pe_conditions = [entry_allowed, vix_pass, daily_macd_bearish, daily_red,
                           macd_cross_bearish, rsi_ok, adx_ok]
            output.append("")
            if all(pe_conditions):
                output.append(">>> RESULT: ALL CONDITIONS MET - PUT ENTRY SIGNAL! <<<")
            else:
                failed = sum(1 for c in pe_conditions if not c)
                output.append(f">>> RESULT: {failed} condition(s) failed - NO PUT SIGNAL <<<")
            
            output.append("")
            
        except Exception as e:
            output.append(f"ERROR processing {key}: {str(e)}")
            output.append("")
    
    output.append("=" * 80)
    output.append("END OF DIAGNOSTIC")
    output.append("=" * 80)
    
    # Write to file
    with open('entry_diagnostic.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(output))
    
    print("Diagnostic complete! Check entry_diagnostic.txt")
    print("")
    print("Quick summary:")
    for line in output:
        if 'RESULT:' in line:
            print(line)

if __name__ == "__main__":
    check_conditions()
