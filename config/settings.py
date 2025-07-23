import os
from dotenv import load_dotenv
from fake_useragent import UserAgent   # already in requirements


load_dotenv()

class Config:
    # Database settings
    MONGODB_URL = os.getenv('MONGODB_URL', 'mongodb://localhost:27017/')
    DATABASE_NAME = os.getenv('DATABASE_NAME', 'web_scraper_db')
    
    # Scraping settings (enhanced for dorking)
    REQUEST_DELAY = 2  # Increased delay for dorking
    CONCURRENT_REQUESTS = 3  # Reduced to avoid detection
    ROTATE_USER_AGENTS = True
    USE_PROXIES = True
    
    # Dorking settings
    MAX_RESULTS_PER_DORK = 50
    DORK_QUERIES_FILE = 'config/dork_queries.json'
    
    # File paths
    DATA_DIR = 'data'
    MEDIA_DIR = 'data/media'
    LOGS_DIR = 'logs'
    
    # Trust settings
    TRUST_DOMAINS_FILE = 'config/trusted_domains.json'
    USER_AGENT = UserAgent().random 
    
    # Headers and stealth
    DEFAULT_HEADERS = {
        'User-Agent': USER_AGENT,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
