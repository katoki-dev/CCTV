content = """# CEMSS - Campus Event management and Surveillance System
# Environment Configuration

# Flask Configuration
SECRET_KEY=cemss-secret-key-change-in-production
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
DEBUG=False

# Database
# DATABASE_PATH=database.db

# YOLO Configuration
YOLO_DEVICE=0

# ==================== Email Alert Configuration ====================
# Enable/disable email alerts
EMAIL_ENABLED=True

# SMTP Server Settings (Gmail)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False

# Email Credentials
# For Gmail: Use an App Password (not your regular password)
# Generate at: https://myaccount.google.com/apppasswords
EMAIL_USERNAME=katoki.dev@gmail.com
EMAIL_PASSWORD=your-app-password-here

# Sender Information
EMAIL_FROM_ADDRESS=katoki.dev@gmail.com
EMAIL_FROM_NAME=CEMSS Alert System

# Recipients (comma-separated list)
EMAIL_RECIPIENT_LIST=katoki317@gmail.com

# WhatsApp Alert Configuration (using pywhatkit)
# Add phone numbers with country code, comma-separated
WHATSAPP_PHONE_NUMBERS=+916364731668

# Crowd Detection
CROWD_THRESHOLD=5
CROWD_ALERT_COOLDOWN_SECONDS=120

# Logging
LOG_LEVEL=INFO

# AI Model Configuration
OLLAMA_ENABLED=True
OLLAMA_HOST=http://localhost:11434
# Use minicpm-v for VLM (Vision) tasks - Optimized Unified Model
OLLAMA_MODEL=minicpm-v
# Use Qwen2.5 0.5B for Chatbot (Text) tasks - Very lightweight
CHATBOT_MODEL=qwen2.5:0.5b

# VLM Configuration Override
VLM_TIER1_MODEL=minicpm-v
VLM_TIER2_MODEL=minicpm-v

# Performance Tuning
FRAME_SKIP_RATE=2
MAX_CONCURRENT_DETECTIONS=2
JPEG_QUALITY=70
VLM_SCAN_INTERVAL=15
ENABLE_HALF_PRECISION=True

# Crowd Optimization
USE_OPENCV_DNN=True
CROWD_HEATMAP_ENABLED=True
CROWD_MODEL_ONNX=models/crowd_detection/weights/crowd_detection_best.onnx
CROWD_ACCUMULATION_TIMEOUT=300
"""
with open('.env', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated .env successfully")
