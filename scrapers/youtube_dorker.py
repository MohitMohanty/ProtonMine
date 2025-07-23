from typing import List, Dict
from .google_dorker import GoogleDorker

class YouTubeDorker(GoogleDorker):
    def __init__(self):
        super().__init__()
    
    def search_youtube_content(self, keywords: List[str]) -> List[Dict]:
        """Search YouTube content using Google dorks"""
        youtube_dorks = [
            f'site:youtube.com "{" ".join(keywords)}"',
            f'site:youtube.com inurl:watch "{" ".join(keywords)}"',
            f'site:youtube.com intitle:"{" ".join(keywords)}"',
            f'"youtube.com/watch" "{" ".join(keywords)}"',
            f'site:youtube.com "{keywords[0]}" filetype:json' if keywords else '',
        ]
        
        all_results = []
        
        for dork in youtube_dorks:
            if dork:
                print(f"YouTube dorking: {dork}")
                results = self.search_google_dork(dork, 30)
                all_results.extend(results)
        
        return all_results
    
    def extract_video_data(self, url: str) -> Dict:
        """Extract YouTube video-specific data"""
        base_data = self.scrape_url(url)
        
        if base_data:
            # Add YouTube-specific metadata
            base_data['social_platform'] = 'youtube'
            base_data['video_id'] = self.extract_video_id(url)
            
        return base_data
    
    def extract_video_id(self, url: str) -> str:
        """Extract video ID from YouTube URL"""
        if 'watch?v=' in url:
            return url.split('watch?v=')[-1].split('&')[0]
        elif 'youtu.be/' in url:
            return url.split('youtu.be/')[-1].split('?')[0]
        return ''
    
    def search(self, keywords: List[str]) -> List[Dict]:
        """Main search method for YouTube content"""
        return self.search_youtube_content(keywords)
