/**
 * CASS - Recordings Page JavaScript
 * Handles video recordings display, filtering, and playback
 */

let currentPage = 1;
let totalPages = 1;
let currentRecordingId = null;
let currentFilters = {
    camera_id: '',
    recording_type: 'all',
    start_date: '',
    end_date: ''
};

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    loadRecordings();
    
    // Set up event listeners
    document.getElementById('cameraFilter').addEventListener('change', updateFilters);
    document.getElementById('typeFilter').addEventListener('change', updateFilters);
    document.getElementById('startDate').addEventListener('change', updateFilters);
    document.getElementById('endDate').addEventListener('change', updateFilters);
});

// Update current filters from form
function updateFilters() {
    currentFilters.camera_id = document.getElementById('cameraFilter').value;
    currentFilters.recording_type = document.getElementById('typeFilter').value;
    currentFilters.start_date = document.getElementById('startDate').value;
    currentFilters.end_date = document.getElementById('endDate').value;
}

// Apply filters and reload
function applyFilters() {
    updateFilters();
    currentPage = 1;
    loadRecordings();
}

// Clear all filters
function clearFilters() {
    document.getElementById('cameraFilter').value = '';
    document.getElementById('typeFilter').value = 'all';
    document.getElementById('startDate').value = '';
    document.getElementById('endDate').value = '';
    currentFilters = {
        camera_id: '',
        recording_type: 'all',
        start_date: '',
        end_date: ''
    };
    currentPage = 1;
    loadRecordings();
}

// Load recordings from API
async function loadRecordings() {
    const loading = document.getElementById('loading');
    const grid = document.getElementById('recordingsGrid');
    const emptyState = document.getElementById('emptyState');
    const pagination = document.getElementById('pagination');
    
    // Show loading
    loading.style.display = 'block';
    grid.innerHTML = '';
    emptyState.style.display = 'none';
    pagination.style.display = 'none';
    
    try {
        // Build query parameters
        const params = new URLSearchParams({
            page: currentPage,
            per_page: 20
        });
        
        if (currentFilters.camera_id) params.append('camera_id', currentFilters.camera_id);
        if (currentFilters.recording_type !== 'all') params.append('recording_type', currentFilters.recording_type);
        if (currentFilters.start_date) params.append('start_date', currentFilters.start_date);
        if (currentFilters.end_date) params.append('end_date', currentFilters.end_date);
        
        const response = await fetch(`/api/recordings?${params}`);
        const data = await response.json();
        
        loading.style.display = 'none';
        
        if (data.recordings && data.recordings.length > 0) {
            displayRecordings(data.recordings);
            updateStatistics(data);
            
            // Show pagination if needed
            totalPages = data.total_pages;
            if (totalPages > 1) {
                displayPagination();
                pagination.style.display = 'flex';
            }
        } else {
            emptyState.style.display = 'block';
            updateStatistics({ total: 0 });
        }
    } catch (error) {
        console.error('Error loading recordings:', error);
        loading.style.display = 'none';
        emptyState.style.display = 'block';
        alert('Failed to load recordings. Please try again.');
    }
}

// Display recordings in grid
function displayRecordings(recordings) {
    const grid = document.getElementById('recordingsGrid');
    grid.innerHTML = '';
    
    recordings.forEach(recording => {
        const card = createRecordingCard(recording);
        grid.appendChild(card);
    });
}

// Create a recording card element
function createRecordingCard(recording) {
    const card = document.createElement('div');
    card.className = 'recording-card';
    card.onclick = () => openVideoModal(recording.id);
    
    const startTime = new Date(recording.start_time);
    const duration = formatDuration(recording.duration);
    const fileSize = formatFileSize(recording.file_size);
    
    let detectionBadge = '';
    if (recording.detection_info) {
        detectionBadge = `
            <div class="detection-badge">
                <strong>Detection:</strong> ${recording.detection_info.model_name} 
                (${recording.detection_info.confidence}% confidence, 
                ${recording.detection_info.severity_level} severity)
            </div>
        `;
    }
    
    card.innerHTML = `
        <div class="recording-thumbnail">
            <!-- Placeholder for video thumbnail -->
        </div>
        <div class="recording-info">
            <div class="recording-header">
                <div class="recording-title">${recording.camera_name}</div>
                <span class="type-badge ${recording.recording_type}">${recording.recording_type}</span>
            </div>
            <div class="recording-meta">
                <span>📅 ${startTime.toLocaleDateString()} ${startTime.toLocaleTimeString()}</span>
                <span>⏱️ Duration: ${duration}</span>
                <span>💾 Size: ${fileSize}</span>
            </div>
            ${detectionBadge}
        </div>
    `;
    
    return card;
}

// Update statistics cards
function updateStatistics(data) {
    document.getElementById('totalRecordings').textContent = data.total || 0;
    
    // Count by type (if we have the full list)
    if (data.recordings) {
        const detectionCount = data.recordings.filter(r => r.recording_type === 'detection').length;
        const continuousCount = data.recordings.filter(r => r.recording_type === 'continuous').length;
        document.getElementById('detectionCount').textContent = detectionCount;
        document.getElementById('continuousCount').textContent = continuousCount;
    }
}

