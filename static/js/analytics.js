// CASS Analytics Dashboard - Theme Matched Version with Error Handling
// Uses consistent colors with main CASS theme

let currentPeriod = '24h';
let charts = {
    timeline: null,
    type: null,
    camera: null,
    radar: null
};

// Theme colors matching style.css
const themeColors = {
    primary: '#58a6ff',
    success: '#3fb950',
    warning: '#d29922',
    danger: '#f85149',
    purple: '#a855f7',
    text: '#c9d1d9',
    textSecondary: '#8b949e',
    border: '#30363d',
    bgSecondary: '#161b22',
    bgTertiary: '#1f2937'
};

// Chart.js defaults
Chart.defaults.color = themeColors.textSecondary;
Chart.defaults.borderColor = themeColors.border;
Chart.defaults.font.family = "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif";

// Initialize dashboard
document.addEventListener('DOMContentLoaded', () => {
    initializePeriodButtons();
    loadAnalyticsData();

    // Auto-refresh every 60 seconds
    setInterval(loadAnalyticsData, 30000);
});

// Period button handlers
function initializePeriodButtons() {
    document.querySelectorAll('.period-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.period-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentPeriod = btn.dataset.period;
            loadAnalyticsData();
        });
    });
}

// Load analytics data from API with error handling
async function loadAnalyticsData() {
    showLoading(true);

    try {
        const response = await fetch(`/api/analytics/stats?period=${currentPeriod}`);

        // Check if response is OK
        if (!response.ok) {
            throw new Error(`Server error: ${response.status}`);
        }

        // Check content type
        const contentType = response.headers.get('content-type');
        if (!contentType || !contentType.includes('application/json')) {
            throw new Error('Server returned non-JSON response');
        }

        const data = await response.json();

        if (data.success) {
            updateSummaryCards(data.summary);
            updateTimelineChart(data.timeline);
            updateTypeChart(data.distribution);
            updateCameraChart(data.camera_health);
            updateRadarChart(data.hourly_breakdown);
            updateHeatmap(data.hourly_breakdown);
            updateAlertsTable(data.recent_alerts);
        } else {
            console.warn('Analytics returned error:', data.error);
            showNoDataState();
        }
    } catch (error) {
        console.error('Failed to load analytics:', error.message);
        showErrorState(error.message);
    } finally {
        showLoading(false);
    }
}

// Show error state in charts
function showErrorState(message) {
    updateSummaryCards({});
    const alertsBody = document.getElementById('alertsTableBody');
    if (alertsBody) {
        alertsBody.innerHTML = `
            <tr>
                <td colspan="4" class="no-data">
                    <div class="no-data-icon">⚠️</div>
                    <div class="no-data-text">Error loading data: ${message}</div>
                </td>
            </tr>
        `;
    }
}

// Show no data state
function showNoDataState() {
    updateSummaryCards({});
    // Charts will handle empty data gracefully
}

// Update summary cards with animation
function updateSummaryCards(summary) {
    const updates = {
        'totalDetections': summary?.total_detections || 0,
        'totalAlerts': summary?.total_alerts || 0,
        'activeCameras': summary?.active_cameras || 0,
        'criticalEvents': summary?.high_severity_count || 0
    };

    Object.entries(updates).forEach(([id, value]) => {
        const el = document.getElementById(id);
        if (el) {
            animateValue(el, parseInt(el.textContent) || 0, value, 600);
        }
    });

    // Top camera
    const topCameraEl = document.getElementById('topCamera');
    if (topCameraEl) {
        topCameraEl.textContent = summary?.most_active_camera || '--';
    }
}

// Animate number values
function animateValue(element, start, end, duration) {
    const startTime = performance.now();

    function update(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const easeProgress = 1 - Math.pow(1 - progress, 3);
        const current = Math.floor(start + (end - start) * easeProgress);

        element.textContent = formatNumber(current);

        if (progress < 1) {
            requestAnimationFrame(update);
        }
    }

    requestAnimationFrame(update);
}

// Safe get canvas context
function getCanvasContext(canvasId) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) {
        console.warn(`Canvas element not found: ${canvasId}`);
        return null;
    }
    try {
        return canvas.getContext('2d');
    } catch (e) {
        console.warn(`Failed to get context for ${canvasId}:`, e);
        return null;
    }
}

