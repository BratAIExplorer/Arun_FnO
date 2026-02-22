"""
Final Verification: Test SymbolMaster Generated Symbols with Live API
"""

from src.market_data import MStockAPI
from src.symbol_master import SymbolMaster
from datetime import date
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def verify_live():
    print("="*60)
    print("FINAL LIVE VERIFICATION")
    print("="*60)
    
    # 1. Initialize API
    try:
        api = MStockAPI()
        print("API Initialized")
    except Exception as e:
        print(f"API Init Failed: {e}")
        return

    # 2. Initialize Master
    master = SymbolMaster()
    print("SymbolMaster Initialized")
    
    # 3. Generate Symbol (Algorithmic)
    # Target: NIFTY 26 APR 2026 24000 CE (Monthly)
    expiry = date(2026, 4, 30) # 30th April 2026
    symbol = master.get_symbol("NIFTY50", expiry, 24000, "CE")
    
    print(f"\nGenerated Symbol: {symbol}")
    
    if not symbol:
        print("FAILED: Failed to generate symbol")
        return
        
    # 4. Check against API
    print(f"Checking with Mstock API...")
    quote = api.get_quote(symbol, "NFO")
    
    if quote:
        print(f"\nSUCCESS! Symbol '{symbol}' is valid and tradeable.")
        print(f"   LTP: {quote.get('last_price')}")
        print(f"   Close: {quote.get('close_price')}")
    else:
        print(f"\nFAILED. API rejected symbol '{symbol}'")

if __name__ == "__main__":
    verify_live()
