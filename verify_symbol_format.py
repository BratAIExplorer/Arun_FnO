"""
Verify Mstock Symbol Format
Tries to fetch quotes for various symbol formats to find the correct one for F&O
"""

from src.market_data import MStockAPI
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_symbol(api, symbol, exchange="NFO"):
    print(f"\nTesting symbol: {symbol} on {exchange}...")
    quote = api.get_quote(symbol, exchange)
    
    if quote:
        print(f"SUCCESS! Format accepted.")
        print(f"LTP: {quote.get('last_price')}")
        print(f"Close: {quote.get('close_price')}")
        return True
    else:
        print(f"FAILED. Invalid format or symbol not found.")
        return False

def main():
    print("Initializing MStock API...")
    try:
        api = MStockAPI()
    except Exception as e:
        print(f"Error checking API: {e}")
        print("Make sure .env and credentials.json are correct")
        return

    # Test parameters
    index = "NIFTY"
    strike = 24000
    opt_type = "CE"
    
    # AMBIGUITY CHECK:
    # 26 Feb 2026: Day=26, Year=26.
    # April 2026 Monthly Expiry: 30 April 2026 (Thursday).
    # Day = 30
    # Year = 26
    
    # If format is DDMMM: NIFTY30APR...
    # If format is YYMMM: NIFTY26APR...
    
    test_formats = [
        # Format DDMMM: NIFTY30APR...
        f"{index}30APR{strike}{opt_type}",
        
        # Format YYMMM: NIFTY26APR...
        f"{index}26APR{strike}{opt_type}",
        
        # Format: NIFTY + 26 (Year) + APR + Strike
        f"{index}26APR{strike}{opt_type}",
        
        # Test NIFTY 50 explicitly
        f"NIFTY 5026APR{strike}{opt_type}",
        f"NIFTY 5030APR{strike}{opt_type}"
    ]
    
    print("="*60)
    print("TESTING SYMBOL FORMATS (APRIL 2026 CHECK)")
    print("="*60)

    
    for fmt in test_formats:
        if test_symbol(api, fmt):
            print(f"FOUND VALID FORMAT: '{fmt}'")
            if "26FEB26" in fmt or "12FEB26" in fmt:
                print("Format identified as: DDMMMYY")
            elif "26FEB" in fmt and "26FEB2" not in fmt:
                 print("Format identified as: DDMMM (Implied Year?)")


if __name__ == "__main__":
    main()
