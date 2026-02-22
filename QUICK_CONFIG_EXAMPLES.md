# Quick Configuration Examples

## 🎯 Want to Change Something? Edit config.json

Open `config.json` in any text editor and change the values:

---

## Example 1: Change Profit Target to 20%

**Before:**
```json
"profit_targets": {
  "profit_target_percent": 15.0
}
```

**After:**
```json
"profit_targets": {
  "profit_target_percent": 20.0
}
```

**Result:** Bot will now exit at 20% profit instead of 15%

---

## Example 2: Tighten Nifty Stop Loss to 0.50%

**Before:**
```json
"NIFTY50": {
  "base_sl_percent": 0.70,
  "vix_adjustments": {
    "vix_12_15": 0.70,
    "vix_15_20": 0.75,
    "vix_above_20": 0.80
  }
}
```

**After:**
```json
"NIFTY50": {
  "base_sl_percent": 0.50,
  "vix_adjustments": {
    "vix_12_15": 0.50,
    "vix_15_20": 0.55,
    "vix_above_20": 0.60
  }
}
```

**Result:** Tighter stop loss = less loss per losing trade, but may get stopped out more often

---

## Example 3: Trade 2 Lots Instead of 1

**Before:**
```json
"lot_sizes": {
  "NIFTY50": {
    "lot_size": 50,
    "num_lots": 1
  }
}
```

**After:**
```json
"lot_sizes": {
  "NIFTY50": {
    "lot_size": 50,
    "num_lots": 2
  }
}
```

**Result:** 
- Before: 50 quantity per trade
- After: 100 quantity per trade (2x profit/loss)

---

## Example 4: Increase Capital and Daily Loss Limit

**Before:**
```json
"capital": {
  "initial_capital": 100000,
  "daily_loss_limit_percent": 3.0
}
```

**After:**
```json
"capital": {
  "initial_capital": 500000,
  "daily_loss_limit_percent": 2.0
}
```

**Result:**
- Starting capital: Rs 5,00,000
- Daily stop at Rs 10,000 loss (2% of 5L)

---

## Example 5: More Aggressive Settings (Higher Risk)

```json
{
  "stop_loss": {
    "NIFTY50": {
      "base_sl_percent": 1.00
    },
    "BANKNIFTY": {
      "base_sl_percent": 1.50
    }
  },
  "profit_targets": {
    "profit_target_percent": 25.0
  },
  "lot_sizes": {
    "NIFTY50": {
      "num_lots": 3
    },
    "BANKNIFTY": {
      "num_lots": 2
    }
  }
}
```

**Effect:**
- ✅ Wider SL = more room for position to work
- ✅ Higher profit target = bigger wins
- ⚠️ More lots = higher profit AND loss
- ⚠️ Higher risk overall

---

## Example 6: Conservative Settings (Lower Risk)

```json
{
  "stop_loss": {
    "NIFTY50": {
      "base_sl_percent": 0.50
    },
    "BANKNIFTY": {
      "base_sl_percent": 0.75
    }
  },
  "profit_targets": {
    "profit_target_percent": 10.0
  },
  "lot_sizes": {
    "NIFTY50": {
      "num_lots": 1
    },
    "BANKNIFTY": {
      "num_lots": 1
    }
  },
  "capital": {
    "daily_loss_limit_percent": 2.0
  }
}
```

**Effect:**
- ✅ Tighter SL = smaller losses
- ✅ Lower profit target = exit faster, more wins
- ✅ 1 lot only = limited risk
- ✅ 2% daily limit = extra safety
- ⚠️ Lower profits per trade

---

## 🚀 After Editing

1. **Save** `config.json`
2. **Restart** the bot:
   ```bash
   python main.py
   ```
3. **Check** the startup log to confirm settings:
   ```
   ✅ Configuration loaded from 'config.json'
      Initial Capital: Rs 100,000.00
      Profit Target: 15.0%
      Nifty SL: 0.7%
      BankNifty SL: 1.0%
      Nifty Lot Size: 50 x 1 lots
      BankNifty Lot Size: 25 x 1 lots
   ```

---

## ⚠️ Safety Tips

1. **Always test in paper mode first** after changing settings
2. **Start conservative** - you can always increase lot size later
3. **Keep SL reasonable** - too tight = frequent stops, too wide = big losses
4. **Monitor daily limit** - 3% daily loss is a safety net, respect it
5. **Backtest changes** if possible before going live

---

## 📝 Common Mistakes to Avoid

❌ **Don't** set SL too tight (< 0.40%) - will get stopped out constantly  
❌ **Don't** set profit target too high (> 30%) - will rarely hit it  
❌ **Don't** increase lot size without testing first  
❌ **Don't** remove daily loss limit  
❌ **Don't** trade too many lots for your capital  

✅ **Do** test new settings in paper mode  
✅ **Do** increase gradually (1 lot → 2 lots → 3 lots)  
✅ **Do** keep SL in 0.50-1.50% range  
✅ **Do** keep profit target in 10-25% range  
✅ **Do** respect the daily loss limit  

---

**Ready to customize? Edit `config.json` now!**
