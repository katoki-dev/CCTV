from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from models import Camera, Permission, db
from logging_manager import get_logging_manager
import json

cameras_bp = Blueprint('cameras', __name__)
logging_manager = get_logging_manager()

@cameras_bp.route('/api/cameras', methods=['GET', 'POST'])
@login_required
def api_cameras():
    """Get all cameras or add a new camera"""
    if request.method == 'GET':
        if current_user.is_admin:
            cameras = Camera.query.all()
        else:
            permissions = Permission.query.filter_by(user_id=current_user.id, can_view=True).all()
            camera_ids = [p.camera_id for p in permissions]
            cameras = Camera.query.filter(Camera.id.in_(camera_ids)).all()
        
        return jsonify([camera.to_dict() for camera in cameras])
    
    elif request.method == 'POST':
        if not current_user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        data = request.get_json()
        
        existing_camera = Camera.query.filter_by(source=data['source']).first()
        if existing_camera:
            return jsonify({
                'error': 'Camera source already exists',
                'existing_camera': existing_camera.name,
                'message': f"A camera with source '{data['source']}' already exists as '{existing_camera.name}'"
            }), 409
        
        camera = Camera(
            name=data['name'],
            source=data['source'],
            location=data.get('location', '')
        )
        
        db.session.add(camera)
        db.session.commit()
        
        if hasattr(current_app, 'detection_pipeline') and current_app.detection_pipeline:
            current_app.detection_pipeline.add_camera(camera.id, camera.source, camera.name)
        
        logging_manager.log_system_event("CAMERA_ADDED", f"Camera '{camera.name}' added by {current_user.username}")
        
        return jsonify(camera.to_dict()), 201

