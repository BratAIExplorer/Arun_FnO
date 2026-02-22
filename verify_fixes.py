import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add src to path
sys.path.insert(0, os.path.dirname(__file__))

# Mock dependencies if they don't exist or fail to import
try:
    from src.market_data import MStockAPI
except ImportError:
    # Create a dummy class if import fails due to missing deps
    class MStockAPI:
         pass

class TestFixes(unittest.TestCase):
    @patch('src.market_data.requests.get')
    def test_get_tradebook_405(self, mock_get):
        print("\nTesting get_tradebook with 405 error...")
        # Mock 405 response
        mock_response = MagicMock()
        mock_response.status_code = 405
        mock_get.return_value = mock_response
        
        with patch.dict(os.environ, {
            'API_KEY': 'test', 'API_SECRET': 'test', 'CLIENT_CODE': 'test', 'PASSWORD': 'test'
        }):
            with patch.object(MStockAPI, 'load_access_token', return_value=None):
                try:
                    api = MStockAPI()
                    # Patch get_headers to avoid attribute error if init failed
                    api.get_headers = MagicMock(return_value={})
                    
                    trades = api.get_tradebook()
                    
                    print(f"Tradebook 405 Result: {trades}")
                    self.assertEqual(trades, [], "Should return empty list on 405")
                    print("PASS: get_tradebook handled 405 correctly")
                except Exception as e:
                    self.fail(f"get_tradebook raised exception on 405: {e}")

    @patch('src.market_data.requests.get')
    def test_get_net_positions_dict_return(self, mock_get):
        print("\nTesting get_net_positions with Dict return (instead of List)...")
        # Mock success 200 but data is a dict
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "success",
            "data": {"some": "dict"} # Not a list
        }
        mock_get.return_value = mock_response
        
        with patch.dict(os.environ, {
            'API_KEY': 'test', 'API_SECRET': 'test', 'CLIENT_CODE': 'test', 'PASSWORD': 'test'
        }):
            with patch.object(MStockAPI, 'load_access_token', return_value=None):
                try:
                    api = MStockAPI()
                    api.get_headers = MagicMock(return_value={})
                    
                    positions = api.get_net_positions()
                    
                    print(f"Net Positions Dict Result: {positions}")
                    self.assertEqual(positions, [], "Should return empty list onto dict return")
                    print("PASS: get_net_positions handled Dict return correctly")
                except Exception as e:
                     self.fail(f"get_net_positions raised exception on dict return: {e}")

if __name__ == '__main__':
    unittest.main()
