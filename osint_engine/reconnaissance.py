import subprocess
import json
import time
import random
import requests
from typing import List, Dict, Set
import dns.resolver
import whois
from urllib.parse import urlparse, urljoin
import builtwith
from waybackpy import WaybackMachineCDXServerAPI
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import undetected_chromedriver as uc
from bs4 import BeautifulSoup
import concurrent.futures
import threading

class OSINTReconEngine:
    def __init__(self):
        self.discovered_domains = set()
        self.discovered_subdomains = set()
        self.discovered_urls = set()
        self.intelligence_data = []
        
        # Setup Selenium with error handling
        self.setup_selenium()
        
        # Indian Navy known domains for reconnaissance
        self.seed_domains = [
            'indiannavy.nic.in',
            'joinindiannavy.gov.in',
            'indiannavy.gov.in',
            'nausena-bharti.nic.in',
            'mod.gov.in',
            'drdo.gov.in'
        ]
    
    def setup_selenium(self):
        """Setup Chrome driver with proper error handling"""
        try:
            options = uc.ChromeOptions()
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--disable-web-security')
            options.add_argument('--disable-images')
            options.add_argument('--disable-javascript')
            
            # Simple user agent
            options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            options.add_argument('--window-size=1920,1080')
            
            self.driver = uc.Chrome(options=options)
            print("✅ Selenium Chrome driver initialized successfully")
            
        except Exception as e:
            print(f"❌ Selenium setup failed: {e}")
            print("🔄 Continuing with requests-only mode...")
            self.driver = None
    
    def comprehensive_subdomain_enumeration(self, domain: str) -> Set[str]:
        """Enhanced subdomain discovery using multiple working methods"""
        subdomains = set()
        
        print(f"🔍 Enumerating subdomains for: {domain}")
        
        # Method 1: Certificate Transparency (Most Reliable)
        try:
            ct_subdomains = self.certificate_transparency_search(domain)
            subdomains.update(ct_subdomains)
            print(f"✅ Certificate Transparency found {len(ct_subdomains)} subdomains")
        except Exception as e:
            print(f"⚠️ CT search error: {e}")
        
        # Method 2: DNS Brute Force (Always Works)
        try:
            brute_subdomains = self.dns_bruteforce(domain)
            subdomains.update(brute_subdomains)
            print(f"✅ DNS Brute Force found {len(brute_subdomains)} subdomains")
        except Exception as e:
            print(f"⚠️ DNS brute force error: {e}")
        
        # Method 3: Wayback Machine (Reliable)
        try:
            wayback_subdomains = self.wayback_machine_search(domain)
            subdomains.update(wayback_subdomains)
            print(f"✅ Wayback Machine found {len(wayback_subdomains)} subdomains")
        except Exception as e:
            print(f"⚠️ Wayback search error: {e}")
        
        # Method 4: Alternative API-based enumeration
        try:
            api_subdomains = self.alternative_subdomain_search(domain)
            subdomains.update(api_subdomains)
            print(f"✅ API search found {len(api_subdomains)} subdomains")
        except Exception as e:
            print(f"⚠️ API search error: {e}")
        
        return subdomains
    
    def certificate_transparency_search(self, domain: str) -> Set[str]:
        """Enhanced Certificate Transparency search with multiple sources"""
        subdomains = set()
        
        # Source 1: crt.sh
        try:
            url = f"https://crt.sh/?q=%25.{domain}&output=json"
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            response = requests.get(url, timeout=30, headers=headers)
            
            if response.status_code == 200:
                certificates = response.json()
                for cert in certificates:
                    name_value = cert.get('name_value', '')
                    for subdomain in name_value.split('\n'):
                        subdomain = subdomain.strip().replace('*.', '')
                        if subdomain and domain in subdomain and not subdomain.startswith('.'):
                            subdomains.add(subdomain)
        except Exception as e:
            print(f"crt.sh search failed: {e}")
        
        # Source 2: Alternative CT log source
        try:
            url = f"https://certspotter.com/api/v1/issuances?domain={domain}&include_subdomains=true&expand=dns_names"
            response = requests.get(url, timeout=20)
            
            if response.status_code == 200:
                data = response.json()
                for item in data:
                    dns_names = item.get('dns_names', [])
                    for name in dns_names:
                        if domain in name and not name.startswith('*.'):
                            subdomains.add(name)
        except Exception as e:
            print(f"Certspotter search failed: {e}")
        
        return subdomains
    
    def alternative_subdomain_search(self, domain: str) -> Set[str]:
        """Alternative subdomain enumeration using HackerTarget API"""
        subdomains = set()
        
        try:
            # HackerTarget API (Free and reliable)
            url = f"https://api.hackertarget.com/hostsearch/?q={domain}"
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                lines = response.text.strip().split('\n')
                for line in lines:
                    if ',' in line:  # Format: subdomain,ip
                        subdomain = line.split(',')[0]
                        if domain in subdomain:
                            subdomains.add(subdomain)
        except Exception as e:
            print(f"HackerTarget API failed: {e}")
        
        return subdomains
    
    def dns_bruteforce(self, domain: str) -> Set[str]:
        """Enhanced DNS brute force with Indian Navy specific wordlist"""
        subdomains = set()
        
        # Extended Indian Navy/Government wordlist
        naval_wordlist = [
            # Basic
            'www', 'mail', 'ftp', 'admin', 'test', 'dev', 'staging', 'portal',
            # Naval specific
            'naval', 'navy', 'fleet', 'command', 'operations', 'ops', 'base',
            'station', 'dockyard', 'shipyard', 'submarine', 'vessel', 'ship',
            # Military/Defense
            'defence', 'defense', 'military', 'security', 'intel', 'logistics',
            'supply', 'stores', 'weapons', 'armament', 'communications', 'signals',
            # Indian Government
            'recruitment', 'career', 'jobs', 'training', 'academy', 'college',
            'tender', 'procurement', 'notification', 'circular', 'order',
            # Technical
            'api', 'cdn', 'static', 'media', 'assets', 'files', 'docs', 'archive',
            'login', 'secure', 'intranet', 'extranet', 'vpn', 'remote'
        ]
        
        def check_subdomain(subdomain):
            try:
                full_domain = f"{subdomain}.{domain}"
                resolver = dns.resolver.Resolver()
                resolver.timeout = 3
                resolver.lifetime = 3
                resolver.resolve(full_domain, 'A')
                return full_domain
            except:
                return None
        
        print(f"  🔍 Testing {len(naval_wordlist)} subdomains...")
        
        # Use threading for faster enumeration
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            future_to_subdomain = {executor.submit(check_subdomain, sub): sub for sub in naval_wordlist}
            
            for future in concurrent.futures.as_completed(future_to_subdomain):
                result = future.result()
                if result:
                    subdomains.add(result)
                    print(f"    ✅ Found: {result}")
        
        return subdomains
    
    def wayback_machine_search(self, domain: str) -> Set[str]:
        """Search Wayback Machine for historical URLs"""
        subdomains = set()
        
        try:
            cdx_api = WaybackMachineCDXServerAPI(f"*.{domain}")
            snapshots = cdx_api.snapshots()
            
            for snapshot in snapshots[:100]:  # Limit to first 100
                url = snapshot.original
                parsed = urlparse(url)
                if parsed.netloc and domain in parsed.netloc:
                    subdomains.add(parsed.netloc)
        except Exception as e:
            print(f"Wayback Machine search failed: {e}")
        
        return subdomains
    
    def advanced_web_scraping(self, url: str) -> Dict:
        """Multi-method web scraping with robust fallbacks"""
        
        # Try Selenium first if available
        if hasattr(self, 'driver') and self.driver is not None:
            try:
                return self.scrape_with_selenium(url)
            except Exception as e:
                print(f"⚠️ Selenium failed for {url}: {e}")
        
        # Fallback to requests
        return self.scrape_with_requests(url)
    
    def scrape_with_selenium(self, url: str) -> Dict:
        """Selenium-based web scraping"""
        data = {
            'url': url,
            'title': '',
            'content': '',
            'links': [],
            'media': {'images': [], 'documents': [], 'videos': []},
            'metadata': {},
            'scraped_successfully': False
        }
        
        try:
            print(f"🌐 Scraping with Selenium: {url}")
            self.driver.get(url)
            time.sleep(3)  # Wait for page load
            
            # Extract basic information
            data['title'] = self.driver.title
            data['content'] = self.driver.find_element("tag name", "body").text[:5000]
            data['scraped_successfully'] = True
            
            # Extract links
            links = self.driver.find_elements("tag name", "a")
            for link in links[:50]:  # Limit to first 50 links
                href = link.get_attribute("href")
                if href and href.startswith('http'):
                    data['links'].append({
                        'url': href,
                        'text': link.text.strip()[:100]
                    })
            
            # Extract images
            images = self.driver.find_elements("tag name", "img")
            for img in images[:20]:  # Limit to first 20 images
                src = img.get_attribute("src")
                if src:
                    data['media']['images'].append({
                        'url': src,
                        'alt': img.get_attribute("alt") or '',
                        'title': img.get_attribute("title") or ''
                    })
            
            # Extract document links
            document_extensions = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx']
            for link in data['links']:
                if any(ext in link['url'].lower() for ext in document_extensions):
                    data['media']['documents'].append(link)
            
            print(f"✅ Selenium scraped: {len(data['content'])} chars, {len(data['links'])} links")
            
        except Exception as e:
            print(f"❌ Selenium scraping failed for {url}: {e}")
        
        return data
    
    def scrape_with_requests(self, url: str) -> Dict:
        """Reliable requests-based scraping"""
        data = {
            'url': url,
            'title': '',
            'content': '',
            'links': [],
            'media': {'images': [], 'documents': [], 'videos': []},
            'metadata': {},
            'scraped_successfully': False
        }
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            
            response = requests.get(url, headers=headers, timeout=15, verify=False)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract basic content
            data['title'] = soup.title.string if soup.title else ''
            data['content'] = soup.get_text()[:5000]
            data['scraped_successfully'] = True
            
            # Extract links
            for link in soup.find_all('a', href=True)[:50]:
                href = link.get('href')
                if href and (href.startswith('http') or href.startswith('/')):
                    if href.startswith('/'):
                        href = urljoin(url, href)
                    data['links'].append({
                        'url': href,
                        'text': link.get_text().strip()[:100]
                    })
            
            # Extract images
            for img in soup.find_all('img', src=True)[:20]:
                src = img.get('src')
                if src:
                    if src.startswith('/'):
                        src = urljoin(url, src)
                    data['media']['images'].append({
                        'url': src,
                        'alt': img.get('alt', ''),
                        'title': img.get('title', '')
                    })
            
            # Extract documents
            document_extensions = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx']
            for link in data['links']:
                if any(ext in link['url'].lower() for ext in document_extensions):
                    data['media']['documents'].append(link)
            
            print(f"✅ Scraped: {len(data['content'])} chars, {len(data['links'])} links, {len(data['media']['documents'])} docs")
            
        except Exception as e:
            print(f"❌ Failed to scrape {url}: {e}")
        
        return data
    
    def get_technology_stack(self, url: str) -> Dict:
        """Get technology stack information"""
        try:
            return builtwith.parse(url)
        except Exception as e:
            print(f"Technology detection failed for {url}: {e}")
            return {}
    
    def get_whois_data(self, url: str) -> Dict:
        """Get WHOIS information"""
        try:
            parsed_domain = urlparse(url).netloc
            return dict(whois.whois(parsed_domain))
        except Exception as e:
            print(f"WHOIS lookup failed for {url}: {e}")
            return {}
    
    def indian_navy_focused_reconnaissance(self) -> Dict:
        """Comprehensive OSINT reconnaissance focused on Indian Navy"""
        results = {
            'domains_discovered': set(),
            'subdomains_discovered': set(),
            'urls_scraped': [],
            'intelligence_gathered': [],
            'media_found': [],
            'documents_found': []
        }
        
        print("🇮🇳 Starting Indian Navy OSINT Reconnaissance...")
        
        # Phase 1: Subdomain enumeration for all seed domains
        for domain in self.seed_domains:
            print(f"\n📡 Phase 1: Subdomain enumeration for {domain}")
            subdomains = self.comprehensive_subdomain_enumeration(domain)
            results['subdomains_discovered'].update(subdomains)
            results['domains_discovered'].add(domain)
        
        # Phase 2: Deep scraping of discovered subdomains
        all_targets = list(results['domains_discovered']) + list(results['subdomains_discovered'])
        
        print(f"\n🌐 Phase 2: Deep scraping {len(all_targets)} targets...")
        for i, target in enumerate(all_targets[:20]):  # Limit to first 20 to avoid overwhelming
            print(f"[{i+1}/{min(20, len(all_targets))}] Processing: {target}")
            
            if not target.startswith('http'):
                target = f"https://{target}"
            
            scraped_data = self.advanced_web_scraping(target)
            if scraped_data['scraped_successfully']:
                results['urls_scraped'].append(scraped_data)
                
                # Collect media and documents
                results['media_found'].extend(scraped_data['media']['images'])
                results['documents_found'].extend(scraped_data['media']['documents'])
                
                # Get additional metadata
                tech_stack = self.get_technology_stack(target)
                whois_data = self.get_whois_data(target)
                
                # Store intelligence
                intelligence_item = {
                    'source': target,
                    'title': scraped_data['title'],
                    'content_preview': scraped_data['content'][:500],
                    'links_count': len(scraped_data['links']),
                    'media_count': len(scraped_data['media']['images']),
                    'documents_count': len(scraped_data['media']['documents']),
                    'technology_stack': tech_stack,
                    'whois_data': whois_data,
                    'timestamp': time.time()
                }
                results['intelligence_gathered'].append(intelligence_item)
                
                print(f"✅ Intelligence gathered from {target}")
            else:
                print(f"❌ Failed to gather intelligence from {target}")
            
            time.sleep(2)  # Rate limiting
        
        # Convert sets to lists for JSON serialization
        results['domains_discovered'] = list(results['domains_discovered'])
        results['subdomains_discovered'] = list(results['subdomains_discovered'])
        
        return results
    
    def __del__(self):
        """Cleanup Selenium driver"""
        if hasattr(self, 'driver') and self.driver:
            try:
                self.driver.quit()
            except:
                pass
