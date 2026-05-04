// CASS - Admin Panel JavaScript

// Utility function for confirmation dialog
function showConfirmation(message, onConfirm) {
    const modal = document.getElementById('confirmModal');
    const messageEl = document.getElementById('confirmMessage');
    const okBtn = document.getElementById('confirmOk');
    const cancelBtn = document.getElementById('confirmCancel');
    const closeBtn = modal.querySelector('.close');

    messageEl.innerHTML = `<p>${message}</p>`;
    modal.classList.add('active');

    const cleanup = () => {
        modal.classList.remove('active');
        okBtn.onclick = null;
        cancelBtn.onclick = null;
        closeBtn.onclick = null;
    };

    okBtn.onclick = () => {
        cleanup();
        onConfirm();
    };

    cancelBtn.onclick = cleanup;
    closeBtn.onclick = cleanup;
}

// Toast notification
function showToast(message, type = 'success') {
    // Create toast if doesn't exist
    let toast = document.getElementById('toast');
    if (!toast) {
        toast = document.createElement('div');
        toast.id = 'toast';
        toast.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 1rem 1.5rem;
            border-radius: 6px;
            color: white;
            font-weight: 500;
            z-index: 10000;
            animation: slideIn 0.3s ease-out;
        `;
        document.body.appendChild(toast);
    }

    toast.textContent = message;
    toast.style.background = type === 'success' ? '#28a745' : '#dc3545';
    toast.style.display = 'block';

    setTimeout(() => {
        toast.style.display = 'none';
    }, 3000);
}

// Add CSS animation
if (!document.getElementById('toast-styles')) {
    const style = document.createElement('style');
    style.id = 'toast-styles';
    style.textContent = `
        @keyframes slideIn {
            from {
                transform: translateX(100%);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }
    `;
    document.head.appendChild(style);
}

document.addEventListener('DOMContentLoaded', () => {
    // ========== Camera Management ==========

    document.querySelectorAll('.delete-camera').forEach(btn => {
        btn.addEventListener('click', async () => {
            const cameraId = btn.dataset.cameraId;
            const cameraName = btn.dataset.cameraName;

            showConfirmation(
                `Are you sure you want to delete camera "<strong>${cameraName}</strong>"?<br><br>
                <strong>Warning:</strong> This will also delete:<br>
                - All permissions for this camera<br>
                - All detection logs<br>
                - All restricted zones<br>
                This action cannot be undone.`,
                async () => {
                    try {
                        const response = await fetch(`/api/cameras/${cameraId}`, {
                            method: 'DELETE'
                        });

                        if (response.ok) {
                            showToast(`Camera "${cameraName}" deleted successfully`);
                            setTimeout(() => location.reload(), 1000);
                        } else {
                            const error = await response.json();
                            showToast(error.error || 'Failed to delete camera', 'error');
                        }
                    } catch (error) {
                        console.error('Error deleting camera:', error);
                        showToast('Failed to delete camera', 'error');
                    }
                }
            );
        });
    });

    // Edit Camera Modal
    const editCameraModal = document.getElementById('editCameraModal');
    const editCameraForm = document.getElementById('editCameraForm');

    document.querySelectorAll('.edit-camera').forEach(btn => {
        btn.addEventListener('click', () => {
            const cameraId = btn.dataset.cameraId;
            const cameraName = btn.dataset.cameraName;
            const cameraLocation = btn.dataset.cameraLocation;
            const cameraSource = btn.dataset.cameraSource;

            // Populate the form
            document.getElementById('editCameraId').value = cameraId;
            document.getElementById('editCameraName').value = cameraName;
            document.getElementById('editCameraLocation').value = cameraLocation || '';
            document.getElementById('editCameraSource').value = cameraSource;

            editCameraModal.classList.add('active');
        });
    });

    if (editCameraModal) {
        const closeBtn = editCameraModal.querySelector('.close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                editCameraModal.classList.remove('active');
            });
        }

        editCameraModal.addEventListener('click', (e) => {
            if (e.target === editCameraModal) {
                editCameraModal.classList.remove('active');
            }
        });

        if (editCameraForm) {
            editCameraForm.addEventListener('submit', async (e) => {
                e.preventDefault();

                const cameraId = document.getElementById('editCameraId').value;
                const formData = {
                    name: document.getElementById('editCameraName').value,
                    source: document.getElementById('editCameraSource').value,
                    location: document.getElementById('editCameraLocation').value
                };

                try {
                    const response = await fetch(`/api/cameras/${cameraId}`, {
                        method: 'PUT',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(formData)
                    });

                    if (response.ok) {
                        showToast('Camera updated successfully');
                        editCameraModal.classList.remove('active');
                        setTimeout(() => location.reload(), 1000);
                    } else {
                        const error = await response.json();
                        showToast(error.error || 'Failed to update camera', 'error');
                    }
                } catch (error) {
                    console.error('Error updating camera:', error);
                    showToast('Failed to update camera', 'error');
                }
            });
        }
    }

    // Add Camera Modal
    const addCameraBtn = document.getElementById('addCameraBtn');
    const addCameraModal = document.getElementById('addCameraModal');
    const addCameraForm = document.getElementById('addCameraForm');

    if (addCameraBtn && addCameraModal) {
        addCameraBtn.addEventListener('click', () => {
            addCameraModal.classList.add('active');
        });

        const closeBtn = addCameraModal.querySelector('.close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                addCameraModal.classList.remove('active');
            });
        }

        addCameraModal.addEventListener('click', (e) => {
            if (e.target === addCameraModal) {
                addCameraModal.classList.remove('active');
            }
        });

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
                        showToast('Camera added successfully');
                        addCameraModal.classList.remove('active');
                        addCameraForm.reset();
                        setTimeout(() => location.reload(), 1000);
                    } else {
                        const error = await response.json();
                        showToast(error.error || error.message || 'Failed to add camera', 'error');
                    }
                } catch (error) {
                    console.error('Error adding camera:', error);
                    showToast('Failed to add camera', 'error');
                }
            });
        }
    }

    // ========== User Management ==========

    // Add User Modal
    const addUserBtn = document.getElementById('addUserBtn');
    const addUserModal = document.getElementById('addUserModal');
    const addUserForm = document.getElementById('addUserForm');

    if (addUserBtn && addUserModal) {
        addUserBtn.addEventListener('click', () => {
            addUserModal.classList.add('active');
        });

        const closeBtn = addUserModal.querySelector('.close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                addUserModal.classList.remove('active');
            });
        }

        addUserModal.addEventListener('click', (e) => {
            if (e.target === addUserModal) {
                addUserModal.classList.remove('active');
            }
        });

        if (addUserForm) {
            addUserForm.addEventListener('submit', async (e) => {
                e.preventDefault();

                const formData = {
                    username: document.getElementById('newUsername').value,
                    email: document.getElementById('newEmail').value,
                    phone_number: document.getElementById('newPhone')?.value || '',
                    password: document.getElementById('newPassword').value,
                    is_admin: document.getElementById('newIsAdmin').checked,
                    is_approved: document.getElementById('newIsApproved').checked
                };

                try {
                    const response = await fetch('/api/users', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(formData)
                    });

                    if (response.ok) {
                        showToast('User created successfully');
                        addUserModal.classList.remove('active');
                        addUserForm.reset();
                        setTimeout(() => location.reload(), 1000);
                    } else {
                        const error = await response.json();
                        showToast(error.error || 'Failed to create user', 'error');
                    }
                } catch (error) {
                    console.error('Error creating user:', error);
                    showToast('Failed to create user', 'error');
                }
            });
        }
    }

    // Approve User
    document.querySelectorAll('.approve-user').forEach(btn => {
        btn.addEventListener('click', async () => {
            const userId = btn.dataset.userId;
            const username = btn.dataset.username;

            try {
                const response = await fetch(`/api/users/${userId}/approve`, {
                    method: 'POST'
                });

                if (response.ok) {
                    showToast(`User "${username}" approved`);
                    setTimeout(() => location.reload(), 1000);
                } else {
                    const error = await response.json();
                    showToast(error.error || 'Failed to approve user', 'error');
                }
            } catch (error) {
                console.error('Error approving user:', error);
                showToast('Failed to approve user', 'error');
            }
        });
    });

    // Reject/Revoke User
    document.querySelectorAll('.reject-user').forEach(btn => {
        btn.addEventListener('click', async () => {
            const userId = btn.dataset.userId;
            const username = btn.dataset.username;

            showConfirmation(
                `Are you sure you want to revoke approval for user "<strong>${username}</strong>"?<br>
                They will not be able to log in until re-approved.`,
                async () => {
                    try {
                        const response = await fetch(`/api/users/${userId}/reject`, {
                            method: 'POST'
                        });

                        if (response.ok) {
                            showToast(`User "${username}" approval revoked`);
                            setTimeout(() => location.reload(), 1000);
                        } else {
                            const error = await response.json();
                            showToast(error.error || 'Failed to revoke user', 'error');
                        }
                    } catch (error) {
                        console.error('Error revoking user:', error);
                        showToast('Failed to revoke user', 'error');
                    }
                }
            );
        });
    });

    // Toggle Admin
    document.querySelectorAll('.toggle-admin').forEach(btn => {
        btn.addEventListener('click', async () => {
            const userId = btn.dataset.userId;
            const username = btn.dataset.username;
            const isAdmin = btn.dataset.isAdmin === 'True';
            const action = isAdmin ? 'revoke admin privileges from' : 'grant admin privileges to';

            showConfirmation(
                `Are you sure you want to ${action} user "<strong>${username}</strong>"?`,
                async () => {
                    try {
                        const response = await fetch(`/api/users/${userId}/toggle-admin`, {
                            method: 'POST'
                        });

                        if (response.ok) {
                            showToast(`Admin status toggled for "${username}"`);
                            setTimeout(() => location.reload(), 1000);
                        } else {
                            const error = await response.json();
                            showToast(error.error || 'Failed to toggle admin', 'error');
                        }
                    } catch (error) {
                        console.error('Error toggling admin:', error);
                        showToast('Failed to toggle admin', 'error');
                    }
                }
            );
        });
    });

    // Delete User
    document.querySelectorAll('.delete-user').forEach(btn => {
        btn.addEventListener('click', async () => {
            const userId = btn.dataset.userId;
            const username = btn.dataset.username;

            showConfirmation(
                `Are you sure you want to delete user "<strong>${username}</strong>"?<br><br>
                <strong>Warning:</strong> This will also delete all permissions for this user.<br>
                This action cannot be undone.`,
                async () => {
                    try {
                        const response = await fetch(`/api/users/${userId}`, {
                            method: 'DELETE'
                        });

                        if (response.ok) {
                            showToast(`User "${username}" deleted`);
                            setTimeout(() => location.reload(), 1000);
                        } else {
                            const error = await response.json();
                            showToast(error.error || 'Failed to delete user', 'error');
                        }
                    } catch (error) {
                        console.error('Error deleting user:', error);
                        showToast('Failed to delete user', 'error');
                    }
                }
            );
        });
    });

    // ========== Permission Management ==========

    // Edit Permissions
    const editPermissionsModal = document.getElementById('editPermissionsModal');
    const permissionsForm = document.getElementById('permissionsForm');

    document.querySelectorAll('.edit-permissions').forEach(btn => {
        btn.addEventListener('click', async () => {
            const userId = btn.dataset.userId;
            const user = users.find(u => u.id == userId);

            if (!user) return;

            // Build permissions form
            permissionsForm.innerHTML = `
                <h4>Permissions for ${user.username}</h4>
                <div class="permissions-table">
                    ${cameras.map(camera => `
                        <div class="permission-row" style="background: var(--bg-tertiary); padding: 1rem; margin-bottom: 0.5rem; border-radius: 6px;">
                            <h5>${camera.name}</h5>
                            <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 0.5rem; margin-top: 0.5rem;">
                                <label>
                                    <input type="checkbox" class="perm-view" data-user="${userId}" data-camera="${camera.id}">
                                    Can View
                                </label>
                                <label>
                                    <input type="checkbox" class="perm-control" data-user="${userId}" data-camera="${camera.id}">
                                    Can Control
                                </label>
                                <label>
                                    <input type="checkbox" class="perm-alerts" data-user="${userId}" data-camera="${camera.id}">
                                    Receive Alerts
                                </label>
                            </div>
                            <div style="margin-top: 0.5rem;">
                                <label style="display: block; margin-bottom: 0.25rem; color: var(--text-secondary); font-size: 0.9rem;">Allowed Models:</label>
                                ${detectionModels.map(model => `
                                    <label style="display: inline-block; margin-right: 1rem;">
                                        <input type="checkbox" class="perm-model" data-user="${userId}" data-camera="${camera.id}" value="${model}">
                                        ${model}
                                    </label>
                                `).join('')}
                            </div>
                        </div>
                    `).join('')}
                </div>
                <button type="button" class="btn btn-primary" id="savePermissionsBtn" style="margin-top: 1rem;">Save Permissions</button>
            `;

            // Load existing permissions
            permissions.forEach(perm => {
                if (perm.user_id == userId) {
                    const viewCb = permissionsForm.querySelector(`.perm-view[data-user="${userId}"][data-camera="${perm.camera_id}"]`);
                    const controlCb = permissionsForm.querySelector(`.perm-control[data-user="${userId}"][data-camera="${perm.camera_id}"]`);
                    const alertsCb = permissionsForm.querySelector(`.perm-alerts[data-user="${userId}"][data-camera="${perm.camera_id}"]`);

                    if (viewCb) viewCb.checked = perm.can_view;
                    if (controlCb) controlCb.checked = perm.can_control;
                    if (alertsCb) alertsCb.checked = perm.receive_alerts;

                    // Check allowed models
                    perm.allowed_models.forEach(model => {
                        const modelCb = permissionsForm.querySelector(
                            `.perm-model[data-user="${userId}"][data-camera="${perm.camera_id}"][value="${model}"]`
                        );
                        if (modelCb) modelCb.checked = true;
                    });
                }
            });

            // Save button handler
            document.getElementById('savePermissionsBtn').addEventListener('click', async () => {
                const permissionsToSave = [];

                cameras.forEach(camera => {
                    const viewCb = permissionsForm.querySelector(`.perm-view[data-user="${userId}"][data-camera="${camera.id}"]`);
                    const controlCb = permissionsForm.querySelector(`.perm-control[data-user="${userId}"][data-camera="${camera.id}"]`);
                    const alertsCb = permissionsForm.querySelector(`.perm-alerts[data-user="${userId}"][data-camera="${camera.id}"]`);
                    const modelCbs = permissionsForm.querySelectorAll(`.perm-model[data-user="${userId}"][data-camera="${camera.id}"]`);

                    const allowedModels = Array.from(modelCbs)
                        .filter(cb => cb.checked)
                        .map(cb => cb.value);

                    if (viewCb && viewCb.checked) {
                        permissionsToSave.push({
                            user_id: parseInt(userId),
                            camera_id: camera.id,
                            can_view: true,
                            can_control: controlCb ? controlCb.checked : false,
                            receive_alerts: alertsCb ? alertsCb.checked : false,
                            allowed_models: allowedModels
                        });
                    }
                });

                // Save each permission
                try {
                    for (const perm of permissionsToSave) {
                        await fetch('/api/permissions', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify(perm)
                        });
                    }

                    showToast('Permissions saved successfully');
                    editPermissionsModal.classList.remove('active');
                    setTimeout(() => location.reload(), 1000);
                } catch (error) {
                    console.error('Error saving permissions:', error);
                    showToast('Failed to save permissions', 'error');
                }
            });

            editPermissionsModal.classList.add('active');
        });
    });

    // Close permissions modal
    if (editPermissionsModal) {
        const closeBtn = editPermissionsModal.querySelector('.close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                editPermissionsModal.classList.remove('active');
            });
        }

        editPermissionsModal.addEventListener('click', (e) => {
            if (e.target === editPermissionsModal) {
                editPermissionsModal.classList.remove('active');
            }
        });
    }

    // Revoke Permission
    document.querySelectorAll('.revoke-permission').forEach(btn => {
        btn.addEventListener('click', async () => {
            const permissionId = btn.dataset.permissionId;
            const username = btn.dataset.username;
            const cameraName = btn.dataset.cameraName;

            showConfirmation(
                `Are you sure you want to revoke permission for user "<strong>${username}</strong>" on camera "<strong>${cameraName}</strong>"?`,
                async () => {
                    try {
                        const response = await fetch(`/api/permissions/${permissionId}`, {
                            method: 'DELETE'
                        });

                        if (response.ok) {
                            showToast('Permission revoked successfully');
                            setTimeout(() => location.reload(), 1000);
                        } else {
                            const error = await response.json();
                            showToast(error.error || 'Failed to revoke permission', 'error');
                        }
                    } catch (error) {
                        console.error('Error revoking permission:', error);
                        showToast('Failed to revoke permission', 'error');
                    }
                }
            );
        });
    });

    // ========== Permission Requests Management ==========

    // Load pending permission requests
    async function loadPermissionRequests() {
        const listContainer = document.getElementById('permissionRequestsList');
        const pendingBadge = document.getElementById('pendingCount');

        if (!listContainer) return;

        try {
            const response = await fetch('/api/admin/permission-requests?status=pending');
            const requests = await response.json();

            // Update pending count badge
            if (pendingBadge) {
                if (requests.length > 0) {
                    pendingBadge.textContent = requests.length;
                    pendingBadge.style.display = 'inline';
                } else {
                    pendingBadge.style.display = 'none';
                }
            }

            if (requests.length === 0) {
                listContainer.innerHTML = '<div class="no-data">No pending permission requests</div>';
                return;
            }

            listContainer.innerHTML = requests.map(req => `
                <div class="request-item" data-request-id="${req.id}">
                    <div class="request-item-header">
                        <div>
                            <strong>${req.username}</strong> requests access to <strong>${req.camera_name}</strong>
                        </div>
                        <span class="request-status pending">Pending</span>
                    </div>
                    <div style="font-size: 0.85rem; color: var(--text-secondary); margin-bottom: 0.5rem;">
                        Type: ${req.request_type} | 
                        Requested: ${new Date(req.created_at).toLocaleString()}
                    </div>
                    <div style="font-size: 0.9rem; margin-bottom: 0.75rem;">
                        <strong>Reason:</strong> ${req.reason || 'No reason provided'}
                    </div>
                    <div style="font-size: 0.85rem; margin-bottom: 0.75rem; background: var(--bg-tertiary); padding: 0.5rem; border-radius: 4px;">
                        <strong>Requested permissions:</strong><br>
                        View: ${req.requested_value.can_view ? '✓' : '✗'} | 
                        Control: ${req.requested_value.can_control ? '✓' : '✗'} | 
                        Alerts: ${req.requested_value.receive_alerts ? '✓' : '✗'}
                    </div>
                    <div style="display: flex; gap: 0.5rem;">
                        <button class="btn btn-sm btn-success approve-request" data-request-id="${req.id}" data-username="${req.username}">
                            Approve
                        </button>
                        <button class="btn btn-sm btn-danger reject-request" data-request-id="${req.id}" data-username="${req.username}">
                            Reject
                        </button>
                    </div>
                </div>
            `).join('');

            // Attach event handlers
            attachRequestHandlers();

        } catch (error) {
            console.error('Error loading permission requests:', error);
            listContainer.innerHTML = '<div class="no-data">Failed to load permission requests</div>';
        }
    }

    function attachRequestHandlers() {
        // Approve request
        document.querySelectorAll('.approve-request').forEach(btn => {
            btn.addEventListener('click', async () => {
                const requestId = btn.dataset.requestId;
                const username = btn.dataset.username;

                const response = prompt(`Approve permission request for "${username}"?\n\nOptional response to user:`);

                if (response === null) return; // Cancelled

                try {
                    const res = await fetch(`/api/admin/permission-requests/${requestId}/approve`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ response: response })
                    });

                    if (res.ok) {
                        showToast(`Permission request approved for ${username}`);
                        loadPermissionRequests();
                    } else {
                        const error = await res.json();
                        showToast(error.error || 'Failed to approve request', 'error');
                    }
                } catch (error) {
                    console.error('Error approving request:', error);
                    showToast('Failed to approve request', 'error');
                }
            });
        });

        // Reject request
        document.querySelectorAll('.reject-request').forEach(btn => {
            btn.addEventListener('click', async () => {
                const requestId = btn.dataset.requestId;
                const username = btn.dataset.username;

                const response = prompt(`Reject permission request for "${username}"?\n\nReason for rejection (recommended):`);

                if (response === null) return; // Cancelled

                try {
                    const res = await fetch(`/api/admin/permission-requests/${requestId}/reject`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ response: response })
                    });

                    if (res.ok) {
                        showToast(`Permission request rejected for ${username}`);
                        loadPermissionRequests();
                    } else {
                        const error = await res.json();
                        showToast(error.error || 'Failed to reject request', 'error');
                    }
                } catch (error) {
                    console.error('Error rejecting request:', error);
                    showToast('Failed to reject request', 'error');
                }
            });
        });
    }

    // Load permission requests on page load
    loadPermissionRequests();
});
