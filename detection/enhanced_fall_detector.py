"""
CEMSS - Campus Event management and Surveillance System
Enhanced Fall Detector - Combines YOLO Fall Detection with Pose Estimation
"""
import cv2
import numpy as np
from pathlib import Path


class EnhancedFallDetector:
    """
    Enhanced fall detection combining:
    1. YOLO fall detection model (pattern-based)
    2. Pose estimation (skeletal analysis)
    
    Falls are confirmed when EITHER detector triggers, but confidence is boosted
    when BOTH agree.
    """
    
    def __init__(self, fall_detector=None, pose_estimator=None, mode='hybrid'):
        """
        Initialize enhanced fall detector.
        
        Args:
            fall_detector: YOLODetector instance for fall detection
            pose_estimator: PoseEstimator instance for skeletal analysis
            mode: Detection mode - 'hybrid', 'yolo_only', 'pose_only', 'dual_only'
        """
        self.fall_detector = fall_detector
        self.pose_estimator = pose_estimator
        self.mode = mode
        
        # Verify at least one detector is available
        if not fall_detector and not pose_estimator:
            raise ValueError("At least one detector (YOLO or Pose) must be available")
        
        # Auto-select mode if only one detector available
        if mode == 'hybrid':
            if not fall_detector:
                self.mode = 'pose_only'
            elif not pose_estimator:
                self.mode = 'yolo_only'
        
        # Confidence boost when both detectors agree
        self.dual_confirmation_boost = 0.20
        
        # OPTIMIZED Thresholds for better accuracy
        self.yolo_min_confidence = 0.50  # Increased from 0.40 for accuracy
        self.pose_min_confidence = 0.55  # Increased from 0.45 for accuracy
        self.combined_min_confidence = 0.45  # Dual confirmation threshold
        self.high_confidence_threshold = 0.70  # Single-source high confidence
        
        # Hybrid mode settings
        self.require_dual_confirmation = (mode == 'dual_only')
        
        print(f"✓ Enhanced Fall Detector initialized (MODE: {self.mode.upper()})")
        print(f"  - YOLO fall detector: {'Available' if fall_detector else 'Not loaded'}")
        print(f"  - Pose estimator: {'Available' if pose_estimator else 'Not loaded'}")
        print(f"  - Thresholds: YOLO≥{self.yolo_min_confidence}, Pose≥{self.pose_min_confidence}, Dual≥{self.combined_min_confidence}")
        print(f"  - High-confidence single-source: {self.high_confidence_threshold}")
    
    def detect(self, frame, annotate=True):
        """
        Run enhanced fall detection on frame.
        
        Args:
            frame: OpenCV BGR frame
            annotate: Whether to draw annotations
            
        Returns:
            dict with:
                - 'detections': List of fall detections
                - 'frame': Annotated frame
                - 'detection_count': Number of falls detected
                - 'method': Detection method used ('yolo', 'pose', 'combined', 'none')
        """
        yolo_falls = []
        pose_falls = []
        combined_detections = []
        annotated_frame = frame.copy() if annotate else frame
        
        # Run YOLO fall detection
        if self.fall_detector:
            try:
                yolo_result = self.fall_detector.detect(frame, annotate=False)
                yolo_falls = yolo_result.get('detections', [])
            except Exception as e:
                print(f"YOLO fall detection error: {e}")
        
        # Run pose estimation for fall detection
        if self.pose_estimator:
            try:
                pose_result = self.pose_estimator.detect_poses(frame, draw_skeleton=annotate, draw_keypoints=annotate)
                
                # Get annotated frame from pose estimator
                if annotate and 'frame' in pose_result:
                    annotated_frame = pose_result['frame']
                
                # Extract falls from pose analysis
                for pose in pose_result.get('poses', []):
                    if pose.get('is_falling', False):
                        pose_falls.append({
                            'bbox': pose['bbox'],
                            'confidence': pose['confidence'],
                            'class_name': 'fall_pose',
                            'keypoints': pose['keypoints'],
                            'distance': pose.get('distance', 'unknown'),
                            'person_id': pose.get('person_id', 0)
                        })
            except Exception as e:
                print(f"Pose fall detection error: {e}")
        
        # Combine detections using IoU matching
        combined_detections = self._combine_detections(yolo_falls, pose_falls, frame.shape)
        
        # Draw fall indicators on frame
        if annotate and combined_detections:
            annotated_frame = self._draw_fall_indicators(annotated_frame, combined_detections)
        
        # Determine detection method
        if combined_detections:
            has_yolo = any(d['source'] in ['yolo', 'combined'] for d in combined_detections)
            has_pose = any(d['source'] in ['pose', 'combined'] for d in combined_detections)
            
            if has_yolo and has_pose:
                method = 'combined'
            elif has_yolo:
                method = 'yolo'
            elif has_pose:
                method = 'pose'
            else:
                method = 'none'
        else:
            method = 'none'
        # Combine detections using IoU matching
        combined_detections = self._combine_detections(yolo_falls, pose_falls, frame.shape)
        
        # Draw fall indicators on frame
        if annotate and combined_detections:
            annotated_frame = self._draw_fall_indicators(annotated_frame, combined_detections)
        
        # Determine detection method (for logging)
        if combined_detections:
            has_yolo = any(d['source'] in ['yolo', 'combined'] for d in combined_detections)
            has_pose = any(d['source'] in ['pose', 'combined'] for d in combined_detections)
            
            if has_yolo and has_pose:
                method = 'combined'
            elif has_yolo:
                method = 'yolo'
            elif has_pose:
                method = 'pose'
            else:
                method = 'none'
        else:
            method = 'none'
        
        return {
            'detections': combined_detections,
            'frame': annotated_frame,
            'detection_count': len(combined_detections),
            'method': method,
            'mode': self.mode
        }
    
    def _combine_detections(self, yolo_falls, pose_falls, frame_shape):
        """
        Combine YOLO and pose-based fall detections using hybrid logic.
        
        HYBRID MODE (default):
        - Accept DUAL confirmation if confidence ≥ combined_min_confidence (0.45)
        - Accept YOLO-only if confidence ≥ high_confidence_threshold (0.70)
        - Accept POSE-only if confidence ≥ high_confidence_threshold (0.70)
        
        DUAL_ONLY MODE:
        - Only accept detections confirmed by BOTH detectors
        
        YOLO_ONLY / POSE_ONLY MODE:
        - Only use specified detector
        """
        combined = []
        used_pose_indices = set()
        
        # Process YOLO detections and look for matching pose detections
        for yolo_det in yolo_falls:
            yolo_bbox = yolo_det['bbox']
            yolo_conf = yolo_det['confidence']
            
            # Check for matching pose detection
            best_match_idx = None
            best_iou = 0
            
            for idx, pose_det in enumerate(pose_falls):
                if idx in used_pose_indices:
                    continue
                
                iou = self._calculate_iou(yolo_bbox, pose_det['bbox'])
                if iou > 0.25 and iou > best_iou:  # 25% IoU threshold for matching
                    best_iou = iou
                    best_match_idx = idx
            
            if best_match_idx is not None:
                # DUAL CONFIRMATION - Both YOLO and pose agree
                pose_det = pose_falls[best_match_idx]
                used_pose_indices.add(best_match_idx)
                
                # Boost confidence for dual confirmation
                boosted_conf = min(1.0, max(yolo_conf, pose_det['confidence']) + self.dual_confirmation_boost)
                
                # Always accept dual confirmation if above threshold
                if boosted_conf >= self.combined_min_confidence:
                    combined.append({
                        'bbox': yolo_bbox,
                        'confidence': boosted_conf,
                        'class_name': 'fall',
                        'source': 'combined',
                        'yolo_conf': yolo_conf,
                        'pose_conf': pose_det['confidence'],
                        'distance': pose_det.get('distance', 'unknown'),
                        'keypoints': pose_det.get('keypoints', [])
                    })
            elif self.mode in ['hybrid', 'yolo_only'] and not self.require_dual_confirmation:
                # YOLO-only detection (hybrid or yolo_only mode)
                # Accept if YOLO confidence is very high OR above minimum threshold
                if yolo_conf >= self.high_confidence_threshold or yolo_conf >= self.yolo_min_confidence:
                    combined.append({
                        'bbox': yolo_bbox,
                        'confidence': yolo_conf,
                        'class_name': 'fall',
                        'source': 'yolo',
                        'distance': self._estimate_distance_from_bbox(yolo_bbox, frame_shape)
                    })
        
        # Add remaining pose-only detections (hybrid or pose_only mode)
        if self.mode in ['hybrid', 'pose_only'] and not self.require_dual_confirmation:
            for idx, pose_det in enumerate(pose_falls):
                if idx in used_pose_indices:
                    continue
                
                # Accept if POSE confidence is very high OR above minimum threshold
                if pose_det['confidence'] >= self.high_confidence_threshold or pose_det['confidence'] >= self.pose_min_confidence:
                    combined.append({
                        'bbox': pose_det['bbox'],
                        'confidence': pose_det['confidence'],
                        'class_name': 'fall',
                        'source': 'pose',
                        'distance': pose_det.get('distance', 'unknown'),
                        'keypoints': pose_det.get('keypoints', [])
                    })
        
        return combined
    
    def _calculate_iou(self, bbox1, bbox2):
        """Calculate Intersection over Union for two bounding boxes."""
        x1_1, y1_1, x2_1, y2_1 = bbox1
        x1_2, y1_2, x2_2, y2_2 = bbox2
        
        # Calculate intersection
        x1_i = max(x1_1, x1_2)
        y1_i = max(y1_1, y1_2)
        x2_i = min(x2_1, x2_2)
        y2_i = min(y2_1, y2_2)
        
        if x2_i <= x1_i or y2_i <= y1_i:
            return 0.0
        
        intersection = (x2_i - x1_i) * (y2_i - y1_i)
        
        # Calculate union
        area1 = (x2_1 - x1_1) * (y2_1 - y1_1)
        area2 = (x2_2 - x1_2) * (y2_2 - y1_2)
        union = area1 + area2 - intersection
        
        return intersection / union if union > 0 else 0.0
    
    def _estimate_distance_from_bbox(self, bbox, frame_shape):
        """Estimate distance category from bounding box size."""
        x1, y1, x2, y2 = bbox
        bbox_area = (x2 - x1) * (y2 - y1)
        frame_area = frame_shape[0] * frame_shape[1]
        area_ratio = bbox_area / frame_area
        
        if area_ratio >= 0.08:
            return 'near'
        elif area_ratio >= 0.02:
            return 'medium'
        else:
            return 'far'
    
    def _draw_fall_indicators(self, frame, detections):
        """Draw fall detection indicators on frame."""
        for det in detections:
            bbox = det['bbox']
            x1, y1, x2, y2 = bbox
            confidence = det['confidence']
            source = det.get('source', 'unknown')
            distance = det.get('distance', 'unknown')
            
            # Color based on source
            if source == 'combined':
                color = (0, 0, 255)  # Red - high confidence
                thickness = 3
            elif source == 'yolo':
                color = (0, 165, 255)  # Orange
                thickness = 2
            elif source == 'pose':
                color = (255, 0, 255)  # Magenta
                thickness = 2
            else:
                color = (0, 255, 255)  # Yellow
                thickness = 2
            
            # Draw bounding box
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness)
            
            # Draw label background
            label = f"FALL! {confidence:.0%}"
            if source == 'combined':
                label = f"FALL! {confidence:.0%} [CONFIRMED]"
            
            label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
            cv2.rectangle(frame, (x1, y1 - label_size[1] - 10), 
                         (x1 + label_size[0] + 10, y1), color, -1)
            cv2.putText(frame, label, (x1 + 5, y1 - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            # Draw distance indicator
            dist_label = f"[{distance.upper()}]"
            cv2.putText(frame, dist_label, (x1, y2 + 20),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        
        # Add warning overlay if falls detected
        if detections:
            h, w = frame.shape[:2]
            # Red border
            cv2.rectangle(frame, (0, 0), (w-1, h-1), (0, 0, 255), 4)
            
            # Warning text
            warning_text = f"⚠ FALL DETECTED ({len(detections)})"
            text_size, _ = cv2.getTextSize(warning_text, cv2.FONT_HERSHEY_SIMPLEX, 1.0, 2)
            text_x = (w - text_size[0]) // 2
            cv2.rectangle(frame, (text_x - 10, 5), (text_x + text_size[0] + 10, 40), (0, 0, 255), -1)
            cv2.putText(frame, warning_text, (text_x, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
        
        return frame


def create_enhanced_fall_detector():
    """
    Factory function to create EnhancedFallDetector with all components.
    """
    from detection.detector import YOLODetector
    from detection.pose_estimator import PoseEstimator
    
    fall_detector = None
    pose_estimator = None
    
    # Try to load YOLO fall detector
    try:
        fall_detector = YOLODetector('fall')
        print("✓ YOLO fall detector loaded")
    except Exception as e:
        print(f"⚠ Could not load YOLO fall detector: {e}")
    
    # Try to load pose estimator
    try:
        pose_estimator = PoseEstimator()
        print("✓ Pose estimator loaded")
    except Exception as e:
        print(f"⚠ Could not load pose estimator: {e}")
    
    return EnhancedFallDetector(fall_detector, pose_estimator)
