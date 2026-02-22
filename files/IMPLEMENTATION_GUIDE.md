# TRADING BOT IMPLEMENTATION GUIDE
## Complete Setup & Usage Instructions

---

## TABLE OF CONTENTS
1. [Bot Architecture](#bot-architecture)
2. [Installation & Setup](#installation--setup)
3. [Data Preparation](#data-preparation)
4. [Running the Bot](#running-the-bot)
5. [Understanding Output](#understanding-output)
6. [Integration with Live Data](#integration-with-live-data)
7. [Troubleshooting](#troubleshooting)

---

## BOT ARCHITECTURE

### Core Components:

```
TradingBot (Main Class)
├── Entry Logic
│   ├── check_entry_conditions_ce() - Call options
│   ├── check_entry_conditions_pe() - Put options
│   ├── _check_macd_crossover_ce()
│   └── _check_macd_crossover_pe()
├── Exit Logic
│   ├── process_position_exits()
│   ├── _check_macd_reversal()
│   ├── check_sl_hit()
│   └── check_profit_hit()
├── Re-entry Logic
│   ├── check_reentry_allowed()
│   └── check_fresh_macd_signal()
├── Utility Functions
│   ├── get_account_summary()
│   ├── save_trades_to_csv()
│   └── print_account_summary()
└── Position (Data Class)
    └── Contains all trade details

TechnicalIndicators (Static Class)
├── calculate_macd()
├── calculate_rsi()
└── calculate_adx()
```

---

## INSTALLATION & SETUP

### Required Libraries:

```bash
pip install pandas numpy
```

### Python Version:
- Python 3.7+

### File Structure:
```
your_project/
├── trading_bot.py          # Main bot code
├── data_loader.py          # (Optional) Load data
├── config.py               # Configuration file
├── trading_bot.log         # Auto-generated logs
└── trading_results.csv     # Auto-generated trade log
```

---

## DATA PREPARATION

### What Data You Need:

#### 1. Daily OHLC Data (for daily confirmations)
```
Index: DateTime
Columns: open, high, low, close
```

#### 2. 15-Minute OHLC Data (for entry/exit signals)
```
Index: DateTime (timestamp for each 15-min candle)
Columns: open, high, low, close
```

#### 3. VIX Data
```
Index: DateTime (aligned with 15-min candles)
Values: VIX levels
```

### Example: Loading Data with Pandas

```python
import pandas as pd
from trading_bot import TradingBot, TechnicalIndicators

# Load daily data
daily_nifty = pd.read_csv('nifty50_daily.csv', parse_dates=['datetime'])
daily_nifty.set_index('datetime', inplace=True)

daily_banknifty = pd.read_csv('banknifty_daily.csv', parse_dates=['datetime'])
daily_banknifty.set_index('datetime', inplace=True)

# Load 15-minute data
intraday_nifty = pd.read_csv('nifty50_15min.csv', parse_dates=['datetime'])
intraday_nifty.set_index('datetime', inplace=True)

intraday_banknifty = pd.read_csv('banknifty_15min.csv', parse_dates=['datetime'])
intraday_banknifty.set_index('datetime', inplace=True)

# Load VIX data (same frequency as intraday)
vix_data = pd.read_csv('vix_15min.csv', parse_dates=['datetime'])
vix_data.set_index('datetime', inplace=True)
vix_data = vix_data['vix'].squeeze()  # Convert to Series

# Ensure all data is aligned
print("Daily Nifty shape:", daily_nifty.shape)
print("Intraday Nifty shape:", intraday_nifty.shape)
print("VIX shape:", vix_data.shape)
```

### Step 1: Calculate Indicators

```python
# For Daily Data
for col in ['high', 'low', 'close']:
    if col not in daily_nifty.columns:
        raise ValueError(f"{col} not found in daily data")

# Calculate MACD (daily)
daily_nifty['MACD'], daily_nifty['MACD_Signal'], daily_nifty['MACD_Hist'] = \
    TechnicalIndicators.calculate_macd(daily_nifty['close'])

daily_banknifty['MACD'], daily_banknifty['MACD_Signal'], daily_banknifty['MACD_Hist'] = \
    TechnicalIndicators.calculate_macd(daily_banknifty['close'])

# Calculate RSI (daily) - optional but useful
daily_nifty['RSI'] = TechnicalIndicators.calculate_rsi(daily_nifty['close'])
daily_banknifty['RSI'] = TechnicalIndicators.calculate_rsi(daily_banknifty['close'])

# Calculate ADX (daily) - optional but useful
daily_nifty['ADX'], daily_nifty['+DI'], daily_nifty['-DI'] = \
    TechnicalIndicators.calculate_adx(daily_nifty['high'], daily_nifty['low'], daily_nifty['close'])

daily_banknifty['ADX'], daily_banknifty['+DI'], daily_banknifty['-DI'] = \
    TechnicalIndicators.calculate_adx(daily_banknifty['high'], daily_banknifty['low'], daily_banknifty['close'])

# For Intraday (15-min) Data
# Calculate MACD (15-min)
intraday_nifty['MACD'], intraday_nifty['MACD_Signal'], intraday_nifty['MACD_Hist'] = \
    TechnicalIndicators.calculate_macd(intraday_nifty['close'])

intraday_banknifty['MACD'], intraday_banknifty['MACD_Signal'], intraday_banknifty['MACD_Hist'] = \
    TechnicalIndicators.calculate_macd(intraday_banknifty['close'])

# Calculate RSI (15-min)
intraday_nifty['RSI'] = TechnicalIndicators.calculate_rsi(intraday_nifty['close'])
intraday_banknifty['RSI'] = TechnicalIndicators.calculate_rsi(intraday_banknifty['close'])

# Calculate ADX (15-min)
intraday_nifty['ADX'], intraday_nifty['+DI'], intraday_nifty['-DI'] = \
    TechnicalIndicators.calculate_adx(intraday_nifty['high'], intraday_nifty['low'], intraday_nifty['close'])

intraday_banknifty['ADX'], intraday_banknifty['+DI'], intraday_banknifty['-DI'] = \
    TechnicalIndicators.calculate_adx(intraday_banknifty['high'], intraday_banknifty['low'], intraday_banknifty['close'])

print("Indicators calculated successfully ✓")
```

---

## RUNNING THE BOT

### Simple Example (Backtest Mode):

```python
from trading_bot import run_trading_bot

# Prepare data dictionaries
daily_data = {
    "NIFTY50": daily_nifty,
    "BANKNIFTY": daily_banknifty
}

intraday_data = {
    "NIFTY50": intraday_nifty,
    "BANKNIFTY": intraday_banknifty
}

# Run the bot
bot = run_trading_bot(
    daily_data=daily_data,
    intraday_data=intraday_data,
    vix_data=vix_data
)

# Results automatically saved to:
# - trading_bot.log (detailed logs)
# - trading_results.csv (all trades)
```

### Advanced Usage with Live Data:

```python
from trading_bot import TradingBot, TradeType, TechnicalIndicators
import time
from datetime import datetime

class LiveTradingBot:
    """Wrapper for live trading"""
    
    def __init__(self, initial_capital=100000):
        self.bot = TradingBot(initial_capital=initial_capital)
    
    def process_tick(self, underlying, current_data, current_vix):
        """
        Process a single tick of data
        
        Parameters:
        -----------
        underlying: str - "NIFTY50" or "BANKNIFTY"
        current_data: dict - {
            'daily_ohlc': DataFrame last row,
            'intraday_ohlc': DataFrame last row,
            'intraday_all': DataFrame all rows,
            'current_premium_ce': float,
            'current_premium_pe': float,
            'current_spot': float
        }
        current_vix: float - Current VIX level
        """
        
        daily_data = current_data['daily_ohlc']
        intraday_data = current_data['intraday_all']
        current_idx = len(intraday_data) - 1
        
        current_spot = current_data['current_spot']
        current_premium_ce = current_data['current_premium_ce']
        current_premium_pe = current_data['current_premium_pe']
        
        # Process exits
        if underlying in self.bot.positions:
            position = self.bot.positions[underlying]
            current_premium = current_premium_ce if position.trade_type.name == 'CE' else current_premium_pe
            
            self.bot.process_position_exits(
                underlying=underlying,
                current_premium=current_premium,
                current_underlying_price=current_spot,
                intraday_data=intraday_data,
                current_row_idx=current_idx
            )
        
        # Process entries
        if self.bot.check_reentry_allowed(underlying):
            if self.bot.check_entry_conditions_ce(
                underlying=underlying,
                daily_data=daily_data,
                intraday_data=intraday_data,
                current_row_idx=current_idx,
                vix=current_vix
            ):
                self.bot.enter_trade(
                    underlying=underlying,
                    trade_type=TradeType.CE,
                    entry_price=current_premium_ce,
                    entry_underlying_price=current_spot,
                    entry_strike=daily_data['close'],
                    vix=current_vix
                )
            
            if self.bot.check_entry_conditions_pe(
                underlying=underlying,
                daily_data=daily_data,
                intraday_data=intraday_data,
                current_row_idx=current_idx,
                vix=current_vix
            ):
                self.bot.enter_trade(
                    underlying=underlying,
                    trade_type=TradeType.PE,
                    entry_price=current_premium_pe,
                    entry_underlying_price=current_spot,
                    entry_strike=daily_data['close'],
                    vix=current_vix
                )

# Usage
live_bot = LiveTradingBot(initial_capital=100000)

# In your main trading loop:
# while market_is_open:
#     current_data = get_current_market_data()
#     current_vix = get_current_vix()
#     live_bot.process_tick("NIFTY50", current_data, current_vix)
```

---

## UNDERSTANDING OUTPUT

### Console Output:

```
====================================================
ACCOUNT SUMMARY
====================================================
Initial Capital:     Rs 100,000.00
Current Capital:     Rs 179,585.00
Total P&L:           Rs 79,585.00
Total P&L %:         79.59%
Total Trades:        87
Winning Trades:      58
Losing Trades:       29
Win Rate:            66.67%
Open Positions:      0
====================================================
```

### Log File (trading_bot.log):

```
2026-01-30 10:15:23 - INFO - Trading Bot Initialized with Capital: Rs 100000
2026-01-30 10:15:45 - INFO - NIFTY50: All CE entry conditions met ✓
2026-01-30 10:15:45 - INFO - ENTRY: NIFTY50_CALL_20260130101545 | Type: CALL | Premium: Rs 75.5 | Spot: 19537.45 | SL: 0.70% | Target: 15%
2026-01-30 10:30:12 - INFO - EXIT: NIFTY50_CALL_20260130101545 | Reason: Profit Target 15%+ | Exit Premium: Rs 86.8 | P&L: Rs 1350.00 (15.27%) | Capital: Rs 101350.00
```

### CSV File (trading_results.csv):

```
Position_ID,Underlying,Type,Entry_Time,Entry_Price,Entry_Spot,SL_Percentage,Exit_Time,Exit_Price,Exit_Spot,Exit_Reason,P&L,P&L_%
NIFTY50_CALL_20260130101545,NIFTY50,CALL,2026-01-30 10:15:45,75.5,19537.45,0.70,2026-01-30 10:30:12,86.8,19585.32,Profit Target 15%+,1350.0,15.27
NIFTY50_PUT_20260130104532,NIFTY50,PUT,2026-01-30 10:45:32,68.2,19520.10,0.70,2026-01-30 10:52:18,78.5,19480.22,SL Hit,-1020.0,-11.83
```

---

## INTEGRATION WITH LIVE DATA

### Option 1: Using a Broker's API (NSE/BSE)

```python
# Example: Using Zerodha Kite API
from kiteconnect import KiteConnect
from trading_bot import TradingBot, TradeType
import pandas as pd

class ZerodhaIntegration:
    def __init__(self, api_key, access_token):
        self.kite = KiteConnect(api_key=api_key)
        self.kite.set_access_token(access_token)
        self.bot = TradingBot(initial_capital=100000)
    
    def get_historical_data(self, instrument_token, from_date, to_date, interval):
        """Fetch historical data"""
        return self.kite.historical_data(
            instrument_token=instrument_token,
            from_date=from_date,
            to_date=to_date,
            interval=interval
        )
    
    def place_order(self, symbol, transaction_type, quantity, order_type='MIS'):
        """Place order on broker"""
        return self.kite.place_order(
            tradingsymbol=symbol,
            exchange='NFO',
            transaction_type=transaction_type,
            quantity=quantity,
            order_type=order_type,
            variety='regular'
        )
    
    def get_ltp(self, instrument_token):
        """Get last traded price"""
        quote = self.kite.quote(instrument_tokens=[instrument_token])
        return quote[instrument_token]['last_price']
```

### Option 2: Using CSV with Real-time Updates

```python
import pandas as pd
from datetime import datetime
import time

class RealTimeDataHandler:
    def __init__(self):
        self.daily_nifty = pd.read_csv('nifty50_daily.csv', index_col=0)
        self.intraday_nifty = pd.read_csv('nifty50_15min.csv', index_col=0)
    
    def update_intraday_data(self, new_candle):
        """Add new 15-min candle"""
        self.intraday_nifty = pd.concat([self.intraday_nifty, new_candle], ignore_index=False)
        self.intraday_nifty = self.intraday_nifty.tail(1000)  # Keep last 1000 candles
        return self.intraday_nifty
    
    def update_daily_data(self, new_daily_candle):
        """Update daily candle if new day"""
        today = datetime.now().date()
        last_date = pd.Timestamp(self.daily_nifty.index[-1]).date()
        
        if today > last_date:
            self.daily_nifty = pd.concat([self.daily_nifty, new_daily_candle], ignore_index=False)
        else:
            self.daily_nifty.iloc[-1] = new_daily_candle
        
        return self.daily_nifty
```

---

## TROUBLESHOOTING

### Common Issues & Solutions:

#### Issue 1: "No entry signals generated"
**Causes:**
- Data doesn't have calculated indicators (MACD, RSI, ADX)
- Indicators have NaN values (need warmup candles)
- VIX is < 10

**Solution:**
```python
# Check for NaN values
print("MACD NaN count:", daily_nifty['MACD'].isna().sum())
print("RSI NaN count:", intraday_nifty['RSI'].isna().sum())

# Drop NaN values or use only after warmup
daily_nifty = daily_nifty.dropna()
intraday_nifty = intraday_nifty.dropna()

# Check VIX
print("VIX min:", vix_data.min())
print("VIX max:", vix_data.max())
```

#### Issue 2: "Position not closing on SL"
**Causes:**
- SL calculation is wrong
- Position.check_sl_hit() logic error

**Solution:**
```python
# Verify SL calculation
position = bot.positions['NIFTY50']
print(f"Entry spot: {position.entry_underlying_price}")
print(f"SL percentage: {position.sl_percentage}")
sl_level = position.entry_underlying_price * (1 - position.sl_percentage / 100)
print(f"SL level: {sl_level}")

# Test manually
current_spot = 19400
print(f"Current spot: {current_spot}")
print(f"SL hit? {position.check_sl_hit(current_spot)}")
```

#### Issue 3: "Capital decreasing rapidly"
**Causes:**
- Win rate is below 50% (strategy not working)
- Entry conditions are too loose
- Slippage is higher than assumed

**Solution:**
```python
# Check win rate
summary = bot.get_account_summary()
print(f"Win rate: {summary['win_rate']:.2f}%")

# If < 60%, review entry logic
# Tighten filters: ADX > 30, RSI narrower range, etc.

# Check P&L distribution
for position in bot.closed_positions:
    print(f"{position.underlying} | {position.trade_type.value} | {position.pnl_percentage:.2f}%")
```

#### Issue 4: "Indicator calculation is slow"
**Causes:**
- Calculating indicators for every tick
- Using inefficient pandas operations

**Solution:**
```python
# Pre-calculate all indicators before running bot
# Only update last row during live trading

def update_indicator_last_row(df):
    """Update only the last row"""
    last_row = df.tail(1)
    # Recalculate for last 30 rows
    subset = df.tail(30).copy()
    subset['MACD'], subset['MACD_Signal'], _ = \
        TechnicalIndicators.calculate_macd(subset['close'])
    # Update original
    df.loc[df.index[-30:], ['MACD', 'MACD_Signal']] = \
        subset[['MACD', 'MACD_Signal']]
    return df
```

---

## CHECKLIST BEFORE LIVE TRADING

- [ ] Data loaded correctly (no missing values)
- [ ] Indicators calculated (MACD, RSI, ADX)
- [ ] Entry conditions verified on historical data
- [ ] Exit conditions working correctly
- [ ] Daily loss limit = 3% of capital
- [ ] VIX filter in place (< 10 = skip)
- [ ] Time filter in place (9:25am - 2:30pm)
- [ ] No duplicate position logic working
- [ ] SL calculation correct
- [ ] Profit target calculation correct
- [ ] Logs being generated
- [ ] CSV export working
- [ ] Paper trading done for 2 weeks
- [ ] All trades reviewed
- [ ] Ready for live trading

---

## SUPPORT & DEBUGGING

### To enable verbose logging:

```python
import logging

# Set to DEBUG for more detailed logs
logging.basicConfig(level=logging.DEBUG)

# Run bot
bot = run_trading_bot(daily_data, intraday_data, vix_data)
```

### To track specific trades:

```python
# Print all closed positions
for position in bot.closed_positions:
    print(f"\n{position.position_id}")
    print(f"Entry: {position.entry_time} @ Rs {position.entry_price}")
    print(f"Exit: {position.exit_time} @ Rs {position.exit_price}")
    print(f"Reason: {position.exit_reason}")
    print(f"P&L: Rs {position.pnl:.2f} ({position.pnl_percentage:.2f}%)")
```

---

## SUMMARY

Your trading bot is now ready to use. It implements:

✅ All entry conditions (MACD, RSI, ADX, daily confirmation)
✅ All exit conditions (SL, profit target, technical reversal, EOD)
✅ Re-entry logic with fresh signal check
✅ Daily loss limit enforcement
✅ VIX-adjusted stop losses
✅ Complete trade logging
✅ Account summary tracking

**Next Steps:**
1. Load your data
2. Calculate indicators
3. Run the bot
4. Review results
5. Paper trade for 2 weeks
6. Go live when confident
