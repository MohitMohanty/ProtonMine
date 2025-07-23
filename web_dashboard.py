from flask import Flask, render_template, jsonify, request, send_file
from flask_socketio import SocketIO, emit, join_room, leave_room
import json
import threading
import time
from datetime import datetime
from database.json_db import JSONDatabase
from scrapers.google_dorker import GoogleDorker
from scrapers.duckduckgo_scraper import DuckDuckGoScraper
from scrapers.twitter_dorker import TwitterDorker
from scrapers.youtube_dorker import YouTubeDorker
from osint_engine.reconnaissance import OSINTReconEngine  # New import
import uuid
import io
import base64
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import networkx as nx
from wordcloud import WordCloud

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
    'keywords_searched': [],
    'osint_intelligence': 0,
    'subdomains_discovered': 0
}

class AdvancedScrapingSystem:
    def __init__(self):
        self.db = JSONDatabase(use_mongodb=True)  # Force MongoDB usage
        self.scrapers = {
            'google_dork': GoogleDorker(),
            'duckduckgo': DuckDuckGoScraper(),
            'twitter_dork': TwitterDorker(),
            'youtube_dork': YouTubeDorker()
        }
        self.osint_engine = OSINTReconEngine()  # New OSINT engine
        self.active_searches = {}
    
    def start_comprehensive_intelligence_gathering(self, search_id: str, keywords: list, engines: list, include_osint: bool = False):
        """Start comprehensive intelligence gathering with OSINT"""
        self.active_searches[search_id] = {
            'status': 'active',
            'keywords': keywords,
            'engines': engines,
            'include_osint': include_osint,
            'start_time': datetime.now(),
            'results_count': 0,
            'media_found': {'images': 0, 'videos': 0, 'documents': 0},
            'osint_data': {'subdomains': 0, 'intelligence_items': 0}
        }
        
        # Start search in background thread
        search_thread = threading.Thread(
            target=self._execute_comprehensive_search,
            args=(search_id, keywords, engines, include_osint)
        )
        search_thread.daemon = True
        search_thread.start()
    
    def _execute_comprehensive_search(self, search_id: str, keywords: list, engines: list, include_osint: bool):
        """Execute comprehensive search with OSINT integration"""
        global scraping_stats
        
        try:
            # Phase 1: Traditional Web Scraping
            socketio.emit('search_phase_start', {
                'search_id': search_id,
                'phase': 'traditional_scraping',
                'message': 'Starting traditional web scraping...'
            })
            
            traditional_results = self._execute_traditional_scraping(search_id, keywords, engines)
            
            # Phase 2: OSINT Reconnaissance (if enabled)
            osint_results = []
            if include_osint:
                socketio.emit('search_phase_start', {
                    'search_id': search_id,
                    'phase': 'osint_reconnaissance',
                    'message': 'Starting OSINT reconnaissance...'
                })
                
                osint_results = self._execute_osint_reconnaissance(search_id, keywords)
            
            # Phase 3: Data Analysis and Visualization
            socketio.emit('search_phase_start', {
                'search_id': search_id,
                'phase': 'analysis',
                'message': 'Analyzing gathered intelligence...'
            })
            
            analysis_results = self._analyze_intelligence_data(search_id, traditional_results + osint_results)
            
            # Emit completion
            socketio.emit('search_complete', {
                'search_id': search_id,
                'final_stats': self.active_searches[search_id],
                'analysis': analysis_results
            })
            
        except Exception as e:
            socketio.emit('search_error', {
                'search_id': search_id,
                'error': str(e)
            })
    
    def _execute_traditional_scraping(self, search_id: str, keywords: list, engines: list):
        """Execute traditional web scraping"""
        all_results = []
        
        for engine in engines:
            if engine in self.scrapers:
                socketio.emit('search_engine_start', {
                    'search_id': search_id,
                    'engine': engine,
                    'keywords': keywords
                })
                
                try:
                    # Get search results based on engine type
                    if engine == 'duckduckgo':
                        search_results = self.scrapers[engine].search(keywords, ['general', 'social', 'news', 'technical'])
                    elif engine == 'google_dork':
                        search_results = self.scrapers[engine]._search_with_dork_types(keywords, ['general', 'media'])
                    elif engine == 'twitter_dork':
                        search_results = self.scrapers[engine].search_twitter_content(keywords)
                    elif engine == 'youtube_dork':
                        search_results = self.scrapers[engine].search_youtube_content(keywords)
                    else:
                        search_results = self.scrapers[engine].search(keywords)
                    
                    # Process each result
                    for i, result in enumerate(search_results[:15]):
                        socketio.emit('scraping_start', {
                            'search_id': search_id,
                            'url': result['url'],
                            'title': result.get('title', 'Unknown'),
                            'engine': engine,
                            'progress': (i + 1) / len(search_results[:15]) * 100
                        })
                        
                        # Scrape the content
                        if engine in ['twitter_dork']:
                            scraped_content = self.scrapers[engine].extract_tweet_data(result['url'])
                        elif engine in ['youtube_dork']:
                            scraped_content = self.scrapers[engine].extract_video_data(result['url'])
                        else:
                            scraped_content = self.scrapers[engine].scrape_url(result['url'])
                        
                        if scraped_content:
                            # Add search metadata
                            scraped_content['search_metadata'] = {
                                'keywords': keywords,
                                'search_engine': engine,
                                'search_id': search_id,
                                'data_type': 'traditional_scraping'
                            }
                            
                            # Store in MongoDB
                            doc_id = self.db.insert_document(scraped_content)
                            all_results.append(scraped_content)
                            
                            # Update statistics
                            media_count = scraped_content.get('metadata', {}).get('media_count', {})
                            scraping_stats['total_images'] += media_count.get('images', 0)
                            scraping_stats['total_videos'] += media_count.get('videos', 0)
                            scraping_stats['total_documents'] += media_count.get('documents', 0)
                            
                            # Emit success
                            socketio.emit('scraping_success', {
                                'search_id': search_id,
                                'doc_id': doc_id,
                                'url': result['url'],
                                'title': scraped_content.get('title', 'Unknown'),
                                'engine': engine,
                                'media_count': media_count,
                                'data_type': 'traditional'
                            })
                        
                        time.sleep(2)
                
                except Exception as e:
                    socketio.emit('search_engine_error', {
                        'search_id': search_id,
                        'engine': engine,
                        'error': str(e)
                    })
        
        return all_results
    
    def _execute_osint_reconnaissance(self, search_id: str, keywords: list):
        """Execute OSINT reconnaissance"""
        osint_results = []
        
        try:
            socketio.emit('osint_start', {
                'search_id': search_id,
                'message': 'Starting comprehensive OSINT reconnaissance...'
            })
            
            # Execute OSINT reconnaissance
            osint_data = self.osint_engine.indian_navy_focused_reconnaissance()
            
            # Process OSINT results
            for intelligence_item in osint_data['intelligence_gathered']:
                # Add search metadata
                intelligence_item['search_metadata'] = {
                    'keywords': keywords,
                    'search_engine': 'osint_reconnaissance',
                    'search_id': search_id,
                    'data_type': 'osint_intelligence'
                }
                
                # Store in MongoDB
                doc_id = self.db.insert_document(intelligence_item)
                osint_results.append(intelligence_item)
                
                # Update statistics
                scraping_stats['osint_intelligence'] += 1
                scraping_stats['subdomains_discovered'] += len(osint_data['subdomains_discovered'])
                
                # Emit OSINT discovery
                socketio.emit('osint_discovery', {
                    'search_id': search_id,
                    'doc_id': doc_id,
                    'source': intelligence_item['source'],
                    'title': intelligence_item.get('title', 'OSINT Intelligence'),
                    'intelligence_type': 'reconnaissance',
                    'media_count': intelligence_item.get('media_count', 0),
                    'documents_count': intelligence_item.get('documents_count', 0)
                })
            
            # Store subdomain data
            subdomain_doc = {
                'data_type': 'subdomain_enumeration',
                'search_metadata': {
                    'keywords': keywords,
                    'search_id': search_id,
                    'data_type': 'osint_subdomains'
                },
                'subdomains_discovered': osint_data['subdomains_discovered'],
                'domains_discovered': osint_data['domains_discovered'],
                'discovery_timestamp': time.time()
            }
            
            self.db.insert_document(subdomain_doc)
            
            socketio.emit('osint_complete', {
                'search_id': search_id,
                'subdomains_found': len(osint_data['subdomains_discovered']),
                'intelligence_items': len(osint_data['intelligence_gathered']),
                'documents_found': len(osint_data['documents_found']),
                'media_found': len(osint_data['media_found'])
            })
            
        except Exception as e:
            socketio.emit('osint_error', {
                'search_id': search_id,
                'error': str(e)
            })
        
        return osint_results
    
    def _analyze_intelligence_data(self, search_id: str, all_data: list):
        """Analyze gathered intelligence data"""
        analysis = {
            'total_sources': len(all_data),
            'domain_distribution': {},
            'content_analysis': {},
            'media_analysis': {},
            'technology_stack': {},
            'visualizations': {}
        }
        
        try:
            # Domain distribution analysis
            domain_counts = {}
            for item in all_data:
                domain = item.get('domain', 'unknown')
                domain_counts[domain] = domain_counts.get(domain, 0) + 1
            
            analysis['domain_distribution'] = domain_counts
            
            # Generate visualizations
            analysis['visualizations'] = self._generate_visualizations(search_id, all_data)
            
        except Exception as e:
            print(f"Analysis error: {e}")
        
        return analysis
    
    def _generate_visualizations(self, search_id: str, data: list):
        """Generate visualization charts"""
        visualizations = {}
        
        try:
            # Domain distribution pie chart
            domains = {}
            for item in data:
                domain = item.get('domain', 'unknown')
                domains[domain] = domains.get(domain, 0) + 1
            
            if domains:
                plt.figure(figsize=(10, 8))
                plt.pie(domains.values(), labels=domains.keys(), autopct='%1.1f%%')
                plt.title('Domain Distribution')
                
                img = io.BytesIO()
                plt.savefig(img, format='png')
                img.seek(0)
                plot_url = base64.b64encode(img.getvalue()).decode()
                plt.close()
                
                visualizations['domain_pie_chart'] = plot_url
            
            # Media type distribution
            media_types = {'images': 0, 'videos': 0, 'documents': 0}
            for item in data:
                media_count = item.get('metadata', {}).get('media_count', {})
                for media_type in media_types:
                    media_types[media_type] += media_count.get(media_type, 0)
            
            if any(media_types.values()):
                plt.figure(figsize=(10, 6))
                plt.bar(media_types.keys(), media_types.values())
                plt.title('Media Type Distribution')
                plt.ylabel('Count')
                
                img = io.BytesIO()
                plt.savefig(img, format='png')
                img.seek(0)
                plot_url = base64.b64encode(img.getvalue()).decode()
                plt.close()
                
                visualizations['media_bar_chart'] = plot_url
        
        except Exception as e:
            print(f"Visualization error: {e}")
        
        return visualizations

