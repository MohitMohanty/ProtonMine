import os
import random  # Make sure this is imported
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Database settings
    MONGODB_URL = os.getenv('MONGODB_URL', 'mongodb://localhost:27017/')
    DATABASE_NAME = os.getenv('DATABASE_NAME', 'web_scraper_db')
    
    # Scraping settings (enhanced for dorking)
    MIN_REQUEST_DELAY = 15  # Minimum delay in seconds
    MAX_REQUEST_DELAY = 30  # Maximum delay in seconds
    CONCURRENT_REQUESTS = 1  # Only 1 request at a time
    MAX_REQUESTS_PER_SESSION = 3  # Rotate session frequently
    ROTATE_USER_AGENTS = True
    USE_PROXIES = True
    
    # Dorking settings
    MAX_RESULTS_PER_DORK = 20
    DORK_QUERIES_FILE = 'config/dork_queries.json'
    
    # File paths
    DATA_DIR = 'data'
    MEDIA_DIR = 'data/media'
    LOGS_DIR = 'logs'
    
    # Trust settings
    TRUST_DOMAINS_FILE = 'config/trusted_domains.json'
    
    # User agent for compatibility
    USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    
    # Headers and stealth
    DEFAULT_HEADERS = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    @classmethod
    def get_random_delay(cls):
        """Get a random delay between min and max"""
        return random.uniform(cls.MIN_REQUEST_DELAY, cls.MAX_REQUEST_DELAY)
