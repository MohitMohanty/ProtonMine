#!/usr/bin/env python3

import argparse
import json
from typing import List, Dict, Optional
from database.json_db import JSONDatabase
from scrapers.google_dorker import GoogleDorker
from scrapers.duckduckgo_scraper import DuckDuckGoScraper  # New import
from scrapers.twitter_dorker import TwitterDorker
from scrapers.youtube_dorker import YouTubeDorker
from scrapers.reverse_engineer import ReverseEngineer
from utils.content_processor import ContentProcessor  # New import
from utils.media_handler import MediaHandler  # New import
from utils.validators import ContentValidator  # New import
from config.settings import Config

class WebScrapingSystem:
    def __init__(self):
        self.db = JSONDatabase()
        self.scrapers = {
            'google_dork': GoogleDorker(),
            'duckduckgo': DuckDuckGoScraper(),  # New scraper
            'twitter_dork': TwitterDorker(),
            'youtube_dork': YouTubeDorker()
        }
        self.reverse_engineer = ReverseEngineer()
        
        # Initialize utility classes
        self.content_processor = ContentProcessor()
        self.media_handler = MediaHandler()
        self.validator = ContentValidator()
    
    def multi_engine_search(self, keywords: List[str], engines: List[str] = ['duckduckgo', 'google_dork']):
        """Search across multiple search engines"""
        print(f"Multi-engine search for: {', '.join(keywords)}")
        print(f"Using engines: {', '.join(engines)}")
        
        all_results = []
        
        for engine in engines:
            if engine in self.scrapers:
                print(f"\n=== Searching with {engine.upper()} ===")
                
                try:
                    if engine == 'duckduckgo':
                        # DuckDuckGo is less restrictive, search multiple categories
                        dork_types = ['general', 'social', 'news', 'technical']
                        search_results = self.scrapers[engine].search(keywords, dork_types)
                    elif engine == 'google_dork':
                        # Google requires more careful handling
                        dork_types = ['general']  # Start with just general to avoid rate limiting
                        search_results = self.scrapers[engine].search(keywords, dork_types)
                    else:
                        search_results = self.scrapers[engine].search(keywords)
                    
                    print(f"Found {len(search_results)} results from {engine}")
                    
                    # Process and scrape results
                    for i, result in enumerate(search_results[:15]):  # Limit results per engine
                        print(f"[{i+1}/{len(search_results[:15])}] Processing: {result['url']}")
                        
                        # Scrape the content
                        scraped_content = self.scrapers[engine].scrape_url(result['url'])
                        
                        if scraped_content:
                            # Process content with utilities
                            processed_content = self.process_scraped_content(
                                scraped_content, keywords, engine, result
                            )
                            
                            if processed_content:
                                # Store in database
                                doc_id = self.db.insert_document(processed_content)
                                print(f"✅ Stored: {doc_id}")
                                all_results.append(processed_content)
                            else:
                                print("❌ Content validation failed")
                        else:
                            print("❌ Scraping failed")
                
                except Exception as e:
                    print(f"❌ Error with {engine}: {e}")
                    continue
        
        return all_results
    
    def process_scraped_content(self, content: Dict, keywords: List[str], engine: str, search_result: Dict) -> Dict:
        """Process scraped content with all utility functions"""
        try:
            # Validate content quality
            quality_assessment = self.validator.validate_content_quality(content)
            
            # Skip low-quality content
            if quality_assessment['overall_score'] < 30:
                print(f"⚠️ Low quality content (score: {quality_assessment['overall_score']:.1f})")
                return None
            
            # Process text content
            text_content = content.get('content', {}).get('text', '')
            if text_content:
                # Extract keywords and entities
                extracted_keywords = self.content_processor.extract_keywords(text_content)
                entities = self.content_processor.extract_entities(text_content)
                summary = self.content_processor.generate_summary(text_content)
                readability_score = self.content_processor.calculate_readability_score(text_content)
                content_hash = self.content_processor.calculate_content_hash(text_content)
                
                # Check for spam
                is_spam = self.content_processor.is_spam_content(text_content)
                if is_spam:
                    print("⚠️ Potential spam content detected")
                    return None
            
            # Process media content
            media_items = self.media_handler.extract_media_from_content(content, download=False)
            media_report = self.media_handler.generate_media_report(media_items)
            
            # Sanitize content
            sanitized_content = self.validator.sanitize_content(content)
            
            # Enhanced content structure
            enhanced_content = {
                **sanitized_content,
                'search_metadata': {
                    'keywords': keywords,
                    'search_engine': engine,
                    'search_query': search_result.get('search_query', ''),
                    'search_result_title': search_result.get('title', ''),
                    'search_result_snippet': search_result.get('snippet', '')
                },
                'content_analysis': {
                    'extracted_keywords': extracted_keywords,
                    'named_entities': entities,
                    'summary': summary,
                    'readability_score': readability_score,
                    'content_hash': content_hash,
                    'quality_assessment': quality_assessment,
                    'is_spam': is_spam
                },
                'media_analysis': {
                    'media_items': media_items,
                    'media_report': media_report
                }
            }
            
            return enhanced_content
        
        except Exception as e:
            print(f"❌ Error processing content: {e}")
            return None

def main():
    parser = argparse.ArgumentParser(description='Advanced Multi-Engine Web Intelligence System')
    parser.add_argument('--keywords', nargs='+', help='Keywords to search for')
    parser.add_argument('--engines', nargs='+', 
                       default=['duckduckgo'], 
                       choices=['google_dork', 'duckduckgo', 'twitter_dork', 'youtube_dork'],
                       help='Search engines to use')
    parser.add_argument('--targets', nargs='+', help='Target domains for reverse engineering')
    parser.add_argument('--comprehensive', action='store_true', 
                       help='Run comprehensive intelligence gathering')
    
    args = parser.parse_args()
    
    system = WebScrapingSystem()
    
    if args.comprehensive and args.keywords:
        # Comprehensive search using all engines
        all_engines = ['duckduckgo', 'google_dork', 'twitter_dork', 'youtube_dork']
        results = system.multi_engine_search(args.keywords, all_engines)
        print(f"\n🎯 COMPREHENSIVE INTELLIGENCE COMPLETE")
        print(f"📊 Total documents gathered: {len(results)}")
    
    elif args.keywords:
        results = system.multi_engine_search(args.keywords, args.engines)
        print(f"\n🎯 SEARCH COMPLETE")
        print(f"📊 Documents gathered: {len(results)}")
    
    elif args.targets:
        results = system.reverse_engineer.reverse_engineer_sites(args.targets)
        print(f"\n🔍 REVERSE ENGINEERING COMPLETE")
        print(f"📊 Targets analyzed: {len(results)}")

if __name__ == "__main__":
    main()
