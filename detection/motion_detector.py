"""
CEMSS - Campus Event management and Surveillance System
Motion Detection Module (Optimized for Dark/Low-Light Conditions)

Provides motion detection capabilities with special handling for:
- Low-light/dark environments
- Noise reduction in dark scenes
- Adaptive sensitivity based on lighting conditions
"""
import cv2
import numpy as np
from typing import Tuple, Optional, Dict, Any
from datetime import datetime, timedelta


class MotionDetector:
    """
    Advanced motion detector with dark/low-light optimization
    
    Features:
    - Background subtraction for motion detection
    - Adaptive thresholding based on scene brightness
    - Noise filtering for dark scenes
    - Configurable sensitivity
    - Motion history tracking
    """
    
    def __init__(
        self,
        min_area: int = 500,
        threshold_sensitivity: int = 25,
        blur_kernel: Tuple[int, int] = (21, 21),
        dilate_iterations: int = 2,
        dark_boost_factor: float = 1.5
    ):
        """
        Initialize motion detector
        
        Args:
            min_area: Minimum contour area to consider as motion (pixels)
            threshold_sensitivity: Threshold for motion detection (0-255, lower = more sensitive)
            blur_kernel: Gaussian blur kernel size for noise reduction
            dilate_iterations: Number of dilation iterations to fill gaps
            dark_boost_factor: Sensitivity multiplier for dark scenes
        """
        self.min_area = min_area
        self.threshold_sensitivity = threshold_sensitivity
        self.blur_kernel = blur_kernel
        self.dilate_iterations = dilate_iterations
        self.dark_boost_factor = dark_boost_factor
        
        # Background model
        self.background = None
        self.background_subtractor = cv2.createBackgroundSubtractorMOG2(
            history=500,
            varThreshold=16,
            detectShadows=True
        )
        
        # Motion tracking
        self.last_motion_time = None
        self.motion_history = []
        self.frame_count = 0
        
        # Statistics
        self.stats = {
            'total_detections': 0,
            'false_positives_filtered': 0,
            'dark_frames_processed': 0
        }
    
    def detect_motion(
        self,
        frame: np.ndarray,
        timestamp: datetime = None
    ) -> Tuple[bool, Optional[np.ndarray], Dict[str, Any]]:
        """
        Detect motion in frame with dark scene optimization
        
        Args:
            frame: Input frame (BGR or grayscale)
            timestamp: Frame timestamp
            
        Returns:
            Tuple of (motion_detected, annotated_frame, motion_info)
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        self.frame_count += 1
        
        # Convert to grayscale if needed
        if len(frame.shape) == 3:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        else:
            gray = frame.copy()
        
        # Detect if scene is dark
        mean_brightness = np.mean(gray)
        is_dark = mean_brightness < 50  # Threshold for dark scene
        
        if is_dark:
            self.stats['dark_frames_processed'] += 1
        
        # Apply histogram equalization for dark scenes
        if is_dark:
            gray = cv2.equalizeHist(gray)
        
        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, self.blur_kernel, 0)
        
        # Initialize background on first frame
        if self.background is None:
            self.background = blurred.copy().astype("float")
            return False, frame.copy(), self._create_motion_info(False, 0, mean_brightness, is_dark)
        
        # Update background model (running average)
        cv2.accumulateWeighted(blurred, self.background, 0.5)
        
        # Compute absolute difference between current frame and background
        frame_delta = cv2.absdiff(blurred, cv2.convertScaleAbs(self.background))
        
        # Adjust threshold based on scene brightness
        if is_dark:
            threshold_value = int(self.threshold_sensitivity / self.dark_boost_factor)
        else:
            threshold_value = self.threshold_sensitivity
        
        # Threshold the delta image
        thresh = cv2.threshold(frame_delta, threshold_value, 255, cv2.THRESH_BINARY)[1]
        
        # Dilate to fill gaps
        thresh = cv2.dilate(thresh, None, iterations=self.dilate_iterations)
        
        # Find contours
        contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Filter contours by area and analyze motion
        motion_detected = False
        total_motion_area = 0
        motion_regions = []
        
        for contour in contours:
            area = cv2.contourArea(contour)
            
            if area < self.min_area:
                continue
            
            motion_detected = True
            total_motion_area += area
            
            # Get bounding box
            (x, y, w, h) = cv2.boundingRect(contour)
            motion_regions.append({
                'bbox': (x, y, w, h),
                'area': area,
                'center': (x + w // 2, y + h // 2)
            })
        
        # Update motion tracking
        if motion_detected:
            self.last_motion_time = timestamp
            self.stats['total_detections'] += 1
            
            # Keep motion history (last 10 events)
            self.motion_history.append({
                'timestamp': timestamp,
                'area': total_motion_area,
                'regions': len(motion_regions),
                'is_dark': is_dark
            })
            if len(self.motion_history) > 10:
                self.motion_history.pop(0)
        
        # Create annotated frame
        annotated_frame = self._annotate_frame(
            frame.copy(),
            motion_regions,
            is_dark,
            mean_brightness
        )
        
        # Create motion info dict
        motion_info = self._create_motion_info(
            motion_detected,
            total_motion_area,
            mean_brightness,
            is_dark,
            motion_regions
        )
        
        return motion_detected, annotated_frame, motion_info
    
    def _annotate_frame(
        self,
        frame: np.ndarray,
        motion_regions: list,
        is_dark: bool,
        brightness: float
    ) -> np.ndarray:
        """Draw motion regions and stats on frame"""
        
        # Draw motion bounding boxes
        for region in motion_regions:
            x, y, w, h = region['bbox']
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            
            # Draw center point
            cx, cy = region['center']
            cv2.circle(frame, (cx, cy), 5, (0, 0, 255), -1)
        
        # Add status text
        status_text = f"Motion: {len(motion_regions)} regions"
        cv2.putText(frame, status_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
                   0.6, (0, 255, 0), 2)
        
        # Add brightness indicator
        brightness_text = f"Brightness: {brightness:.1f} {'(DARK MODE)' if is_dark else ''}"
        cv2.putText(frame, brightness_text, (10, 60), cv2.FONT_HERSHEY_SIMPLEX,
                   0.5, (255, 255, 0) if is_dark else (255, 255, 255), 1)
        
        return frame
    
    def _create_motion_info(
        self,
        detected: bool,
        total_area: float,
        brightness: float,
        is_dark: bool,
        regions: list = None
    ) -> Dict[str, Any]:
        """Create motion information dictionary"""
        
        return {
            'motion_detected': detected,
            'total_area': total_area,
            'num_regions': len(regions) if regions else 0,
            'brightness': brightness,
            'is_dark_scene': is_dark,
            'frame_number': self.frame_count,
            'last_motion_time': self.last_motion_time.isoformat() if self.last_motion_time else None,
            'recent_history': self.motion_history[-5:] if self.motion_history else [],
            'regions': regions if regions else []
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get detection statistics"""
        return {
            **self.stats,
            'frames_processed': self.frame_count,
            'dark_scene_percentage': (
                (self.stats['dark_frames_processed'] / self.frame_count * 100)
                if self.frame_count > 0 else 0
            ),
            'motion_history_count': len(self.motion_history)
        }
    
    def reset_background(self):
        """Reset background model (useful after camera movement)"""
        self.background = None
        self.background_subtractor = cv2.createBackgroundSubtractorMOG2(
            history=500,
            varThreshold=16,
            detectShadows=True
        )
    
    def adjust_sensitivity(self, increase: bool = True):
        """Dynamically adjust motion sensitivity"""
        if increase:
            self.threshold_sensitivity = max(10, self.threshold_sensitivity - 5)
            self.min_area = max(100, int(self.min_area * 0.8))
        else:
            self.threshold_sensitivity = min(50, self.threshold_sensitivity + 5)
            self.min_area = min(2000, int(self.min_area * 1.2))
    
    def is_continuous_motion(self, time_window: int = 5) -> bool:
        """
        Check if motion has been continuous in the last N seconds
        
        Args:
            time_window: Time window in seconds
            
        Returns:
            True if motion detected continuously in time window
        """
        if not self.motion_history:
            return False
        
        cutoff_time = datetime.now() - timedelta(seconds=time_window)
        recent_motion = [
            m for m in self.motion_history
            if m['timestamp'] >= cutoff_time
        ]
        
        return len(recent_motion) >= 3  # At least 3 detections in window


def create_motion_detector(
    sensitivity: str = 'medium',
    optimize_for_dark: bool = True
) -> MotionDetector:
    """
    Factory function to create motion detector with preset configurations
    
    Args:
        sensitivity: 'low', 'medium', or 'high'
        optimize_for_dark: Enable dark scene optimization
        
    Returns:
        Configured MotionDetector instance
    """
    configs = {
        'low': {
            'min_area': 1000,
            'threshold_sensitivity': 35,
            'dark_boost_factor': 1.3
        },
        'medium': {
            'min_area': 500,
            'threshold_sensitivity': 25,
            'dark_boost_factor': 1.5
        },
        'high': {
            'min_area': 300,
            'threshold_sensitivity': 15,
            'dark_boost_factor': 1.8
        }
    }
    
    config = configs.get(sensitivity, configs['medium'])
    
    if not optimize_for_dark:
        config['dark_boost_factor'] = 1.0
    
    return MotionDetector(**config)
