import subprocess
import json
import time
import requests
from typing import List, Dict, Set
import dns.resolver
import whois
from urllib.parse import urlparse
import builtwith
from waybackpy import WaybackMachineCDXServerAPI
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import undetected_chromedriver as uc

class OSINTReconEngine:
    def __init__(self):
        self.discovered_domains = set()
        self.discovered_subdomains = set()
        self.discovered_urls = set()
        self.intelligence_data = []
        
        # Setup Selenium with stealth capabilities
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
        """Setup undetected Chrome driver for advanced scraping"""
        options = uc.ChromeOptions()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        self.driver = uc.Chrome(options=options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    def comprehensive_subdomain_enumeration(self, domain: str) -> Set[str]:
        """Advanced subdomain discovery using multiple OSINT techniques"""
        subdomains = set()
        
        print(f"🔍 Enumerating subdomains for: {domain}")
        
        # Method 1: Sublist3r
        try:
            import sublist3r
            result = sublist3r.main(domain, 40, None, ports=None, silent=True, verbose=False,
                                  enable_bruteforce=False, engines=None)
            if result:
                subdomains.update(result)
                print(f"✅ Sublist3r found {len(result)} subdomains")
        except Exception as e:
            print(f"⚠️ Sublist3r error: {e}")
        
        # Method 2: Certificate Transparency Logs
        try:
            ct_subdomains = self.certificate_transparency_search(domain)
            subdomains.update(ct_subdomains)
            print(f"✅ Certificate Transparency found {len(ct_subdomains)} subdomains")
        except Exception as e:
            print(f"⚠️ CT search error: {e}")
        
        # Method 3: DNS Brute Force
        try:
            brute_subdomains = self.dns_bruteforce(domain)
            subdomains.update(brute_subdomains)
            print(f"✅ DNS Brute Force found {len(brute_subdomains)} subdomains")
        except Exception as e:
            print(f"⚠️ DNS brute force error: {e}")
        
        # Method 4: Wayback Machine URLs
        try:
            wayback_subdomains = self.wayback_machine_search(domain)
            subdomains.update(wayback_subdomains)
            print(f"✅ Wayback Machine found {len(wayback_subdomains)} subdomains")
        except Exception as e:
            print(f"⚠️ Wayback search error: {e}")
        
        return subdomains
    
    def certificate_transparency_search(self, domain: str) -> Set[str]:
        """Search Certificate Transparency logs for subdomains"""
        subdomains = set()
        
        # crt.sh API
        try:
            url = f"https://crt.sh/?q=%25.{domain}&output=json"
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                certificates = response.json()
                for cert in certificates:
                    name_value = cert.get('name_value', '')
                    for subdomain in name_value.split('\n'):
                        subdomain = subdomain.strip()
                        if subdomain and domain in subdomain:
                            subdomains.add(subdomain)
        except Exception as e:
            print(f"crt.sh search failed: {e}")
        
        return subdomains
    
    def dns_bruteforce(self, domain: str) -> Set[str]:
        """DNS brute force using common subdomain wordlist"""
        subdomains = set()
        
        # Common Indian government/military subdomains
        wordlist = [
            'www', 'mail', 'ftp', 'admin', 'test', 'dev', 'staging', 'portal',
            'secure', 'login', 'api', 'cdn', 'static', 'media', 'assets',
            'recruitment', 'career', 'jobs', 'training', 'academy', 'college',
            'naval', 'navy', 'defence', 'defense', 'military', 'ops', 'operations',
            'command', 'fleet', 'base', 'station', 'ship', 'vessel', 'submarine',
            'logistics', 'supply', 'stores', 'workshop', 'dockyard', 'shipyard',
            'communications', 'signals', 'radar', 'sonar', 'weapons', 'armament'
        ]
        
        resolver = dns.resolver.Resolver()
        resolver.timeout = 5
        resolver.lifetime = 5
        
        for subdomain in wordlist:
            try:
                full_domain = f"{subdomain}.{domain}"
                resolver.resolve(full_domain, 'A')
                subdomains.add(full_domain)
                print(f"  ✅ Found: {full_domain}")
                time.sleep(0.1)  # Rate limiting
            except:
                pass
        
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
                if parsed.netloc:
                    subdomains.add(parsed.netloc)
        except Exception as e:
            print(f"Wayback Machine search failed: {e}")
        
        return subdomains
    
    def advanced_web_scraping(self, url: str) -> Dict:
        """Advanced web scraping with multiple fallback methods"""
        data = {
            'url': url,
            'title': '',
            'content': '',
            'links': [],
            'media': {'images': [], 'documents': [], 'videos': []},
            'metadata': {},
            'technology_stack': {},
            'whois_data': {}
        }
        
        try:
            # Method 1: Selenium with stealth
            print(f"🌐 Scraping with Selenium: {url}")
            self.driver.get(url)
            time.sleep(3)  # Wait for page load
            
            # Extract basic information
            data['title'] = self.driver.title
            data['content'] = self.driver.find_element("tag name", "body").text[:5000]
            
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
            for link in data['links']:
                url_lower = link['url'].lower()
                if any(ext in url_lower for ext in ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt']):
                    data['media']['documents'].append(link)
            
            print(f"✅ Successfully scraped: {len(data['content'])} chars, {len(data['links'])} links")
            
        except Exception as e:
            print(f"❌ Selenium scraping failed for {url}: {e}")
            
            # Fallback to requests
            try:
                print(f"🔄 Fallback to requests: {url}")
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
                response = requests.get(url, headers=headers, timeout=10)
                response.raise_for_status()
                
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(response.text, 'html.parser')
                
                data['title'] = soup.title.string if soup.title else ''
                data['content'] = soup.get_text()[:5000]
                
                print(f"✅ Fallback successful: {len(data['content'])} chars")
                
            except Exception as e2:
                print(f"❌ Fallback also failed: {e2}")
        
        # Get technology stack
        try:
            parsed_domain = urlparse(url).netloc
            data['technology_stack'] = builtwith.parse(url)
            print(f"📊 Technology stack detected for {parsed_domain}")
        except:
            pass
        
        # Get WHOIS data
        try:
            parsed_domain = urlparse(url).netloc
            data['whois_data'] = dict(whois.whois(parsed_domain))
            print(f"📋 WHOIS data retrieved for {parsed_domain}")
        except:
            pass
        
        return data
    
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
        for target in all_targets[:20]:  # Limit to first 20 to avoid overwhelming
            if not target.startswith('http'):
                target = f"https://{target}"
            
            scraped_data = self.advanced_web_scraping(target)
            if scraped_data['content']:
                results['urls_scraped'].append(scraped_data)
                
                # Collect media and documents
                results['media_found'].extend(scraped_data['media']['images'])
                results['documents_found'].extend(scraped_data['media']['documents'])
                
                # Store intelligence
                intelligence_item = {
                    'source': target,
                    'title': scraped_data['title'],
                    'content_preview': scraped_data['content'][:500],
                    'links_count': len(scraped_data['links']),
                    'media_count': len(scraped_data['media']['images']),
                    'documents_count': len(scraped_data['media']['documents']),
                    'technology_stack': scraped_data['technology_stack'],
                    'timestamp': time.time()
                }
                results['intelligence_gathered'].append(intelligence_item)
            
            time.sleep(2)  # Rate limiting
        
        # Convert sets to lists for JSON serialization
        results['domains_discovered'] = list(results['domains_discovered'])
        results['subdomains_discovered'] = list(results['subdomains_discovered'])
        
        return results
    
    def __del__(self):
        """Cleanup Selenium driver"""
        if hasattr(self, 'driver'):
            self.driver.quit()
