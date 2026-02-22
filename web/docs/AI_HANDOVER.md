# AI Handover Document — F&O Sentinel Web Platform

> **Living document.** Update this before any handover to a new AI session or developer.
> Last Updated: 2026-02-22

---

## Project Identity

| | |
|--|--|
| **Product** | F&O Sentinel Web Platform |
| **Founder** | Arun Samant |
| **GitHub** | https://github.com/BratAIExplorer/Arun_FnO |
| **VPS** | 76.13.179.32 — port **8080** (standalone) |
| **Exchange** | mStock only (Phase 1) |
| **Base Bot Repo** | https://github.com/spotontradingtips-creator/Arun-Samant--F-O |

---

## Repository Layout

```
/ (project root — original bot, DO NOT MODIFY)
├── src/                    ← Original trading engine (read-only)
├── main.py                 ← Original bot entry point (read-only)
├── config.json             ← Original bot config (read-only)
├── Dockerfile.web          ← NEW: Docker for web platform
├── docker-compose.web.yml  ← NEW: Local Docker
├── docker-compose.web.prod.yml ← NEW: VPS Docker (port 8080)
└── web/                    ← NEW: Entire web platform lives here
    ├── backend/
    │   ├── app/
    │   │   ├── main.py         ← FastAPI app
    │   │   ├── api/auth.py     ← JWT login/register
    │   │   ├── api/settings.py ← All strategy config API
    │   │   ├── api/bot.py      ← Start/stop/status/OTP
    │   │   ├── models/database.py ← SQLAlchemy models
    │   │   └── core/security.py   ← JWT + Fernet encryption
    │   └── requirements.txt
    ├── frontend/
    │   ├── templates/
    │   │   ├── login.html      ← Login page
    │   │   └── app.html        ← Single-page app
    │   └── static/
    │       ├── css/main.css    ← Apple dark glassmorphic design
    │       └── js/app.js       ← All dashboard logic
    ├── nginx/nginx.conf        ← Reverse proxy config
    ├── .env.example
    ├── docs/
        ├── CHANGELOG.md        ← This version's features
        ├── AI_HANDOVER.md      ← This file
        ├── FEATURES_COMPARISON.md ← Original vs Web comparison
        ├── SECURITY_NO_DOMAIN.md ← How to secure IP access
        └── DEPLOY_VPS.md       ← VPS setup steps
```

---

## Key Decisions Made

| Decision | Choice | Reason |
|----------|--------|--------|
| UI Library | OAT (oat.ink) | Zero deps, 8KB, semantic HTML, mobile-first |
| Backend | FastAPI | Async, easy JWT, Python (matches original engine) |
| Auth | JWT + bcrypt | Standard, stateless, multi-user safe |
| Credential storage | Fernet symmetric encryption | Secrets never stored in plain text |
| Telegram | Per-user bot token | No notification cross-contamination |
| DB (local) | SQLite | Simple, no setup, file-based |
| DB (prod) | PostgreSQL ready | More robust for concurrent users |
| VPS port | 8080 | Unique, avoids conflict with other projects |
| Original bot | Zero modifications | Wrapped, not replaced |

---

## What Was NOT Built Yet (Backlog)

- WebSocket live log streaming (currently 3s polling)
- Trade history page with charts
- Admin user management panel
- Mobile PWA manifest + offline support
- Multi-broker support (Upstox, Angel)
- Automated daily token refresh (cron)

---

## How the Bot Engine Integration Works

The web platform calls the original `src/fno_trading_bot.py`, `src/market_data.py`, and `src/trading_config.py` directly. The `web/backend/app/api/bot.py` creates per-user `Threading.Thread` instances that run the trading loop. User settings from the DB override `TradingConfig` defaults at startup. The original `config.json` is still present but is NOT used by the web platform — all config comes from the DB.

---

## Environment Variables Required

```env
SECRET_KEY=<random 32+ char string>      # JWT signing + Fernet key derivation
DATABASE_URL=sqlite:////app/data/trading.db  # or postgresql://...
ENVIRONMENT=production
```

---

## VPS Deployment (76.13.179.32)

```bash
# One-time setup
git clone https://github.com/BratAIExplorer/Arun_FnO
cd Arun_FnO
cp web/.env.example web/.env
nano web/.env   # Set SECRET_KEY

# Deploy
docker-compose -f docker-compose.web.prod.yml up -d --build

# Access
http://76.13.179.32:8080
```

---

## First-Time User Flow

1. Go to `http://76.13.179.32:8080/login`
2. Register with email + password
3. Expand ⚙️ Strategy Settings
4. Enter mStock API credentials → Save Settings
5. Click "📱 Initiate mStock Login (OTP)" → Enter OTP
6. Configure strategy, capital, notifications → Save Settings
7. Click **START BOT** 🚀
