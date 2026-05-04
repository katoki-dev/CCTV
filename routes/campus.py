from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required, current_user
from models import Magazine, Event, EventRegistration, Post, User, db
from datetime import datetime
import os
import threading
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = 'static/uploads/portal'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_image(file, prefix=''):
    if file and allowed_file(file.filename):
        filename = secure_filename(f"{prefix}_{datetime.now().timestamp()}_{file.filename}")
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(path)
        return f"/static/uploads/portal/{filename}"
    return None

campus_bp = Blueprint('campus', __name__)


# ==================== Portal Page ====================

@campus_bp.route('/social')
@login_required
def portal_page():
    """Student/Faculty Campus Portal page"""
    return render_template('portal.html', user=current_user)


# ==================== Notification Helpers ====================

def create_notification(user_id, n_type, title, message, link=None):
    """Helper to create DB notification and emit socket event"""
    from models import Notification, db
    try:
        notif = Notification(user_id=user_id, type=n_type, title=title, message=message, link=link)
        db.session.add(notif)
        db.session.commit()
        
        from app import socketio
        socketio.emit('new_notification', notif.to_dict(), room=f"user_{user_id}")
        return notif
    except Exception as e:
        print(f"Error creating notification: {e}")
        return None


# ==================== Notification API ====================

@campus_bp.route('/api/notifications', methods=['GET'])
@login_required
def api_get_notifications():
    """Get unread notifications for current user"""
    from models import Notification
    notifs = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).limit(20).all()
    return jsonify([n.to_dict() for n in notifs])


@campus_bp.route('/api/notifications/mark_read', methods=['POST'])
@login_required
def api_mark_notifications_read():
    """Mark all notifications as read for current user"""
    from models import Notification, db
    Notification.query.filter_by(user_id=current_user.id, is_read=False).update({'is_read': True})
    db.session.commit()
    return jsonify({'success': True})


# ==================== Posts API ====================

@campus_bp.route('/api/posts', methods=['GET'])
@login_required
def api_get_posts():
    """Get all campus posts (newest first)"""
    posts = Post.query.order_by(Post.created_at.desc()).limit(50).all()
    return jsonify([p.to_dict() for p in posts])


@campus_bp.route('/api/posts', methods=['POST'])
@login_required
def api_create_post():
    """Create a new campus post"""
    data = request.get_json()
    content = data.get('content', '').strip()

    if not content:
        return jsonify({'error': 'Post content is required'}), 400
    if len(content) > 500:
        return jsonify({'error': 'Post must be under 500 characters'}), 400

    post = Post(content=content, author_id=current_user.id)
    db.session.add(post)
    db.session.commit()

    return jsonify(post.to_dict()), 201


# ==================== SOS Emergency API ====================

@campus_bp.route('/api/sos', methods=['POST'])
@login_required
def api_trigger_sos():
    """Trigger an emergency SOS alert"""
    from models import User
    # In a real app, this would notify security/police
    admins = User.query.filter_by(is_admin=True).all()
    
    alert_msg = f"EMERGENCY SOS triggered by {current_user.username}"
    
    # Notify all admins
    for admin in admins:
        create_notification(
            user_id=admin.id,
            n_type='emergency',
            title='🚨 SOS EMERGENCY ALERT',
            message=alert_msg,
            link='/dashboard'
        )
    
    # Broadcast global emergency event via socket
    try:
        from app import socketio
        socketio.emit('emergency_alert', {
            'user': current_user.username,
            'message': 'SOS Triggered!',
            'timestamp': datetime.now().isoformat()
        }, broadcast=True)
    except Exception as e:
        print(f"Socket emit failed: {e}")
    
    return jsonify({
        'success': True, 
        'message': 'Emergency services and admins have been notified. Please stay calm.'
    })


@campus_bp.route('/api/posts/<int:post_id>', methods=['DELETE'])
@login_required
def api_delete_post(post_id):
    """Delete a post (own posts or admin)"""
    post = Post.query.get_or_404(post_id)

    if post.author_id != current_user.id and not current_user.is_admin:
        return jsonify({'error': 'Permission denied'}), 403

    db.session.delete(post)
    db.session.commit()

    return jsonify({'success': True, 'message': 'Post deleted'})


# ==================== Comments API ====================

@campus_bp.route('/api/posts/<int:post_id>/comments', methods=['GET'])
@login_required
def api_get_comments(post_id):
    """Get discussion for a post"""
    from models import Comment
    comments = Comment.query.filter_by(post_id=post_id).order_by(Comment.created_at.asc()).all()
    return jsonify([c.to_dict() for c in comments])


