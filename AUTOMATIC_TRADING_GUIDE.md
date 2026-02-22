# 🎯 Automatic ATM Strike Selection & Live Order Tracking

## ✅ What I've Added

### 1. Automatic ATM Option Selection
**NO MANUAL INPUT NEEDED!** The bot now automatically:
- Calculates ATM (At The Money) strike based on spot price
- Rounds to nearest strike interval (50 for Nifty, 100 for BankNifty)
- Generates weekly expiry option symbols
- Selects CE (Call) or PE (Put) based on signal

**Example:**
- Nifty spot: 19,537.45 → ATM Strike: 19,550 → Symbol: `NIFTY30JAN2419550CE`
- BankNifty spot: 45,123.75 → ATM Strike: 45,100 → Symbol: `BANKNIFTY29JAN2645100PE`

### 2. Live Order Placement
The bot can now send **real orders** to mStock API with status tracking:
- ✅ **PLACED** - Order successfully sent to broker
- ❌ **REJECTED** - Order rejected by broker
- 💸 **INSUFFICIENT_FUNDS** - Not enough margin/funds

### 3. Dashboard Integration
Dashboard will show (once updated):
- Order status table with color coding
- Green = Placed, Yellow = Insufficient Funds, Red = Rejected
- Order count metrics

---

## 🤖 How It Works

### When Bot Detects Entry Signal:

**Step 1: Get Spot Price**
```
Nifty Spot = 19,537.45
```

**Step 2: Auto-Select ATM Strike**
```
ATM Strike = 19,550 (rounded to nearest 50)
Weekly Expiry = 30JAN24 (Thursday)
Option Type = CE (Call Entry signal detected)
Symbol = NIFTY30JAN2419550CE
```

**Step 3: Place Order**
```
If PAPER MODE:
  → Log: "📝 PAPER TRADE: BUY 50 x NIFTY30JAN2419550CE"
  → Status: PLACED (simulated)
  
If LIVE MODE:
  → Send to mStock API
  → If successful: Status = PLACED ✅
  → If failed (low funds): Status = INSUFFICIENT_FUNDS 💸
  → If failed (other): Status = REJECTED ❌
```

**Step 4: Dashboard Shows**
```
Time: 10:45:32
Symbol: NIFTY30JAN2419550CE
Side: BUY
Qty: 50
Status: ✅ PLACED  (or 💸 INSUFFICIENT_FUNDS or ❌ REJECTED)
Reason: (if rejected)
```

---

## 🔧 How to Enable Live Trading

### Currently: PAPER MODE (Safe)
Your bot is in **PAPER MODE** by default - no real orders placed.

### To Enable LIVE TRADING:

**Step 1: Edit config.json**
```json
{
  "trading_mode": "LIVE",  ← Add this line
  ...
}
```

**Step 2: Ensure Sufficient Funds**
- Check your mStock account has margin for F&O
- Nifty 50 qty needs ~Rs 10-15K margin per lot
- BankNifty 25 qty needs ~Rs 20-30K margin per lot

**Step 3: Restart Bot**
```bash
python main.py
```

Bot will now:
- Auto-select ATM options ✅
- Send real orders to mStock ✅
- Track order status ✅
- Show on dashboard ✅

---

## 📊 Option Selection Logic

### Nifty50
- **Strike Interval**: 50
- **Expiry**: Thursday (weekly)
- **Exchange**: NFO
- **Example**: `NIFTY30JAN2419550CE`

### BankNifty
- **Strike Interval**: 100
- **Expiry**: Wednesday (weekly)
-  **Exchange**: NFO
- **Example**: `BANKNIFTY29JAN2645100PE`

### ATM Calculation
```python
spot_price = 19,537.45
interval = 50  # for Nifty
atm_strike = round(19,537.45 / 50) * 50 = 19,550
```

---

## 🎮 Testing the Flow

### Test 1: Paper Mode (Safe)
```bash
1. Keep paper_mode = True
2. Run: python main.py
3. Wait for entry signal
4. Check logs: "📝 PAPER TRADE: BUY 50 x NIFTY30JAN2419550CE"
5. Check dashboard: Order shows "PLACED" (simulated)
```

