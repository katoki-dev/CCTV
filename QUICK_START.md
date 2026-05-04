# CEMSS - Quick Start Guide

## 🚀 Get Started in 5 Minutes

### Prerequisites

Before you begin, ensure you have:

- **Python 3.9+** installed
- **Git** (for cloning)
- **Ollama** installed ([download here](https://ollama.ai))
- **Webcam or IP camera** connected
- **4GB RAM minimum** (8GB recommended)

---

## Step 1: Download & Install (2 minutes)

### Option A: Clone from GitHub

```bash
git clone https://github.com/yourusername/CEMSS.git
cd CEMSS
```

### Option B: Download ZIP

1. Download ZIP from GitHub
2. Extract to `C:\CEMSS` (or your preferred location)
3. Open terminal in that folder

---

## Step 2: Install Dependencies (1 minute)

```bash
# Install Python packages
pip install -r requirements.txt

# Pull AI models (this may take a few minutes)
ollama pull qwen2.5:0.5b
ollama pull moondream
```

**Expected output**:

```
✓ qwen2.5:0.5b downloaded (397 MB)
✓ moondream downloaded (828 MB)
```

---

## Step 3: Configure System (30 seconds)

### Quick Configuration

```bash
# Copy example config
copy .env.example .env

# Edit .env with your settings (optional for first run)
notepad .env
```

**Important settings** (defaults work for most users):

- `FLASK_PORT=5000` - Web interface port
- `CHATBOT_MODEL=qwen2.5:0.5b` - Text chat model
- `OLLAMA_MODEL=moondream` - Vision model

---

## Step 4: Initialize Database (30 seconds)

```bash
python init_db.py
```

**Expected output**:

```
✓ Database created
✓ Admin user created
✓ Sample camera added
```

**Default login**:

- Username: `admin`
- Password: `admin`

> ⚠️ **Security**: Change the admin password immediately after first login!

---

## Step 5: Start the System (1 minute)

### Start Ollama (if not already running)

```bash
ollama serve
```

### Start CEMSS

```bash
python app.py
```

**Expected output**:

```
✓ Camera pool initialized
✓ Chatbot available: qwen2.5:0.5b
✓ VLM available: moondream
✓ Continuous Analysis Manager initialized

Server: http://0.0.0.0:5000
Default Login: admin / admin
```

---

## Step 6: Access the Dashboard

1. Open browser: **<http://localhost:5000>**
2. Login with `admin` / `admin`
3. **You're in!** 🎉

---

## 🎯 First Steps After Login

### 1. Configure Your Camera

- Go to **Admin** → **Camera Management**
- Add your camera (webcam or IP camera)
- Test the feed

### 2. Try the Chatbot

- Click the **chat icon** (bottom-right)
- Ask: **"What do you see?"**
- Wait for the AI analysis

### 3. Explore Features

- **Dashboard**: Live feeds & system stats
- **Detections**: Security event log
- **Analytics**: Charts & insights
- **Recordings**: Video archive

---

## 🆘 Troubleshooting

### Ollama Not Found

**Problem**: `ollama: command not found`

**Solution**:

```bash
# Install Ollama
# Windows: Download from https://ollama.ai
# Linux/Mac: curl https://ollama.ai/install.sh | sh
```

### Chatbot Says "Unavailable"

**Problem**: Chatbot shows as unavailable

**Solution**:

```bash
# Check Ollama is running
curl http://localhost:11434/api/version

# Pull models again
ollama pull qwen2.5:0.5b
ollama pull moondream

# Restart app
python app.py
```

### Camera Not Showing

**Problem**: Black screen or "Camera not found"

**Solution**:

1. Check camera index in Admin panel (try 0, 1, 2)
2. Ensure camera not used by another app
3. For IP camera, verify URL format: `rtsp://user:pass@ip:port/stream`

### High Memory Usage

**Problem**: System slow or crashes

**Solution**:

- Close other applications
- Use lighter models (already configured by default)
- Disable continuous VLM:

  ```python
  # In detection_pipeline.py, comment out:
  # self.continuous_analyzer = ...
  ```

### Port 5000 Already in Use

**Problem**: `Address already in use`

**Solution**:

```bash
# Change port in .env
FLASK_PORT=8080

# Or kill existing process
# Windows:
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# Linux/Mac:
lsof -ti:5000 | xargs kill
```

---

## 📚 Next Steps

### Learn More

- Read **[USER_GUIDE.md](USER_GUIDE.md)** for detailed features
- Read **[ADMIN_GUIDE.md](ADMIN_GUIDE.md)** for administration
- Check **[FINAL_PRESENTATION.md](FINAL_PRESENTATION.md)** for capabilities

### Customize

1. **Add more cameras**: Admin → Camera Management
2. **Configure alerts**: Email/WhatsApp settings in `.env`
3. **Train custom models**: See `ADMIN_GUIDE.md`

### Get Help

- Check **[FAQ](#common-questions)** below
- Review **logs/cemss.log** for errors
- Contact system administrator

---

## 💡 Common Questions

**Q: How do I add more users?**
A: Admin panel → User Management → Add User

**Q: Can I use it on a Raspberry Pi?**
A: Yes, but use lighter models. Set `OLLAMA_MODEL=tinyllama`

**Q: Does it work offline?**
A: Yes! All AI models run locally once downloaded.

**Q: How much disk space needed?**
A: ~5GB minimum (models + recordings)

**Q: Can I access remotely?**
A: Yes, configure firewall and use IP address. For security, use HTTPS (see ADMIN_GUIDE.md)

---

## ⚡ Quick Commands Reference

```bash
# Start system
python app.py

# Run tests
python test_full_system.py

# Check performance
python test_performance.py

# View logs
tail -f logs/cemss.log    # Linux/Mac
Get-Content logs\cemss.log -Tail 50 -Wait  # Windows

# Backup database
copy database.db database_backup.db

# Pull new models
ollama pull <model-name>
```

---

**🎉 Congratulations! Your CEMSS system is running!**

For advanced features and customization, see the [USER_GUIDE.md](USER_GUIDE.md) and [ADMIN_GUIDE.md](ADMIN_GUIDE.md).
