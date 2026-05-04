"""
CEMSS - Campus Event management and Surveillance System
Pose Estimator Module - Skeletal Tracking with Adaptive Confidence
"""
import cv2
import numpy as np
from ultralytics import YOLO
import torch
from config import YOLO_DEVICE, YOLO_IMG_SIZE, YOLO_IOU_THRESHOLD

# COCO keypoint connections for skeleton drawing
SKELETON_CONNECTIONS = [
    (0, 1), (0, 2), (1, 3), (2, 4),  # Head
    (5, 6), (5, 7), (7, 9), (6, 8), (8, 10),  # Arms
    (5, 11), (6, 12), (11, 12),  # Torso
    (11, 13), (13, 15), (12, 14), (14, 16)  # Legs
]

# Keypoint names (COCO format)
KEYPOINT_NAMES = [
    'nose', 'left_eye', 'right_eye', 'left_ear', 'right_ear',
    'left_shoulder', 'right_shoulder', 'left_elbow', 'right_elbow',
    'left_wrist', 'right_wrist', 'left_hip', 'right_hip',
    'left_knee', 'right_knee', 'left_ankle', 'right_ankle'
]

# Colors for different people (max 10 distinct colors)
PERSON_COLORS = [
    (0, 255, 0),    # Green
    (255, 0, 0),    # Blue
    (0, 0, 255),    # Red
    (255, 255, 0),  # Cyan
    (255, 0, 255),  # Magenta
    (0, 255, 255),  # Yellow
    (128, 0, 255),  # Purple
    (255, 128, 0),  # Orange
    (0, 128, 255),  # Light Blue
    (255, 0, 128),  # Pink
]


class AdaptiveConfidenceCalculator:
    """
    Calculates adaptive confidence thresholds based on bounding box size.
    Larger boxes (near) require higher confidence, smaller boxes (far) allow lower confidence.
    """
    
    def __init__(self, 
                 near_threshold=0.6,    # Confidence for near objects (large bbox)
                 far_threshold=0.25,    # Confidence for far objects (small bbox)
                 near_bbox_ratio=0.15,  # Bbox area ratio considered "near" (15% of frame)
                 far_bbox_ratio=0.01):  # Bbox area ratio considered "far" (1% of frame)
        """
        Args:
            near_threshold: Required confidence for near (large) objects
            far_threshold: Required confidence for far (small) objects
            near_bbox_ratio: Bbox area / frame area ratio for "near" objects
            far_bbox_ratio: Bbox area / frame area ratio for "far" objects
        """
        self.near_threshold = near_threshold
        self.far_threshold = far_threshold
        self.near_bbox_ratio = near_bbox_ratio
        self.far_bbox_ratio = far_bbox_ratio
    
    def get_threshold(self, bbox, frame_shape):
        """
        Calculate adaptive confidence threshold based on bbox size.
        
        Args:
            bbox: [x1, y1, x2, y2] bounding box coordinates
            frame_shape: (height, width, channels) of frame
            
        Returns:
            float: Confidence threshold for this detection
        """
        x1, y1, x2, y2 = bbox
        bbox_area = (x2 - x1) * (y2 - y1)
        frame_area = frame_shape[0] * frame_shape[1]
        
        area_ratio = bbox_area / frame_area
        
        # Linear interpolation between far and near thresholds
        if area_ratio >= self.near_bbox_ratio:
            return self.near_threshold
        elif area_ratio <= self.far_bbox_ratio:
            return self.far_threshold
        else:
            # Interpolate
            ratio_range = self.near_bbox_ratio - self.far_bbox_ratio
            threshold_range = self.near_threshold - self.far_threshold
            normalized_pos = (area_ratio - self.far_bbox_ratio) / ratio_range
            return self.far_threshold + (normalized_pos * threshold_range)
    
    def passes_threshold(self, confidence, bbox, frame_shape):
        """Check if detection passes adaptive threshold."""
        threshold = self.get_threshold(bbox, frame_shape)
        return confidence >= threshold