@cameras_bp.route('/api/cameras/<int:camera_id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
def api_camera(camera_id):
    """Get, update, or delete a camera"""
    camera = Camera.query.get_or_404(camera_id)
    
    if not current_user.is_admin and not current_user.has_camera_access(camera_id):
        return jsonify({'error': 'Access denied'}), 403
    
    if request.method == 'GET':
        return jsonify(camera.to_dict())
    
    elif request.method == 'PUT':
        if not current_user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        data = request.get_json()
        old_source = camera.source
        
        camera.name = data.get('name', camera.name)
        camera.location = data.get('location', camera.location)
        camera.is_active = data.get('is_active', camera.is_active)
        
        new_source = data.get('source')
        if new_source and new_source != old_source:
            camera.source = new_source
            if hasattr(current_app, 'detection_pipeline') and current_app.detection_pipeline:
                current_app.detection_pipeline.remove_camera(camera_id)
                current_app.detection_pipeline.add_camera(camera_id, new_source, camera.name)
            logging_manager.log_camera_event(camera.name, "SOURCE_UPDATED", f"New source: {new_source}")
        
        db.session.commit()
        logging_manager.log_camera_event(camera.name, "UPDATED", f"Updated by {current_user.username}")
        return jsonify(camera.to_dict())
    
    elif request.method == 'DELETE':
        if not current_user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        if hasattr(current_app, 'detection_pipeline') and current_app.detection_pipeline:
            current_app.detection_pipeline.remove_camera(camera_id)
        db.session.delete(camera)
        db.session.commit()
        
        logging_manager.log_system_event("CAMERA_DELETED", f"Camera '{camera.name}' deleted by {current_user.username}")
        
        return jsonify({'success': True})

@cameras_bp.route('/api/detection/global/start', methods=['POST'])
@login_required
def api_start_global_detection():
    if not current_user.is_admin:
        return jsonify({'error': 'Admin access required'}), 403
    return jsonify({'error': 'Global detection is disabled for performance optimization (8GB RAM / 1-Camera limit)'}), 403

@cameras_bp.route('/api/detection/global/stop', methods=['POST'])
@login_required
def api_stop_global_detection():
    if not current_user.is_admin:
        return jsonify({'error': 'Admin access required'}), 403
    
    if hasattr(current_app, 'detection_pipeline') and current_app.detection_pipeline:
        current_app.detection_pipeline.stop_global_detection()
    
    return jsonify({'success': True, 'message': 'Global detection stopped'})

@cameras_bp.route('/api/detection/<int:camera_id>/start', methods=['POST'])
@login_required
def api_start_detection(camera_id):
    camera = Camera.query.get_or_404(camera_id)
    
    if not current_user.is_admin and not current_user.has_camera_access(camera_id):
        return jsonify({'error': 'Access denied'}), 403
    
    data = request.get_json() or {}
    models = data.get('models')
    
    if not current_user.is_admin and models:
        allowed_models = []
        for model in models:
            if current_user.has_detection_permission(camera_id, model):
                allowed_models.append(model)
        models = allowed_models
    
    # Enforce 1-camera limit
    active_cameras = Camera.query.filter_by(detection_enabled=True).all()
    for active_cam in active_cameras:
        if active_cam.id != camera_id:
            if hasattr(current_app, 'detection_pipeline') and current_app.detection_pipeline:
                current_app.detection_pipeline.stop_detection(active_cam.id)
            active_cam.detection_enabled = False
            logging_manager.log_camera_event(active_cam.name, "DETECTION_STOPPED", "Automatic stop due to 1-camera limit")

    if hasattr(current_app, 'detection_pipeline') and current_app.detection_pipeline:
        current_app.detection_pipeline.start_detection(camera_id, models)
    camera.detection_enabled = True
    camera.set_active_models(models or [])
    db.session.commit()
    
    return jsonify({'success': True, 'message': f'Detection started for {camera.name}'})

@cameras_bp.route('/api/detection/<int:camera_id>/stop', methods=['POST'])
@login_required
def api_stop_detection(camera_id):
    camera = Camera.query.get_or_404(camera_id)
    
    if not current_user.is_admin and not current_user.has_camera_access(camera_id):
        return jsonify({'error': 'Access denied'}), 403
    
    if hasattr(current_app, 'detection_pipeline') and current_app.detection_pipeline:
        current_app.detection_pipeline.stop_detection(camera_id)
    camera.detection_enabled = False
    db.session.commit()
    
    return jsonify({'success': True, 'message': f'Detection stopped for {camera.name}'})

@cameras_bp.route('/api/recording/<int:camera_id>/start', methods=['POST'])
@login_required
def api_start_recording(camera_id):
    camera = Camera.query.get_or_404(camera_id)
    if not current_user.is_admin and not current_user.has_camera_access(camera_id):
        return jsonify({'error': 'Access denied'}), 403
    
    file_path = None
    if hasattr(current_app, 'detection_pipeline') and current_app.detection_pipeline:
        file_path = current_app.detection_pipeline.start_recording(camera_id)
    
    if file_path:
        camera.recording_enabled = True
        db.session.commit()
        return jsonify({'success': True, 'file_path': file_path})
    
    return jsonify({'error': 'Failed to start recording'}), 500

@cameras_bp.route('/api/recording/<int:camera_id>/stop', methods=['POST'])
@login_required
def api_stop_recording(camera_id):
    camera = Camera.query.get_or_404(camera_id)
    if not current_user.is_admin and not current_user.has_camera_access(camera_id):
        return jsonify({'error': 'Access denied'}), 403
    
    file_path = None
    if hasattr(current_app, 'detection_pipeline') and current_app.detection_pipeline:
        file_path = current_app.detection_pipeline.stop_recording(camera_id)
    camera.recording_enabled = False
    db.session.commit()
    
    return jsonify({'success': True, 'file_path': file_path})

@cameras_bp.route('/api/alert/manual/<int:camera_id>', methods=['POST'])
@login_required
def api_send_manual_alert(camera_id):
    camera = Camera.query.get_or_404(camera_id)
    if not current_user.is_admin and not current_user.has_camera_access(camera_id):
        return jsonify({'error': 'Access denied'}), 403
    
    data = request.get_json()
    message = data.get('message', 'Manual alert triggered')
    
    if hasattr(current_app, 'alert_manager') and current_app.alert_manager:
        current_app.alert_manager.send_manual_alert(
            camera_id,
            camera.name,
            message,
            current_user.email or current_user.username
        )
    
    return jsonify({'success': True, 'message': 'Alert sent'})

@cameras_bp.route('/api/zones/<int:camera_id>', methods=['GET'])
@login_required
def api_get_zones(camera_id):
    from models import RestrictedZone
    zones = RestrictedZone.query.filter_by(camera_id=camera_id).all()
    return jsonify({'success': True, 'zones': [zone.to_dict() for zone in zones]})

@cameras_bp.route('/api/zones/<int:camera_id>', methods=['POST'])
@login_required
def api_create_zone(camera_id):
    from models import RestrictedZone
    data = request.json
    try:
        zone = RestrictedZone(
            camera_id=camera_id,
            name=data.get('name', 'Restricted Zone'),
            coordinates=json.dumps(data['coordinates']),
            enabled=data.get('enabled', True)
        )
        db.session.add(zone)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Zone created successfully', 'zone': zone.to_dict()})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@cameras_bp.route('/api/zones/<int:zone_id>', methods=['PUT'])
@login_required
def api_update_zone(zone_id):
    from models import RestrictedZone
    zone = RestrictedZone.query.get_or_404(zone_id)
    data = request.json
    try:
        if 'name' in data:
            zone.name = data['name']
        if 'coordinates' in data:
            zone.coordinates = json.dumps(data['coordinates'])
        if 'enabled' in data:
            zone.enabled = data['enabled']
        db.session.commit()
        return jsonify({'success': True, 'message': 'Zone updated successfully', 'zone': zone.to_dict()})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@cameras_bp.route('/api/zones/<int:zone_id>', methods=['DELETE'])
@login_required
def api_delete_zone(zone_id):
    from models import RestrictedZone
    zone = RestrictedZone.query.get_or_404(zone_id)
    try:
        db.session.delete(zone)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Zone deleted successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400
