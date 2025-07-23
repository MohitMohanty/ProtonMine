import json
import time
import random
from typing import List, Dict
from urllib.parse import quote_plus, urljoin
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import cloudscraper
import requests
from .base_scraper import BaseScraper
from config.settings import Config

class DuckDuckGoScraper(BaseScraper):
    def __init__(self):
        super().__init__()
        self.ua = UserAgent()
        self.scraper = cloudscraper.create_scraper()
        
    def search_duckduckgo(self, query: str, num_results: int = 50) -> List[Dict]:
        """Search DuckDuckGo - much more permissive than Google"""
        results = []
        
        # DuckDuckGo doesn't require as much stealth as Google
        headers = {
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        try:
            # Much shorter delay needed for DuckDuckGo
            time.sleep(random.uniform(2, 5))
            
            # DuckDuckGo search URL
            encoded_query = quote_plus(query)
            search_url = f"https://duckduckgo.com/html/?q={encoded_query}"
            
            response = self.scraper.get(search_url, headers=headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract DuckDuckGo results
            result_containers = soup.find_all('div', class_='result')
            
            for container in result_containers[:num_results]:
                title_elem = container.find('a', class_='result__a')
                snippet_elem = container.find('a', class_='result__snippet')
                
                if title_elem:
                    url = title_elem.get('href', '')
                    title = title_elem.get_text().strip()
                    snippet = snippet_elem.get_text().strip() if snippet_elem else ''
                    
                    # Only include trusted domains
                    if url and self.is_trusted_domain(url):
                        results.append({
                            'url': url,
                            'title': title,
                            'snippet': snippet,
                            'source': 'duckduckgo',
                            'search_query': query
                        })
        
        except Exception as e:
            print(f"Error searching DuckDuckGo for '{query}': {e}")
        
        return results
    
    def generate_duckduckgo_dorks(self, keywords: List[str], dork_type: str = "general") -> List[str]:
        """Generate DuckDuckGo-specific search queries"""
        keyword_string = " ".join(keywords)
        
        dork_queries = {
            "general": [
                f'"{keyword_string}" filetype:pdf',
                f'"{keyword_string}" site:edu',
                f'"{keyword_string}" site:gov',
                f'"{keyword_string}" intitle:"{keyword_string}"',
                f'"{keyword_string}" -site:facebook.com -site:twitter.com',
            ],
            "social": [
                f'"{keyword_string}" site:twitter.com',
                f'"{keyword_string}" site:reddit.com',
                f'"{keyword_string}" site:linkedin.com',
                f'"{keyword_string}" site:youtube.com',
            ],
            "news": [
                f'"{keyword_string}" site:reuters.com',
                f'"{keyword_string}" site:bbc.com',
                f'"{keyword_string}" site:cnn.com',
                f'"{keyword_string}" after:2023',  # Recent news
            ],
            "technical": [
                f'"{keyword_string}" site:stackoverflow.com',
                f'"{keyword_string}" site:github.com',
                f'"{keyword_string}" filetype:json',
                f'"{keyword_string}" inurl:api',
            ]
        }
        
        return dork_queries.get(dork_type, dork_queries["general"])
    
    def search(self, keywords: List[str], dork_types: List[str] = ["general"]) -> List[Dict]:
        """Main search method using DuckDuckGo"""
        all_results = []
        
        for dork_type in dork_types:
            print(f"DuckDuckGo {dork_type} search...")
            queries = self.generate_duckduckgo_dorks(keywords, dork_type)
            
            for query in queries:
                print(f"DuckDuckGo search: {query}")
                results = self.search_duckduckgo(query, 20)
                all_results.extend(results)
                
                # Short delay between queries
                time.sleep(random.uniform(3, 6))
        
        # Remove duplicates
        seen_urls = set()
        unique_results = []
        for result in all_results:
            if result['url'] not in seen_urls:
                seen_urls.add(result['url'])
                unique_results.append(result)
        
        return unique_results
    
    def scrape_url(self, url: str) -> Dict:
        """Scrape content from URL found via DuckDuckGo"""
        try:
            headers = {
                'User-Agent': self.ua.random,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Referer': 'https://duckduckgo.com/'
            }
            
            response = self.scraper.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            
            content = self.extract_basic_content(response.text, url)
            
            return {
                'url': url,
                'domain': response.url.split('/')[2] if '//' in response.url else url.split('/')[2],
                'title': content['title'],
                'meta_description': content['meta_description'],
                'content': {
                    'text': content['text'][:15000],  # Limit text length
                    'headings': content['headings'][:25],
                    'links': content['links'][:60]
                },
                'media': {
                    'images': content['images'][:40],
                    'videos': [],
                    'audio': []
                },
                'metadata': {
                    'content_type': response.headers.get('content-type', ''),
                    'language': 'en',
                    'trust_score': 7.5 if self.is_trusted_domain(url) else 5.5,
                    'scraped_via': 'duckduckgo'
                }
            }
        
        except Exception as e:
            print(f"Error scraping {url}: {e}")
            return {}
