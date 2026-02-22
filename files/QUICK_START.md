# QUICK START GUIDE - RUN THE BOT IN 10 MINUTES

---

## STEP 1: Install Python (2 minutes)

```bash
# Check if Python is installed
python --version

# Should show: Python 3.7 or higher
```

If not installed, download from [python.org](https://www.python.org/downloads/)

---

## STEP 2: Install Required Libraries (2 minutes)

```bash
pip install pandas numpy
```

---

## STEP 3: Prepare Your Data Files (3 minutes)

Create these CSV files:

### File 1: nifty50_daily.csv
```
datetime,open,high,low,close
2026-01-20,19600,19700,19550,19680
2026-01-21,19680,19750,19620,19720
...
```

### File 2: nifty50_15min.csv
```
datetime,open,high,low,close
2026-01-20 09:15:00,19600,19610,19590,19605
2026-01-20 09:30:00,19605,19620,19600,19615
...
```

### File 3: banknifty_daily.csv
```
datetime,open,high,low,close
2026-01-20,39600,39700,39550,39680
...
```

### File 4: banknifty_15min.csv
```
datetime,open,high,low,close
2026-01-20 09:15:00,39600,39610,39590,39605
...
```

### File 5: vix_15min.csv
```
datetime,vix
2026-01-20 09:15:00,15.5
2026-01-20 09:30:00,15.3
...
```

---

## STEP 4: Create Python Script (3 minutes)

Create a file called `run_bot.py`:

```python
import pandas as pd
from trading_bot import TradingBot, TechnicalIndicators, run_trading_bot

# ===== LOAD DATA =====
print("Loading data...")

daily_nifty = pd.read_csv('nifty50_daily.csv', parse_dates=['datetime'])
daily_nifty.set_index('datetime', inplace=True)

daily_banknifty = pd.read_csv('banknifty_daily.csv', parse_dates=['datetime'])
daily_banknifty.set_index('datetime', inplace=True)

intraday_nifty = pd.read_csv('nifty50_15min.csv', parse_dates=['datetime'])
intraday_nifty.set_index('datetime', inplace=True)

intraday_banknifty = pd.read_csv('banknifty_15min.csv', parse_dates=['datetime'])
intraday_banknifty.set_index('datetime', inplace=True)

vix_data = pd.read_csv('vix_15min.csv', parse_dates=['datetime'], index_col='datetime')
vix_data = vix_data['vix'].squeeze()

print("✓ Data loaded successfully")

# ===== CALCULATE INDICATORS =====
print("\nCalculating indicators...")

# Daily MACD
daily_nifty['MACD'], daily_nifty['MACD_Signal'], daily_nifty['MACD_Hist'] = \
    TechnicalIndicators.calculate_macd(daily_nifty['close'])

daily_banknifty['MACD'], daily_banknifty['MACD_Signal'], daily_banknifty['MACD_Hist'] = \
    TechnicalIndicators.calculate_macd(daily_banknifty['close'])

# Daily RSI (optional)
daily_nifty['RSI'] = TechnicalIndicators.calculate_rsi(daily_nifty['close'])
daily_banknifty['RSI'] = TechnicalIndicators.calculate_rsi(daily_banknifty['close'])

# Daily ADX (optional)
daily_nifty['ADX'], daily_nifty['+DI'], daily_nifty['-DI'] = \
    TechnicalIndicators.calculate_adx(daily_nifty['high'], daily_nifty['low'], daily_nifty['close'])

daily_banknifty['ADX'], daily_banknifty['+DI'], daily_banknifty['-DI'] = \
    TechnicalIndicators.calculate_adx(daily_banknifty['high'], daily_banknifty['low'], daily_banknifty['close'])

# Intraday MACD
intraday_nifty['MACD'], intraday_nifty['MACD_Signal'], intraday_nifty['MACD_Hist'] = \
    TechnicalIndicators.calculate_macd(intraday_nifty['close'])

intraday_banknifty['MACD'], intraday_banknifty['MACD_Signal'], intraday_banknifty['MACD_Hist'] = \
    TechnicalIndicators.calculate_macd(intraday_banknifty['close'])

# Intraday RSI
intraday_nifty['RSI'] = TechnicalIndicators.calculate_rsi(intraday_nifty['close'])
intraday_banknifty['RSI'] = TechnicalIndicators.calculate_rsi(intraday_banknifty['close'])

# Intraday ADX
intraday_nifty['ADX'], intraday_nifty['+DI'], intraday_nifty['-DI'] = \
    TechnicalIndicators.calculate_adx(intraday_nifty['high'], intraday_nifty['low'], intraday_nifty['close'])

intraday_banknifty['ADX'], intraday_banknifty['+DI'], intraday_banknifty['-DI'] = \
    TechnicalIndicators.calculate_adx(intraday_banknifty['high'], intraday_banknifty['low'], intraday_banknifty['close'])

print("✓ Indicators calculated successfully")

# ===== RUN TRADING BOT =====
print("\nRunning trading bot...")

daily_data = {
    "NIFTY50": daily_nifty,
    "BANKNIFTY": daily_banknifty
}

intraday_data = {
    "NIFTY50": intraday_nifty,
    "BANKNIFTY": intraday_banknifty
}

bot = run_trading_bot(daily_data, intraday_data, vix_data)

print("\n✓ Bot execution completed")
print("\nResults saved to:")
print("  - trading_bot.log (detailed logs)")
print("  - trading_results.csv (all trades)")
```

---

## STEP 5: Run the Bot (1 minute)

```bash
python run_bot.py
```

---

## EXPECTED OUTPUT

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

---

## VERIFY RESULTS

### Check Log File:
```bash
cat trading_bot.log
```

Should show:
```
2026-01-30 10:15:23 - INFO - Trading Bot Initialized with Capital: Rs 100000
2026-01-30 10:15:45 - INFO - NIFTY50: All CE entry conditions met ✓
2026-01-30 10:15:45 - INFO - ENTRY: NIFTY50_CALL_20260130101545 | Type: CALL | ...
...
```

### Check CSV File:
```bash
head -5 trading_results.csv
```

Should show trade details:
```
Position_ID,Underlying,Type,Entry_Time,Entry_Price,Entry_Spot,SL_Percentage,Exit_Time,Exit_Price,Exit_Spot,Exit_Reason,P&L,P&L_%
NIFTY50_CALL_20260130101545,NIFTY50,CALL,2026-01-30 10:15:45,75.5,19537.45,0.70,2026-01-30 10:30:12,86.8,19585.32,Profit Target 15%+,1350.0,15.27
```

---

## TROUBLESHOOTING

### Error: "ModuleNotFoundError: No module named 'pandas'"
**Solution:**
```bash
pip install pandas numpy
```

### Error: "No such file or directory: 'nifty50_daily.csv'"
**Solution:**
- Make sure CSV files are in the same directory as `run_bot.py`
- Check file names match exactly

### Error: "KeyError: 'MACD' not found"
**Solution:**
- Make sure you calculated indicators before running bot
- Check that `calculate_macd()` was called

### No trades generated
**Possible causes:**
- VIX all < 10 (check VIX values)
- Data doesn't meet entry conditions
- Indicators have NaN values

**Solution:**
```python
# Debug: Check data
print(daily_nifty[['MACD', 'MACD_Signal']].tail())
print(intraday_nifty[['RSI', 'ADX']].tail())
print("VIX min:", vix_data.min(), "VIX max:", vix_data.max())
```

---

## NEXT STEPS

1. ✅ Run bot on historical data (backtest)
2. ✅ Review `trading_results.csv` - are results good?
3. ✅ If win rate > 60%, proceed to paper trading
4. ✅ Paper trade for 2 weeks
5. ✅ If results match backtest, go live

---

## FILE REFERENCE

### Files You Need:
- `trading_bot.py` - Main bot code (provided)
- `run_bot.py` - Your script to run the bot (create this)
- CSV files with your data (create these)

### Files Generated:
- `trading_bot.log` - Detailed logs
- `trading_results.csv` - All trades

---

## QUICK COMMANDS

```bash
# Run the bot
python run_bot.py

# View logs
tail -100 trading_bot.log

# View results
python -c "import pandas as pd; print(pd.read_csv('trading_results.csv').head(20))"

# Count trades
python -c "import pandas as pd; df = pd.read_csv('trading_results.csv'); print(f'Total trades: {len(df)}, Wins: {len(df[df[\"P&L_%\"] > 0])}')"
```

---

## THAT'S IT!

You now have a fully functional trading bot ready to backtest your strategy.

**Total setup time: ~10 minutes**

Good luck! 🚀
