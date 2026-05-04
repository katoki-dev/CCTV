"""
CEMSS - Campus Event management and Surveillance System
Database Models
"""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import json

db = SQLAlchemy()


class User(UserMixin, db.Model):
    """User model for authentication and authorization"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True, index=True)
    phone_number = db.Column(db.String(20), nullable=True)  # WhatsApp number with country code
    is_admin = db.Column(db.Boolean, default=False, index=True)
    role = db.Column(db.String(20), default='student', index=True)  # student, faculty, admin
    is_approved = db.Column(db.Boolean, default=False, index=True)  # User registration approval
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # Relationships
    permissions = db.relationship('Permission', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verify password"""
        return check_password_hash(self.password_hash, password)
    
    def has_camera_access(self, camera_id):
        """Check if user has access to a specific camera"""
        if self.is_admin:
            return True
        return Permission.query.filter_by(
            user_id=self.id,
            camera_id=camera_id,
            can_view=True
        ).first() is not None
    
    def has_detection_permission(self, camera_id, model_name):
        """Check if user can use a specific detection model on a camera"""
        if self.is_admin:
            return True
        permission = Permission.query.filter_by(
            user_id=self.id,
            camera_id=camera_id
        ).first()
        if not permission:
            return False
        
        allowed_models = json.loads(permission.allowed_models) if permission.allowed_models else []
        return model_name in allowed_models
    
    def should_receive_alert(self, camera_id, model_name):
        """Check if user should receive alerts for a camera/model combination"""
        # User needs a phone number to receive WhatsApp alerts
        if not self.phone_number:
            return False
        
        permission = Permission.query.filter_by(
            user_id=self.id,
            camera_id=camera_id
        ).first()
        if not permission or not permission.receive_alerts:
            return False
        
        allowed_models = json.loads(permission.allowed_models) if permission.allowed_models else []
        return model_name in allowed_models
    
    def to_dict(self):
        """Convert user to dictionary"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'phone_number': self.phone_number,
            'is_admin': self.is_admin,
            'role': self.role,
            'is_approved': self.is_approved,
            'created_at': self.created_at.isoformat()
        }


class Camera(db.Model):
    """Camera model for camera sources"""
    __tablename__ = 'cameras'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    source = db.Column(db.String(500), nullable=False, unique=True)  # RTSP URL or device index
    location = db.Column(db.String(200))
    is_active = db.Column(db.Boolean, default=True, index=True)
    detection_enabled = db.Column(db.Boolean, default=False)
    recording_enabled = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # Active detection models (JSON string)
    active_models = db.Column(db.Text, default='[]')
    
    # Relationships
    permissions = db.relationship('Permission', backref='camera', lazy='dynamic', cascade='all, delete-orphan')
    detection_logs = db.relationship('DetectionLog', backref='camera', lazy='dynamic', cascade='all, delete-orphan')
    alerts = db.relationship('Alert', backref='camera', lazy='dynamic', cascade='all, delete-orphan')
    restricted_zones = db.relationship('RestrictedZone', backref='camera', lazy='dynamic', cascade='all, delete-orphan')
    
    def get_active_models(self):
        """Get list of active detection models"""
        return json.loads(self.active_models) if self.active_models else []
    
    def set_active_models(self, models):
        """Set active detection models"""
        self.active_models = json.dumps(models)
    
    def to_dict(self):
        """Convert camera to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'source': self.source,
            'location': self.location,
            'is_active': self.is_active,
            'detection_enabled': self.detection_enabled,
            'recording_enabled': self.recording_enabled,
            'active_models': self.get_active_models(),
            'created_at': self.created_at.isoformat()
        }


