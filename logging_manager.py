"""
CEMSS - Campus Event management and Surveillance System
Logging Manager
"""
import logging
import json
from datetime import datetime
from pathlib import Path
from config import LOGS_DIR, LOG_FORMAT, LOG_LEVEL, SESSION_LOG_FORMAT


class LoggingManager:
    """Manages session-based logging for CEMSS"""
    
    def __init__(self):
        self.session_start = datetime.now()
        self.session_log_file = LOGS_DIR / self.session_start.strftime(SESSION_LOG_FORMAT)
        self.detection_log_file = LOGS_DIR / f"detections_{self.session_start.strftime('%Y%m%d_%H%M%S')}.jsonl"
        self.incident_log_file = LOGS_DIR / f"incidents_{self.session_start.strftime('%Y%m%d_%H%M%S')}.jsonl"
        
        # Setup main logger
        self.logger = self._setup_logger()
        
        self.logger.info("="*80)
        self.logger.info(f"CEMSS Session Started: {self.session_start.isoformat()}")
        self.logger.info("="*80)
    
    def _setup_logger(self):
        """Setup the main application logger"""
        logger = logging.getLogger('CEMSS')
        logger.setLevel(getattr(logging, LOG_LEVEL))
        
        # File handler
        file_handler = logging.FileHandler(self.session_log_file)
        file_handler.setLevel(getattr(logging, LOG_LEVEL))
        file_formatter = logging.Formatter(LOG_FORMAT)
        file_handler.setFormatter(file_formatter)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, LOG_LEVEL))
        console_formatter = logging.Formatter('%(levelname)s - %(message)s')
        console_handler.setFormatter(console_formatter)
        
        # Add handlers
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def log_detection(self, camera_id, camera_name, model_name, confidence, 
                     detection_data=None, video_clip_path=None, note=None):
        """Log a detection event"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'camera_id': camera_id,
            'camera_name': camera_name,
            'model_name': model_name,
            'confidence': confidence,
            'detection_data': detection_data or {},
            'video_clip_path': video_clip_path,
            'note': note
        }
        
        # Write to JSONL file
        with open(self.detection_log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
        
        # Log to main logger
        note_text = f" - Note: {note}" if note else ""
        self.logger.info(
            f"Detection: Camera '{camera_name}' ({camera_id}) - "
            f"Model '{model_name}' - Confidence: {confidence:.2f}{note_text}"
        )
    
    def log_incident(self, camera_id, camera_name, incident_type, description, 
                    user=None, video_clip_path=None, is_manual=False):
        """Log an incident or alert"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'camera_id': camera_id,
            'camera_name': camera_name,
            'incident_type': incident_type,
            'description': description,
            'user': user,
            'video_clip_path': video_clip_path,
            'is_manual': is_manual
        }
        
        # Write to JSONL file
        with open(self.incident_log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
        
        # Log to main logger
        manual_tag = " [MANUAL]" if is_manual else ""
        self.logger.warning(
            f"Incident{manual_tag}: Camera '{camera_name}' ({camera_id}) - "
            f"Type: {incident_type} - {description}"
        )
    
    def log_alert_sent(self, camera_name, model_name, recipients, video_clip_path=None):
        """Log when an alert is sent"""
        self.logger.info(
            f"Alert Sent: Camera '{camera_name}' - Model '{model_name}' - "
            f"To: {', '.join(recipients)}"
        )
    
    def log_camera_event(self, camera_name, event_type, message):
        """Log camera-related events (connect, disconnect, error)"""
        self.logger.info(f"Camera '{camera_name}': {event_type} - {message}")
    
    def log_system_event(self, event_type, message):
        """Log system-level events"""
        self.logger.info(f"System: {event_type} - {message}")
    
    def get_session_summary(self):
        """Get a summary of the current session"""
        detection_count = 0
        incident_count = 0
        
        if self.detection_log_file.exists():
            with open(self.detection_log_file, 'r') as f:
                detection_count = sum(1 for _ in f)
        
        if self.incident_log_file.exists():
            with open(self.incident_log_file, 'r') as f:
                incident_count = sum(1 for _ in f)
        
        duration = datetime.now() - self.session_start
        
        return {
            'session_start': self.session_start.isoformat(),
            'duration_seconds': duration.total_seconds(),
            'detection_count': detection_count,
            'incident_count': incident_count,
            'log_file': str(self.session_log_file),
            'detection_log_file': str(self.detection_log_file),
            'incident_log_file': str(self.incident_log_file)
        }
    
    def close_session(self):
        """Close the logging session"""
        summary = self.get_session_summary()
        
        self.logger.info("="*80)
        self.logger.info("Session Summary:")
        self.logger.info(f"  Duration: {summary['duration_seconds']:.1f} seconds")
        self.logger.info(f"  Total Detections: {summary['detection_count']}")
        self.logger.info(f"  Total Incidents: {summary['incident_count']}")
        self.logger.info("="*80)
        self.logger.info("CEMSS Session Ended")
        
        # Close handlers
        for handler in self.logger.handlers[:]:
            handler.close()
            self.logger.removeHandler(handler)


# Global logging manager instance
_logging_manager = None

def get_logging_manager():
    """Get or create the global logging manager"""
    global _logging_manager
    if _logging_manager is None:
        _logging_manager = LoggingManager()
    return _logging_manager
