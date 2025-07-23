#!/usr/bin/env python3

import argparse
import json
from typing import List
from database.json_db import JSONDatabase
from scrapers.google_dorker import GoogleDorker
from scrapers.twitter_dorker import TwitterDorker
from scrapers.youtube_dorker import YouTubeDorker
from scrapers.reverse_engineer import ReverseEngineer
from config.settings import Config

class WebScrapingSystem:
    def __init__(self):
        self.db = JSONDatabase()
        self.scrapers = {
            'google_dork': GoogleDorker(),
            'twitter_dork': TwitterDorker(),
            'youtube_dork': YouTubeDorker()
        }
        self.reverse_engineer = ReverseEngineer()
    
    def dork_and_scrape(self, keywords: List[str], platforms: List[str] = ['google_dork']):
        """Search using Google dorking techniques"""
        print(f"Dorking for keywords: {', '.join(keywords)}")
        print(f"Using platforms: {', '.join(platforms)}")
        
        all_results = []
        
        for platform in platforms:
            if platform in self.scrapers:
                print(f"\nDorking {platform}...")
                
                # Get dork results
                if platform == 'google_dork':
                    dork_types = ['general', 'media']
                    search_results = self.scrapers[platform].search(keywords, dork_types)
                else:
                    search_results = self.scrapers[platform].search(keywords)
                
                # Scrape each result
                for result in search_results[:20]:  # Limit results
                    print(f"Scraping: {result['url']}")
                    
                    if platform in ['twitter_dork']:
                        scraped_content = self.scrapers[platform].extract_tweet_data(result['url'])
                    elif platform in ['youtube_dork']:
                        scraped_content = self.scrapers[platform].extract_video_data(result['url'])
                    else:
                        scraped_content = self.scrapers[platform].scrape_url(result['url'])
                    
                    if scraped_content:
                        # Add dork metadata
                        scraped_content['keywords'] = keywords
                        scraped_content['dork_platform'] = platform
                        scraped_content['dork_query'] = result.get('dork_query', '')
                        
                        # Store in database
                        doc_id = self.db.insert_document(scraped_content)
                        print(f"Stored document: {doc_id}")
                        all_results.append(scraped_content)
        
        return all_results
    
    def reverse_engineer_sites(self, urls: List[str]):
        """Reverse engineer websites for data extraction"""
        results = []
        
        for url in urls:
            print(f"Reverse engineering: {url}")
            
            analysis = self.reverse_engineer.reverse_engineer_site(url)
            
            # Store analysis results
            doc_id = self.db.insert_document({
                'url': url,
                'type': 'reverse_engineering_analysis',
                'analysis': analysis,
                'metadata': {
                    'analysis_type': 'reverse_engineering'
                }
            })
            
            print(f"Stored analysis: {doc_id}")
            results.append(analysis)
        
        return results
    
    def comprehensive_intelligence_gathering(self, keywords: List[str], target_domains: List[str] = None):
        """Comprehensive OSINT-style data gathering"""
        print("=== COMPREHENSIVE INTELLIGENCE GATHERING ===")
        
        # Phase 1: Google Dorking
        print("\n[Phase 1] Google Dorking...")
        dork_results = self.dork_and_scrape(keywords, ['google_dork'])
        
        # Phase 2: Social Media Dorking
        print("\n[Phase 2] Social Media Dorking...")
        social_results = self.dork_and_scrape(keywords, ['twitter_dork', 'youtube_dork'])
        
        # Phase 3: Reverse Engineering (if target domains provided)
        if target_domains:
            print("\n[Phase 3] Reverse Engineering...")
            re_results = self.reverse_engineer_sites(target_domains)
        
        print(f"\n=== GATHERING COMPLETE ===")
        print(f"Dorked results: {len(dork_results)}")
        print(f"Social media results: {len(social_results)}")
        
        return {
            'dork_results': dork_results,
            'social_results': social_results,
            'reverse_engineering': re_results if target_domains else []
        }

def main():
    parser = argparse.ArgumentParser(description='Advanced Web Intelligence Gathering System')
    parser.add_argument('--keywords', nargs='+', help='Keywords to search for')
    parser.add_argument('--platforms', nargs='+', 
                       default=['google_dork'], 
                       choices=['google_dork', 'twitter_dork', 'youtube_dork'],
                       help='Platforms to search')
    parser.add_argument('--targets', nargs='+', help='Target domains for reverse engineering')
    parser.add_argument('--comprehensive', action='store_true', 
                       help='Run comprehensive intelligence gathering')
    
    args = parser.parse_args()
    
    system = WebScrapingSystem()
    
    if args.comprehensive and args.keywords:
        results = system.comprehensive_intelligence_gathering(args.keywords, args.targets)
        print(f"\nTotal intelligence gathered: {sum(len(v) for v in results.values() if isinstance(v, list))}")
    
    elif args.keywords:
        results = system.dork_and_scrape(args.keywords, args.platforms)
        print(f"\nGathered {len(results)} documents")
    
    elif args.targets:
        results = system.reverse_engineer_sites(args.targets)
        print(f"\nAnalyzed {len(results)} targets")

if __name__ == "__main__":
    main()
