"""
Enhanced API endpoints for alert management and clip playback
Add these to api_chatbot.py
"""
from flask import Blueprint, jsonify, request, current_app, send_file
from flask_login import login_required, current_user
from models import Alert, DetectionLog, db
from datetime import datetime
import os

# Alert Acknowledgment Endpoint
@chatbot_bp.route('/api/alerts/<int:alert_id>/acknowledge', methods=['POST'])
@login_required
def acknowledge_alert(alert_id):
    """
    Acknowledge an alert
    
    POST /api/alerts/123/acknowledge
    Body: {"note": "Reviewed - false alarm"}
    """
    try:
        alert = Alert.query.get(alert_id)
        
        if not alert:
            return jsonify({
                'success': False,
                'error': f'Alert {alert_id} not found'
            }), 404
        
        # Check permissions (users can only acknowledge alerts for cameras they can view)
        if not current_user.is_admin:
            from models import Permission
            permission = Permission.query.filter_by(
                user_id=current_user.id,
                camera_id=alert.camera_id,
                can_view=True
            ).first()
            
            if not permission:
                return jsonify({
                    'success': False,
                    'error': 'You do not have permission to acknowledge this alert'
                }), 403
        
        # Update alert
        data = request.get_json() or {}
        alert.acknowledged = True
        alert.acknowledged_by = current_user.id
        alert.acknowledged_at = datetime.now()
        alert.acknowledgment_note = data.get('note', '')
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Alert {alert_id} acknowledged',
            'alert': {
                'id': alert.id,
                'acknowledged': alert.acknowledged,
                'acknowledged_at': alert.acknowledged_at.isoformat(),
                'acknowledged_by': current_user.username
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# Clip Playback Endpoint
@chatbot_bp.route('/api/clips/<int:detection_id>')
@login_required
def get_detection_clip(detection_id):
    """
    Get video clip for a detection
    
    GET /api/clips/456
    """
    try:
        detection = DetectionLog.query.get(detection_id)
        
        if not detection:
            return jsonify({
                'success': False,
                'error': f'Detection {detection_id} not found'
            }), 404
        
        # Check permissions
        if not current_user.is_admin:
            from models import Permission
            permission = Permission.query.filter_by(
                user_id=current_user.id,
                camera_id=detection.camera_id,
                can_view=True
            ).first()
            
            if not permission:
                return jsonify({
                    'success': False,
                    'error': 'You do not have permission to view this clip'
                }), 403
        
        # Get clip path (assume stored in recordings directory)
        clip_filename = f"detection_{detection_id}.mp4"
        clip_path = os.path.join('recordings', clip_filename)
        
        if not os.path.exists(clip_path):
            # Try to generate from detection pipeline
            detection_pipeline = getattr(current_app, 'detection_pipeline', None)
            if detection_pipeline and hasattr(detection_pipeline, 'get_recent_clip'):
                clip_data = detection_pipeline.get_recent_clip(
                    detection.camera_id,
                    detection.timestamp
                )
                if clip_data:
                    return jsonify({
                        'success': True,
                        'clip_url': f'/api/clips/{detection_id}/stream',
                        'timestamp': detection.timestamp.isoformat(),
                        'available': True
                    })
            
            return jsonify({
                'success': False,
                'error': 'Clip file not found',
                'note': 'Clip may have been deleted or not recorded'
            }), 404
        
        # Return clip file
        return send_file(
            clip_path,
            mimetype='video/mp4',
            as_attachment=True,
            download_name=clip_filename
        )
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# Multi-Camera Analysis Endpoint
@chatbot_bp.route('/api/chatbot/analyze_all_cameras', methods=['POST'])
@login_required
def analyze_all_cameras():
    """
    Analyze all accessible cameras simultaneously
    
    POST /api/chatbot/analyze_all_cameras
    Body: {"query": "Are there any people visible?"}
    """
    try:
        data = request.get_json()
        query = data.get('query', 'What do you see?')
        
        # Get accessible cameras
        from models import Camera, Permission
        
        if current_user.is_admin:
            cameras = Camera.query.filter_by(enabled=True).all()
        else:
            # Get cameras user has permission to view
            permissions = Permission.query.filter_by(
                user_id=current_user.id,
                can_view=True
            ).all()
            camera_ids = [p.camera_id for p in permissions]
            cameras = Camera.query.filter(
                Camera.id.in_(camera_ids),
                Camera.enabled == True
            ).all()
        
        if not cameras:
            return jsonify({
                'success': False,
                'error': 'No accessible cameras found'
            })
        
        # Get chatbot and analyze each camera
        chatbot = getattr(current_app, 'chatbot_service', None)
        if not chatbot or not chatbot.vlm_analyzer:
            return jsonify({
                'success': False,
                'error': 'VLM not available'
            }), 503
        
        results = []
        for camera in cameras:
            try:
                # Analyze camera
                analysis = chatbot.vlm_analyzer.analyze_frame(
                    camera_id=camera.id,
                    prompt=query,
                    flask_app=current_app
                )
                
                results.append({
                    'camera_id': camera.id,
                    'camera_name': camera.name,
                    'success': analysis.get('success', False),
                    'analysis': analysis.get('analysis', 'No analysis available')
                })
            except Exception as e:
                results.append({
                    'camera_id': camera.id,
                    'camera_name': camera.name,
                    'success': False,
                    'error': str(e)
                })
        
        return jsonify({
            'success': True,
            'query': query,
            'cameras_analyzed': len(results),
            'results': results
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# Usage examples in chatbot_service.py:
# 
# def _analyze_query_intent(self, message, flask_app, current_user):
#     # Check for alert acknowledgment
#     if re.search(r'acknowledge|dismiss|clear.*alert (\d+)', message.lower()):
#         alert_id = re.search(r'alert (\d+)', message).group(1)
#         # Call API internally or return instruction
#         return {
#             'query_type': 'alert_acknowledgment',
#             'alert_id': alert_id
#         }
#     
#     # Check for clip playback
#     if re.search(r'show|play.*clip|detection (\d+)', message.lower()):
#         detection_id = re.search(r'(?:clip|detection) (\d+)', message).group(1)
#         return {
#             'query_type': 'clip_playback',
#             'detection_id': detection_id
#         }
