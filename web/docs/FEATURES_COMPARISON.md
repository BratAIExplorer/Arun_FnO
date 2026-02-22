# Features Comparison — Original Bot vs Web Platform

> **Living document.** Updated as new web features ship.
> Last Updated: 2026-02-22

---

## Side-by-Side Comparison

| Feature | Original Bot (CLI) | F&O Sentinel Web Platform |
|---------|-------------------|--------------------------|
| **UI** | Terminal / Streamlit | Browser & Mobile (OAT glassmorphic) |
| **Access** | Local machine only | Any device, any browser |
| **Users** | Single user | Up to 5 users (multi-user, isolated) |
| **Start/Stop** | `python main.py` in terminal | One big button in browser |
| **Config changes** | Edit `config.json`, restart bot | Live in-UI, no restart needed |
| **Credentials** | `.env` file (plain text) | Encrypted in DB (Fernet AES) |
| **mStock Auth** | Manual terminal OTP entry | OTP prompt in browser |
| **Email alerts** | ❌ Not built | ✅ Full SMTP notifications |
| **Telegram alerts** | ❌ Not built | ✅ Per-user bot, 9 event types |
| **Live logs** | Terminal scrolling | Browser terminal panel (3s refresh) |
| **Trade history** | CSV file | DB (queryable, expandable) |
| **Docker** | ❌ | ✅ Local + VPS one-command deploy |
| **Remote VPS** | Manual setup | `docker-compose up -d` |
| **Mobile** | ❌ | ✅ Fully responsive |

---

## Trading Conditions — 100% Preserved

| Condition | Original | Web Platform |
|-----------|----------|-------------|
| MACD + RSI + ADX strategy | ✅ | ✅ Identical code |
| 8 entry conditions | ✅ | ✅ |
| VIX-adjusted stop loss | ✅ | ✅ Configurable per index |
| Dual-speed monitoring (1s) | ✅ | ✅ |
| Daily loss limit | ✅ | ✅ Configurable |
| Daily profit cap | ✅ | ✅ Configurable |
| ATM/ITM strike selection | ✅ | ✅ Configurable |
| State persistence (restart safe) | ✅ | ✅ Extended to DB |
| Anti-duplication | ✅ | ✅ |
| NIFTY, BANKNIFTY, FINNIFTY, SENSEX | ✅ | ✅ Per-user toggle |

---

## What's New in Web Platform

1. **Browser access** — trade from phone, tablet, laptop
2. **Multi-user** — 5 isolated users, no data crossover
3. **Full in-UI config** — change any parameter without touching files
4. **Encrypted credentials** — mStock keys stored securely
5. **Hands-free OTP** — one-time auth via browser prompt
6. **Notifications** — Email + Telegram for all 9 trading events
7. **Docker ready** — deploy locally or on VPS with one command
8. **Living docs** — CHANGELOG, AI_HANDOVER, this file

---

## What's NOT Changed

- All core trading logic (`src/fno_trading_bot.py`, `src/indicators.py`, etc.)
- All strategy conditions and thresholds (only now editable in UI)
- mStock API integration patterns
- State management and position persistence

> The web platform is a **wrapper and UI layer** over the original engine. It does not change any trading behaviour.
