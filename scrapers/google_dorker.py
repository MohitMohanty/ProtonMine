import json
import time
import random
import re
from typing import List, Dict
from urllib.parse import quote_plus, urljoin, urlparse
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import cloudscraper
import requests
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
        
        # Enhanced anti-detection
        self.session_requests = 0
        self.max_requests_per_session = 5
        
        # Enhanced media patterns for better detection
        self.media_patterns = {
            'documents': ['.pdf', '.doc', '.docx', '.ppt', '.pptx', '.xls', '.xlsx', '.txt', '.rtf', '.odt'],
            'images': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg', '.tiff', '.ico'],
            'videos': ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.3gp'],
            'audio': ['.mp3', '.wav', '.aac', '.ogg', '.m4a', '.flac', '.wma', '.opus']
        }
        
        # Document type keywords for enhanced detection
        self.document_keywords = [
            'download', 'pdf', 'document', 'report', 'whitepaper', 'manual', 
            'specification', 'datasheet', 'brochure', 'guide', 'handbook'
        ]
    
    def search(self, keywords: List[str]) -> List[Dict]:
        """Search using multiple dork queries (implements abstract method)"""
        # Default to general dorks if no specific types provided
        return self._search_with_dork_types(keywords, ["general"])

    def _search_with_dork_types(self, keywords: List[str], dork_types: List[str] = ["general"]) -> List[Dict]:
        """Internal method that handles dork types"""
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
    
    def rotate_session(self):
        """Create new session with fresh fingerprint"""
        self.scraper = cloudscraper.create_scraper()
        self.session_requests = 0
        print("🔄 Rotated session to avoid detection")
    
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
        """Execute Google dork search with enhanced media detection"""
        results = []
        
        # Rotate session if needed
        if self.session_requests >= self.max_requests_per_session:
            self.rotate_session()
        
        # Enhanced headers with rotation
        headers = Config.DEFAULT_HEADERS.copy()
        headers['User-Agent'] = self.ua.random
        
        # Add random referer sometimes
        if random.choice([True, False]):
            headers['Referer'] = random.choice([
                'https://www.google.com/',
                'https://duckduckgo.com/',
                'https://www.bing.com/'
            ])
        
        # Encode the dork query
        encoded_query = quote_plus(dork_query)
        
        # Use different Google domains randomly
        google_domains = [
            'www.google.com',
            'www.google.co.uk',
            'www.google.ca',
            'www.google.com.au'
        ]
        
        domain = random.choice(google_domains)
        search_url = f"https://{domain}/search?q={encoded_query}&num={min(num_results, 20)}"
        
        try:
            # Use dynamic delay from config
            delay = Config.get_random_delay()
            print(f"⏳ Waiting {delay:.1f}s before next request...")
            time.sleep(delay)
            
            response = self.scraper.get(search_url, headers=headers, timeout=15)
            
            # Check for rate limiting
            if 'sorry/index' in response.url or response.status_code == 429:
                print("🚫 Rate limited! Waiting longer...")
                time.sleep(random.uniform(60, 120))  # Wait 1-2 minutes
                return results
            
            response.raise_for_status()
            self.session_requests += 1
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract search results with enhanced selectors
            result_selectors = [
                'div.g',
                'div[data-ved]',
                '.rc',
                '.ZINbbc',
                '.kCrYT'
            ]
            
            search_results = []
            for selector in result_selectors:
                search_results = soup.select(selector)
                if search_results:
                    break
            
            for result in search_results[:15]:  # Increased limit for better coverage
                title_elem = result.select_one('h3, .LC20lb, .DKV0Md')
                link_elem = result.select_one('a[href]')
                snippet_elem = result.select_one('.aCOpRe, .st, .VwiC3b, .s3v9rd')
                
                if title_elem and link_elem:
                    href = link_elem.get('href', '')
                    
                    # Clean Google redirect URLs
                    if href.startswith('/url?q='):
                        actual_url = href.split('/url?q=')[1].split('&')[0]
                    elif href.startswith('http'):
                        actual_url = href
                    else:
                        continue
                    
                    # Enhanced media detection in URLs
                    media_type = self.detect_media_type_from_url(actual_url)
                    
                    # Only include trusted domains or valuable media files
                    if self.is_trusted_domain(actual_url) or media_type:
                        result_data = {
                            'url': actual_url,
                            'title': title_elem.get_text().strip(),
                            'snippet': snippet_elem.get_text().strip() if snippet_elem else '',
                            'source': 'google_dork',
                            'dork_query': dork_query,
                            'detected_media_type': media_type,
                            'is_media_file': bool(media_type)
                        }
                        
                        # Add special handling for document files
                        if media_type in ['pdf', 'doc', 'docx', 'ppt', 'pptx', 'xls', 'xlsx']:
                            result_data['is_document'] = True
                            result_data['priority'] = 'high'  # Documents get high priority
                        
                        results.append(result_data)
        
        except Exception as e:
            print(f"❌ Error executing dork query '{dork_query}': {e}")
            # If we get blocked, wait even longer
            if '429' in str(e) or 'sorry' in str(e):
                print("🛑 Detected as bot. Cooling down...")
                time.sleep(random.uniform(120, 300))  # Wait 2-5 minutes
        
        return results
    
    def detect_media_type_from_url(self, url: str) -> str:
        """Detect media type from URL"""
        url_lower = url.lower()
        
        # Check file extensions
        for media_type, extensions in self.media_patterns.items():
            for ext in extensions:
                if ext in url_lower:
                    return ext.replace('.', '')
        
        # Check for specific patterns
        if any(keyword in url_lower for keyword in self.document_keywords):
            return 'document'
        
        if 'youtube.com/watch' in url_lower or 'youtu.be/' in url_lower:
            return 'youtube_video'
        
        if 'vimeo.com/' in url_lower:
            return 'vimeo_video'
        
        return None
    
    def extract_enhanced_media_content(self, html: str, url: str) -> Dict:
        """Enhanced media extraction with comprehensive detection"""
        soup = BeautifulSoup(html, 'html.parser')
        base_url = url
        
        media_content = {
            'images': [],
            'videos': [],
            'audio': [],
            'documents': [],
            'social_media': [],
            'external_links': []
        }
        
        # Extract images with enhanced metadata
        for img in soup.find_all('img', src=True):
            img_data = self.process_image_element(img, base_url)
            if img_data:
                media_content['images'].append(img_data)
        
        # Extract background images from CSS
        for element in soup.find_all(style=True):
            style = element.get('style', '')
            bg_image_match = re.search(r'background-image:\s*url\(["\']?([^"\')\s]+)["\']?\)', style)
            if bg_image_match:
                img_url = urljoin(base_url, bg_image_match.group(1))
                media_content['images'].append({
                    'url': img_url,
                    'type': 'background_image',
                    'alt_text': '',
                    'title': element.get('title', ''),
                    'source_tag': 'css_background'
                })
        
        # Extract videos
        for video in soup.find_all(['video', 'source']):
            video_data = self.process_video_element(video, base_url)
            if video_data:
                media_content['videos'].append(video_data)
        
        # Extract YouTube embedded videos
        youtube_patterns = [
            r'youtube\.com/embed/([a-zA-Z0-9_-]+)',
            r'youtube\.com/watch\?v=([a-zA-Z0-9_-]+)',
            r'youtu\.be/([a-zA-Z0-9_-]+)'
        ]
        
        for iframe in soup.find_all('iframe', src=True):
            src = iframe.get('src', '')
            for pattern in youtube_patterns:
                match = re.search(pattern, src)
                if match:
                    video_id = match.group(1)
                    media_content['videos'].append({
                        'url': src,
                        'type': 'youtube_embed',
                        'video_id': video_id,
                        'title': iframe.get('title', ''),
                        'platform': 'youtube',
                        'thumbnail': f'https://img.youtube.com/vi/{video_id}/maxresdefault.jpg'
                    })
                    break
        
        # Extract Vimeo videos
        vimeo_pattern = r'vimeo\.com/video/(\d+)'
        for iframe in soup.find_all('iframe', src=True):
            src = iframe.get('src', '')
            match = re.search(vimeo_pattern, src)
            if match:
                video_id = match.group(1)
                media_content['videos'].append({
                    'url': src,
                    'type': 'vimeo_embed',
                    'video_id': video_id,
                    'title': iframe.get('title', ''),
                    'platform': 'vimeo'
                })
        
        # Extract document links with enhanced detection
        for link in soup.find_all('a', href=True):
            href = link['href']
            full_url = urljoin(base_url, href)
            link_text = link.get_text().strip()
            
            # Check if it's a document
            doc_type = None
            for ext in self.media_patterns['documents']:
                if ext in href.lower() or ext in link_text.lower():
                    doc_type = ext.replace('.', '')
                    break
            
            # Also check for document keywords in link text
            if not doc_type:
                for keyword in self.document_keywords:
                    if keyword in link_text.lower():
                        doc_type = 'document'
                        break
            
            if doc_type:
                media_content['documents'].append({
                    'url': full_url,
                    'filename': self.extract_filename_from_url(full_url) or link_text,
                    'type': doc_type,
                    'link_text': link_text,
                    'file_size': self.estimate_file_size(link),
                    'description': self.extract_link_description(link)
                })
        
        # Extract audio files
        for audio in soup.find_all(['audio', 'source']):
            audio_data = self.process_audio_element(audio, base_url)
            if audio_data:
                media_content['audio'].append(audio_data)
        
        # Extract social media links
        social_platforms = {
            'twitter.com': 'twitter',
            'x.com': 'twitter',
            'facebook.com': 'facebook',
            'linkedin.com': 'linkedin',
            'instagram.com': 'instagram',
            'youtube.com': 'youtube',
            'tiktok.com': 'tiktok'
        }
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            for domain, platform in social_platforms.items():
                if domain in href.lower():
                    media_content['social_media'].append({
                        'url': href,
                        'platform': platform,
                        'link_text': link.get_text().strip(),
                        'title': link.get('title', '')
                    })
                    break
        
        return media_content
    
    def process_image_element(self, img_element, base_url: str) -> Dict:
        """Process individual image elements with enhanced metadata"""
        src = img_element.get('src')
        if not src:
            return None
        
        full_url = urljoin(base_url, src)
        
        # Skip very small images (likely icons/decorations)
        width = img_element.get('width')
        height = img_element.get('height')
        if width and height:
            try:
                if int(width) < 50 or int(height) < 50:
                    return None
            except (ValueError, TypeError):
                pass
        
        return {
            'url': full_url,
            'type': 'image',
            'alt_text': img_element.get('alt', ''),
            'title': img_element.get('title', ''),
            'width': width or '',
            'height': height or '',
            'caption': self.extract_image_caption(img_element),
            'filename': self.extract_filename_from_url(full_url),
            'source_tag': img_element.name,
            'class': ' '.join(img_element.get('class', [])),
            'lazy_loading': img_element.get('loading') == 'lazy'
        }
    
    def process_video_element(self, video_element, base_url: str) -> Dict:
        """Process video elements"""
        src = video_element.get('src')
        if not src:
            return None
        
        full_url = urljoin(base_url, src)
        
        return {
            'url': full_url,
            'type': 'video',
            'filename': self.extract_filename_from_url(full_url),
            'source_tag': video_element.name,
            'controls': video_element.get('controls') is not None,
            'autoplay': video_element.get('autoplay') is not None,
            'poster': video_element.get('poster', '')
        }
    
    def process_audio_element(self, audio_element, base_url: str) -> Dict:
        """Process audio elements"""
        src = audio_element.get('src')
        if not src:
            return None
        
        full_url = urljoin(base_url, src)
        
        return {
            'url': full_url,
            'type': 'audio',
            'filename': self.extract_filename_from_url(full_url),
            'source_tag': audio_element.name,
            'controls': audio_element.get('controls') is not None,
            'autoplay': audio_element.get('autoplay') is not None
        }
    
    def extract_image_caption(self, img_element):
        """Extract image captions from surrounding elements"""
        # Look for figcaption
        figure = img_element.find_parent('figure')
        if figure:
            caption = figure.find('figcaption')
            if caption:
                return caption.get_text().strip()
        
        # Look for nearby captions
        next_elem = img_element.find_next_sibling()
        if next_elem and next_elem.name in ['p', 'div', 'span']:
            text = next_elem.get_text().strip()
            if len(text) < 200:  # Likely a caption
                return text
        
        # Look for parent div with caption class
        parent = img_element.find_parent(['div', 'span'], class_=re.compile(r'caption|description'))
        if parent:
            return parent.get_text().strip()
        
        return ''
    
    def extract_filename_from_url(self, url: str) -> str:
        """Extract filename from URL"""
        try:
            parsed = urlparse(url)
            filename = parsed.path.split('/')[-1]
            return filename if filename else 'unknown'
        except:
            return 'unknown'
    
    def estimate_file_size(self, link_element):
        """Estimate file size from link text or surrounding content"""
        text = link_element.get_text().lower()
        parent_text = ''
        
        # Check parent element for size info
        parent = link_element.find_parent()
        if parent:
            parent_text = parent.get_text().lower()
        
        combined_text = f"{text} {parent_text}"
        
        size_patterns = [
            r'(\d+\.?\d*)\s*(kb|mb|gb|bytes?)',
            r'\((\d+\.?\d*)\s*(kb|mb|gb|bytes?)\)',
            r'size:\s*(\d+\.?\d*)\s*(kb|mb|gb|bytes?)',
            r'(\d+\.?\d*)\s*(k|m|g)b'
        ]
        
        for pattern in size_patterns:
            match = re.search(pattern, combined_text)
            if match:
                return f"{match.group(1)} {match.group(2).upper()}"
        
        return ''
    
    def extract_link_description(self, link_element):
        """Extract description for document links"""
        # Check title attribute
        title = link_element.get('title', '')
        if title:
            return title
        
        # Check next sibling for description
        next_elem = link_element.find_next_sibling()
        if next_elem and next_elem.name in ['p', 'div', 'span']:
            text = next_elem.get_text().strip()
            if len(text) < 300:  # Likely a description
                return text
        
        # Check parent container
        parent = link_element.find_parent(['div', 'td', 'li'])
        if parent:
            # Get all text but exclude the link text itself
            link_text = link_element.get_text()
            parent_text = parent.get_text()
            description = parent_text.replace(link_text, '').strip()
            if description and len(description) < 300:
                return description
        
        return ''
    
    def scrape_url(self, url: str) -> Dict:
        """Enhanced scraping with comprehensive media detection"""
        try:
            headers = Config.DEFAULT_HEADERS.copy()
            headers['User-Agent'] = self.ua.random
            
            # Add specific headers for document downloads
            if any(ext in url.lower() for ext in ['.pdf', '.doc', '.docx', '.ppt', '.xls']):
                headers['Accept'] = 'application/pdf,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document,*/*'
            
            response = self.scraper.get(url, headers=headers, timeout=20)
            response.raise_for_status()
            
            # Handle different content types
            content_type = response.headers.get('content-type', '').lower()
            
            if 'text/html' in content_type:
                # HTML content - extract everything
                basic_content = self.extract_basic_content(response.text, url)
                enhanced_media = self.extract_enhanced_media_content(response.text, url)
                
                return {
                    'url': url,
                    'domain': response.url.split('//')[1].split('/')[0] if '//' in response.url else url.split('//')[1].split('/')[0],
                    'title': basic_content['title'],
                    'meta_description': basic_content['meta_description'],
                    'content': {
                        'text': basic_content['text'][:15000],  # Increased limit
                        'headings': basic_content['headings'][:30],
                        'links': basic_content['links'][:100]
                    },
                    'media': enhanced_media,
                    'metadata': {
                        'content_type': content_type,
                        'content_length': len(response.content),
                        'language': 'en',
                        'trust_score': 8.0 if self.is_trusted_domain(url) else 6.0,
                        'scraped_via': 'google_dork',
                        'media_count': {
                            'images': len(enhanced_media['images']),
                            'videos': len(enhanced_media['videos']),
                            'documents': len(enhanced_media['documents']),
                            'audio': len(enhanced_media['audio']),
                            'social_media': len(enhanced_media['social_media'])
                        },
                        'is_media_rich': sum(len(v) for v in enhanced_media.values()) > 5
                    }
                }
            
            elif any(doc_type in content_type for doc_type in ['pdf', 'msword', 'document', 'spreadsheet', 'presentation']):
                # Document file - return metadata
                return {
                    'url': url,
                    'domain': response.url.split('//')[1].split('/')[0] if '//' in response.url else url.split('//')[1].split('/')[0],
                    'title': self.extract_filename_from_url(url),
                    'meta_description': f'Document file: {content_type}',
                    'content': {
                        'text': f'Binary document file: {self.extract_filename_from_url(url)}',
                        'headings': [],
                        'links': []
                    },
                    'media': {
                        'documents': [{
                            'url': url,
                            'filename': self.extract_filename_from_url(url),
                            'type': content_type.split('/')[-1],
                            'file_size': len(response.content),
                            'is_direct_download': True
                        }],
                        'images': [], 'videos': [], 'audio': [], 'social_media': []
                    },
                    'metadata': {
                        'content_type': content_type,
                        'content_length': len(response.content),
                        'language': 'unknown',
                        'trust_score': 9.0,  # Direct documents get high trust
                        'scraped_via': 'google_dork',
                        'is_document_file': True,
                        'media_count': {'documents': 1, 'images': 0, 'videos': 0, 'audio': 0}
                    }
                }
            
            else:
                # Other content types
                return {
                    'url': url,
                    'domain': response.url.split('//')[1].split('/')[0] if '//' in response.url else url.split('//')[1].split('/')[0],
                    'title': self.extract_filename_from_url(url),
                    'meta_description': f'File: {content_type}',
                    'content': {'text': '', 'headings': [], 'links': []},
                    'media': {'images': [], 'videos': [], 'documents': [], 'audio': []},
                    'metadata': {
                        'content_type': content_type,
                        'content_length': len(response.content),
                        'trust_score': 7.0,
                        'scraped_via': 'google_dork',
                        'media_count': {'images': 0, 'videos': 0, 'documents': 0, 'audio': 0}
                    }
                }
        
        except Exception as e:
            print(f"❌ Error scraping {url}: {e}")
            return {}
