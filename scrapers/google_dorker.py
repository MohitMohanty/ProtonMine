import json
import time
import random
from typing import List, Dict
from urllib.parse import quote_plus, urljoin
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import cloudscraper
from .base_scraper import BaseScraper
from config.settings import Config

class GoogleDorker(BaseScraper):
    def __init__(self):
        super().__init__()
        self.ua = UserAgent()
        self.scraper = cloudscraper.create_scraper()
        
        # Load dork queries
        with open(Config.DORK_QUERIES_FILE, 'r') as f:
            self.dork_queries = json.load(f)
    
    def generate_dork_query(self, keywords: List[str], dork_type: str = "general") -> List[str]:
        """Generate Google dork queries based on keywords"""
        queries = []
        keyword_string = " ".join(keywords)
        
        dork_templates = self.dork_queries.get(f"{dork_type}_dorks", self.dork_queries["general_dorks"])
        
        for template in dork_templates:
            query = template.format(keyword=keyword_string)
            queries.append(query)
        
        return queries
    
    def search_google_dork(self, dork_query: str, num_results: int = 50) -> List[Dict]:
        """Execute Google dork search"""
        results = []
        
        # Rotate user agent
        headers = Config.DEFAULT_HEADERS.copy()
        headers['User-Agent'] = self.ua.random
        
        # Encode the dork query
        encoded_query = quote_plus(dork_query)
        
        # Google search URL
        search_url = f"https://www.google.com/search?q={encoded_query}&num={num_results}"
        
        try:
            # Add random delay
            time.sleep(random.uniform(2, 5))
            
            response = self.scraper.get(search_url, headers=headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract search results
            for result in soup.find_all('div', class_='g'):
                title_elem = result.find('h3')
                link_elem = result.find('a')
                snippet_elem = result.find('span', class_=['aCOpRe', 'st'])
                
                if title_elem and link_elem:
                    href = link_elem.get('href', '')
                    if href.startswith('/url?q='):
                        # Clean Google redirect URL
                        actual_url = href.split('/url?q=')[1].split('&')[0]
                    else:
                        actual_url = href
                    
                    if self.is_trusted_domain(actual_url):
                        results.append({
                            'url': actual_url,
                            'title': title_elem.get_text().strip(),
                            'snippet': snippet_elem.get_text().strip() if snippet_elem else '',
                            'source': 'google_dork',
                            'dork_query': dork_query
                        })
        
        except Exception as e:
            print(f"Error executing dork query '{dork_query}': {e}")
        
        return results
    
    def search(self, keywords: List[str], dork_types: List[str] = ["general"]) -> List[Dict]:
        """Search using multiple dork queries"""
        all_results = []
        
        for dork_type in dork_types:
            print(f"Executing {dork_type} dorks...")
            queries = self.generate_dork_query(keywords, dork_type)
            
            for query in queries:
                print(f"Dorking: {query}")
                results = self.search_google_dork(query, Config.MAX_RESULTS_PER_DORK)
                all_results.extend(results)
                
                # Random delay between queries
                time.sleep(random.uniform(3, 7))
        
        # Remove duplicates
        seen_urls = set()
        unique_results = []
        for result in all_results:
            if result['url'] not in seen_urls:
                seen_urls.add(result['url'])
                unique_results.append(result)
        
        return unique_results
    
    def scrape_url(self, url: str) -> Dict:
        """Scrape content from dorked URL"""
        try:
            headers = Config.DEFAULT_HEADERS.copy()
            headers['User-Agent'] = self.ua.random
            
            response = self.scraper.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            
            content = self.extract_basic_content(response.text, url)
            
            return {
                'url': url,
                'domain': response.url.split('/')[2] if '//' in response.url else url.split('/')[2],
                'title': content['title'],
                'meta_description': content['meta_description'],
                'content': {
                    'text': content['text'][:10000],  # Limit text length
                    'headings': content['headings'][:20],
                    'links': content['links'][:50]
                },
                'media': {
                    'images': content['images'][:30],
                    'videos': [],
                    'audio': []
                },
                'metadata': {
                    'content_type': response.headers.get('content-type', ''),
                    'language': 'en',
                    'trust_score': 8.0 if self.is_trusted_domain(url) else 6.0,
                    'scraped_via': 'google_dork'
                }
            }
        
        except Exception as e:
            print(f"Error scraping {url}: {e}")
            return {}
