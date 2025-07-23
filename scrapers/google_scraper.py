import requests
from typing import List, Dict
from .base_scraper import BaseScraper
from config.settings import Config

class GoogleScraper(BaseScraper):
    def __init__(self):
        super().__init__()
        self.api_key = Config.GOOGLE_API_KEY
        self.search_engine_id = 'your_search_engine_id'  # Get from Google Custom Search
    
    def search(self, keywords: List[str]) -> List[Dict]:
        """Search Google using Custom Search API"""
        results = []
        query = ' '.join(keywords)
        
        if not self.api_key:
            print("Warning: Google API key not configured")
            return results
        
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            'key': self.api_key,
            'cx': self.search_engine_id,
            'q': query,
            'num': 10
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            for item in data.get('items', []):
                if self.is_trusted_domain(item['link']):
                    results.append({
                        'url': item['link'],
                        'title': item['title'],
                        'snippet': item.get('snippet', ''),
                        'source': 'google_search'
                    })
        
        except Exception as e:
            print(f"Google search error: {e}")
        
        return results
    
    def scrape_url(self, url: str) -> Dict:
        """Scrape content from URL"""
        try:
            response = self.make_request(url)
            content = self.extract_basic_content(response.text, url)
            
            return {
                'url': url,
                'domain': requests.utils.urlparse(url).netloc,
                'title': content['title'],
                'meta_description': content['meta_description'],
                'content': {
                    'text': content['text'],
                    'headings': content['headings'],
                    'links': content['links']
                },
                'media': {
                    'images': content['images'],
                    'videos': [],
                    'audio': []
                },
                'metadata': {
                    'content_type': response.headers.get('content-type', ''),
                    'language': 'en',  # Could be detected
                    'trust_score': 8.0 if self.is_trusted_domain(url) else 5.0
                }
            }
        
        except Exception as e:
            print(f"Error scraping {url}: {e}")
            return {}
