
import os
import sys
import logging
from datetime import datetime
from src.market_data import MStockAPI

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_formats():
    api = MStockAPI()
    
    # NIFTY Expiry: 05 FEB 2026 (Thursday)
    # Strike: 25750 (ATM approx)
    nifty_strike = 25750
    # NIFTY Expiry: 05 FEB 2026 (Weekly) & 26 FEB 2026 (Monthly)
    # Strike: 25750
    nifty_variations = [
        "NIFTY2621225750PE",     # Wk: Next Week (Feb 12)
        "FINNIFTY2621027800PE",  # FinNifty Wk (Feb 10) - Spot ~27800
        "NIFTY2620525750PE",     # Retry Current Wk
        "NIFTY26FEB25750PE",     # Monthly (Control)
    ]
    
    print("\n--- Testing NIFTY Formats ---")
    for symbol in nifty_variations:
        print(f"Checking {symbol}...", end=" ")
        quote = api.get_quote(symbol, "NFO")
        if quote and 'error' not in quote:
             print("[FOUND]")
             print(quote)
        else:
             print("[FAILED]")

    # BANKNIFTY Expiry: 25 FEB 2026 (Monthly Last Wed)
    # Strike: 60200
    bn_strike = 60200
    bn_variations = [
        "BANKNIFTY25FEB2660200PE", # DDMMMYY
        "BANKNIFTY26FEB60200PE",   # YYMMM (Monthly)
        "BANKNIFTY2622560200PE",   # YYMDD
    ]

    print("\n--- Testing BANKNIFTY Formats ---")
    for symbol in bn_variations:
        print(f"Checking {symbol}...", end=" ")
        quote = api.get_quote(symbol, "NFO")
        if quote and 'error' not in quote:
             print("[FOUND]")
             print(quote)
        else:
             print("[FAILED]")

if __name__ == "__main__":
    test_formats()
