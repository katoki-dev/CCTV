// CASS - Enhanced Zone Manager
// Rectangle-based zone drawing with snapshot capture - IMPROVED UX

class ZoneManager {
    constructor(videoElement, cameraId) {
        this.video = videoElement;
        this.cameraId = cameraId;
        this.canvas = null;
        this.ctx = null;
        this.zones = [];
        this.isDrawing = false;

        // Rectangle drawing state
        this.rectStart = null;
        this.rectEnd = null;
        this.isDragging = false;

        // Snapshot modal elements
        this.modal = null;
        this.snapshotCanvas = null;
        this.snapshotCtx = null;

        this.init();
        this.loadZones();
    }

    init() {
        // Create canvas overlay for live view
        this.canvas = document.createElement('canvas');
        this.canvas.className = 'zone-canvas';
        this.canvas.style.cssText = `
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            z-index: 10;
        `;

        this.video.parentElement.style.position = 'relative';
        this.video.parentElement.appendChild(this.canvas);

        this.ctx = this.canvas.getContext('2d');

        // Match video dimensions
        this.updateCanvasSize();
        window.addEventListener('resize', () => this.updateCanvasSize());

        // Create zone editor modal
        this.createZoneEditorModal();

        // Initial render
        this.render();
    }

    createZoneEditorModal() {
        // Create modal HTML with better fixed layout
        const modalHTML = `
            <div id="zoneEditorModal" class="zone-modal-overlay">
                <div class="zone-modal-container">
                    <div class="zone-modal-header">
                        <h3>📍 Add Restricted Zone</h3>
                        <button class="zone-modal-close" id="closeZoneEditor">✕</button>
                    </div>
                    
                    <div class="zone-modal-body">
                        <div class="zone-instructions">
                            <div class="instruction-main">
                                <span class="instruction-icon">🖱️</span>
                                <span>Click and drag on the image to draw a rectangle zone</span>
                            </div>
                            <div class="instruction-note">
                                💡 Only actual person detections will trigger alerts — lighting changes are ignored
                            </div>
                        </div>
                        
                        <div class="zone-canvas-wrapper">
                            <canvas id="snapshotCanvas"></canvas>
                            <div class="canvas-loading" id="canvasLoading">
                                <div class="loading-spinner"></div>
                                <span>Loading camera snapshot...</span>
                            </div>
                        </div>
                    </div>
                    
                    <div class="zone-modal-footer">
                        <div class="zone-name-input">
                            <label>Zone Name:</label>
                            <input type="text" id="zoneNameInput" placeholder="e.g., Server Room" value="Restricted Zone">
                        </div>
                        <div class="zone-action-buttons">
                            <button id="clearZoneBtn" class="zone-btn zone-btn-secondary">Clear</button>
                            <button id="cancelZoneModalBtn" class="zone-btn zone-btn-danger">Cancel</button>
                            <button id="saveZoneBtn" class="zone-btn zone-btn-success" disabled>Save Zone</button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Add modal to DOM
        document.body.insertAdjacentHTML('beforeend', modalHTML);
        this.modal = document.getElementById('zoneEditorModal');

        // Add modal styles
        this.addModalStyles();

        // Setup modal event listeners
        this.setupModalListeners();
    }

    addModalStyles() {
        const styleId = 'zone-editor-styles-v2';
        if (document.getElementById(styleId)) return;

        const styles = document.createElement('style');
        styles.id = styleId;
        styles.textContent = `
            .zone-modal-overlay {
                display: none;
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(0, 0, 0, 0.85);
                z-index: 9999;
                justify-content: center;
                align-items: center;
                padding: 20px;
            }
            
            .zone-modal-container {
                background: linear-gradient(145deg, #1e1e2e, #252538);
                border-radius: 16px;
                width: 100%;
                max-width: 800px;
                max-height: 90vh;
                display: flex;
                flex-direction: column;
                box-shadow: 0 25px 50px rgba(0,0,0,0.5);
                border: 1px solid rgba(255,255,255,0.1);
            }
            
            .zone-modal-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 16px 20px;
                border-bottom: 1px solid rgba(255,255,255,0.1);
                flex-shrink: 0;
            }
            
            .zone-modal-header h3 {
                margin: 0;
                color: #fff;
                font-size: 18px;
            }
            
            .zone-modal-close {
                background: rgba(255,255,255,0.1);
                border: none;
                color: #fff;
                width: 32px;
                height: 32px;
                border-radius: 8px;
                cursor: pointer;
                font-size: 16px;
                transition: all 0.2s;
            }
            
            .zone-modal-close:hover {
                background: #ff4757;
            }
            
            .zone-modal-body {
                flex: 1;
                overflow: hidden;
                padding: 16px 20px;
                display: flex;
                flex-direction: column;
                gap: 12px;
            }
            
            .zone-instructions {
                flex-shrink: 0;
            }
            
            .instruction-main {
                display: flex;
                align-items: center;
                gap: 10px;
                color: #fff;
                font-size: 15px;
                padding: 10px 14px;
                background: rgba(59, 130, 246, 0.2);
                border-radius: 8px;
                border: 1px solid rgba(59, 130, 246, 0.3);
            }
            
            .instruction-icon {
                font-size: 20px;
            }
            
            .instruction-note {
                margin-top: 8px;
                color: #888;
                font-size: 13px;
                padding-left: 5px;
            }
            
            .zone-canvas-wrapper {
                position: relative;
                flex: 1;
                min-height: 300px;
                background: #000;
                border-radius: 10px;
                overflow: hidden;
                display: flex;
                justify-content: center;
                align-items: center;
            }
            
            #snapshotCanvas {
                max-width: 100%;
                max-height: 100%;
                cursor: crosshair;
                display: block;
            }
            
