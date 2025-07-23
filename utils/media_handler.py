import os
import requests
from urllib.parse import urlparse, urljoin
from PIL import Image
import hashlib
from typing import Dict, List, Optional, Tuple
import mimetypes
from config.settings import Config

class MediaHandler:
    def __init__(self):
        self.supported_image_formats = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp']
        self.supported_video_formats = ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv']
        self.supported_audio_formats = ['.mp3', '.wav', '.aac', '.ogg', '.m4a']
        
        # Create media directory if it doesn't exist
        os.makedirs(Config.MEDIA_DIR, exist_ok=True)
    
    def download_media(self, url: str, base_dir: str = None) -> Optional[Dict]:
        """Download media file from URL"""
        if not base_dir:
            base_dir = Config.MEDIA_DIR
        
        try:
            # Parse URL to get filename
            parsed_url = urlparse(url)
            filename = os.path.basename(parsed_url.path)
            
            if not filename or '.' not in filename:
                # Generate filename from URL hash
                url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
                extension = self.guess_extension_from_url(url)
                filename = f"media_{url_hash}{extension}"
            
            # Create safe filename
            safe_filename = self.sanitize_filename(filename)
            file_path = os.path.join(base_dir, safe_filename)
            
            # Download file
            response = requests.get(url, timeout=30, stream=True)
            response.raise_for_status()
            
            # Check content type
            content_type = response.headers.get('content-type', '')
            
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # Get file info
            file_info = self.analyze_media_file(file_path, url)
            
            return {
                'original_url': url,
                'local_path': file_path,
                'filename': safe_filename,
                'content_type': content_type,
                'file_size': os.path.getsize(file_path),
                'analysis': file_info
            }
        
        except Exception as e:
            print(f"Error downloading media from {url}: {e}")
            return None
    
    def analyze_media_file(self, file_path: str, original_url: str = "") -> Dict:
        """Analyze downloaded media file"""
        analysis = {
            'type': 'unknown',
            'format': '',
            'size_bytes': 0,
            'dimensions': None,
            'duration': None,
            'metadata': {}
        }
        
        try:
            file_size = os.path.getsize(file_path)
            analysis['size_bytes'] = file_size
            
            # Get file extension
            _, ext = os.path.splitext(file_path)
            ext = ext.lower()
            
            # Analyze based on file type
            if ext in self.supported_image_formats:
                analysis.update(self.analyze_image(file_path))
            elif ext in self.supported_video_formats:
                analysis.update(self.analyze_video(file_path))
            elif ext in self.supported_audio_formats:
                analysis.update(self.analyze_audio(file_path))
            
            analysis['format'] = ext
            
        except Exception as e:
            print(f"Error analyzing media file {file_path}: {e}")
        
        return analysis
    
    def analyze_image(self, file_path: str) -> Dict:
        """Analyze image file"""
        try:
            with Image.open(file_path) as img:
                return {
                    'type': 'image',
                    'dimensions': img.size,
                    'mode': img.mode,
                    'format': img.format,
                    'metadata': {
                        'width': img.size[0],
                        'height': img.size[1],
                        'aspect_ratio': img.size[0] / img.size[1] if img.size[1] > 0 else 0
                    }
                }
        except Exception as e:
            return {'type': 'image', 'error': str(e)}
    
    def analyze_video(self, file_path: str) -> Dict:
        """Analyze video file (basic implementation)"""
        # For full video analysis, you'd need ffmpeg-python
        # This is a basic implementation
        return {
            'type': 'video',
            'metadata': {
                'analyzed': False,
                'note': 'Video analysis requires ffmpeg integration'
            }
        }
    
    def analyze_audio(self, file_path: str) -> Dict:
        """Analyze audio file (basic implementation)"""
        # For full audio analysis, you'd need audio processing libraries
        return {
            'type': 'audio',
            'metadata': {
                'analyzed': False,
                'note': 'Audio analysis requires additional libraries'
            }
        }
    
    def extract_media_from_content(self, content: Dict, download: bool = False) -> List[Dict]:
        """Extract and optionally download media from scraped content"""
        media_items = []
        
        # Process images
        for img in content.get('media', {}).get('images', []):
            media_item = {
                'type': 'image',
                'url': img.get('url', ''),
                'alt_text': img.get('alt_text', ''),
                'caption': img.get('caption', ''),
                'local_path': None
            }
            
            if download and media_item['url']:
                download_result = self.download_media(media_item['url'])
                if download_result:
                    media_item['local_path'] = download_result['local_path']
                    media_item['analysis'] = download_result['analysis']
            
            media_items.append(media_item)
        
        # Process videos
        for video_url in content.get('media', {}).get('videos', []):
            media_item = {
                'type': 'video',
                'url': video_url,
                'local_path': None
            }
            
            if download:
                download_result = self.download_media(video_url)
                if download_result:
                    media_item['local_path'] = download_result['local_path']
                    media_item['analysis'] = download_result['analysis']
            
            media_items.append(media_item)
        
        # Process audio
        for audio_url in content.get('media', {}).get('audio', []):
            media_item = {
                'type': 'audio',
                'url': audio_url,
                'local_path': None
            }
            
            if download:
                download_result = self.download_media(audio_url)
                if download_result:
                    media_item['local_path'] = download_result['local_path']
                    media_item['analysis'] = download_result['analysis']
            
            media_items.append(media_item)
        
        return media_items
    
    def sanitize_filename(self, filename: str) -> str:
        """Create safe filename for filesystem"""
        # Remove or replace problematic characters
        safe_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-_"
        safe_filename = ''.join(c if c in safe_chars else '_' for c in filename)
        
        # Limit length
        if len(safe_filename) > 100:
            name, ext = os.path.splitext(safe_filename)
            safe_filename = name[:95] + ext
        
        return safe_filename
    
    def guess_extension_from_url(self, url: str) -> str:
        """Guess file extension from URL or content type"""
        parsed = urlparse(url)
        
        # Try to get extension from path
        _, ext = os.path.splitext(parsed.path)
        if ext:
            return ext
        
        # Default extensions for common cases
        if 'image' in url.lower():
            return '.jpg'
        elif 'video' in url.lower():
            return '.mp4'
        elif 'audio' in url.lower():
            return '.mp3'
        
        return '.dat'  # Generic data file
    
    def generate_media_report(self, media_items: List[Dict]) -> Dict:
        """Generate summary report of media items"""
        report = {
            'total_items': len(media_items),
            'by_type': {'image': 0, 'video': 0, 'audio': 0, 'other': 0},
            'total_size_bytes': 0,
            'downloaded_items': 0,
            'failed_downloads': 0
        }
        
        for item in media_items:
            item_type = item.get('type', 'other')
            report['by_type'][item_type] = report['by_type'].get(item_type, 0) + 1
            
            if item.get('local_path'):
                report['downloaded_items'] += 1
                if item.get('analysis', {}).get('size_bytes'):
                    report['total_size_bytes'] += item['analysis']['size_bytes']
            else:
                report['failed_downloads'] += 1
        
        return report