# Initialize the enhanced system
enhanced_system = AdvancedScrapingSystem()

@app.route('/')
def dashboard():
    """Enhanced dashboard with OSINT capabilities"""
    return render_template('enhanced_dashboard.html')

@app.route('/osint-intelligence')
def osint_intelligence():
    """OSINT Intelligence page"""
    return render_template('osint_intelligence.html')

@app.route('/neural-graph')
def neural_graph():
    """Neural network visualization page (restored)"""
    return render_template('neural-graph.html')  # Keep original template name

@app.route('/api/graph-data')
def get_graph_data():
    """Get data for neural network graph (original functionality)"""
    # Query database for recent documents (keep original logic)
    recent_docs = enhanced_system.db.find_documents({})
    
    nodes = []
    links = []
    
    # Create nodes for domains, keywords, and documents (original logic)
    domain_nodes = {}
    keyword_nodes = {}
    
    for doc in recent_docs[-50:]:  # Last 50 documents
        doc_id = doc.get('id', str(uuid.uuid4()))
        domain = doc.get('domain', 'unknown')
        keywords = doc.get('keywords', []) or doc.get('search_metadata', {}).get('keywords', [])
        
        # Document node (original structure)
        nodes.append({
            'id': doc_id,
            'type': 'document',
            'label': doc.get('title', 'Unknown')[:30],
            'url': doc.get('url', ''),
            'trust_score': doc.get('metadata', {}).get('trust_score', 0),
            'media_count': sum(doc.get('metadata', {}).get('media_count', {}).values()) if doc.get('metadata', {}).get('media_count') else 0
        })
        
        # Domain node (original logic)
        if domain not in domain_nodes:
            domain_nodes[domain] = {
                'id': f'domain_{domain}',
                'type': 'domain',
                'label': domain,
                'count': 0
            }
        domain_nodes[domain]['count'] += 1
        
        # Link document to domain (original structure)
        links.append({
            'source': doc_id,
            'target': f'domain_{domain}',
            'type': 'belongs_to'
        })
        
        # Keyword nodes and links (original logic)
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