class Permission(db.Model):
    """Permission model for user-camera access control"""
    __tablename__ = 'permissions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    camera_id = db.Column(db.Integer, db.ForeignKey('cameras.id'), nullable=False)
    can_view = db.Column(db.Boolean, default=True)
    can_control = db.Column(db.Boolean, default=False)
    receive_alerts = db.Column(db.Boolean, default=False)
    allowed_models = db.Column(db.Text, default='[]')  # JSON list of allowed model names
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # Unique constraint
    __table_args__ = (db.UniqueConstraint('user_id', 'camera_id', name='_user_camera_uc'),)
    
    def get_allowed_models(self):
        """Get list of allowed models"""
        return json.loads(self.allowed_models) if self.allowed_models else []
    
    def set_allowed_models(self, models):
        """Set allowed models"""
        self.allowed_models = json.dumps(models)
    
    def to_dict(self):
        """Convert permission to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'camera_id': self.camera_id,
            'can_view': self.can_view,
            'can_control': self.can_control,
            'receive_alerts': self.receive_alerts,
            'allowed_models': self.get_allowed_models()
        }


class DetectionLog(db.Model):
    """Detection log model for recording all detection events"""
    __tablename__ = 'detection_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    camera_id = db.Column(db.Integer, db.ForeignKey('cameras.id'), nullable=False, index=True)
    model_name = db.Column(db.String(50), nullable=False, index=True)
    confidence = db.Column(db.Float, nullable=False)
    detection_data = db.Column(db.Text)  # JSON data with bounding boxes, etc.
    timestamp = db.Column(db.DateTime, default=datetime.now, index=True)
    video_clip_path = db.Column(db.String(500))
    
    # Phase 1: Severity scoring
    severity_score = db.Column(db.Integer, default=0)  # 1-10 severity score
    severity_level = db.Column(db.String(10))  # LOW, MEDIUM, HIGH, CRITICAL
    
    # Composite indexes for common query patterns
    __table_args__ = (
        db.Index('idx_camera_timestamp', 'camera_id', 'timestamp'),
        db.Index('idx_camera_model_timestamp', 'camera_id', 'model_name', 'timestamp'),
        db.Index('idx_severity_timestamp', 'severity_level', 'timestamp'),
    )
    
    def to_dict(self):
        """Convert detection log to dictionary"""
        return {
            'id': self.id,
            'camera_id': self.camera_id,
            'camera_name': self.camera.name if self.camera else 'Unknown',
            'model_name': self.model_name,
            'confidence': self.confidence,
            'detection_data': json.loads(self.detection_data) if self.detection_data else {},
            'timestamp': self.timestamp.isoformat(),
            'video_clip_path': self.video_clip_path,
            'severity_score': self.severity_score,
            'severity_level': self.severity_level
        }


class Alert(db.Model):
    """Alert model for tracking sent alerts"""
    __tablename__ = 'alerts'
    
    id = db.Column(db.Integer, primary_key=True)
    camera_id = db.Column(db.Integer, db.ForeignKey('cameras.id'), nullable=False, index=True)
    detection_log_id = db.Column(db.Integer, db.ForeignKey('detection_logs.id'))
    model_name = db.Column(db.String(50), nullable=False, index=True)
    recipient_emails = db.Column(db.Text)  # JSON list of emails
    subject = db.Column(db.String(200))
    message = db.Column(db.Text)
    video_clip_path = db.Column(db.String(500))
    sent_at = db.Column(db.DateTime, default=datetime.now, index=True)
    is_manual = db.Column(db.Boolean, default=False)  # True if manually triggered
    
    # Phase 1: Alert enhancements
    severity_score = db.Column(db.Integer, default=0)  # 1-10 severity score
    priority_level = db.Column(db.String(10), default='MEDIUM')  # LOW, MEDIUM, HIGH, CRITICAL
    aggregated_count = db.Column(db.Integer, default=1)  # Number of detections aggregated
    detection_ids = db.Column(db.Text)  # JSON array of DetectionLog IDs in this alert
    
    # Composite indexes for common query patterns
    __table_args__ = (
        db.Index('idx_camera_sent_at', 'camera_id', 'sent_at'),
        db.Index('idx_priority_sent_at', 'priority_level', 'sent_at'),
    )
    
    def to_dict(self):
        """Convert alert to dictionary"""
        return {
            'id': self.id,
            'camera_id': self.camera_id,
            'camera_name': self.camera.name if self.camera else 'Unknown',
            'model_name': self.model_name,
            'recipient_emails': json.loads(self.recipient_emails) if self.recipient_emails else [],
            'subject': self.subject,
            'sent_at': self.sent_at.isoformat(),
            'is_manual': self.is_manual,
            'video_clip_path': self.video_clip_path,
            'severity_score': self.severity_score,
            'priority_level': self.priority_level,
            'aggregated_count': self.aggregated_count,
            'detection_ids': json.loads(self.detection_ids) if self.detection_ids else []
        }


class RestrictedZone(db.Model):
    """Restricted zone model for area-based person detection alerts"""
    __tablename__ = 'restricted_zones'
    
    id = db.Column(db.Integer, primary_key=True)
    camera_id = db.Column(db.Integer, db.ForeignKey('cameras.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    coordinates = db.Column(db.Text, nullable=False)  # JSON array of [x, y] polygon points
    enabled = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    def get_coordinates(self):
        """Get polygon coordinates as Python list"""
        return json.loads(self.coordinates) if self.coordinates else []
    
    def set_coordinates(self, coords):
        """Set polygon coordinates from Python list"""
        self.coordinates = json.dumps(coords)
    
    def to_dict(self):
        """Convert zone to dictionary"""
        return {
            'id': self.id,
            'camera_id': self.camera_id,
            'name': self.name,
            'coordinates': self.get_coordinates(),
            'enabled': self.enabled,
            'created_at': self.created_at.isoformat()
        }


class VideoRecording(db.Model):
    """Video recording model for tracking all recorded video clips"""
    __tablename__ = 'video_recordings'
    
    id = db.Column(db.Integer, primary_key=True)
    camera_id = db.Column(db.Integer, db.ForeignKey('cameras.id'), nullable=False, index=True)
    filename = db.Column(db.String(255), nullable=False)
    filepath = db.Column(db.String(500), nullable=False)
    recording_type = db.Column(db.String(20), nullable=False, index=True)  # 'detection' or 'continuous'
    start_time = db.Column(db.DateTime, nullable=False, index=True)
    end_time = db.Column(db.DateTime)
    duration = db.Column(db.Float)  # Duration in seconds
    file_size = db.Column(db.Integer)  # File size in bytes
    detection_log_id = db.Column(db.Integer, db.ForeignKey('detection_logs.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now, index=True)
    
    # Relationships
    camera = db.relationship('Camera', backref=db.backref('recordings', lazy='dynamic'))
    detection_log = db.relationship('DetectionLog', backref=db.backref('recording', uselist=False))
    
    # Composite indexes for common query patterns
    __table_args__ = (
        db.Index('idx_camera_type_created', 'camera_id', 'recording_type', 'created_at'),
        db.Index('idx_type_created', 'recording_type', 'created_at'),
    )
    
    def to_dict(self):
        """Convert video recording to dictionary"""
        result = {
            'id': self.id,
            'camera_id': self.camera_id,
            'camera_name': self.camera.name if self.camera else 'Unknown',
            'filename': self.filename,
            'filepath': self.filepath,
            'recording_type': self.recording_type,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration': self.duration,
            'file_size': self.file_size,
            'detection_log_id': self.detection_log_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
        
        # Include detection log info if linked
        if self.detection_log:
            result['detection_info'] = {
                'model_name': self.detection_log.model_name,
                'confidence': self.detection_log.confidence,
                'severity_level': self.detection_log.severity_level,
                'severity_score': self.detection_log.severity_score,
                'timestamp': self.detection_log.timestamp.isoformat()
            }
        
        return result


# ==================== Phase 1 Models ====================

class SeverityRule(db.Model):
    """Severity scoring rules for detection events"""
    __tablename__ = 'severity_rules'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    model_name = db.Column(db.String(50))  # NULL = applies to all
    zone_id = db.Column(db.Integer, db.ForeignKey('restricted_zones.id'))  # NULL = any zone
    time_window_start = db.Column(db.Time)  # NULL = any time
    time_window_end = db.Column(db.Time)
    severity_score = db.Column(db.Integer, nullable=False)  # 1-10
    is_active = db.Column(db.Boolean, default=True, index=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    def to_dict(self):
        """Convert severity rule to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'model_name': self.model_name,
            'zone_id': self.zone_id,
            'time_window_start': self.time_window_start.isoformat() if self.time_window_start else None,
            'time_window_end': self.time_window_end.isoformat() if self.time_window_end else None,
            'severity_score': self.severity_score,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat()
        }


