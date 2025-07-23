from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit, join_room, leave_room
import json
import threading
import time
from datetime import datetime
from database.json_db import JSONDatabase
from scrapers.google_dorker import GoogleDorker
from scrapers.duckduckgo_scraper import DuckDuckGoScraper
import uuid

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
socketio = SocketIO(app, cors_allowed_origins="*")

# Global variables for real-time tracking
active_searches = {}
scraping_stats = {
    'total_documents': 0,
    'total_images': 0,
    'total_videos': 0,
    'active_scrapers': 0,
    'domains_scraped': set(),
    'keywords_searched': []
}

class RealTimeScrapingSystem:
    def __init__(self):
        self.db = JSONDatabase()
        self.scrapers = {
            'google_dork': GoogleDorker(),
            'duckduckgo': DuckDuckGoScraper()
        }
        self.active_searches = {}
    
    def start_real_time_search(self, search_id: str, keywords: list, engines: list):
        """Start a real-time search with WebSocket updates"""
        self.active_searches[search_id] = {
            'status': 'active',
            'keywords': keywords,
            'engines': engines,
            'start_time': datetime.now(),
            'results_count': 0,
            'media_found': {'images': 0, 'videos': 0, 'documents': 0}
        }
        
        # Start search in background thread
        search_thread = threading.Thread(
            target=self._execute_search_with_updates,
            args=(search_id, keywords, engines)
        )
        search_thread.daemon = True
        search_thread.start()
    
    def _execute_search_with_updates(self, search_id: str, keywords: list, engines: list):
        """Execute search with real-time WebSocket updates"""
        global scraping_stats
        
        try:
            for engine in engines:
                if engine in self.scrapers:
                    # Emit search start
                    socketio.emit('search_engine_start', {
                        'search_id': search_id,
                        'engine': engine,
                        'keywords': keywords
                    })
                    
                    # Get search results
                    if engine == 'duckduckgo':
                        search_results = self.scrapers[engine].search(keywords)  # Keep as is for DuckDuckGo
                    elif engine == 'google_dork':
                    # Use the internal method for Google dorking with dork types
                        search_results = self.scrapers[engine]._search_with_dork_types(keywords, ['general', 'media'])
                    else:
                        search_results = self.scrapers[engine].search(keywords)
                    
                    # Process each result with real-time updates
                    for i, result in enumerate(search_results[:10]):
                        # Emit scraping start
                        socketio.emit('scraping_start', {
                            'search_id': search_id,
                            'url': result['url'],
                            'title': result.get('title', 'Unknown'),
                            'progress': (i + 1) / len(search_results[:10]) * 100
                        })
                        
                        # Scrape the content
                        scraped_content = self.scrapers[engine].scrape_url(result['url'])
                        
                        if scraped_content:
                            # Update statistics
                            media_count = scraped_content.get('metadata', {}).get('media_count', {})
                            scraping_stats['total_images'] += media_count.get('images', 0)
                            scraping_stats['total_videos'] += media_count.get('videos', 0)
                            scraping_stats['total_documents'] += media_count.get('documents', 0)
                            scraping_stats['domains_scraped'].add(scraped_content.get('domain', ''))
                            
                            # Store in database
                            doc_id = self.db.insert_document(scraped_content)
                            
                            # Emit successful scrape
                            socketio.emit('scraping_success', {
                                'search_id': search_id,
                                'doc_id': doc_id,
                                'url': result['url'],
                                'title': scraped_content.get('title', 'Unknown'),
                                'media_count': media_count,
                                'domain': scraped_content.get('domain', ''),
                                'content_preview': scraped_content.get('content', {}).get('text', '')[:200],
                                'trust_score': scraped_content.get('metadata', {}).get('trust_score', 0)
                            })
                            
                            # Update search stats
                            self.active_searches[search_id]['results_count'] += 1
                            for media_type in ['images', 'videos', 'documents']:
                                self.active_searches[search_id]['media_found'][media_type] += media_count.get(media_type, 0)
                        
                        time.sleep(2)  # Delay between requests
            
            # Emit search completion
            socketio.emit('search_complete', {
                'search_id': search_id,
                'final_stats': self.active_searches[search_id]
            })
            
        except Exception as e:
            socketio.emit('search_error', {
                'search_id': search_id,
                'error': str(e)
            })

