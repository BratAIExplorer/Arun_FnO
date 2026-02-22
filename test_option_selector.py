"""
Test Option Selector - Verify Weekly vs Monthly Expiry
"""

from src.option_selector import OptionSelector
from datetime import datetime

print("="*60)
print("OPTION SELECTOR TEST")
print("="*60)
print(f"Current Date: {datetime.now().strftime('%d-%b-%Y %A')}")
print()

# Test Nifty50 (Weekly)
print("NIFTY50 (Weekly Thursday Expiry)")
print("-" * 60)
nifty_spot = 19537.45
strike, symbol = OptionSelector.select_option("NIFTY50", nifty_spot, "CE")
print(f"Spot Price: {nifty_spot}")
print(f"ATM Strike: {strike}")
print(f"Symbol: {symbol}")
print(f"[TEST] Weekly expiry on Thursday")
print()

# Test BankNifty (Monthly)
print("BANKNIFTY (Monthly Last Wednesday Expiry)")
print("-" * 60)
bn_spot = 45123.75
strike, symbol = OptionSelector.select_option("BANKNIFTY", bn_spot, "PE")
print(f"Spot Price: {bn_spot}")
print(f"ATM Strike: {strike}")
print(f"Symbol: {symbol}")
print(f"[TEST] Monthly expiry on last Wednesday")
print()

print("="*60)
print("TEST COMPLETE")
print("="*60)
