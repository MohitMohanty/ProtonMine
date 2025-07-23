class MediaGallery {
    constructor() {
        this.mediaData = {};
        this.filteredData = {};
        this.currentFilter = {
            search: '',
            domain: '',
            engine: ''
        };
        
        this.loadMediaData();
        this.setupEventListeners();
    }
    
    async loadMediaData() {
        try {
            const [mediaResponse, statsResponse] = await Promise.all([
                fetch('/api/media-data'),
                fetch('/api/media-stats')
            ]);
            
            this.mediaData = await mediaResponse.json();
            const stats = await statsResponse.json();
            
            this.updateStats(stats);
            this.populateFilters();
            this.displayMedia();
            
        } catch (error) {
            console.error('Error loading media data:', error);
            this.showError('Failed to load media data');
        }
    }
    
    updateStats(stats) {
        document.getElementById('totalImages').textContent = stats.total_images || 0;
        document.getElementById('totalVideos').textContent = stats.total_videos || 0;
        document.getElementById('totalDocuments').textContent = stats.total_documents || 0;
        document.getElementById('totalAudio').textContent = stats.total_audio || 0;
    }
    
    populateFilters() {
        const domains = new Set();
        const engines = new Set();
        
        // Collect unique domains and engines
        Object.values(this.mediaData).forEach(mediaList => {
            if (Array.isArray(mediaList)) {
                mediaList.forEach(item => {
                    if (item.domain) domains.add(item.domain);
                    if (item.search_engine) engines.add(item.search_engine);
                });
            }
        });
        
        // Populate domain filter
        const domainFilter = document.getElementById('domainFilter');
        domains.forEach(domain => {
            const option = document.createElement('option');
            option.value = domain;
            option.textContent = domain;
            domainFilter.appendChild(option);
        });
        
        // Populate engine filter
        const engineFilter = document.getElementById('engineFilter');
        engines.forEach(engine => {
            const option = document.createElement('option');
            option.value = engine;
            option.textContent = engine.toUpperCase();
            engineFilter.appendChild(option);
        });
    }
    
    displayMedia() {
        this.displayImages();
        this.displayVideos();
        this.displayDocuments();
        this.displayAudio();
    }
    
    displayImages() {
        const container = document.getElementById('imagesGallery');
        const images = this.filteredData.images || this.mediaData.images || [];
        
        if (images.length === 0) {
            container.innerHTML = '<div class="col-12 text-center text-muted"><p>No images found</p></div>';
            return;
        }
        
        container.innerHTML = images.map(image => `
            <div class="col-md-4 col-lg-3 mb-3">
                <div class="card bg-dark border-info h-100">
                    <img src="${image.url}" class="card-img-top" style="height: 200px; object-fit: cover;" 
                         alt="${image.alt}" onerror="this.src='data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjNTU1Ii8+PHRleHQgeD0iNTAlIiB5PSI1MCUiIGZvbnQtc2l6ZT0iMTgiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGR5PSIuM2VtIiBmaWxsPSIjOTk5Ij5JbWFnZSBOb3QgRm91bmQ8L3RleHQ+PC9zdmc+'">
                    <div class="card-body p-2">
                        <h6 class="card-title text-truncate" title="${image.alt || image.title}">${image.alt || image.title || 'Image'}</h6>
                        <small class="text-muted d-block text-truncate">${image.domain}</small>
                        <small class="text-info">${image.search_engine.toUpperCase()}</small>
                    </div>
                    <div class="card-footer p-2">
                        <button class="btn btn-outline-info btn-sm w-100" onclick="showMediaDetails('image', ${JSON.stringify(image).replace(/"/g, '&quot;')})">
                            <i class="fas fa-eye me-1"></i>View Details
                        </button>
                    </div>
                </div>
            </div>
        `).join('');
    }
    
    displayVideos() {
        const container = document.getElementById('videosGallery');
        const videos = this.filteredData.videos || this.mediaData.videos || [];
        
        if (videos.length === 0) {
            container.innerHTML = '<div class="col-12 text-center text-muted"><p>No videos found</p></div>';
            return;
        }
        
        container.innerHTML = videos.map(video => `
            <div class="col-md-6 col-lg-4 mb-3">
                <div class="card bg-dark border-danger h-100">
                    <div class="card-img-top bg-secondary d-flex align-items-center justify-content-center" style="height: 200px;">
                        ${video.thumbnail ? 
                            `<img src="${video.thumbnail}" style="max-width: 100%; max-height: 100%; object-fit: cover;" alt="${video.title}">` :
                            `<i class="fas fa-video fa-3x text-muted"></i>`
                        }
                    </div>
                    <div class="card-body p-2">
                        <h6 class="card-title text-truncate" title="${video.title}">${video.title || 'Video'}</h6>
                        <small class="text-muted d-block text-truncate">${video.domain}</small>
                        <small class="text-info">${video.search_engine.toUpperCase()}</small>
                        ${video.platform ? `<small class="text-warning d-block">${video.platform.toUpperCase()}</small>` : ''}
                    </div>
                    <div class="card-footer p-2">
                        <button class="btn btn-outline-danger btn-sm w-100" onclick="showMediaDetails('video', ${JSON.stringify(video).replace(/"/g, '&quot;')})">
                            <i class="fas fa-play me-1"></i>View Details
                        </button>
                    </div>
                </div>
            </div>
        `).join('');
    }
    
    displayDocuments() {
        const container = document.getElementById('documentsGallery');
        const documents = this.filteredData.documents || this.mediaData.documents || [];
        
        if (documents.length === 0) {
            container.innerHTML = '<div class="col-12 text-center text-muted"><p>No documents found</p></div>';
            return;
        }
        
        container.innerHTML = documents.map(doc => `
            <div class="col-md-6 col-lg-4 mb-3">
                <div class="card bg-dark border-success h-100">
                    <div class="card-body">
                        <div class="d-flex align-items-center mb-2">
                            <i class="fas fa-file-${this.getDocumentIcon(doc.type)} fa-2x text-success me-3"></i>
                            <div class="flex-grow-1">
                                <h6 class="card-title text-truncate" title="${doc.filename}">${doc.filename || 'Document'}</h6>
                                <small class="text-muted">${doc.type.toUpperCase()}</small>
                                ${doc.file_size ? `<small class="text-info d-block">${doc.file_size}</small>` : ''}
                            </div>
                        </div>
                        <small class="text-muted d-block text-truncate">${doc.domain}</small>
                        <small class="text-info">${doc.search_engine.toUpperCase()}</small>
                    </div>
                    <div class="card-footer p-2">
                        <button class="btn btn-outline-success btn-sm w-100" onclick="showMediaDetails('document', ${JSON.stringify(doc).replace(/"/g, '&quot;')})">
                            <i class="fas fa-download me-1"></i>View Details
                        </button>
                    </div>
                </div>
            </div>
        `).join('');
    }
    
    displayAudio() {
        const container = document.getElementById('audioGallery');
        const audio = this.filteredData.audio || this.mediaData.audio || [];
        
        if (audio.length === 0) {
            container.innerHTML = '<div class="col-12 text-center text-muted"><p>No audio files found</p></div>';
            return;
        }
        
        container.innerHTML = audio.map(audioItem => `
            <div class="col-md-6 col-lg-4 mb-3">
                <div class="card bg-dark border-warning h-100">
                    <div class="card-body">
                        <div class="d-flex align-items-center mb-2">
                            <i class="fas fa-music fa-2x text-warning me-3"></i>
                            <div class="flex-grow-1">
                                <h6 class="card-title text-truncate" title="${audioItem.title}">${audioItem.title || 'Audio'}</h6>
                                <small class="text-muted">${audioItem.type.toUpperCase()}</small>
                            </div>
                        </div>
                        <small class="text-muted d-block text-truncate">${audioItem.domain}</small>
                        <small class="text-info">${audioItem.search_engine.toUpperCase()}</small>
                    </div>
                    <div class="card-footer p-2">
                        <button class="btn btn-outline-warning btn-sm w-100" onclick="showMediaDetails('audio', ${JSON.stringify(audioItem).replace(/"/g, '&quot;')})">
                            <i class="fas fa-headphones me-1"></i>View Details
                        </button>
                    </div>
                </div>
            </div>
        `).join('');
    }
    
    getDocumentIcon(type) {
        const icons = {
            'pdf': 'pdf',
            'doc': 'word',
            'docx': 'word',
            'xls': 'excel',
            'xlsx': 'excel',
            'ppt': 'powerpoint',
            'pptx': 'powerpoint',
            'txt': 'alt'
        };
        return icons[type] || 'alt';
    }
    
    applyFilters() {
        const search = document.getElementById('mediaSearch').value.toLowerCase();
        const domain = document.getElementById('domainFilter').value;
        const engine = document.getElementById('engineFilter').value;
        
        this.filteredData = {};
        
        Object.keys(this.mediaData).forEach(mediaType => {
            this.filteredData[mediaType] = this.mediaData[mediaType].filter(item => {
                const matchesSearch = !search || 
                    (item.title && item.title.toLowerCase().includes(search)) ||
                    (item.alt && item.alt.toLowerCase().includes(search)) ||
                    (item.filename && item.filename.toLowerCase().includes(search));
                
                const matchesDomain = !domain || item.domain === domain;
                const matchesEngine = !engine || item.search_engine === engine;
                
                return matchesSearch && matchesDomain && matchesEngine;
            });
        });
        
        this.displayMedia();
    }
    
    setupEventListeners() {
        document.getElementById('mediaSearch').addEventListener('input', () => this.applyFilters());
        document.getElementById('domainFilter').addEventListener('change', () => this.applyFilters());
        document.getElementById('engineFilter').addEventListener('change', () => this.applyFilters());
    }
    
    showError(message) {
        const containers = ['imagesGallery', 'videosGallery', 'documentsGallery', 'audioGallery'];
        containers.forEach(containerId => {
            document.getElementById(containerId).innerHTML = 
                `<div class="col-12 text-center text-danger"><p><i class="fas fa-exclamation-triangle me-2"></i>${message}</p></div>`;
        });
    }
}

