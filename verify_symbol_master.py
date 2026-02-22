
import logging
import sys
import os

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("VERIFY")

# Add src to path
sys.path.append(os.getcwd())

from src.symbol_master import SymbolMaster
from src.option_selector import OptionSelector

def verify():
    print("--- Verifying Symbol Master ---")
    
    # 1. Initialize Symbol Master
    sm = SymbolMaster()
    if not sm.initialized:
        print("FAIL: SymbolMaster not initialized")
        return
        
    print(f"Loaded Expiries for BANKNIFTY: {sm.expiries.get('BANKNIFTY')}")
    
    # 2. Test Get Expiry via OptionSelector
    expiry = OptionSelector.get_expiry("BANKNIFTY")
    print(f"OptionSelector Expiry: {expiry} (Type: {type(expiry)})")
    
    if not expiry:
        print("FAIL: No expiry found")
        return

    # 3. Test Symbol Lookup (ATM)
    spot = 45000
    strike = OptionSelector.get_atm_strike(spot, "BANKNIFTY")
    print(f"ATM Strike for {spot}: {strike}")
    
    # Check if strike exists in master
    # We need to check if the specific strike exists for the expiry
    # If not, let's try to find *any* valid strike near it to prove lookup works
    # Or just try looking it up.
    
    symbol_ce = OptionSelector.get_option_symbol("BANKNIFTY", strike, "CE", expiry)
    symbol_pe = OptionSelector.get_option_symbol("BANKNIFTY", strike, "PE", expiry)
    
    print(f"Symbol CE: {symbol_ce}")
    print(f"Symbol PE: {symbol_pe}")
    
    if "???" in symbol_ce or "???" in symbol_pe:
        print("FAIL: Symbol lookup returned fallback")
    else:
        print("SUCCESS: Symbol found!")

if __name__ == "__main__":
    verify()
