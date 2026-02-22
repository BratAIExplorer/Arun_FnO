# F&O Trading Bot - Complete Implementation

## 🎯 Overview

Your F&O trading bot is ready! This implementation combines:
- **MACD + RSI + ADX Strategy** with 8 mandatory entry conditions
- **Live mStock API Integration** for real-time data and orders
- **VIX-Adjusted Stop Losses** (0.70% Nifty, 1.00% BankNifty)
- **Risk Management** (15% profit targets, 3% daily loss limit)
- **Paper Trading Mode** for safe testing
- **Live Dashboard** for monitoring trades and P&L

## 📋 Your Trading Conditions

### Entry Conditions (8 Checks)
✅ **1. No duplicate positions** - Max 1 position per underlying  
✅ **2. Trading hours** - 9:25 AM - 2:30 PM IST only  
✅ **3. VIX filter** - Skip if VIX < 10  
✅ **4. Daily MACD** - Bullish (CE) or Bearish (PE)  
✅ **5. Daily candle** - Green (CE) or Red (PE)  
✅ **6. 15m MACD crossover** - Fresh crossover required  
✅ **7. 15m RSI** - Must be in 45-65 range  
✅ **8. 15m ADX** - Must be > 25 for trend strength  

3. **MACD Reversal** - Safety exit confirmed on candle close

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Setup Credentials (Auto-loaded)
Your mStock credentials are automatically loaded from `.env` file.  
**No UI input needed!** ✅

`.env` file:
```env
API_KEY=your_mstock_api_key
API_SECRET=your_mstock_api_secret
CLIENT_CODE=your_client_code
PASSWORD=your_password
```

### 3. Launch Dashboard (Recommended)
```bash
run_dashboard.bat
```
Or:
```bash
streamlit run dashboard.py
```

### 4. Run Trading Bot
```bash
python main.py
```

### 5. Run Backtest (Optional)
```python
from backtest import run_backtest
from src.trading_config import TradingConfig
import pandas as pd

# Load your historical data
daily_nifty = pd.read_csv('data/nifty50_daily.csv', parse_dates=['datetime'], index_col='datetime')
intraday_nifty = pd.read_csv('data/nifty50_15min.csv', parse_dates=['datetime'], index_col='datetime')
vix_data = pd.read_csv('data/vix_15min.csv', parse_dates=['datetime'], index_col='datetime')['vix']

# Prepare data dictionaries
daily_data = {"NIFTY50": daily_nifty}
intraday_data = {"NIFTY50": intraday_nifty}

# Run backtest
config = TradingConfig()
bot = run_backtest(daily_data, intraday_data, vix_data, config, "backtest_results.csv")
```

## 📁 Project Structure

```
.
├── src/
│   ├── indicators.py         # MACD, RSI, ADX calculations
│   ├── trading_config.py     # All trading parameters
│   ├── fno_trading_bot.py    # Main trading engine
│   ├── market_data.py        # mStock API integration
│   └── utils.py              # Helper functions
│
├── main.py                   # Paper trading execution
├── backtest.py               # Backtesting module
│
├── logs/                     # Trading logs and results
├── data/                     # Historical data (for backtest)
├── files/                    # Documentation from your original setup
│
├── .env                      # API credentials (create this)
├── credentials.json          # mStock access token (auto-generated)
└── README.md                 # This file
```

## ⚙️ Configuration

Edit `src/trading_config.py` to customize:

```python
# Capital Management
initial_capital: float = 100000.0
daily_loss_limit_pct: float = 3.0

# Trading Hours
market_open: time = time(9, 25)
entry_cutoff: time = time(14, 30)

# VIX Configuration
vix_min_threshold: float = 10.0

# Profit Target
profit_target_pct: float = 15.0

# Indicator Periods
rsi_period: int = 14
adx_min: float = 25.0
```

## 📊 Example Usage - Custom Script