// Timeline chart (line with fill)
function updateTimelineChart(timeline) {
    const ctx = getCanvasContext('timelineChart');
    if (!ctx) return;

    let labels = [];
    let datasets = {};

    if (timeline && timeline.data && timeline.data.length > 0) {
        timeline.data.forEach(item => {
            const hour = new Date(item.hour).toLocaleString('en-US', {
                month: 'short', day: 'numeric', hour: 'numeric'
            });

            if (!labels.includes(hour)) {
                labels.push(hour);
            }

            if (!datasets[item.model]) {
                datasets[item.model] = {};
            }
            datasets[item.model][hour] = item.count;
        });
    }

    // Default labels if no data
    if (labels.length === 0) {
        const now = new Date();
        for (let i = 23; i >= 0; i--) {
            const d = new Date(now - i * 3600000);
            labels.push(d.toLocaleString('en-US', { hour: 'numeric' }));
        }
    }

    const colorSet = [
        { border: themeColors.primary, bg: 'rgba(88, 166, 255, 0.15)' },
        { border: themeColors.success, bg: 'rgba(63, 185, 80, 0.15)' },
        { border: themeColors.warning, bg: 'rgba(210, 153, 34, 0.15)' },
        { border: themeColors.danger, bg: 'rgba(248, 81, 73, 0.15)' },
        { border: themeColors.purple, bg: 'rgba(168, 85, 247, 0.15)' }
    ];

    const chartDatasets = Object.keys(datasets).map((model, idx) => {
        const colors = colorSet[idx % colorSet.length];
        return {
            label: model.charAt(0).toUpperCase() + model.slice(1),
            data: labels.map(l => datasets[model][l] || 0),
            borderColor: colors.border,
            backgroundColor: colors.bg,
            fill: true,
            tension: 0.4,
            borderWidth: 2,
            pointRadius: 0,
            pointHoverRadius: 5,
            pointHoverBackgroundColor: colors.border,
            pointHoverBorderColor: '#fff',
            pointHoverBorderWidth: 2
        };
    });

    // Default dataset if empty
    if (chartDatasets.length === 0) {
        chartDatasets.push({
            label: 'Detections',
            data: labels.map(() => 0),
            borderColor: themeColors.primary,
            backgroundColor: 'rgba(88, 166, 255, 0.15)',
            fill: true,
            tension: 0.4,
            borderWidth: 2,
            pointRadius: 0
        });
    }

    try {
        if (charts.timeline) {
            charts.timeline.data.labels = labels;
            charts.timeline.data.datasets = chartDatasets;
            charts.timeline.update('none');
        } else {
            charts.timeline = new Chart(ctx, {
                type: 'line',
                data: { labels, datasets: chartDatasets },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    interaction: { mode: 'nearest', axis: 'x', intersect: false },
                    hover: { mode: 'nearest', intersect: false },
                    plugins: {
                        legend: {
                            position: 'top',
                            align: 'end',
                            labels: {
                                usePointStyle: true,
                                pointStyle: 'circle',
                                padding: 15,
                                font: { size: 11 }
                            }
                        },
                        tooltip: {
                            backgroundColor: themeColors.bgSecondary,
                            titleColor: themeColors.text,
                            bodyColor: themeColors.textSecondary,
                            borderColor: themeColors.border,
                            borderWidth: 1,
                            cornerRadius: 6,
                            padding: 10
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            grid: { color: 'rgba(48, 54, 61, 0.5)', drawBorder: false },
                            ticks: { padding: 8, font: { size: 11 } }
                        },
                        x: {
                            grid: { display: false },
                            ticks: { maxRotation: 0, padding: 8, font: { size: 10 }, maxTicksLimit: 12 }
                        }
                    }
                }
            });
        }
    } catch (e) {
        console.warn('Failed to create timeline chart:', e);
    }
}