class AlertRule(db.Model):
    """Configurable alert triggering rules"""
    __tablename__ = 'alert_rules'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    camera_id = db.Column(db.Integer, db.ForeignKey('cameras.id'))  # NULL = all cameras
    model_name = db.Column(db.String(50))  # NULL = all models
    min_severity = db.Column(db.Integer, default=1)  # Trigger only if severity >= this
    require_zone_violation = db.Column(db.Boolean, default=False)
    time_based = db.Column(db.Boolean, default=False) # Apply time-based severity boost
    cooldown_seconds = db.Column(db.Integer, default=60)
    is_active = db.Column(db.Boolean, default=True, index=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    def to_dict(self):
        """Convert alert rule to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'camera_id': self.camera_id,
            'model_name': self.model_name,
            'min_severity': self.min_severity,
            'require_zone_violation': self.require_zone_violation,
            'time_based': self.time_based,
            'cooldown_seconds': self.cooldown_seconds,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat()
        }


class AnalyticsCache(db.Model):
    """Pre-computed analytics data for performance"""
    __tablename__ = 'analytics_cache'
    
    id = db.Column(db.Integer, primary_key=True)
    cache_key = db.Column(db.String(200), unique=True, nullable=False, index=True)
    cache_type = db.Column(db.String(50), index=True)  # 'hourly', 'daily', 'weekly'
    data = db.Column(db.Text)  # JSON serialized data
    created_at = db.Column(db.DateTime, default=datetime.now)
    expires_at = db.Column(db.DateTime, index=True)
    
    def to_dict(self):
        """Convert analytics cache to dictionary"""
        return {
            'id': self.id,
            'cache_key': self.cache_key,
            'cache_type': self.cache_type,
            'data': json.loads(self.data) if self.data else {},
            'created_at': self.created_at.isoformat(),
            'expires_at': self.expires_at.isoformat() if self.expires_at else None
        }


class PermissionRequest(db.Model):
    """Permission change requests from users requiring admin approval"""
    __tablename__ = 'permission_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    camera_id = db.Column(db.Integer, db.ForeignKey('cameras.id'), nullable=False)
    request_type = db.Column(db.String(50), nullable=False)  # 'access', 'model', 'alert', 'control'
    requested_value = db.Column(db.Text)  # JSON with requested permissions
    reason = db.Column(db.Text)  # User's reason for the request
    status = db.Column(db.String(20), default='pending', index=True)  # pending, approved, rejected
    admin_response = db.Column(db.Text)  # Admin's reason for decision
    reviewed_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.now)
    reviewed_at = db.Column(db.DateTime)
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref=db.backref('permission_requests', lazy='dynamic'))
    camera = db.relationship('Camera', backref=db.backref('permission_requests', lazy='dynamic'))
    reviewer = db.relationship('User', foreign_keys=[reviewed_by])
    
    # Index for common queries
    __table_args__ = (
        db.Index('idx_user_status', 'user_id', 'status'),
        db.Index('idx_status_created', 'status', 'created_at'),
    )
    
    def get_requested_value(self):
        """Get requested value as Python object"""
        return json.loads(self.requested_value) if self.requested_value else {}
    
    def set_requested_value(self, value):
        """Set requested value from Python object"""
        self.requested_value = json.dumps(value)
    
    def to_dict(self):
        """Convert permission request to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.user.username if self.user else 'Unknown',
            'camera_id': self.camera_id,
            'camera_name': self.camera.name if self.camera else 'Unknown',
            'request_type': self.request_type,
            'requested_value': self.get_requested_value(),
            'reason': self.reason,
            'status': self.status,
            'admin_response': self.admin_response,
            'reviewed_by': self.reviewed_by,
            'reviewer_name': self.reviewer.username if self.reviewer else None,
            'created_at': self.created_at.isoformat(),
            'reviewed_at': self.reviewed_at.isoformat() if self.reviewed_at else None
        }


