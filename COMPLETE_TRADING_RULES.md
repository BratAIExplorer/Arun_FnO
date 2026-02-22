# Complete Trading Conditions & Rules
## F&O Options Trading Bot - All Indices

**Trading Indices**: NIFTY50, BANKNIFTY, FINNIFTY, SENSEX

---

## 📊 ENTRY CONDITIONS (BUY)

All conditions checked **every 1 second**. **ALL must be TRUE** for a trade to execute.

### Common Rules (Both CALL & PUT)

| # | Condition | Value | Notes |
|---|-----------|-------|-------|
| 1 | **Trading Hours** | 09:15 AM - 03:15 PM | No new entries after 3:15 PM |
| 2 | **VIX Minimum** | ≥ 10.0 | Skip trading if VIX too low |
| 3 | **No Duplicate Position** | Max 1 position per index | Cannot have multiple positions in same underlying |
| 4 | **No Duplicate Signal** | Fresh crossover required | Won't re-enter on same candle |
| 5 | **15m RSI Range** | 30.0 to 65.0 | Momentum must be in range |
| 6 | **Daily ADX** | > 25.0 | Higher timeframe trend strength |
| 7 | **MACD Histogram** | **Dark Color** | CE: Dark Green (Inc) / PE: Dark Red (Dec) |
| 8 | **15m ADX** | > 25.0 | **CURRENTLY DISABLED** (Optional) |

### CALL (CE) Specific Conditions

| Condition | First Trade of Day | Subsequent Trades |
|-----------|-------------------|-------------------|
| **MACD Signal** | MACD > Signal (Trend Active) | **MACD > Signal (Trend Active)** |
| **Entry Type** | Relaxed Entry | **RELAXED ENTRY** |
| **Logic** | Enters if bullish trend is active | **NO Fresh Crossover Needed**. Enters if Trend is Active. |
| **Momentum** | **Dark Green** | Histogram > 0 AND Histogram > Previous |

**Strict Anti-Duplication**:
- ❌ Cannot re-enter the **EXACT SAME** Option Strike/Symbol if already traded today.
- ✅ CAN enter a **different** strike if the trend continues.

### PUT (PE) Specific Conditions

| Condition | First Trade of Day | Subsequent Trades |
|-----------|-------------------|-------------------|
| **MACD Signal** | MACD < Signal (Trend Active) | **MACD < Signal (Trend Active)** |
| **Entry Type** | Relaxed Entry | **RELAXED ENTRY** |
| **Logic** | Enters if bearish trend is active | **NO Fresh Crossover Needed**. Enters if Trend is Active. |
| **Momentum** | **Dark Red** | Histogram < 0 AND Histogram < Previous |

**Strict Anti-Duplication**:
- ❌ Cannot re-enter the **EXACT SAME** Option Strike/Symbol if already traded today.
- ✅ CAN enter a **different** strike if the trend continues.

---

## 🎯 STRIKE SELECTION

Controlled by `strike_depth` parameter in `config.json`:

| Value | Strike Type | Description |
|-------|-------------|-------------|
| **0** | **ATM / Closest ITM** | **NEVER OTM**. Picks closest ATM or forced ITM. |
| **1** | ITM 1 | 1 strike deeper In-The-Money |
| **2** | ITM 2 | 2 strikes deeper In-The-Money |

**Current Setting**: `strike_depth = 0` (ATM)

---

## 🚪 EXIT CONDITIONS (SELL)

Checked **every 1 second** in **priority order**:

### Priority 1: Stop Loss (HIGHEST PRIORITY)
**Based on UNDERLYING SPOT MOVEMENT** (not premium)

#### NIFTY50 Stop Loss

| VIX Range | Stop Loss % | Trigger Logic |
|-----------|-------------|---------------|
| 12-15 | 0.70% | **CE**: Exit if spot drops 0.70% |
| 15-20 | 0.75% | **PE**: Exit if spot rises 0.70% |
| 20+ | 0.80% | Adjusted for volatility |

#### BANKNIFTY Stop Loss

