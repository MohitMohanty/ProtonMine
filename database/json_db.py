import json
import os
import uuid
from datetime import datetime
from typing import Dict, List, Optional
from pymongo import MongoClient
from config.settings import Config

class JSONDatabase:
    def __init__(self, use_mongodb=True):
        self.use_mongodb = use_mongodb
        if use_mongodb:
            self.client = MongoClient(Config.MONGODB_URL)
            self.db = self.client[Config.DATABASE_NAME]
            self.collection = self.db.web_content
        else:
            self.file_path = os.path.join(Config.DATA_DIR, 'scraped_content.json')
            self._ensure_file_exists()
    
    def _ensure_file_exists(self):
        """Create JSON file if it doesn't exist"""
        if not os.path.exists(self.file_path):
            with open(self.file_path, 'w') as f:
                json.dump([], f)
    
    def insert_document(self, document: Dict) -> str:
        """Insert a new document"""
        document['id'] = str(uuid.uuid4())
        document['metadata']['crawl_date'] = datetime.now().isoformat()
        
        if self.use_mongodb:
            result = self.collection.insert_one(document)
            return str(result.inserted_id)
        else:
            # File-based storage
            with open(self.file_path, 'r') as f:
                data = json.load(f)
            
            data.append(document)
            
            with open(self.file_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            return document['id']
    
    def find_documents(self, query: Dict) -> List[Dict]:
        """Find documents matching query"""
        if self.use_mongodb:
            return list(self.collection.find(query))
        else:
            # Simple file-based search
            with open(self.file_path, 'r') as f:
                data = json.load(f)
            
            results = []
            for doc in data:
                if all(doc.get(k) == v for k, v in query.items()):
                    results.append(doc)
            return results
    
    def update_document(self, doc_id: str, updates: Dict) -> bool:
        """Update an existing document"""
        if self.use_mongodb:
            result = self.collection.update_one(
                {'_id': doc_id}, 
                {'$set': updates}
            )
            return result.modified_count > 0
        else:
            with open(self.file_path, 'r') as f:
                data = json.load(f)
            
            for doc in data:
                if doc.get('id') == doc_id:
                    doc.update(updates)
                    break
            
            with open(self.file_path, 'w') as f:
                json.dump(data, f, indent=2)
            return True
