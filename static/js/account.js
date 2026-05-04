// CASS - Account Page JavaScript

// Toast notification
function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
        <span>${message}</span>
        <button onclick="this.parentElement.remove()">×</button>
    `;

    toast.style.cssText = `
        position: fixed;
        bottom: 20px;
        right: 20px;
        padding: 1rem 1.5rem;
        border-radius: 8px;
        color: white;
        font-size: 0.9rem;
        display: flex;
        align-items: center;
        gap: 1rem;
        z-index: 9999;
        animation: slideIn 0.3s ease;
        background: ${type === 'success' ? '#3fb950' : type === 'error' ? '#f85149' : '#d29922'};
    `;

    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 5000);
}

document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('permissionRequestForm');

    if (form) {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();

            const cameraId = document.getElementById('cameraSelect').value;
            const reason = document.getElementById('requestReason').value;

            if (!cameraId) {
                showToast('Please select a camera', 'error');
                return;
            }

            const requestedValue = {
                can_view: document.getElementById('reqView').checked,
                can_control: document.getElementById('reqControl').checked,
                receive_alerts: document.getElementById('reqAlerts').checked
            };

            try {
                const response = await fetch('/api/permission-requests', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        camera_id: parseInt(cameraId),
                        request_type: 'access',
                        requested_value: requestedValue,
                        reason: reason
                    })
                });

                const data = await response.json();

                if (response.ok) {
                    showToast('Permission request submitted successfully!', 'success');
                    form.reset();
                    // Reload to show the new request in history
                    setTimeout(() => location.reload(), 1500);
                } else {
                    showToast(data.error || 'Failed to submit request', 'error');
                }
            } catch (error) {
                console.error('Error submitting request:', error);
                showToast('Failed to submit request', 'error');
            }
        });
    }
});
