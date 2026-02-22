# 🌅 MORNING READINESS CHECKLIST

Follow these steps every morning at **09:00 AM** to ensure the bot is ready for a safe and profitable session.

### 1. � Connectivity & Authentication (FIRST STEP)
- **Dashboard Status**: Open the Sentinel Hub in your browser.
- **Login Request**: The header must show **"STATUS: ONLINE"** in green.
- **OTP Entry**: If it shows "SESSION EXPIRED", click **"INITIATE LOGIN REQUEST"**, check your phone, and enter the OTP immediately. **The bot cannot talk to the market without this.**

### 2. 📂 State Cleanup
- **Check active positions**: Open `data/positions.json`. If you have no overnight trades, this file must be `{}`.
- **Clear old logs**: Ensure you are looking at the log file with today's date.

### 3. 🤖 Automated Audit (CRITICAL)
Run the following command in your terminal:
```powershell
python pre_flight_audit.py
```
**Wait for ALL CHECKS to return [PASS].** This scan proves that the "Safety Shield" (15-min rule) is active in the code.

### 4. 🚀 Launch Sequence
1. **Restart the Bot**: Close any old terminal windows. Run `python main.py`.
2. **Verify Heartbeat**: Ensure you see "ENTRY MONITORING THREAD STARTED" in the logs.
3. **Verify Settings**: Check the Dashboard to confirm your **Profit Target (Rs 250)** and **Lots** are exactly what you want.

---
> [!IMPORTANT]
> The bot is now "Hardcoded" to wait for 15-minute candle closes. **Never expect a reversal exit at 09:20 or 09:27**; it will always happen at 09:30, 09:45, etc.