@app.route('/media-gallery')
def media_gallery():
    """Media gallery page showing all discovered media"""
    return render_template('media_gallery.html')

@app.route('/api/media-data')
def get_media_data():
    """Get media data for gallery"""
    try:
        # Query database for documents with media
        recent_docs = enhanced_system.db.find_documents({})
        
        media_items = {
            'images': [],
            'videos': [],
            'documents': [],
            'audio': []
        }
        
        for doc in recent_docs:
            # Extract media from traditional scraping results
            media = doc.get('media', {})
            
            # Process images
            for img in media.get('images', []):
                media_items['images'].append({
                    'url': img.get('url', ''),
                    'alt': img.get('alt_text', img.get('alt', '')),
                    'title': img.get('title', ''),
                    'source_url': doc.get('url', ''),
                    'source_title': doc.get('title', 'Unknown'),
                    'domain': doc.get('domain', 'unknown'),
                    'discovery_date': doc.get('inserted_at', ''),
                    'search_engine': doc.get('search_metadata', {}).get('search_engine', 'unknown')
                })
            
            # Process videos
            for video in media.get('videos', []):
                if isinstance(video, dict):
                    media_items['videos'].append({
                        'url': video.get('url', ''),
                        'title': video.get('title', ''),
                        'type': video.get('type', 'video'),
                        'platform': video.get('platform', 'unknown'),
                        'thumbnail': video.get('thumbnail', ''),
                        'source_url': doc.get('url', ''),
                        'source_title': doc.get('title', 'Unknown'),
                        'domain': doc.get('domain', 'unknown'),
                        'discovery_date': doc.get('inserted_at', ''),
                        'search_engine': doc.get('search_metadata', {}).get('search_engine', 'unknown')
                    })
                else:
                    # Handle string URLs
                    media_items['videos'].append({
                        'url': video,
                        'title': 'Video',
                        'type': 'video',
                        'platform': 'unknown',
                        'source_url': doc.get('url', ''),
                        'source_title': doc.get('title', 'Unknown'),
                        'domain': doc.get('domain', 'unknown'),
                        'discovery_date': doc.get('inserted_at', ''),
                        'search_engine': doc.get('search_metadata', {}).get('search_engine', 'unknown')
                    })
            
            # Process documents
            for document in media.get('documents', []):
                if isinstance(document, dict):
                    media_items['documents'].append({
                        'url': document.get('url', ''),
                        'filename': document.get('filename', document.get('text', 'Document')),
                        'type': document.get('type', 'pdf'),
                        'file_size': document.get('file_size', ''),
                        'source_url': doc.get('url', ''),
                        'source_title': doc.get('title', 'Unknown'),
                        'domain': doc.get('domain', 'unknown'),
                        'discovery_date': doc.get('inserted_at', ''),
                        'search_engine': doc.get('search_metadata', {}).get('search_engine', 'unknown')
                    })
                else:
                    # Handle string URLs
                    media_items['documents'].append({
                        'url': document,
                        'filename': 'Document',
                        'type': 'pdf',
                        'source_url': doc.get('url', ''),
                        'source_title': doc.get('title', 'Unknown'),
                        'domain': doc.get('domain', 'unknown'),
                        'discovery_date': doc.get('inserted_at', ''),
                        'search_engine': doc.get('search_metadata', {}).get('search_engine', 'unknown')
                    })
            
            # Process audio
            for audio in media.get('audio', []):
                if isinstance(audio, dict):
                    media_items['audio'].append({
                        'url': audio.get('url', ''),
                        'title': audio.get('title', 'Audio'),
                        'type': audio.get('type', 'audio'),
                        'source_url': doc.get('url', ''),
                        'source_title': doc.get('title', 'Unknown'),
                        'domain': doc.get('domain', 'unknown'),
                        'discovery_date': doc.get('inserted_at', ''),
                        'search_engine': doc.get('search_metadata', {}).get('search_engine', 'unknown')
                    })
                else:
                    # Handle string URLs
                    media_items['audio'].append({
                        'url': audio,
                        'title': 'Audio',
                        'type': 'audio',
                        'source_url': doc.get('url', ''),
                        'source_title': doc.get('title', 'Unknown'),
                        'domain': doc.get('domain', 'unknown'),
                        'discovery_date': doc.get('inserted_at', ''),
                        'search_engine': doc.get('search_metadata', {}).get('search_engine', 'unknown')
                    })
        
        # Limit results and sort by discovery date
        for media_type in media_items:
            media_items[media_type] = sorted(
                media_items[media_type], 
                key=lambda x: x.get('discovery_date', ''), 
                reverse=True
            )[:100]  # Limit to 100 items per type
        
        return jsonify(media_items)
        
    except Exception as e:
        return jsonify({'error': str(e), 'images': [], 'videos': [], 'documents': [], 'audio': []})