@campus_bp.route('/api/posts/<int:post_id>/comments', methods=['POST'])
@login_required
def api_create_comment(post_id):
    """Add a comment to a post"""
    from models import Comment, Post, db
    data = request.get_json()
    content = data.get('content', '').strip()
    
    if not content:
        return jsonify({'error': 'Comment content is required'}), 400
        
    post = Post.query.get_or_404(post_id)
    comment = Comment(post_id=post_id, author_id=current_user.id, content=content)
    db.session.add(comment)
    db.session.commit()
    
    # Notify post author if it's not the same person
    if post.author_id != current_user.id:
        create_notification(
            user_id=post.author_id,
            n_type='comment',
            title='New Comment',
            message=f'{current_user.username} commented on your post: "{content[:30]}..."',
            link='/social#feed'
        )
    
    return jsonify(comment.to_dict()), 201


# ==================== Events API ====================

@campus_bp.route('/api/events', methods=['GET'])
@login_required
def api_events():
    """Get all events with registration status for current user"""
    events = Event.query.order_by(Event.date.desc()).all()
    result = []
    for e in events:
        event_data = e.to_dict()
        # Add registration count
        event_data['attendee_count'] = EventRegistration.query.filter_by(event_id=e.id).count()
        # Check if current user is registered
        reg = EventRegistration.query.filter_by(
            event_id=e.id, student_id=current_user.id
        ).first()
        event_data['is_registered'] = reg is not None
        event_data['qr_scanned'] = reg.qr_code_scanned if reg else False
        result.append(event_data)
    return jsonify(result)


@campus_bp.route('/api/events', methods=['POST'])
@login_required
def api_create_event():
    """Create a new event (Faculty/Admin only)"""
    if current_user.role not in ['faculty', 'admin']:
        return jsonify({'error': 'Permission denied'}), 403

    # Handle Multi-part form data instead of JSON for file upload
    title = request.form.get('title')
    date_str = request.form.get('date')
    
    if not title or not date_str:
        return jsonify({'error': 'Title and Date are required'}), 400

    try:
        image_url = None
        if 'image' in request.files:
            image_url = save_image(request.files['image'], 'event')

        event = Event(
            title=title,
            description=request.form.get('description', ''),
            location=request.form.get('location', ''),
            date=datetime.fromisoformat(date_str.replace('Z', '')),
            max_participants=int(request.form.get('max_participants', 100)),
            organizer_id=current_user.id,
            camera_id=request.form.get('camera_id'),
            image_url=image_url,
            status='upcoming'
        )

        db.session.add(event)
        db.session.commit()

        # WhatsApp Alert (New Request)
        if request.form.get('whatsapp_alert') == 'true':
            try:
                from config import WHATSAPP_PHONE_NUMBERS
                from alerts.whatsapp_service import WhatsAppService
                
                ws = WhatsAppService.get_instance()
                # Format a premium-looking message
                msg = (
                    f"📢 *NEW CAMPUS EVENT*\n\n"
                    f"*Title:* {event.title}\n"
                    f"*Date:* {event.date.strftime('%B %d, %Y at %I:%M %p')}\n"
                    f"*Location:* {event.location or 'TBD'}\n\n"
                    f"🔗 _Check the portal for full details and RSVP!_"
                )
                
                def send_alerts():
                    for phone in WHATSAPP_PHONE_NUMBERS:
                        ws.send_message(phone, msg)
                
                threading.Thread(target=send_alerts, daemon=True).start()
            except Exception as wa_err:
                print(f"WhatsApp alert failed: {wa_err}")

        try:
            from app import socketio
            socketio.emit('new_event', event.to_dict())
        except Exception:
            pass

        return jsonify({'success': True, 'message': 'Event created successfully', 'event': event.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400


@campus_bp.route('/api/events/<int:event_id>', methods=['GET'])
@login_required
def api_get_event(event_id):
    """Get single event details"""
    event = Event.query.get_or_404(event_id)
    event_data = event.to_dict()
    
    # Add registration status
    reg = EventRegistration.query.filter_by(
        event_id=event_id, student_id=current_user.id
    ).first()
    event_data['is_registered'] = reg is not None
    event_data['qr_scanned'] = reg.qr_code_scanned if reg else False
    event_data['attendee_count'] = EventRegistration.query.filter_by(event_id=event_id).count()
    
    # Add organizer name
    organizer = User.query.get(event.organizer_id)
    event_data['organizer_name'] = organizer.username if organizer else 'Unknown'
    
    return jsonify(event_data)


@campus_bp.route('/api/events/<int:event_id>', methods=['PUT'])
@login_required
def api_update_event(event_id):
    """Update event (Faculty/Admin only)"""
    if current_user.role not in ['faculty', 'admin']:
        return jsonify({'error': 'Permission denied'}), 403
    
    event = Event.query.get_or_404(event_id)
    
    # Check if form or json
    if request.form:
        if 'title' in request.form: event.title = request.form['title']
        if 'description' in request.form: event.description = request.form['description']
        if 'location' in request.form: event.location = request.form['location']
        if 'date' in request.form: event.date = datetime.fromisoformat(request.form['date'].replace('Z', ''))
        if 'max_participants' in request.form: event.max_participants = int(request.form['max_participants'])
        if 'camera_id' in request.form: event.camera_id = request.form['camera_id']
        if 'status' in request.form: event.status = request.form['status']
        if 'image' in request.files:
            event.image_url = save_image(request.files['image'], 'event')
    else:
        data = request.get_json()
        if 'title' in data: event.title = data['title']
        if 'description' in data: event.description = data['description']
        if 'location' in data: event.location = data['location']
        if 'date' in data: event.date = datetime.fromisoformat(data['date'].replace('Z', ''))
        if 'max_participants' in data: event.max_participants = data['max_participants']
        if 'camera_id' in data: event.camera_id = data['camera_id']
        if 'status' in data: event.status = data['status']
        
    db.session.commit()
    return jsonify(event.to_dict())
    
@campus_bp.route('/api/events/<int:event_id>', methods=['DELETE'])
@login_required
def api_delete_event(event_id):
    """Delete event (Faculty/Admin only)"""
    if current_user.role not in ['faculty', 'admin']:
        return jsonify({'error': 'Permission denied'}), 403
    
    event = Event.query.get_or_404(event_id)
    db.session.delete(event)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Event deleted'})


@campus_bp.route('/api/events/<int:event_id>/rsvp', methods=['POST'])
@login_required
def api_event_rsvp(event_id):
    """Register (RSVP) current user for an event"""
    event = Event.query.get_or_404(event_id)

    # Check if already registered
    existing = EventRegistration.query.filter_by(
        event_id=event_id, student_id=current_user.id
    ).first()
    if existing:
        return jsonify({'error': 'Already registered for this event'}), 400

    # Check capacity
    current_count = EventRegistration.query.filter_by(event_id=event_id).count()
    if current_count >= event.max_participants:
        return jsonify({'error': 'Event is at full capacity'}), 400

    reg = EventRegistration(
        event_id=event_id,
        student_id=current_user.id
    )
    db.session.add(reg)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': f'Successfully registered for {event.title}',
        'attendee_count': current_count + 1
    })


