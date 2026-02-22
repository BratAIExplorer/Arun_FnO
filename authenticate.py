"""
Simple authentication script for mStock API
"""
import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from src.market_data import MStockAPI

print("="*60)
print("  mStock API Authentication")
print("="*60)
print()
print("You will receive an OTP on your registered mobile/email.")
print("Please have it ready.")
print()
input("Press Enter to continue...")
print()

try:
    api = MStockAPI()
    success = api.refresh_token()
    
    if success:
        print()
        print("="*60)
        print("  SUCCESS! Authentication Complete")
        print("="*60)
        print()
        print("Your access token has been saved.")
        print()
        print("Next steps:")
        print("  1. Refresh your dashboard in the browser")
        print("  2. You should now see 'Connection: ONLINE'")
        print("  3. Start trading with START_BOT.bat")
        print()
    else:
        print()
        print("="*60)
        print("  Authentication Failed")
        print("="*60)
        print()
        print("Please check:")
        print("  - Your .env file has correct credentials")
        print("  - You entered the correct OTP")
        print("  - Your internet connection is working")
        print()

except Exception as e:
    print()
    print("="*60)
    print("  ERROR")
    print("="*60)
    print()
    print(f"Error: {str(e)}")
    print()

input("Press any key to exit...")
