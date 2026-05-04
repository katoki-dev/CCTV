# CEMSS Admin Guide

## System Administration

### Installation & Setup

#### Prerequisites

- Python 3.9+
- Ollama (for AI features)
- CUDA-capable GPU (recommended)

#### Initial Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Pull AI models
ollama pull qwen2.5:0.5b    # Text chat (397 MB)
ollama pull moondream        # Vision analysis (828 MB)

# Initialize database
python init_db.py

# Start application
python app.py
```

---

## Model Configuration

### Current Setup (Optimized for Limited RAM)

```
Text Chat: qwen2.5:0.5b (397 MB)
Vision: moondream (828 MB)
Total: ~1.2 GB
```

### Alternative Configurations

**High Performance** (Requires 6GB+ RAM):

```
OLLAMA_MODEL=llava:latest
CHATBOT_MODEL=llava:latest
```

**Ultra Lightweight** (Requires 512MB):

```
CHATBOT_MODEL=tinyllama
# Disable VLM or use moondream on-demand only
```

---

## System Monitoring

### Key Logs

- `logs/cemss.log` - Main application log
- `logs/continuous_analysis.log` - VLM monitoring log
- `logs/detection.log` - Detection events

### Performance Metrics

Monitor via:

```bash
# CPU & Memory
python test_performance.py

# System health
htop  # or Task Manager on Windows
```

---

## Database Management

### Backup

```bash
# Create backup
cp database.db database_backup_$(date +%Y%m%d).db

# Automated backup (add to cron/Task Scheduler)
0 2 * * * /path/to/backup_script.sh
```

### Cleanup

```python
# Delete old detections (30+ days)
from models import DetectionLog
from datetime import datetime, timedelta

cutoff = datetime.now() - timedelta(days=30)
DetectionLog.query.filter(DetectionLog.timestamp < cutoff).delete()
db.session.commit()
```

---

## User Management

### Adding Users

```python
from models import User, db
from werkzeug.security import generate_password_hash

user = User(
    username="newuser",
    password=generate_password_hash("password"),
    email="user@example.com",
    is_admin=False
)
db.session.add(user)
db.session.commit()
```

### Camera Permissions

```python
from models import Permission, db

perm = Permission(
    user_id=user_id,
    camera_id=camera_id,
    can_view=True,
    can_control=False
)
db.session.add(perm)
db.session.commit()
```

---

## Troubleshooting

### Ollama Not Responding

```bash
# Check if running
curl http://localhost:11434/api/version

# Restart Ollama
ollama serve

# Check models
ollama list
```

### High Memory Usage

1. Check `continuous_analyzer` is using moondream (not llava)
2. Reduce `VLM_SCAN_INTERVAL` in config
3. Disable continuous VLM if not needed

### Detection Pipeline Issues

```python
# Check detector status
# In app.py logs, look for:
"✓ person detector loaded on GPU"
"✓ fall detector loaded on GPU"
```

---

## Security

### Change Default Credentials

```python
from models import User
from werkzeug.security import generate_password_hash

admin = User.query.filter_by(username='admin').first()
admin.password = generate_password_hash('NEW_SECURE_PASSWORD')
db.session.commit()
```

### Enable HTTPS

```nginx
# Nginx reverse proxy
server {
    listen 443 ssl;
    server_name cemss.example.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://localhost:5000;
    }
}
```

---

## Optimization

### Database Indexes

Already created:

- `idx_detection_timestamp`
- `idx_detection_camera_timestamp`
- `idx_alert_sent_at`

### Caching (Phase 4 Implementation)

```python
# Add in chatbot_service.py
from functools import lru_cache

@lru_cache(maxsize=100)
def get_camera_info(camera_id):
    # Cache camera metadata
    pass
```

---

## API Reference

See [API_DOCUMENTATION.md](API_DOCUMENTATION.md) for complete API reference.

### Key Endpoints

- `POST /api/chatbot/message` - Chatbot query
- `GET /api/cameras` - Camera list
- `GET /api/detections/recent` - Recent detections
- `GET /api/alerts` - Alert list

---

**Version**: 11.2  
**Last Updated**: January 2026
