"""
CASS - Advanced Prompt Engineering System
Centralized, sophisticated prompts for VLM and LLM integration.

This module provides context-aware, role-specific prompts that enhance
user experience and ensure consistent, professional AI responses.
"""

from typing import Dict, Optional, List
from datetime import datetime


# ============================================================================
# CORE SYSTEM IDENTITY
# ============================================================================

SYSTEM_IDENTITY = """You are **CASS** (Camera Alert Surveillance System), an advanced AI security assistant.

**CORE DIRECTIVES:**
1. 🔒 **Security First**: Prioritize safety observations and potential threats.
2. 🗣️ **English Only**: ALWAYS respond in English. Never use any other language.
3. ✍️ **Professional Tone**: Be concise, clear, and actionable.
4. 🎯 **Context Awareness**: Tailor responses to the user's role and query type.
5. 🚫 **No Hallucination**: Only describe what you can verify. Say "I cannot determine" if unsure."""


# ============================================================================
# VLM PROMPTS - Vision Language Model (for analyzing frames/video)
# ============================================================================

class VLMPrompts:
    """Sophisticated prompts for Vision Language Model analysis"""
    
    @staticmethod
    def continuous_monitoring(camera_id: int, location: str = None) -> Dict[str, str]:
        """
        Prompt for continuous background monitoring.
        Optimized for factual, observation-only descriptions with no speculation.
        """
        context = f"Camera {camera_id}"
        if location:
            context += f" ({location})"
            
        return {
            'system': f"""You are CASS, a surveillance monitoring AI for {context}.

**STRICT OBSERVATION RULES:**
⚠️ ONLY describe what you can DIRECTLY SEE in these frames.
⚠️ NEVER speculate about intent, emotions, or what "might" happen.
⚠️ NEVER describe sounds, smells, or things outside the frame.
⚠️ Do NOT use phrases like "appears to be", "seems like", "might be", "possibly", "probably".

**WHAT TO REPORT:**
✓ Number of people visible (exact count if ≤5, "several" if 6-10, "many" if >10)
✓ Physical positions (standing, sitting, walking, running)
✓ Direction of movement (left, right, toward camera, away)
✓ Visible objects being carried or present
✓ Clothing colors and types
✓ Environmental conditions visible (lighting, weather if outdoor)

**WHAT TO AVOID:**
✗ Assumptions about identity or purpose
✗ Emotional states or intentions
✗ Predictions about future actions
✗ Describing things not visible in frame

**FORMAT:** One concise sentence describing the observable scene. English only.""",
            
            'question': """Describe ONLY what is directly visible in these frames.
Count people, state their positions and movements, note visible objects.
Do NOT speculate or assume anything not clearly visible."""
        }
    
    @staticmethod
    def crowd_analysis() -> Dict[str, str]:
        """Specialized prompt for crowd density and safety analysis"""
        return {
            'system': """You are CASS Crowd Safety Analyst - specialized in crowd dynamics and safety assessment.

**ANALYSIS FRAMEWORK:**
1. **Density Estimation**:
   - LOW: Sparse, individuals clearly distinguishable, free movement
   - MEDIUM: Moderate crowd, some clustering, movement possible
   - HIGH: Dense crowd, limited movement, potential bottlenecks
   - CRITICAL: Overcrowded, safety risk, immediate attention required

2. **Behavior Assessment**:
   - Movement pattern (static/flowing/chaotic)
   - Crowd mood indicators (calm/anxious/agitated)
   - Potential pressure points or bottlenecks

3. **Safety Indicators**:
   - Clear evacuation paths
   - Crowd crush risk areas
   - Unusual gathering patterns

**OUTPUT FORMAT:**
Density: [LEVEL] | Count Estimate: [X-Y people]
Movement: [PATTERN]
Safety: [ASSESSMENT]
Action: [RECOMMENDATION if needed]""",
            
            'question': """Analyze crowd density and safety in this scene.
Provide: estimated count, density level, movement pattern, and safety assessment.
Flag any concerns requiring attention."""
        }
    
    @staticmethod
    def threat_assessment() -> Dict[str, str]:
        """Specialized prompt for security threat identification"""
        return {
            'system': """You are CASS Threat Analyst - specialized in security threat identification.

**THREAT ASSESSMENT PROTOCOL:**
⚠️ IMPORTANT: Only report OBSERVABLE evidence. Do not speculate or assume threats.

**OBSERVATION CATEGORIES:**
1. **People Behavior**:
   - Aggressive postures or movements
   - Suspicious loitering or surveillance behavior
   - Unauthorized access attempts
   - Physical altercations

2. **Object Detection**:
   - Unattended bags or packages
   - Visible weapons or weapon-like objects
   - Destructive tools or materials

3. **Environmental Anomalies**:
   - Forced entry signs
   - Unusual smoke or fire indicators
   - Barrier breaches

**THREAT LEVELS:**
- GREEN: Normal activity, no concerns
- YELLOW: Unusual but not immediately threatening
- ORANGE: Suspicious activity requiring attention
- RED: Active threat requiring immediate response

**OUTPUT FORMAT:**
Status: [LEVEL]
Observation: [What you see]
Concern: [Why it's flagged, if applicable]
Recommended: [Action if needed]""",
            
            'question': """Conduct a security threat assessment of this scene.
Report threat level, specific observations, and any recommended actions.
Only report what you can directly observe. Do not speculate."""
        }
    
    @staticmethod
    def general_scene_description(camera_name: str = None, user_question: str = None) -> Dict[str, str]:
        """General purpose scene analysis prompt"""
        camera_context = f" for {camera_name}" if camera_name else ""
        
        return {
            'system': f"""You are CASS, providing visual intelligence{camera_context}.

**OBSERVATION GUIDELINES:**
- Describe the scene accurately and professionally.
- Highlight security-relevant details (people, vehicles, activities).
- Note any anomalies or changes from typical patterns.
- If asked a specific question, answer it directly using visual evidence.
- Be concise but thorough.

**DESCRIPTION STRUCTURE:**
1. **Setting**: Location type and general environment
2. **Activity**: What is happening (people, movement, actions)  
3. **Notable**: Anything unusual or security-relevant
4. **Assessment**: Brief summary of scene status""",
            
            'question': user_question or "Describe what you see in this scene, focusing on people, activities, and anything security-relevant."
        }
    
    @staticmethod
    def person_identification() -> Dict[str, str]:
        """Prompt for detailed person description (not facial recognition)"""
        return {
            'system': """You are CASS Person Descriptor - providing detailed visual descriptions for security purposes.

**DESCRIPTION PROTOCOL:**
⚠️ NO facial recognition or identity speculation. Describe observable attributes only.

**ATTRIBUTES TO REPORT:**
1. **Physical**: Approximate height, build, apparent age range
2. **Clothing**: Colors, types, distinctive items
3. **Carried Items**: Bags, packages, equipment
4. **Behavior**: Actions, direction of movement, interactions
5. **Distinguishing Features**: Hats, glasses, distinctive clothing patterns

**OUTPUT FORMAT:**
Person [#]: [Build/Height] | [Clothing description] | [Carrying] | [Action]

Example:
Person 1: Medium build, adult | Blue jacket, dark pants | Backpack | Walking toward entrance""",
            
            'question': """Describe each visible person in detail.
Include: build, clothing, carried items, and current action.
Do not attempt facial recognition or identity speculation."""
        }


