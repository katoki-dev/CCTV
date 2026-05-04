"""
CASS - VLM Verifier
Automatic detection verification using Vision Language Models
"""
import os
import base64
import json
import requests
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Tuple, Optional

from config import (
    OLLAMA_HOST, VLM_VERIFICATION_MODEL, VLM_VERIFICATION_TIMEOUT,
    VLM_MIN_CONFIDENCE
)

logger = logging.getLogger(__name__)


class VLMVerifier:
    """Uses VLM to automatically verify detection correctness"""
    
    # Specialized prompts for each detection type
    VERIFICATION_PROMPTS = {
        'violence': {
            'prompt': "Analyze this image carefully. Is there any violent behavior, fighting, or aggressive physical contact visible between people? Answer with YES, NO, or UNCERTAIN, then explain briefly what you see.",
            'keywords': ['fight', 'hitting', 'violence', 'aggressive', 'attack', 'punch', 'kick']
        },
        'fall': {
            'prompt': "Is there a person who has fallen down or appears to be lying on the ground in distress in this image? Look for someone who is not standing upright. Answer YES, NO, or UNCERTAIN, then explain what you observe.",
            'keywords': ['fallen', 'lying', 'ground', 'floor', 'collapsed', 'down']
        },
        'phone': {
            'prompt': "Is someone holding or using a mobile phone/smartphone in this image? Look carefully at people's hands. Answer YES, NO, or UNCERTAIN, then describe what you see.",
            'keywords': ['phone', 'mobile', 'smartphone', 'holding', 'device']
        },
        'person': {
            'prompt': "How many people can you clearly see in this image? Count only distinct individuals. Provide the count and briefly describe their locations.",
            'keywords': ['person', 'people', 'individual', 'human']
        }
    }
    
    def __init__(self):
        """Initialize VLM verifier"""
        self.ollama_host = OLLAMA_HOST
        self.model = VLM_VERIFICATION_MODEL
        self.timeout = VLM_VERIFICATION_TIMEOUT
        self.min_confidence = VLM_MIN_CONFIDENCE
    
    def verify_detection(
        self,
        image_path: str,
        model_name: str,
        detection_data: Dict = None
    ) -> Optional[Dict]:
        """
        Verify a single detection using VLM
        
        Args:
            image_path: Path to the detection image
            model_name: Type of detection (violence, fall, phone, person)
            detection_data: Optional detection metadata
        
        Returns:
            Dict with verification results or None if failed
        """
        try:
            # Build verification prompt
            prompt = self._build_verification_prompt(model_name, detection_data)
            
            # Read and encode image
            if not os.path.exists(image_path):
                logger.error(f"Image not found: {image_path}")
                return None
            
            with open(image_path, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode('utf-8')
            
            # Call Ollama VLM API
            response = requests.post(
                f"{self.ollama_host}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "images": [image_data],
                    "stream": False
                },
                timeout=self.timeout
            )
            
            if response.status_code != 200:
                logger.error(f"VLM API error: {response.status_code}")
                return None
            
            vlm_response = response.json().get('response', '')
            
            # Parse VLM response
            verification_result, confidence = self._parse_vlm_response(
                vlm_response, model_name, detection_data
            )
            
            return {
                'verification_result': verification_result,
                'confidence': confidence,
                'vlm_response': vlm_response,
                'vlm_model_used': self.model,
                'timestamp': datetime.now()
            }
        
        except Exception as e:
            logger.error(f"Error in VLM verification: {str(e)}")
            return None
    
    def _build_verification_prompt(self, model_name: str, detection_data: Dict = None) -> str:
        """
        Build model-specific verification prompt
        
        Args:
            model_name: Type of detection
            detection_data: Optional detection metadata
        
        Returns:
            Prompt string for VLM
        """
        base_prompt = self.VERIFICATION_PROMPTS.get(model_name, {}).get(
            'prompt',
            "Describe what you see in this image."
        )
        
        # Add context if available
        if detection_data:
            if model_name == 'person' and 'count' in detection_data:
                base_prompt += f"\n\nNote: The detection system counted {detection_data['count']} person(s)."
            elif 'confidence' in detection_data:
                base_prompt += f"\n\nNote: The detection system reported {detection_data['confidence']:.1%} confidence."
        
        return base_prompt
    
    def _parse_vlm_response(
        self,
        vlm_response: str,
        model_name: str,
        detection_data: Dict = None
    ) -> Tuple[str, float]:
        """
        Parse VLM response to extract verification result
        
        Args:
            vlm_response: Raw VLM response text
            model_name: Type of detection
            detection_data: Optional detection metadata
        
        Returns:
            Tuple of (verification_result, confidence)
            verification_result: CORRECT, INCORRECT, UNCERTAIN
            confidence: 0-1 confidence in the verification
        """
        vlm_lower = vlm_response.lower()
        
        # Default to uncertain
        result = 'UNCERTAIN'
        confidence = 0.5
        
        if model_name == 'person':
            # For person detection, parse count
            result, confidence = self._parse_person_count(vlm_response, detection_data)
        else:
            # For binary detections (violence, fall, phone)
            # Look for YES/NO in response
            if vlm_lower.startswith('yes') or 'yes,' in vlm_lower or 'yes.' in vlm_lower:
                result = 'CORRECT'
                confidence = self._calculate_vlm_confidence(vlm_response, model_name, True)
            elif vlm_lower.startswith('no') or 'no,' in vlm_lower or 'no.' in vlm_lower:
                result = 'INCORRECT'
                confidence = self._calculate_vlm_confidence(vlm_response, model_name, False)
            elif 'uncertain' in vlm_lower or 'unclear' in vlm_lower or 'cannot' in vlm_lower:
                result = 'UNCERTAIN'
                confidence = 0.5
            else:
                # Check for keywords
                keywords = self.VERIFICATION_PROMPTS.get(model_name, {}).get('keywords', [])
                keyword_count = sum(1 for kw in keywords if kw in vlm_lower)
                if keyword_count >= 2:
                    result = 'CORRECT'
                    confidence = min(0.6 + (keyword_count * 0.1), 0.9)
        
        return result, confidence
    
    def _parse_person_count(self, vlm_response: str, detection_data: Dict = None) -> Tuple[str, float]:
        """Parse person count from VLM response"""
        import re
        
        vlm_lower = vlm_response.lower()
        
        # Try to extract number from response
        numbers = re.findall(r'\b(\d+)\b', vlm_response.split('.')[0])  # Look in first sentence
        
        if not numbers:
            return 'UNCERTAIN', 0.5
        
        vlm_count = int(numbers[0])
        
        if not detection_data or 'count' not in detection_data:
            # No detection data to compare
            return 'UNCERTAIN', 0.6
        
        detected_count = detection_data['count']
        
        # Compare counts
        if vlm_count == detected_count:
            result = 'CORRECT'
            confidence = 0.9
        elif abs(vlm_count - detected_count) == 1:
            # Off by one is still reasonable
            result = 'CORRECT'
            confidence = 0.7
        elif abs(vlm_count - detected_count) <= 2:
            # Close enough
            result = 'UNCERTAIN'
            confidence = 0.6
        else:
            result = 'INCORRECT'
            confidence = 0.8
        
        return result, confidence
    
    def _calculate_vlm_confidence(self, vlm_response: str, model_name: str, positive: bool) -> float:
        """
        Calculate confidence in VLM's assessment
        
        Args:
            vlm_response: VLM response text
            model_name: Type of detection
            positive: Whether VLM said YES (True) or NO (False)
        
        Returns:
            Confidence score 0-1
        """
        base_confidence = 0.7
        
        # Check for confidence indicators in response
        vlm_lower = vlm_response.lower()
        
        # High confidence indicators
        if any(word in vlm_lower for word in ['clearly', 'definitely', 'obvious', 'certainly']):
            base_confidence += 0.15
        
        # Medium confidence indicators
        elif any(word in vlm_lower for word in ['appears', 'seems', 'likely', 'probably']):
            base_confidence += 0.05
        
        # Low confidence indicators 
        elif any(word in vlm_lower for word in ['might', 'maybe', 'possibly', 'could be']):
            base_confidence -= 0.1
        
        # Check for relevant keywords
        keywords = self.VERIFICATION_PROMPTS.get(model_name, {}).get('keywords', [])
        keyword_matches = sum(1 for kw in keywords if kw in vlm_lower)
        
        if positive and keyword_matches >= 2:
            base_confidence += 0.1
        elif not positive and keyword_matches == 0:
            base_confidence += 0.1
        
        # Clamp confidence to valid range
        return max(0.5, min(base_confidence, 0.95))
    
    def verify_batch(self, verifications: list) -> list:
        """
        Verify multiple detections in batch
        
        Args:
            verifications: List of dicts with {image_path, model_name, detection_data}
        
        Returns:
            List of verification results
        """
        results = []
        for v in verifications:
            result = self.verify_detection(
                v['image_path'],
                v['model_name'],
                v.get('detection_data')
            )
            if result:
                result['detection_id'] = v.get('detection_id')
                results.append(result)
        
        return results
