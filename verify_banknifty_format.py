"""
Verify BANKNIFTY Symbol Format
"""

from src.market_data import MStockAPI
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_symbol(api, symbol, exchange="NFO"):
    print(f"Testing: {symbol}...")
    quote = api.get_quote(symbol, exchange)
    
    if quote:
        print(f"SUCCESS! Found: {symbol}")
        print(f"FULL QUOTE DATA: {quote}")
        return True
    else:
        print(f"FAILED: {symbol}")
        return False

def main():
    try:
        api = MStockAPI()
    except:
        return

    # Check typical BankNifty variations for Feb 2026
    # Expiry 24 Feb 2026 (Monthly or Weekly?)
    # Strike 60000
    
    strikes = [60000, 59900]
    
    # FORMAT 1: YYMMM (26FEB) - Monthly standard
    # FORMAT 2: DDMMM (24FEB) - Weekly style
    
    print("="*60)
    print("TESTING BANKNIFTY FORMATS")
    print("="*60)
    
    for strike in strikes:
        formats = [
             # YYMMM Standard
            f"BANKNIFTY26FEB{strike}CE",
            
            # DDMMM (Specific Date)
            f"BANKNIFTY24FEB{strike}CE",
             
            # DDMMMYY
            f"BANKNIFTY24FEB26{strike}CE",
            
            # NSE Standard format sometimes used
            f"BANKNIFTY26FEB26{strike}CE"
        ]
        
        for fmt in formats:
            if test_symbol(api, fmt):
                print(f"VALID FORMAT FOUND: {fmt}")
                return

if __name__ == "__main__":
    main()
