class RealTimeUpdates {
    constructor() {
        this.socket = io();
        this.currentSearchId = null;
        this.setupSocketHandlers();
        this.updateStats();
    }
    
    setupSocketHandlers() {
        this.socket.on('connect', () => {
            console.log('Connected to real-time updates');
            this.addActivityItem('Connected to intelligence network', 'info');
        });
        
        this.socket.on('search_engine_start', (data) => {
            this.addActivityItem(
                `🔍 Starting ${data.engine} search for: ${data.keywords.join(', ')}`,
                'info'
            );
        });
        
        this.socket.on('scraping_start', (data) => {
            this.addActivityItem(
                `🌐 Analyzing: ${data.title} (${data.url})`,
                'info'
            );
            this.updateProgress(data.search_id, data.progress);
        });
        
        this.socket.on('scraping_success', (data) => {
            const mediaInfo = Object.entries(data.media_count)
                .filter(([key, value]) => value > 0)
                .map(([key, value]) => `${value} ${key}`)
                .join(', ');
            
            this.addActivityItem(
                `✅ Captured: ${data.title} | Trust: ${data.trust_score}/10 | Media: ${mediaInfo || 'none'}`,
                'success'
            );
            
            this.addDiscoveryCard(data);
            this.updateStats();
        });
        
        this.socket.on('search_complete', (data) => {
            this.addActivityItem(
                `🎯 Search completed! Found ${data.final_stats.results_count} documents`,
                'success'
            );
        });
        
        this.socket.on('search_error', (data) => {
            this.addActivityItem(
                `❌ Error in search: ${data.error}`,
                'error'
            );
        });
    }
    
    addActivityItem(message, type) {
        const feed = document.getElementById('activityFeed');
        const timestamp = new Date().toLocaleTimeString();
        
        const item = document.createElement('div');
        item.className = `activity-item ${type}`;
        item.innerHTML = `
            <div class="d-flex justify-content-between align-items-start">
                <div class="flex-grow-1">
                    <div class="fw-bold">${message}</div>
                </div>
                <small class="text-muted">${timestamp}</small>
            </div>
        `;
        
        // Remove placeholder if exists
        const placeholder = feed.querySelector('.text-center');
        if (placeholder) {
            placeholder.remove();
        }
        
        feed.insertBefore(item, feed.firstChild);
        
        // Keep only last 50 items
        while (feed.children.length > 50) {
            feed.removeChild(feed.lastChild);
        }
        
        // Scroll to top
        feed.scrollTop = 0;
    }
    
    updateProgress(searchId, progress) {
        const progressContainer = document.getElementById('searchProgress');
        let progressBar = document.getElementById(`progress-${searchId}`);
        
        if (!progressBar) {
            progressContainer.innerHTML = `
                <div class="progress-container" id="progress-${searchId}">
                    <div class="d-flex justify-content-between mb-2">
                        <span>Search Progress</span>
                        <span class="progress-text">0%</span>
                    </div>
                    <div class="progress">
                        <div class="progress-bar bg-info progress-bar-striped progress-bar-animated" 
                             role="progressbar" style="width: 0%"></div>
                    </div>
                </div>
            `;
            progressBar = document.getElementById(`progress-${searchId}`);
        }
        
        const bar = progressBar.querySelector('.progress-bar');
        const text = progressBar.querySelector('.progress-text');
        
        bar.style.width = `${progress}%`;
        text.textContent = `${Math.round(progress)}%`;
    }
    
    addDiscoveryCard(data) {
        const container = document.getElementById('recentDiscoveries');
        
        const trustClass = data.trust_score >= 7 ? 'high' : 
                          data.trust_score >= 4 ? 'medium' : 'low';
        
        const mediaInfo = Object.entries(data.media_count)
            .filter(([key, value]) => value > 0)
            .map(([key, value]) => `<span class="media-badge bg-secondary">${value} ${key}</span>`)
            .join('');
        
        const card = document.createElement('div');
        card.className = 'col-md-6 col-lg-4';
        card.innerHTML = `
            <div class="discovery-card">
                <h6 class="text-truncate" title="${data.title}">
                    <i class="fas fa-file-alt me-2"></i>${data.title}
                </h6>
                <p class="text-muted small mb-2">${data.domain}</p>
                <p class="small mb-2">${data.content_preview}...</p>
                <div class="d-flex justify-content-between align-items-center">
                    <div class="media-info">
                        ${mediaInfo}
                    </div>
                    <span class="trust-score ${trustClass}">
                        ${data.trust_score}/10
                    </span>
                </div>
                <a href="${data.url}" target="_blank" class="stretched-link"></a>
            </div>
        `;
        
        container.insertBefore(card, container.firstChild);
        
        // Keep only last 12 items
        while (container.children.length > 12) {
            container.removeChild(container.lastChild);
        }
    }
    
    async updateStats() {
        try {
            const response = await fetch('/api/stats');
            const stats = await response.json();
            
            document.getElementById('totalDocuments').textContent = stats.total_documents;
            document.getElementById('totalImages').textContent = stats.total_images;
            document.getElementById('totalVideos').textContent = stats.total_videos;
            document.getElementById('domainsScraped').textContent = stats.domains_scraped.length;
        } catch (error) {
            console.error('Error updating stats:', error);
        }
    }
    
    startSearch(keywords, engines) {
        fetch('/api/start-search', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                keywords: keywords,
                engines: engines
            })
        })
        .then(response => response.json())
        .then(data => {
            this.currentSearchId = data.search_id;
            this.socket.emit('join_search', { search_id: data.search_id });
        })
        .catch(error => {
            console.error('Error starting search:', error);
        });
    }
}

// Initialize real-time updates
document.addEventListener('DOMContentLoaded', function() {
    const rtUpdates = new RealTimeUpdates();
    
    // Handle search form submission
    document.getElementById('searchForm').addEventListener('submit', function(e) {
        e.preventDefault();
        
        const keywordsText = document.getElementById('keywords').value;
        const keywords = keywordsText.split('\n').map(k => k.trim()).filter(k => k);
        
        const engines = Array.from(document.querySelectorAll('input[type="checkbox"]:checked'))
            .map(cb => cb.value);
        
        if (keywords.length === 0) {
            alert('Please enter at least one keyword');
            return;
        }
        
        if (engines.length === 0) {
            alert('Please select at least one search engine');
            return;
        }
        
        rtUpdates.startSearch(keywords, engines);
    });
    
    // Update stats every 10 seconds
    setInterval(() => {
        rtUpdates.updateStats();
    }, 10000);
});
