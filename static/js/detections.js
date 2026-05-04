// CASS - Detections Page JavaScript (Enhanced Timeline View)

let currentOffset = 0;
let currentLimit = 50;
let totalDetections = 0;

// Detection type icons
const typeIcons = {
    'person': '🚶',
    'fall': '🤕',
    'fire': '🔥',
    'suspicious': '🕵️',
    'violence': '⚔️',
    'motion': '🏃',
    'crowd': '👥'
};

// Format relative time (e.g., "2 minutes ago")
function getRelativeTime(isoString) {
    const date = new Date(isoString);
    const now = new Date();
    const diff = now - date;
    const seconds = Math.floor(diff / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);

    if (seconds < 60) return 'Just now';
    if (minutes < 60) return `${minutes} minute${minutes > 1 ? 's' : ''} ago`;
    if (hours < 24) return `${hours} hour${hours > 1 ? 's' : ''} ago`;
    if (days < 7) return `${days} day${days > 1 ? 's' : ''} ago`;

    return date.toLocaleDateString();
}

// Format full timestamp
function formatTimestamp(isoString) {
    const date = new Date(isoString);
    return date.toLocaleString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
}

// Get date group label
function getDateGroup(isoString) {
    const date = new Date(isoString);
    const today = new Date();
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);

    const dateStr = date.toDateString();
    const todayStr = today.toDateString();
    const yesterdayStr = yesterday.toDateString();

    if (dateStr === todayStr) return 'Today';
    if (dateStr === yesterdayStr) return 'Yesterday';

    const diffDays = Math.floor((today - date) / (1000 * 60 * 60 * 24));
    if (diffDays < 7) return 'This Week';
    if (diffDays < 30) return 'This Month';

    return date.toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
}

// Group detections by date
function groupDetectionsByDate(detections) {
    const groups = {};

    detections.forEach(detection => {
        const group = getDateGroup(detection.timestamp);
        if (!groups[group]) {
            groups[group] = [];
        }
        groups[group].push(detection);
    });

    return groups;
}

// Load detections from API
async function loadDetections() {
    const cameraId = document.getElementById('cameraFilter').value;
    const typeFilter = document.getElementById('typeFilter').value;
    const severityFilter = document.getElementById('severityFilter').value;
    const dateFilter = document.getElementById('dateFilter').value;

    const params = new URLSearchParams({
        limit: currentLimit,
        offset: currentOffset
    });

    if (cameraId) params.append('camera_id', cameraId);
    if (typeFilter) params.append('model_name', typeFilter);
    if (severityFilter) params.append('severity', severityFilter);

    try {
        const response = await fetch(`/api/detections?${params}`);
        const data = await response.json();

        totalDetections = data.total;
        renderDetectionTimeline(data.detections);
        updatePagination();
        updateStats(data.detections);

    } catch (error) {
        console.error('Error loading detections:', error);
        showError('Failed to load detections. Please try again.');
    }
}

