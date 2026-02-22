# Configuration Guide

## How to Edit Your Trading Parameters

Simply edit the `config.json` file in the root folder. The bot will automatically load these settings when it starts.

## ⚙️ Editable Parameters

### 1. Stop Loss (SL)

**Nifty50:**
```json
"NIFTY50": {
  "base_sl_percent": 0.70,        // Base SL: 0.70%
  "vix_adjustments": {
    "vix_12_15": 0.70,            // When VIX is 12-15
    "vix_15_20": 0.75,            // When VIX is 15-20
    "vix_above_20": 0.80          // When VIX is above 20
  }
}
```

**BankNifty:**
```json
"BANKNIFTY": {
  "base_sl_percent": 1.00,        // Base SL: 1.00%
  "vix_adjustments": {
    "vix_12_15": 1.00,            // When VIX is 12-15
    "vix_15_20": 1.25,            // When VIX is 15-20
    "vix_above_20": 1.50          // When VIX is above 20
  }
}
```

### 2. Profit Target

```json
"profit_targets": {
  "profit_target_percent": 15.0   // Exit at 15%+ profit
}
```

**Examples:**
- Set to `10.0` for 10% profit target
- Set to `20.0` for 20% profit target
- Set to `25.0` for 25% profit target

### 3. Lot Sizes

**Nifty50:**
```json
"NIFTY50": {
  "lot_size": 50,                 // 1 lot = 50 quantity
  "num_lots": 1                   // Trade 1 lot
}
```

**BankNifty:**
```json
"BANKNIFTY": {
  "lot_size": 25,                 // 1 lot = 25 quantity
  "num_lots": 1                   // Trade 1 lot
}
```

**Examples:**
- Trade 2 lots of Nifty: Change `"num_lots": 2`
- Trade 3 lots of BankNifty: Change `"num_lots": 3`

### 4. Capital Settings

```json
"capital": {
  "initial_capital": 100000,      // Starting capital (Rs)
  "daily_loss_limit_percent": 3.0 // Stop trading at 3% daily loss
}
```

## 📝 Quick Examples

### Example 1: More Aggressive (Higher Risk/Reward)
```json
{
  "stop_loss": {
    "NIFTY50": {
      "base_sl_percent": 1.00     // Wider SL (more room to breathe)
    }
  },
  "profit_targets": {
    "profit_target_percent": 25.0 // Higher profit target
  },
  "lot_sizes": {
    "NIFTY50": {
      "num_lots": 2              // Trade 2 lots
    }
  }
}
```

### Example 2: More Conservative (Lower Risk)
```json
{
  "stop_loss": {
    "NIFTY50": {
      "base_sl_percent": 0.50     // Tighter SL
    }
  },
  "profit_targets": {
    "profit_target_percent": 10.0 // Lower profit target (exit faster)
  },
  "lot_sizes": {
    "NIFTY50": {
      "num_lots": 1              // Trade 1 lot only
    }
  }
}
```

### Example 3: Small Capital (1 Lakh)
```json
{
  "capital": {
    "initial_capital": 100000,
    "daily_loss_limit_percent": 2.0 // Stricter daily limit
  },
  "lot_sizes": {
    "NIFTY50": {
      "num_lots": 1              // 1 lot only
    },
    "BANKNIFTY": {
      "num_lots": 1              // 1 lot only
    }
  }
}
```

### Example 4: Large Capital (5 Lakhs)
```json
{
  "capital": {
    "initial_capital": 500000,
    "daily_loss_limit_percent": 3.0
  },
  "lot_sizes": {
    "NIFTY50": {
      "num_lots": 3              // 3 lots (150 qty)
    },
    "BANKNIFTY": {
      "num_lots": 2              // 2 lots (50 qty)
    }
  }
}
```

## 🔄 How to Apply Changes

1. Edit `config.json`
2. Save the file
3. Restart the trading bot:
   ```bash
   python main.py
   ```

The bot will automatically load your new settings and display them:
```
✅ Configuration loaded from 'config.json'
   Initial Capital: Rs 100,000.00
   Profit Target: 15.0%
   Nifty SL: 0.7%
   BankNifty SL: 1.0%
   Nifty Lot Size: 50 x 1 lots
   BankNifty Lot Size: 25 x 1 lots
```

## ⚠️ Important Notes

### Stop Loss Guidelines
- **Too tight** (< 0.50%): May get stopped out frequently
- **Too wide** (> 1.50%): Larger losses when SL hits
- **Recommended**: 0.60-0.80% for Nifty, 0.90-1.10% for BankNifty

### Profit Target Guidelines
- **Lower targets** (10-12%): Higher win rate, faster exits
- **Higher targets** (20-25%): Lower win rate, bigger wins
- **Recommended**: 12-18% for balanced approach

### Lot Size Guidelines
- **1 lot**: Good for 1-2 lakh capital
- **2-3 lots**: Good for 3-5 lakh capital
- **4+ lots**: Only if capital > 5 lakh and tested thoroughly

### Risk Warning
- **Always test** new settings in paper trading mode first
- **Don't increase** lot size too quickly
- **Monitor** daily loss limit carefully
- **Backtest** any major changes before going live

## 🧪 Testing Your Settings

After changing config:
```bash
# Test in paper trading mode
python main.py

# Or run a backtest
python example_backtest.py
```

## 📊 Default Settings (Your Original Strategy)

The default `config.json` contains your documented strategy:
- **Nifty SL**: 0.70% (0.75% mid-VIX, 0.80% high-VIX)
- **BankNifty SL**: 1.00% (1.25% mid-VIX, 1.50% high-VIX)
- **Profit Target**: 15%
- **Lot Sizes**: 1 lot each
- **Capital**: Rs 1,00,000
- **Daily Loss Limit**: 3%

---

**Tip:** Keep a backup of `config.json` before making changes!
