from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from models import User, Camera, Permission, PermissionRequest, db
from sqlalchemy.orm import selectinload
from logging_manager import get_logging_manager
from datetime import datetime
from config import DETECTION_MODELS

admin_bp = Blueprint('admin', __name__)
logging_manager = get_logging_manager()

@admin_bp.route('/admin')
@login_required
def admin_panel():
    """Admin panel"""
    if not current_user.is_admin:
        return "Access denied", 403
    
    users = User.query.all()
    cameras = Camera.query.all()
    # Eager load relationships to avoid lazy loading errors in template
    permissions = Permission.query.options(
        selectinload(Permission.user),
        selectinload(Permission.camera)
    ).all()
    
    # Convert to dictionaries for JSON serialization in template
    users_json = [user.to_dict() for user in users]
    cameras_json = [camera.to_dict() for camera in cameras]
    permissions_json = [perm.to_dict() for perm in permissions]
    
    return render_template('admin.html',
                         users=users,
                         cameras=cameras,
                         permissions=permissions,
                         users_json=users_json,
                         cameras_json=cameras_json,
                         permissions_json=permissions_json,
                         detection_models=DETECTION_MODELS)

@admin_bp.route('/api/users', methods=['GET', 'POST'])
@login_required
def api_users():
    """Get all users or create a new user"""
    if not current_user.is_admin:
        return jsonify({'error': 'Admin access required'}), 403
    
    if request.method == 'GET':
        users = User.query.all()
        return jsonify([user.to_dict() for user in users])
    
    elif request.method == 'POST':
        data = request.get_json()
        user = User(
            username=data['username'],
            email=data.get('email'),
            is_admin=data.get('is_admin', False),
            is_approved=data.get('is_approved', True)  # Default to approved when admin creates
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.commit()
        
        logging_manager.log_system_event("USER_CREATED", f"User '{user.username}' created by {current_user.username}")
        
        return jsonify(user.to_dict()), 201

@admin_bp.route('/api/permissions', methods=['POST'])
@login_required
def api_create_permission():
    """Create or update a permission"""
    if not current_user.is_admin:
        return jsonify({'error': 'Admin access required'}), 403
    
    data = request.get_json()
    
    permission = Permission.query.filter_by(
        user_id=data['user_id'],
        camera_id=data['camera_id']
    ).first()
    
    if permission:
        # Update existing
        permission.can_view = data.get('can_view', permission.can_view)
        permission.can_control = data.get('can_control', permission.can_control)
        permission.receive_alerts = data.get('receive_alerts', permission.receive_alerts)
        permission.set_allowed_models(data.get('allowed_models', []))
    else:
        # Create new
        permission = Permission(
            user_id=data['user_id'],
            camera_id=data['camera_id'],
            can_view=data.get('can_view', True),
            can_control=data.get('can_control', False),
            receive_alerts=data.get('receive_alerts', False)
        )
        permission.set_allowed_models(data.get('allowed_models', []))
        db.session.add(permission)
    
    db.session.commit()
    return jsonify(permission.to_dict())

@admin_bp.route('/api/users/<int:user_id>/approve', methods=['POST'])
@login_required
def api_approve_user(user_id):
    """Approve a pending user"""
    if not current_user.is_admin:
        return jsonify({'error': 'Admin access required'}), 403
    
    user = User.query.get_or_404(user_id)
    user.is_approved = True
    db.session.commit()
    
    logging_manager.log_system_event("USER_APPROVED", f"User '{user.username}' approved by {current_user.username}")
    return jsonify({'success': True, 'message': f'User {user.username} approved', 'user': user.to_dict()})

@admin_bp.route('/api/users/<int:user_id>/reject', methods=['POST'])
@login_required
def api_reject_user(user_id):
    """Reject/disable a user"""
    if not current_user.is_admin:
        return jsonify({'error': 'Admin access required'}), 403
    
    user = User.query.get_or_404(user_id)
    if user.is_admin:
        return jsonify({'error': 'Cannot reject admin users'}), 400
    
    user.is_approved = False
    db.session.commit()
    
    logging_manager.log_system_event("USER_REJECTED", f"User '{user.username}' rejected by {current_user.username}")
    return jsonify({'success': True, 'message': f'User {user.username} rejected'})

@admin_bp.route('/api/users/<int:user_id>/toggle-admin', methods=['POST'])
@login_required
def api_toggle_admin(user_id):
    """Toggle admin status for a user"""
    if not current_user.is_admin:
        return jsonify({'error': 'Admin access required'}), 403
    
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        return jsonify({'error': 'Cannot modify your own admin status'}), 400
    
    user.is_admin = not user.is_admin
    db.session.commit()
    
    action = "granted" if user.is_admin else "revoked"
    logging_manager.log_system_event("ADMIN_TOGGLED", f"Admin privileges {action} for '{user.username}' by {current_user.username}")
    return jsonify({'success': True, 'message': f'Admin status toggled', 'user': user.to_dict()})

@admin_bp.route('/api/users/<int:user_id>', methods=['PUT', 'DELETE'])
@login_required
def api_manage_user(user_id):
    """Update or delete a user"""
    if not current_user.is_admin:
        return jsonify({'error': 'Admin access required'}), 403
    
    user = User.query.get_or_404(user_id)
    if request.method == 'PUT':
        data = request.get_json()
        if 'email' in data:
            existing = User.query.filter_by(email=data['email']).first()
            if existing and existing.id != user.id:
                return jsonify({'error': 'Email already in use'}), 400
            user.email = data['email']
        if 'is_admin' in data and user.id != current_user.id:
            user.is_admin = data['is_admin']
        if 'is_approved' in data:
            user.is_approved = data['is_approved']
        db.session.commit()
        logging_manager.log_system_event("USER_UPDATED", f"User '{user.username}' updated by {current_user.username}")
        return jsonify({'success': True, 'user': user.to_dict()})
    elif request.method == 'DELETE':
        if user.id == current_user.id:
            return jsonify({'error': 'Cannot delete your own account'}), 400
        username = user.username
        db.session.delete(user)
        db.session.commit()
        logging_manager.log_system_event("USER_DELETED", f"User '{username}' deleted by {current_user.username}")
        return jsonify({'success': True, 'message': f'User {username} deleted'})

@admin_bp.route('/api/permissions/<int:permission_id>', methods=['GET', 'DELETE'])
@login_required
def api_manage_permission(permission_id):
    """Get or delete a specific permission"""
    if not current_user.is_admin:
        return jsonify({'error': 'Admin access required'}), 403
    
    permission = Permission.query.get_or_404(permission_id)
    if request.method == 'GET':
        return jsonify(permission.to_dict())
    elif request.method == 'DELETE':
        user = User.query.get(permission.user_id)
        camera = Camera.query.get(permission.camera_id)
        db.session.delete(permission)
        db.session.commit()
        logging_manager.log_system_event("PERMISSION_REVOKED", f"Permission revoked: User '{user.username}' - Camera '{camera.name}' by {current_user.username}")
        return jsonify({'success': True, 'message': 'Permission revoked'})

@admin_bp.route('/api/admin/permission-requests', methods=['GET'])
@login_required
def api_admin_permission_requests():
    """Admin: Get all pending permission requests"""
    if not current_user.is_admin:
        return jsonify({'error': 'Admin access required'}), 403
    
    status = request.args.get('status', 'pending')
    query = PermissionRequest.query.options(
        selectinload(PermissionRequest.user),
        selectinload(PermissionRequest.camera)
    )
    if status != 'all':
        query = query.filter_by(status=status)
    requests = query.order_by(PermissionRequest.created_at.desc()).all()
    return jsonify([req.to_dict() for req in requests])

@admin_bp.route('/api/admin/permission-requests/<int:request_id>/approve', methods=['POST'])
@login_required
def api_approve_permission_request(request_id):
    """Admin: Approve a permission request"""
    if not current_user.is_admin:
        return jsonify({'error': 'Admin access required'}), 403
    
    perm_request = PermissionRequest.query.get_or_404(request_id)
    if perm_request.status != 'pending':
        return jsonify({'error': 'Request has already been processed'}), 400
    
    data = request.get_json() or {}
    perm_request.status = 'approved'
    perm_request.admin_response = data.get('response', '')
    perm_request.reviewed_by = current_user.id
    perm_request.reviewed_at = datetime.now()
    
    requested = perm_request.get_requested_value()
    permission = Permission.query.filter_by(user_id=perm_request.user_id, camera_id=perm_request.camera_id).first()
    
    if permission:
        permission.can_view = requested.get('can_view', permission.can_view)
        permission.can_control = requested.get('can_control', permission.can_control)
        permission.receive_alerts = requested.get('receive_alerts', permission.receive_alerts)
    else:
        permission = Permission(
            user_id=perm_request.user_id,
            camera_id=perm_request.camera_id,
            can_view=requested.get('can_view', True),
            can_control=requested.get('can_control', False),
            receive_alerts=requested.get('receive_alerts', False)
        )
        db.session.add(permission)
    
    db.session.commit()
    logging_manager.log_system_event("PERMISSION_APPROVED", f"Admin '{current_user.username}' approved permission request #{request_id} for user '{perm_request.user.username}'")
    return jsonify({'success': True, 'message': 'Permission request approved', 'request': perm_request.to_dict()})

@admin_bp.route('/api/admin/permission-requests/<int:request_id>/reject', methods=['POST'])
@login_required
def api_reject_permission_request(request_id):
    """Admin: Reject a permission request"""
    if not current_user.is_admin:
        return jsonify({'error': 'Admin access required'}), 403
    
    perm_request = PermissionRequest.query.get_or_404(request_id)
    if perm_request.status != 'pending':
        return jsonify({'error': 'Request has already been processed'}), 400
    
    data = request.get_json() or {}
    perm_request.status = 'rejected'
    perm_request.admin_response = data.get('response', '')
    perm_request.reviewed_by = current_user.id
    perm_request.reviewed_at = datetime.now()
    
    db.session.commit()
    logging_manager.log_system_event("PERMISSION_REJECTED", f"Admin '{current_user.username}' rejected permission request #{request_id} for user '{perm_request.user.username}'")
    return jsonify({'success': True, 'message': 'Permission request rejected', 'request': perm_request.to_dict()})
