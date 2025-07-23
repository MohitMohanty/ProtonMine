import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Database settings
    MONGODB_URL = os.getenv('MONGODB_URL', 'mongodb://localhost:27017/')
    DATABASE_NAME = os.getenv('DATABASE_NAME', 'web_scraper_db')
    
    # API Keys
    GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY', '')
    TWITTER_BEARER_TOKEN = os.getenv('TWITTER_BEARER_TOKEN', '')
    YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY', '')
    
    # Scraping settings
    REQUEST_DELAY = 1  # seconds between requests
    CONCURRENT_REQUESTS = 8
    USER_AGENT = 'WebScrapingBot/1.0'
    
    # File paths
    DATA_DIR = 'data'
    MEDIA_DIR = 'data/media'
    LOGS_DIR = 'logs'
    
    # Trust settings
    TRUST_DOMAINS_FILE = 'config/trusted_domains.json'
