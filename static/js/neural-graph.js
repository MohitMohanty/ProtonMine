class NeuralGraph {
    constructor(containerId) {
        this.container = d3.select(`#${containerId}`);
        this.width = this.container.node().getBoundingClientRect().width;
        this.height = 600;
        
        this.svg = this.container.append('svg')
            .attr('width', this.width)
            .attr('height', this.height);
        
        this.g = this.svg.append('g');
        
        // Add zoom behavior
        this.zoom = d3.zoom()
            .scaleExtent([0.1, 4])
            .on('zoom', (event) => {
                this.g.attr('transform', event.transform);
            });
        
        this.svg.call(this.zoom);
        
        // Initialize simulation
        this.simulation = d3.forceSimulation()
            .force('link', d3.forceLink().id(d => d.id).distance(100))
            .force('charge', d3.forceManyBody().strength(-300))
            .force('center', d3.forceCenter(this.width / 2, this.height / 2))
            .force('collision', d3.forceCollide().radius(20));
        
        this.nodes = [];
        this.links = [];
        
        this.loadData();
        this.setupTooltip();
    }
    
    setupTooltip() {
        this.tooltip = d3.select('body').append('div')
            .attr('class', 'tooltip')
            .style('position', 'absolute')
            .style('background', 'rgba(0, 0, 0, 0.9)')
            .style('color', 'white')
            .style('padding', '10px')
            .style('border-radius', '5px')
            .style('pointer-events', 'none')
            .style('opacity', 0);
    }
    
    async loadData() {
        try {
            const response = await fetch('/api/graph-data');
            const data = await response.json();
            this.updateGraph(data.nodes, data.links);
        } catch (error) {
            console.error('Error loading graph data:', error);
        }
    }
    
    updateGraph(nodes, links) {
        this.nodes = nodes;
        this.links = links;
        
        // Clear existing graph
        this.g.selectAll('*').remove();
        
        // Create links
        const link = this.g.append('g')
            .attr('class', 'links')
            .selectAll('line')
            .data(this.links)
            .enter().append('line')
            .attr('stroke', '#999')
            .attr('stroke-opacity', 0.6)
            .attr('stroke-width', 2);
        
        // Create nodes
        const node = this.g.append('g')
            .attr('class', 'nodes')
            .selectAll('circle')
            .data(this.nodes)
            .enter().append('circle')
            .attr('r', d => this.getNodeRadius(d))
            .attr('fill', d => this.getNodeColor(d))
            .attr('stroke', '#fff')
            .attr('stroke-width', 2)
            .call(d3.drag()
                .on('start', this.dragstarted.bind(this))
                .on('drag', this.dragged.bind(this))
                .on('end', this.dragended.bind(this)));
        
        // Add labels
        const label = this.g.append('g')
            .attr('class', 'labels')
            .selectAll('text')
            .data(this.nodes)
            .enter().append('text')
            .text(d => d.label)
            .attr('font-size', '10px')
            .attr('dx', 15)
            .attr('dy', 4)
            .attr('fill', '#fff');
        
        // Add hover effects
        node.on('mouseover', (event, d) => {
                this.tooltip.transition()
                    .duration(200)
                    .style('opacity', .9);
                this.tooltip.html(this.getTooltipContent(d))
                    .style('left', (event.pageX + 10) + 'px')
                    .style('top', (event.pageY - 28) + 'px');
            })
            .on('mouseout', () => {
                this.tooltip.transition()
                    .duration(500)
                    .style('opacity', 0);
            });
        
        // Update simulation
        this.simulation.nodes(this.nodes);
        this.simulation.force('link').links(this.links);
        
        this.simulation.on('tick', () => {
            link
                .attr('x1', d => d.source.x)
                .attr('y1', d => d.source.y)
                .attr('x2', d => d.target.x)
                .attr('y2', d => d.target.y);
            
            node
                .attr('cx', d => d.x)
                .attr('cy', d => d.y);
            
            label
                .attr('x', d => d.x)
                .attr('y', d => d.y);
        });
        
        this.simulation.restart();
    }
    
    getNodeColor(d) {
        const colors = {
            'document': '#007bff',
            'domain': '#ffc107',
            'keyword': '#28a745'
        };
        return colors[d.type] || '#6c757d';
    }
    
    getNodeRadius(d) {
        if (d.type === 'document') return 8;
        if (d.type === 'domain') return Math.min(15, 8 + (d.count || 0));
        if (d.type === 'keyword') return Math.min(12, 6 + (d.count || 0));
        return 6;
    }
    
    getTooltipContent(d) {
        if (d.type === 'document') {
            return `
                <strong>${d.label}</strong><br>
                URL: ${d.url}<br>
                Trust Score: ${d.trust_score || 'N/A'}<br>
                Media Items: ${d.media_count || 0}
            `;
        } else if (d.type === 'domain') {
            return `
                <strong>Domain: ${d.label}</strong><br>
                Documents: ${d.count || 0}
            `;
        } else if (d.type === 'keyword') {
            return `
                <strong>Keyword: ${d.label}</strong><br>
                Mentions: ${d.count || 0}
            `;
        }
        return d.label;
    }
    
    dragstarted(event, d) {
        if (!event.active) this.simulation.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
    }
    
    dragged(event, d) {
        d.fx = event.x;
        d.fy = event.y;
    }
    
    dragended(event, d) {
        if (!event.active) this.simulation.alphaTarget(0);
        d.fx = null;
        d.fy = null;
    }
}

// Initialize neural graph when page loads
document.addEventListener('DOMContentLoaded', function() {
    const neuralGraph = new NeuralGraph('neuralGraph');
    
    // Auto-refresh graph every 30 seconds
    setInterval(() => {
        neuralGraph.loadData();
    }, 30000);
});

function resetGraph() {
    location.reload();
}

function toggleFullscreen() {
    const elem = document.getElementById('neuralGraph');
    if (elem.requestFullscreen) {
        elem.requestFullscreen();
    }
}
