"""
CEMSS - Campus Event management and Surveillance System
Email Service - Send alerts via email with attachments
Using Flask-Mail for improved reliability
"""
import logging
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)

# Try to import Flask-Mail
try:
    from flask_mail import Mail, Message
    FLASK_MAIL_AVAILABLE = True
except ImportError:
    FLASK_MAIL_AVAILABLE = False
    logger.warning("Flask-Mail not installed. Falling back to smtplib")
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    from email.mime.base import MIMEBase
    from email import encoders


class EmailService:
    """Handle email sending for alerts using Flask-Mail or smtplib fallback"""
    
    def __init__(self, host, port, username, password, from_address, from_name, 
                 use_tls=True, use_ssl=False, mail_instance=None):
        """
        Initialize email service
        
        Args:
            host: SMTP server hostname
            port: SMTP port (587 for TLS, 465 for SSL)
            username: Email username
            password: Email password or app password
            from_address: Sender email address
            from_name: Sender display name
            use_tls: Use TLS encryption
            use_ssl: Use SSL encryption
            mail_instance: Flask-Mail instance (optional)
        """
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.from_address = from_address
        self.from_name = from_name
        self.use_tls = use_tls
        self.use_ssl = use_ssl
        self.mail = mail_instance
        self.use_flask_mail = FLASK_MAIL_AVAILABLE and mail_instance is not None
        
        # Validate configuration
        if not all([host, port, username, password, from_address]):
            logger.warning("Email service not fully configured")
            self.enabled = False
        else:
            self.enabled = True
            method = "Flask-Mail" if self.use_flask_mail else "SMTP"
            logger.info(f"Email service initialized ({method}): {from_address} via {host}:{port}")
    
    def send_email(self, recipients: List[str], subject: str, body: str, 
                   html_body: Optional[str] = None, attachment_path: Optional[str] = None) -> bool:
        """
        Send an email using Flask-Mail or SMTP fallback
        
        Args:
            recipients: List of recipient email addresses
            subject: Email subject
            body: Plain text email body
            html_body: Optional HTML email body
            attachment_path: Optional path to file attachment
        
        Returns:
            bool: True if sent successfully
        """
        if not self.enabled:
            logger.warning("Email service is disabled - skipping email send")
            return False
        
        if not recipients:
            logger.warning("No recipients specified")
            return False
        
        try:
            if self.use_flask_mail:
                return self._send_with_flask_mail(recipients, subject, body, html_body, attachment_path)
            else:
                return self._send_with_smtp(recipients, subject, body, html_body, attachment_path)
        except Exception as e:
            logger.error(f"Unexpected error sending email: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _send_with_flask_mail(self, recipients, subject, body, html_body, attachment_path):
        """Send email using Flask-Mail"""
        try:
            msg = Message(
                subject=subject,
                sender=(self.from_name, self.from_address),
                recipients=recipients,
                body=body,
                html=html_body
            )
            
            # Attach file if provided
            if attachment_path and Path(attachment_path).exists():
                try:
                    with open(attachment_path, 'rb') as f:
                        msg.attach(
                            Path(attachment_path).name,
                            'video/mp4',
                            f.read()
                        )
                    logger.info(f"Attached file: {attachment_path}")
                except Exception as e:
                    logger.error(f"Failed to attach file {attachment_path}: {e}")
            
            self.mail.send(msg)
            logger.info(f"Email sent via Flask-Mail to {len(recipients)} recipient(s)")
            return True
            
        except Exception as e:
            logger.error(f"Flask-Mail error: {e}")
            return False
    
    def _send_with_smtp(self, recipients, subject, body, html_body, attachment_path):
        """Send email using raw SMTP (fallback method)"""
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{self.from_name} <{self.from_address}>"
            msg['To'] = ', '.join(recipients)
            msg['Subject'] = subject
            
            # Attach plain text body
            msg.attach(MIMEText(body, 'plain'))
            
            # Attach HTML body if provided
            if html_body:
                msg.attach(MIMEText(html_body, 'html'))
            
            # Attach file if provided
            if attachment_path and Path(attachment_path).exists():
                try:
                    with open(attachment_path, 'rb') as f:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(f.read())
                        encoders.encode_base64(part)
                        part.add_header(
                            'Content-Disposition',
                            f'attachment; filename={Path(attachment_path).name}'
                        )
                        msg.attach(part)
                    logger.info(f"Attached file: {attachment_path}")
                except Exception as e:
                    logger.error(f"Failed to attach file {attachment_path}: {e}")
            
            # Connect and send
            if self.use_ssl:
                server = smtplib.SMTP_SSL(self.host, self.port)
            else:
                server = smtplib.SMTP(self.host, self.port)
            
            if self.use_tls and not self.use_ssl:
                server.starttls()
            
            server.login(self.username, self.password)
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Email sent via SMTP to {len(recipients)} recipient(s)")
            return True
            
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"Email authentication failed: {e}")
            logger.error("Check EMAIL_USERNAME and EMAIL_PASSWORD in config")
            return False
        except smtplib.SMTPException as e:
            logger.error(f"SMTP error sending email: {e}")
            return False
    
    def send_detection_alert(self, recipients: List[str], camera_name: str, 
                           model_name: str, confidence: float, timestamp: str,
                           detection_count: int = 0, zone_name: Optional[str] = None,
                           severity_level: str = 'MEDIUM', severity_score: int = 5,
                           video_clip_path: Optional[str] = None) -> bool:
        """
        Send a detection alert email
        
        Args:
            recipients: List of recipient email addresses
            camera_name: Name of the camera
            model_name: Detection model name
            confidence: Detection confidence
            timestamp: Detection timestamp
            detection_count: Number of detections
            zone_name: Restricted zone name if applicable
            severity_level: Severity level (LOW/MEDIUM/HIGH/CRITICAL)
            severity_score: Severity score (1-10)
            video_clip_path: Path to video clip attachment
        
        Returns:
            bool: True if sent successfully
        """
        # Determine severity color
        severity_colors = {
            'LOW': '#4CAF50',
            'MEDIUM': '#FF9800',
            'HIGH': '#F44336',
            'CRITICAL': '#9C27B0'
        }
        color = severity_colors.get(severity_level, '#FF9800')
        
        # Build subject
        if model_name == 'crowd':
            subject = f"🚨 CEMSS CROWD ALERT - {camera_name}"
        else:
            subject = f"🚨 CEMSS {severity_level} ALERT - {model_name.title()} Detected - {camera_name}"
        
        # Build plain text body
        zone_info = f"\n⚠️ Restricted Zone: {zone_name}" if zone_name else ""
        
        if model_name == 'crowd':
            body = f"""CEMSS CROWD ALERT

Camera: {camera_name}
Crowd Detected: {detection_count} people
Confidence: {confidence:.0%}
Time: {timestamp}{zone_info}

Severity: {severity_level} (Score: {severity_score}/10)

This is an automated alert from CEMSS Surveillance System.
{'Video clip attached.' if video_clip_path else 'No video clip available.'}
"""
        else:
            body = f"""CEMSS DETECTION ALERT

Camera: {camera_name}
Detection: {model_name.title()}
Confidence: {confidence:.0%}
Time: {timestamp}
Count: {detection_count}{zone_info}

Severity: {severity_level} (Score: {severity_score}/10)

This is an automated alert from CEMSS Surveillance System.
{'Video clip attached.' if video_clip_path else 'No video clip available.'}
"""
        
        # Build HTML body
        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: {color}; color: white; padding: 20px; border-radius: 5px 5px 0 0; }}
        .content {{ background: #f9f9f9; padding: 20px; border: 1px solid #ddd; }}
        .info-row {{ margin: 10px 0; }}
        .label {{ font-weight: bold; color: #555; }}
        .value {{ color: #000; }}
        .severity {{ background: {color}; color: white; padding: 5px 10px; border-radius: 3px; display: inline-block; }}
        .footer {{ background: #333; color: white; padding: 10px; text-align: center; border-radius: 0 0 5px 5px; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1 style="margin: 0;">🚨 CEMSS {'CROWD' if model_name == 'crowd' else 'DETECTION'} ALERT</h1>
        </div>
        <div class="content">
            <div class="info-row">
                <span class="label">Camera:</span> <span class="value">{camera_name}</span>
            </div>
            <div class="info-row">
                <span class="label">Detection:</span> <span class="value">{model_name.title()}</span>
            </div>
            <div class="info-row">
                <span class="label">Confidence:</span> <span class="value">{confidence:.0%}</span>
            </div>
            <div class="info-row">
                <span class="label">Time:</span> <span class="value">{timestamp}</span>
            </div>
            <div class="info-row">
                <span class="label">Count:</span> <span class="value">{detection_count}</span>
            </div>
            {f'<div class="info-row"><span class="label">⚠️ Restricted Zone:</span> <span class="value">{zone_name}</span></div>' if zone_name else ''}
            <div class="info-row">
                <span class="label">Severity:</span> <span class="severity">{severity_level} (Score: {severity_score}/10)</span>
            </div>
            {f'<div class="info-row" style="margin-top: 20px; color: #4CAF50;">✅ Video clip attached</div>' if video_clip_path else ''}
        </div>
        <div class="footer">
            This is an automated alert from CEMSS Surveillance System
        </div>
    </div>
</body>
</html>
"""
        
        return self.send_email(recipients, subject, body, html_body, video_clip_path)
    
    def send_manual_alert(self, recipients: List[str], camera_name: str, 
                        message: str, user: str, timestamp: str,
                        video_clip_path: Optional[str] = None) -> bool:
        """
        Send a manual alert email
        
        Args:
            recipients: List of recipient email addresses
            camera_name: Name of the camera
            message: Custom message
            user: User who triggered the alert
            timestamp: Alert timestamp
            video_clip_path: Path to video clip attachment
        
        Returns:
            bool: True if sent successfully
        """
        subject = f"⚠️ CEMSS MANUAL ALERT - {camera_name}"
        
        body = f"""CEMSS MANUAL ALERT

Camera: {camera_name}
Triggered By: {user}
Time: {timestamp}

Message:
{message}

This is a manual alert from CEMSS Surveillance System.
{'Video clip attached.' if video_clip_path else 'No video clip available.'}
"""
        
        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: #2196F3; color: white; padding: 20px; border-radius: 5px 5px 0 0; }}
        .content {{ background: #f9f9f9; padding: 20px; border: 1px solid #ddd; }}
        .info-row {{ margin: 10px 0; }}
        .label {{ font-weight: bold; color: #555; }}
        .value {{ color: #000; }}
        .message {{ background: white; padding: 15px; border-left: 4px solid #2196F3; margin: 15px 0; }}
        .footer {{ background: #333; color: white; padding: 10px; text-align: center; border-radius: 0 0 5px 5px; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1 style="margin: 0;">⚠️ CEMSS MANUAL ALERT</h1>
        </div>
        <div class="content">
            <div class="info-row">
                <span class="label">Camera:</span> <span class="value">{camera_name}</span>
            </div>
            <div class="info-row">
                <span class="label">Triggered By:</span> <span class="value">{user}</span>
            </div>
            <div class="info-row">
                <span class="label">Time:</span> <span class="value">{timestamp}</span>
            </div>
            <div class="message">
                <strong>Message:</strong><br>
                {message.replace(chr(10), '<br>')}
            </div>
            {f'<div class="info-row" style="margin-top: 20px; color: #4CAF50;">✅ Video clip attached</div>' if video_clip_path else ''}
        </div>
        <div class="footer">
            This is a manual alert from CEMSS Surveillance System
        </div>
    </div>
</body>
</html>
"""
        
        return self.send_email(recipients, subject, body, html_body, video_clip_path)


# Global email service instance
_email_service = None


def get_email_service(mail_instance=None):
    """
    Get or create global email service instance
    
    Args:
        mail_instance: Flask-Mail instance (optional, for Flask-Mail support)
    """
    global _email_service
    
    if _email_service is None:
        try:
            from config import (
                EMAIL_ENABLED, EMAIL_HOST, EMAIL_PORT, EMAIL_USERNAME, 
                EMAIL_PASSWORD, EMAIL_FROM_ADDRESS, EMAIL_FROM_NAME,
                EMAIL_USE_TLS, EMAIL_USE_SSL
            )
            
            if EMAIL_ENABLED:
                _email_service = EmailService(
                    host=EMAIL_HOST,
                    port=EMAIL_PORT,
                    username=EMAIL_USERNAME,
                    password=EMAIL_PASSWORD,
                    from_address=EMAIL_FROM_ADDRESS,
                    from_name=EMAIL_FROM_NAME,
                    use_tls=EMAIL_USE_TLS,
                    use_ssl=EMAIL_USE_SSL,
                    mail_instance=mail_instance
                )
            else:
                logger.info("Email service is disabled in configuration")
                _email_service = EmailService('', 0, '', '', '', '', False, False, None)
                _email_service.enabled = False
        except ImportError as e:
            logger.error(f"Failed to import email configuration: {e}")
            _email_service = EmailService('', 0, '', '', '', '', False, False, None)
            _email_service.enabled = False
    
    return _email_service