class AnalysisLog(db.Model):
    """Log of continuous VLM frame analysis"""
    __tablename__ = 'analysis_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    camera_id = db.Column(db.Integer, db.ForeignKey('cameras.id'), nullable=False, index=True)
    timestamp = db.Column(db.DateTime, default=datetime.now, index=True)
    summary = db.Column(db.Text, nullable=False)
    motion_detected = db.Column(db.Boolean, default=False)
    
    # Relationship
    camera = db.relationship('Camera', backref=db.backref('analysis_logs', lazy='dynamic'))

    def to_dict(self):
        return {
            'id': self.id,
            'camera_id': self.camera_id,
            'timestamp': self.timestamp.isoformat(),
            'summary': self.summary,
            'motion_detected': self.motion_detected
        }


class VLMAnalysis(db.Model):
    """VLM Analysis results for enhanced surveillance monitoring"""
    __tablename__ = 'vlm_analyses'
    
    id = db.Column(db.Integer, primary_key=True)
    camera_id = db.Column(db.Integer, db.ForeignKey('cameras.id'), nullable=False, index=True)
    detection_log_id = db.Column(db.Integer, db.ForeignKey('detection_logs.id'))  # Optional link to detection
    timestamp = db.Column(db.DateTime, default=datetime.now, index=True)
    
    # Tier 1 results (fast scan)
    tier1_threat_level = db.Column(db.String(10))  # LOW, MEDIUM, HIGH
    tier1_keywords = db.Column(db.Text)  # JSON array of keywords
    tier1_action = db.Column(db.String(20))  # MONITOR, INVESTIGATE, ALERT
    tier1_assessment = db.Column(db.Text)  # Full assessment text
    
    # Tier 2 results (detailed vision)
    tier2_triggered = db.Column(db.Boolean, default=False)
    tier2_analysis = db.Column(db.Text)  # Full visual analysis
    tier2_timestamp = db.Column(db.DateTime)  # When Tier 2 ran
    
    # Metadata
    detection_type = db.Column(db.String(50))  # Type of detection that triggered this
    processing_time_ms = db.Column(db.Integer)  # Total processing time
    
    # Relationships
    camera = db.relationship('Camera', backref=db.backref('vlm_analyses', lazy='dynamic'))
    detection_log = db.relationship('DetectionLog', backref=db.backref('vlm_analysis', uselist=False))
    
    # Indexes
    __table_args__ = (
        db.Index('idx_vlm_camera_timestamp', 'camera_id', 'timestamp'),
        db.Index('idx_vlm_threat_level', 'tier1_threat_level', 'timestamp'),
    )
    
    def get_tier1_keywords(self):
        """Get keywords as Python list"""
        return json.loads(self.tier1_keywords) if self.tier1_keywords else []
    
    def set_tier1_keywords(self, keywords):
        """Set keywords from Python list"""
        self.tier1_keywords = json.dumps(keywords)
    
    def to_dict(self):
        """Convert VLM analysis to dictionary"""
        return {
            'id': self.id,
            'camera_id': self.camera_id,
            'camera_name': self.camera.name if self.camera else None,
            'detection_log_id': self.detection_log_id,
            'timestamp': self.timestamp.isoformat(),
            'tier1': {
                'threat_level': self.tier1_threat_level,
                'keywords': self.get_tier1_keywords(),
                'action': self.tier1_action,
                'assessment': self.tier1_assessment
            },
            'tier2': {
                'triggered': self.tier2_triggered,
                'analysis': self.tier2_analysis,
                'timestamp': self.tier2_timestamp.isoformat() if self.tier2_timestamp else None
            } if self.tier2_triggered else None,
            'detection_type': self.detection_type,
            'processing_time_ms': self.processing_time_ms
        }


