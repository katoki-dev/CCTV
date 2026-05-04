"""
CEMSS - Campus Event management and Surveillance System
Main Flask Application
"""
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, Response
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import cv2
import json
from datetime import datetime
import numpy as np

from config import (
    SECRET_KEY, DATABASE_URI, FLASK_HOST, FLASK_PORT, DEBUG,
    SOCKETIO_ASYNC_MODE, SOCKETIO_CORS_ALLOWED_ORIGINS,
    SESSION_PERMANENT, PERMANENT_SESSION_LIFETIME, DETECTION_MODELS,
    EMAIL_ENABLED, EMAIL_HOST, EMAIL_PORT, EMAIL_USERNAME, EMAIL_PASSWORD,
    EMAIL_USE_TLS, EMAIL_USE_SSL, EMAIL_FROM_ADDRESS, RECORDING_BASE_DIR
)
from models import db, User, Camera, Permission, DetectionLog, Alert, PermissionRequest, Magazine, Event
from database import init_database
from logging_manager import get_logging_manager
from alerts.alert_manager import AlertManager
from detection.detection_pipeline import DetectionPipeline
from sqlalchemy.orm import selectinload

# Try to import Flask-Mail
try:
    from flask_mail import Mail
    FLASK_MAIL_AVAILABLE = True
except ImportError:
    FLASK_MAIL_AVAILABLE = False
    Mail = None

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
app.config['SECRET_KEY'] = SECRET_KEY
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SESSION_PERMANENT'] = SESSION_PERMANENT
app.config['PERMANENT_SESSION_LIFETIME'] = PERMANENT_SESSION_LIFETIME

# Configure Flask-Mail
if FLASK_MAIL_AVAILABLE and EMAIL_ENABLED:
    app.config['MAIL_SERVER'] = EMAIL_HOST
    app.config['MAIL_PORT'] = EMAIL_PORT
    app.config['MAIL_USE_TLS'] = EMAIL_USE_TLS
    app.config['MAIL_USE_SSL'] = EMAIL_USE_SSL
    app.config['MAIL_USERNAME'] = EMAIL_USERNAME
    app.config['MAIL_PASSWORD'] = EMAIL_PASSWORD
    app.config['MAIL_DEFAULT_SENDER'] = EMAIL_FROM_ADDRESS
    mail = Mail(app)
    print("✓ Flask-Mail initialized for email alerts")
else:
    mail = None
    if EMAIL_ENABLED and not FLASK_MAIL_AVAILABLE:
        print("⚠ Flask-Mail not available, falling back to SMTP")

# Initialize extensions
db.init_app(app)
socketio = SocketIO(app, async_mode=SOCKETIO_ASYNC_MODE, cors_allowed_origins=SOCKETIO_CORS_ALLOWED_ORIGINS)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

# Initialize components
logging_manager = None
alert_manager = None
detection_pipeline = None


# Import health routes
try:
    from api_health import register_health_routes
    _health_routes_available = True
except ImportError:
    _health_routes_available = False



# Register custom blueprints
try:
    from routes.auth import auth_bp
    app.register_blueprint(auth_bp)
    from routes.admin import admin_bp
    app.register_blueprint(admin_bp)
    from routes.campus import campus_bp
    app.register_blueprint(campus_bp)
    from routes.cameras import cameras_bp
    app.register_blueprint(cameras_bp)
    print("✓ Cameras blueprint loaded")
except ImportError as e:
    print(f"⚠ Failed to load custom blueprints: {e}")
@login_manager.user_loader
def load_user(user_id):
    """Load user for Flask-Login"""
    return User.query.get(int(user_id))


