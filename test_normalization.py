import sys
import os
from datetime import datetime

# Add root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.symbol_master import SymbolMaster

def test_normalization():
    print("--- Testing Symbol Normalization ---")
    sm = SymbolMaster()
    
    # 1. Weekly Nifty
    expiry_10feb = datetime.strptime("10Feb2026", "%d%b%Y")
    sym1 = sm.get_symbol("NIFTY50", expiry_10feb, 25500, "PE")
    print(f"NIFTY 10Feb2026 25500 PE -> {sym1}")
    # Based on extract_master_samples, 10Feb2026 NIFTY uses YYMDD format
    # Expecting: NIFTY2621025500PE
    assert "26210" in sym1
    print("PASS: Weekly Nifty format found")

    # 2. Monthly BankNifty
    expiry_24feb = datetime.strptime("24Feb2026", "%d%b%Y")
    sym2 = sm.get_symbol("BANKNIFTY", expiry_24feb, 60200, "PE")
    print(f"BANKNIFTY 24Feb2026 60200 PE -> {sym2}")
    # Expecting: BANKNIFTY26FEB60200PE (Monthly uses YYMMM)
    assert "26FEB" in sym2
    print("PASS: Monthly BankNifty format found")

    # 3. Weekly Algorithmic Fallback (if not in master)
    # 17Feb is weekly
    expiry_17feb = datetime.strptime("17Feb2026", "%d%b%Y")
    # Using a fake strike that might not be in master to trigger fallback
    sym3 = sm.get_symbol("NIFTY50", expiry_17feb, 99999, "CE")
    print(f"NIFTY 17Feb2026 99999 CE (Fallback) -> {sym3}")
    assert "26217" in sym3
    print("PASS: Weekly Fallback format correct")

if __name__ == "__main__":
    try:
        test_normalization()
        print("\nSYMBOL NORMALIZATION VERIFIED!")
    except Exception as e:
        print(f"\nTEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
