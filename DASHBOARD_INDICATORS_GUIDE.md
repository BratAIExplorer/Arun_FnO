# 📊 Real-time Dashboard Indicators Guide

## ✅ What's Added to Your UI

Your dashboard now shows **LIVE market indicators** refreshing every **5 seconds**!

### 🔴 Real-time Indicators Panel

#### For NIFTY 50:
1. **Spot Price** (live)
2. **Daily Timeframe:**
   - RSI value
   - ADX value
   - MACD trend (🟢 Bullish / 🔴 Bearish)

3. **15-Min Timeframe:**
   - RSI value
   - ADX value
   - MACD trend (🟢 Bullish / 🔴 Bearish)

#### For BANK NIFTY:
1. **Spot Price** (live)
2. **Daily Timeframe:**
   - RSI value
   - ADX value
   - MACD trend (🟢 Bullish / 🔴 Bearish)

3. **15-Min Timeframe:**
   - RSI value
   - ADX value
   - MACD trend (🟢 Bullish / 🔴 Bearish)

#### VIX:
- **Current VIX value** (live)

---

## 🎯 Dashboard Layout

```
┌─────────────────────────────────────────────┐
│  F&O Trading Bot Dashboard                 │
│  🔄 Auto-refresh: 5 seconds                │
├─────────────────────────────────────────────┤
│  Bot Status | Credentials | Mode           │
├─────────────────────────────────────────────┤
│                                             │
│  🔴 LIVE MARKET INDICATORS                 │
│                                             │
│  ┌──────────────┬──────────────┐           │
│  │  NIFTY 50    │  BANK NIFTY  │           │
│  │  Spot: 19,537│  Spot: 45,123│           │
│  │              │              │           │
│  │  Daily:      │  Daily:      │           │
│  │  RSI: 54.32  │  RSI: 48.76  │           │
│  │  ADX: 32.15  │  ADX: 28.45  │           │
│  │  MACD: 🟢 B  │  MACD: 🔴 B  │           │
│  │              │              │           │
│  │  15-Min:     │  15-Min:     │           │
│  │  RSI: 58.12  │  RSI: 52.34  │           │
│  │  ADX: 29.87  │  ADX: 31.22  │           │
│  │  MACD: 🟢 B  │  MACD: 🔴 B  │           │
│  └──────────────┴──────────────┘           │
│                                             │
│  📊 VIX: 14.25                              │
├─────────────────────────────────────────────┤
│  Total P&L | Win Rate | Today | Avg        │
├─────────────────────────────────────────────┤
│  🔴 Recent Trades Table                    │
├─────────────────────────────────────────────┤
│  📅 Daily Performance Table                │
└─────────────────────────────────────────────┘
```

---

## 🚀 How to Launch

```bash
run_dashboard.bat
```

Or:
```bash
streamlit run dashboard.py
```

Dashboard opens at `http://localhost:8505`

---

## ⚡ Features

### 1. Auto-Refresh (5 seconds)
Dashboard automatically updates every 5 seconds with:
- Latest spot prices
- Current RSI, ADX values
- MACD trend (Bullish/Bearish)
- VIX value

### 2. Color-Coded MACD
- 🟢 Green = Bullish (MACD > Signal)
- 🔴 Red = Bearish (MACD < Signal)

### 3. Two Timeframes
- **Daily**: For overall trend
- **15-Min**: For intraday signals

### 4. Side-by-Side Comparison
- Nifty50 and BankNifty displayed together
- Easy to compare indicators

---

## 📊 What Each Indicator Tells You

### RSI (Relative Strength Index)
- **< 30**: Oversold (potential buy)
- **45-65**: Neutral zone (entry range for bot)
- **> 70**: Overbought (potential sell)

### ADX (Average Directional Index)
- **< 25**: Weak trend (bot skips)
- **25-40**: Strong trend (bot trades)
- **> 40**: Very strong trend

### MACD Trend
- **🟢 Bullish**: MACD line above signal line
  - Bot looks for Call (CE) entries on 15m crossover
- **🔴 Bearish**: MACD line below signal line
  - Bot looks for Put (PE) entries on 15m crossover

### VIX (Volatility Index)
- **< 10**: Bot skips (too low volatility)
- **10-15**: Normal volatility
- **15-20**: Moderate volatility (wider SL)
- **> 20**: High volatility (widest SL)

---

## 🎮 Usage Tips

### 1. Pre-Market Check (9:00 AM)
Look at dashboard to see:
- Daily MACD trend for both indices
- Daily RSI levels
- VIX value

### 2. During Market Hours
Monitor every few minutes:
- 15-min MACD for potential crossovers
- 15-min RSI staying in 45-65 range
- ADX above 25

### 3. Entry Confirmation
When bot places an order, you can verify:
- Daily MACD matches signal (Bullish for CE, Bearish for PE)
- 15-min had fresh MACD crossover
- RSI was in 45-65 range
- ADX was > 25

---

## 🔧 Technical Details

### Data Source
- Fetched from mStock API
- Daily data: Last 60 days
- 15-min data: Last 5 days

### Calculation
Uses same `TechnicalIndicators` class as trading bot:
- RSI: 14-period (TradingView method)
- ADX: 14-period
- MACD: 12/26/9 settings

### Refresh Rate
- **Indicators**: Update every 5 seconds
- **P&L Metrics**: Update every 5 seconds
- **Trade Table**: Update every 5 seconds

---

## 🚨 Troubleshooting

### Indicators show 0 or N/A
**Cause:** mStock API connection issue or insufficient data

**Fix:**
1. Check `.env` credentials
2. Verify `credentials.json` has valid token
3. Restart dashboard

### Dashboard not refreshing
**Cause:** Auto-refresh disabled

**Fix:** Reload dashboard page

### Slow loading
**Cause:** Fetching historical data

**Note:** First load takes 5-10 seconds, then smooth

---

## 💡 Pro Tips

1. **Watch MACD Divergence**: If daily is bullish but 15-min is bearish, wait for alignment

2. **Monitor VIX**: If VIX spikes above 20, expect wider SL triggers

3. **RSI Extremes**: If 15-min RSI hits <45 or >65, reversion likely

4. **ADX Strength**: Higher ADX = stronger trend = better win rate

5. **Use with Bot**: Keep dashboard open while bot runs for full visibility

---

## ✅ Summary

Your dashboard now shows:
- ✅ Nifty50 Daily: RSI, ADX, MACD trend
- ✅ Nifty50 15-Min: RSI, ADX, MACD trend  
- ✅ BankNifty Daily: RSI, ADX, MACD trend
- ✅ BankNifty 15-Min: RSI, ADX, MACD trend
- ✅ VIX value
- ✅ Auto-refresh every 5 seconds

**Everything you need to monitor your bot in real-time!** 📊🚀
