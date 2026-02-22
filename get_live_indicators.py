
from src.market_data import MStockAPI
from src.indicators import TechnicalIndicators
from src.trading_config import config
import pandas as pd
from datetime import datetime
import pytz

def get_live_stats():
    api = MStockAPI()
    symbols = {
        "NIFTY 50": ("NSE", "26000", "NIFTY50"),
        "NIFTY BANK": ("NSE", "26009", "BANKNIFTY"),
        "NIFTY FIN SERVICE": ("NSE", "26037", "FINNIFTY"),
        "SENSEX": ("BSE", "51", "SENSEX")
    }
    
    results = {}
    
    print(f"Fetching Live Data as of {datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%H:%M:%S')} IST...")
    
    for name, (exchange, token, underlying) in symbols.items():
        try:
            # Get current spot
            quote = api.get_quote(name, exchange)
            current_spot = quote.get('last_price', 0) if quote else 0
            
            # Fetch intraday 15min data
            intraday_df = api.get_hybrid_history(name, exchange, token, "15minute", days=10)
            
            if intraday_df is not None and len(intraday_df) >= 50:
                # Calculate indicators
                macd, signal, hist = TechnicalIndicators.calculate_macd(intraday_df['close'])
                rsi = TechnicalIndicators.calculate_rsi(intraday_df['close'])
                adx, plus_di, minus_di = TechnicalIndicators.calculate_adx(intraday_df['high'], intraday_df['low'], intraday_df['close'])
                
                # Get latest values
                results[underlying] = {
                    "Spot": current_spot,
                    "RSI": rsi.iloc[-1],
                    "MACD": macd.iloc[-1],
                    "Signal": signal.iloc[-1],
                    "ADX": adx.iloc[-1]
                }
        except Exception as e:
            print(f"Error for {underlying}: {e}")
            
    # Print results in a nice table format
    print("\n" + "="*80)
    print(f"{'Index':<12} | {'Spot':<10} | {'RSI':<8} | {'ADX':<8} | {'MACD':<10} | {'Signal':<10}")
    print("-" * 80)
    for index, data in results.items():
        print(f"{index:<12} | {data['Spot']:<10.2f} | {data['RSI']:<8.2f} | {data['ADX']:<8.2f} | {data['MACD']:<10.2f} | {data['Signal']:<10.2f}")
    print("="*80)

if __name__ == "__main__":
    get_live_stats()