// Global functions
function showMediaDetails(type, mediaItem) {
    const modal = new bootstrap.Modal(document.getElementById('mediaDetailModal'));
    const titleElement = document.getElementById('mediaDetailTitle');
    const bodyElement = document.getElementById('mediaDetailBody');
    const openButton = document.getElementById('openMediaUrl');
    
    titleElement.textContent = `${type.charAt(0).toUpperCase() + type.slice(1)} Details`;
    
    let detailsHtml = `
        <div class="row">
            <div class="col-md-6">
                <strong>Title:</strong> ${mediaItem.title || mediaItem.alt || mediaItem.filename || 'N/A'}
            </div>
            <div class="col-md-6">
                <strong>Domain:</strong> ${mediaItem.domain}
            </div>
            <div class="col-md-6 mt-2">
                <strong>Source:</strong> ${mediaItem.search_engine.toUpperCase()}
            </div>
            <div class="col-md-6 mt-2">
                <strong>Discovery Date:</strong> ${new Date(mediaItem.discovery_date).toLocaleDateString()}
            </div>
            <div class="col-12 mt-2">
                <strong>Source URL:</strong><br>
                <a href="${mediaItem.source_url}" target="_blank" class="text-info text-break">${mediaItem.source_url}</a>
            </div>
            <div class="col-12 mt-2">
                <strong>Media URL:</strong><br>
                <a href="${mediaItem.url}" target="_blank" class="text-warning text-break">${mediaItem.url}</a>
            </div>
        </div>
    `;
    
    if (type === 'image') {
        detailsHtml += `
            <div class="row mt-3">
                <div class="col-12 text-center">
                    <img src="${mediaItem.url}" class="img-fluid" style="max-height: 400px;" alt="${mediaItem.alt}">
                </div>
            </div>
        `;
    }
    
    bodyElement.innerHTML = detailsHtml;
    
    openButton.onclick = () => window.open(mediaItem.url, '_blank');
    
    modal.show();
}

function refreshMediaGallery() {
    location.reload();
}

function downloadMediaReport() {
    // Create and download a simple report
    const mediaGallery = window.mediaGallery;
    const report = {
        generated_at: new Date().toISOString(),
        summary: {
            total_images: mediaGallery.mediaData.images.length,
            total_videos: mediaGallery.mediaData.videos.length,
            total_documents: mediaGallery.mediaData.documents.length,
            total_audio: mediaGallery.mediaData.audio.length
        },
        media_data: mediaGallery.mediaData
    };
    
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `media_report_${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

function applyMediaFilters() {
    window.mediaGallery.applyFilters();
}

// Initialize media gallery
document.addEventListener('DOMContentLoaded', function() {
    window.mediaGallery = new MediaGallery();
});