// Display pagination controls
function displayPagination() {
    const pagination = document.getElementById('pagination');
    pagination.innerHTML = '';
    
    // Previous button
    const prevBtn = document.createElement('button');
    prevBtn.textContent = '← Previous';
    prevBtn.disabled = currentPage === 1;
    prevBtn.onclick = () => changePage(currentPage - 1);
    pagination.appendChild(prevBtn);
    
    // Page info
    const pageInfo = document.createElement('span');
    pageInfo.textContent = `Page ${currentPage} of ${totalPages}`;
    pagination.appendChild(pageInfo);
    
    // Next button
    const nextBtn = document.createElement('button');
    nextBtn.textContent = 'Next →';
    nextBtn.disabled = currentPage === totalPages;
    nextBtn.onclick = () => changePage(currentPage + 1);
    pagination.appendChild(nextBtn);
}

// Change page
function changePage(page) {
    if (page >= 1 && page <= totalPages) {
        currentPage = page;
        loadRecordings();
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }
}

// Open video modal
async function openVideoModal(recordingId) {
    currentRecordingId = recordingId;
    
    try {
        const response = await fetch(`/api/recordings/${recordingId}`);
        const recording = await response.json();
        
        // Set video source
        const videoPlayer = document.getElementById('videoPlayer');
        videoPlayer.src = `/api/recordings/video/${recordingId}`;
        
        // Set modal title
        document.getElementById('modalTitle').textContent = `${recording.camera_name} - ${new Date(recording.start_time).toLocaleString()}`;
        
        // Display recording details
        displayRecordingDetails(recording);
        
        // Show modal
        document.getElementById('videoModal').classList.add('active');
    } catch (error) {
        console.error('Error loading recording details:', error);
        alert('Failed to load recording details.');
    }
}

// Display recording details in modal
function displayRecordingDetails(recording) {
    const detailsContainer = document.getElementById('recordingDetails');
    
    const startTime = new Date(recording.start_time);
    const endTime = recording.end_time ? new Date(recording.end_time) : null;
    
    let detectionInfo = '';
    if (recording.detection_info) {
        detectionInfo = `
            <div class="detail-group">
                <h4>Detection Information</h4>
                <p><strong>Type:</strong> ${recording.detection_info.model_name}</p>
                <p><strong>Confidence:</strong> ${recording.detection_info.confidence}%</p>
                <p><strong>Severity:</strong> ${recording.detection_info.severity_level} (${recording.detection_info.severity_score}/10)</p>
                <p><strong>Detected At:</strong> ${new Date(recording.detection_info.timestamp).toLocaleString()}</p>
            </div>
        `;
    }
    
    detailsContainer.innerHTML = `
        <div class="detail-group">
            <h4>Recording Information</h4>
            <p><strong>Camera:</strong> ${recording.camera_name}</p>
            <p><strong>Type:</strong> ${recording.recording_type}</p>
            <p><strong>Filename:</strong> ${recording.filename}</p>
        </div>
        <div class="detail-group">
            <h4>Time Information</h4>
            <p><strong>Started:</strong> ${startTime.toLocaleString()}</p>
            ${endTime ? `<p><strong>Ended:</strong> ${endTime.toLocaleString()}</p>` : ''}
            <p><strong>Duration:</strong> ${formatDuration(recording.duration)}</p>
        </div>
        <div class="detail-group">
            <h4>File Information</h4>
            <p><strong>Size:</strong> ${formatFileSize(recording.file_size)}</p>
            <p><strong>Path:</strong> ${recording.filepath}</p>
        </div>
        ${detectionInfo}
    `;
}

// Close video modal
function closeVideoModal() {
    const modal = document.getElementById('videoModal');
    const videoPlayer = document.getElementById('videoPlayer');
    
    modal.classList.remove('active');
    videoPlayer.pause();
    videoPlayer.src = '';
    currentRecordingId = null;
}

// Download recording
function downloadRecording() {
    if (currentRecordingId) {
        window.open(`/api/recordings/video/${currentRecordingId}`, '_blank');
    }
}

// Delete recording (admin only)
async function deleteRecording() {
    if (!currentRecordingId) return;
    
    if (!confirm('Are you sure you want to delete this recording? This action cannot be undone.')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/recordings/${currentRecordingId}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert('Recording deleted successfully');
            closeVideoModal();
            loadRecordings(); // Reload the list
        } else {
            alert('Failed to delete recording: ' + (data.error || 'Unknown error'));
        }
    } catch (error) {
        console.error('Error deleting recording:', error);
        alert('Failed to delete recording. Please try again.');
    }
}

// Utility: Format duration in seconds to readable format
function formatDuration(seconds) {
    if (!seconds) return '0:00';
    
    seconds = Math.floor(seconds);
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    
    if (hours > 0) {
        return `${hours}:${String(minutes).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
    } else {
        return `${minutes}:${String(secs).padStart(2, '0')}`;
    }
}

// Utility: Format file size in bytes to readable format
function formatFileSize(bytes) {
    if (!bytes) return 'Unknown';
    
    const units = ['B', 'KB', 'MB', 'GB'];
    let size = bytes;
    let unitIndex = 0;
    
    while (size >= 1024 && unitIndex < units.length - 1) {
        size /= 1024;
        unitIndex++;
    }
    
    return `${size.toFixed(1)} ${units[unitIndex]}`;
}

// Close modal when clicking outside
window.onclick = function(event) {
    const modal = document.getElementById('videoModal');
    if (event.target === modal) {
        closeVideoModal();
    }
}