@app.route('/api/media-stats')
def get_media_stats():
    """Get media statistics"""
    try:
        response = get_media_data()
        media_data = response.get_json()
        
        stats = {
            'total_images': len(media_data.get('images', [])),
            'total_videos': len(media_data.get('videos', [])),
            'total_documents': len(media_data.get('documents', [])),
            'total_audio': len(media_data.get('audio', [])),
            'total_media': (
                len(media_data.get('images', [])) +
                len(media_data.get('videos', [])) +
                len(media_data.get('documents', [])) +
                len(media_data.get('audio', []))
            ),
            'domains': len(set([
                item.get('domain', 'unknown') 
                for media_list in media_data.values() 
                if isinstance(media_list, list)
                for item in media_list
            ])),
            'search_engines': len(set([
                item.get('search_engine', 'unknown') 
                for media_list in media_data.values() 
                if isinstance(media_list, list)
                for item in media_list
            ]))
        }
        
        return jsonify(stats)
        
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/start-comprehensive-search', methods=['POST'])
def start_comprehensive_search():
    """Start comprehensive intelligence gathering"""
    data = request.json
    search_id = str(uuid.uuid4())
    keywords = data.get('keywords', [])
    engines = data.get('engines', ['duckduckgo'])
    include_osint = data.get('include_osint', False)
    
    enhanced_system.start_comprehensive_intelligence_gathering(
        search_id, keywords, engines, include_osint
    )
    
    return jsonify({
        'search_id': search_id,
        'status': 'started',
        'keywords': keywords,
        'engines': engines,
        'include_osint': include_osint
    })