class PoseEstimator:
    """
    YOLO-based pose estimation with skeletal tracking for multiple people.
    Uses adaptive confidence based on distance (bounding box size).
    Includes state tracking to detect standing→fallen transitions.
    """
    
    # Posture states
    STATE_STANDING = 'standing'
    STATE_FALLEN = 'fallen'
    STATE_UNKNOWN = 'unknown'
    
    def __init__(self, model_path=None):
        """
        Initialize pose estimator.
        
        Args:
            model_path: Path to YOLO pose model, or None to download default
        """
        self.model = None
        self.device = YOLO_DEVICE
        self.adaptive_confidence = AdaptiveConfidenceCalculator(
            near_threshold=0.6,   # 60% confidence for close people
            far_threshold=0.25,   # 25% confidence for distant people
            near_bbox_ratio=0.10, # 10% of frame = close
            far_bbox_ratio=0.005  # 0.5% of frame = far
        )
        
        # State tracking for fall detection
        # Format: {camera_id: {person_track_id: {'state': state, 'last_seen': timestamp, 'fall_alerted': bool}}}
        self.person_states = {}
        
        # Time window for tracking same person (seconds)
        self.tracking_timeout = 3.0
        
        # Consecutive frames needed to confirm state change
        self.state_confirmation_frames = 3
        self.state_frame_counters = {}  # {camera_id: {person_id: {'standing': n, 'fallen': n}}}
        
        self._load_model(model_path)
    
    def _load_model(self, model_path):
        """Load the YOLO pose model."""
        try:
            if model_path and Path(model_path).exists():
                self.model = YOLO(model_path)
                print(f"✓ Pose estimator loaded from {model_path}")
            else:
                # Download default YOLOv8n pose model
                print("Downloading YOLOv8n pose model...")
                self.model = YOLO('yolov8n-pose.pt')
                print("✓ Pose estimator loaded (yolov8n-pose)")
            
            # Set device
            if torch.cuda.is_available() and self.device == '0':
                print("  Using GPU for pose estimation")
            else:
                self.device = 'cpu'
                print("  Using CPU for pose estimation")
                
        except Exception as e:
            print(f"⚠️ Failed to load pose model: {e}")
            self.model = None
    
    def detect_poses(self, frame, draw_skeleton=True, draw_keypoints=True):
        """
        Detect poses for all people in frame with adaptive confidence.
        
        Args:
            frame: OpenCV BGR frame
            draw_skeleton: Whether to draw skeleton lines
            draw_keypoints: Whether to draw keypoint circles
            
        Returns:
            dict with:
                - 'poses': List of pose data for each person
                - 'frame': Annotated frame
                - 'person_count': Number of people detected
        """
        if self.model is None:
            return {'poses': [], 'frame': frame, 'person_count': 0}
        
        try:
            # Run inference with low initial threshold (filtering done adaptively)
            results = self.model(
                frame,
                device=self.device,
                conf=0.2,  # Low threshold, will filter adaptively
                iou=YOLO_IOU_THRESHOLD,
                imgsz=YOLO_IMG_SIZE,
                verbose=False
            )
            
            poses = []
            annotated_frame = frame.copy()
            frame_shape = frame.shape
            
            for result in results:
                if result.keypoints is None or result.boxes is None:
                    continue
                
                keypoints_data = result.keypoints
                boxes = result.boxes
                
                for idx, (kps, box) in enumerate(zip(keypoints_data, boxes)):
                    # Get bounding box
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    bbox = [int(x1), int(y1), int(x2), int(y2)]
                    confidence = float(box.conf[0])
                    
                    # Apply adaptive confidence threshold
                    if not self.adaptive_confidence.passes_threshold(confidence, bbox, frame_shape):
                        continue
                    
                    # Get color for this person
                    color = PERSON_COLORS[idx % len(PERSON_COLORS)]
                    
                    # Extract keypoints
                    kps_xy = kps.xy[0].cpu().numpy()  # Shape: (17, 2)
                    kps_conf = kps.conf[0].cpu().numpy() if kps.conf is not None else np.ones(17)
                    
                    # Build pose data
                    keypoints = []
                    for kp_idx, (xy, conf) in enumerate(zip(kps_xy, kps_conf)):
                        keypoints.append({
                            'name': KEYPOINT_NAMES[kp_idx],
                            'x': float(xy[0]),
                            'y': float(xy[1]),
                            'confidence': float(conf)
                        })
                    
                    # Check for fall posture (basic heuristic)
                    is_falling = self._check_fall_posture(keypoints)
                    
                    pose_data = {
                        'person_id': idx,
                        'bbox': bbox,
                        'confidence': confidence,
                        'keypoints': keypoints,
                        'is_falling': is_falling,
                        'distance': self._estimate_distance(bbox, frame_shape)
                    }
                    poses.append(pose_data)
                    
                    # Draw skeleton
                    if draw_skeleton:
                        self._draw_skeleton(annotated_frame, kps_xy, kps_conf, color)
                    
                    # Draw keypoints
                    if draw_keypoints:
                        self._draw_keypoints(annotated_frame, kps_xy, kps_conf, color)
                    
                    # Draw person label
                    label = f"P{idx+1}"
                    if is_falling:
                        label += " FALL!"
                        color = (0, 0, 255)  # Red for fall
                    
                    cv2.putText(annotated_frame, label, 
                               (bbox[0], bbox[1] - 10),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
            
            return {
                'poses': poses,
                'frame': annotated_frame,
                'person_count': len(poses)
            }
            
        except Exception as e:
            print(f"Error during pose estimation: {e}")
            return {'poses': [], 'frame': frame, 'person_count': 0}
    
    def _draw_skeleton(self, frame, keypoints_xy, keypoints_conf, color, min_conf=0.3):
        """Draw skeleton connections on frame."""
        for connection in SKELETON_CONNECTIONS:
            idx1, idx2 = connection
            
            # Check confidence
            if keypoints_conf[idx1] < min_conf or keypoints_conf[idx2] < min_conf:
                continue
            
            pt1 = tuple(keypoints_xy[idx1].astype(int))
            pt2 = tuple(keypoints_xy[idx2].astype(int))
            
            # Skip if points are at origin (not detected)
            if pt1[0] == 0 and pt1[1] == 0:
                continue
            if pt2[0] == 0 and pt2[1] == 0:
                continue
            
            cv2.line(frame, pt1, pt2, color, 2)
    
    def _draw_keypoints(self, frame, keypoints_xy, keypoints_conf, color, min_conf=0.3):
        """Draw keypoint circles on frame."""
        for idx, (xy, conf) in enumerate(zip(keypoints_xy, keypoints_conf)):
            if conf < min_conf:
                continue
            if xy[0] == 0 and xy[1] == 0:
                continue
            
            pt = tuple(xy.astype(int))
            cv2.circle(frame, pt, 4, color, -1)
            cv2.circle(frame, pt, 5, (255, 255, 255), 1)
    
    def _check_fall_posture(self, keypoints, min_conf=0.3):
        """
        Improved fall detection heuristic based on keypoint positions.
        
        A fall is detected when MULTIPLE conditions are met:
        1. Body width > body height (person is horizontal, not vertical)
        2. Head is significantly below normal standing position
        3. Torso is nearly horizontal
        
        This reduces false positives when person is standing or bending.
        """
        # Get relevant keypoints
        head_kps = ['nose', 'left_eye', 'right_eye']
        hip_kps = ['left_hip', 'right_hip']
        shoulder_kps = ['left_shoulder', 'right_shoulder']
        ankle_kps = ['left_ankle', 'right_ankle']
        
        def get_avg_point(kp_names):
            """Get average X and Y for a group of keypoints."""
            xs, ys = [], []
            for kp in keypoints:
                if kp['name'] in kp_names and kp['confidence'] > min_conf:
                    if kp['x'] > 0 and kp['y'] > 0:
                        xs.append(kp['x'])
                        ys.append(kp['y'])
            if xs and ys:
                return (np.mean(xs), np.mean(ys))
            return None
        
        head_point = get_avg_point(head_kps)
        hip_point = get_avg_point(hip_kps)
        shoulder_point = get_avg_point(shoulder_kps)
        ankle_point = get_avg_point(ankle_kps)
        
        # Need at least head and hip detection
        if head_point is None or hip_point is None:
            return False
        
        head_x, head_y = head_point
        hip_x, hip_y = hip_point
        
        # ===== CONDITION 1: Body aspect ratio =====
        # Calculate body bounding box from keypoints
        all_x = [head_x, hip_x]
        all_y = [head_y, hip_y]
        
        if shoulder_point:
            all_x.append(shoulder_point[0])
            all_y.append(shoulder_point[1])
        if ankle_point:
            all_x.append(ankle_point[0])
            all_y.append(ankle_point[1])
        
        body_width = max(all_x) - min(all_x)
        body_height = max(all_y) - min(all_y)
        
        # Body is horizontal if width > height (aspect ratio check)
        # Standing person has height >> width
        is_horizontal = body_width > body_height * 0.8 if body_height > 0 else False
        
        # ===== CONDITION 2: Head position relative to hips =====
        # In image coords: higher Y = lower in frame
        # When standing: head is ABOVE hips (head_y < hip_y by significant margin)
        # When fallen: head is at or near hip level
        
        # Calculate normal standing head-hip distance (should be significant)
        head_hip_diff = hip_y - head_y  # Positive when standing (head above hip)
        
        # Head is too low if the difference is small or negative
        # Threshold: head should be at least 30% of body height above hips when standing
        min_head_hip_ratio = 0.3
        head_too_low = head_hip_diff < (body_height * min_head_hip_ratio) if body_height > 0 else False
        
        # ===== CONDITION 3: Torso orientation =====
        # Check if shoulders and hips are at similar Y level (horizontal torso)
        torso_horizontal = False
        if shoulder_point:
            shoulder_y = shoulder_point[1]
            # Shoulders and hips at similar height = lying down
            torso_diff = abs(shoulder_y - hip_y)
            torso_horizontal = torso_diff < body_height * 0.25 if body_height > 0 else False
        
        # ===== CONDITION 4: Ankle-head relationship =====
        # When lying down, ankles and head are at similar Y levels
        ankles_near_head = False
        if ankle_point:
            ankle_y = ankle_point[1]
            ankle_head_diff = abs(ankle_y - head_y)
            # If ankles and head are close in Y, person is horizontal
            ankles_near_head = ankle_head_diff < body_height * 0.4 if body_height > 50 else False
        
        # ===== FINAL DECISION =====
        # Require at least 2 strong indicators for a fall detection
        fall_indicators = 0
        
        if is_horizontal:
            fall_indicators += 2  # Strong indicator
        if head_too_low:
            fall_indicators += 1
        if torso_horizontal:
            fall_indicators += 1
        if ankles_near_head:
            fall_indicators += 2  # Strong indicator
        
        # Need at least 2 points for fall detection
        return fall_indicators >= 2
    
    def _estimate_distance(self, bbox, frame_shape):
        """
        Estimate relative distance category based on bbox size.
        
        Returns:
            str: 'near', 'medium', or 'far'
        """
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
    
    def detect_with_state_tracking(self, frame, camera_id, draw_skeleton=True, draw_keypoints=True):
        """
        Detect poses and track state changes for fall detection.
        
        Args:
            frame: OpenCV BGR frame
            camera_id: Camera ID for state tracking
            draw_skeleton: Whether to draw skeleton lines
            draw_keypoints: Whether to draw keypoint circles
            
        Returns:
            dict with:
                - 'poses': List of pose data for each person
                - 'frame': Annotated frame
                - 'person_count': Number of people detected
                - 'fall_transitions': List of persons who just transitioned to fallen state
        """
        import time
        current_time = time.time()
        
        # Initialize camera state tracking if needed
        if camera_id not in self.person_states:
            self.person_states[camera_id] = {}
        if camera_id not in self.state_frame_counters:
            self.state_frame_counters[camera_id] = {}
        
        # Get pose detections
        result = self.detect_poses(frame, draw_skeleton, draw_keypoints)
        poses = result.get('poses', [])
        annotated_frame = result.get('frame', frame)
        
        fall_transitions = []
        
        # Process each detected person
        for pose in poses:
            person_id = pose.get('person_id', 0)
            bbox = pose.get('bbox', [0, 0, 0, 0])
            is_falling = pose.get('is_falling', False)
            
            # Determine current posture state
            current_state = self.STATE_FALLEN if is_falling else self.STATE_STANDING
            
            # Initialize frame counters for this person
            if person_id not in self.state_frame_counters[camera_id]:
                self.state_frame_counters[camera_id][person_id] = {
                    'standing': 0,
                    'fallen': 0
                }
            
            # Update frame counters
            if current_state == self.STATE_STANDING:
                self.state_frame_counters[camera_id][person_id]['standing'] += 1
                self.state_frame_counters[camera_id][person_id]['fallen'] = 0
            else:
                self.state_frame_counters[camera_id][person_id]['fallen'] += 1
                self.state_frame_counters[camera_id][person_id]['standing'] = 0
            
            # Determine confirmed state (needs multiple frames)
            counters = self.state_frame_counters[camera_id][person_id]
            confirmed_state = self.STATE_UNKNOWN
            if counters['standing'] >= self.state_confirmation_frames:
                confirmed_state = self.STATE_STANDING
            elif counters['fallen'] >= self.state_confirmation_frames:
                confirmed_state = self.STATE_FALLEN
            
            # Get previous state
            person_key = self._get_person_key(camera_id, bbox)
            prev_data = self.person_states[camera_id].get(person_key, {
                'state': self.STATE_UNKNOWN,
                'last_seen': current_time,
                'fall_alerted': False
            })
            
            prev_state = prev_data['state']
            
            # Check for state transition: Standing → Fallen
            if (prev_state == self.STATE_STANDING and 
                confirmed_state == self.STATE_FALLEN and 
                not prev_data.get('fall_alerted', False)):
                
                # FALL TRANSITION DETECTED!
                fall_transitions.append({
                    'person_id': person_id,
                    'bbox': bbox,
                    'confidence': pose.get('confidence', 0),
                    'transition': 'standing_to_fallen',
                    'distance': pose.get('distance', 'unknown')
                })
                
                # Mark as alerted so we don't alert again
                prev_data['fall_alerted'] = True
                
                # Draw alert on frame
                x1, y1, x2, y2 = bbox
                cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 0, 255), 3)
                cv2.putText(annotated_frame, "FALL DETECTED!", (x1, y1 - 40),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
            
            # Update state if confirmed
            if confirmed_state != self.STATE_UNKNOWN:
                # If person returned to standing, reset fall alert
                if confirmed_state == self.STATE_STANDING:
                    prev_data['fall_alerted'] = False
                
                prev_data['state'] = confirmed_state
            
            prev_data['last_seen'] = current_time
            self.person_states[camera_id][person_key] = prev_data
            
            # Add state info to pose
            pose['confirmed_state'] = confirmed_state
            pose['state_transition'] = 'standing_to_fallen' if pose in [f for f in fall_transitions] else None
        
        # Cleanup old person states (not seen for a while)
        self._cleanup_old_states(camera_id, current_time)
        
        return {
            'poses': poses,
            'frame': annotated_frame,
            'person_count': len(poses),
            'fall_transitions': fall_transitions
        }
    
    def _get_person_key(self, camera_id, bbox):
        """Generate a tracking key for a person based on bbox center."""
        x1, y1, x2, y2 = bbox
        center_x = (x1 + x2) // 2
        center_y = (y1 + y2) // 2
        # Quantize to grid cells for approximate matching
        grid_x = center_x // 50
        grid_y = center_y // 50
        return f"p_{grid_x}_{grid_y}"
    
    def _cleanup_old_states(self, camera_id, current_time):
        """Remove stale person tracking data."""
        if camera_id not in self.person_states:
            return
        
        stale_keys = []
        for key, data in self.person_states[camera_id].items():
            if current_time - data.get('last_seen', 0) > self.tracking_timeout:
                stale_keys.append(key)
        
        for key in stale_keys:
            del self.person_states[camera_id][key]


# Import Path here to avoid circular import
from pathlib import Path
