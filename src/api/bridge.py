import requests
import logging
import threading
from datetime import datetime

class SentinelBridge:
    """Briddge to send data from Bot to FastAPI Hub"""
    API_URL = "http://localhost:8000/api/push"
    
    @staticmethod
    def push_log(module: str, message: str, level: str = "INFO"):
        """Send a log message to the dashboard"""
        try:
            # Run in a separate thread to avoid blocking the bot logic
            payload = {
                "timestamp": datetime.now().strftime("%H:%M:%S"),
                "module": module,
                "message": message,
                "level": level
            }
            threading.Thread(target=SentinelBridge._send, args=(f"{SentinelBridge.API_URL}/log", payload), daemon=True).start()
        except:
            pass

    @staticmethod
    def push_data(data: dict):
        """Send live data (prices, P&L) to the dashboard"""
        try:
            threading.Thread(target=SentinelBridge._send, args=(f"{SentinelBridge.API_URL}/data", data), daemon=True).start()
        except:
            pass

    @staticmethod
    def _send(url: str, payload: dict):
        try:
            requests.post(url, json=payload, timeout=0.1)
        except:
            pass

# Custom Logging Handler for the Bot
class SentinelHandler(logging.Handler):
    def emit(self, record):
        log_entry = self.format(record)
        SentinelBridge.push_log(record.name, log_entry, record.levelname)