# ============================================================================
# PROMPT BUILDER FUNCTIONS
# ============================================================================

def get_vlm_prompt(
    prompt_type: str,
    camera_id: int = None,
    camera_name: str = None,
    location: str = None,
    user_question: str = None
) -> Dict[str, str]:
    """
    Get the appropriate VLM prompt based on context.
    
    Args:
        prompt_type: One of 'continuous', 'crowd', 'threat', 'general', 'person'
        camera_id: Camera ID for context
        camera_name: Camera name for context
        location: Camera location
        user_question: Optional specific question from user
        
    Returns:
        Dictionary with 'system' and 'question' prompts
    """
    prompt_map = {
        'continuous': lambda: VLMPrompts.continuous_monitoring(camera_id or 0, location),
        'crowd': VLMPrompts.crowd_analysis,
        'threat': VLMPrompts.threat_assessment,
        'person': VLMPrompts.person_identification,
        'general': lambda: VLMPrompts.general_scene_description(camera_name, user_question)
    }
    
    getter = prompt_map.get(prompt_type, prompt_map['general'])
    return getter() if callable(getter) else getter


# ============================================================================
# LOG SEARCH UTILITIES - Find events by timestamp/keywords
# ============================================================================

import os
import re
from datetime import datetime, timedelta
from typing import Tuple


