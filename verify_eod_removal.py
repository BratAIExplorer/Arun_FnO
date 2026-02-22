
import sys
import os
from datetime import time
import json

# Add src to path
sys.path.insert(0, os.path.join(os.getcwd(), 'src'))

try:
    from trading_config import config
    print("LOG: TradingConfig loaded successfully")
    
    # Check if eod_exit exists in config object
    if hasattr(config, 'eod_exit'):
        print("ERROR: config still has eod_exit attribute")
    else:
        print("SUCCESS: eod_exit attribute removed from TradingConfig")
        
    # Check if should_force_exit method exists
    if hasattr(config, 'should_force_exit'):
        print("ERROR: config still has should_force_exit method")
    else:
        print("SUCCESS: should_force_exit method removed from TradingConfig")

    # Check config.json directly
    with open('config.json', 'r') as f:
        cfg = json.load(f)
        if 'eod_exit' in cfg.get('trading_hours', {}):
             print("ERROR: eod_exit still present in config.json")
        else:
             print("SUCCESS: eod_exit removed from config.json")

except Exception as e:
    print(f"ERROR during verification: {e}")