# ==================== Self-Learning System Models ====================

class VerificationLog(db.Model):
    """Verification log for both VLM automatic verification and user manual feedback"""
    __tablename__ = 'verification_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    detection_log_id = db.Column(db.Integer, db.ForeignKey('detection_logs.id'), nullable=False, index=True)
    verification_source = db.Column(db.String(20), nullable=False, index=True)  # VLM_AUTO, USER_MANUAL
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))  # Nullable for VLM verifications
    verification_result = db.Column(db.String(20), nullable=False)  # CORRECT, INCORRECT, UNCERTAIN
    corrected_label = db.Column(db.String(50))  # What it should have been if incorrect
    confidence_rating = db.Column(db.Float)  # 0-1 confidence in verification
    vlm_model_used = db.Column(db.String(50))  # e.g., 'moondream', 'llava', null for user feedback
    vlm_response = db.Column(db.Text)  # Full VLM response for debugging
    notes = db.Column(db.Text)  # Optional text notes, mainly for user feedback
    image_path = db.Column(db.String(500))  # Path to saved detection frame
    timestamp = db.Column(db.DateTime, default=datetime.now, index=True)
    processed = db.Column(db.Boolean, default=False)  # Whether included in retraining
    sampled_randomly = db.Column(db.Boolean, default=False)  # Whether this was from random sampling
    
    # Relationships
    detection_log = db.relationship('DetectionLog', backref=db.backref('verifications', lazy='dynamic'))
    user = db.relationship('User', backref=db.backref('verifications', lazy='dynamic'))
    
    # Indexes
    __table_args__ = (
        db.Index('idx_verification_source_timestamp', 'verification_source', 'timestamp'),
        db.Index('idx_verification_result', 'verification_result', 'processed'),
    )
    
    def to_dict(self):
        """Convert verification log to dictionary"""
        return {
            'id': self.id,
            'detection_log_id': self.detection_log_id,
            'verification_source': self.verification_source,
            'user_id': self.user_id,
            'username': self.user.username if self.user else None,
            'verification_result': self.verification_result,
            'corrected_label': self.corrected_label,
            'confidence_rating': self.confidence_rating,
            'vlm_model_used': self.vlm_model_used,
            'vlm_response': self.vlm_response,
            'notes': self.notes,
            'image_path': self.image_path,
            'timestamp': self.timestamp.isoformat(),
            'processed': self.processed,
            'sampled_randomly': self.sampled_randomly
        }


