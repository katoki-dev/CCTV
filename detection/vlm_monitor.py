"""
CEMSS - Vision Language Model Monitor
Hybrid two-tier VLM monitoring for enhanced surveillance
"""
import requests
import base64
import cv2
import os
from datetime import datetime
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class VLMMonitor:
    """
    Hybrid VLM monitoring system with two-tier analysis:
    - Tier 1: Fast text-based threat assessment (qwen2.5:0.5b)
    - Tier 2: Detailed vision analysis (llava:7b)
    """
    
    def __init__(self, 
                 tier1_model='qwen2.5:0.5b',
                 tier2_model='llava:7b',
                 ollama_host='http://localhost:11434'):
        """
        Initialize VLM Monitor
        
        Args:
            tier1_model: Fast scanning model name
            tier2_model: Detailed vision model name
            ollama_host: Ollama API endpoint
        """
        self.tier1_model = tier1_model
        self.tier2_model = tier2_model
        self.ollama_host = ollama_host
        self.enabled = True
        
        logger.info(f"VLM Monitor initialized: Tier1={tier1_model}, Tier2={tier2_model}")
    
    def tier1_fast_scan(self, context: str) -> Dict[str, Any]:
        """
        Tier 1: Fast text-based threat assessment
        
        Args:
            context: Contextual information about the frame/detection
            
        Returns:
            Dictionary with assessment results
        """
        prompt = f"""Security AI rapid threat assessment:

{context}

Provide:
1. Threat Level: LOW/MEDIUM/HIGH
2. Keywords: 2-3 key observations
3. Action: MONITOR / INVESTIGATE / ALERT

Response format:
THREAT: [level]
KEYWORDS: [keyword1, keyword2, keyword3]
ACTION: [action]
REASONING: [1 sentence]"""

        try:
            response = requests.post(
                f'{self.ollama_host}/api/generate',
                json={
                    'model': self.tier1_model,
                    'prompt': prompt,
                    'stream': False,
                    'options': {
                        'temperature': 0.3,  # Lower for more consistent assessments
                        'num_predict': 150
                    }
                },
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                assessment = result.get('response', '')
                
                # Parse response
                threat_level = self._extract_threat_level(assessment)
                keywords = self._extract_keywords(assessment)
                action = self._extract_action(assessment)
                
                return {
                    'success': True,
                    'model': self.tier1_model,
                    'threat_level': threat_level,
                    'keywords': keywords,
                    'action': action,
                    'raw_assessment': assessment,
                    'timestamp': datetime.now().isoformat()
                }
            else:
                logger.error(f"Tier 1 API error: {response.status_code}")
                return {
                    'success': False,
                    'error': f"API returned {response.status_code}"
                }
                
        except Exception as e:
            logger.error(f"Tier 1 scan error: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def tier2_detailed_vision(self, frame_path: str, detection_info: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Tier 2: Detailed visual analysis with VLM
        
        Args:
            frame_path: Path to image file
            detection_info: Optional detection metadata
            
        Returns:
            Dictionary with detailed analysis
        """
        if not os.path.exists(frame_path):
            return {'success': False, 'error': 'Frame file not found'}
        
        # Encode image
        try:
            with open(frame_path, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode('utf-8')
        except Exception as e:
            logger.error(f"Image encoding error: {e}")
            return {'success': False, 'error': str(e)}
        
        # Build prompt
        detection_context = ""
        if detection_info:
            detection_context = f"Detection Type: {detection_info.get('type', 'Unknown')}\n"
            detection_context += f"Confidence: {detection_info.get('confidence', 0):.0%}\n"
        
        prompt = f"""Analyze this surveillance frame in detail:

{detection_context}

Provide:
1. SCENE: What do you see?
2. PEOPLE: Count and activities
3. SAFETY CONCERNS: Any risks?
4. RECOMMENDATION: Security action needed

Be specific and security-focused."""

        try:
            response = requests.post(
                f'{self.ollama_host}/api/generate',
                json={
                    'model': self.tier2_model,
                    'prompt': prompt,
                    'images': [image_data],
                    'stream': False,
                    'options': {
                        'temperature': 0.5,
                        'num_predict': 300
                    }
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                analysis = result.get('response', '')
                
                return {
                    'success': True,
                    'model': self.tier2_model,
                    'visual_analysis': analysis,
                    'timestamp': datetime.now().isoformat()
                }
            else:
                logger.error(f"Tier 2 API error: {response.status_code}")
                return {
                    'success': False,
                    'error': f"API returned {response.status_code}"
                }
                
        except Exception as e:
            logger.error(f"Tier 2 analysis error: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def analyze_detection(self, 
                         camera_id: int,
                         detection_type: str,
                         confidence: float,
                         frame=None,
                         frame_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Full hybrid analysis of a detection event
        
        Args:
            camera_id: Camera identifier
            detection_type: Type of detection (fall, person, etc.)
            confidence: Detection confidence
            frame: Optional CV2 frame array
            frame_path: Optional path to saved frame
            
        Returns:
            Complete analysis results
        """
        if not self.enabled:
            return {'enabled': False}
        
        # Build context for Tier 1
        context = f"""Camera ID: {camera_id}
Detection: {detection_type}
Confidence: {confidence:.1%}
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Context: Surveillance system detected {detection_type} event."""

        # Run Tier 1
        tier1_result = self.tier1_fast_scan(context)
        
        # Determine if Tier 2 is needed
        run_tier2 = False
        if tier1_result.get('success'):
            threat_level = tier1_result.get('threat_level', '').upper()
            run_tier2 = threat_level in ['HIGH', 'MEDIUM']
        
        # Run Tier 2 if needed and frame is available
        tier2_result = None
        if run_tier2:
            # Save frame if needed
            temp_frame_path = frame_path
            if frame is not None and frame_path is None:
                temp_frame_path = f'temp_vlm_frame_{camera_id}.jpg'
                cv2.imwrite(temp_frame_path, frame)
            
            if temp_frame_path and os.path.exists(temp_frame_path):
                tier2_result = self.tier2_detailed_vision(
                    temp_frame_path,
                    {'type': detection_type, 'confidence': confidence}
                )
                
                # Cleanup temp file
                if frame is not None and frame_path is None:
                    try:
                        os.remove(temp_frame_path)
                    except:
                        pass
        
        return {
            'camera_id': camera_id,
            'detection_type': detection_type,
            'tier1': tier1_result,
            'tier2': tier2_result,
            'tier2_triggered': run_tier2,
            'timestamp': datetime.now().isoformat()
        }
    
    def _extract_threat_level(self, text: str) -> str:
        """Extract threat level from assessment text"""
        text_upper = text.upper()
        if 'HIGH' in text_upper:
            return 'HIGH'
        elif 'MEDIUM' in text_upper:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def _extract_keywords(self, text: str) -> list:
        """Extract keywords from assessment text"""
        # Simple extraction - look for KEYWORDS: line
        for line in text.split('\n'):
            if 'KEYWORDS:' in line.upper() or 'KEY OBSERVATIONS' in line.upper():
                keywords_text = line.split(':', 1)[1] if ':' in line else line
                keywords = [k.strip() for k in keywords_text.split(',')]
                return keywords[:3]  # Max 3
        return []
    
    def _extract_action(self, text: str) -> str:
        """Extract recommended action from assessment text"""
        text_upper = text.upper()
        if 'ALERT' in text_upper:
            return 'ALERT'
        elif 'INVESTIGATE' in text_upper:
            return 'INVESTIGATE'
        else:
            return 'MONITOR'
    
    def check_availability(self) -> Dict[str, bool]:
        """Check if VLM models are available"""
        try:
            response = requests.get(f'{self.ollama_host}/api/tags', timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                model_names = [m.get('name', '') for m in models]
                
                return {
                    'ollama_running': True,
                    'tier1_available': self.tier1_model in model_names,
                    'tier2_available': self.tier2_model in model_names
                }
        except:
            pass
        
        return {
            'ollama_running': False,
            'tier1_available': False,
            'tier2_available': False
        }
