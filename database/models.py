from datetime import datetime
from typing import List, Dict, Optional

class WebContentModel:
    def __init__(self):
        self.schema = {
            "id": str,
            "url": str,
            "domain": str,
            "title": str,
            "meta_description": str,
            "keywords": List[str],
            "content": {
                "text": str,
                "headings": List[str],
                "links": List[str]
            },
            "media": {
                "images": List[Dict],
                "videos": List[str],
                "audio": List[str]
            },
            "metadata": {
                "crawl_date": datetime,
                "last_modified": datetime,
                "content_type": str,
                "language": str,
                "trust_score": float
            },
            "social_signals": {
                "twitter_mentions": int,
                "shares": int,
                "likes": int
            }
        }
    
    def validate_document(self, document: Dict) -> bool:
        """Validate document structure"""
        required_fields = ["url", "domain", "content"]
        return all(field in document for field in required_fields)
