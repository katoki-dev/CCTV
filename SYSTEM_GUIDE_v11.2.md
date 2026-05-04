# CEMSS v11.2 - System Guide & Documentation

Welcome to the **Campus Event management and Surveillance System (CEMSS) v11.2**. This guide provides a detailed overview of the system's features and instructions on how to use them effectively, especially in low-resource environments.

---

## 🚀 1. Features & Functionalities

### 🛡️ AI Security Suite
- **Person Detection**: Real-time tracking of individuals in the camera field.
- **Fall Detection**: Uses advanced AI to detect if someone falls (Highest Priority).
- **Violence Detection**: Detects physical altercations and aggressive behavior.
- **Fire & Smoke Detection**: Visual-based alerting for early fire detection.
- **Restricted Zone Monitoring**: Define custom areas (e.g., "Faculty Lounge") where any movement triggers an immediate alert.

### 📊 Campus Management (Portals)
- **Faculty Command Center**:
    - Manage live camera feeds.
    - Create campus events linked to specific cameras.
    - Approve or reject student magazine submissions.
    - Receive real-time AI-generated activity briefings.
- **Student Safety Portal**:
    - View upcoming campus events.
    - Submit articles or updates to the Digital Magazine.
    - Request access to specific camera feeds (subject to approval).

### 📢 Alert System
- **Multi-Channel Notifications**: Alerts are sent via the Web Dashboard, WhatsApp, and Email.
- **Manual Alerts**: Faculty can trigger a manual "Security Alert" for any camera.
- **Acknowledgment System**: Track who reviewed and resolved each alert.

---

## ⚙️ 2. How to Use the System

### For Faculty Users
1.  **Dashboard**: Access the "Faculty Command Center" to see a summary of recent activity.
2.  **Live Feeds**: Click on a camera to view its live stream. **Note: You can only enable AI analysis for ONE camera at a time to save CPU.**
3.  **Events**: Use the "Add Event" button to schedule activities. You can link these to a camera so security monitors that area during the event.
4.  **Approvals**: Review pending Magazine articles in the "Pending Approvals" section.

### For Student Users
1.  **Events**: Check the main page for "Upcoming Events" and locations.
2.  **Magazine**: Navigate to the Magazine section to read approved articles or submit your own.
3.  **Access Requests**: If you need to see a specific camera feed, go to "Account" and submit a "Permission Request."

---

## 🔋 3. Low-Resource Optimization (8GB RAM / i3 CPU)

The system has been specifically tuned for your hardware profile (8GB RAM, i3 CPU, Radeon GPU).

### Enforced Limits
- **1-Camera Limit**: The system will automatically disable AI on any other camera when you start analysis on a new one. This prevents your CPU from reaching 100% and crashing the system.
- **Frame Skipping**: The system processes 1 frame out of every 10-12. This might look "choppy" but ensures the AI stays real-time without lag.
- **Disabled Modules**: The VLM (Vision-Language Model) and LLM Chatbot are disabled to save ~3GB of RAM.

### 💡 Optimization Tips
1.  **Close Other Apps**: Before running CEMSS, close Chrome tabs, Photoshop, or other heavy software.
2.  **Virtual Memory**: In Windows, go to "System Properties" > "Advanced" > "Performance Settings" > "Virtual Memory" and set it to at least **16384 MB (16GB)**. This prevents "Out of Memory" crashes.
3.  **Browser**: Use a lightweight browser (like Edge or a fresh Chrome profile) to view the dashboard.

---

## 🛠️ 4. Technical Support
If the system crashes or feels slow:
- **Restart CEMSS**: Run the `CEMSS.bat` file again.
- **Check Logs**: View the `logs/` folder to see if there are specific "Memory Error" or "Timeout" messages.
- **Disable unused models**: Only enable "Person" or "Fall" detection if you don't need the others.