# Initialize the real-time system
rt_system = RealTimeScrapingSystem()

@app.route('/')
def dashboard():
    """Main dashboard page"""
    return render_template('dashboard.html')

@app.route('/neural-graph')
def neural_graph():
    """Neural network visualization page"""
    return render_template('neural-graph.html')

@app.route('/media-gallery')
def media_gallery():
    """Media gallery page"""
    return render_template('media-gallery.html')

@app.route('/api/start-search', methods=['POST'])
def start_search():
    """API endpoint to start a new search"""
    data = request.json
    search_id = str(uuid.uuid4())
    keywords = data.get('keywords', [])
    engines = data.get('engines', ['duckduckgo'])
    
    rt_system.start_real_time_search(search_id, keywords, engines)
    
    return jsonify({
        'search_id': search_id,
        'status': 'started',
        'keywords': keywords,
        'engines': engines
    })

@app.route('/api/stats')
def get_stats():
    """Get current scraping statistics"""
    stats = scraping_stats.copy()
    stats['domains_scraped'] = list(stats['domains_scraped'])
    stats['active_searches'] = len(active_searches)
    return jsonify(stats)

@app.route('/api/graph-data')
def get_graph_data():
    """Get data for neural network graph"""
    # Query database for recent documents
    recent_docs = rt_system.db.find_documents({})
    
    nodes = []
    links = []
    
    # Create nodes for domains, keywords, and documents
    domain_nodes = {}
    keyword_nodes = {}
    
    for doc in recent_docs[-50:]:  # Last 50 documents
        doc_id = doc.get('id', str(uuid.uuid4()))
        domain = doc.get('domain', 'unknown')
        keywords = doc.get('search_metadata', {}).get('keywords', [])
        
        # Document node
        nodes.append({
            'id': doc_id,
            'type': 'document',
            'label': doc.get('title', 'Unknown')[:30],
            'url': doc.get('url', ''),
            'trust_score': doc.get('metadata', {}).get('trust_score', 0),
            'media_count': sum(doc.get('metadata', {}).get('media_count', {}).values())
        })
        
        # Domain node
        if domain not in domain_nodes:
            domain_nodes[domain] = {
                'id': f'domain_{domain}',
                'type': 'domain',
                'label': domain,
                'count': 0
            }
        domain_nodes[domain]['count'] += 1
        
        # Link document to domain
        links.append({
            'source': doc_id,
            'target': f'domain_{domain}',
            'type': 'belongs_to'
        })
        
        # Keyword nodes and links
        for keyword in keywords:
            keyword_id = f'keyword_{keyword}'
            if keyword not in keyword_nodes:
                keyword_nodes[keyword] = {
                    'id': keyword_id,
                    'type': 'keyword',
                    'label': keyword,
                    'count': 0
                }
            keyword_nodes[keyword]['count'] += 1
            
            # Link document to keyword
            links.append({
                'source': doc_id,
                'target': keyword_id,
                'type': 'tagged_with'
            })
    
    # Add domain and keyword nodes
    nodes.extend(domain_nodes.values())
    nodes.extend(keyword_nodes.values())
    
    return jsonify({'nodes': nodes, 'links': links})

@socketio.on('connect')
def handle_connect():
    """Handle WebSocket connection"""
    emit('connected', {'status': 'Connected to real-time updates'})

@socketio.on('join_search')
def handle_join_search(data):
    """Join a specific search room for updates"""
    search_id = data['search_id']
    join_room(search_id)
    emit('joined_search', {'search_id': search_id})

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
