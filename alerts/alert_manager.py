"""
CEMSS - Campus Event management and Surveillance System
Alert Manager - WhatsApp Alerts using pywhatkit
"""
import threading
from datetime import datetime
from pathlib import Path
from config import MAX_ALERTS_PER_HOUR

# WhatsApp configuration - set these in config.py or .env
import requests
import urllib.parse
try:
    from config import WHATSAPP_PHONE_NUMBERS, CALLMEBOT_API_KEY, CALLMEBOT_PHONE
except ImportError:
    WHATSAPP_PHONE_NUMBERS = []
    CALLMEBOT_API_KEY = ''
    CALLMEBOT_PHONE = ''


# Try to import pywhatkit
try:
    import pywhatkit
    PYWHATKIT_AVAILABLE = True
except ImportError:
    PYWHATKIT_AVAILABLE = False
    print("⚠ WARNING: pywhatkit not installed. WhatsApp alerts will not work.")
    print("  Install with: pip install pywhatkit")

from alerts.whatsapp_service import WhatsAppService
from alerts.email_service import get_email_service

# Email configuration
try:
    from config import EMAIL_ENABLED, EMAIL_RECIPIENT_LIST
except ImportError:
    EMAIL_ENABLED = False
    EMAIL_RECIPIENT_LIST = []