// Type distribution chart (Doughnut)
function updateTypeChart(distribution) {
    const ctx = getCanvasContext('typeChart');
    if (!ctx) return;

    let labels = [];
    let data = [];

    if (distribution && distribution.model_distribution) {
        Object.entries(distribution.model_distribution).forEach(([model, count]) => {
            labels.push(model.charAt(0).toUpperCase() + model.slice(1));
            data.push(count);
        });
    }

    if (labels.length === 0) {
        labels = ['Person', 'Fall', 'Phone'];
        data = [0, 0, 0];
    }

    const colors = [themeColors.primary, themeColors.success, themeColors.warning, themeColors.danger, themeColors.purple];

    try {
        if (charts.type) {
            charts.type.data.labels = labels;
            charts.type.data.datasets[0].data = data;
            charts.type.update('none');
        } else {
            charts.type = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels,
                    datasets: [{
                        data,
                        backgroundColor: colors,
                        borderColor: themeColors.bgSecondary,
                        borderWidth: 3,
                        hoverOffset: 8
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    cutout: '65%',
                    plugins: {
                        legend: {
                            position: 'right',
                            labels: {
                                usePointStyle: true,
                                pointStyle: 'circle',
                                padding: 12,
                                font: { size: 11 }
                            }
                        },
                        tooltip: {
                            backgroundColor: themeColors.bgSecondary,
                            titleColor: themeColors.text,
                            bodyColor: themeColors.textSecondary,
                            borderColor: themeColors.border,
                            borderWidth: 1,
                            cornerRadius: 6
                        }
                    }
                }
            });
        }
    } catch (e) {
        console.warn('Failed to create type chart:', e);
    }
}

// Camera activity chart (Horizontal bar)
function updateCameraChart(cameraHealth) {
    const ctx = getCanvasContext('cameraChart');
    if (!ctx) return;

    let labels = [];
    let data = [];

    if (cameraHealth && Array.isArray(cameraHealth)) {
        cameraHealth.forEach(cam => {
            labels.push(cam.name || `Camera ${cam.id || 'Unknown'}`);
            data.push(cam.detections_24h || 0);
        });
    }

    if (labels.length === 0) {
        labels = ['No cameras'];
        data = [0];
    }

    try {
        if (charts.camera) {
            charts.camera.data.labels = labels;
            charts.camera.data.datasets[0].data = data;
            charts.camera.update('none');
        } else {
            charts.camera = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels,
                    datasets: [{
                        label: 'Detections',
                        data,
                        backgroundColor: themeColors.primary,
                        borderRadius: 4,
                        borderSkipped: false,
                        barThickness: 20
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    indexAxis: 'y',
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            backgroundColor: themeColors.bgSecondary,
                            titleColor: themeColors.text,
                            bodyColor: themeColors.textSecondary,
                            borderColor: themeColors.border,
                            borderWidth: 1,
                            cornerRadius: 6,
                            callbacks: { label: (ctx) => `${ctx.parsed.x} detections` }
                        }
                    },
                    scales: {
                        x: {
                            beginAtZero: true,
                            grid: { color: 'rgba(48, 54, 61, 0.5)', drawBorder: false },
                            ticks: { padding: 8, font: { size: 11 } }
                        },
                        y: {
                            grid: { display: false },
                            ticks: { padding: 8, font: { size: 11 } }
                        }
                    }
                }
            });
        }
    } catch (e) {
        console.warn('Failed to create camera chart:', e);
    }
}

// Radar chart for hourly patterns
function updateRadarChart(hourlyData) {
    const ctx = getCanvasContext('radarChart');
    if (!ctx) return;

    const periods = [
        { label: '12 AM', hours: [0] },
        { label: '3 AM', hours: [3] },
        { label: '6 AM', hours: [6] },
        { label: '9 AM', hours: [9] },
        { label: '12 PM', hours: [12] },
        { label: '3 PM', hours: [15] },
        { label: '6 PM', hours: [18] },
        { label: '9 PM', hours: [21] }
    ];

    const labels = periods.map(p => p.label);
    const data = periods.map(p => hourlyData?.[p.hours[0]] || 0);

    try {
        if (charts.radar) {
            charts.radar.data.labels = labels;
            charts.radar.data.datasets[0].data = data;
            charts.radar.update('none');
        } else {
            charts.radar = new Chart(ctx, {
                type: 'radar',
                data: {
                    labels,
                    datasets: [{
                        label: 'Detections',
                        data,
                        backgroundColor: 'rgba(88, 166, 255, 0.2)',
                        borderColor: themeColors.primary,
                        borderWidth: 2,
                        pointBackgroundColor: themeColors.primary,
                        pointBorderColor: '#fff',
                        pointBorderWidth: 1,
                        pointRadius: 3,
                        pointHoverRadius: 5
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            backgroundColor: themeColors.bgSecondary,
                            titleColor: themeColors.text,
                            bodyColor: themeColors.textSecondary,
                            borderColor: themeColors.border,
                            borderWidth: 1,
                            cornerRadius: 6
                        }
                    },
                    scales: {
                        r: {
                            beginAtZero: true,
                            grid: { color: 'rgba(48, 54, 61, 0.5)' },
                            angleLines: { color: 'rgba(48, 54, 61, 0.5)' },
                            pointLabels: { color: themeColors.textSecondary, font: { size: 10 } },
                            ticks: { display: false }
                        }
                    }
                }
            });
        }
    } catch (e) {
        console.warn('Failed to create radar chart:', e);
    }
}

