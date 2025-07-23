class EnhancedIntelligenceSystem {
    constructor() {
        this.socket = io();
        this.currentSearchId = null;
        this.setupSocketHandlers();
        this.updateStats();
        this.activeFilters = ['all'];
    }
    
    setupSocketHandlers() {
        this.socket.on('connect', () => {
            console.log('Connected to enhanced intelligence network');
            this.addActivityItem('🔗 Connected to enhanced intelligence network', 'info');
        });
        
        // Phase-based progress tracking
        this.socket.on('search_phase_start', (data) => {
            this.updateOperationPhase(data.phase, data.message);
        });
        
        // Traditional scraping updates
        this.socket.on('search_engine_start', (data) => {
            this.addActivityItem(
                `🔍 Starting ${data.engine.toUpperCase()} intelligence gathering for: ${data.keywords.join(', ')}`,
                'info'
            );
        });
        
        this.socket.on('scraping_success', (data) => {
            const mediaInfo = Object.entries(data.media_count || {})
                .filter(([key, value]) => value > 0)
                .map(([key, value]) => `${value} ${key}`)
                .join(', ');
            
            this.addActivityItem(
                `✅ [${data.engine.toUpperCase()}] ${data.title} | Media: ${mediaInfo || 'none'}`,
                'success',
                data.data_type || 'traditional'
            );
            
            this.addIntelligenceCard(data);
            this.updateStats();
        });
        
        // OSINT-specific updates
        this.socket.on('osint_start', (data) => {
            this.addActivityItem(
                `🕵️ ${data.message}`,
                'osint'
            );
        });
        
        this.socket.on('osint_discovery', (data) => {
            this.addActivityItem(
                `🎯 OSINT Discovery: ${data.title} | Intelligence: ${data.intelligence_type} | Docs: ${data.documents_count}`,
                'osint',
                'osint'
            );
            
            this.addIntelligenceCard(data, 'osint');
            this.updateStats();
        });
        
        this.socket.on('osint_complete', (data) => {
            this.addActivityItem(
                `🏆 OSINT Complete: ${data.subdomains_found} subdomains, ${data.intelligence_items} intel items, ${data.documents_found} documents`,
                'osint'
            );
        });
        
        // Social media updates
        this.socket.on('scraping_success', (data) => {
            if (data.engine === 'twitter_dork' || data.engine === 'youtube_dork') {
                this.addActivityItem(
                    `📱 [${data.engine.toUpperCase()}] ${data.title}`,
                    'social',
                    'social'
                );
            }
        });
        
        // Operation completion
        this.socket.on('search_complete', (data) => {
            this.addActivityItem(
                `🎉 Intelligence operation completed! Check analysis results.`,
                'success'
            );
            this.displayAnalysisResults(data.analysis);
        });
        
        // Error handling
        this.socket.on('search_error', (data) => {
            this.addActivityItem(
                `❌ Operation error: ${data.error}`,
                'error'
            );
        });
    }
    
    addActivityItem(message, type, category = 'all') {
        const feed = document.getElementById('enhancedActivityFeed');
        const timestamp = new Date().toLocaleTimeString();
        
        // Remove placeholder if exists
        const placeholder = feed.querySelector('.text-center');
        if (placeholder) {
            placeholder.remove();
        }
        
        const item = document.createElement('div');
        item.className = `activity-item ${type}`;
        item.setAttribute('data-category', category);
        
        // Different styling based on type
        let iconClass, bgColor;
        switch(type) {
            case 'osint':
                iconClass = 'fas fa-user-secret';
                bgColor = 'rgba(220, 53, 69, 0.1)';
                break;
            case 'social':
                iconClass = 'fas fa-share-alt';
                bgColor = 'rgba(255, 193, 7, 0.1)';
                break;
            case 'success':
                iconClass = 'fas fa-check-circle';
                bgColor = 'rgba(40, 167, 69, 0.1)';
                break;
            case 'info':
                iconClass = 'fas fa-info-circle';
                bgColor = 'rgba(23, 162, 184, 0.1)';
                break;
            default:
                iconClass = 'fas fa-circle';
                bgColor = 'rgba(255, 255, 255, 0.05)';
        }
        
        item.innerHTML = `
            <div class="d-flex align-items-start" style="background: ${bgColor}; padding: 10px; border-radius: 8px;">
                <i class="${iconClass} me-3 mt-1" style="min-width: 20px;"></i>
                <div class="flex-grow-1">
                    <div class="fw-bold">${message}</div>
                    <small class="text-muted">${timestamp}</small>
                </div>
            </div>
        `;
        
        feed.insertBefore(item, feed.firstChild);
        
        // Apply current filter
        this.applyActivityFilter();
        
        // Keep only last 100 items
        while (feed.children.length > 100) {
            feed.removeChild(feed.lastChild);
        }
        
        feed.scrollTop = 0;
    }
    
    updateOperationPhase(phase, message) {
        const progressContainer = document.getElementById('operationProgress');
        
        const phaseMap = {
            'traditional_scraping': { icon: 'fas fa-search', color: 'primary', label: 'Traditional Scraping' },
            'osint_reconnaissance': { icon: 'fas fa-user-secret', color: 'danger', label: 'OSINT Reconnaissance' },
            'analysis': { icon: 'fas fa-chart-line', color: 'success', label: 'Intelligence Analysis' }
        };
        
        const phaseInfo = phaseMap[phase] || { icon: 'fas fa-cog', color: 'info', label: 'Processing' };
        
        progressContainer.innerHTML = `
            <div class="text-center">
                <div class="mb-3">
                    <i class="${phaseInfo.icon} fa-3x text-${phaseInfo.color}"></i>
                </div>
                <h6 class="text-${phaseInfo.color}">${phaseInfo.label}</h6>
                <p class="text-muted">${message}</p>
                <div class="progress">
                    <div class="progress-bar bg-${phaseInfo.color} progress-bar-striped progress-bar-animated" 
                         role="progressbar" style="width: 100%"></div>
                </div>
            </div>
        `;
    }
    
    addIntelligenceCard(data, type = 'traditional') {
        const container = document.getElementById('intelligenceDiscoveries');
        
        const typeConfig = {
            'osint': {
                icon: 'fas fa-user-secret',
                color: 'danger',
                badge: 'OSINT'
            },
            'social': {
                icon: 'fas fa-share-alt',
                color: 'warning',
                badge: 'SOCIAL'
            },
            'traditional': {
                icon: 'fas fa-file-alt',
                color: 'primary',
                badge: 'WEB'
            }
        };
        
        const config = typeConfig[type] || typeConfig.traditional;
        
        const card = document.createElement('div');
        card.className = 'col-md-6 col-lg-4 mb-3';
        card.innerHTML = `
            <div class="intelligence-card" data-type="${type}">
                <div class="card bg-dark border-${config.color}">
                    <div class="card-header bg-${config.color} d-flex justify-content-between align-items-center">
                        <small class="fw-bold">${config.badge}</small>
                        <i class="${config.icon}"></i>
                    </div>
                    <div class="card-body">
                        <h6 class="card-title text-truncate" title="${data.title}">
                            ${data.title || 'Intelligence Item'}
                        </h6>
                        <p class="card-text small text-muted">
                            ${data.source || data.url || 'Unknown Source'}
                        </p>
                        ${data.media_count ? `
                            <div class="d-flex justify-content-between align-items-center">
                                <small class="text-info">
                                    📊 ${Object.values(data.media_count).reduce((a, b) => a + b, 0)} media items
                                </small>
                                <small class="text-success">
                                    Trust: ${data.trust_score || 'N/A'}
                                </small>
                            </div>
                        ` : ''}
                    </div>
                </div>
            </div>
        `;
        
        container.insertBefore(card, container.firstChild);
        
        // Keep only last 24 items
        while (container.children.length > 24) {
            container.removeChild(container.lastChild);
        }
    }
    
    async updateStats() {
        try {
            const response = await fetch('/api/enhanced-stats');
            const stats = await response.json();
            
            document.getElementById('totalDocuments').textContent = stats.total_documents;
            document.getElementById('osintIntelligence').textContent = stats.osint_intelligence;
            document.getElementById('subdomainsFound').textContent = stats.subdomains_discovered;
            document.getElementById('totalImages').textContent = stats.total_images + stats.total_videos + stats.total_documents_media;
            
            // Update progress bars
            const total = stats.total_documents + stats.osint_intelligence;
            if (total > 0) {
                document.getElementById('traditionalProgress').style.width = 
                    `${(stats.total_documents / total) * 100}%`;
                document.getElementById('osintProgress').style.width = 
                    `${(stats.osint_intelligence / total) * 100}%`;
            }
            
        } catch (error) {
            console.error('Error updating stats:', error);
        }
    }
    
    applyActivityFilter() {
        const selectedFilter = document.querySelector('input[name="feedFilter"]:checked').id;
        const items = document.querySelectorAll('.activity-item');
        
        items.forEach(item => {
            const category = item.getAttribute('data-category') || 'all';
            
            if (selectedFilter === 'allFeed' || 
                (selectedFilter === 'osintFeed' && category === 'osint') ||
                (selectedFilter === 'socialFeed' && category === 'social')) {
                item.style.display = 'block';
            } else {
                item.style.display = 'none';
            }
        });
    }
    
    startEnhancedSearch(keywords, engines, includeOSINT) {
        fetch('/api/start-comprehensive-search', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                keywords: keywords,
                engines: engines,
                include_osint: includeOSINT
            })
        })
        .then(response => response.json())
        .then(data => {
            this.currentSearchId = data.search_id;
            this.socket.emit('join_search', { search_id: data.search_id });
            
            this.addActivityItem(
                `🚀 Launched comprehensive intelligence operation [${data.search_id.substring(0, 8)}]`,
                'info'
            );
        })
        .catch(error => {
            console.error('Error starting search:', error);
            this.addActivityItem('❌ Failed to start intelligence operation', 'error');
        });
    }
}

