"""
Enhanced Chatbot Features - Quick Implementation
Adds camera-specific queries, alert acknowledgment, and clip playback
"""

# This file provides enhanced chatbot commands that can be integrated

ENHANCED_COMMANDS = {
    "camera_specific": {
        "patterns": [
            r"camera (\d+)",
            r"show me camera (\d+)",
            r"what.*camera (\d+)",
            r"analyze camera (\d+)"
        ],
        "handler": "handle_camera_query"
    },
    
    "alert_management": {
        "patterns": [
            r"acknowledge alert (\d+)",
            r"dismiss alert (\d+)",
            r"clear alert (\d+)"
        ],
        "handler": "handle_alert_acknowledgment"
    },
    
    "clip_playback": {
        "patterns": [
            r"show clip (\d+)",
            r"play detection (\d+)",
            r"view recording (\d+)"
        ],
        "handler": "handle_clip_playback"
    }
}

def get_enhanced_help_text():
    """Return help text for enhanced features"""
    return """
**Enhanced Commands:**

📹 **Camera Queries:**
- "Show me camera 2" - View specific camera
- "What's on camera 3?" - Analyze camera feed
- "Analyze camera 1" - Get detailed analysis

🔔 **Alert Management:**
- "Acknowledge alert 123" - Mark alert as reviewed
- "Dismiss alert 456" - Clear alert notification

🎬 **Clip Playback:**
- "Show clip 789" - View detection clip
- "Play recent detection" - View latest event

💡 **General:**
- "What do you see?" - Analyze current camera
- "Show recent detections" - View detection log
- "How many cameras are active?" - System status
"""

# Integration points for chatbot_service.py
INTEGRATION_NOTES = """
To integrate these features:

1. Add to _analyze_query_intent():
   - Check for alert acknowledgment patterns
   - Check for clip playback patterns

2. Add new handler methods:
   - _handle_alert_acknowledgment(alert_id, flask_app, current_user)
   - _handle_clip_playback(clip_id, flask_app, current_user)

3. Update API endpoints in api_chatbot.py:
   - POST /api/chatbot/acknowledge_alert
   - GET /api/chatbot/clips/<id>
"""

print("Enhanced chatbot features outlined in chatbot_enhancements.py")
print("Integration notes included for manual implementation")