@campus_bp.route('/api/events/<int:event_id>/rsvp', methods=['DELETE'])
@login_required
def api_cancel_rsvp(event_id):
    """Cancel RSVP for an event"""
    reg = EventRegistration.query.filter_by(
        event_id=event_id, student_id=current_user.id
    ).first()

    if not reg:
        return jsonify({'error': 'Not registered for this event'}), 404

    db.session.delete(reg)
    db.session.commit()

    count = EventRegistration.query.filter_by(event_id=event_id).count()
    return jsonify({
        'success': True,
        'message': 'RSVP cancelled',
        'attendee_count': count
    })


@campus_bp.route('/api/events/<int:event_id>/attendees', methods=['GET'])
@login_required
def api_event_attendees(event_id):
    """List attendees for an event (Faculty/Admin only)"""
    if current_user.role not in ['faculty', 'admin']:
        return jsonify({'error': 'Permission denied'}), 403

    registrations = EventRegistration.query.filter_by(event_id=event_id).all()
    attendees = []
    for reg in registrations:
        user = User.query.get(reg.student_id)
        attendees.append({
            'id': reg.id,
            'student_id': reg.student_id,
            'username': user.username if user else 'Unknown',
            'email': user.email if user else '',
            'qr_scanned': reg.qr_code_scanned,
            'registered_at': reg.registered_at.isoformat()
        })

    return jsonify(attendees)


