import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from src.option_selector import OptionSelector

def test_strike_selection():
    print("Testing Strike Selection Logic...\n")
    
    # Test Data
    underlying = "NIFTY50"
    spot_price = 26523.45  # ATM should be 26500 (Round to nearest 50)
    
    expected_atm = 26500
    interval = 50
    
    print(f"Underlying: {underlying}")
    print(f"Spot Price: {spot_price}")
    print(f"Expected ATM: {expected_atm}")
    print(f"Interval: {interval}\n")
    
    # Test ATM (Depth 0)
    print("--- Testing ATM (Depth 0) ---")
    strike_ce_0, _ = OptionSelector.select_option(underlying, spot_price, "CE", depth=0)
    strike_pe_0, _ = OptionSelector.select_option(underlying, spot_price, "PE", depth=0)
    
    print(f"CE Strike (0): {strike_ce_0} (Expected: {expected_atm})")
    print(f"PE Strike (0): {strike_pe_0} (Expected: {expected_atm})")
    
    if strike_ce_0 == expected_atm and strike_pe_0 == expected_atm:
        print("[OK] ATM Test PASSED")
    else:
        print("[FAIL] ATM Test FAILED")
        
    print("\n")
    
    # Test ITM 1 (Depth 1)
    # CE ITM = ATM - Interval (Lower Strike) -> 26450
    # PE ITM = ATM + Interval (Higher Strike) -> 26550
    print("--- Testing ITM 1 (Depth 1) ---")
    strike_ce_1, _ = OptionSelector.select_option(underlying, spot_price, "CE", depth=1)
    strike_pe_1, _ = OptionSelector.select_option(underlying, spot_price, "PE", depth=1)
    
    expected_ce_1 = expected_atm - interval
    expected_pe_1 = expected_atm + interval
    
    print(f"CE Strike (1): {strike_ce_1} (Expected: {expected_ce_1})")
    print(f"PE Strike (1): {strike_pe_1} (Expected: {expected_pe_1})")
    
    if strike_ce_1 == expected_ce_1 and strike_pe_1 == expected_pe_1:
        print("[OK] ITM 1 Test PASSED")
    else:
        print("[FAIL] ITM 1 Test FAILED")

    print("\n")

    # Test ITM 2 (Depth 2)
    # CE ITM = ATM - 2*Interval -> 26400
    # PE ITM = ATM + 2*Interval -> 26600
    print("--- Testing ITM 2 (Depth 2) ---")
    strike_ce_2, _ = OptionSelector.select_option(underlying, spot_price, "CE", depth=2)
    strike_pe_2, _ = OptionSelector.select_option(underlying, spot_price, "PE", depth=2)
    
    expected_ce_2 = expected_atm - (2 * interval)
    expected_pe_2 = expected_atm + (2 * interval)
    
    print(f"CE Strike (2): {strike_ce_2} (Expected: {expected_ce_2})")
    print(f"PE Strike (2): {strike_pe_2} (Expected: {expected_pe_2})")
    
    if strike_ce_2 == expected_ce_2 and strike_pe_2 == expected_pe_2:
        print("[OK] ITM 2 Test PASSED")
    else:
        print("[FAIL] ITM 2 Test FAILED")

if __name__ == "__main__":
    test_strike_selection()
