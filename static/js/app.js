// CASS - Main Application JavaScript

// Global Detection Control
document.addEventListener('DOMContentLoaded', () => {
    const globalDetectionBtn = document.getElementById('globalDetectionBtn');
    let globalDetectionActive = false;

    if (globalDetectionBtn) {
        globalDetectionBtn.addEventListener('click', async () => {
            try {
                const endpoint = globalDetectionActive ?
                    '/api/detection/global/stop' : '/api/detection/global/start';

                const response = await fetch(endpoint, { method: 'POST' });
                const data = await response.json();

                if (data.success) {
                    globalDetectionActive = !globalDetectionActive;
                    globalDetectionBtn.textContent = globalDetectionActive ?
                        'Stop Global Detection' : 'Start Global Detection';
                    globalDetectionBtn.classList.toggle('btn-success');
                    globalDetectionBtn.classList.toggle('btn-danger');

                    showNotification(data.message, 'success');
                }
            } catch (error) {
                console.error('Error toggling global detection:', error);
                showNotification('Failed to toggle detection', 'error');
            }
        });
    }

    // Add Camera Modal
    const addCameraBtn = document.getElementById('addCameraBtn');
    const addCameraModal = document.getElementById('addCameraModal');
    const addCameraForm = document.getElementById('addCameraForm');

    if (addCameraBtn && addCameraModal) {
        addCameraBtn.addEventListener('click', () => {
            addCameraModal.classList.add('active');
        });

        // Close modal
        const closeBtn = addCameraModal.querySelector('.close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                addCameraModal.classList.remove('active');
            });
        }

        // Close on outside click
        addCameraModal.addEventListener('click', (e) => {
            if (e.target === addCameraModal) {
                addCameraModal.classList.remove('active');
            }
        });

        // Submit form
        if (addCameraForm) {
            addCameraForm.addEventListener('submit', async (e) => {
                e.preventDefault();

                const formData = {
                    name: document.getElementById('cameraName').value,
                    source: document.getElementById('cameraSource').value,
                    location: document.getElementById('cameraLocation').value
                };

                try {
                    const response = await fetch('/api/cameras', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(formData)
                    });

                    if (response.ok) {
                        showNotification('Camera added successfully', 'success');
                        addCameraModal.classList.remove('active');
                        addCameraForm.reset();
                        setTimeout(() => location.reload(), 1000);
                    } else if (response.status === 409) {
                        // Duplicate camera source
                        const error = await response.json();
                        showNotification(error.message || `Camera source already exists: ${error.existing_camera}`, 'error');
                    } else {
                        const error = await response.json();
                        showNotification(error.error || 'Failed to add camera', 'error');
                    }
                } catch (error) {
                    console.error('Error adding camera:', error);
                    showNotification('Failed to add camera', 'error');
                }
            });
        }
    }

    // Camera View - Detection Controls
    const applyDetectionBtn = document.getElementById('applyDetectionBtn');
    const stopDetectionBtn = document.getElementById('stopDetectionBtn');

    if (applyDetectionBtn && typeof cameraId !== 'undefined') {
        applyDetectionBtn.addEventListener('click', async () => {
            const selectedModels = Array.from(document.querySelectorAll('.detection-model:checked'))
                .map(cb => cb.dataset.model);

            try {
                const response = await fetch(`/api/detection/${cameraId}/start`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ models: selectedModels })
                });

                const data = await response.json();
                if (data.success) {
                    showNotification(data.message, 'success');
                }
            } catch (error) {
                console.error('Error starting detection:', error);
                showNotification('Failed to start detection', 'error');
            }
        });
    }

    if (stopDetectionBtn && typeof cameraId !== 'undefined') {
        stopDetectionBtn.addEventListener('click', async () => {
            try {
                const response = await fetch(`/api/detection/${cameraId}/stop`, {
                    method: 'POST'
                });

                const data = await response.json();
                if (data.success) {
                    showNotification(data.message, 'success');
                    document.querySelectorAll('.detection-model').forEach(cb => cb.checked = false);
                }
            } catch (error) {
                console.error('Error stopping detection:', error);
                showNotification('Failed to stop detection', 'error');
            }
        });
    }

    // Recording Control
    const recordBtn = document.getElementById('recordBtn');
    let isRecording = recordBtn && recordBtn.textContent.includes('Stop');

    if (recordBtn && typeof cameraId !== 'undefined') {
        recordBtn.addEventListener('click', async () => {
            try {
                const endpoint = isRecording ?
                    `/api/recording/${cameraId}/stop` : `/api/recording/${cameraId}/start`;

                const response = await fetch(endpoint, { method: 'POST' });
                const data = await response.json();

                if (data.success) {
                    isRecording = !isRecording;
                    recordBtn.textContent = isRecording ? 'Stop Recording' : 'Start Recording';
                    recordBtn.classList.toggle('btn-primary');
                    recordBtn.classList.toggle('btn-danger');

                    showNotification(
                        isRecording ? 'Recording started' : 'Recording stopped',
                        'success'
                    );
                }
            } catch (error) {
                console.error('Error toggling recording:', error);
                showNotification('Failed to toggle recording', 'error');
            }
        });
    }

    // Manual Alert
    const manualAlertBtn = document.getElementById('manualAlertBtn');
    const manualAlertModal = document.getElementById('manualAlertModal');
    const manualAlertForm = document.getElementById('manualAlertForm');

    if (manualAlertBtn && manualAlertModal) {
        manualAlertBtn.addEventListener('click', () => {
            manualAlertModal.classList.add('active');
        });

        const closeBtn = manualAlertModal.querySelector('.close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                manualAlertModal.classList.remove('active');
            });
        }

        manualAlertModal.addEventListener('click', (e) => {
            if (e.target === manualAlertModal) {
                manualAlertModal.classList.remove('active');
            }
        });

        if (manualAlertForm && typeof cameraId !== 'undefined') {
            manualAlertForm.addEventListener('submit', async (e) => {
                e.preventDefault();

                const message = document.getElementById('alertMessage').value;

                try {
                    const response = await fetch(`/api/alert/manual/${cameraId}`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ message })
                    });

                    const data = await response.json();
                    if (data.success) {
                        showNotification('Alert sent successfully', 'success');
                        manualAlertModal.classList.remove('active');
                        manualAlertForm.reset();
                    }
                } catch (error) {
                    console.error('Error sending alert:', error);
                    showNotification('Failed to send alert', 'error');
                }
            });
        }
    }
});

// Notification System
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;

    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 1rem 1.5rem;
        background: ${type === 'success' ? '#3fb950' : type === 'error' ? '#f85149' : '#58a6ff'};
        color: white;
        border-radius: 6px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
        z-index: 10000;
        animation: slideIn 0.3s ease;
    `;

    document.body.appendChild(notification);

    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Add animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(400px);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(400px);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);