class ModelPerformance(db.Model):
    """Track model performance metrics over time based on verified data"""
    __tablename__ = 'model_performance'
    
    id = db.Column(db.Integer, primary_key=True)
    model_name = db.Column(db.String(50), nullable=False, index=True)  # e.g., 'violence', 'fall', 'phone'
    date = db.Column(db.Date, nullable=False, index=True)  # Date of metrics
    total_detections = db.Column(db.Integer, default=0)  # Count of all detections
    verified_detections = db.Column(db.Integer, default=0)  # Count of verified detections
    true_positives = db.Column(db.Integer, default=0)  # Count from correct verifications
    false_positives = db.Column(db.Integer, default=0)  # Count from incorrect verifications
    avg_confidence = db.Column(db.Float)  # Average detection confidence
    threshold_used = db.Column(db.Float)  # Confidence threshold at the time
    accuracy_rate = db.Column(db.Float)  # Calculated from verifications (TP / (TP + FP))
    f1_score = db.Column(db.Float)  # Calculated when available
    timestamp = db.Column(db.DateTime, default=datetime.now)
    
    # Composite index for common query patterns
    __table_args__ = (
        db.Index('idx_model_date', 'model_name', 'date'),
        db.UniqueConstraint('model_name', 'date', name='_model_date_uc'),
    )
    
    def to_dict(self):
        """Convert model performance to dictionary"""
        return {
            'id': self.id,
            'model_name': self.model_name,
            'date': self.date.isoformat() if self.date else None,
            'total_detections': self.total_detections,
            'verified_detections': self.verified_detections,
            'true_positives': self.true_positives,
            'false_positives': self.false_positives,
            'avg_confidence': self.avg_confidence,
            'threshold_used': self.threshold_used,
            'accuracy_rate': self.accuracy_rate,
            'f1_score': self.f1_score,
            'timestamp': self.timestamp.isoformat()
        }


