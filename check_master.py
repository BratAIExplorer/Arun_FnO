import json
from datetime import datetime

# Load master file
with open('nfo_master.csv', 'r') as f:
    data = json.load(f)

# Filter NIFTY options
nifty = [x for x in data if x.get('symbol') == 'NIFTY' and x.get('instrumenttype') == 'OPTIDX']

# Get unique expiries
expiries = sorted(set([x['expiry'] for x in nifty]))

print("Available NIFTY expiries (first 10):")
for e in expiries[:10]:
    dt = datetime.strptime(e, "%d%b%Y")
    print(f"  {e} ({dt.strftime('%Y-%m-%d')} - {dt.strftime('%A')})")

print("\nChecking for specific symbol: NIFTY2621025600CE")
found = [x for x in data if x.get('name') == 'NIFTY2621025600CE']
if found:
    print(f"  FOUND! Token: {found[0].get('token')}")
    print(f"  Full data: {found[0]}")
else:
    print("  NOT FOUND in master file")

# Check BANKNIFTY
print("\nAvailable BANKNIFTY expiries (first 10):")
banknifty = [x for x in data if x.get('symbol') == 'BANKNIFTY' and x.get('instrumenttype') == 'OPTIDX']
bn_expiries = sorted(set([x['expiry'] for x in banknifty]))
for e in bn_expiries[:10]:
    dt = datetime.strptime(e, "%d%b%Y")
    print(f"  {e} ({dt.strftime('%Y-%m-%d')} - {dt.strftime('%A')})")

print("\nChecking for specific symbol: BANKNIFTY26FEB60100CE")
found_bn = [x for x in data if x.get('name') == 'BANKNIFTY26FEB60100CE']
if found_bn:
    print(f"  FOUND! Token: {found_bn[0].get('token')}")
else:
    print("  NOT FOUND in master file")