            .canvas-loading {
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                gap: 12px;
                color: #888;
                background: rgba(0,0,0,0.8);
            }
            
            .canvas-loading.hidden {
                display: none;
            }
            
            .loading-spinner {
                width: 40px;
                height: 40px;
                border: 3px solid rgba(255,255,255,0.1);
                border-top-color: #3b82f6;
                border-radius: 50%;
                animation: spin 0.8s linear infinite;
            }
            
            @keyframes spin {
                to { transform: rotate(360deg); }
            }
            
            .zone-modal-footer {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 16px 20px;
                border-top: 1px solid rgba(255,255,255,0.1);
                flex-shrink: 0;
                gap: 20px;
                flex-wrap: wrap;
            }
            
            .zone-name-input {
                display: flex;
                align-items: center;
                gap: 10px;
                flex: 1;
                min-width: 200px;
            }
            
            .zone-name-input label {
                color: #aaa;
                font-size: 14px;
                white-space: nowrap;
            }
            
            .zone-name-input input {
                flex: 1;
                padding: 10px 14px;
                border: 1px solid rgba(255,255,255,0.2);
                border-radius: 8px;
                background: rgba(255,255,255,0.05);
                color: #fff;
                font-size: 14px;
                outline: none;
                transition: all 0.2s;
            }
            
            .zone-name-input input:focus {
                border-color: #3b82f6;
                background: rgba(59, 130, 246, 0.1);
            }
            
            .zone-action-buttons {
                display: flex;
                gap: 10px;
            }
            
            .zone-btn {
                padding: 10px 20px;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.2s;
            }
            
            .zone-btn:disabled {
                opacity: 0.5;
                cursor: not-allowed;
            }
            
            .zone-btn-secondary {
                background: rgba(255,255,255,0.1);
                color: #fff;
            }
            
            .zone-btn-secondary:hover:not(:disabled) {
                background: rgba(255,255,255,0.2);
            }
            
            .zone-btn-danger {
                background: rgba(239, 68, 68, 0.2);
                color: #ef4444;
            }
            
