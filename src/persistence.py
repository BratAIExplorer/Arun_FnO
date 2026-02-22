import json
import os
import logging
from datetime import datetime
from typing import Dict, Any, List
from src.trading_models import Position, TradeType, ExitReason

logger = logging.getLogger(__name__)

class StateManager:
    """Manages persistence of trading state to disk"""
    
    FILE_PATH = "data/positions.json"
    
    @staticmethod
    def _json_serial(obj):
        """JSON serializer for objects not serializable by default json code"""
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, TradeType):
            return obj.value
        if isinstance(obj, ExitReason):
            return obj.value
        raise TypeError (f"Type {type(obj)} not serializable")

    @staticmethod
    def save_positions(positions: Dict[str, Position]):
        """Save active positions to JSON file"""
        try:
            os.makedirs("data", exist_ok=True)
            
            # Convert Position objects to dicts
            data = {}
            for underlying, pos in positions.items():
                pos_dict = pos.__dict__.copy()
                data[underlying] = pos_dict
            
            # Atomic save: Write to temp file then rename
            tmp_path = StateManager.FILE_PATH + ".tmp"
            with open(tmp_path, 'w') as f:
                json.dump(data, f, default=StateManager._json_serial, indent=4)
            
            # Use os.replace for atomic operation
            os.replace(tmp_path, StateManager.FILE_PATH)
                
            logger.debug(f"Saved {len(positions)} positions to state file")
            
        except Exception as e:
            logger.error(f"Failed to save state: {e}")
            if 'tmp_path' in locals() and os.path.exists(tmp_path):
                os.remove(tmp_path)

    @staticmethod
    def load_positions() -> Dict[str, Position]:
        """Load positions from JSON file"""
        if not os.path.exists(StateManager.FILE_PATH):
            return {}
            
        try:
            with open(StateManager.FILE_PATH, 'r') as f:
                data = json.load(f)
                
            loaded_positions = {}
            for underlying, pos_data in data.items():
                # Reconstruct Position object
                # Convert ISO strings back to datetime and Enums
                if pos_data.get('entry_time'):
                    pos_data['entry_time'] = datetime.fromisoformat(pos_data['entry_time'])
                if pos_data.get('exit_time'):
                    pos_data['exit_time'] = datetime.fromisoformat(pos_data['exit_time'])
                    
                # Enum conversion
                if pos_data.get('trade_type'):
                    pos_data['trade_type'] = TradeType(pos_data['trade_type'])
                if pos_data.get('exit_reason'):
                    pos_data['exit_reason'] = ExitReason(pos_data['exit_reason'])
                    
                # Create object
                # Filter out keys that might not match __init__ if class changed, 
                # but dataclass typically accepts these if they match fields.
                # Inspect Position fields:
                # position_id, underlying, trade_type, entry_time, entry_price, 
                # entry_underlying_price, lot_size, sl_percentage, vix_at_entry, ...
                
                # Safer: construct with known keys
                position = Position(**pos_data)
                loaded_positions[underlying] = position
                
            logger.info(f"Loaded {len(loaded_positions)} active positions from disk")
            return loaded_positions
            
        except Exception as e:
            logger.error(f"Failed to load state: {e}")
            return {}

    @staticmethod
    def save_history(history: List[Position]):
        """Save closed trades to JSON file"""
        try:
            os.makedirs("data", exist_ok=True)
            
            data = []
            for pos in history:
                data.append(pos.__dict__)
                
            # Atomic save: Write to temp file then rename
            hist_path = "data/daily_history.json"
            tmp_path = hist_path + ".tmp"
            with open(tmp_path, 'w') as f:
                json.dump(data, f, default=StateManager._json_serial, indent=4)
            
            os.replace(tmp_path, hist_path)
                
            logger.debug(f"Saved {len(history)} historical trades to state file")
            
        except Exception as e:
            logger.error(f"Failed to save history: {e}")
            if 'tmp_path' in locals() and os.path.exists(tmp_path):
                os.remove(tmp_path)

    @staticmethod
    def load_history() -> List[Position]:
        """Load closed trades from JSON file"""
        try:
            if not os.path.exists("data/daily_history.json"):
                return []
                
            with open("data/daily_history.json", 'r') as f:
                content = f.read().strip()
                if not content:
                    return []
                data = json.loads(content)
                
            history = []
            for pos_data in data:
                # Convert date strings
                if pos_data.get('entry_time'):
                    pos_data['entry_time'] = datetime.fromisoformat(pos_data['entry_time'])
                if pos_data.get('exit_time'):
                    pos_data['exit_time'] = datetime.fromisoformat(pos_data['exit_time'])
                
                # Enum conversion
                if pos_data.get('trade_type'):
                    pos_data['trade_type'] = TradeType(pos_data['trade_type'])
                if pos_data.get('exit_reason'):
                    pos_data['exit_reason'] = ExitReason(pos_data['exit_reason'])
                    
                history.append(Position(**pos_data))
                
            return history
        except Exception as e:
            logger.error(f"Failed to load history: {e}")
            return []
