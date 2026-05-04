# CEMSS - Campus Event management and Surveillance System

## User Manual v1.0

---

## Table of Contents

1. [Introduction](#introduction)
2. [System Requirements](#system-requirements)
3. [Getting Started](#getting-started)
4. [Dashboard Overview](#dashboard-overview)
5. [AI Chatbot Assistant](#ai-chatbot-assistant)
6. [Camera Management](#camera-management)
7. [Detection Features](#detection-features)
8. [Skeletal Tracking](#skeletal-tracking)
9. [Fall Detection](#fall-detection)
10. [Restricted Zones](#restricted-zones)
11. [Alerts & Notifications](#alerts--notifications)
12. [Admin Panel](#admin-panel)
13. [Analytics Dashboard](#analytics-dashboard)
14. [Recording](#recording)
15. [Detection Logs](#detection-logs)
16. [Account Settings](#account-settings)
17. [Troubleshooting](#troubleshooting)
18. [Quick Reference](#quick-reference)
19. [Support](#support)

---

## Introduction

CEMSS (Campus Event management and Surveillance System) is an AI-powered real-time surveillance platform that provides intelligent monitoring, detection, and alerting capabilities. The system uses advanced computer vision with YOLO models and pose estimation to detect various events and send instant notifications.

### Key Features

- **Real-time Video Monitoring**: Live streaming from multiple cameras
- **AI-Powered Detection**: Fall detection, phone usage detection, crowd monitoring
- **AI Chatbot Assistant**: Intelligent assistant with visual frame analysis
- **Skeletal Tracking**: Visual skeleton overlay showing body pose
- **State-Based Fall Detection**: Alerts only on standing→fallen transitions
- **Restricted Zones**: Define areas for person detection alerts
- **WhatsApp Alerts**: Instant notifications via WhatsApp
- **Analytics Dashboard**: Detection trends and statistics
- **Multi-User Support**: Role-based access control
- **Responsive Design**: Optimized for desktop, tablet, and mobile devices

---

## System Requirements

### Server Requirements

- Python 3.8 or higher
- 4GB RAM minimum (8GB recommended)
- NVIDIA GPU with CUDA (optional, for faster detection)
- Webcam or IP cameras

### Supported Browsers

- Google Chrome (recommended)
- Mozilla Firefox
- Microsoft Edge
- Safari

---

## Getting Started

### Starting the System

1. Open a terminal in the CEMSS directory
2. Run: `python start.py`
3. Wait for the startup message:

   ```text
   Server starting at: http://0.0.0.0:5000
   Default Login: admin / admin
   ```

### First Login

1. Open your browser and navigate to `http://localhost:5000`
2. Enter the default credentials:
   - **Username**: `admin`
   - **Password**: `admin`
3. Click **Login**

> ⚠️ **Important**: Change the default password after first login!

### User Registration

New users can register by:

1. Click **Register** on the login page
2. Fill in the registration form:
   - Username
   - Email
   - Phone Number (for WhatsApp alerts)
   - Password
3. Submit and wait for admin approval

---

## Dashboard Overview

The dashboard is your main control center showing all connected cameras.

### Dashboard Elements

| Element | Description |
|---------|-------------|
| **Camera Grid** | Live feed thumbnails from all cameras |
| **Chatbot Bubble** | AI assistant button (bottom-right corner) |
| **Navigation Bar** | Links to Dashboard, Admin, Analytics, Account |
| **Camera Status** | Green = Active, Red = Offline |
| **Quick Actions** | Click any camera to view full screen |

### Accessing Cameras

- Click on any camera thumbnail to open the full camera view
- Camera view shows live feed with detection overlays

---

## AI Chatbot Assistant

CEMSS includes an intelligent AI assistant that can answer questions about your surveillance system and analyze camera feeds in real-time.

### Accessing the Chatbot

1. **Desktop**: Click the floating 🤖 bubble in the bottom-right corner
2. **Mobile**: Tap the bubble to open full-screen chat interface
3. **Close**: Click the × button or tap outside the chat window

### What the Chatbot Can Do

#### Text-Based Queries

Ask questions about system status and data:

**System Status:**

- "Which cameras are currently active?"
- "How many cameras do I have?"
- "What's the system status?"

**Detection History:**

- "Show me detections from the last hour"
- "How many falls were detected today?"
- "Recent detections from Camera 1"

**Camera Information:**

- "What cameras are online?"
- "Which camera has the most detections?"
- "Show me camera details"

**Alerts & Statistics:**

- "Recent alerts"
- "Show me high priority alerts"
- "Detection summary for today"

#### Visual Queries (Frame Analysis)

Ask the chatbot to analyze what it sees in camera feeds:

**Single Camera Analysis:**

- "What do you see in Camera 1?"
- "Is anyone in the parking lot?"
- "Analyze Camera 2"

**Specific Object Queries:**

- "Where is a red truck seen?"
- "Are there any people in Camera 3?"
- "What objects are visible?"

**Scene Understanding:**

- "Describe what's happening in Camera 1"
- "What's in the main entrance?"
- "Check the back door camera"

### Using the Chatbot

#### Step 1: Open the Chat

Click the 🤖 chatbot bubble in the bottom-right corner.

#### Step 2: Type Your Question

Enter your question in plain English. Examples:

```text
"Which cameras are active?"
"What do you see in Camera 1?"
"Show me detections from the last 2 hours"
```

#### Step 3: View the Response

The chatbot will:

- Process your question (shows typing indicator)
- Query the database or analyze camera frames
- Display the results in a clear format
- Show camera images for visual queries

### Chat Interface Features

| Feature | Description |
|---------|-------------|
| **User Messages** | Your messages appear in blue bubbles (right side) |
| **Bot Messages** | AI responses appear in gray bubbles (left side) |
| **Robot Icon** | 🤖 icon identifies bot messages |
| **Typing Indicator** | Animated dots show when bot is thinking |
| **Camera Images** | Visual queries display analyzed frames |
| **Scrollbar** | Custom themed scrollbar for message history |
| **Mobile Mode** | Full-screen bottom sheet on mobile devices |

### Example Conversations

#### Example 1: System Status

```text
You: "Which cameras are active?"

Bot: "You have 4 active cameras:
     • Front Door (Active, 12 detections today)
     • Parking Lot (Active, 5 detections today)
     • Main Hallway (Active, 8 detections today)
     • Back Entrance (Active, 3 detections today)
     
     All cameras are operating normally."
```

#### Example 2: Visual Analysis

```text
You: "What do you see in Camera 1?"

Bot: [Analyzes frame]
     "I can see 2 people in the frame. They appear to be
     standing in what looks like an entrance area. There's
     a door visible in the background. No safety concerns
     detected."

     [Displays Camera 1 frame image]
```

#### Example 3: Detection History

```text
You: "Show me detections from the last hour"

Bot: "In the last hour, there were 15 detections:
     
     • Person: 12 detections (avg confidence: 85%)
       - Camera 1: 5 detections
       - Camera 2: 7 detections
     
     • Phone: 3 detections (avg confidence: 72%)
       - Camera 3: 3 detections
     
     Highest severity: 6/10 (MEDIUM)
     Latest detection: Person at 14:23:15"
```

#### Example 4: Specific Object Search

```text
You: "Where is a red truck seen?"

Bot: [Analyzing all camera feeds...]
     "Checking Camera 3 (Parking Lot):
     I can see a red vehicle in the parking area on the
     left side of the frame. It appears to be a truck or
     SUV parked near the entrance."

     [Displays Camera 3 frame image]
```

### Response Times

- **Text Queries**: 2-5 seconds (database queries)
- **Visual Queries**: 20-30 seconds (AI frame analysis)
- **Cached Frames**: < 1 second (if asked again within 30s)

### Tips for Better Results

✅ **DO:**

- Ask specific questions
- Mention camera names or IDs
- Use natural language
- Be patient with visual queries (processing takes time)

❌ **DON'T:**

- Use overly complex multi-part questions
- Expect instant responses for visual analysis
- Ask about future predictions
- Request real-time video streaming

### Mobile Usage

On mobile devices, the chatbot:

- Opens as a full-screen bottom sheet (60% of screen height)
- Has larger touch targets for easy interaction
- Swipe down to close or tap outside
- Images automatically resize for mobile screens

### Limitations

- Visual analysis requires active cameras
- Response accuracy depends on camera quality
- Frame analysis uses last captured frame (not real-time video)
- Conversation history limited to last 10 messages
- One visual query at a time

---

## Camera Management

### Adding a New Camera

1. Go to **Admin Panel** → **Camera Management**
2. Click **Add Camera**
3. Fill in the details:
   - **Name**: Display name for the camera
   - **Source**: Can be:
     - `0`, `1`, `2`... for webcams
     - RTSP URL: `rtsp://username:password@ip:port/stream`
     - Video file path
   - **Location**: Physical location description
4. Click **Add Camera**

### Editing a Camera

1. Go to **Admin Panel** → **Camera Management**
2. Click **Edit** next to the camera
3. Modify the details:
   - Camera Name
   - Location
   - Source URL/Device
4. Click **Save Changes**

### Deleting a Camera

1. Go to **Admin Panel** → **Camera Management**
2. Click **Delete** next to the camera
3. Confirm the deletion

---

## Detection Features

### Available Detection Models

| Model | Description | Use Case |
|-------|-------------|----------|
| **Fall Detection** | Detects when a person falls | Elderly care, workplace safety |
| **Phone Detection** | Detects phone usage | Schools, restricted areas |
| **Person Detection** | Counts people in view | Crowd monitoring |

### Enabling Detection

1. Open a camera view by clicking on it from the dashboard
2. In the **Detection Controls** panel:
   - Toggle the detection types you want to enable
   - **Fall Detection** - Detects falls with skeletal tracking
   - **Phone Detection** - Detects phone usage
   - **Crowd Detection** - Counts people (5+ triggers alert)
3. Click **Apply Detection**

### Detection Persistence

Detection settings are automatically saved and restored:

- When you enable detection, the settings are saved to the database
- When the server restarts, detection automatically resumes on cameras that had it enabled

---

## Skeletal Tracking

When Person Detection or Fall Detection is enabled, the system displays skeletal overlays on detected people.

### What You'll See

- **Green skeleton lines** connecting body keypoints
- **White circles** at each joint point
- **Person labels** (P1, P2, etc.) above each person
- **"People: N"** counter in top-left corner

### Tracked Keypoints (17-point COCO format)

- Head: nose, eyes, ears
- Upper body: shoulders, elbows, wrists
- Torso: hip points
- Lower body: knees, ankles

### Adaptive Confidence

The system uses adaptive confidence thresholds:

- **Near people** (large in frame): 60% confidence required
- **Far people** (small in frame): 25% confidence required

This prevents missed detections for distant people while maintaining accuracy for nearby ones.

---

## Fall Detection

CEMSS uses advanced state-based fall detection that tracks posture transitions.

### How It Works

```text
Standing → Standing → Standing    = Normal (no alert)
Standing → Falling → Fallen       = 🚨 ALERT!
Fallen → Fallen → Fallen         = No repeated alert
Fallen → Getting Up → Standing    = Reset (ready for next detection)
```

### Fall Detection Criteria

A fall is detected when MULTIPLE conditions are met:

1. **Body Aspect Ratio**: Width > Height (horizontal body)
2. **Head Position**: Head below normal standing position
3. **Torso Orientation**: Shoulders and hips at similar height
4. **Ankle-Head Relationship**: Ankles near head level

### Visual Indicators

- **Green skeleton** = Person standing normally
- **Red bounding box** = Fall transition detected
- **"FALL DETECTED!"** label = Alert triggered

### State Confirmation

- Requires **3 consecutive frames** to confirm a state change
- Prevents false positives from momentary poses

---

## Restricted Zones

Restrict person detection alerts to specific areas within the camera view.

### Creating a Restricted Zone

1. Go to camera view
2. Click **Manage Zones**
3. Click **Add Zone**
4. Draw a polygon on the camera snapshot:
   - Click to add corner points
   - Close the polygon to finish
5. Enter a zone name
6. Click **Save Zone**

### Zone Behavior

- Person alerts only trigger when someone enters a restricted zone
- Zones are shown as colored overlays on the camera view
- You can have multiple zones per camera

### Managing Zones

- **Edit**: Modify zone coordinates
- **Toggle**: Enable/disable without deleting
- **Delete**: Remove the zone permanently

---

## Alerts & Notifications

### WhatsApp Alerts

CEMSS sends instant WhatsApp notifications when detections occur.

### Setting Up WhatsApp Alerts

1. Ensure `pywhatkit` is installed
2. Configure phone numbers in `.env`:

   ```env
   WHATSAPP_PHONE_NUMBERS=+1234567890,+0987654321
   ```

3. Keep WhatsApp Web logged in on the server

### What Triggers Alerts

| Detection | Trigger Condition |
|-----------|-------------------|
| Fall | Person transitions from standing to fallen |
| Phone | Phone detected in frame |
| Crowd | 5+ people detected simultaneously |
| Restricted Zone | Person enters defined zone |

### Alert Throttling

- **Cooldown period**: Prevents spam alerts
- Default: 60 seconds between same-type alerts
- Configurable in `config.py`

### Alert Content

Each alert includes:

- Camera name
- Detection type
- Confidence percentage
- Timestamp

---

## Admin Panel

Access administrative functions through the Admin Panel.

### User Management

| Action | Description |
|--------|-------------|
| **View Users** | See all registered users |
| **Approve User** | Activate pending registrations |
| **Reject User** | Disable a user account |
| **Toggle Admin** | Grant/revoke admin privileges |
| **Delete User** | Permanently remove a user |

### Permission Management

Control who can access which cameras:

1. Select a user
2. Assign camera permissions:
   - **Can View**: See the camera feed
   - **Can Control**: Start/stop detection
   - **Receive Alerts**: Get notifications
3. Save permissions

### Permission Requests

Users can request additional access:

1. Admin sees pending requests
2. Review the reason provided
3. Approve or reject with feedback

---

## Analytics Dashboard

Access detection analytics at `/analytics`.

### Available Metrics

- **Detection Timeline**: Hourly/daily detection trends
- **Detection Distribution**: Breakdown by type
- **Camera Activity**: Activity per camera
- **Recent Alerts**: Latest alert history

### Time Filters

- Last 24 hours
- Last 7 days
- Last 30 days
- Custom date range

### Charts

- **Line Chart**: Detection trends over time
- **Pie Chart**: Detection type distribution
- **Bar Chart**: Camera comparison

---

## Recording

CEMSS supports video recording with detection events.

### Manual Recording

1. Open camera view
2. Click **Start Recording**
3. Recording indicator appears
4. Click **Stop Recording** when done

### Automatic Recording

Detection events automatically trigger clip recording:

- Clips are saved to the `recordings/` directory
- Default clip duration: 10 seconds
- Can be attached to alerts

### Recording Location

Recordings are saved in:

```text
CEMSS/v11/recordings/
├── camera_name/
│   ├── 2024-12-22_13-00-00.mp4
│   └── ...
```

---

## Detection Logs

View all detection events at `/detections`.

### Log Information

Each log entry contains:

- Timestamp
- Camera name
- Detection type (fall, phone, person)
- Confidence percentage
- Severity level

### Filtering

Filter logs by:

- Camera
- Detection type
- Date range
- Severity level

### Camera-Specific Logs

View logs for a specific camera:

- Go to camera view
- Click **View Detection History**

---

## Account Settings

Access your account at `/account`.

### Profile Settings

- View your username and email
- See your assigned camera permissions
- View alert preferences

### Requesting Camera Access

Request additional access:

1. Click **Request Access**
2. Select the camera
3. Choose access type needed
4. Provide a reason
5. Submit and wait for admin approval

---

## Troubleshooting

### Camera Not Loading

**Symptoms**: Camera shows "No Feed" or black screen

**Solutions**:

1. Verify the camera source is correct
2. Check if webcam is being used by another application
3. For RTSP streams, verify the URL and credentials
4. Restart the camera from Admin Panel

### Detection Not Working

**Symptoms**: No detection overlays appearing

**Solutions**:

1. Ensure detection is enabled (toggle and click Apply)
2. Check if the model file exists in `models/`
3. Verify GPU/CPU detection is working
4. Check server logs for model loading errors

### Alerts Not Sending

**Symptoms**: Detections occur but no WhatsApp messages

**Solutions**:

1. Verify WhatsApp Web is logged in
2. Check phone numbers in `.env` format (+countrycode)
3. Ensure `pywhatkit` is installed
4. Check for rate limiting (cooldown period)

### Server Won't Start

**Symptoms**: Error on `python start.py`

**Solutions**:

1. Check all dependencies are installed: `pip install -r requirements.txt`
2. Verify `.env` file exists with required variables
3. Check if port 5000 is already in use
4. Review the error message for specific issues

### Fall Detection Too Sensitive

**Symptoms**: False fall alerts when person is standing

**Solutions**:

- The system now requires BOTH YOLO and pose confirmation
- State transitions need 3 consecutive frames
- Adjust confidence thresholds in `config.py` if needed

### Performance Issues

**Symptoms**: Slow video feed, high CPU usage

**Solutions**:

1. Reduce camera resolution
2. Lower FPS in `config.py`
3. Enable GPU acceleration (NVIDIA CUDA)
4. Reduce number of active detection models

### Chatbot Not Responding

**Symptoms**: Chatbot bubble not appearing or not responding to messages

**Solutions**:

1. **Check if chatbot is enabled**:
   - Verify `CHATBOT_ENABLED=True` in `.env`
   - Check that Ollama is running (`ollama list`)

2. **Verify models are available**:

   ```bash
   ollama list
   # Should show: qwen2.5:0.5b and llava:7b
   ```

3. **Test Ollama connection**:
   - Open `http://localhost:11434` in browser
   - Should see "Ollama is running"

4. **Refresh the browser** (Ctrl+R / F5)

5. **Check browser console** (F12) for JavaScript errors

### Visual Queries Not Working

**Symptoms**: Chatbot responds to text but not visual queries

**Solutions**:

1. **Verify VLM model is installed**:

   ```bash
   ollama pull llava:7b
   ```

2. **Check camera is active**:
   - Camera must be running to capture frames
   - Green status indicator = camera active

3. **Wait for full response time**:
   - Visual queries take 20-30 seconds
   - Don't close chat while processing

4. **Check configuration**:
   - `VLM_ENABLED=True` in `.env`
   - `VLM_MODEL=llava:7b`

### Camera Images Not Displaying

**Symptoms**: Bot responds but no image shown in chat

**Solutions**:

1. Verify camera is actively streaming
2. Check browser image loading (disable ad blockers)
3. Clear browser cache and refresh
4. Check network connection

---

## Quick Reference

### Keyboard Shortcuts (Camera View)

| Key | Action |
|-----|--------|
| `Space` | Toggle detection |
| `R` | Start/stop recording |
| `Esc` | Return to dashboard |

### Default Credentials

- **Username**: admin
- **Password**: admin

### Important Files

| File | Purpose |
|------|---------|
| `start.py` | Launch the application |
| `config.py` | System configuration |
| `.env` | Environment variables |
| `cemss.db` | SQLite database |

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/cameras` | GET | List all cameras |
| `/api/cameras/<id>` | PUT | Update camera |
| `/api/detection/<id>/start` | POST | Start detection |
| `/api/detection/<id>/stop` | POST | Stop detection |
| `/api/zones/<camera_id>` | GET | Get restricted zones |
| `/api/chatbot/status` | GET | Check chatbot availability |
| `/api/chatbot/message` | POST | Send message to chatbot |
| `/api/camera/<id>/frame` | GET | Get camera frame (JPEG) |

---

## Support

For technical support or bug reports:

1. Check the troubleshooting section above
2. Review server logs in `logs/` directory
3. Contact your system administrator

---

**CEMSS v11.1** | Campus Event management and Surveillance System with AI Assistant
*Last Updated: January 2026*