| VIX Range | Stop Loss % | Trigger Logic |
|-----------|-------------|---------------|
| 12-15 | 1.20% | **CE**: Exit if spot drops 1.20% |
| 15-20 | 1.25% | **PE**: Exit if spot rises 1.20% |
| 20+ | 1.50% | Wider stop for high volatility |

#### FINNIFTY Stop Loss

| VIX Range | Stop Loss % | Trigger Logic |
|-----------|-------------|---------------|
| 12-15 | 1.00% | **CE**: Exit if spot drops 1.00% |
| 15-20 | 1.25% | **PE**: Exit if spot rises 1.00% |
| 20+ | 1.50% | Adjusted for volatility |

#### SENSEX Stop Loss

| VIX Range | Stop Loss % | Trigger Logic |
|-----------|-------------|---------------|
| 12-15 | 1.00% | **CE**: Exit if spot drops 1.00% |
| 15-20 | 1.25% | **PE**: Exit if spot rises 1.00% |
| 20+ | 1.50% | Adjusted for volatility |

### Priority 2: Profit Target
**Based on FIXED AMOUNT**

| Target | Value | Calculation |
|--------|-------|-------------|
| **Profit Target** | **Rs 250** | Net P&L per position |
| **Safety Net** | **-50%** | Hard exit on premium loss |

**Current Setting**: `profit_target_amount = 250.0` (Hardcoded for safety)

### Priority 3: Trend Reversal (Safety Exit)
**Applies regardless of current profit. MUST BE CONFIRMED ON CANDLE CLOSE.**

#### For CALL (CE) Positions:
Exit if **PREVIOUS 15-min Candle** closed with:
- MACD crossing **BELOW** Signal (Bearish Crossover)
- +DI crossing **BELOW** -DI (Bearish DI Crossover)

#### For PUT (PE) Positions:
Exit if **PREVIOUS 15-min Candle** closed with:
- MACD crossing **ABOVE** Signal (Bullish Crossover)
- +DI crossing **ABOVE** -DI (Bullish DI Crossover)

*Note: This prevents exiting on intraday "ticks" that might reverse before the candle closes.*


---

## 💰 PROFIT & LOSS CALCULATION

### How Profit is Calculated

**Formula**:
```
P&L (Rs) = (Exit Premium - Entry Premium) × Lot Size
P&L (%) = ((Exit Premium - Entry Premium) / Entry Premium) × 100
```

**Example - NIFTY CALL**:
- Entry Premium: Rs 100
- Exit Premium: Rs 105
- Lot Size: 65
- **P&L**: (105 - 100) × 65 = **Rs 325**
- **P&L %**: ((105 - 100) / 100) × 100 = **5.0%**

### How Loss is Calculated

**Stop Loss Trigger** (based on spot movement):

**Example - NIFTY CALL with 0.70% SL**:
- Entry Spot: 25,000
- Current Spot: 24,825 (dropped 175 points = 0.70%)
- **Stop Loss TRIGGERED** → Exit at current premium

**Example - BANKNIFTY PUT with 1.20% SL**:
- Entry Spot: 50,000
- Current Spot: 50,600 (rose 600 points = 1.20%)
- **Stop Loss TRIGGERED** → Exit at current premium

---

## 📈 LOT SIZES & POSITION SIZING

| Index | Lot Size | Number of Lots | Total Quantity |
|-------|----------|----------------|----------------|
| **NIFTY50** | 65 | 1 | 65 |
| **BANKNIFTY** | 30 | 1 | 30 |
| **FINNIFTY** | 60 | 1 | 60 |
| **SENSEX** | 20 | 1 | 20 |

**Position Limits**:
- Max 1 position per underlying at a time
- Can trade multiple indices simultaneously

---

## 📊 TECHNICAL INDICATOR SETTINGS

### MACD Parameters
| Parameter | Value |
|-----------|-------|
| Fast Period | 12 |
| Slow Period | 26 |
| Signal Period | 9 |

### RSI Parameters
| Parameter | Value |
|-----------|-------|
| Period | 14 |
| Entry Range | 30.0 - 65.0 |

### ADX Parameters
| Parameter | Value |
|-----------|-------|
| Period | 14 |
| 15m ADX Min | 25.0 (DISABLED) |
| Daily ADX Min | 25.0 (ACTIVE) |