def reload_cameras_from_db():
    """Reload all cameras from database into detection pipeline on startup"""
    try:
        cameras = Camera.query.all()
        if cameras:
            logging_manager.log_system_event("CAMERA_RELOAD", f"Loading {len(cameras)} cameras from database...")
            cameras_with_detection = []
            
            for camera in cameras:
                success = detection_pipeline.add_camera(
                    camera.id, 
                    camera.source, 
                    camera.name,
                    autostart=True
                )
                if success:
                    logging_manager.log_camera_event(
                        camera.name, 
                        "LOADED", 
                        f"Camera reloaded from database (Source: {camera.source})"
                    )
                    # Track cameras that had detection enabled
                    if camera.detection_enabled:
                        cameras_with_detection.append(camera)
                else:
                    logging_manager.log_camera_event(
                        camera.name, 
                        "LOAD_FAILED", 
                        f"Failed to reload camera from database"
                    )
            
            logging_manager.log_system_event("CAMERA_RELOAD_COMPLETE", f"Finished loading {len(cameras)} cameras. Auto-start disabled.")
            
            # Disable detection for all cameras on startup to save resources
            if cameras_with_detection:
                logging_manager.log_system_event("DETECTION_RESTORE", f"Disabling auto-start for {len(cameras_with_detection)} cameras to save CPU/RAM...")
                for camera in cameras_with_detection:
                    try:
                        # Explicitly set detection to False in DB and do not start the pipeline
                        camera.detection_enabled = False
                        logging_manager.log_camera_event(
                            camera.name,
                            "AUTO_START_DISABLED",
                            "Detection was active previously but is now disabled for manual startup."
                        )
                    except Exception as e:
                        logging_manager.log_camera_event(
                            camera.name,
                            "AUTO_START_DISABLE_FAILED",
                            f"Failed to update database: {str(e)}"
                        )
                
                db.session.commit()
        else:
            logging_manager.log_system_event("CAMERA_RELOAD", "No cameras found in database")
    except Exception as e:
        logging_manager.log_system_event("CAMERA_RELOAD_ERROR", f"Error loading cameras: {str(e)}")


# ==================== VLM Monitoring API ====================