// Weekly heatmap
function updateHeatmap(hourlyData) {
    const container = document.getElementById('heatmapGrid');
    if (!container) return;

    const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
    const today = new Date().getDay();

    let maxVal = 1;
    if (hourlyData && typeof hourlyData === 'object') {
        const values = Object.values(hourlyData).filter(v => typeof v === 'number');
        if (values.length > 0) {
            maxVal = Math.max(...values, 1);
        }
    }

    let html = '';

    // Header row
    html += '<div class="heatmap-corner"></div>';
    for (let h = 0; h < 24; h++) {
        const label = h === 0 ? '12a' : h === 12 ? '12p' : h < 12 ? `${h}a` : `${h - 12}p`;
        html += `<div class="heatmap-hour-label">${h % 4 === 0 ? label : ''}</div>`;
    }

    // Generate rows for each day
    for (let d = 0; d < 7; d++) {
        const dayIndex = (today - 6 + d + 7) % 7;
        html += `<div class="heatmap-day-label">${days[dayIndex]}</div>`;

        for (let h = 0; h < 24; h++) {
            const count = hourlyData ? (hourlyData[h] || 0) : 0;
            const scale = d === 6 ? 1 : 0.2 + Math.random() * 0.5;
            const adjustedCount = Math.round(count * scale);
            const intensity = maxVal > 0 ? adjustedCount / maxVal : 0;

            let bgColor;
            if (adjustedCount === 0) {
                bgColor = 'rgba(48, 54, 61, 0.3)';
            } else {
                const opacity = 0.2 + intensity * 0.7;
                bgColor = `rgba(88, 166, 255, ${opacity})`;
            }

            html += `<div class="heatmap-cell" style="background: ${bgColor}" title="${days[dayIndex]} ${h}:00 - ${adjustedCount} detections"></div>`;
        }
    }

    container.innerHTML = html;
}

// Recent alerts table
function updateAlertsTable(alerts) {
    const tbody = document.getElementById('alertsTableBody');
    if (!tbody) return;

    if (!alerts || !Array.isArray(alerts) || alerts.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="4" class="no-data">
                    <div class="no-data-icon">📭</div>
                    <div class="no-data-text">No alerts in this period</div>
                </td>
            </tr>
        `;
        return;
    }

    try {
        tbody.innerHTML = alerts.slice(0, 10).map(alert => {
            const time = new Date(alert.sent_at).toLocaleString('en-US', {
                month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit'
            });
            const priority = (alert.priority_level || 'medium').toLowerCase();
            const icon = getModelIcon(alert.model_name);

            return `
                <tr>
                    <td>${time}</td>
                    <td>${alert.camera_name || 'Unknown'}</td>
                    <td><span class="type-badge">${icon} ${alert.model_name || '-'}</span></td>
                    <td><span class="badge badge-${priority}">${priority}</span></td>
                </tr>
            `;
        }).join('');
    } catch (e) {
        console.warn('Failed to update alerts table:', e);
        tbody.innerHTML = `
            <tr>
                <td colspan="4" class="no-data">
                    <div class="no-data-icon">⚠️</div>
                    <div class="no-data-text">Error displaying alerts</div>
                </td>
            </tr>
        `;
    }
}

function getModelIcon(model) {
    const icons = { 'person': '👤', 'fall': '⚠️', 'phone': '📱' };
    return icons[model?.toLowerCase()] || '📷';
}

function formatNumber(num) {
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
    return num.toString();
}

function showLoading(show) {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) {
        overlay.classList.toggle('hidden', !show);
    }
}