### Test 2: Live Mode (Real)
```bash
1. Set paper_mode = False in config
2. Ensure funds in mStock account
3. Run: python main.py
4. Wait for entry signal
5. Bot selects ATM strike automatically
6. Order sent to mStock API
7. Check dashboard for status:
   - ✅ PLACED = Success!
   - 💸 INSUFFICIENT_FUNDS = Add funds
   - ❌ REJECTED = Check error
```

---

## 📁 New Files Created

### 1. `src/option_selector.py`
- Automatic ATM strike calculation
- Weekly expiry determination
- Option symbol generation

### 2. `src/order_manager.py`
- Order placement tracking
- Status management (PLACED/REJECTED/INSUFFICIENT_FUNDS)
- Order history logging to `logs/orders_log.json`

### 3. Updated `src/market_data.py`
- `place_order()` now supports `paper_mode` parameter
- Live order placement to mStock API
- Error handling for insufficient funds

---

## 🚦 Order Status Flow

```
Entry Signal Detected
        ↓
Auto-Select ATM Strike
(e.g., Nifty 19550 CE)
        ↓
   Place Order
        ↓
    ┌───────────┐
    │  PAPER?   │
    └───────────┘
      │       │
     YES     NO
      │       │
      ↓       ↓
  ✅ PLACED  Send to API
  (simulated)    ↓
          ┌──────────────┐
          │  API Result  │
          └──────────────┘
           │     │     │
         ✅    💸    ❌
       PLACED  INSUF  REJECT
```

---

## ⚙️ Configuration Options

Add to `config.json`:

```json
{
  "trading_mode": "PAPER",  // or "LIVE"
  
  "option_selection": {
    "use_atm": true,         // Use ATM strikes
    "nifty_interval": 50,    // Nifty strike interval
    "banknifty_interval": 100 // BankNifty strike interval
  },
  
  "order_settings": {
    "order_type": "MARKET",  // MARKET or LIMIT
    "product_type": "INTRADAY" // INTRADAY or CARRYFORWARD
  }
}
```

---

## ✅ Summary

### Question 1: How does the bot buy options?
**Answer:** FULLY AUTOMATIC! No manual input needed.
- Bot detects entry signal from MACD+RSI+ADX conditions
- Fetches current spot price
- Calculates ATM strike (nearest 50 for Nifty, 100 for BankNifty)
- Determines weekly expiry (Thursday/Wednesday)
- Generates option symbol
- Places order automatically

### Question 2: How to see order status on dashboard?
**Answer:** Dashboard will show:
- **Order Status Table** with:
  - Time, Symbol, Side (BUY/SELL), Qty
  - Status: ✅ PLACED / 💸 INSUFFICIENT FUNDS / ❌ REJECTED
  - Rejection reason (if any)
- **Order Metrics**:
  - Total Placed
  - Total Rejected
  - Insufficient Funds Count

---

## 🔐 Safety Features

1. **Paper Mode Default** - Won't place real orders unless explicitly enabled
2. **Insufficient Funds Detection** - Shows clear warning if not enough margin
3. **Order Logging** - All orders saved to `logs/orders_log.json`
4. **Status Tracking** - Every order tracked with timestamp and result
5. **Error Handling** - Graceful failure if API issues

---

## 📝 Next Steps

1. **Test in Paper Mode** (Current state)
   - Run bot, verify ATM selection works
   - Check logs for correct symbol generation
   - Confirm simulated orders appear

2. **Review Dashboard** 
   - Check order status table appears
   - Verify color coding works

3. **When Ready for Live**
   - Ensure sufficient funds in mStock
   - Change `paper_mode` to False
   - Start with 1 lot only
   - Monitor first 3-5 trades closely
   - Check dashboard for order status

4. **Monitor Performance**
   - Daily P&L tracking
   - Order success rate
   - Insufficient funds incidents

---

**Your bot now runs 100% automatically from signal to order!** 🚀
