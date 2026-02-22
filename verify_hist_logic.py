import pandas as pd
import numpy as np
from datetime import datetime
from src.fno_trading_bot import FnOTradingBot
from src.trading_config import config
from src.trading_models import TradeType

def test_histogram_logic():
    bot = FnOTradingBot(config)
    
    # Bypass non-histogram checks
    bot.config.can_enter_new_position = lambda x: True
    bot.config.vix_min_threshold = 0.0
    bot.daily_pnl = 0.0
    bot.positions = {}
    bot.closed_trades = []
    
    def get_mock_df(hist_prev, hist_curr, macd_val, signal_val):
        data = {
            'close': [100, 101],
            'MACD': [0, macd_val],
            'MACD_Signal': [0, signal_val],
            'MACD_Hist': [hist_prev, hist_curr],
            'RSI': [50, 50],
            'ADX': [30, 30]
        }
        return pd.DataFrame(data)

    def get_mock_daily():
        return pd.DataFrame({'ADX': [30]})

    print("\n--- TESTING CE LOGIC (Bullish) ---")
    
    # 1. Dark Green (Valid)
    df = get_mock_df(1.0, 1.5, 10, 8.5) # Hist: 1.5 > 1.0 > 0
    result = bot.check_entry_conditions_ce("TEST", get_mock_daily(), df, 1, 15.0)
    print(f"CE Dark Green (1.0 -> 1.5): {'PASS' if result else 'FAIL'}")

    # 2. Light Green (Invalid)
    df = get_mock_df(2.0, 1.5, 10, 8.5) # Hist: 1.5 < 2.0 (Fading)
    result = bot.check_entry_conditions_ce("TEST", get_mock_daily(), df, 1, 15.0)
    print(f"CE Light Green (2.0 -> 1.5): {'PASS' if result else 'FAIL'}")

    # 3. Negative (Invalid)
    df = get_mock_df(-1.0, -0.5, 8.5, 9.0) # Hist: -0.5 < 0
    result = bot.check_entry_conditions_ce("TEST", get_mock_daily(), df, 1, 15.0)
    print(f"CE Negative (-1.0 -> -0.5): {'PASS' if result else 'FAIL'}")

    print("\n--- TESTING PE LOGIC (Bearish) ---")
    
    # 1. Dark Red (Valid)
    df = get_mock_df(-1.0, -1.5, 8.5, 10) # Hist: -1.5 < -1.0 < 0
    result = bot.check_entry_conditions_pe("TEST", get_mock_daily(), df, 1, 15.0)
    print(f"PE Dark Red (-1.0 -> -1.5): {'PASS' if result else 'FAIL'}")

    # 2. Light Red (Invalid)
    df = get_mock_df(-2.0, -1.5, 8.5, 10) # Hist: -1.5 > -2.0 (Fading)
    result = bot.check_entry_conditions_pe("TEST", get_mock_daily(), df, 1, 15.0)
    print(f"PE Light Red (-2.0 -> -1.5): {'PASS' if result else 'FAIL'}")

    # 3. Positive (Invalid)
    df = get_mock_df(1.0, 0.5, 10.5, 10) # Hist: 0.5 > 0
    result = bot.check_entry_conditions_pe("TEST", get_mock_daily(), df, 1, 15.0)
    print(f"PE Positive (1.0 -> 0.5): {'PASS' if result else 'FAIL'}")

if __name__ == "__main__":
    test_histogram_logic()
