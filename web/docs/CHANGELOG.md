# Changelog — F&O Sentinel Web Platform

> Living document. Updated with every feature change or deployment.

---

## [1.0.0] — 2026-02-22 (Initial Release)

### Added
- **Web Platform Launch**: Full FastAPI + OAT UI single-page web application
- **Advanced Auth Flow**: 
  - Register page (`/register`) with full-name capture
  - Forgot Password flow with email links
  - Reset Password page via secure tokens
  - Email confirmation flow
- **Multi-User Auth**: JWT-based login for up to 5 users, fully isolated
- **Single-Page Dashboard** (`/app`):
  - BIG START/STOP button (Command Center)
  - 4 live stat cards: Capital, Today P&L, Profit Cap Left, Bot Status
  - Active Positions section with live LTP and P&L
  - Live Signals panel (NIFTY, BANKNIFTY, FINNIFTY, SENSEX)
  - Full in-UI Strategy Settings (all conditions editable, no file editing)
  - Terminal log (live, last 100 entries, auto-scroll)
- **100% In-UI Configuration**:
  - Wallet amount, daily loss limit, daily profit cap
  - RSI range, ADX min, VIX min, profit target, strike depth
  - Trading hours (open, cutoff)
  - VIX-band stop loss per index (Low/Mid/High)
  - Lot sizes per index
  - Active/inactive index toggles
  - mStock API credentials (encrypted, never stored in plain text)
  - Email + Telegram notification config (per-user bot token)
- **Hands-Free mStock Auth**: OTP prompt in UI, token saved encrypted in DB
- **Deep-Dive Trade Capture**: Enhanced `TradeRecord` model to store RSI, ADX, MACD, and full signals JSON for every entry/exit
- **IP Security Guide**: Added `SECURITY_NO_DOMAIN.md` with SSH tunneling and VPN instructions
- **Paper / Live Toggle**: Inline radio with confirmation dialog for LIVE
- **Notifications**: Email (SMTP) + Telegram (per-user bot) for all 9 event types
- **Docker Deployment**: Local (`docker-compose.web.yml`) + VPS (`docker-compose.web.prod.yml` on port 8080)
- **Standalone VPS**: Port 8080 on 76.13.179.32, isolated from all other projects

### Architecture
- Backend: FastAPI + SQLAlchemy (SQLite local, PostgreSQL ready)
- Frontend: OAT UI (8KB) + Vanilla JS + Apple glassmorphic CSS
- Auth: JWT + bcrypt + Fernet encryption for credentials
- Bot Engine: Original `src/` code wrapped, zero modifications

### Original Project (Untouched)
- `main.py`, `src/`, `config.json`, all `.bat` files — zero changes
- Web platform lives entirely in `web/`, `Dockerfile.web`, `docker-compose.web*.yml`

---

## Upcoming
- WebSocket live log streaming (replaces 3s polling)
- Trade history page with daily P&L chart
- Admin user management panel
- Mobile PWA manifest