class LogSearchEngine:
    """
    Search engine for continuous analysis logs.
    Enables finding specific events by timestamp, camera, and keywords.
    """
    
    LOG_PATH = os.path.join("logs", "continuous_analysis.log")
    # Log format: [YYYY-MM-DD HH:MM:SS] CAM_{id}: description
    LOG_PATTERN = re.compile(r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\] CAM_(\d+): (.+)')
    
    @classmethod
    def search_by_timestamp(
        cls,
        start_time: datetime = None,
        end_time: datetime = None,
        camera_id: int = None,
        max_results: int = 50
    ) -> List[Dict]:
        """
        Search analysis logs within a time range.
        
        Args:
            start_time: Start of search window (default: 1 hour ago)
            end_time: End of search window (default: now)
            camera_id: Optional camera filter
            max_results: Maximum results to return
            
        Returns:
            List of log entries with parsed fields
        """
        if not os.path.exists(cls.LOG_PATH):
            return []
        
        # Default time range: last 1 hour
        if not end_time:
            end_time = datetime.now()
        if not start_time:
            start_time = end_time - timedelta(hours=1)
        
        results = []
        try:
            with open(cls.LOG_PATH, 'r', encoding='utf-8') as f:
                for line in f:
                    match = cls.LOG_PATTERN.match(line.strip())
                    if match:
                        timestamp_str, cam_id, description = match.groups()
                        log_time = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                        
                        # Time filter
                        if not (start_time <= log_time <= end_time):
                            continue
                        
                        # Camera filter
                        if camera_id and int(cam_id) != camera_id:
                            continue
                        
                        results.append({
                            'timestamp': log_time,
                            'timestamp_str': timestamp_str,
                            'camera_id': int(cam_id),
                            'description': description,
                            'raw': line.strip()
                        })
                        
                        if len(results) >= max_results:
                            break
            
            # Return most recent first
            return sorted(results, key=lambda x: x['timestamp'], reverse=True)
            
        except Exception as e:
            return []
    
    @classmethod
    def search_by_keyword(
        cls,
        keywords: List[str],
        camera_id: int = None,
        hours_back: int = 24,
        max_results: int = 50,
        match_all: bool = False
    ) -> List[Dict]:
        """
        Search analysis logs for specific keywords.
        
        Args:
            keywords: List of keywords to search for
            camera_id: Optional camera filter
            hours_back: How many hours back to search
            max_results: Maximum results to return
            match_all: If True, all keywords must match; if False, any keyword matches
            
        Returns:
            List of matching log entries
        """
        if not os.path.exists(cls.LOG_PATH):
            return []
        
        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        keywords_lower = [k.lower() for k in keywords]
        
        results = []
        try:
            with open(cls.LOG_PATH, 'r', encoding='utf-8') as f:
                for line in f:
                    match = cls.LOG_PATTERN.match(line.strip())
                    if match:
                        timestamp_str, cam_id, description = match.groups()
                        log_time = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                        
                        # Time filter
                        if log_time < cutoff_time:
                            continue
                        
                        # Camera filter
                        if camera_id and int(cam_id) != camera_id:
                            continue
                        
                        # Keyword filter
                        desc_lower = description.lower()
                        if match_all:
                            keyword_match = all(k in desc_lower for k in keywords_lower)
                        else:
                            keyword_match = any(k in desc_lower for k in keywords_lower)
                        
                        if not keyword_match:
                            continue
                        
                        # Find which keywords matched
                        matched_keywords = [k for k in keywords if k.lower() in desc_lower]
                        
                        results.append({
                            'timestamp': log_time,
                            'timestamp_str': timestamp_str,
                            'camera_id': int(cam_id),
                            'description': description,
                            'matched_keywords': matched_keywords,
                            'raw': line.strip()
                        })
                        
                        if len(results) >= max_results:
                            break
            
            return sorted(results, key=lambda x: x['timestamp'], reverse=True)
            
        except Exception as e:
            return []
    
    @classmethod
    def find_event(
        cls,
        description_query: str,
        approximate_time: datetime = None,
        time_window_minutes: int = 30,
        camera_id: int = None
    ) -> Optional[Dict]:
        """
        Find a specific event by description and approximate time.
        Useful for locating recordings or investigating incidents.
        
        Args:
            description_query: What to search for (e.g., "person running", "crowd forming")
            approximate_time: Approximate time of the event (default: now)
            time_window_minutes: How many minutes before/after to search
            camera_id: Optional camera filter
            
        Returns:
            Best matching log entry or None
        """
        if not approximate_time:
            approximate_time = datetime.now()
        
        # Create search window
        start_time = approximate_time - timedelta(minutes=time_window_minutes)
        end_time = approximate_time + timedelta(minutes=time_window_minutes)
        
        # Get logs in time range
        logs = cls.search_by_timestamp(
            start_time=start_time,
            end_time=end_time,
            camera_id=camera_id,
            max_results=100
        )
        
        if not logs:
            return None
        
        # Score each log by keyword match
        query_words = description_query.lower().split()
        best_match = None
        best_score = 0
        
        for log in logs:
            desc_lower = log['description'].lower()
            # Count matching words
            score = sum(1 for word in query_words if word in desc_lower)
            # Bonus for proximity to approximate time
            time_diff = abs((log['timestamp'] - approximate_time).total_seconds())
            time_score = max(0, 1 - (time_diff / (time_window_minutes * 60)))
            
            total_score = score + (time_score * 0.5)
            
            if total_score > best_score:
                best_score = total_score
                best_match = log
        
        return best_match if best_score > 0 else None
    
    @classmethod
    def get_camera_timeline(
        cls,
        camera_id: int,
        hours_back: int = 1
    ) -> List[Dict]:
        """
        Get a chronological timeline of events for a specific camera.
        
        Args:
            camera_id: Camera to get timeline for
            hours_back: How many hours of history
            
        Returns:
            List of log entries in chronological order
        """
        logs = cls.search_by_timestamp(
            start_time=datetime.now() - timedelta(hours=hours_back),
            camera_id=camera_id,
            max_results=100
        )
        # Return in chronological order
        return sorted(logs, key=lambda x: x['timestamp'])
    
    @classmethod
    def summarize_activity(
        cls,
        camera_id: int = None,
        hours_back: int = 1
    ) -> Dict:
        """
        Generate an activity summary from logs.
        
        Args:
            camera_id: Optional camera filter (None = all cameras)
            hours_back: How many hours to summarize
            
        Returns:
            Summary dictionary with counts and patterns
        """
        logs = cls.search_by_timestamp(
            start_time=datetime.now() - timedelta(hours=hours_back),
            camera_id=camera_id,
            max_results=500
        )
        
        if not logs:
            return {
                'total_entries': 0,
                'cameras': {},
                'time_range': f"Last {hours_back} hour(s)",
                'status': 'No activity recorded'
            }
        
        # Aggregate by camera
        cameras = {}
        for log in logs:
            cam = log['camera_id']
            if cam not in cameras:
                cameras[cam] = {
                    'count': 0,
                    'first_entry': log['timestamp'],
                    'last_entry': log['timestamp'],
                    'sample_descriptions': []
                }
            cameras[cam]['count'] += 1
            cameras[cam]['first_entry'] = min(cameras[cam]['first_entry'], log['timestamp'])
            cameras[cam]['last_entry'] = max(cameras[cam]['last_entry'], log['timestamp'])
            if len(cameras[cam]['sample_descriptions']) < 3:
                cameras[cam]['sample_descriptions'].append(log['description'][:100])
        
        return {
            'total_entries': len(logs),
            'cameras': cameras,
            'time_range': f"Last {hours_back} hour(s)",
            'oldest_entry': min(l['timestamp'] for l in logs).strftime('%H:%M:%S'),
            'newest_entry': max(l['timestamp'] for l in logs).strftime('%H:%M:%S'),
            'status': 'Active monitoring'
        }


