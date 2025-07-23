import re
import urllib.parse
from typing import Dict, List, Optional, Tuple
import requests
from urllib.robotparser import RobotFileParser
import json

class ContentValidator:
    def __init__(self):
        self.robots_cache = {}
        
        # Common patterns for validation
        self.url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        
        self.email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    
    def is_valid_url(self, url: str) -> bool:
        """Validate URL format"""
        if not url or not isinstance(url, str):
            return False
        
        return bool(self.url_pattern.match(url))
    
    def is_accessible_url(self, url: str, timeout: int = 10) -> Tuple[bool, Optional[str]]:
        """Check if URL is accessible"""
        try:
            response = requests.head(url, timeout=timeout, allow_redirects=True)
            if response.status_code < 400:
                return True, None
            else:
                return False, f"HTTP {response.status_code}"
        except requests.exceptions.RequestException as e:
            return False, str(e)
    
    def check_robots_txt(self, url: str, user_agent: str = '*') -> bool:
        """Check if URL is allowed by robots.txt"""
        try:
            parsed_url = urllib.parse.urlparse(url)
            base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
            robots_url = f"{base_url}/robots.txt"
            
            # Check cache first
            if robots_url in self.robots_cache:
                rp = self.robots_cache[robots_url]
            else:
                rp = RobotFileParser()
                rp.set_url(robots_url)
                try:
                    rp.read()
                    self.robots_cache[robots_url] = rp
                except:
                    # If robots.txt doesn't exist or can't be read, assume allowed
                    return True
            
            return rp.can_fetch(user_agent, url)
        
        except Exception:
            # If there's any error, assume allowed
            return True
    
    def validate_content_quality(self, content: Dict) -> Dict[str, any]:
        """Validate content quality and return score"""
        quality_score = {
            'overall_score': 0,
            'text_quality': 0,
            'media_quality': 0,
            'structure_quality': 0,
            'issues': []
        }
        
        # Text quality checks
        text_content = content.get('content', {}).get('text', '')
        if text_content:
            text_quality = self._assess_text_quality(text_content)
            quality_score['text_quality'] = text_quality['score']
            quality_score['issues'].extend(text_quality['issues'])
        
        # Media quality checks
        media_content = content.get('media', {})
        media_quality = self._assess_media_quality(media_content)
        quality_score['media_quality'] = media_quality['score']
        quality_score['issues'].extend(media_quality['issues'])
        
        # Structure quality checks
        structure_quality = self._assess_structure_quality(content)
        quality_score['structure_quality'] = structure_quality['score']
        quality_score['issues'].extend(structure_quality['issues'])
        
        # Calculate overall score
        quality_score['overall_score'] = (
            quality_score['text_quality'] * 0.5 +
            quality_score['media_quality'] * 0.2 +
            quality_score['structure_quality'] * 0.3
        )
        
        return quality_score
    
    def _assess_text_quality(self, text: str) -> Dict:
        """Assess text content quality"""
        issues = []
        score = 100
        
        if not text:
            return {'score': 0, 'issues': ['No text content']}
        
        # Length checks
        if len(text) < 50:
            issues.append('Text too short')
            score -= 30
        elif len(text) > 50000:
            issues.append('Text extremely long')
            score -= 10
        
        # Language and readability
        words = text.split()
        if len(words) < 10:
            issues.append('Too few words')
            score -= 20
        
        # Check for spam indicators
        spam_keywords = ['click here', 'buy now', 'limited time', 'act fast']
        spam_count = sum(1 for keyword in spam_keywords if keyword.lower() in text.lower())
        if spam_count > 2:
            issues.append('Possible spam content')
            score -= 40
        
        # Check for repeated content
        sentences = text.split('.')
        if len(set(sentences)) < len(sentences) * 0.8:
            issues.append('High content repetition')
            score -= 20
        
        return {'score': max(0, score), 'issues': issues}
    
    def _assess_media_quality(self, media: Dict) -> Dict:
        """Assess media content quality"""
        issues = []
        score = 100
        
        images = media.get('images', [])
        videos = media.get('videos', [])
        audio = media.get('audio', [])
        
        total_media = len(images) + len(videos) + len(audio)
        
        if total_media == 0:
            return {'score': 50, 'issues': ['No media content']}
        
        # Check image quality
        valid_images = 0
        for img in images:
            if img.get('url') and self.is_valid_url(img['url']):
                valid_images += 1
            else:
                issues.append('Invalid image URL found')
                score -= 5
        
        if valid_images < len(images) * 0.8:
            issues.append('Many invalid image URLs')
            score -= 20
        
        # Check for alt text (accessibility)
        images_with_alt = sum(1 for img in images if img.get('alt_text'))
        if images and images_with_alt < len(images) * 0.5:
            issues.append('Poor image accessibility (missing alt text)')
            score -= 15
        
        return {'score': max(0, score), 'issues': issues}
    
    def _assess_structure_quality(self, content: Dict) -> Dict:
        """Assess content structure quality"""
        issues = []
        score = 100
        
        # Check for title
        if not content.get('title'):
            issues.append('Missing title')
            score -= 20
        
        # Check for meta description
        if not content.get('meta_description'):
            issues.append('Missing meta description')
            score -= 10
        
        # Check for headings
        headings = content.get('content', {}).get('headings', [])
        if not headings:
            issues.append('No headings structure')
            score -= 15
        
        # Check for links
        links = content.get('content', {}).get('links', [])
        if not links:
            issues.append('No outbound links')
            score -= 5
        
        # Check URL structure
        url = content.get('url', '')
        if url:
            parsed = urllib.parse.urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                issues.append('Malformed URL')
                score -= 10
        
        return {'score': max(0, score), 'issues': issues}
    
    def is_duplicate_content(self, content1: Dict, content2: Dict, threshold: float = 0.8) -> bool:
        """Check if two content items are duplicates"""
        # Simple duplicate detection based on text similarity
        text1 = content1.get('content', {}).get('text', '')
        text2 = content2.get('content', {}).get('text', '')
        
        if not text1 or not text2:
            return False
        
        # Simple Jaccard similarity
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return False
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        similarity = intersection / union if union > 0 else 0
        return similarity > threshold
    
    def validate_trusted_domain(self, url: str, trusted_domains: List[str]) -> bool:
        """Validate if URL belongs to trusted domain"""
        if not self.is_valid_url(url):
            return False
        
        parsed_url = urllib.parse.urlparse(url)
        domain = parsed_url.netloc.lower()
        
        for trusted_domain in trusted_domains:
            if trusted_domain.startswith('.'):
                # Handle TLD patterns like .gov, .edu
                if domain.endswith(trusted_domain):
                    return True
            elif trusted_domain in domain:
                return True
        
        return False
    
    def sanitize_content(self, content: Dict) -> Dict:
        """Sanitize content by removing potentially harmful elements"""
        sanitized = content.copy()
        
        # Sanitize text content
        if 'content' in sanitized and 'text' in sanitized['content']:
            text = sanitized['content']['text']
            # Remove script tags and content
            text = re.sub(r'<script.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)
            # Remove style tags and content
            text = re.sub(r'<style.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
            # Remove potentially dangerous HTML tags
            dangerous_tags = ['iframe', 'embed', 'object', 'applet']
            for tag in dangerous_tags:
                text = re.sub(f'<{tag}.*?</{tag}>', '', text, flags=re.DOTALL | re.IGNORECASE)
            
            sanitized['content']['text'] = text
        
        # Validate and sanitize URLs
        if 'media' in sanitized:
            if 'images' in sanitized['media']:
                valid_images = []
                for img in sanitized['media']['images']:
                    if img.get('url') and self.is_valid_url(img['url']):
                        valid_images.append(img)
                sanitized['media']['images'] = valid_images
        
        return sanitized
