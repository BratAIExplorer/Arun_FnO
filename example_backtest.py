"""
Example Backtest Script
Run this to test the strategy on historical data
"""

import pandas as pd
from datetime import datetime
from src.trading_config import TradingConfig
from backtest import run_backtest, prepare_data_with_indicators
from src.utils import setup_logging


def main():
    """Run example backtest"""
    
    # Setup logging
    setup_logging("logs/backtest_example.log")
    
    print("="*70)
    print("F&O TRADING BOT - BACKTEST EXAMPLE")
    print("="*70)
    print("\n📋 This script demonstrates how to run a backtest")
    print("   You need to provide your own historical data files\n")
    
    # Check if data files exist
    data_files_needed = [
        "data/nifty50_daily.csv",
        "data/nifty50_15min.csv",
        "data/vix_15min.csv"
    ]
    
    print("📁 Required data files:")
    for file in data_files_needed:
        print(f"   - {file}")
    
    print("\n💡 Data format example:")
    print("   CSV with columns: datetime, open, high, low, close")
    print("   Index: datetime (parsed as datetime)")
    
    try:
        # Try to load data
        print("\n🔄 Loading data...")
        
        daily_nifty = pd.read_csv('data/nifty50_daily.csv', parse_dates=['datetime'], index_col='datetime')
        intraday_nifty = pd.read_csv('data/nifty50_15min.csv', parse_dates=['datetime'], index_col='datetime')
        vix_data = pd.read_csv('data/vix_15min.csv', parse_dates=['datetime'], index_col='datetime')['vix']
        
        print(f"   Daily data: {len(daily_nifty)} candles")
        print(f"   Intraday data: {len(intraday_nifty)} candles")
        print(f"   VIX data: {len(vix_data)} values")
        
        # Prepare data dictionaries
        daily_data = {"NIFTY50": daily_nifty}
        intraday_data = {"NIFTY50": intraday_nifty}
        
        # Initialize config
        config = TradingConfig()
        
        # Run backtest
        print("\n🚀 Starting backtest...")
        print(f"   Initial Capital: Rs {config.initial_capital:,.2f}")
        print(f"   Profit Target: {config.profit_target_pct}%")
        print(f"   Daily Loss Limit: {config.daily_loss_limit_pct}%")
        print(f"   RSI Range: {config.rsi_min}-{config.rsi_max}")
        print(f"   ADX Minimum: {config.adx_min}")
        
        bot = run_backtest(
            daily_data,
            intraday_data,
            vix_data,
            config,
            output_file=f"logs/backtest_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )
        
        print("\n✅ Backtest complete!")
        print(f"   Check logs/ folder for results")
        
    except FileNotFoundError as e:
        print(f"\n❌ Data file not found: {e}")
        print("\n📝 To run backtest:")
        print("   1. Create 'data/' folder")
        print("   2. Add your historical data CSV files:")
        print("      - data/nifty50_daily.csv")
        print("      - data/nifty50_15min.csv")
        print("      - data/vix_15min.csv")
        print("   3. Run this script again")
        print("\n💡 Data format example:")
        print("   datetime,open,high,low,close")
        print("   2024-01-01 09:15:00,19500.5,19520.2,19495.3,19515.8")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