class AlertManager:
    """Manages email and WhatsApp alerts for detection events"""
    
    def __init__(self, db_session, logging_manager, mail_instance=None):
        """
        Initialize alert manager
        
        Args:
            db_session: Database session
            logging_manager: Logging manager instance
            mail_instance: Flask-Mail instance (optional, for improved email delivery)
        """
        self.db = db_session
        self.logging_manager = logging_manager
        self.lock = threading.Lock()
        
        # Alert rate limiting
        self.alert_history = {}  # (camera_id, model_name) -> list of timestamps
        
        # Initialize Email Service with Flask-Mail support
        self.email_service = get_email_service(mail_instance=mail_instance)
        if self.email_service and self.email_service.enabled:
            method = "Flask-Mail" if self.email_service.use_flask_mail else "SMTP"
            print(f"✓ Email service initialized ({method})")
        else:
            print("⚠ WARNING: Email service is disabled or not configured.")
            print("  Set EMAIL_ENABLED=True and configure SMTP settings in .env")
        
        # Initialize Persistent WhatsApp Service
        try:
            self.wa_service = WhatsAppService.get_instance()
        except:
            self.wa_service = None
        
        # Check WhatsApp configuration
        if not WHATSAPP_PHONE_NUMBERS:
            print("⚠ WARNING: No WhatsApp phone numbers configured.")
            print("  Add WHATSAPP_PHONE_NUMBERS in config.py (e.g., ['+911234567890'])")
        
        if not PYWHATKIT_AVAILABLE:
            print("⚠ WARNING: pywhatkit not available. WhatsApp alerts disabled.")
    
    def send_detection_alert(self, camera_id, camera_name, model_name, 
                           confidence, detection_data, video_clip_path=None):
        """
        Send email and WhatsApp alerts for a detection event
        
        Args:
            camera_id: Database ID of the camera
            camera_name: Display name of the camera
            model_name: Name of the detection model
            confidence: Detection confidence score
            detection_data: Detection data (bounding boxes, etc.)
            video_clip_path: Path to video clip (optional)
        """
        # Check rate limiting
        if not self._check_rate_limit(camera_id, model_name):
            print(f"Alert rate limit reached for {camera_name} - {model_name}")
            return
        
        # Get email recipients
        email_recipients = self._get_email_recipients(camera_id, model_name)
        
        # Get phone numbers for WhatsApp alerts
        whatsapp_recipients = self._get_alert_recipients(camera_id, model_name)
        
        # Extract zone information and severity
        zone_name = None
        severity_level = 'MEDIUM'
        severity_score = 5
        if detection_data and len(detection_data) > 0:
            first_detection = detection_data[0]
            if isinstance(first_detection, dict):
                zone_name = first_detection.get('zone_name')
                severity_level = first_detection.get('severity_level', 'MEDIUM')
                severity_score = first_detection.get('severity_score', 5)
        
        detection_count = len(detection_data) if detection_data else 0
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Send email alerts
        if email_recipients and self.email_service and self.email_service.enabled:
            try:
                self.email_service.send_detection_alert(
                    recipients=email_recipients,
                    camera_name=camera_name,
                    model_name=model_name,
                    confidence=confidence,
                    timestamp=timestamp,
                    detection_count=detection_count,
                    zone_name=zone_name,
                    severity_level=severity_level,
                    severity_score=severity_score,
                    video_clip_path=video_clip_path
                )
                print(f"✓ Email alert sent to {len(email_recipients)} recipient(s)")
            except Exception as e:
                print(f"✗ Failed to send email alert: {e}")
        
        # Build WhatsApp alert message
        zone_info = f"\n⚠️ Restricted Zone: {zone_name}" if zone_name else ""
        
        if not whatsapp_recipients:
            # If no WhatsApp recipients but email was sent, return success
            if email_recipients:
                return
            print(f"No alert recipients configured for {camera_name} - {model_name}")
            return
        
        # Special message for crowd detection
        if model_name == 'crowd':
            person_count = len(detection_data) if detection_data else 0
            message = f"""🚨 *CEMSS CROWD ALERT* 🚨

📷 Camera: {camera_name}
👥 Crowd Detected: {person_count} people
📊 Confidence: {confidence:.0%}
🕐 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{zone_info}

_Automated alert from CEMSS Surveillance_"""
        else:
            detection_count = len(detection_data) if detection_data else 0
            message = f"""🚨 *CEMSS ALERT* 🚨

📷 Camera: {camera_name}
🔍 Detection: {model_name.title()}
📊 Confidence: {confidence:.0%}
🕐 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
📌 Count: {detection_count}{zone_info}

_Automated alert from CEMSS Surveillance_"""
        
        # Send WhatsApp message in a separate thread to avoid blocking
        thread = threading.Thread(
            target=self._send_whatsapp_message,
            args=(whatsapp_recipients, message, video_clip_path),
            daemon=True
        )
        thread.start()
        
        # Log the alert (combine email and WhatsApp recipients)
        all_recipients = list(set(email_recipients + whatsapp_recipients))
        self.logging_manager.log_alert_sent(camera_name, model_name, all_recipients, video_clip_path)
        
        # Save to database
        self._save_alert_to_db(camera_id, model_name, all_recipients, 
                              f"Alert: {model_name}", message, video_clip_path)
    
    def send_manual_alert(self, camera_id, camera_name, message, user_email, 
                         video_clip_path=None):
        """
        Send manual email and WhatsApp alerts triggered by a user
        
        Args:
            camera_id: Database ID of the camera
            camera_name: Display name of the camera
            message: Custom message
            user_email: Email of the user who triggered the alert
            video_clip_path: Path to video clip (optional)
        """
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Get email recipients for manual alerts
        email_recipients = EMAIL_RECIPIENT_LIST if EMAIL_ENABLED else []
        
        # Send email alerts
        if email_recipients and self.email_service and self.email_service.enabled:
            try:
                self.email_service.send_manual_alert(
                    recipients=email_recipients,
                    camera_name=camera_name,
                    message=message,
                    user=user_email,
                    timestamp=timestamp,
                    video_clip_path=video_clip_path
                )
                print(f"✓ Manual email alert sent to {len(email_recipients)} recipient(s)")
            except Exception as e:
                print(f"✗ Failed to send manual email alert: {e}")
        
        # Get all configured phone numbers for manual alerts
        whatsapp_recipients = WHATSAPP_PHONE_NUMBERS if WHATSAPP_PHONE_NUMBERS else []
        
        if not whatsapp_recipients and not email_recipients:
            print("No recipients configured for manual alerts")
            return
        
        whatsapp_message = f"""⚠️ *CEMSS MANUAL ALERT* ⚠️

📷 Camera: {camera_name}
👤 Triggered By: {user_email}
🕐 Time: {timestamp}

📝 Message:
{message}

_Manual alert from CEMSS Surveillance_"""
        
        # Send WhatsApp message if recipients configured
        if whatsapp_recipients:
            thread = threading.Thread(
                target=self._send_whatsapp_message,
                args=(whatsapp_recipients, whatsapp_message, video_clip_path),
                daemon=True
            )
            thread.start()
        
        # Log the alert
        all_recipients = list(set(email_recipients + whatsapp_recipients))
        self.logging_manager.log_incident(
            camera_id, camera_name, "manual_alert", message,
            user=user_email, video_clip_path=video_clip_path, is_manual=True
        )
        
        # Save to database
        self._save_alert_to_db(camera_id, "manual", all_recipients, 
                              "Manual Alert", whatsapp_message, 
                              video_clip_path, is_manual=True)
    
    def _send_whatsapp_message(self, recipients, message, video_clip_path=None):
        """
        Send a WhatsApp message to multiple recipients
        Priority:
        1. Selenium Persistent Driver (Fast, needs setup)
        2. CallMeBot API (Fast, needs API key)
        3. PyWhatKit (Slow, opens browser tab)
        """
        if not recipients:
            print("No recipients for WhatsApp message")
            return False
            
        success_count = 0
        remaining_recipients = list(recipients)

        # 1. Try Selenium Persistent Service
        if self.wa_service and self.wa_service.driver:
            # We clone the list to iterate safely while modifying
            for phone in list(remaining_recipients):
                status = False
                if video_clip_path and Path(video_clip_path).exists():
                    # Send as media if video exists
                    status = self.wa_service.send_media(phone, video_clip_path, caption=message)
                else:
                    # Send as text
                    status = self.wa_service.send_message(phone, message)
                
                if status:
                    success_count += 1
                    remaining_recipients.remove(phone)
            
            if not remaining_recipients:
                return True

        # 2. Try CallMeBot (Browser-less, fast)
        if CALLMEBOT_API_KEY and CALLMEBOT_PHONE:
            for phone in list(remaining_recipients):
                # Normalize numbers to check match
                p1 = phone.replace(' ', '').replace('+', '')
                p2 = CALLMEBOT_PHONE.replace(' ', '').replace('+', '')
                
                if p1 == p2:
                    if self._send_via_callmebot(message):
                        success_count += 1
                        remaining_recipients.remove(phone)
            
            if not remaining_recipients and success_count > 0:
                return True
        
        # 3. Fallback to PyWhatKit (Browser-based) - DISABLED to prevent browser hijacking
        # if remaining_recipients:
        #    print("PyWhatKit fallback disabled to prevent disrupting user session.")
        #    pass
            
        return success_count > 0

    def _send_via_callmebot(self, message):
        """Send WhatsApp message using CallMeBot API (No browser required)"""
        try:
            # Encode message for URL
            encoded_msg = urllib.parse.quote(message)
            url = f"https://api.callmebot.com/whatsapp.php?phone={CALLMEBOT_PHONE}&text={encoded_msg}&apikey={CALLMEBOT_API_KEY}"
            
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                print(f"✓ WhatsApp alert sent via CallMeBot API")
                return True
            else:
                print(f"✗ CallMeBot API Error: {response.text}")
                return False
        except Exception as e:
            print(f"✗ Failed to call CallMeBot API: {e}")
            return False

    def _get_alert_recipients(self, camera_id, model_name):
        """
        Get list of phone numbers who should receive WhatsApp alerts
        
        Args:
            camera_id: Database ID of the camera
            model_name: Name of the detection model
        
        Returns:
            list: List of phone numbers
        """
        recipients = []
        
        try:
            # Import and use app context for database queries (needed in worker threads)
            from app import app
            from models import User
            
            with app.app_context():
                # Get users who should receive alerts for this camera/model
                users = User.query.all()
                for user in users:
                    if user.should_receive_alert(camera_id, model_name) and user.phone_number:
                        recipients.append(user.phone_number)
        except Exception as e:
            print(f"Error fetching user recipients: {e}")
        
        # Also include configured admin numbers from .env
        if WHATSAPP_PHONE_NUMBERS:
            for phone in WHATSAPP_PHONE_NUMBERS:
                if phone and phone.strip() and phone not in recipients:
                    recipients.append(phone.strip())
        
        return recipients
    
    def _get_email_recipients(self, camera_id, model_name):
        """
        Get list of email addresses who should receive email alerts
        
        Args:
            camera_id: Database ID of the camera
            model_name: Name of the detection model
        
        Returns:
            list: List of email addresses
        """
        recipients = []
        
        try:
            # Import and use app context for database queries (needed in worker threads)
            from app import app
            from models import User
            
            with app.app_context():
                # Get users who should receive alerts for this camera/model
                users = User.query.all()
                for user in users:
                    if user.should_receive_alert(camera_id, model_name) and user.email:
                        recipients.append(user.email)
        except Exception as e:
            print(f"Error fetching email recipients: {e}")
        
        # Also include configured admin emails from .env
        if EMAIL_ENABLED and EMAIL_RECIPIENT_LIST:
            for email in EMAIL_RECIPIENT_LIST:
                if email and email.strip() and email not in recipients:
                    recipients.append(email.strip())
        
        return recipients
    
    def _check_rate_limit(self, camera_id, model_name):
        """
        Check if alert rate limit has been reached
        
        Args:
            camera_id: Database ID of the camera
            model_name: Name of the detection model
        
        Returns:
            bool: True if alert can be sent, False if rate limited
        """
        key = (camera_id, model_name)
        now = datetime.now()
        
        with self.lock:
            # Initialize if not exists
            if key not in self.alert_history:
                self.alert_history[key] = []
            
            # Remove alerts older than 1 hour
            self.alert_history[key] = [
                ts for ts in self.alert_history[key]
                if (now - ts).total_seconds() < 3600
            ]
            
            # Check limit
            if len(self.alert_history[key]) >= MAX_ALERTS_PER_HOUR:
                return False
            
            # Add current alert
            self.alert_history[key].append(now)
            return True
    
    def _save_alert_to_db(self, camera_id, model_name, recipients, subject, 
                         message, video_clip_path=None, is_manual=False):
        """Save alert to database"""
        try:
            from models import Alert
            import json
            
            alert = Alert(
                camera_id=camera_id,
                model_name=model_name,
                recipient_emails=json.dumps(recipients),  # Store phone numbers here
                subject=subject,
                message=message,
                video_clip_path=video_clip_path,
                is_manual=is_manual
            )
            
            self.db.add(alert)
            self.db.commit()
        
        except Exception as e:
            print(f"Failed to save alert to database: {str(e)}")
            self.db.rollback()
