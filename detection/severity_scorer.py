"""
CEMSS - Campus Event management and Surveillance System
Severity Scoring Engine

Calculates severity scores for detection events based on:
- Model type (fall > person in restricted zone > phone)
- Time of day (night hours increase severity)
- Zone violation (restricted zones increase severity)
- Confidence level
- Custom severity rules
"""
from datetime import datetime
from models import SeverityRule, RestrictedZone, db
from config import (
    SEVERITY_SCORING_ENABLED,
    BASE_SEVERITY_SCORES,
    NIGHT_HOURS_START,
    NIGHT_HOURS_END,
    NIGHT_TIME_SEVERITY_BOOST,
    RESTRICTED_ZONE_SEVERITY_BOOST,
    ALERT_PRIORITIES
)


class SeverityScorer:
    """Calculate severity scores for detection events"""
    
    def __init__(self, db_session=None):
        """
        Initialize severity scorer
        
        Args:
            db_session: SQLAlchemy database session (optional)
        """
        self.db_session = db_session or db.session
        self.enabled = SEVERITY_SCORING_ENABLED
    
    def calculate_severity(self, camera_id, model_name, confidence, timestamp=None, 
                          zone_id=None, detection_data=None):
        """
        Calculate severity score for a detection event
        
        Args:
            camera_id: Database ID of the camera
            model_name: Name of the detection model (person, fall, phone)
            confidence: Detection confidence (0.0 - 1.0)
            timestamp: Detection timestamp (defaults to now)
            zone_id: ID of restricted zone if detected in one
            detection_data: Additional detection data
        
        Returns:
            dict: {
                'score': int (1-10),
                'level': str (LOW/MEDIUM/HIGH/CRITICAL),
                'factors': list of contributing factors
            }
        """
        if not self.enabled:
            return {
                'score': 5,
                'level': 'MEDIUM',
                'factors': ['scoring_disabled']
            }
        
        timestamp = timestamp or datetime.now()
        factors = []
        
        # Start with base score for model type
        base_score = BASE_SEVERITY_SCORES.get(model_name, 5)
        score = base_score
        factors.append(f'base_{model_name}={base_score}')
        
        # Check for custom severity rules (highest priority)
        custom_score = self._check_custom_rules(camera_id, model_name, zone_id, timestamp)
        if custom_score is not None:
            score = max(score, custom_score)
            factors.append(f'custom_rule={custom_score}')
        
        # Time-based multiplier
        if self._is_night_time(timestamp):
            score += NIGHT_TIME_SEVERITY_BOOST
            factors.append(f'night_time=+{NIGHT_TIME_SEVERITY_BOOST}')
        
        # Zone violation multiplier
        if zone_id is not None:
            score += RESTRICTED_ZONE_SEVERITY_BOOST
            factors.append(f'restricted_zone=+{RESTRICTED_ZONE_SEVERITY_BOOST}')
        
        # Confidence factor (high confidence adds +1)
        if confidence >= 0.85:
            score += 1
            factors.append('high_confidence=+1')
        
        # Multi-model fusion boost (if detection_data indicates multiple models)
        if detection_data and isinstance(detection_data, dict):
            concurrent_models = detection_data.get('concurrent_models', [])
            if len(concurrent_models) > 1:
                score += 2
                factors.append('multi_model_fusion=+2')
        
        # Clamp score to 1-10 range
        score = max(1, min(10, int(score)))
        
        # Determine severity level from score
        level = self._score_to_level(score)
        
        return {
            'score': score,
            'level': level,
            'factors': factors
        }
    
    def _check_custom_rules(self, camera_id, model_name, zone_id, timestamp):
        """
        Check for custom severity rules that match this detection
        
        Returns:
            int or None: Severity score from matching rule, or None if no match
        """
        # Query active severity rules
        rules = SeverityRule.query.filter_by(is_active=True).all()
        
        matched_score = None
        
        for rule in rules:
            # Check if rule matches this detection
            if rule.model_name and rule.model_name != model_name:
                continue
            
            if rule.zone_id and rule.zone_id != zone_id:
                continue
            
            # Check time window
            if rule.time_window_start and rule.time_window_end:
                current_time = timestamp.time()
                if not self._time_in_window(current_time, rule.time_window_start, 
                                           rule.time_window_end):
                    continue
            
            # Rule matches - use highest matching score
            if matched_score is None or rule.severity_score > matched_score:
                matched_score = rule.severity_score
        
        return matched_score
    
    def _is_night_time(self, timestamp):
        """Check if timestamp is during night hours"""
        hour = timestamp.hour
        
        # Handle wraparound (e.g., 22:00 to 06:00)
        if NIGHT_HOURS_START > NIGHT_HOURS_END:
            return hour >= NIGHT_HOURS_START or hour < NIGHT_HOURS_END
        else:
            return NIGHT_HOURS_START <= hour < NIGHT_HOURS_END
    
    def _time_in_window(self, current_time, start_time, end_time):
        """Check if time falls within a window (handles midnight wraparound)"""
        if start_time <= end_time:
            return start_time <= current_time < end_time
        else:
            # Wraparound case
            return current_time >= start_time or current_time < end_time
    
    def _score_to_level(self, score):
        """Convert numeric score to severity level string"""
        for level, config in ALERT_PRIORITIES.items():
            if config['min_severity'] <= score <= config['max_severity']:
                return level
        return 'MEDIUM'  # fallback
    
    def get_priority_color(self, level):
        """Get color code for a priority level"""
        return ALERT_PRIORITIES.get(level, {}).get('color', '#808080')


# Global severity scorer instance
_scorer_instance = None


def get_severity_scorer():
    """Get global severity scorer instance (singleton)"""
    global _scorer_instance
    if _scorer_instance is None:
        _scorer_instance = SeverityScorer()
    return _scorer_instance
