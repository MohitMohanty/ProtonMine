from playwright.sync_api import sync_playwright
import json
import re
from typing import Dict, List
from config.settings import Config

class ReverseEngineer:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.page = None
        self.setup_browser()
    
    def setup_browser(self):
        """Setup Playwright browser"""
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-dev-shm-usage']
        )
        self.page = self.browser.new_page()
    
    def find_api_endpoints(self, url: str) -> List[str]:
        """Find potential API endpoints from page source"""
        try:
            self.page.goto(url)
            page_source = self.page.content()
            
            # Same regex patterns as before
            api_patterns = [
                r'["\']([^"\']*api[^"\']*)["\']',
                r'["\']([^"\']*\.json[^"\']*)["\']',
                r'["\']([^"\']*graphql[^"\']*)["\']',
                r'["\']([^"\']*rest[^"\']*)["\']',
                r'fetch\(["\']([^"\']+)["\']',
            ]
            
            endpoints = []
            for pattern in api_patterns:
                matches = re.findall(pattern, page_source, re.IGNORECASE)
                endpoints.extend(matches)
            
            return list(set(endpoints))
        
        except Exception as e:
            print(f"Error finding API endpoints for {url}: {e}")
            return []
    
    def cleanup(self):
        """Clean up browser resources"""
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
    
    def __del__(self):
        """Ensure cleanup on deletion"""
        self.cleanup()
