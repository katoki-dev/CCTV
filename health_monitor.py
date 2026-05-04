"""
System Health Monitoring Dashboard
Real-time system health checks and alerts
"""
from flask import Blueprint, jsonify, render_template
from flask_login import login_required
import psutil
import requests
from datetime import datetime
from models import db, DetectionLog, Alert, Camera
import os

health_bp = Blueprint('health', __name__)

@health_bp.route('/health')
def health_check():
    """Basic health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '11.2'
    })

@health_bp.route('/api/system/health')
@login_required
def system_health():
    """
    Comprehensive system health check
    Returns detailed system metrics
    """
    try:
        health_data = {
            'timestamp': datetime.now().isoformat(),
            'overall_status': 'healthy',
            'checks': {}
        }
        
        # 1. System Resources
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('.')
        
        health_data['checks']['system_resources'] = {
            'status': 'healthy' if cpu_percent < 80 and memory.percent < 90 else 'warning',
            'cpu_percent': cpu_percent,
            'memory_percent': memory.percent,
            'memory_available_gb': memory.available / (1024**3),
            'disk_percent': disk.percent,
            'disk_free_gb': disk.free / (1024**3)
        }
        
        # 2. Database
        try:
            db.session.execute('SELECT 1')
            detection_count = DetectionLog.query.count()
            alert_count = Alert.query.count()
            
            health_data['checks']['database'] = {
                'status': 'healthy',
                'connected': True,
                'total_detections': detection_count,
                'total_alerts': alert_count
            }
        except Exception as e:
            health_data['checks']['database'] = {
                'status': 'critical',
                'connected': False,
                'error': str(e)
            }
            health_data['overall_status'] = 'critical'
        
        # 3. Ollama Service
        try:
            response = requests.get('http://localhost:11434/api/version', timeout=5)
            ollama_healthy = response.status_code == 200
            
            # Check loaded models
            models_response = requests.get('http://localhost:11434/api/tags', timeout=5)
            models = models_response.json().get('models', []) if models_response.status_code == 200 else []
            model_names = [m['name'] for m in models]
            
            health_data['checks']['ollama'] = {
                'status': 'healthy' if ollama_healthy else 'critical',
                'available': ollama_healthy,
                'models_loaded': model_names,
                'model_count': len(models)
            }
        except Exception as e:
            health_data['checks']['ollama'] = {
                'status': 'critical',
                'available': False,
                'error': 'Ollama service not responding'
            }
            health_data['overall_status'] = 'degraded'
        
        # 4. Cameras
        try:
            cameras = Camera.query.all()
            active_cameras = [c for c in cameras if c.enabled]
            
            camera_status = []
            for cam in active_cameras:
                # Check if camera has recent frames (detection pipeline)
                camera_status.append({
                    'id': cam.id,
                    'name': cam.name,
                    'enabled': cam.enabled,
                    'source': cam.source
                })
            
            health_data['checks']['cameras'] = {
                'status': 'healthy' if len(active_cameras) > 0 else 'warning',
                'total': len(cameras),
                'active': len(active_cameras),
                'cameras': camera_status
            }
        except Exception as e:
            health_data['checks']['cameras'] = {
                'status': 'warning',
                'error': str(e)
            }
        
        # 5. Chatbot Service
        from flask import current_app
        chatbot = getattr(current_app, 'chatbot_service', None)
        
        if chatbot:
            vlm_available = chatbot.vlm_analyzer.is_available() if chatbot.vlm_analyzer else False
            health_data['checks']['chatbot'] = {
                'status': 'healthy' if chatbot.is_available() else 'degraded',
                'available': chatbot.is_available(),
                'model': chatbot.model,
                'vlm_available': vlm_available
            }
        else:
            health_data['checks']['chatbot'] = {
                'status': 'critical',
                'available': False,
                'error': 'Chatbot service not initialized'
            }
            health_data['overall_status'] = 'degraded'
        
        # 6. Detection Pipeline
        detection_pipeline = getattr(current_app, 'detection_pipeline', None)
        
        if detection_pipeline:
            health_data['checks']['detection_pipeline'] = {
                'status': 'healthy',
                'active': True,
                'has_camera_pool': detection_pipeline.camera_pool is not None,
                'continuous_analysis': detection_pipeline.continuous_analyzer is not None
            }
        else:
            health_data['checks']['detection_pipeline'] = {
                'status': 'critical',
                'active': False
            }
            health_data['overall_status'] = 'critical'
        
        # Calculate overall status
        critical_checks = [k for k, v in health_data['checks'].items() if v.get('status') == 'critical']
        warning_checks = [k for k, v in health_data['checks'].items() if v.get('status') == 'warning']
        
        if critical_checks:
            health_data['overall_status'] = 'critical'
        elif warning_checks:
            health_data['overall_status'] = 'degraded'
        else:
            health_data['overall_status'] = 'healthy'
        
        health_data['summary'] = {
            'total_checks': len(health_data['checks']),
            'healthy': sum(1 for v in health_data['checks'].values() if v.get('status') == 'healthy'),
            'warnings': len(warning_checks),
            'critical': len(critical_checks)
        }
        
        return jsonify(health_data)
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@health_bp.route('/dashboard/health')
@login_required
def health_dashboard():
    """
    Render health monitoring dashboard
    """
    return render_template('health_dashboard.html')


# Add to app.py:
# from health_monitor import health_bp
# app.register_blueprint(health_bp)

"""
Example health dashboard template (templates/health_dashboard.html):

<!DOCTYPE html>
<html>
<head>
    <title>System Health Monitor</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>
    <h1>CEMSS System Health</h1>
    <div id="overall-status"></div>
    <div id="system-checks"></div>
    
    <script>
        async function updateHealth() {
            const response = await fetch('/api/system/health');
            const data = await response.json();
            
            // Update UI
            document.getElementById('overall-status').innerHTML = 
                `<h2>Status: ${data.overall_status}</h2>`;
            
            let checksHTML = '<ul>';
            for (const [key, check] of Object.entries(data.checks)) {
                checksHTML += `<li>${key}: ${check.status}</li>`;
            }
            checksHTML += '</ul>';
            document.getElementById('system-checks').innerHTML = checksHTML;
        }
        
        updateHealth();
        setInterval(updateHealth, 30000); // Update every 30s
    </script>
</body>
</html>
"""