            .zone-btn-danger:hover:not(:disabled) {
                background: #ef4444;
                color: #fff;
            }
            
            .zone-btn-success {
                background: #10b981;
                color: #fff;
            }
            
            .zone-btn-success:hover:not(:disabled) {
                background: #059669;
            }
            
            /* Zone list styling improvements */
            .zone-item {
                background: rgba(255,255,255,0.05);
                border-radius: 8px;
                padding: 12px;
                margin-bottom: 10px;
                border: 1px solid rgba(255,255,255,0.1);
                transition: all 0.2s;
            }
            
            .zone-item:hover {
                background: rgba(255,255,255,0.08);
            }
            
            .zone-item.disabled {
                opacity: 0.6;
            }
            
            .zone-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 8px;
            }
            
            .zone-name {
                font-weight: 600;
                color: #fff;
            }
            
            .zone-status {
                font-size: 12px;
                padding: 3px 8px;
                border-radius: 4px;
            }
            
            .zone-status.status-active {
                background: rgba(16, 185, 129, 0.2);
                color: #10b981;
            }
            
            .zone-status.status-inactive {
                background: rgba(239, 68, 68, 0.2);
                color: #ef4444;
            }
            
            .zone-actions {
                display: flex;
                gap: 8px;
            }
            
            .zone-actions .btn-small {
                padding: 6px 12px;
                font-size: 12px;
                border-radius: 6px;
                border: none;
                cursor: pointer;
                transition: all 0.2s;
                background: rgba(255,255,255,0.1);
                color: #fff;
            }
            
            .zone-actions .btn-small:hover {
                background: rgba(255,255,255,0.2);
            }
            
            .zone-actions .btn-small.btn-danger {
                background: rgba(239, 68, 68, 0.2);
                color: #ef4444;
            }
            
            .zone-actions .btn-small.btn-danger:hover {
                background: #ef4444;
                color: #fff;
            }
        `;
        document.head.appendChild(styles);
    }

    setupModalListeners() {
        const closeBtn = document.getElementById('closeZoneEditor');
        const saveBtn = document.getElementById('saveZoneBtn');
        const clearBtn = document.getElementById('clearZoneBtn');
        const cancelBtn = document.getElementById('cancelZoneModalBtn');

        closeBtn.addEventListener('click', () => this.closeModal());
        cancelBtn.addEventListener('click', () => this.closeModal());
        saveBtn.addEventListener('click', () => this.saveZoneFromModal());
        clearBtn.addEventListener('click', () => this.clearRectangle());

        // Close on outside click
        this.modal.addEventListener('click', (e) => {
            if (e.target === this.modal) this.closeModal();
        });

        // ESC key to close
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.modal.style.display === 'flex') {
                this.closeModal();
            }
        });
    }

    updateCanvasSize() {
        const rect = this.video.getBoundingClientRect();
        this.canvas.width = rect.width;
        this.canvas.height = rect.height;
        this.render();
    }

    async loadZones() {
        try {
            const response = await fetch(`/api/zones/${this.cameraId}`);
            const data = await response.json();

            if (data.success) {
                this.zones = data.zones;
                this.render();
                this.updateZoneList();
            }
        } catch (error) {
            console.error('Failed to load zones:', error);
        }
    }

    // Start rectangle drawing mode with snapshot
    startDrawing() {
        this.openModal();
        this.captureSnapshot();
    }

    async captureSnapshot() {
        const loadingEl = document.getElementById('canvasLoading');
        if (loadingEl) loadingEl.classList.remove('hidden');

        try {
            // Try server-side snapshot first
            const response = await fetch(`/api/snapshot/${this.cameraId}`);
            const data = await response.json();

            if (data.success && data.image) {
                // Load the base64 image
                const img = new Image();
                img.onload = () => {
                    this.displaySnapshot(img, data.width, data.height);
                    if (loadingEl) loadingEl.classList.add('hidden');
                };
                img.onerror = () => {
                    // Fallback to video element capture
                    this.captureFromVideo();
                    if (loadingEl) loadingEl.classList.add('hidden');
                };
                img.src = data.image;
            } else {
                // Fallback to video element capture
                this.captureFromVideo();
                if (loadingEl) loadingEl.classList.add('hidden');
            }
        } catch (error) {
            console.error('Snapshot API failed:', error);
            this.captureFromVideo();
            if (loadingEl) loadingEl.classList.add('hidden');
        }
    }

    captureFromVideo() {
        // Create a temporary canvas to capture from video element
        const tempCanvas = document.createElement('canvas');
        const tempCtx = tempCanvas.getContext('2d');

        tempCanvas.width = this.video.naturalWidth || this.video.width || 640;
        tempCanvas.height = this.video.naturalHeight || this.video.height || 480;

        tempCtx.drawImage(this.video, 0, 0, tempCanvas.width, tempCanvas.height);

        const img = new Image();
        img.onload = () => {
            this.displaySnapshot(img, tempCanvas.width, tempCanvas.height);
        };
        img.src = tempCanvas.toDataURL('image/jpeg');
    }

    displaySnapshot(img, width, height) {
        this.snapshotCanvas = document.getElementById('snapshotCanvas');
        this.snapshotCtx = this.snapshotCanvas.getContext('2d');

        // Calculate display size (fit within container)
        const container = this.snapshotCanvas.parentElement;
        const containerWidth = container.clientWidth - 20;
        const containerHeight = container.clientHeight - 20;

        const aspectRatio = height / width;
        let displayWidth = Math.min(width, containerWidth);
        let displayHeight = displayWidth * aspectRatio;

        if (displayHeight > containerHeight) {
            displayHeight = containerHeight;
            displayWidth = displayHeight / aspectRatio;
        }

        this.snapshotCanvas.width = displayWidth;
        this.snapshotCanvas.height = displayHeight;

        // Draw the snapshot
        this.snapshotCtx.drawImage(img, 0, 0, displayWidth, displayHeight);

        // Store original for redrawing
        this.originalSnapshot = img;
        this.snapshotWidth = width;
        this.snapshotHeight = height;

        // Draw existing zones
        this.drawExistingZonesOnSnapshot();

        // Setup drawing listeners
        this.setupDrawingListeners();
    }

    openModal() {
        this.modal.style.display = 'flex';

        // Reset state
        this.rectStart = null;
        this.rectEnd = null;
        this.isDragging = false;

        const saveBtn = document.getElementById('saveZoneBtn');
        if (saveBtn) saveBtn.disabled = true;

        const loadingEl = document.getElementById('canvasLoading');
        if (loadingEl) loadingEl.classList.remove('hidden');
    }

    setupDrawingListeners() {
        if (!this.snapshotCanvas) return;

        // Remove old listeners
        this.snapshotCanvas.onmousedown = null;
        this.snapshotCanvas.onmousemove = null;
        this.snapshotCanvas.onmouseup = null;
        this.snapshotCanvas.onmouseleave = null;

        // Add new listeners
        this.snapshotCanvas.onmousedown = (e) => this.handleMouseDown(e);
        this.snapshotCanvas.onmousemove = (e) => this.handleMouseMove(e);
        this.snapshotCanvas.onmouseup = (e) => this.handleMouseUp(e);
        this.snapshotCanvas.onmouseleave = (e) => {
            if (this.isDragging) this.handleMouseUp(e);
        };
    }

    handleMouseDown(e) {
        const rect = this.snapshotCanvas.getBoundingClientRect();
        this.rectStart = {
            x: e.clientX - rect.left,
            y: e.clientY - rect.top
        };
        this.rectEnd = null;
        this.isDragging = true;
    }

    handleMouseMove(e) {
        if (!this.isDragging || !this.rectStart) return;

        const rect = this.snapshotCanvas.getBoundingClientRect();
        this.rectEnd = {
            x: Math.max(0, Math.min(e.clientX - rect.left, this.snapshotCanvas.width)),
            y: Math.max(0, Math.min(e.clientY - rect.top, this.snapshotCanvas.height))
        };

        this.renderSnapshotWithRect();
    }

    handleMouseUp(e) {
        if (!this.isDragging) return;
        this.isDragging = false;

        if (this.rectStart && this.rectEnd) {
            const width = Math.abs(this.rectEnd.x - this.rectStart.x);
            const height = Math.abs(this.rectEnd.y - this.rectStart.y);

            if (width > 30 && height > 30) {
                document.getElementById('saveZoneBtn').disabled = false;
            } else {
                showNotification('Draw a larger rectangle', 'warning');
                this.clearRectangle();
            }
        }
    }

    drawExistingZonesOnSnapshot() {
        if (!this.snapshotCanvas || !this.snapshotCtx) return;

        this.zones.forEach(zone => {
            const coords = zone.coordinates.map(([x, y]) => [
                x * this.snapshotCanvas.width,
                y * this.snapshotCanvas.height
            ]);

            const color = zone.enabled ? 'rgba(255, 165, 0, 0.3)' : 'rgba(128, 128, 128, 0.3)';
            const strokeColor = zone.enabled ? '#ffa500' : '#888';

            this.snapshotCtx.beginPath();
            this.snapshotCtx.moveTo(coords[0][0], coords[0][1]);
            for (let i = 1; i < coords.length; i++) {
                this.snapshotCtx.lineTo(coords[i][0], coords[i][1]);
            }
            this.snapshotCtx.closePath();

            this.snapshotCtx.fillStyle = color;
            this.snapshotCtx.fill();
            this.snapshotCtx.strokeStyle = strokeColor;
            this.snapshotCtx.lineWidth = 2;
            this.snapshotCtx.stroke();

            // Zone label
            const centerX = coords.reduce((sum, [x]) => sum + x, 0) / coords.length;
            const centerY = coords.reduce((sum, [, y]) => sum + y, 0) / coords.length;

            this.snapshotCtx.fillStyle = 'white';
            this.snapshotCtx.strokeStyle = 'black';
            this.snapshotCtx.lineWidth = 3;
            this.snapshotCtx.font = 'bold 12px Arial';
            this.snapshotCtx.strokeText(zone.name, centerX - 20, centerY);
            this.snapshotCtx.fillText(zone.name, centerX - 20, centerY);
        });
    }

    renderSnapshotWithRect() {
        if (!this.snapshotCanvas || !this.originalSnapshot) return;

        // Redraw snapshot
        this.snapshotCtx.drawImage(
            this.originalSnapshot,
            0, 0,
            this.snapshotCanvas.width,
            this.snapshotCanvas.height
        );

        // Draw existing zones
        this.drawExistingZonesOnSnapshot();

        // Draw current rectangle being created
        if (this.rectStart && this.rectEnd) {
            const x = Math.min(this.rectStart.x, this.rectEnd.x);
            const y = Math.min(this.rectStart.y, this.rectEnd.y);
            const width = Math.abs(this.rectEnd.x - this.rectStart.x);
            const height = Math.abs(this.rectEnd.y - this.rectStart.y);

            // Animated dashed border
            this.snapshotCtx.setLineDash([8, 4]);
            this.snapshotCtx.lineDashOffset = -performance.now() / 50;

            // Semi-transparent fill
            this.snapshotCtx.fillStyle = 'rgba(255, 50, 50, 0.25)';
            this.snapshotCtx.fillRect(x, y, width, height);

            // Red border
            this.snapshotCtx.strokeStyle = '#ff3333';
            this.snapshotCtx.lineWidth = 3;
            this.snapshotCtx.strokeRect(x, y, width, height);

            this.snapshotCtx.setLineDash([]);

            // Corner handles
            const handleSize = 10;
            this.snapshotCtx.fillStyle = '#fff';
            this.snapshotCtx.strokeStyle = '#ff3333';
            this.snapshotCtx.lineWidth = 2;

            [[x, y], [x + width, y], [x, y + height], [x + width, y + height]].forEach(([hx, hy]) => {
                this.snapshotCtx.fillRect(hx - handleSize / 2, hy - handleSize / 2, handleSize, handleSize);
                this.snapshotCtx.strokeRect(hx - handleSize / 2, hy - handleSize / 2, handleSize, handleSize);
            });

            // Dimension label
            const dimText = `${Math.round(width)} × ${Math.round(height)}`;
            this.snapshotCtx.fillStyle = 'rgba(0,0,0,0.7)';
            this.snapshotCtx.fillRect(x + width / 2 - 35, y + height / 2 - 10, 70, 20);
            this.snapshotCtx.fillStyle = '#fff';
            this.snapshotCtx.font = '12px Arial';
            this.snapshotCtx.textAlign = 'center';
            this.snapshotCtx.fillText(dimText, x + width / 2, y + height / 2 + 4);
            this.snapshotCtx.textAlign = 'left';
        }
    }

    clearRectangle() {
        this.rectStart = null;
        this.rectEnd = null;
        document.getElementById('saveZoneBtn').disabled = true;

        if (this.snapshotCanvas && this.originalSnapshot) {
            this.snapshotCtx.drawImage(
                this.originalSnapshot,
                0, 0,
                this.snapshotCanvas.width,
                this.snapshotCanvas.height
            );
            this.drawExistingZonesOnSnapshot();
        }
    }

    async saveZoneFromModal() {
        if (!this.rectStart || !this.rectEnd) {
            showNotification('Please draw a rectangle first', 'warning');
            return;
        }

        const zoneName = document.getElementById('zoneNameInput').value.trim() || 'Restricted Zone';

        // Convert to normalized coordinates
        const x1 = Math.min(this.rectStart.x, this.rectEnd.x) / this.snapshotCanvas.width;
        const y1 = Math.min(this.rectStart.y, this.rectEnd.y) / this.snapshotCanvas.height;
        const x2 = Math.max(this.rectStart.x, this.rectEnd.x) / this.snapshotCanvas.width;
        const y2 = Math.max(this.rectStart.y, this.rectEnd.y) / this.snapshotCanvas.height;

        const coordinates = [
            [x1, y1], [x2, y1], [x2, y2], [x1, y2]
        ];

        try {
            const response = await fetch(`/api/zones/${this.cameraId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    name: zoneName,
                    coordinates: coordinates,
                    enabled: true
                })
            });

            const data = await response.json();

            if (data.success) {
                this.zones.push(data.zone);
                showNotification(`Zone "${zoneName}" created!`, 'success');
                this.closeModal();
                this.render();
                this.updateZoneList();
            } else {
                showNotification('Failed: ' + data.error, 'error');
            }
        } catch (error) {
            console.error('Failed to save zone:', error);
            showNotification('Failed to save zone', 'error');
        }
    }

    closeModal() {
        this.modal.style.display = 'none';
        this.rectStart = null;
        this.rectEnd = null;
        this.isDragging = false;

        // Reset buttons
        const drawZoneBtn = document.getElementById('drawZoneBtn');
        const cancelZoneBtn = document.getElementById('cancelZoneBtn');
        if (drawZoneBtn) drawZoneBtn.style.display = 'block';
        if (cancelZoneBtn) cancelZoneBtn.style.display = 'none';
    }

    cancelDrawing() {
        this.closeModal();
    }

    async deleteZone(zoneId) {
        if (!confirm('Delete this zone?')) return;

        try {
            const response = await fetch(`/api/zones/${zoneId}`, { method: 'DELETE' });
            const data = await response.json();

            if (data.success) {
                this.zones = this.zones.filter(z => z.id !== zoneId);
                showNotification('Zone deleted', 'success');
                this.render();
                this.updateZoneList();
            } else {
                console.error('Delete failed:', data);
                showNotification(data.error || 'Failed to delete zone', 'error');
            }
        } catch (error) {
            console.error('Failed to delete zone:', error);
            showNotification('Failed to delete zone: ' + error.message, 'error');
        }
    }

    async toggleZone(zoneId) {
        const zone = this.zones.find(z => z.id === zoneId);
        if (!zone) return;

        try {
            const response = await fetch(`/api/zones/${zoneId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ enabled: !zone.enabled })
            });

            const data = await response.json();

            if (data.success) {
                zone.enabled = !zone.enabled;
                this.render();
                this.updateZoneList();
                showNotification(`Zone ${zone.enabled ? 'enabled' : 'disabled'}`, 'success');
            }
        } catch (error) {
            console.error('Failed to toggle zone:', error);
        }
    }

    render() {
        const rect = this.canvas.getBoundingClientRect();
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

        this.zones.forEach(zone => {
            const coords = zone.coordinates.map(([x, y]) => [
                x * rect.width,
                y * rect.height
            ]);

            const color = zone.enabled ? 'rgba(255, 0, 0, 0.2)' : 'rgba(128, 128, 128, 0.15)';
            const strokeColor = zone.enabled ? '#ff0000' : '#888';

            this.drawPolygon(coords, color, strokeColor);

            if (coords.length > 0) {
                const centerX = coords.reduce((sum, [x]) => sum + x, 0) / coords.length;
                const centerY = coords.reduce((sum, [, y]) => sum + y, 0) / coords.length;

                this.ctx.fillStyle = 'white';
                this.ctx.strokeStyle = 'black';
                this.ctx.lineWidth = 3;
                this.ctx.font = 'bold 14px Arial';
                this.ctx.textAlign = 'center';
                this.ctx.strokeText(zone.name, centerX, centerY);
                this.ctx.fillText(zone.name, centerX, centerY);
                this.ctx.textAlign = 'left';
            }
        });
    }

    drawPolygon(points, fillColor, strokeColor) {
        if (points.length === 0) return;

        this.ctx.beginPath();
        this.ctx.moveTo(points[0][0], points[0][1]);
        for (let i = 1; i < points.length; i++) {
            this.ctx.lineTo(points[i][0], points[i][1]);
        }
        this.ctx.closePath();

        this.ctx.fillStyle = fillColor;
        this.ctx.fill();
        this.ctx.strokeStyle = strokeColor;
        this.ctx.lineWidth = 2;
        this.ctx.stroke();
    }

    updateZoneList() {
        const zoneList = document.getElementById('zoneList');
        if (!zoneList) return;

        if (this.zones.length === 0) {
            zoneList.innerHTML = '<p class="no-data">No zones yet. Click "Draw New Zone" to add one.</p>';
            return;
        }

        zoneList.innerHTML = this.zones.map(zone => `
            <div class="zone-item ${zone.enabled ? '' : 'disabled'}">
                <div class="zone-header">
                    <span class="zone-name">${zone.name}</span>
                    <span class="zone-status ${zone.enabled ? 'status-active' : 'status-inactive'}">
                        ${zone.enabled ? '✓ Active' : '○ Off'}
                    </span>
                </div>
                <div class="zone-actions">
                    <button class="btn-small" onclick="zoneManager.toggleZone(${zone.id})">
                        ${zone.enabled ? 'Disable' : 'Enable'}
                    </button>
                    <button class="btn-small btn-danger" onclick="zoneManager.deleteZone(${zone.id})">
                        Delete
                    </button>
                </div>
            </div>
        `).join('');
    }
}

// Global instance
let zoneManager = null;