class TrainingQueue(db.Model):
    """Queue for managing automated model retraining jobs"""
    __tablename__ = 'training_queue'
    
    id = db.Column(db.Integer, primary_key=True)
    model_name = db.Column(db.String(50), nullable=False, index=True)
    priority = db.Column(db.String(10), default='MEDIUM')  # LOW, MEDIUM, HIGH
    verified_sample_count = db.Column(db.Integer, default=0)  # Number of verified samples available
    status = db.Column(db.String(20), default='PENDING', index=True)  # PENDING, IN_PROGRESS, COMPLETED, FAILED
    scheduled_time = db.Column(db.DateTime)  # When to start training
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    old_model_path = db.Column(db.String(500))  # Backup of previous model
    new_model_path = db.Column(db.String(500))  # Path to retrained model
    performance_improvement = db.Column(db.Float)  # Percentage improvement
    error_message = db.Column(db.Text)  # If failed
    created_at = db.Column(db.DateTime, default=datetime.now, index=True)
    
    # Indexes
    __table_args__ = (
        db.Index('idx_status_scheduled', 'status', 'scheduled_time'),
    )
    
    def to_dict(self):
        """Convert training queue entry to dictionary"""
        return {
            'id': self.id,
            'model_name': self.model_name,
            'priority': self.priority,
            'verified_sample_count': self.verified_sample_count,
            'status': self.status,
            'scheduled_time': self.scheduled_time.isoformat() if self.scheduled_time else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'old_model_path': self.old_model_path,
            'new_model_path': self.new_model_path,
            'performance_improvement': self.performance_improvement,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat()
        }


class ModelVersion(db.Model):
    """Track model versions for rollback capability"""
    __tablename__ = 'model_versions'
    
    id = db.Column(db.Integer, primary_key=True)
    model_name = db.Column(db.String(50), nullable=False, index=True)
    version_number = db.Column(db.Integer, nullable=False)  # Auto-incremented per model
    model_path = db.Column(db.String(500), nullable=False)
    deployed_at = db.Column(db.DateTime, default=datetime.now)
    performance_metrics = db.Column(db.Text)  # JSON: accuracy, F1, etc.
    trained_on_samples = db.Column(db.Integer)  # Count of training samples used
    is_active = db.Column(db.Boolean, default=False, index=True)  # Currently deployed model
    rollback_available = db.Column(db.Boolean, default=True)
    notes = db.Column(db.Text)
    
    # Composite indexes
    __table_args__ = (
        db.Index('idx_model_version', 'model_name', 'version_number'),
        db.Index('idx_model_active', 'model_name', 'is_active'),
        db.UniqueConstraint('model_name', 'version_number', name='_model_version_uc'),
    )
    
    def get_performance_metrics(self):
        """Get performance metrics as Python dict"""
        return json.loads(self.performance_metrics) if self.performance_metrics else {}
    
    def set_performance_metrics(self, metrics):
        """Set performance metrics from Python dict"""
        self.performance_metrics = json.dumps(metrics)
    
    def to_dict(self):
        """Convert model version to dictionary"""
        return {
            'id': self.id,
            'model_name': self.model_name,
            'version_number': self.version_number,
            'model_path': self.model_path,
            'deployed_at': self.deployed_at.isoformat() if self.deployed_at else None,
            'performance_metrics': self.get_performance_metrics(),
            'trained_on_samples': self.trained_on_samples,
            'is_active': self.is_active,
        }

# ==================== Event Management & Social Media Models ====================

