# 🔴 LIVE TRADING MODE ENABLED

## ✅ What I Did

Your bot is now configured for **LIVE TRADING** - it will place **real orders** to your mStock account.

### Changes Made:

1. **config.json** - Added `"live_trading": true`
2. **trading_config.py** - Loads live trading flag
3. **Bot will place REAL orders** to mStock API

---

## ⚠️ IMPORTANT - BEFORE YOU START

### 1. Verify Your mStock Account Has Funds

**Check you have sufficient margin for F&O trading:**
- Nifty50 (50 qty) requires ~Rs 10,000-15,000 margin per lot
- BankNifty (25 qty) requires ~Rs 20,000-30,000 margin per lot

**Current lot configuration:**
- Nifty: 1 lot (50 qty)
- BankNifty: 1 lot (25 qty)

### 2. Verify Credentials Are Correct

Your `.env` file should have:
```env
API_KEY=your_actual_api_key
API_SECRET=your_actual_secret
CLIENT_CODE=your_client_code
PASSWORD=your_password
```

Your `credentials.json` should have a valid access token.

### 3. Start Small!

**First Day Recommendations:**
- Keep 1 lot only (already configured)
- Watch the first 2-3 trades closely
- Verify orders appear in your mStock app
- Check dashboard shows correct status

---

## 🚀 How to Start Live Trading

### Step 1: Launch Dashboard
```bash
run_dashboard.bat
```

### Step 2: Start Trading Bot
```bash
python main.py
```

### Step 3: Watch Console Output

You'll see:
```
✅ Configuration loaded from 'config.json'
   🔴 LIVE TRADING MODE: ENABLED
   Initial Capital: Rs 100,000.00
   Profit Target: 15.0%
   ...
```

### Step 4: Monitor Orders

When conditions are met, you'll see:
```
📤 Placing LIVE order: BUY 50 x NIFTY05FEB2619550CE
✅ Order placed successfully! Order ID: 123456789
```

Or if insufficient funds:
```
💸 INSUFFICIENT FUNDS for NIFTY05FEB2619550CE
```

---

## 📊 What Happens Now

### 1. Bot Monitors Market
- Checks every 15 minutes
- Evaluates all 8 entry conditions

### 2. When ALL Conditions Met
- Fetches live spot price
- Calculates ATM strike automatically
- Selects correct expiry (weekly/monthly)
- **Sends REAL order to mStock API** 🔴

### 3. Order Status
- ✅ **PLACED** - Order successful
- 💸 **INSUFFICIENT_FUNDS** - Need more margin
- ❌ **REJECTED** - Order failed (check logs)

### 4. Dashboard Updates
- Shows order status
- Updates P&L live
- Tracks performance

---

## 🛡️ Safety Features

### Daily Loss Limit: 3%
If you lose 3% of capital in a day, bot stops trading automatically.

Current: Rs 1,00,000 → Stop at Rs 3,000 loss

### Position Limits
- Max 1 position per underlying
- Only trades during market hours (9:25 AM - 2:30 PM)
- Auto-exits all positions at 2:30 PM

### Stop Loss
- Nifty: 0.70% (adjusts with VIX)
- BankNifty: 1.00% (adjusts with VIX)

---

## 📱 How to Monitor

### 1. Dashboard
Real-time view of:
- Total P&L
- Today's P&L
- Win rate
- Order status (Placed/Rejected/Insufficient Funds)

### 2. mStock App
Check your broker app to see:
- Actual positions
- Order confirmations
- Real-time P&L

### 3. Log Files
- `logs/trading_bot_YYYYMMDD.log` - Detailed execution log
- `logs/orders_log.json` - All order statuses
- `logs/paper_trades_*.csv` - Trade history

---

## 🚨 If Something Goes Wrong

### Insufficient Funds
**Dashboard will show:** 💸 INSUFFICIENT_FUNDS

**Fix:** Add margin to your mStock account

### Order Rejected
**Dashboard will show:** ❌ REJECTED

**Check:**
1. Is market open?
2. Is symbol correct?
3. Check mStock app for rejection reason

### Bot Not Placing Orders
**Check:**
1. Are all 8 conditions being met? (check logs)
2. Is VIX > 10?
3. Is it within trading hours (9:25 AM - 2:30 PM)?
4. Daily loss limit not hit?

---

## 🔧 To Disable Live Trading (Switch Back to Paper)

If you want to test first:

**Edit config.json:**
```json
{
  "trading_mode": {
    "live_trading": false  ← Change to false
  }
}
```

Then restart bot.

---

## ✅ Final Checklist Before Starting

- [ ] Verified mStock account has sufficient margin
- [ ] `.env` credentials are correct
- [ ] `credentials.json` has valid access token
- [ ] Understand daily loss limit (3% = Rs 3,000)
- [ ] Dashboard is open for monitoring
- [ ] Ready to watch first few trades closely
- [ ] mStock app open to verify orders

---

## 🎯 You're Ready!

**Your bot will now:**
✅ Monitor market conditions  
✅ Calculate ATM strikes automatically  
✅ Send REAL orders to mStock API  
✅ Track order status on dashboard  
✅ Manage positions automatically  
✅ Exit at SL/Profit/EOD  

**Start trading:**
```bash
python main.py
```

**Good luck! Trade responsibly.** 🚀📊

---

**Remember:** 
- Start with 1 lot only
- Monitor closely for first week
- Check mStock app frequently
- Dashboard updates every 30 seconds
- Daily loss limit protects you

Let's make some profits! 💰
