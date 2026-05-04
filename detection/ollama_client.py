"""
CEMSS - Campus Event management and Surveillance System
Ollama LLM Client - Vision Model Integration
"""
import requests
import base64
import json
from io import BytesIO
import cv2
import numpy as np
from typing import Optional, Dict, Any, List


class OllamaClient:
    """Client for interacting with Ollama vision models"""
    
    def __init__(self, host: str = "http://localhost:11434", model: str = "llava:latest", timeout: int = 30):
        """
        Initialize Ollama client
        
        Args:
            host: Ollama server URL
            model: Vision model to use (e.g., llava:latest, llava-phi3:latest)
            timeout: Request timeout in seconds
        """
        self.host = host.rstrip('/')
        self.model = model
        self.timeout = timeout
        self.available = False
        
        # Check if Ollama is available
        self._check_availability()
    
    def _check_availability(self) -> bool:
        """Check if Ollama server is running and model is available"""
        try:
            # Check server
            response = requests.get(f"{self.host}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                model_names = [m['name'] for m in models]
                
                # Check if our model is available
                if self.model in model_names or self.model.split(':')[0] in [m.split(':')[0] for m in model_names]:
                    self.available = True
                    print(f"✓ Ollama available with model: {self.model}")
                    return True
                else:
                    print(f"⚠ Ollama running but model '{self.model}' not found")
                    print(f"  Available models: {', '.join(model_names)}")
                    return False
            return False
        except Exception as e:
            print(f"⚠ Ollama not available: {e}")
            return False
    
    def is_available(self) -> bool:
        """Check if Ollama is available for use"""
        return self.available
    
    def _encode_frame(self, frame: np.ndarray) -> str:
        """
        Encode OpenCV frame to base64 string
        
        Args:
            frame: OpenCV BGR frame
            
        Returns:
            Base64 encoded JPEG image
        """
        # Convert BGR to RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Encode to JPEG
        success, buffer = cv2.imencode('.jpg', frame_rgb, [cv2.IMWRITE_JPEG_QUALITY, 85])
        if not success:
            raise ValueError("Failed to encode frame")
        
        # Convert to base64
        jpg_as_text = base64.b64encode(buffer).decode('utf-8')
        return jpg_as_text
    
    def analyze_frame(
        self, 
        frame: np.ndarray, 
        prompt: str,
        temperature: float = 0.2
    ) -> Dict[str, Any]:
        """
        Analyze a single frame with the vision model
        
        Args:
            frame: OpenCV BGR frame
            prompt: Question/instruction for the model
            temperature: Model temperature (0-1, lower = more focused)
            
        Returns:
            Dictionary with response and metadata
        """
        if not self.available:
            return {
                'success': False,
                'response': '',
                'error': 'Ollama not available'
            }
        
        try:
            # Encode frame
            image_b64 = self._encode_frame(frame)
            
            # Prepare request
            payload = {
                'model': self.model,
                'prompt': prompt,
                'images': [image_b64],
                'stream': False,
                'options': {
                    'temperature': temperature
                }
            }
            
            # Send request
            response = requests.post(
                f"{self.host}/api/generate",
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'response': result.get('response', '').strip(),
                    'model': result.get('model', self.model),
                    'eval_count': result.get('eval_count', 0),
                    'eval_duration': result.get('eval_duration', 0)
                }
            else:
                return {
                    'success': False,
                    'response': '',
                    'error': f"HTTP {response.status_code}: {response.text}"
                }
        
        except Exception as e:
            return {
                'success': False,
                'response': '',
                'error': str(e)
            }
    
    def analyze_frames_batch(
        self,
        frames: List[np.ndarray],
        prompt: str,
        temperature: float = 0.2
    ) -> Dict[str, Any]:
        """
        Analyze multiple frames with a single prompt
        
        Args:
            frames: List of OpenCV BGR frames
            prompt: Question/instruction for the model
            temperature: Model temperature
            
        Returns:
            Dictionary with response and metadata
        """
        if not self.available:
            return {
                'success': False,
                'response': '',
                'error': 'Ollama not available'
            }
        
        try:
            # Encode all frames
            images_b64 = [self._encode_frame(frame) for frame in frames]
            
            # Prepare request with multiple images
            payload = {
                'model': self.model,
                'prompt': prompt,
                'images': images_b64,
                'stream': False,
                'options': {
                    'temperature': temperature
                }
            }
            
            # Send request
            response = requests.post(
                f"{self.host}/api/generate",
                json=payload,
                timeout=self.timeout * len(frames)  # Longer timeout for multiple frames
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'response': result.get('response', '').strip(),
                    'model': result.get('model', self.model),
                    'eval_count': result.get('eval_count', 0),
                    'eval_duration': result.get('eval_duration', 0),
                    'num_frames': len(frames)
                }
            else:
                return {
                    'success': False,
                    'response': '',
                    'error': f"HTTP {response.status_code}: {response.text}"
                }
        
        except Exception as e:
            return {
                'success': False,
                'response': '',
                'error': str(e)
            }
    
    def validate_fall_detection(self, frame: np.ndarray) -> Dict[str, Any]:
        """
        Specialized method for fall detection validation
        
        Args:
            frame: OpenCV BGR frame
            
        Returns:
            Dictionary with validation result
        """
        prompt = """Analyze this image carefully. Focus on whether there is a person who has fallen down or is in distress.

Answer in this exact format:
FALL_DETECTED: [YES/NO]
CONFIDENCE: [LOW/MEDIUM/HIGH]
DESCRIPTION: [Brief description of what you see]

Be specific about the person's position and whether they appear to need help."""
        
        result = self.analyze_frame(frame, prompt, temperature=0.1)
        
        if result['success']:
            response = result['response']
            
            # Parse response
            fall_detected = 'YES' in response.upper().split('FALL_DETECTED:')[1].split('\n')[0] if 'FALL_DETECTED:' in response else False
            
            # Extract confidence
            confidence = 'MEDIUM'
            if 'CONFIDENCE:' in response:
                conf_line = response.split('CONFIDENCE:')[1].split('\n')[0].strip().upper()
                if 'HIGH' in conf_line:
                    confidence = 'HIGH'
                elif 'LOW' in conf_line:
                    confidence = 'LOW'
            
            # Extract description
            description = ''
            if 'DESCRIPTION:' in response:
                description = response.split('DESCRIPTION:')[1].strip()
            
            return {
                'success': True,
                'fall_detected': fall_detected,
                'confidence': confidence,
                'description': description,
                'raw_response': response
            }
        else:
            return result


def test_ollama_client():
    """Test the Ollama client"""
    print("Testing Ollama Client...")
    print("=" * 80)
    
    # Initialize client
    client = OllamaClient()
    
    if not client.is_available():
        print("❌ Ollama is not available. Please:")
        print("   1. Install Ollama from https://ollama.ai")
        print("   2. Run: ollama pull llava:latest")
        print("   3. Ensure Ollama is running")
        return
    
    # Create a test frame
    print("\nCreating test frame...")
    test_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    cv2.putText(test_frame, "Test Frame", (200, 240), 
                cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 3)
    
    # Test single frame analysis
    print("\nTesting single frame analysis...")
    result = client.analyze_frame(test_frame, "What do you see in this image?")
    
    if result['success']:
        print(f"✓ Analysis successful")
        print(f"  Response: {result['response']}")
        print(f"  Model: {result['model']}")
    else:
        print(f"✗ Analysis failed: {result['error']}")
    
    print("\n" + "=" * 80)


if __name__ == '__main__':
    test_ollama_client()