---

## ⏰ TRADING HOURS

| Event | Time (IST) | Description |
|-------|------------|-------------|
| **Market Open** | 09:15 AM | Trading starts |
| **Entry Cutoff** | 03:15 PM | Last entry allowed |
| **Market Close** | 03:30 PM | Market closes |

---

## 💼 CAPITAL MANAGEMENT

| Parameter | Value |
|-----------|-------|
| **Initial Capital** | Rs 1,00,000 |
| **Daily Loss Limit** | 5.0% (Rs 5,000) |
| **Daily Profit Cap** | Rs 1,200 |
| **Trading Mode** | LIVE (Real orders) |

---

## 🔄 RE-ENTRY LOGIC

### First Trade of Day
- **Relaxed Entry**: Enters if trend is active (MACD > Signal for CE, MACD < Signal for PE)
- No fresh crossover required

### Subsequent Trades (Same Day)
- **Relaxed Entry**: Enters if trend is active (MACD > Signal for CE, MACD < Signal for PE)
- **NO Fresh Crossover Needed** (per latest update)
- **Anti-Duplication**: Still prevents re-entering the EXACT same strike.

---

## 📝 SUMMARY OF KEY RULES

### Entry Decision
✅ All 7 common conditions must be TRUE  
✅ MACD signal appropriate for trade type (CE/PE)  
✅ First trade = Relaxed, Subsequent = Relaxed (Trend Active)
 
 ### Exit Decision (Priority Order)
 1. **Stop Loss** → Based on spot movement (VIX-adjusted)
 2. **Profit Target** → Based on hardcoded amount (Rs 250.0)
 3. **Trend Reversal** → MACD or DI crossover against position

### Profit/Loss Basis
- **Profit Target**: Calculated as **FIXED AMOUNT (Rs 250.0)**
- **Stop Loss**: Triggered by **UNDERLYING SPOT MOVEMENT** (0.7%-1.5% depending on index and VIX)
- **Final P&L**: Difference in premium × lot size

---

## 🎛️ EDITABLE PARAMETERS

All these can be changed in [`config.json`](file:///c:/Antigravity/Arun%20Samant%20-%20F&O/config.json):

- ✏️ Profit target percentage
- ✏️ Stop loss percentages (per index, per VIX range)
- ✏️ Lot sizes and number of lots
- ✏️ RSI range (min/max)
- ✏️ ADX thresholds
- ✏️ VIX minimum threshold
- ✏️ Trading hours
- ✏️ Strike depth (ATM/ITM)
- ✏️ Daily loss limit

---

## 📍 Current Active Settings

From your [`config.json`](file:///c:/Antigravity/Arun%20Samant%20-%20F&O/config.json):
- **Live Trading**: ✅ ENABLED
- **Strike Depth**: 0 (ATM)
- **Profit Target**: Rs 250.0 (Hardcoded)
- **Daily Profit Cap**: Rs 1,200 (Stop for day if reached)
- **NIFTY SL**: 0.7% (base)
- **BANKNIFTY SL**: 1.2% (base)
- **FINNIFTY SL**: 1.0% (base)
- **SENSEX SL**: 1.0% (base)
- **Initial Capital**: Rs 1,00,000
- **Daily Loss Limit**: 5.0%
- **Entry Type**: RELAXED (No Fresh Crossover Needed)

---

## 🧠 BOT MEMORY & PERSISTENCE

The bot uses a **Dual-Layer Memory System** to ensure safety across restarts:

1.  **Active Position Memory** (`data/positions.json`)
    *   **Function**: Remembers any trade currently open.
    *   **Behavior**: If you restart the bot while a trade is running, it will **resume management** (SL/Target) immediately. It will NOT forget the trade.

2.  **Daily History Memory** (`data/daily_history.json`)
    *   **Function**: Remembers all trades closed today.
    *   **Critical Safety**:
        *   **No Double Entry**: Prevents re-entering a symbol if a trade was already taken on the same signal.
        *   **Loss Tracking**: Calculates Total Daily P&L from *all* sessions today to enforce the **Daily Loss Limit**.

*This means you can safely stop/start the bot without losing track of your day's progress.*
