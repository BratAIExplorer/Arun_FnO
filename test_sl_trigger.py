import sys
import os
from datetime import datetime

# Add root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.trading_models import Position, TradeType, ExitReason
from src.trading_config import config
from src.fno_trading_bot import FnOTradingBot

def test_safety_net():
    print("--- Testing Safety Net Logic ---")
    
    # 1. Normal Position with loss
    pos1 = Position(
        position_id="test_1",
        underlying="NIFTY50",
        trade_type=TradeType.CE,
        entry_time=datetime.now(),
        entry_price=100.0,
        entry_underlying_price=25000.0,
        lot_size=50,
        sl_percentage=0.7,
        vix_at_entry=15.0
    )
    
    # Simulate LTP = 40 (60% loss, should trigger safety net -50%)
    pnl_pct_1 = pos1.calculate_pnl_pct(40.0)
    print(f"Pos 1 P&L%: {pnl_pct_1:.2f}%")
    
    # Mock bot for config access
    bot = FnOTradingBot(config)
    bot.config.max_premium_loss_percent = -50.0
    
    reason1 = bot.check_exit_conditions(pos1, 40.0, 25000.0, 0, None)
    print(f"Pos 1 Exit Reason: {reason1}")
    assert reason1 == ExitReason.STOP_LOSS
    print("PASS: Safety Net Triggered at -60%")

    # 2. Position with entry_price = 0
    pos2 = Position(
        position_id="test_2",
        underlying="BANKNIFTY",
        trade_type=TradeType.PE,
        entry_time=datetime.now(),
        entry_price=0.0,
        entry_underlying_price=50000.0,
        lot_size=30,
        sl_percentage=1.2,
        vix_at_entry=15.0
    )
    
    # Simulate LTP = 1.0 (Value near zero, should return -99.9% sentinel)
    pnl_pct_2 = pos2.calculate_pnl_pct(1.0)
    print(f"Pos 2 P&L%: {pnl_pct_2:.2f}%")
    
    reason2 = bot.check_exit_conditions(pos2, 1.0, 50000.0, 0, None)
    print(f"Pos 2 Exit Reason: {reason2}")
    assert reason2 == ExitReason.STOP_LOSS
    print("PASS: Safety Net Triggered for zero entry price with low LTP")

    # 3. Profitable Position (but below target)
    pos3 = Position(
        position_id="test_3",
        underlying="NIFTY50",
        trade_type=TradeType.CE,
        entry_time=datetime.now(),
        entry_price=100.0,
        entry_underlying_price=25000.0,
        lot_size=50,
        sl_percentage=0.7,
        vix_at_entry=15.0
    )
    
    # P&L = (101 - 100) * 50 = 50. Target is 250 or 500. Should not exit.
    reason3 = bot.check_exit_conditions(pos3, 101.0, 25005.0, 0, None)
    print(f"Pos 3 (Minor Profit) Exit Reason: {reason3}")
    assert reason3 is None
    print("PASS: No exit for minor profitable position")

if __name__ == "__main__":
    try:
        test_safety_net()
        print("\nALL TESTS PASSED!")
    except Exception as e:
        print(f"\nTEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
