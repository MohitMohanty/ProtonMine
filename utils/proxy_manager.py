import random
import requests
from typing import List, Optional

class ProxyManager:
    def __init__(self):
        self.proxies = self.load_free_proxies()
        self.current_proxy = None
    
    def load_free_proxies(self) -> List[Dict]:
        """Load free proxy list"""
        # You can get free proxies from various sources
        # This is a basic implementation
        return [
            {'http': 'http://proxy1:port', 'https': 'https://proxy1:port'},
            {'http': 'http://proxy2:port', 'https': 'https://proxy2:port'},
            # Add more proxies
        ]
    
    def get_random_proxy(self) -> Optional[Dict]:
        """Get a random working proxy"""
        if not self.proxies:
            return None
        return random.choice(self.proxies)
    
    def test_proxy(self, proxy: Dict) -> bool:
        """Test if proxy is working"""
        try:
            response = requests.get('http://httpbin.org/ip', 
                                  proxies=proxy, timeout=10)
            return response.status_code == 200
        except:
            return False