@app.route('/api/enhanced-stats')
def get_enhanced_stats():
    """Get enhanced statistics including OSINT data"""
    # Query MongoDB for recent statistics
    recent_docs = enhanced_system.db.find_documents({})
    
    stats = {
        'total_documents': len([d for d in recent_docs if d.get('search_metadata', {}).get('data_type') == 'traditional_scraping']),
        'osint_intelligence': len([d for d in recent_docs if d.get('search_metadata', {}).get('data_type') == 'osint_intelligence']),
        'subdomains_discovered': len([d for d in recent_docs if d.get('search_metadata', {}).get('data_type') == 'osint_subdomains']),
        'total_images': sum([d.get('metadata', {}).get('media_count', {}).get('images', 0) for d in recent_docs]),
        'total_videos': sum([d.get('metadata', {}).get('media_count', {}).get('videos', 0) for d in recent_docs]),
        'total_documents_media': sum([d.get('metadata', {}).get('media_count', {}).get('documents', 0) for d in recent_docs]),
        'domains_scraped': len(set([d.get('domain', '') for d in recent_docs if d.get('domain')])),
        'active_searches': len(active_searches)
    }
    
    return jsonify(stats)

@app.route('/api/enhanced-graph-data')
def get_enhanced_graph_data():
    """Get enhanced graph data including OSINT relationships"""
    recent_docs = enhanced_system.db.find_documents({})
    
    nodes = []
    links = []
    
    # Create different node types
    domain_nodes = {}
    keyword_nodes = {}
    osint_nodes = {}
    
    for doc in recent_docs[-100:]:  # Last 100 documents
        doc_id = doc.get('id', str(uuid.uuid4()))
        domain = doc.get('domain', 'unknown')
        keywords = doc.get('search_metadata', {}).get('keywords', [])
        data_type = doc.get('search_metadata', {}).get('data_type', 'unknown')
        
        # Different node types based on data source
        if data_type == 'osint_intelligence':
            node_type = 'osint'
            node_color = '#ff6b6b'
        elif data_type == 'traditional_scraping':
            node_type = 'traditional'
            node_color = '#4ecdc4'
        else:
            node_type = 'other'
            node_color = '#95e1d3'
        
        # Document node
        nodes.append({
            'id': doc_id,
            'type': node_type,
            'label': doc.get('title', 'Unknown')[:30],
            'url': doc.get('url', ''),
            'trust_score': doc.get('metadata', {}).get('trust_score', 0),
            'media_count': sum(doc.get('metadata', {}).get('media_count', {}).values()) if doc.get('metadata', {}).get('media_count') else 0,
            'color': node_color,
            'size': 10 + (doc.get('metadata', {}).get('trust_score', 0) * 2)
        })
        
        # Domain relationships
        if domain not in domain_nodes:
            domain_nodes[domain] = {
                'id': f'domain_{domain}',
                'type': 'domain',
                'label': domain,
                'count': 0,
                'color': '#ffd93d',
                'size': 15
            }
        domain_nodes[domain]['count'] += 1
        
        links.append({
            'source': doc_id,
            'target': f'domain_{domain}',
            'type': 'belongs_to',
            'strength': 1
        })
    
    # Add domain nodes
    nodes.extend(domain_nodes.values())
    
    return jsonify({'nodes': nodes, 'links': links})