class Event(db.Model):
    """Event model for campus events"""
    __tablename__ = 'events'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    location = db.Column(db.String(200))
    date = db.Column(db.DateTime, nullable=False)
    max_participants = db.Column(db.Integer, default=100)
    status = db.Column(db.String(50), default='upcoming') # upcoming, Live, completed
    organizer_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.now)
    camera_id = db.Column(db.Integer, db.ForeignKey('cameras.id'), nullable=True)
    image_url = db.Column(db.String(255), nullable=True)
    
    organizer = db.relationship('User', backref=db.backref('organized_events', lazy='dynamic'))
    camera = db.relationship('Camera', backref=db.backref('events', lazy='dynamic'))

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'location': self.location,
            'date': self.date.isoformat(),
            'max_participants': self.max_participants,
            'status': self.status,
            'organizer_id': self.organizer_id,
            'camera_id': self.camera_id,
            'camera_name': self.camera.name if self.camera else None,
            'image_url': self.image_url,
            'created_at': self.created_at.isoformat()
        }


class Magazine(db.Model):
    """Magazine model for student submissions"""
    __tablename__ = 'magazines'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    description = db.Column(db.String(500), nullable=True)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    faculty_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.now)
    image_url = db.Column(db.String(255), nullable=True)
    content_image_url = db.Column(db.String(255), nullable=True)
    
    author = db.relationship('User', foreign_keys=[author_id], backref=db.backref('magazines', lazy='dynamic'))
    faculty = db.relationship('User', foreign_keys=[faculty_id])

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'description': self.description,
            'author_id': self.author_id,
            'author_name': self.author.username,
            'status': self.status,
            'faculty_id': self.faculty_id,
            'faculty_name': self.faculty.username if self.faculty else None,
            'image_url': self.image_url,
            'content_image_url': self.content_image_url,
            'created_at': self.created_at.isoformat()
        }


class EventRegistration(db.Model):
    """Registration for event with QR code tracking"""
    __tablename__ = 'event_registrations'
    
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    qr_code_scanned = db.Column(db.Boolean, default=False)
    registered_at = db.Column(db.DateTime, default=datetime.now)
    
    event = db.relationship('Event', backref=db.backref('registrations', lazy='dynamic', cascade='all, delete-orphan'))
    student = db.relationship('User', backref=db.backref('event_registrations', lazy='dynamic', cascade='all, delete-orphan'))

    def to_dict(self):
        return {
            'id': self.id,
            'event_id': self.event_id,
            'student_id': self.student_id,
            'qr_code_scanned': self.qr_code_scanned,
            'registered_at': self.registered_at.isoformat()
        }


class Post(db.Model):
    """Social Media Post for Campus Portal"""
    __tablename__ = 'posts'
    
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    author = db.relationship('User', backref=db.backref('posts', lazy='dynamic', cascade='all, delete-orphan'))

    def to_dict(self):
        return {
            'id': self.id,
            'content': self.content,
            'author_id': self.author_id,
            'author_name': self.author.username if self.author else 'Unknown',
            'created_at': self.created_at.isoformat()
        }


class Comment(db.Model):
    """Comment model for discussion on campus posts"""
    __tablename__ = 'comments'
    
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    post = db.relationship('Post', backref=db.backref('comments', lazy='dynamic', cascade='all, delete-orphan'))
    author = db.relationship('User', backref=db.backref('post_comments', lazy='dynamic'))

    def to_dict(self):
        return {
            'id': self.id,
            'post_id': self.post_id,
            'author_id': self.author_id,
            'author_name': self.author.username if self.author else 'Unknown',
            'content': self.content,
            'created_at': self.created_at.isoformat()
        }


class Notification(db.Model):
    """In-app notification system"""
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    type = db.Column(db.String(50), nullable=False)  # 'magazine_approval', 'event_update', 'comment', etc.
    title = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    link = db.Column(db.String(255))  # Optional link to follow
    is_read = db.Column(db.Boolean, default=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.now, index=True)
    
    user = db.relationship('User', backref=db.backref('notifications', lazy='dynamic', cascade='all, delete-orphan'))

    def to_dict(self):
        return {
            'id': self.id,
            'type': self.type,
            'title': self.title,
            'message': self.message,
            'link': self.link,
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat()
        }
