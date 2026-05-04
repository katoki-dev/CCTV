// CASS - Camera Detection History Page JavaScript

let currentOffset = 0;
let currentLimit = 50;
let totalDetections = 0;

// Format timestamp
function formatTime(isoString) {
    const date = new Date(isoString);
    return date.toLocaleString();
}

// Get severity badge class
function getSeverityClass(level) {
    switch (level) {
        case 'CRITICAL': return 'badge-danger';
        case 'HIGH': return 'badge-warning';
        case 'MEDIUM': return 'badge-primary';
        default: return 'badge-secondary';
    }
}

// Load detections from API
async function loadDetections() {
    const modelName = document.getElementById('modelFilter').value;
    currentLimit = parseInt(document.getElementById('limitFilter').value);

    const params = new URLSearchParams({
        camera_id: cameraId,
        limit: currentLimit,
        offset: currentOffset
    });

    if (modelName) params.append('model_name', modelName);

    try {
        const response = await fetch(`/api/detections?${params}`);
        const data = await response.json();

        totalDetections = data.total;
        renderDetections(data.detections);
        updatePagination();
        updateStats(data.detections);

    } catch (error) {
        console.error('Error loading detections:', error);
        document.getElementById('detectionsBody').innerHTML =
            '<tr><td colspan="4" class="no-data">Failed to load detections</td></tr>';
    }
}

// Render detections table
function renderDetections(detections) {
    const tbody = document.getElementById('detectionsBody');

    if (detections.length === 0) {
        tbody.innerHTML = '<tr><td colspan="4" class="no-data">No detections found</td></tr>';
        return;
    }

    tbody.innerHTML = detections.map(d => `
        <tr>
            <td>${formatTime(d.timestamp)}</td>
            <td>
                <span class="model-badge model-${d.model_name}">${d.model_name}</span>
            </td>
            <td>${(d.confidence * 100).toFixed(1)}%</td>
            <td>
                <span class="badge ${getSeverityClass(d.severity_level)}">
                    ${d.severity_level || 'N/A'}
                </span>
            </td>
        </tr>
    `).join('');
}

// Update pagination controls
function updatePagination() {
    const currentPage = Math.floor(currentOffset / currentLimit) + 1;
    const totalPages = Math.ceil(totalDetections / currentLimit);

    document.getElementById('pageInfo').textContent = `Page ${currentPage} of ${totalPages || 1}`;
    document.getElementById('prevPage').disabled = currentOffset === 0;
    document.getElementById('nextPage').disabled = currentOffset + currentLimit >= totalDetections;

    document.getElementById('totalDetections').textContent = totalDetections;
}

// Update stats based on current data
function updateStats(detections) {
    const personCount = detections.filter(d => d.model_name === 'person').length;
    const fallCount = detections.filter(d => d.model_name === 'fall').length;
    const phoneCount = detections.filter(d => d.model_name === 'phone').length;

    document.getElementById('personCount').textContent = personCount;
    document.getElementById('fallCount').textContent = fallCount;
    document.getElementById('phoneCount').textContent = phoneCount;
}

// Event listeners
document.addEventListener('DOMContentLoaded', () => {
    // Load initial data
    loadDetections();

    // Filter changes
    document.getElementById('modelFilter').addEventListener('change', () => {
        currentOffset = 0;
        loadDetections();
    });

    document.getElementById('limitFilter').addEventListener('change', () => {
        currentOffset = 0;
        loadDetections();
    });

    // Refresh button
    document.getElementById('refreshBtn').addEventListener('click', loadDetections);

    // Pagination
    document.getElementById('prevPage').addEventListener('click', () => {
        if (currentOffset >= currentLimit) {
            currentOffset -= currentLimit;
            loadDetections();
        }
    });

    document.getElementById('nextPage').addEventListener('click', () => {
        if (currentOffset + currentLimit < totalDetections) {
            currentOffset += currentLimit;
            loadDetections();
        }
    });

    // Auto-refresh every 30 seconds
    // Auto-refresh every 5 seconds
    setInterval(loadDetections, 5000);
});
