"""
CEMSS - Campus Event management and Surveillance System
Configuration Management
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base directory
BASE_DIR = Path(__file__).parent.absolute()

# Database configuration
DATABASE_PATH = os.getenv('DATABASE_PATH', str(BASE_DIR / 'database.db'))
DATABASE_URI = f'sqlite:///{DATABASE_PATH}'

# SQLAlchemy optimization settings
SQLALCHEMY_POOL_SIZE = int(os.getenv('SQLALCHEMY_POOL_SIZE', 10))
SQLALCHEMY_POOL_RECYCLE = int(os.getenv('SQLALCHEMY_POOL_RECYCLE', 3600))
SQLALCHEMY_MAX_OVERFLOW = int(os.getenv('SQLALCHEMY_MAX_OVERFLOW', 20))
SQLALCHEMY_POOL_TIMEOUT = int(os.getenv('SQLALCHEMY_POOL_TIMEOUT', 30))
SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_ECHO = False  # Set to True for SQL query debugging

# Database cleanup settings
DETECTION_LOG_MAX_AGE_DAYS = int(os.getenv('DETECTION_LOG_MAX_AGE_DAYS', 30))
ALERT_LOG_MAX_AGE_DAYS = int(os.getenv('ALERT_LOG_MAX_AGE_DAYS', 90))

# Flask configuration
SECRET_KEY = os.getenv('SECRET_KEY', 'cemss-default-secret-key-change-in-production')
FLASK_HOST = os.getenv('FLASK_HOST', '0.0.0.0')
FLASK_PORT = int(os.getenv('FLASK_PORT', 5000))
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

# Directory paths
LOGS_DIR = BASE_DIR / 'logs'
VIDEOS_DIR = BASE_DIR / 'videos'
RECORDING_BASE_DIR = BASE_DIR / 'recordings'  # Base directory for all recordings
MODELS_DIR = BASE_DIR / 'models'
STATIC_DIR = BASE_DIR / 'static'
TEMPLATES_DIR = BASE_DIR / 'templates'

# Create directories if they don't exist
for directory in [LOGS_DIR, VIDEOS_DIR, RECORDING_BASE_DIR, MODELS_DIR, STATIC_DIR, TEMPLATES_DIR]:
    directory.mkdir(exist_ok=True)

# Create subdirectories for recordings
(RECORDING_BASE_DIR / 'detection').mkdir(exist_ok=True)
(RECORDING_BASE_DIR / 'continuous').mkdir(exist_ok=True)

# Detection configuration
DETECTION_MODELS = {
    'person': {
        'enabled': True,
        'model_path': str(BASE_DIR / 'yolov8n.pt'),  # Using standard YOLOv8n directly
        'confidence_threshold': 0.5,
        'description': 'Person Detection (Standard YOLO)'
    },
    'fall': {
        'enabled': True,
        'model_path': str(MODELS_DIR / 'fall_detection.pt'),
        'confidence_threshold': 0.50,  # Optimized for accuracy (increased from 0.30)
        'required_frames': 2,  # Require 2 consecutive frames for confirmation
        'description': 'Fall Detection (YOLO + Pose Estimation)'
    },
    'violence': {
        'enabled': True,
        'model_path': str(MODELS_DIR / 'violence_detection' / 'weights' / 'violence_detection_best.pt'),  # Newly trained on RWF-2000 (91.8% acc)
        'confidence_threshold': 0.6,
        'required_frames': 5,
        'description': 'Violence Detection (CEMSS Optimized)'
    },
    'motion': {
        'enabled': True,
        'model_path': None,  # No model file, uses OpenCV
        'confidence_threshold': 0.0,  # Motion detection doesn't use confidence
        'description': 'Motion Detection (Dark Optimized)',
        'sensitivity': 'medium',  # 'low', 'medium', 'high'
        'optimize_for_dark': True,  # Enable dark scene optimization
        'min_area': 500,  # Minimum motion area in pixels
        'dark_boost_factor': 1.5  # Sensitivity multiplier for dark scenes
    },
    'fire': {
        'enabled': True,
        'model_path': str(MODELS_DIR / 'yolov8n.pt'), # Placeholder
        'confidence_threshold': 0.5,
        'description': 'Fire Detection'
    },
    'suspicious': {
        'enabled': True,
        'model_path': str(MODELS_DIR / 'yolov8n.pt'), # Placeholder
        'confidence_threshold': 0.5,
        'description': 'Suspicious Activity Detection'
    }
}

# Phone Detection Optimization (DISABLED - Phone detection removed)
PHONE_FACE_FILTER_ENABLED = False  # Phone detection disabled
PHONE_FACE_IOU_THRESHOLD = float(os.getenv('PHONE_FACE_IOU_THRESHOLD', 0.25))
PHONE_HEAD_REGION_RATIO = float(os.getenv('PHONE_HEAD_REGION_RATIO', 0.35))
PHONE_MIN_DISTANCE_FROM_FACE = int(os.getenv('PHONE_MIN_DISTANCE_FROM_FACE', 30))


# YOLO configuration
YOLO_DEVICE = os.getenv('YOLO_DEVICE', 'cpu')  # Force CPU for low RAM system
YOLO_IMG_SIZE = 320  # Reduced for low RAM
YOLO_IOU_THRESHOLD = 0.45

# Caching configuration
CACHE_TYPE = os.getenv('CACHE_TYPE', 'simple')  # 'simple', 'redis', 'memcached'
CACHE_DEFAULT_TIMEOUT = int(os.getenv('CACHE_DEFAULT_TIMEOUT', 300))  # 5 minutes
CACHE_ENABLED = os.getenv('CACHE_ENABLED', 'True').lower() == 'true'

# Camera configuration
DEFAULT_CAMERA_FPS = 30
CAMERA_RECONNECT_ATTEMPTS = 5
CAMERA_RECONNECT_DELAY = 5  # seconds

# Video recording configuration
VIDEO_CLIP_DURATION = 5  # seconds for alert clips (2s pre + 3s post detection)
VIDEO_CODEC = 'mp4v'  # or 'avc1' for H.264
VIDEO_FPS = 30
PRE_DETECTION_BUFFER_SECONDS = 3  # Reduced to 3s for faster VLM analysisd chatbot analysis

# WhatsApp Alert configuration (using pywhatkit)
# Add phone numbers with country code, e.g., ['+911234567890', '+919876543210']
WHATSAPP_PHONE_NUMBERS = os.getenv('WHATSAPP_PHONE_NUMBERS', '').split(',') if os.getenv('WHATSAPP_PHONE_NUMBERS') else []
# Example: Set in .env as WHATSAPP_PHONE_NUMBERS=+911234567890,+919876543210

# Alert throttling (to prevent spam)
ALERT_COOLDOWN_SECONDS = 60  # Minimum time between alerts for the same camera/model
MAX_ALERTS_PER_HOUR = 20  # Maximum alerts per camera per hour

# Crowd detection configuration
CROWD_THRESHOLD = int(os.getenv('CROWD_THRESHOLD', 3))  # Trigger alert on 3 people (was 5)
CROWD_ALERT_COOLDOWN_SECONDS = int(os.getenv('CROWD_ALERT_COOLDOWN_SECONDS', 120))  # Cooldown for crowd alerts

# Email Alert configuration
EMAIL_ENABLED = os.getenv('EMAIL_ENABLED', 'True').lower() == 'true'
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')  # SMTP server
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))  # SMTP port (587 for TLS, 465 for SSL)
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True').lower() == 'true'
EMAIL_USE_SSL = os.getenv('EMAIL_USE_SSL', 'False').lower() == 'true'
EMAIL_USERNAME = os.getenv('EMAIL_USERNAME', '')  # Your email address
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD', '')  # App password or email password
EMAIL_FROM_ADDRESS = os.getenv('EMAIL_FROM_ADDRESS', EMAIL_USERNAME)  # Sender address
EMAIL_FROM_NAME = os.getenv('EMAIL_FROM_NAME', 'CEMSS Alert System')
EMAIL_RECIPIENT_LIST = [addr.strip() for addr in os.getenv('EMAIL_RECIPIENT_LIST', '').split(',') if addr.strip()]
# Example: Set in .env as EMAIL_RECIPIENT_LIST=admin@example.com,security@example.com

# Logging configuration
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
SESSION_LOG_FORMAT = 'session_%Y%m%d_%H%M%S.log'

# WebSocket configuration
SOCKETIO_ASYNC_MODE = 'threading'
SOCKETIO_CORS_ALLOWED_ORIGINS = '*'

# Session configuration
SESSION_PERMANENT = False
PERMANENT_SESSION_LIFETIME = 3600  # 1 hour

# Monitoring panel configuration
MONITOR_REFRESH_RATE = 100  # milliseconds
MONITOR_GRID_PADDING = 5  # pixels

# Performance tuning
LOW_POWER_MODE = os.getenv('LOW_POWER_MODE', 'True').lower() == 'true'  # Enabled by default for 8GB RAM/i3
FRAME_SKIP_RATE = int(os.getenv('FRAME_SKIP_RATE', 10 if LOW_POWER_MODE else 5))
VIDEO_FRAME_SKIP_RATE = int(os.getenv('VIDEO_FRAME_SKIP_RATE', 12 if LOW_POWER_MODE else 5))
DETECTION_BATCH_SIZE = int(os.getenv('DETECTION_BATCH_SIZE', 1))  # Batch size for inference
MAX_CONCURRENT_DETECTIONS = int(os.getenv('MAX_CONCURRENT_DETECTIONS', 1))  # Optimized for 8GB RAM: Reduced to 1 concurrent thread
JPEG_QUALITY = int(os.getenv('JPEG_QUALITY', 70))  # Optimized: JPEG quality for video streaming
ENABLE_HALF_PRECISION = os.getenv('ENABLE_HALF_PRECISION', 'True').lower() == 'true'  # Enabled for speed/memory

# Crowd Analysis Optimization
USE_OPENCV_DNN = os.getenv('USE_OPENCV_DNN', 'True').lower() == 'true'
CROWD_HEATMAP_ENABLED = os.getenv('CROWD_HEATMAP_ENABLED', 'True').lower() == 'true'
CROWD_MODEL_ONNX = os.getenv('CROWD_MODEL_ONNX', str(MODELS_DIR / 'crowd_detection' / 'weights' / 'crowd_detection_best.onnx'))
CROWD_ACCUMULATION_TIMEOUT = int(os.getenv('CROWD_ACCUMULATION_TIMEOUT', 300))  # 5 minutes in seconds

# Training optimization
ENABLE_AMP_TRAINING = os.getenv('ENABLE_AMP_TRAINING', 'True').lower() == 'true'  # Automatic Mixed Precision
GRADIENT_ACCUMULATION_STEPS = int(os.getenv('GRADIENT_ACCUMULATION_STEPS', 1))
ENABLE_MODEL_WARMUP = os.getenv('ENABLE_MODEL_WARMUP', 'True').lower() == 'true'

# API rate limiting
API_RATE_LIMIT_ENABLED = os.getenv('API_RATE_LIMIT_ENABLED', 'False').lower() == 'true'
API_RATE_LIMIT = os.getenv('API_RATE_LIMIT', '100 per minute')  # Format: "N per second/minute/hour"

# ==================== Phase 1 Enhancements ====================

# Temporal Smoothing (False-Positive Reduction)
TEMPORAL_SMOOTHING_ENABLED = os.getenv('TEMPORAL_SMOOTHING_ENABLED', 'True').lower() == 'true'
TEMPORAL_SMOOTHING_FRAMES = {
    'person': int(os.getenv('TEMPORAL_SMOOTHING_PERSON', 2)),  # Optimized: 3 -> 2 for faster alerts
    'fall': int(os.getenv('TEMPORAL_SMOOTHING_FALL', 1)),  # Already optimal for critical detection
    'violence': int(os.getenv('TEMPORAL_SMOOTHING_VIOLENCE', 5)),  # 5 frames for violence
    'phone': int(os.getenv('TEMPORAL_SMOOTHING_PHONE', 3))  # 3 frames for phone detection
}

# Enhanced Confidence Thresholds
MIN_CONFIDENCE_OVERRIDES = {
    'person': float(os.getenv('MIN_CONFIDENCE_PERSON', 0.55)),  # Optimized: 0.6 -> 0.55 for better sensitivity
    'fall': float(os.getenv('MIN_CONFIDENCE_FALL', 0.25)),  # Optimized: 0.30 -> 0.25 for earlier fall detection
    'phone': float(os.getenv('MIN_CONFIDENCE_PHONE', 0.50))  # Optimized: 0.55 -> 0.50 for better detection
}

# Multi-Model Fusion
MULTI_MODEL_FUSION_ENABLED = os.getenv('MULTI_MODEL_FUSION_ENABLED', 'True').lower() == 'true'
FUSION_BOOST_FACTOR = float(os.getenv('FUSION_BOOST_FACTOR', 0.15))  # 15% confidence boost
FUSION_COMBINATIONS = {
    'person+phone': {'boost': 0.15, 'severity_modifier': 2},
    'person+fall': {'boost': 0.20, 'severity_modifier': 3}
}

# Severity Scoring
SEVERITY_SCORING_ENABLED = os.getenv('SEVERITY_SCORING_ENABLED', 'True').lower() == 'true'
BASE_SEVERITY_SCORES = {
    'fall': 9,  # Optimized: 8 -> 9 (medical emergency priority)
    'violence': 10,  # Optimized: 9 -> 10 (critical - immediate response)
    'person': 5,  # Base score, increases with zone/time context
    'phone': 4
}
NIGHT_HOURS_START = int(os.getenv('NIGHT_HOURS_START', 22))  # 10 PM
NIGHT_HOURS_END = int(os.getenv('NIGHT_HOURS_END', 6))  # 6 AM
NIGHT_TIME_SEVERITY_BOOST = int(os.getenv('NIGHT_TIME_SEVERITY_BOOST', 2))
RESTRICTED_ZONE_SEVERITY_BOOST = int(os.getenv('RESTRICTED_ZONE_SEVERITY_BOOST', 3))

# Alert Aggregation
ALERT_AGGREGATION_ENABLED = os.getenv('ALERT_AGGREGATION_ENABLED', 'True').lower() == 'true'
ALERT_AGGREGATION_WINDOW = int(os.getenv('ALERT_AGGREGATION_WINDOW', 60))  # seconds
MAX_DETECTIONS_PER_AGGREGATE = int(os.getenv('MAX_DETECTIONS_PER_AGGREGATE', 10))

# Alert Priority Levels
ALERT_PRIORITIES = {
    'LOW': {'min_severity': 1, 'max_severity': 3, 'color': '#4CAF50'},
    'MEDIUM': {'min_severity': 4, 'max_severity': 6, 'color': '#FF9800'},
    'HIGH': {'min_severity': 7, 'max_severity': 8, 'color': '#F44336'},
    'CRITICAL': {'min_severity': 9, 'max_severity': 10, 'color': '#9C27B0'}
}

# Analytics Configuration
ANALYTICS_ENABLED = os.getenv('ANALYTICS_ENABLED', 'True').lower() == 'true'
ANALYTICS_CACHE_TTL_HOURLY = int(os.getenv('ANALYTICS_CACHE_TTL_HOURLY', 86400))  # 24 hours
ANALYTICS_CACHE_TTL_DAILY = int(os.getenv('ANALYTICS_CACHE_TTL_DAILY', 604800))  # 7 days
ANALYTICS_DEFAULT_PERIOD = os.getenv('ANALYTICS_DEFAULT_PERIOD', '24h')  # 24h, 7d, 30d
ANALYTICS_MAX_DATA_POINTS = int(os.getenv('ANALYTICS_MAX_DATA_POINTS', 1000))

# Resource Monitoring
RESOURCE_MONITORING_ENABLED = os.getenv('RESOURCE_MONITORING_ENABLED', 'True').lower() == 'true'
CPU_THRESHOLD_HIGH = int(os.getenv('CPU_THRESHOLD_HIGH', 85))  # percent
GPU_THRESHOLD_HIGH = int(os.getenv('GPU_THRESHOLD_HIGH', 90))  # percent
CPU_THRESHOLD_LOW = int(os.getenv('CPU_THRESHOLD_LOW', 60))  # percent
GPU_THRESHOLD_LOW = int(os.getenv('GPU_THRESHOLD_LOW', 70))  # percent
RESOURCE_CHECK_INTERVAL = int(os.getenv('RESOURCE_CHECK_INTERVAL', 10))  # seconds
MAX_FRAME_SKIP_RATE = int(os.getenv('MAX_FRAME_SKIP_RATE', 5))  # max frames to skip

# Ollama LLM Configuration (Unified Vision + Text Model)
OLLAMA_ENABLED = os.getenv('OLLAMA_ENABLED', 'False').lower() == 'true'  # Default to False for 8GB RAM
OLLAMA_HOST = os.getenv('OLLAMA_HOST', 'http://localhost:11434')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'minicpm-v')  # Unified efficient model
OLLAMA_TIMEOUT = int(os.getenv('OLLAMA_TIMEOUT', 180))  # Increased from 120s to 180s for slower but accurate VLM responses
OLLAMA_ANALYSIS_MODE = os.getenv('OLLAMA_ANALYSIS_MODE', 'post_detection')
OLLAMA_KEYFRAMES_PER_CLIP = int(os.getenv('OLLAMA_KEYFRAMES_PER_CLIP', 3))
OLLAMA_MIN_CONFIDENCE_FOR_LLM = float(os.getenv('OLLAMA_MIN_CONFIDENCE_FOR_LLM', 0.4))

# Hybrid VLM Monitoring Configuration (Unified)
VLM_ENABLED = os.getenv('VLM_ENABLED', 'False').lower() == 'true'  # Default to False for 8GB RAM
VLM_TIER1_MODEL = os.getenv('VLM_TIER1_MODEL', 'minicpm-v')  # Unified model
VLM_TIER2_MODEL = os.getenv('VLM_TIER2_MODEL', 'minicpm-v')  # Unified model
VLM_SCAN_INTERVAL = int(os.getenv('VLM_SCAN_INTERVAL', 10))
VLM_TIER2_THRESHOLD = os.getenv('VLM_TIER2_THRESHOLD', 'MEDIUM')
VLM_AUTO_ENHANCE_ALERTS = os.getenv('VLM_AUTO_ENHANCE_ALERTS', 'True').lower() == 'true'

# Custom Specialized Models (Legacy references kept but mapped to new model or removed if truly gone)
CUSTOM_FALL_DETECTOR_MODEL = os.getenv('CUSTOM_FALL_DETECTOR_MODEL', 'minicpm-v') # Fallback to main model
CUSTOM_VIOLENCE_DETECTOR_MODEL = os.getenv('CUSTOM_VIOLENCE_DETECTOR_MODEL', 'minicpm-v')
CUSTOM_THREAT_SCANNER_MODEL = os.getenv('CUSTOM_THREAT_SCANNER_MODEL', 'minicpm-v')

# WhatsApp Configuration
WHATSAPP_PHONE_NUMBERS = [num.strip() for num in os.getenv('WHATSAPP_PHONE_NUMBERS', '').split(',') if num.strip()]
# CallMeBot (Free WhatsApp API) Configuration
CALLMEBOT_API_KEY = os.getenv('CALLMEBOT_API_KEY', '')
CALLMEBOT_PHONE = os.getenv('CALLMEBOT_PHONE', '')

# Video Overlay Configuration (Timestamps)
TIMESTAMP_ENABLED = os.getenv('TIMESTAMP_ENABLED', 'True').lower() == 'true'
TIMESTAMP_FORMAT = os.getenv('TIMESTAMP_FORMAT', '%Y-%m-%d %H:%M:%S')
TIMESTAMP_POSITION = os.getenv('TIMESTAMP_POSITION', 'top-right')
TIMESTAMP_FONT_SCALE = float(os.getenv('TIMESTAMP_FONT_SCALE', 0.6))
TIMESTAMP_COLOR = tuple(map(int, os.getenv('TIMESTAMP_COLOR', '255,255,255').split(',')))
TIMESTAMP_BG_COLOR = tuple(map(int, os.getenv('TIMESTAMP_BG_COLOR', '0,0,0').split(',')))
TIMESTAMP_BG_ALPHA = float(os.getenv('TIMESTAMP_BG_ALPHA', 0.7))



# Frame Cache Configuration (for VLM frame analysis)
FRAME_CACHE_DIR = os.path.join(BASE_DIR, 'cache', 'frames')
FRAME_CACHE_TTL = int(os.getenv('FRAME_CACHE_TTL', 30))

# ==================== Self-Learning System Configuration ====================

# Core learning system
LEARNING_ENABLED = os.getenv('LEARNING_ENABLED', 'False').lower() == 'true'  # Default to False for 8GB RAM
LEARNING_DATA_DIR = BASE_DIR / 'learning_data'
VERIFICATION_IMAGE_DIR = LEARNING_DATA_DIR / 'verification_images'
RETRAINING_DATA_DIR = LEARNING_DATA_DIR / 'retraining_datasets'

# Create learning directories
for directory in [LEARNING_DATA_DIR, VERIFICATION_IMAGE_DIR, RETRAINING_DATA_DIR]:
    directory.mkdir(exist_ok=True)

# Random sampling configuration
RANDOM_SAMPLING_ENABLED = os.getenv('RANDOM_SAMPLING_ENABLED', 'True').lower() == 'true'
SAMPLING_RATE = float(os.getenv('SAMPLING_RATE', 0.01))
SAMPLING_MIN_INTERVAL_SECONDS = int(os.getenv('SAMPLING_MIN_INTERVAL_SECONDS', 30))

# VLM Verification configuration
VLM_VERIFICATION_ENABLED = os.getenv('VLM_VERIFICATION_ENABLED', 'False').lower() == 'true'  # Default to False for 8GB RAM
VLM_VERIFICATION_MODEL = os.getenv('VLM_VERIFICATION_MODEL', 'minicpm-v')  # Unified model
VLM_VERIFICATION_TIMEOUT = int(os.getenv('VLM_VERIFICATION_TIMEOUT', 120))  # Increased from 60s to 120s for thorough verification
VLM_BATCH_SIZE = int(os.getenv('VLM_BATCH_SIZE', 5))
VLM_MIN_CONFIDENCE = float(os.getenv('VLM_MIN_CONFIDENCE', 0.7))

# Automatic threshold adjustment
AUTO_THRESHOLD_ADJUSTMENT = os.getenv('AUTO_THRESHOLD_ADJUSTMENT', 'True').lower() == 'true'
THRESHOLD_ADJUSTMENT_WINDOW = int(os.getenv('THRESHOLD_ADJUSTMENT_WINDOW', 100))
MIN_VERIFIED_SAMPLES_FOR_ADJUSTMENT = int(os.getenv('MIN_VERIFIED_SAMPLES_FOR_ADJUSTMENT', 30))
THRESHOLD_STEP_SIZE = float(os.getenv('THRESHOLD_STEP_SIZE', 0.05))

# Retraining configuration
AUTO_RETRAINING_ENABLED = os.getenv('AUTO_RETRAINING_ENABLED', 'True').lower() == 'true'
MIN_VERIFIED_SAMPLES_FOR_RETRAINING = int(os.getenv('MIN_VERIFIED_SAMPLES_FOR_RETRAINING', 200))
RETRAINING_SCHEDULE_HOUR = int(os.getenv('RETRAINING_SCHEDULE_HOUR', 2))  # 2 AM
RETRAINING_DAYS = os.getenv('RETRAINING_DAYS', 'Saturday,Sunday')  # Only on weekends by default
VALIDATION_SPLIT = float(os.getenv('VALIDATION_SPLIT', 0.2))  # 20% for validation
MIN_ACCURACY_IMPROVEMENT = float(os.getenv('MIN_ACCURACY_IMPROVEMENT', 0.02))  # 2% minimum improvement

# Data retention
VERIFICATION_RETENTION_DAYS = int(os.getenv('VERIFICATION_RETENTION_DAYS', 90))
MAX_VERIFICATION_STORAGE_GB = int(os.getenv('MAX_VERIFICATION_STORAGE_GB', 50))

# Model versioning
MAX_MODEL_VERSIONS = int(os.getenv('MAX_MODEL_VERSIONS', 5))  # Keep last 5 versions

# NOTE: VLM configuration is in the "Hybrid VLM Monitoring Configuration" section above (lines 250-256)

