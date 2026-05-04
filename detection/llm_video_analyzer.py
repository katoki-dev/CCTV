"""
CEMSS - LLM Video Analyzer
Wrapper for VLM analysis of video clips for specific detection verification
"""
import logging
from typing import Dict, Any, Optional
from utils.vlm_frame_analyzer import VLMFrameAnalyzer

logger = logging.getLogger(__name__)

class LLMVideoAnalyzer:
    """
    Analyzes video clips using VLM to verify detections (e.g. falls)
    """
    
    def __init__(self, ollama_host: str, model: str):
        """
        Initialize LLM Video Analyzer
        
        Args:
            ollama_host: Ollama server URL
            model: VLM model name
        """
        self.ollama_host = ollama_host
        self.model = model
        self.vlm = VLMFrameAnalyzer(ollama_host, model) 
        
    def is_available(self) -> bool:
        """Check if VLM service is available"""
        return self.vlm.is_available()
        
    def analyze_clip(self, video_path: str, num_frames: int = 5, analysis_type: str = 'general') -> Dict[str, Any]:
        """
        Analyze a video clip
        
        Args:
            video_path: Path to video file
            num_frames: Number of keyframes to extract
            analysis_type: Type of analysis ('fall_detection', 'violence', 'general')
            
        Returns:
            Dict with analysis results
        """
        if not self.is_available():
            return {'success': False, 'error': 'VLM not available'}
            
        # Determine prompt based on verification type
        prompt = ""
        if analysis_type == 'fall_detection':
            prompt = (
                "Analyze this video sequence of a potential fall event. "
                "Did a person clearly fall down? "
                "Respond in English only in this EXACT format:\n"
                "FALL_DETECTED: [YES/NO]\n"
                "CONFIDENCE: [HIGH/MEDIUM/LOW]\n"
                "SUMMARY: [Brief description of what happened]"
            )
        elif analysis_type == 'violence':
            prompt = (
                "Analyze this video sequence for physical violence or fighting. "
                "Is there clear physical violence? "
                "Respond in English only in this EXACT format:\n"
                "VIOLENCE_DETECTED: [YES/NO]\n"
                "CONFIDENCE: [HIGH/MEDIUM/LOW]\n"
                "SUMMARY: [Brief description]"
            )
        else:
            prompt = "Describe what is happening in this video sequence in detail. Respond in English only."
            
        try:
            # Use VLM to analyze video
            # We use analyze_video from VLMFrameAnalyzer but we need to handle the frame extraction 
            # internally there or pass logic. VLMFrameAnalyzer.analyze_video does exactly what we need.
            
            result = self.vlm.analyze_video(
                video_path=video_path,
                question=prompt
            )
            
            if not result['success']:
                return result
                
            response_text = result['response']
            
            # Parse structured response for specific types
            parsed_result = {
                'success': True,
                'raw_response': response_text,
                'analysis_time': result.get('timestamp'),
                'summary': response_text 
            }
            
            if analysis_type == 'fall_detection':
                # Parse customized format
                parsed_result['fall_detected'] = 'FALL_DETECTED: YES' in response_text.upper()
                
                confidence = 'LOW'
                if 'CONFIDENCE: HIGH' in response_text.upper():
                    confidence = 'HIGH'
                elif 'CONFIDENCE: MEDIUM' in response_text.upper():
                    confidence = 'MEDIUM'
                parsed_result['confidence'] = confidence
                
                # Extract summary if possible
                if 'SUMMARY:' in response_text:
                    parsed_result['summary'] = response_text.split('SUMMARY:')[1].strip()
                    
            elif analysis_type == 'violence':
                parsed_result['violence_detected'] = 'VIOLENCE_DETECTED: YES' in response_text.upper()
                
                confidence = 'LOW'
                if 'CONFIDENCE: HIGH' in response_text.upper():
                    confidence = 'HIGH'
                elif 'CONFIDENCE: MEDIUM' in response_text.upper():
                    confidence = 'MEDIUM'
                parsed_result['confidence'] = confidence
                
                if 'SUMMARY:' in response_text:
                    parsed_result['summary'] = response_text.split('SUMMARY:')[1].strip()
            
            return parsed_result
            
        except Exception as e:
            logger.error(f"Error in LLMVideoAnalyzer: {e}")
            return {'success': False, 'error': str(e)}