@campus_bp.route('/api/events/<int:event_id>/scan_qr', methods=['POST'])
@login_required
def api_scan_qr(event_id):
    """Scan a student QR code at event entrance (Faculty/Admin only)"""
    if current_user.role not in ['faculty', 'admin']:
        return jsonify({'error': 'Permission denied'}), 403

    data = request.get_json()
    student_id = data.get('student_id')

    if not student_id:
        return jsonify({'error': 'Student ID is required'}), 400

    reg = EventRegistration.query.filter_by(
        event_id=event_id, student_id=student_id
    ).first()

    if not reg:
        return jsonify({'error': 'Student is not registered for this event'}), 404

    if reg.qr_code_scanned:
        return jsonify({'message': 'QR code already scanned — student already checked in'}), 200

    reg.qr_code_scanned = True
    db.session.commit()

    student = User.query.get(student_id)
    return jsonify({
        'success': True,
        'message': f'{student.username} checked in successfully!'
    })


# ==================== Magazines API ====================

@campus_bp.route('/api/magazines', methods=['GET'])
@login_required
def api_magazines():
    """List magazines (filtered by status and role)"""
    if current_user.role == 'student':
        magazines = Magazine.query.filter(
            (Magazine.status == 'approved') | (Magazine.author_id == current_user.id)
        ).order_by(Magazine.created_at.desc()).all()
    elif current_user.role in ['faculty', 'admin']:
        magazines = Magazine.query.order_by(Magazine.created_at.desc()).all()
    else:
        magazines = Magazine.query.filter_by(status='approved').order_by(Magazine.created_at.desc()).all()

    return jsonify([m.to_dict() for m in magazines])


@campus_bp.route('/api/magazines', methods=['POST'])
@login_required
def api_submit_magazine():
    """Student magazine submission with dual image support"""
    title = request.form.get('title', '').strip()
    description = request.form.get('description', '').strip()
    content = request.form.get('content', '').strip()

    if not title or not content:
        return jsonify({'error': 'Title and content are required'}), 400

    image_url = None
    if 'image' in request.files:
        image_url = save_image(request.files['image'], 'mag_poster')

    content_image_url = None
    if 'content_image' in request.files:
        content_image_url = save_image(request.files['content_image'], 'mag_content')

    magazine = Magazine(
        title=title,
        description=description,
        content=content,
        author_id=current_user.id,
        image_url=image_url,
        content_image_url=content_image_url,
        status='pending'
    )

    db.session.add(magazine)
    db.session.commit()

    return jsonify(magazine.to_dict()), 201


@campus_bp.route('/api/magazines/<int:magazine_id>/approve', methods=['POST'])
@login_required
def api_approve_magazine(magazine_id):
    """Faculty approval of magazine"""
    if current_user.role not in ['faculty', 'admin']:
        return jsonify({'error': 'Permission denied'}), 403

    magazine = Magazine.query.get_or_404(magazine_id)
    magazine.status = 'approved'
    magazine.faculty_id = current_user.id
    db.session.commit()

    # Notify student
    create_notification(
        user_id=magazine.author_id,
        n_type='magazine_approval',
        title='Article Approved! 🎉',
        message=f'Your article "{magazine.title}" has been approved by {current_user.username}.',
        link='/social#magazines'
    )

    return jsonify(magazine.to_dict())


@campus_bp.route('/api/magazines/<int:magazine_id>/reject', methods=['POST'])
@login_required
def api_reject_magazine(magazine_id):
    """Faculty rejection of magazine"""
    if current_user.role not in ['faculty', 'admin']:
        return jsonify({'error': 'Permission denied'}), 403

    magazine = Magazine.query.get_or_404(magazine_id)
    magazine.status = 'rejected'
    magazine.faculty_id = current_user.id
    db.session.commit()

    # Notify student
    create_notification(
        user_id=magazine.author_id,
        n_type='magazine_approval',
        title='Article Update',
        message=f'Your article "{magazine.title}" was not approved at this time.',
        link='/social#magazines'
    )

    return jsonify(magazine.to_dict())


@campus_bp.route('/api/magazines/<int:magazine_id>', methods=['GET'])
@login_required
def api_get_magazine(magazine_id):
    """Get single magazine content"""
    magazine = Magazine.query.get_or_404(magazine_id)
    
    # Check permissions (only approved or author or faculty)
    if magazine.status != 'approved' and magazine.author_id != current_user.id and current_user.role not in ['faculty', 'admin']:
        return jsonify({'error': 'Permission denied'}), 403
        
    return jsonify(magazine.to_dict())


@campus_bp.route('/api/magazines/<int:magazine_id>', methods=['DELETE'])
@login_required
def api_delete_magazine(magazine_id):
    """Delete magazine submission (Author or Admin only)"""
    magazine = Magazine.query.get_or_404(magazine_id)
    
    if magazine.author_id != current_user.id and not current_user.is_admin:
        return jsonify({'error': 'Permission denied'}), 403
        
    db.session.delete(magazine)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Magazine article deleted'})