def parse_time_from_message(message: str) -> Tuple[Optional[datetime], Optional[datetime]]:
    """
    Parse time references from natural language.
    
    Args:
        message: User message containing time references
        
    Returns:
        Tuple of (start_time, end_time) or (None, None) if not found
    """
    message_lower = message.lower()
    now = datetime.now()
    
    # Relative time patterns
    if 'last hour' in message_lower or 'past hour' in message_lower:
        return (now - timedelta(hours=1), now)
    
    if 'last 30 minutes' in message_lower or 'past 30 minutes' in message_lower:
        return (now - timedelta(minutes=30), now)
    
    if 'last 15 minutes' in message_lower or 'past 15 minutes' in message_lower:
        return (now - timedelta(minutes=15), now)
    
    if 'today' in message_lower:
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        return (start_of_day, now)
    
    if 'this morning' in message_lower:
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        noon = now.replace(hour=12, minute=0, second=0, microsecond=0)
        return (start_of_day, min(noon, now))
    
    if 'this afternoon' in message_lower:
        noon = now.replace(hour=12, minute=0, second=0, microsecond=0)
        evening = now.replace(hour=18, minute=0, second=0, microsecond=0)
        return (noon, min(evening, now))
    
    # Try to parse specific times like "at 2:30" or "around 14:00"
    time_match = re.search(r'(?:at|around|about)\s+(\d{1,2}):?(\d{2})?\s*(am|pm)?', message_lower)
    if time_match:
        hour = int(time_match.group(1))
        minute = int(time_match.group(2) or 0)
        meridiem = time_match.group(3)
        
        if meridiem == 'pm' and hour < 12:
            hour += 12
        elif meridiem == 'am' and hour == 12:
            hour = 0
        
        try:
            target_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            # If time is in the future, assume yesterday
            if target_time > now:
                target_time -= timedelta(days=1)
            # 30-minute window around the specified time
            return (target_time - timedelta(minutes=15), target_time + timedelta(minutes=15))
        except ValueError:
            pass
    
    return (None, None)
