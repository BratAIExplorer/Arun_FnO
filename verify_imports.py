import sys
import os

# Add src to path
sys.path.insert(0, os.path.dirname(__file__))

try:
    print("Testing imports...")
    from src.fno_trading_bot import FnOTradingBot
    from src.persistence import StateManager
    from src.trading_models import Position, TradeType, ExitReason
    
    print("[OK] All imports successful! No circular dependency detected.")
    
    # Try creating a StateManager instance or calling its methods
    print("Testing StateManager...")
    StateManager.load_positions()
    print("[OK] StateManager test successful.")
    
    # Try creating a dummy position
    print("Testing Position model...")
    from datetime import datetime
    pos = Position(
        position_id="test",
        underlying="NIFTY50",
        trade_type=TradeType.CE,
        entry_time=datetime.now(),
        entry_price=100.0,
        entry_underlying_price=25000.0,
        lot_size=50,
        sl_percentage=1.0,
        vix_at_entry=15.0
    )
    print(f"[OK] Position model test successful: {pos.position_id}")
    
except ImportError as e:
    print(f"[ERROR] ImportError: {e}")
    sys.exit(1)
except Exception as e:
    print(f"[ERROR] Unexpected error: {e}")
    sys.exit(1)