@app.route('/api/osint-intelligence-data')
def get_osint_intelligence_data():
    """Get OSINT intelligence data for visualization"""
    osint_docs = enhanced_system.db.find_documents({
        'search_metadata.data_type': 'osint_intelligence'
    })
    
    intelligence_data = []
    for doc in osint_docs[-50:]:  # Last 50 OSINT items
        intelligence_data.append({
            'source': doc.get('source', ''),
            'title': doc.get('title', ''),
            'content_preview': doc.get('content_preview', '')[:200],
            'links_count': doc.get('links_count', 0),
            'media_count': doc.get('media_count', 0),
            'documents_count': doc.get('documents_count', 0),
            'timestamp': doc.get('timestamp', 0)
        })
    
    return jsonify(intelligence_data)

@socketio.on('connect')
def handle_connect():
    """Handle WebSocket connection"""
    emit('connected', {'status': 'Connected to enhanced intelligence network'})

@socketio.on('join_search')
def handle_join_search(data):
    """Join a specific search room for updates"""
    search_id = data['search_id']
    join_room(search_id)
    emit('joined_search', {'search_id': search_id})

if __name__ == '__main__':
    # Ensure MongoDB connection
    print("🔧 Initializing Enhanced Intelligence Dashboard...")
    print("📊 MongoDB connection established")
    print("🕵️ OSINT engine loaded")
    print("🌍 Multi-platform scrapers ready")
    
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
