#!/usr/bin/env python3

import json
import argparse
from datetime import datetime
from osint_engine.reconnaissance import OSINTReconEngine

def save_results(results: dict, filename: str = None):
    """Save OSINT results to JSON file"""
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"indian_navy_osint_{timestamp}.json"
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"💾 Results saved to: {filename}")

def print_summary(results: dict):
    """Print comprehensive summary of OSINT results"""
    print("\n" + "="*60)
    print("🇮🇳 INDIAN NAVY OSINT RECONNAISSANCE SUMMARY")
    print("="*60)
    
    print(f"📡 Domains Discovered: {len(results['domains_discovered'])}")
    print(f"🔍 Subdomains Found: {len(results['subdomains_discovered'])}")
    print(f"🌐 URLs Successfully Scraped: {len(results['urls_scraped'])}")
    print(f"📊 Intelligence Items: {len(results['intelligence_gathered'])}")
    print(f"🖼️ Media Files Found: {len(results['media_found'])}")
    print(f"📄 Documents Discovered: {len(results['documents_found'])}")
    
    print(f"\n🎯 TOP DISCOVERED SUBDOMAINS:")
    for subdomain in list(results['subdomains_discovered'])[:10]:
        print(f"  • {subdomain}")
    
    print(f"\n📄 DOCUMENTS FOUND:")
    for doc in results['documents_found'][:5]:
        print(f"  • {doc.get('text', 'Unknown')} - {doc.get('url', '')}")
    
    print(f"\n🖼️ MEDIA DISCOVERED:")
    for media in results['media_found'][:5]:
        print(f"  • {media.get('alt', 'Unknown')} - {media.get('url', '')}")

def main():
    parser = argparse.ArgumentParser(description='Advanced Indian Navy OSINT Reconnaissance')
    parser.add_argument('--target', help='Specific target domain (optional)')
    parser.add_argument('--output', help='Output filename for results')
    parser.add_argument('--deep', action='store_true', help='Enable deep reconnaissance mode')
    
    args = parser.parse_args()
    
    print("🔍 Initializing Advanced OSINT Reconnaissance Engine...")
    osint_engine = OSINTReconEngine()
    
    if args.target:
        print(f"🎯 Targeting specific domain: {args.target}")
        # Add custom target to seed domains
        osint_engine.seed_domains.append(args.target)
    
    # Execute comprehensive reconnaissance
    results = osint_engine.indian_navy_focused_reconnaissance()
    
    # Print summary
    print_summary(results)
    
    # Save results
    save_results(results, args.output)
    
    print(f"\n🎉 OSINT Reconnaissance Complete!")
    print(f"✅ Successfully gathered intelligence from {len(results['urls_scraped'])} sources")
    print(f"📊 Total data points collected: {len(results['intelligence_gathered'])}")

if __name__ == "__main__":
    main()
