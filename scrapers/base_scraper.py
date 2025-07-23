import requests
import time
import json
from abc import ABC, abstractmethod
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from typing import Dict, List
from config.settings import Config

class BaseScraper(ABC):
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': Config.USER_AGENT
        })
        
        # Load trusted domains
        with open(Config.TRUST_DOMAINS_FILE, 'r') as f:
            self.trusted_domains = json.load(f)
    
    def is_trusted_domain(self, url: str) -> bool:
        """Check if URL belongs to trusted domain"""
        domain = urlparse(url).netloc.lower()
        
        for category, domains in self.trusted_domains.items():
            for trusted_domain in domains:
                if trusted_domain.startswith('.'):
                    # Handle TLD patterns like .gov, .edu
                    if domain.endswith(trusted_domain):
                        return True
                elif trusted_domain in domain:
                    return True
        return False
    
    def make_request(self, url: str) -> requests.Response:
        """Make HTTP request with rate limiting"""
        time.sleep(Config.REQUEST_DELAY)
        response = self.session.get(url, timeout=10)
        response.raise_for_status()
        return response
    
    def extract_basic_content(self, html: str, url: str) -> Dict:
        """Extract basic content from HTML"""
        soup = BeautifulSoup(html, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        content = {
            'title': soup.title.string if soup.title else '',
            'meta_description': '',
            'headings': [],
            'text': soup.get_text().strip(),
            'links': [],
            'images': []
        }
        
        # Extract meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc:
            content['meta_description'] = meta_desc.get('content', '')
        
        # Extract headings
        for heading in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            content['headings'].append(heading.get_text().strip())
        
        # Extract links
        for link in soup.find_all('a', href=True):
            full_url = urljoin(url, link['href'])
            content['links'].append(full_url)
        
        # Extract images
        for img in soup.find_all('img', src=True):
            img_url = urljoin(url, img['src'])
            content['images'].append({
                'url': img_url,
                'alt_text': img.get('alt', ''),
                'caption': img.get('title', '')
            })
        
        return content
    
    @abstractmethod
    def search(self, keywords: List[str]) -> List[Dict]:
        """Search for content based on keywords"""
        pass
    
    @abstractmethod
    def scrape_url(self, url: str) -> Dict:
        """Scrape content from specific URL"""
        pass