@app.route('/api/vlm/status')
@login_required
def api_vlm_status():
    """Get VLM system status"""
    try:
        from detection.vlm_monitor import VLMMonitor
        from config import VLM_ENABLED, VLM_TIER1_MODEL, VLM_TIER2_MODEL
        from datetime import timedelta
        
        if not VLM_ENABLED:
            return jsonify({
                'enabled': False,
                'message': 'VLM monitoring is disabled in configuration'
            })
        
        vlm = VLMMonitor(tier1_model=VLM_TIER1_MODEL, tier2_model=VLM_TIER2_MODEL)
        status = vlm.check_availability()
        
        # Get recent analyses count
        from models import VLMAnalysis
        recent_count = VLMAnalysis.query.filter(
            VLMAnalysis.timestamp >= datetime.now() - timedelta(hours=1)
        ).count()
        
        return jsonify({
            'enabled': VLM_ENABLED,
            'models': {
                'tier1': VLM_TIER1_MODEL,
                'tier2': VLM_TIER2_MODEL
            },
            'status': status,
            'recent_analyses': recent_count
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/vlm/test', methods=['POST'])
@login_required
def api_vlm_test():
    """Test VLM analysis on a detection"""
    try:
        from detection.vlm_monitor import VLMMonitor
        from config import VLM_ENABLED, VLM_TIER1_MODEL, VLM_TIER2_MODEL
        
        if not VLM_ENABLED:
            return jsonify({'error': 'VLM monitoring is disabled'}), 400
        
        # Initialize VLM
        vlm = VLMMonitor(tier1_model=VLM_TIER1_MODEL, tier2_model=VLM_TIER2_MODEL)
        
        # Check availability
        status = vlm.check_availability()
        if not status['ollama_running']:
            return jsonify({'error': 'Ollama is not running'}), 503
        
        # Get request data
        data = request.get_json()
        camera_id = data.get('camera_id', 1)
        detection_type = data.get('detection_type', 'test')
        confidence = data.get('confidence', 0.85)
        
        # Build context for test
        context = f"""Camera ID: {camera_id}
Detection: {detection_type}
Confidence: {confidence:.1%}
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Context: Surveillance system detected {detection_type} event."""
        
        # Run Tier 1 analysis
        tier1_result = vlm.tier1_fast_scan(context)
        
        return jsonify({
            'success': True,
            'vlm_enabled': VLM_ENABLED,
            'models': {
                'tier1': VLM_TIER1_MODEL,
                'tier2': VLM_TIER2_MODEL
            },
            'status': status,
            'analysis': {
                'tier1': tier1_result
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500





# ==================== Initialization ====================

def init_components():
    """Initialize CEMSS components"""
    global logging_manager, alert_manager, detection_pipeline
    
    # Auto-optimize system config before anything else starts
    try:
        from utils.system_optimizer import SystemOptimizer
        SystemOptimizer.apply_auto_optimization()
    except Exception as e:
        print(f"Failed to run System Optimizer: {e}")
        
    logging_manager = get_logging_manager()
    
    # Verify model files exist
    verify_model_files()
    
    alert_manager = AlertManager(db.session, logging_manager, mail_instance=mail)
    app.alert_manager = alert_manager  # Attach to app for blueprints
    detection_pipeline = DetectionPipeline(logging_manager, alert_manager, flask_app=app)
    app.detection_pipeline = detection_pipeline  # Attach to app for blueprints
    detection_pipeline.start()
    
    logging_manager.log_system_event("STARTUP", "CEMSS application started")
    
    # Reload cameras from database
    reload_cameras_from_db()




def verify_model_files():
    """Verify that detection model files exist at startup"""
    import os
    from config import DETECTION_MODELS
    
    missing_models = []
    for model_name, config in DETECTION_MODELS.items():
        if config.get('enabled', True):
            model_path = config.get('model_path', '')
            if model_path and not os.path.exists(model_path):
                missing_models.append((model_name, model_path))
                logging_manager.log_system_event(
                    "MODEL_MISSING", 
                    f"Warning: Model file not found for '{model_name}': {model_path}"
                )
    
    if missing_models:
        print(f"⚠ Warning: {len(missing_models)} detection model(s) not found:")
        for name, path in missing_models:
            print(f"  - {name}: {path}")
        print("  Detection may not work properly for these models.")
    else:
        print("✓ All detection model files verified")


# ==================== Authentication Routes ====================

# Auth routes moved to routes/auth.py


# ==================== Dashboard Routes ====================

@app.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard"""
    # Get cameras accessible by user
    if current_user.is_admin:
        cameras = Camera.query.filter_by(is_active=True).all()
    else:
        # Optimized query using JOIN to avoid N+1 issue
        cameras = Camera.query.join(Permission).filter(
            Permission.user_id == current_user.id,
            Permission.can_view == True,
            Camera.is_active == True
        ).all()
    
    return render_template('dashboard.html', 
                         user=current_user,
                         cameras=cameras,
                         detection_models=DETECTION_MODELS)


@app.route('/camera/<int:camera_id>')
@login_required
def camera_view(camera_id):
    """Individual camera view"""
    camera = Camera.query.get_or_404(camera_id)
    
    # Check permission
    if not current_user.is_admin and not current_user.has_camera_access(camera_id):
        return "Access denied", 403
    
    # Get recent detections for this camera
    recent_detections = DetectionLog.query.filter_by(camera_id=camera_id)\
        .order_by(DetectionLog.timestamp.desc()).limit(20).all()
    
    # Get user permissions for this camera
    user_permission = Permission.query.filter_by(
        user_id=current_user.id,
        camera_id=camera_id
    ).first() if not current_user.is_admin else None
    
    return render_template('camera.html',
                         user=current_user,
                         camera=camera,
                         recent_detections=recent_detections,
                         detection_models=DETECTION_MODELS,
                         user_permission=user_permission)


@app.route('/camera/<int:camera_id>/detections')
@login_required
def camera_detections_page(camera_id):
    """Camera-specific detection history page"""
    camera = Camera.query.get_or_404(camera_id)
    
    # Check permission
    if not current_user.is_admin and not current_user.has_camera_access(camera_id):
        return "Access denied", 403
    
    return render_template('camera_detections.html',
                         user=current_user,
                         camera=camera)


# Camera, Detection, Recording, Alert, and Zone routes moved to routes/cameras.py


# Admin and permission request routes moved to routes/admin.py


# ==================== Detection Logs Routes ====================

@app.route('/detections')
@login_required
def detections_page():
    """View all detection logs"""
    # Get cameras accessible by user
    if current_user.is_admin:
        cameras = Camera.query.all()
    else:
        permissions = Permission.query.filter_by(user_id=current_user.id, can_view=True).all()
        camera_ids = [p.camera_id for p in permissions]
        cameras = Camera.query.filter(Camera.id.in_(camera_ids)).all()
    
    return render_template('detections.html',
                         user=current_user,
                         cameras=cameras)


@app.route('/api/detections')
@login_required
def api_get_detections():
    """Get detection logs with filtering options"""
    # Parse query parameters
    camera_id = request.args.get('camera_id', type=int)
    model_name = request.args.get('model_name')
    limit = request.args.get('limit', 50, type=int)
    offset = request.args.get('offset', 0, type=int)
    
    # Build query
    query = DetectionLog.query
    
    # Filter by camera access for non-admins
    if not current_user.is_admin:
        # Optimized query using JOIN
        query = query.join(Permission, DetectionLog.camera_id == Permission.camera_id)\
                     .filter(Permission.user_id == current_user.id, Permission.can_view == True)
    
    # Apply filters
    if camera_id:
        query = query.filter_by(camera_id=camera_id)
    if model_name:
        query = query.filter_by(model_name=model_name)
    
    # Get total count
    total = query.count()
    
    # Get detections with pagination
    detections = query.order_by(DetectionLog.timestamp.desc())\
        .offset(offset).limit(limit).all()
    
    return jsonify({
        'detections': [d.to_dict() for d in detections],
        'total': total,
        'limit': limit,
        'offset': offset
    })


@app.route('/api/detections/recent')
@login_required
def api_get_recent_detections():
    """Get recent detections across all accessible cameras"""
    limit = request.args.get('limit', 10, type=int)
    limit = min(limit, 50)  # Cap at 50
    
    # Get cameras user has access to
    if current_user.is_admin:
        detections = DetectionLog.query\
            .order_by(DetectionLog.timestamp.desc())\
            .limit(limit).all()
    else:
        # Optimized query using JOIN
        detections = DetectionLog.query\
            .join(Permission, DetectionLog.camera_id == Permission.camera_id)\
            .filter(Permission.user_id == current_user.id, Permission.can_view == True)\
            .order_by(DetectionLog.timestamp.desc())\
            .limit(limit).all()
    
    return jsonify({
        'detections': [d.to_dict() for d in detections],
        'count': len(detections)
    })



@app.route('/api/detections/camera/<int:camera_id>')
@login_required
def api_get_camera_detections(camera_id):
    """Get recent detections for a specific camera"""
    # Check permission
    if not current_user.is_admin and not current_user.has_camera_access(camera_id):
        return jsonify({'error': 'Access denied'}), 403
    
    limit = request.args.get('limit', 20, type=int)
    
    detections = DetectionLog.query.filter_by(camera_id=camera_id)\
        .order_by(DetectionLog.timestamp.desc())\
        .limit(limit).all()
    
    return jsonify({
        'detections': [d.to_dict() for d in detections],
        'camera_id': camera_id
    })





# ==================== API Routes - Analytics (Phase 1) ====================

@app.route('/api/analytics/timeline')
@login_required
def api_analytics_timeline():
    """Get detection timeline data"""
    from analytics.analytics_engine import AnalyticsEngine
    
    analytics = AnalyticsEngine()
    
    # Parse query parameters
    start_str = request.args.get('start_date')
    end_str = request.args.get('end_date')
    camera_id = request.args.get('camera_id', type=int)
    model_name = request.args.get('model_name')
    
    from datetime import datetime
    start_date = datetime.fromisoformat(start_str) if start_str else None
    end_date = datetime.fromisoformat(end_str) if end_str else None
    
    try:
        data = analytics.get_detection_timeline(start_date, end_date, camera_id, model_name)
        return jsonify(data), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/analytics/distribution')
@login_required
def api_analytics_distribution():
    """Get detection distribution by model/camera/severity"""
    from analytics.analytics_engine import AnalyticsEngine
    
    analytics = AnalyticsEngine()
    period = request.args.get('period', '24h')
    camera_id = request.args.get('camera_id', type=int)
    
    try:
        data = analytics.get_detection_distribution(period, camera_id)
        return jsonify(data), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/analytics/camera-health')
@login_required
def api_analytics_camera_health():
    """Get camera health metrics"""
    from analytics.analytics_engine import AnalyticsEngine
    
    analytics = AnalyticsEngine()
    camera_id = request.args.get('camera_id', type=int)
    
    try:
        data = analytics.get_camera_health_metrics(camera_id)
        return jsonify(data), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/analytics/summary')
@login_required
def api_analytics_summary():
    """Get summary statistics"""
    from analytics.analytics_engine import AnalyticsEngine
    
    analytics = AnalyticsEngine()
    period = request.args.get('period', '24h')
    
    try:
        data = analytics.get_summary_stats(period)
        return jsonify(data), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== Dashboard API ====================

@app.route('/api/dashboard/briefing')
@login_required
def api_dashboard_briefing():
    """Generate a summary of recent system activity"""
    from models import DetectionLog
    from datetime import datetime, timedelta
    
    time_window = request.args.get('time_window', default=15, type=int)
    since = datetime.now() - timedelta(minutes=time_window)
    
    detections = DetectionLog.query.filter(DetectionLog.timestamp >= since).all()
    
    if not detections:
        return jsonify({
            'success': True,
            'briefing': f"System scan complete. No significant security events or detections recorded in the last {time_window} minutes. All sectors remain secure.",
            'generated_by': 'template',
            'timestamp': datetime.now().isoformat()
        })
    
    # Simple count-based summary
    counts = {}
    for d in detections:
        counts[d.model_name] = counts.get(d.model_name, 0) + 1
    
    summary_parts = []
    for model, count in counts.items():
        summary_parts.append(f"{count} {model} detection{'s' if count > 1 else ''}")
    
    briefing_text = f"Activity Alert: In the last {time_window} minutes, the system has identified {', '.join(summary_parts)}. "
    if 'violence' in counts or 'fall' in counts:
        briefing_text += "**High-priority events detected. Immediate review recommended.**"
    else:
        briefing_text += "Monitoring continues as scheduled."
        
    return jsonify({
        'success': True,
        'briefing': briefing_text,
        'generated_by': 'template',
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/detections/recent')
@login_required
def api_recent_detections():
    """Get the latest detections for the dashboard"""
    from models import DetectionLog
    limit = request.args.get('limit', default=10, type=int)
    
    detections = DetectionLog.query.order_by(DetectionLog.timestamp.desc()).limit(limit).all()
    
    return jsonify({
        'success': True,
        'detections': [d.to_dict() for d in detections]
    })


# ==================== Video Streaming ====================

@app.route('/api/snapshot/<int:camera_id>')
@login_required
def api_camera_snapshot(camera_id):
    """Get a current snapshot from the camera for zone editing"""
    if detection_pipeline is None:
        return jsonify({'error': 'Detection pipeline not available'}), 500
    
    frame = detection_pipeline.get_latest_frame(camera_id, annotated=False)
    if frame is None:
        return jsonify({'error': 'Unable to capture frame'}), 500
    
    import cv2
    import base64
    
    # Encode frame as JPEG
    _, buffer = cv2.imencode('.jpg', frame)
    img_base64 = base64.b64encode(buffer).decode('utf-8')
    
    return jsonify({
        'success': True,
        'image': f'data:image/jpeg;base64,{img_base64}',
        'width': frame.shape[1],
        'height': frame.shape[0]
    })


@app.route('/api/stream/<int:camera_id>')
@login_required
def video_stream(camera_id):
    """Stream video from a camera"""
    if detection_pipeline is None:
        return "Detection pipeline not initialized", 503
        
    camera = Camera.query.get_or_404(camera_id)
    
    # Check permission
    if not current_user.is_admin and not current_user.has_camera_access(camera_id):
        return "Access denied", 403
    
    def generate():
        """Generate video frames"""
        from config import JPEG_QUALITY
        
        while True:
            frame = detection_pipeline.get_latest_frame(camera_id, annotated=True)
            
            if frame is not None:
                # Encode frame as JPEG with configurable quality
                encode_params = [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY]
                ret, buffer = cv2.imencode('.jpg', frame, encode_params)
                if ret:
                    frame_bytes = buffer.tobytes()
                    yield (b'--frame\r\n'
                          b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            
            # Small delay using non-blocking sleep if possible
            try:
                from app import socketio
                socketio.sleep(0.033)  # ~30 FPS
            except Exception:
                import time
                time.sleep(0.033)
    
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')


# ==================== Status Routes ====================

@app.route('/api/status')
@login_required
def api_status():
    """Get system status"""
    return jsonify({
        'user': current_user.to_dict(),
        'pipeline': detection_pipeline.get_status(),
        'session': logging_manager.get_session_summary()
    })


@app.route('/account')
@login_required
def account_page():
    """User account/profile page"""
    return render_template('account.html', user=current_user)


# ==================== Analytics Dashboard ====================

@app.route('/analytics')
@login_required
def analytics_dashboard():
    """Analytics dashboard page"""
    return render_template('analytics.html', user=current_user)


@app.route('/api/analytics/stats')
@login_required
def api_analytics_stats():
    """Get analytics statistics for dashboard"""
    from analytics.analytics_engine import AnalyticsEngine
    from datetime import timedelta
    
    period = request.args.get('period', '24h')
    
    try:
        analytics = AnalyticsEngine()
        
        # Get summary stats
        summary = analytics.get_summary_stats(period)
        
        # Get detection timeline
        if period == '7d':
            start_date = datetime.now() - timedelta(days=7)
        elif period == '30d':
            start_date = datetime.now() - timedelta(days=30)
        else:
            start_date = datetime.now() - timedelta(hours=24)
        
        timeline = analytics.get_detection_timeline(start_date=start_date)
        
        # Get distribution
        distribution = analytics.get_detection_distribution(period)
        
        # Get camera health
        camera_health = analytics.get_camera_health_metrics()
        
        # Get recent alerts
        recent_alerts = Alert.query.order_by(Alert.sent_at.desc()).limit(10).all()
        
        # Get hourly breakdown for heatmap
        hourly_data = {}
        detections = DetectionLog.query.filter(DetectionLog.timestamp >= start_date).all()
        for d in detections:
            hour = d.timestamp.hour
            hourly_data[hour] = hourly_data.get(hour, 0) + 1
        
        return jsonify({
            'success': True,
            'period': period,
            'summary': summary,
            'timeline': timeline,
            'distribution': distribution,
            'camera_health': camera_health,
            'recent_alerts': [a.to_dict() for a in recent_alerts],
            'hourly_breakdown': hourly_data
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== Application Lifecycle ====================

@app.before_request
def before_first_request():
    """Initialize components on first request"""
    global logging_manager, detection_pipeline
    
    if logging_manager is None:
        with app.app_context():
            init_components()


def shutdown_handler():
    """Cleanup on shutdown"""
    if detection_pipeline:
        detection_pipeline.stop()
    if logging_manager:
        logging_manager.close_session()


import atexit
# ==================== Video Recordings Routes ====================

@app.route('/recordings')
@login_required
def recordings_page():
    """Video recordings page"""
    # Get cameras accessible by user for filter dropdown
    if current_user.is_admin:
        cameras = Camera.query.filter_by(is_active=True).all()
    else:
        permissions = Permission.query.filter_by(user_id=current_user.id, can_view=True).all()
        camera_ids = [p.camera_id for p in permissions]
        cameras = Camera.query.filter(Camera.id.in_(camera_ids), Camera.is_active == True).all()
    
    return render_template('recordings.html',
                         user=current_user,
                         cameras=cameras)


@app.route('/api/recordings', methods=['GET'])
@login_required
def api_get_recordings():
    """Get all recordings with filtering and pagination"""
    from models import VideoRecording
    from sqlalchemy import desc
    
    # Get query parameters
    camera_id = request.args.get('camera_id', type=int)
    recording_type = request.args.get('recording_type', 'all')  # 'all', 'detection', 'continuous'
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    # Build query
    query = VideoRecording.query
    
    # Filter by user permissions (non-admin users)
    if not current_user.is_admin:
        permissions = Permission.query.filter_by(user_id=current_user.id, can_view=True).all()
        camera_ids = [p.camera_id for p in permissions]
        query = query.filter(VideoRecording.camera_id.in_(camera_ids))
    
    # Apply filters
    if camera_id:
        query = query.filter_by(camera_id=camera_id)
    
    if recording_type != 'all':
        query = query.filter_by(recording_type=recording_type)
    
    if start_date:
        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(VideoRecording.start_time >= start_dt)
        except ValueError:
            pass
    
    if end_date:
        try:
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            # Add 1 day to include the entire end date
            end_dt = end_dt.replace(hour=23, minute=59, second=59)
            query = query.filter(VideoRecording.start_time <= end_dt)
        except ValueError:
            pass
    
    # Get total count
    total = query.count()
    
    # Get recordings with pagination
    offset = (page - 1) * per_page
    recordings = query.order_by(desc(VideoRecording.created_at))\
        .offset(offset).limit(per_page).all()
    
    return jsonify({
        'recordings': [r.to_dict() for r in recordings],
        'total': total,
        'page': page,
        'per_page': per_page,
        'total_pages': (total + per_page - 1) // per_page
    })


@app.route('/api/recordings/<int:recording_id>', methods=['GET'])
@login_required
def api_get_recording(recording_id):
    """Get detailed information about a specific recording"""
    from models import VideoRecording
    
    recording = VideoRecording.query.get_or_404(recording_id)
    
    # Check permission
    if not current_user.is_admin and not current_user.has_camera_access(recording.camera_id):
        return jsonify({'error': 'Access denied'}), 403
    
    return jsonify(recording.to_dict())


@app.route('/api/recordings/video/<int:recording_id>')
@login_required
def api_serve_recording_video(recording_id):
    """Serve video file for playback with byte-range support"""
    from models import VideoRecording
    from flask import send_file, Response
    import os
    
    recording = VideoRecording.query.get_or_404(recording_id)
    
    # Check permission
    if not current_user.is_admin and not current_user.has_camera_access(recording.camera_id):
        return jsonify({'error': 'Access denied'}), 403
    
    # Get full file path
    file_path = os.path.join(RECORDING_BASE_DIR, recording.filepath)
    
    if not os.path.exists(file_path):
        return jsonify({'error': 'Video file not found'}), 404
    
    # Get file size
    file_size = os.path.getsize(file_path)
    
    # Check for Range header (for video seeking)
    range_header = request.headers.get('Range', None)
    
    if not range_header:
        # No range requested, send entire file
        return send_file(file_path, mimetype='video/mp4')
    
    # Parse range header
    byte_range = range_header.replace('bytes=', '').split('-')
    start = int(byte_range[0]) if byte_range[0] else 0
    end = int(byte_range[1]) if len(byte_range) > 1 and byte_range[1] else file_size - 1
    
    # Read chunk
    chunk_size = end - start + 1
    
    def generate():
        with open(file_path, 'rb') as f:
            f.seek(start)
            data = f.read(chunk_size)
            yield data
    
    # Create response with partial content
    response = Response(generate(), 206, mimetype='video/mp4',
                       direct_passthrough=True)
    response.headers.add('Content-Range', f'bytes {start}-{end}/{file_size}')
    response.headers.add('Accept-Ranges', 'bytes')
    response.headers.add('Content-Length', str(chunk_size))
    
    return response


@app.route('/api/recordings/<int:recording_id>', methods=['DELETE'])
@login_required
def api_delete_recording(recording_id):
    """Delete a recording (admin only)"""
    from models import VideoRecording
    import os
    
    if not current_user.is_admin:
        return jsonify({'error': 'Admin access required'}), 403
    
    recording = VideoRecording.query.get_or_404(recording_id)
    
    # Delete file from disk
    file_path = os.path.join(RECORDING_BASE_DIR, recording.filepath)
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        logging_manager.log_system_event("RECORDING_DELETE_ERROR", f"Failed to delete file: {str(e)}")
    
    # Delete database entry
    db.session.delete(recording)
    db.session.commit()
    
    logging_manager.log_system_event(
        "RECORDING_DELETED",
        f"Recording '{recording.filename}' deleted by {current_user.username}"
    )
    
    return jsonify({'success': True, 'message': 'Recording deleted'})


# =================== Shutdown Handler ====================

@socketio.on('connect')
def handle_connect():
    if current_user.is_authenticated:
        from flask_socketio import join_room
        join_room(f"user_{current_user.id}")
        # print(f"DEBUG: User {current_user.username} joined room user_{current_user.id}")

@socketio.on('join_notifications')
def handle_join_notifications(data):
    if current_user.is_authenticated:
        from flask_socketio import join_room
        join_room(f"user_{current_user.id}")

atexit.register(shutdown_handler)


# ==================== Main ====================

if __name__ == '__main__':
    with app.app_context():
        # Initialize database
        init_database(app)
        
        # Initialize components (detection pipeline, etc)
        init_components()
    
    print("\n" + "="*60)
    print("CEMSS - Campus Event management and Surveillance System")
    print("="*60)
    print(f"Server: http://{FLASK_HOST}:{FLASK_PORT}")
    print("Default Login: admin / admin")
    print("="*60 + "\n")
    
    # Run Flask app
    socketio.run(app, host=FLASK_HOST, port=FLASK_PORT, debug=DEBUG, allow_unsafe_werkzeug=True)
