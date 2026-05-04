"""
CASS - VLM Frame Analyzer
Analyzes camera frames using Vision Language Models to answer visual questions
"""
import requests
import cv2
import base64
import json
import os
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple
from pathlib import Path
import logging
import threading

logger = logging.getLogger(__name__)


class VLMFrameAnalyzer:
    """
    Analyzer that uses VLM to answer questions about camera feed frames
    """
    
    def __init__(self, ollama_host: str, model: str = "llava:latest", timeout: int = 30):
        """
        Initialize VLM frame analyzer
        
        Args:
            ollama_host: Ollama server URL
            model: VLM model to use (llava, bakllava, etc.)
            timeout: Request timeout in seconds
        """
        self.ollama_host = ollama_host.rstrip('/')
        self.model = model
        self.timeout = timeout
        self.available = False
        
        # Frame cache settings
        self.cache_dir = Path('cache/frames')
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_ttl = 30  # seconds
        self.frame_cache = {}  # camera_id: (timestamp, frame_path)
        
        # Concurrency control
        self.lock = threading.Lock()
        
        self._check_availability()
    
    def _check_availability(self) -> bool:
        """Check if VLM is available"""
        try:
            response = requests.get(f"{self.ollama_host}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                model_names = [m.get('name', '') for m in models]
                
                # Check if our VLM model is available
                base_model = self.model.split(':')[0]
                if any(base_model in name for name in model_names):
                    self.available = True
                    logger.info(f"✓ VLM available: {self.model}")
                    return True
                else:
                    logger.warning(f"⚠ VLM model '{self.model}' not found")
                    logger.info(f"Available models: {', '.join(model_names)}")
            return False
        except Exception as e:
            logger.warning(f"⚠ VLM not available: {e}")
            return False
    
    def is_available(self) -> bool:
        """Check if VLM is available"""
        return self.available
    
    def capture_frame(self, camera_id: int, camera_manager) -> Optional[str]:
        """
        Capture current frame from camera
        
        Args:
            camera_id: Camera ID
            camera_manager: CameraManager instance
            
        Returns:
            Path to saved frame or None
        """
        try:
            # Check cache first
            if camera_id in self.frame_cache:
                cached_time, cached_path = self.frame_cache[camera_id]
                if time.time() - cached_time < self.cache_ttl:
                    if os.path.exists(cached_path):
                        logger.debug(f"Using cached frame for camera {camera_id}")
                        return cached_path
            
            # Get camera from CameraPool
            camera = camera_manager.get_camera(camera_id)
            if not camera:
                logger.warning(f"Camera {camera_id} not found in camera pool")
                return None
            
            # Get latest frame from camera
            frame = camera.get_last_frame()
            
            if frame is None or frame.size == 0:
                logger.warning(f"No frame available for camera {camera_id}")
                return None
            
            # Save frame
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            frame_path = self.cache_dir / f"cam{camera_id}_{timestamp}.jpg"
            
            cv2.imwrite(str(frame_path), frame)
            
            # Update cache
            self.frame_cache[camera_id] = (time.time(), str(frame_path))
            
            logger.info(f"Captured frame from camera {camera_id}")
            return str(frame_path)
            
        except Exception as e:
            logger.error(f"Error capturing frame from camera {camera_id}: {e}")
            return None
    
    def encode_image(self, image_path: str) -> Optional[str]:
        """
        Encode image to base64 for VLM
        
        Args:
            image_path: Path to image file
            
        Returns:
            Base64 encoded image or None
        """
        try:
            with open(image_path, 'rb') as f:
                image_data = f.read()
            return base64.b64encode(image_data).decode('utf-8')
        except Exception as e:
            logger.error(f"Error encoding image: {e}")
            return None
    
    def analyze_frame(
        self,
        frame_path: str | list[str],
        question: str,
        context: Optional[str] = None,
        history: list = None,
        system_prompt: str = None
    ) -> Dict[str, Any]:
        """
        Analyze a frame (or list of frames) using VLM
        
        Args:
            frame_path: Path to frame image or list of paths
            question: Question to ask about the frame
            context: Optional context about the camera/location
            history: Optional list of previous messages for conversational context
            system_prompt: Optional system prompt to override the default VLM instructions
            
        Returns:
            Dictionary with analysis results
        """
        if not self.available:
            return {
                'success': False,
                'response': 'VLM not available',
                'error': 'VLM service unavailable'
            }
        
        # Acquire lock to ensure only one VLM request at a time
        try:
            with self.lock:
                return self._perform_analysis(frame_path, question, context, history, system_prompt)
        except Exception as e:
             logger.error(f"Error getting VLM lock: {e}")
             return {'success': False, 'error': str(e)}

    def try_analyze_frame(self, frame_path, question, context=None, history=None, system_prompt=None):
        """Non-blocking analysis for background tasks"""
        if not self.lock.acquire(blocking=False):
            return {'success': False, 'error': 'VLM busy'}
        
        try:
            return self._perform_analysis(frame_path, question, context, history, system_prompt)
        finally:
            self.lock.release()

    def _perform_analysis(self, frame_path, question, context, history, system_prompt=None):
        """Internal analysis logic (assumes lock is held)"""
        try:
            # Handle single or multiple frames
            frames = frame_path if isinstance(frame_path, list) else [frame_path]
            images_b64 = []
            
            for path in frames:
                img_b64 = self.encode_image(path)
                if not img_b64:
                    return {
                        'success': False,
                        'response': 'Failed to encode image',
                        'error': f'Image encoding failed for {path}'
                    }
                images_b64.append(img_b64)
            
            # Build messages for Chat API
            messages = []
            
            # System instruction (Use custom if provided, else default)
            if not system_prompt:
                system_prompt = (
                    "You are CASS (Camera Alert Surveillance System), a security monitoring AI. "
                    "CRITICAL RULES - You MUST follow these: "
                    "1) ONLY describe what you can DIRECTLY SEE in the image(s). "
                    "2) NEVER speculate about intent, emotions, identity, or what 'might' happen. "
                    "3) Do NOT use phrases like 'appears to be', 'seems like', 'might be', 'possibly', 'probably'. "
                    "4) Count people visible. State their physical positions (standing, sitting, walking). "
                    "5) Describe movement direction and visible objects/clothing. "
                    "6) If you cannot clearly see something, say 'not clearly visible'. "
                    "7) Respond ONLY in English. "
                    "Be concise, factual, and security-focused."
                )
            messages.append({'role': 'system', 'content': system_prompt})

            # Add conversation history if available
            if history:
                for msg in history[-6:]:
                    role = msg.get('role', 'user')
                    content = msg.get('content', '')
                    if role in ['user', 'assistant']:
                        messages.append({'role': role, 'content': content})

            # User message with images
            user_content_parts = []
            if context:
                user_content_parts.append(f"Context: {context}")
            
            user_content_parts.append(f"Question: {question}")
            
            messages.append({
                'role': 'user', 
                'content': "\n".join(user_content_parts),
                'images': images_b64
            })
            
            # Log the prompt for debugging
            logger.info(f"[VLM] Analyzing with {len(images_b64)} image(s) via Chat API")
            
            # Call VLM API (Chat)
            response = requests.post(
                f"{self.ollama_host}/api/chat",
                json={
                    'model': self.model,
                    'messages': messages,
                    'stream': False,
                    'options': {
                        'temperature': 0.2,
                        'num_predict': 150,
                        'top_p': 0.9
                    }
                },
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                answer = result.get('message', {}).get('content', '').strip()
                
                # Log the RAW response for debugging
                logger.info(f"[VLM] API response - Keys: {list(result.keys())}")
                logger.info(f"[VLM] Response length: {len(answer)} chars")
                logger.info(f"[VLM] Response preview: '{answer[:200] if answer else '<EMPTY>'}...'")
                
                # Check if response is empty or too short
                if not answer or len(answer) < 5:
                    logger.warning(f"[VLM] EMPTY RESPONSE DETECTED! Raw result: {result}")
                    return {
                        'success': False,
                        'response': 'VLM unable to analyze image - received empty response',
                        'error': 'Empty VLM response'
                    }
                
                return {
                    'success': True,
                    'response': answer,
                    'model': self.model,
                    'timestamp': datetime.now().isoformat()
                }
            else:
                logger.error(f"VLM API error: {response.status_code}")
                return {
                    'success': False,
                    'response': 'VLM analysis failed',
                    'error': f'API returned {response.status_code}'
                }
                
        except Exception as e:
            logger.error(f"VLM analysis error: {e}")
            return {
                'success': False,
                'response': 'Analysis error occurred',
                'error': str(e)
            }
    
    def analyze_camera(
        self, 
        camera_id: int, 
        question: str, 
        camera_manager,
        camera_name: str = None,
        history: list = None,
        prompt_context: str = None,
        system_prompt: str = None
    ) -> Dict[str, Any]:
        """
        Analyze the current frame from a specific camera
        """
        # Capture frame
        frame_path = self.capture_frame(camera_id, camera_manager)
        if not frame_path:
            return {
                'success': False,
                'response': f'Unable to capture frame from camera {camera_id}',
                'error': 'Frame capture failed'
            }
        
        # Build context
        context_parts = []
        if camera_name:
            context_parts.append(f"Camera: {camera_name}")
        context_parts.append(f"Camera ID: {camera_id}")
        context = " | ".join(context_parts) if context_parts else None
        
        # Analyze
        return self.analyze_frame(frame_path, question, context, history)
    
    def cleanup_old_frames(self, max_age_seconds: int = 300):
        """
        Clean up old cached frames
        
        Args:
            max_age_seconds: Maximum age of frames to keep
        """
        try:
            cutoff_time = time.time() - max_age_seconds
            
            for frame_file in self.cache_dir.glob('*.jpg'):
                if frame_file.stat().st_mtime < cutoff_time:
                    frame_file.unlink()
                    logger.debug(f"Deleted old frame: {frame_file}")
            
            # Clean cache dict
            self.frame_cache = {
                cam_id: (ts, path)
                for cam_id, (ts, path) in self.frame_cache.items()
                if ts > cutoff_time and os.path.exists(path)
            }
            
        except Exception as e:
            logger.error(f"Error cleaning up frames: {e}")

    def analyze_video(
        self,
        video_path: str,
        question: str,
        context: Optional[str] = None,
        history: list = None
    ) -> Dict[str, Any]:
        """
        Analyze a video clip by extracting keyframes
        
        Args:
            video_path: Path to the video file
            question: Question about the video
            context: Optional context
            history: Conversation history
            
        Returns:
            Analysis results
        """
        if not os.path.exists(video_path):
            return {
                'success': False,
                'response': 'Video file not found',
                'error': 'Video path invalid'
            }
            
        # Extract keyframes from video
        from config import OLLAMA_KEYFRAMES_PER_CLIP
        frames = self._extract_keyframes(video_path, num_frames=OLLAMA_KEYFRAMES_PER_CLIP)
        
        if not frames:
            return {
                'success': False,
                'response': 'Failed to extract frames from video',
                'error': 'Video processing failed'
            }
            
        # Analyze using the extracted frames
        # We modify the prompt slightly to indicate this is a video sequence
        video_context = (context or "") + " [Analysis of a 5-second video sequence]"
        
        return self.analyze_frame(frames, question, video_context, history)
        
    def _extract_keyframes(self, video_path: str, num_frames: int = None) -> list[str]:
        """
        Extract evenly spaced keyframes from a video
        """
        if num_frames is None:
             from config import OLLAMA_KEYFRAMES_PER_CLIP
             num_frames = OLLAMA_KEYFRAMES_PER_CLIP
             
        frames_paths = []
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                return []
                
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            if total_frames <= 0:
                # Fallback for streams where frame count unknown
                ret, frame = cap.read()
                if ret:
                    # Just save first frame
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_f0')
                    path = self.cache_dir / f"vid_frame_{timestamp}.jpg"
                    cv2.imwrite(str(path), frame)
                    frames_paths.append(str(path))
                cap.release()
                return frames_paths
                
            # Calculate indices
            indices = [int(i * total_frames / num_frames) for i in range(num_frames)]
            indices = sorted(list(set(indices))) # Unique and sorted
            
            for i in indices:
                cap.set(cv2.CAP_PROP_POS_FRAMES, i)
                ret, frame = cap.read()
                if ret:
                    timestamp = datetime.now().strftime(f'%Y%m%d_%H%M%S_f{i}')
                    path = self.cache_dir / f"vid_frame_{timestamp}.jpg"
                    cv2.imwrite(str(path), frame)
                    frames_paths.append(str(path))
                    
            cap.release()
            return frames_paths
            
        except Exception as e:
            logger.error(f"Error extracting keyframes: {e}")
            return frames_paths


# Global singleton instance
_vlm_instance = None

def create_vlm_analyzer(flask_app=None):
    """Factory function to create or get the shared VLM analyzer"""
    global _vlm_instance
    try:
        from config import VLM_ENABLED, VLM_TIER2_MODEL, OLLAMA_HOST, OLLAMA_TIMEOUT
        
        if VLM_ENABLED:
            if _vlm_instance is None:
                _vlm_instance = VLMFrameAnalyzer(
                    ollama_host=OLLAMA_HOST,
                    model=VLM_TIER2_MODEL,
                    timeout=OLLAMA_TIMEOUT
                )
            return _vlm_instance
    except Exception as e:
        logger.error(f"Failed to create VLM analyzer: {e}")
    
    return None
