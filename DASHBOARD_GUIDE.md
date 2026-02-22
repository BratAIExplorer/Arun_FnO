# 📊 Dashboard Guide

## Launch Dashboard

### Windows
Double-click: **`run_dashboard.bat`**

### Manual
```bash
streamlit run dashboard.py
```

The dashboard will automatically open in your browser at `http://localhost:8505`

---

## 🎯 What You'll See

### 1. Status Indicators
- **Bot Status**: 🟢 ONLINE / 🔴 OFFLINE
- **Credentials**: ✅ Loaded from .env (automatic)
- **Mode**: PAPER / LIVE

### 2. Live Metrics (4 Boxes)
- **Total P&L** - Overall profit/loss (green/red background)
- **Win Rate** - Percentage of winning trades
- **Today's P&L** - Today's performance
- **Avg P&L/Trade** - Average per trade

### 3. Live Trades Table
Shows last 10 trades with:
- Position ID
- Underlying (NIFTY50/BANKNIFTY)
- Type (CALL/PUT)
- Entry/Exit times
- Entry/Exit prices
- Exit reason
- P&L (colored: green=profit, red=loss)

### 4. Daily Performance Table
Shows performance from **Jan 2026 onwards**:
- Date
- Daily P&L
- Number of trades
- Average profit %
- Win rate %
- Cumulative P&L

### 5. Overall Summary
- Trading days
- Cumulative P&L
- Total trades

---

## ⚙️ Features

### Auto-Refresh
- Dashboard refreshes every **30 seconds**
- Toggle in sidebar if needed

### No Login Required
- Credentials loaded automatically from `.env` file
- Token loaded from `credentials.json`
- **Zero manual input!** ✅

### Clean UI
- Minimal design - only what matters
- Color-coded P&L (green/red)
- Responsive layout

---

## 📝 How It Works

1. Dashboard reads trade logs from `logs/` folder
2. Automatically displays latest data
3. Calculates daily and overall performance
4. No manual refresh needed (auto-updates)

---

## 🔍 Troubleshooting

### "No trades data available"
- Start the trading bot: `python main.py`
- Wait for at least one trade to complete
- Trades are saved in `logs/paper_trades_*.csv`

### "Bot shows OFFLINE"
- Check if `main.py` is running
- Log file must be updated recently (< 5 min)

### Dashboard won't open
```bash
pip install streamlit
streamlit run dashboard.py
```

---

## 💡 Tips

1. **Keep bot running** in one terminal
2. **Keep dashboard open** in browser for monitoring
3. **Check daily performance** to track consistency
4. **Monitor win rate** - should be 60%+ over time

---

**Ready to monitor! Open dashboard and start trading.** 🚀