```python
from src.fno_trading_bot import FnOTradingBot, TradeType
from src.trading_config import TradingConfig
from src.market_data import MStockAPI
from src.utils import setup_logging
import pandas as pd

# Setup
setup_logging("my_trading.log")
config = TradingConfig()
api = MStockAPI()
bot = FnOTradingBot(config)

# Get market data (example for Nifty)
daily_df = api.get_historical_data("NIFTY 50", "NSE", "26000", "day", days=60)
intraday_df = api.get_historical_data("NIFTY 50", "NSE", "26000", "15minute", days=10)

# Calculate indicators (handled automatically in backtest.py)
# ... add indicators to dataframes ...

# Check entry conditions
vix = 15.0  # Get from API
current_idx = len(intraday_df) - 1

if bot.check_entry_conditions_ce("NIFTY50", daily_df, intraday_df, current_idx, vix):
    # Entry signal detected!
    current_spot = intraday_df.iloc[-1]['close']
    current_premium = current_spot * 0.015  # Approx, use actual option premium
    
    bot.enter_trade(
        "NIFTY50",
        TradeType.CE,
        current_premium,
        current_spot,
        vix,
        current_idx
    )

# Check exit conditions
if "NIFTY50" in bot.positions:
    position = bot.positions["NIFTY50"]
    current_spot = intraday_df.iloc[-1]['close']
    current_premium = current_spot * 0.015
    
    exit_reason = bot.check_exit_conditions(
        position,
        current_premium,
        current_spot,
        current_idx,
        intraday_df
    )
    
    if exit_reason:
        bot.exit_trade("NIFTY50", current_premium, current_spot, exit_reason)

# Print summary
bot.print_account_summary()
```

## 🔍 Monitoring & Logs

### Console Output
```
✅ NIFTY50: All CE entry conditions met | RSI=52.45 | ADX=28.32 | VIX=15.20
🔵 ENTRY: NIFTY50_CALL_20260130104532 | Type: CALL | Premium: Rs 75.50 | Spot: 19537.45 | SL: 0.70% | Qty: 50
🟢 EXIT: NIFTY50_CALL_20260130104532 | Reason: Profit Target 15%+ | Exit Premium: Rs 86.80 | P&L: Rs 565.00 (+15.23%) | Capital: Rs 100,565.00
```

### Log Files
- `logs/trading_bot_YYYYMMDD.log` - Detailed execution logs
- `logs/paper_trades_YYYYMMDD_HHMMSS.csv` - Trade history CSV

### CSV Output Format
```csv
Position_ID,Underlying,Type,Entry_Time,Entry_Price,Entry_Spot,SL_Percentage,Exit_Time,Exit_Price,Exit_Spot,Exit_Reason,P&L,P&L_%,VIX
NIFTY50_CALL_20260130104532,NIFTY50,CALL,2026-01-30 10:45:32,75.5,19537.45,0.70,2026-01-30 11:12:18,86.8,19585.32,Profit Target 15%+,565.0,15.23,15.2
```

## ⚠️ Important Notes

### Paper Trading Mode
- **Current status**: `main.py` runs in PAPER TRADING mode
- No actual orders are placed to broker
- Simulates premium as ~1.5% of spot price
- Safe for testing without risking capital

### Before Going Live
1. ✅ Run paper trading for minimum 2 weeks
2. ✅ Verify entry/exit signals match your expectations
3. ✅ Check RSI/MACD values against TradingView
4. ✅ Test during different VIX conditions
5. ✅ Start with small capital (1-2 lakh)
6. ✅ Update `main.py` to use actual option premiums (not simulated)
7. ✅ Implement actual order placement (currently paper mode)

### Customization for Live Trading
To enable live order placement:
1. Get actual instrument tokens for options from mStock API
2. Fetch real option premium prices (not simulated spot * 0.015)
3. Update `market_data.py` `place_order()` to actually execute orders
4. Add option strike selection logic
5. Test with 1 lot first

## 🎓 Testing Checklist

- [ ] Paper trade for 2 weeks minimum
- [ ] Backtest on 60+ days of historical data
- [ ] Win rate > 60%
- [ ] Verify daily loss limit works
- [ ] Test SL triggers correctly
- [ ] Confirm profit targets hit
- [ ] Check trading hours enforcement
- [ ] Validate MACD crossover detection
- [ ] Test VIX adjustment logic

## 📞 Support

For issues or questions:
1. Check logs in `logs/` directory
2. Review `files/` folder documentation
3. Verify `.env` credentials are correct
4. Ensure market is open during testing

## 🔐 Risk Disclaimer

This is an algorithmic trading bot. Key risks:
- **Capital Loss**: Can lose entire capital if not monitored
- **Slippage**: Actual execution may differ from signals
- **API Failures**: Network/broker issues can prevent trades
- **Strategy Risk**: Past performance ≠ future results
- **Daily Loss Limit**: Hard stop at 3% daily loss

**Always start with paper trading and small capital!**

## 📈 Expected Performance

Based on backtests (see `files/` documentation):
- **Win Rate**: 65-70%
- **Profit Factor**: 3.0-3.5x
- **Monthly Return**: 15-25% (in optimal conditions)
- **Max Drawdown**: 2-5%

**Note**: Live trading typically achieves 50-70% of backtest returns due to slippage and execution delays.

---

**Ready to trade! 🚀**

Start with:
```bash
python main.py
```

Good luck and trade safely! 📊
