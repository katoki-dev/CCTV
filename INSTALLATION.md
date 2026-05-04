# CEMSS Installation Guide

## Campus Event management and Surveillance System v11.1

Complete guide for installing and setting up CEMSS from scratch on a new system.

---

## 📋 Table of Contents

1. [System Requirements](#system-requirements)
2. [Quick Installation](#quick-installation)
3. [Manual Installation](#manual-installation)
4. [Configuration](#configuration)
5. [First Run](#first-run)
6. [Troubleshooting](#troubleshooting)

---

## 🖥️ System Requirements

### Minimum Requirements

- **OS**: Windows 10/11, Linux, or macOS
- **Python**: 3.8 or higher
- **RAM**: 8GB (16GB recommended)
- **Storage**: 10GB free space
- **GPU**: NVIDIA GPU with CUDA support (optional, recommended for better performance)

### Software Dependencies

- Python 3.8+
- pip (Python package manager)
- Git (optional, for cloning repository)

### Optional Components

- **Ollama** (for AI chatbot and VLM features)
  - Download from: <https://ollama.ai>
  - Models: `qwen2.5:0.5b`, `moondream`

---

## ⚡ Quick Installation

### For Windows Users

1. **Download/Extract CEMSS**

   ```cmd
   cd path\to\CEMSS\v11.1
   ```

2. **Run Setup Script**

   ```cmd
   setup_cemss.bat
   ```

   This will automatically:
   - Check Python version
   - Install all dependencies
   - Create configuration files
   - Initialize database
   - Verify system readiness

3. **Configure Settings**
   - Edit `.env` file with your email/alert settings

4. **Start CEMSS**

   ```cmd
   start_cemss.bat
   ```

5. **Access Dashboard**
   - Open browser: <http://localhost:5000>
   - Default login: `admin` / `admin`
   - **Change password immediately after first login!**

---

## 🔧 Manual Installation

### Step 1: Install Python Dependencies

```bash
pip install -r requirements.txt
```

**This installs:**

- Flask (Web framework)
- OpenCV (Computer vision)
- Ultralytics YOLO (Detection models)
- PyTorch (Deep learning)
- Flask-SocketIO (Real-time updates)
- And 30+ other dependencies

### Step 2: Create Environment Configuration

```bash
# Copy template to .env
copy .env.example .env     # Windows
cp .env.example .env       # Linux/Mac
```

### Step 3: Edit Configuration

Open `.env` file and configure:

#### Required Settings

```env
SECRET_KEY=your-unique-secret-key-here
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
```

#### Email Alerts (recommended)

```env
EMAIL_ENABLED=True
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USERNAME=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
EMAIL_RECIPIENT_LIST=recipient@example.com
```

> **Gmail Users**: Generate App Password at <https://myaccount.google.com/apppasswords>

#### Optional: WhatsApp Alerts

```env
WHATSAPP_PHONE_NUMBERS=+1234567890
```

### Step 4: Initialize Database

```bash
python setup.py
```

Or manually:

```bash
python -c "from database import init_database; init_database()"
```

### Step 5: Create Required Directories

```bash
mkdir logs recordings videos models cache
mkdir recordings\detection recordings\continuous
mkdir cache\frames
```

### Step 6: Install Ollama (AI Features)

**Optional but Recommended** - Enables AI chatbot and visual query features

#### Windows/MacOS

1. **Download Ollama**
   - Visit: <https://ollama.ai>
   - Download installer for your OS
   - Run the installer

2. **Verify Installation**

   ```cmd
   ollama --version
   ```

3. **Start Ollama Server** (may start automatically)

   ```cmd
   ollama serve
   ```

4. **Install Required AI Models**

   ```cmd
   # Chatbot LLM (fast, 400MB)
   ollama pull qwen2.5:0.5b
   
   # VLM for camera analysis (2GB)
   ollama pull moondream
   
   # Advanced VLM - Optional (4.5GB)
   ollama pull llava:7b
   ```

5. **Verify Models**

   ```cmd
   ollama list
   ```

#### Linux

```bash
# Install Ollama
curl https://ollama.ai/install.sh | sh

# Start Ollama service
ollama serve &

# Install models
ollama pull qwen2.5:0.5b
ollama pull moondream
ollama pull llava:7b  # Optional

# Verify
ollama list
```

#### What Each Model Does

| Model | Size | Purpose | Required |
|-------|------|---------|----------|
| `qwen2.5:0.5b` | 400MB | Chatbot LLM for natural language queries | Yes |
| `moondream` | 2GB | VLM for camera frame analysis | Yes |
| `llava:7b` | 4.5GB | Advanced VLM for detailed visual analysis | Optional |

> **Note**: Without Ollama, CEMSS will still work but AI chatbot and visual query features will be disabled.

### Step 7: Download Detection Models (Optional)

Place custom-trained models in `models/` directory:

- `fall_detection.pt` (Fall detection)
- `violence_detection.pt` (Violence/fight detection)
- `phone_detection.pt` (Phone usage detection)

> Base YOLOv8 models will auto-download on first run

---

## ⚙️ Configuration

### Database Configuration

Default: SQLite database (`database.db`)

```env
DATABASE_PATH=database.db
```

### Detection Models Configuration

Edit `config.py` to enable/disable models:

```python
DETECTION_MODELS = {
    'person': {'enabled': True, 'confidence_threshold': 0.5},
    'fall': {'enabled': True, 'confidence_threshold': 0.30},
    'violence': {'enabled': True, 'confidence_threshold': 0.65},
    'phone': {'enabled': True, 'confidence_threshold': 0.6},
    'motion': {'enabled': True}
}
```

### AI Features Configuration

```env
# Ollama LLM Configuration
OLLAMA_ENABLED=True
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=moondream

# Chatbot Configuration
CHATBOT_ENABLED=True
CHATBOT_MODEL=qwen2.5:0.5b
```

### Performance Tuning

```env
# GPU/CPU Configuration
YOLO_DEVICE=0              # 0 for GPU, 'cpu' for CPU-only

# Frame Processing
FRAME_SKIP_RATE=1          # Process every Nth frame
VIDEO_FRAME_SKIP_RATE=2    # Skip rate for video files
JPEG_QUALITY=85            # Streaming quality (1-100)

# Detection Optimization
ENABLE_HALF_PRECISION=True # FP16 for GPU (faster)
```

---

## 🚀 First Run

### 1. Start the System

**Windows**:

```cmd
start_cemss.bat
```

**Linux/Mac**:

```bash
python start.py
```

### 2. Verify Startup

Check console output for:

```
✓ Flask-Mail initialized
✓ Chatbot API endpoints loaded via Blueprint
✓ Loaded detection models: ['person', 'fall', 'violence', 'phone', 'motion']
✓ All detection model files verified
Server starting at: http://0.0.0.0:5000
```

### 3. Access Dashboard

1. Open browser: `http://localhost:5000`
2. Login with default credentials:
   - Username: `admin`
   - Password: `admin`

### 4. Initial Configuration

After logging in:

1. **Change Admin Password**
   - Go to Account Settings
   - Update password immediately

2. **Add Cameras**
   - Navigate to Admin Panel
   - Add RTSP/USB cameras
   - Test connectivity

3. **Configure Alerts**
   - Set up email recipients
   - Test alert system
   - Configure alert thresholds

4. **Enable Detection Models**
   - Select which models to activate
   - Configure detection zones (optional)
   - Set severity levels

---

## 🔍 Verification Checklist

After installation, verify:

- [ ] Python 3.8+ installed
- [ ] All dependencies installed (run `pip list`)
- [ ] `.env` file created and configured
- [ ] Database initialized (`database.db` exists)
- [ ] Directories created (logs, recordings, models, cache)
- [ ] Server starts without errors
- [ ] Can access dashboard at localhost:5000
- [ ] Can login with admin credentials
- [ ] Email alerts configured (if enabled)

---

## 🐛 Troubleshooting

### Issue: "Module not found" errors

**Solution**:

```bash
pip install -r requirements.txt --upgrade
```

### Issue: "Database initialization failed"

**Solution**:

```bash
# Delete existing database
del database.db

# Reinitialize
python setup.py
```

### Issue: "Port 5000 already in use"

**Solution 1**: Stop other services using port 5000

**Solution 2**: Change port in `.env`:

```env
FLASK_PORT=5001
```

### Issue: "Failed to load detection models"

**Solution**:

- Check `models/` directory exists
- Verify model files are present
- Base models will auto-download on first detection

### Issue: "Ollama connection failed"

**Solution**:

```bash
# Install Ollama from https://ollama.ai

# Pull required models
ollama pull qwen2.5:0.5b
ollama pull moondream

# Verify Ollama is running
ollama list
```

### Issue: "Camera connection failed"

**Common Causes**:

1. **RTSP URL incorrect** - Verify camera IP and credentials
2. **Firewall blocking** - Allow Python through firewall
3. **Camera offline** - Check camera network connection

**Test RTSP URL**:

```bash
# Using VLC or ffplay
ffplay "rtsp://username:password@camera-ip:554/stream"
```

### Issue: "Email alerts not sending"

**Gmail Users**:

1. Enable 2-Factor Authentication
2. Generate App Password: <https://myaccount.google.com/apppasswords>
3. Use App Password in `.env` file

**Test Email**:

```bash
python test_email.py
```

### Issue: "High CPU/Memory usage"

**Solutions**:

1. Increase frame skip rate in `.env`:

   ```env
   FRAME_SKIP_RATE=2
   VIDEO_FRAME_SKIP_RATE=3
   ```

2. Reduce JPEG quality:

   ```env
   JPEG_QUALITY=70
   ```

3. Disable unused detection models in `config.py`

4. Use GPU instead of CPU:

   ```env
   YOLO_DEVICE=0
   ```

---

## 📚 Additional Resources

### Documentation

- **User Manual**: [USER_MANUAL.md](file:///c:/Users/anina/OneDrive/Desktop/Project/CEMSS/v11.1/USER_MANUAL.md)
- **README**: [README.md](file:///c:/Users/anina/OneDrive/Desktop/Project/CEMSS/v11.1/README.md)
- **Email Setup Guide**: [EMAIL_SETUP.md](file:///c:/Users/anina/OneDrive/Desktop/Project/CEMSS/v11.1/EMAIL_SETUP.md)

### Useful Commands

```bash
# Reset database
python -c "from database import reset_database; reset_database()"

# Test email alerts
python test_email.py

# Test VLM functionality
python test_vlm.py

# Check system
python setup.py
```

### Default Credentials

**Admin Account**:

- Username: `admin`
- Password: `admin`
- Role: Administrator

> **⚠️ CRITICAL**: Change this password immediately after first login!

---

## 🔐 Security Recommendations

1. **Change default admin password** immediately
2. **Use strong SECRET_KEY** in `.env`
3. **Enable HTTPS** in production (use reverse proxy like Nginx)
4. **Restrict access** to trusted networks
5. **Keep dependencies updated**: `pip install -r requirements.txt --upgrade`
6. **Use App Passwords** for email (never use main password)
7. **Regular backups** of database (`database.db`)

---

## 📞 Support

For issues not covered in this guide:

1. Check console output for error messages
2. Review log files in `logs/` directory
3. Verify all configuration in `.env`
4. Ensure all dependencies are installed

---

## ✅ Installation Complete

If you've completed all steps successfully:

1. Start CEMSS: `start_cemss.bat`
2. Access: <http://localhost:5000>
3. Login: `admin` / `admin`
4. **Change password!**
5. Add cameras and start monitoring

**Welcome to CEMSS! 🎉**