// Initialize enhanced system
document.addEventListener('DOMContentLoaded', function() {
    const enhancedSystem = new EnhancedIntelligenceSystem();
    
    // Handle enhanced search form
    document.getElementById('enhancedSearchForm').addEventListener('submit', function(e) {
        e.preventDefault();
        
        const keywordsText = document.getElementById('keywords').value;
        const keywords = keywordsText.split('\n').map(k => k.trim()).filter(k => k);
        
        const engines = Array.from(document.querySelectorAll('input[type="checkbox"]:checked'))
            .map(cb => cb.value);
        
        const includeOSINT = document.getElementById('includeOSINT').checked;
        
        if (keywords.length === 0) {
            alert('Please enter at least one keyword');
            return;
        }
        
        if (engines.length === 0) {
            alert('Please select at least one search engine');
            return;
        }
        
        enhancedSystem.startEnhancedSearch(keywords, engines, includeOSINT);
    });
    
    // Handle feed filters
    document.querySelectorAll('input[name="feedFilter"]').forEach(radio => {
        radio.addEventListener('change', () => {
            enhancedSystem.applyActivityFilter();
        });
    });
    
    // Update stats every 15 seconds
    setInterval(() => {
        enhancedSystem.updateStats();
    }, 15000);
});

// Export functionality
function exportIntelligence() {
    // Implementation for exporting intelligence data
    alert('Intelligence export feature - implementation needed');
}