// Render detection timeline with cards and date grouping
function renderDetectionTimeline(detections) {
    const timeline = document.getElementById('detectionTimeline');
    const paginationControls = document.getElementById('paginationControls');

    if (detections.length === 0) {
        timeline.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">🔍</div>
                <div class="empty-state-text">No detections found</div>
            </div>
        `;
        paginationControls.style.display = 'none';
        return;
    }

    paginationControls.style.display = 'flex';
    const groupedDetections = groupDetectionsByDate(detections);

    timeline.innerHTML = Object.entries(groupedDetections).map(([dateGroup, groupDetections]) => `
        <div class="date-group">
            <div class="date-header">
                <div class="date-header-icon">📅</div>
                <div class="date-header-text">${dateGroup}</div>
            </div>
            ${groupDetections.map(d => renderDetectionCard(d)).join('')}
        </div>
    `).join('');
}

// Render individual detection card
function renderDetectionCard(detection) {
    const icon = typeIcons[detection.model_name] || '🔔';
    const confidence = (detection.confidence * 100).toFixed(1);

    return `
        <div class="detection-card">
            <div class="detection-header">
                <div class="detection-type">
                    <div class="type-icon ${detection.model_name}">
                        ${icon}
                    </div>
                    <div>
                        <h4 class="detection-title">${detection.model_name} Detection</h4>
                        <div class="detection-time">
                            🕒 ${getRelativeTime(detection.timestamp)}
                        </div>
                    </div>
                </div>
                <span class="severity-badge ${detection.severity_level || 'LOW'}">
                    ${detection.severity_level || 'LOW'}
                </span>
            </div>
            <div class="detection-body">
                <div class="detection-meta">
                    <div class="meta-item">
                        <span class="meta-icon">📹</span>
                        <span class="meta-label">Camera:</span>
                        <span class="meta-value">${detection.camera_name}</span>
                    </div>
                    <div class="meta-item">
                        <span class="meta-icon">⏰</span>
                        <span class="meta-label">Time:</span>
                        <span class="meta-value">${formatTimestamp(detection.timestamp)}</span>
                    </div>
                    <div class="meta-item">
                        <span class="meta-icon">📊</span>
                        <span class="meta-label">Confidence:</span>
                        <span class="meta-value">${confidence}%</span>
                    </div>
                    <div class="confidence-bar">
                        <div class="confidence-fill" style="width: ${confidence}%"></div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

// Update statistics summary
function updateStats(detections) {
    const totalCount = detections.length;
    const criticalCount = detections.filter(d => d.severity_level === 'CRITICAL').length;
    const highCount = detections.filter(d => d.severity_level === 'HIGH').length;
    const mediumLowCount = detections.filter(d =>
        d.severity_level === 'MEDIUM' || d.severity_level === 'LOW' || !d.severity_level
    ).length;

    document.getElementById('totalCount').textContent = totalCount;
    document.getElementById('criticalCount').textContent = criticalCount;
    document.getElementById('highCount').textContent = highCount;
    document.getElementById('lowCount').textContent = mediumLowCount;
}

// Update pagination controls
function updatePagination() {
    const currentPage = Math.floor(currentOffset / currentLimit) + 1;
    const totalPages = Math.ceil(totalDetections / currentLimit);

    document.getElementById('pageInfo').textContent =
        `Showing ${currentOffset + 1}-${Math.min(currentOffset + currentLimit, totalDetections)} of ${totalDetections}`;

    document.getElementById('prevPage').disabled = currentOffset === 0;
    document.getElementById('nextPage').disabled = currentOffset + currentLimit >= totalDetections;
}

// Show error message
function showError(message) {
    const timeline = document.getElementById('detectionTimeline');
    timeline.innerHTML = `
        <div class="empty-state">
            <div class="empty-state-icon">⚠️</div>
            <div class="empty-state-text">${message}</div>
        </div>
    `;
}

// Event listeners
document.addEventListener('DOMContentLoaded', () => {
    // Load initial data
    loadDetections();

    // Filter changes - all filters
    ['dateFilter', 'cameraFilter', 'typeFilter', 'severityFilter'].forEach(filterId => {
        document.getElementById(filterId).addEventListener('change', () => {
            currentOffset = 0;
            loadDetections();
        });
    });

    // Refresh button
    document.getElementById('refreshBtn').addEventListener('click', () => {
        loadDetections();
        // Visual feedback
        const btn = document.getElementById('refreshBtn');
        btn.textContent = '⏳ Refreshing...';
        setTimeout(() => {
            btn.textContent = '🔄 Refresh';
        }, 1000);
    });

    // Pagination
    document.getElementById('prevPage').addEventListener('click', () => {
        if (currentOffset >= currentLimit) {
            currentOffset -= currentLimit;
            loadDetections();
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }
    });

    document.getElementById('nextPage').addEventListener('click', () => {
        if (currentOffset + currentLimit < totalDetections) {
            currentOffset += currentLimit;
            loadDetections();
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }
    });

    // Auto-refresh every 5 seconds for near real-time updates
    setInterval(() => {
        loadDetections();
        // Show subtle refresh indicator
        const refreshBtn = document.getElementById('refreshBtn');
        if (refreshBtn) {
            refreshBtn.classList.add('auto-refreshing');
            setTimeout(() => refreshBtn.classList.remove('auto-refreshing'), 500);
        }
    }, 5000);
});
