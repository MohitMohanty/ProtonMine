from typing import List, Dict
from .google_dorker import GoogleDorker

class TwitterDorker(GoogleDorker):
    def __init__(self):
        super().__init__()
    
    def search_twitter_content(self, keywords: List[str]) -> List[Dict]:
        """Search Twitter content using Google dorks"""
        twitter_dorks = [
            f'site:twitter.com "{" ".join(keywords)}"',
            f'site:x.com "{" ".join(keywords)}"',
            f'site:twitter.com inurl:status "{" ".join(keywords)}"',
            f'"twitter.com" "{" ".join(keywords)}" -inurl:login -inurl:signup',
            f'site:twitter.com "{keywords[0]}" OR site:x.com "{keywords[0]}"' if keywords else '',
        ]
        
        all_results = []
        
        for dork in twitter_dorks:
            if dork:  # Skip empty dorks
                print(f"Twitter dorking: {dork}")
                results = self.search_google_dork(dork, 30)
                all_results.extend(results)
        
        return all_results
    
    def extract_tweet_data(self, url: str) -> Dict:
        """Extract tweet-specific data"""
        base_data = self.scrape_url(url)
        
        if base_data:
            # Add Twitter-specific metadata
            base_data['social_platform'] = 'twitter'
            base_data['tweet_id'] = self.extract_tweet_id(url)
            
        return base_data
    
    def extract_tweet_id(self, url: str) -> str:
        """Extract tweet ID from URL"""
        if '/status/' in url:
            return url.split('/status/')[-1].split('?')[0]
        return ''
    
    def search(self, keywords: List[str]) -> List[Dict]:
        """Main search method for Twitter content"""
        return self.search_twitter_content(keywords)
