"""
CEMSS - Campus Event management and Surveillance System
Detection Pipeline - Main Orchestration
"""
import threading
import time
import cv2
from queue import Queue
from datetime import datetime, timedelta
from pathlib import Path
from detection.detector import MultiModelDetector
from detection.detection_config import DetectionConfig
from detection.severity_scorer import get_severity_scorer
from detection.video_overlay import add_timestamp_overlay
from detection.video_overlay import add_timestamp_overlay
from config import (
    VIDEO_CLIP_DURATION, VIDEO_FPS, CROWD_THRESHOLD, CROWD_ALERT_COOLDOWN_SECONDS,
    TIMESTAMP_ENABLED, TIMESTAMP_FORMAT, TIMESTAMP_POSITION,
    TIMESTAMP_FONT_SCALE, TIMESTAMP_COLOR, TIMESTAMP_BG_COLOR, TIMESTAMP_BG_ALPHA
)


from detection.continuous_analyzer import ContinuousAnalysisManager
from detection.camera_manager import CameraPool
from detection.video_recorder import VideoRecorderPool

class DetectionPipeline:
    """Main detection pipeline orchestrating cameras, detectors, and recording"""
    
    def __init__(self, logging_manager, alert_manager, flask_app=None):
        """
        Initialize detection pipeline
        
        Args:
            logging_manager: LoggingManager instance
            alert_manager: AlertManager instance
            flask_app: Flask app instance for database operations
        """
        self.logging_manager = logging_manager
        self.alert_manager = alert_manager
        self.flask_app = flask_app
        
        # Components
        self.camera_pool = CameraPool()
        self.recorder_pool = VideoRecorderPool()
        self.multi_detector = None
        
        # Detection threads
        self.detection_threads = {}  # camera_id -> thread
        self.active_detections = {}  # camera_id -> set of active model names
        self.global_detection_enabled = False
        
        # Control
        self.is_running = False
        self.lock = threading.Lock()
        
        # Detection event queue (for alert processing)
        self.detection_queue = Queue()
        
        # Last detection times (for throttling)
        self.last_detections = {}  # (camera_id, model_name) -> datetime
        
        # Crowd detection tracking
        self.last_crowd_alerts = {}  # camera_id -> datetime
        self.crowd_start_times = {}  # camera_id -> datetime (when crowd first detected)
        # OpenCV crowd detector removed per user request (using YOLO only)
        self.opencv_crowd_detector = None
        
        # Phase 1: Temporal smoothing tracker
        # Tracks consecutive frame detections: {(camera_id, model_name): count}
        self.detection_frame_counter = {}
        
        # Phase 1: Multi-model fusion tracker
        # Tracks concurrent detections across models: {camera_id: {model_name: timestamp}}
        self.concurrent_detections = {}
        
        # Phase 1: Severity scorer
        self.severity_scorer = get_severity_scorer()
        
        # Initialize multi-model detector
        try:
            self.multi_detector = MultiModelDetector()
            print(f"✓ Loaded detection models: {self.multi_detector.get_loaded_models()}")
        except Exception as e:
            print(f"✗ Failed to load detection models: {str(e)}")
        
        # Initialize LLM video analyzer for intelligent analysis
        self.llm_analyzer = None
        try:
            from config import OLLAMA_ENABLED, OLLAMA_HOST, OLLAMA_MODEL
            if OLLAMA_ENABLED:
                from detection.llm_video_analyzer import LLMVideoAnalyzer
                self.llm_analyzer = LLMVideoAnalyzer(ollama_host=OLLAMA_HOST, model=OLLAMA_MODEL)
                if self.llm_analyzer.is_available():
                    print("✓ LLM Video Analyzer loaded for enhanced detection validation")
                else:
                    self.llm_analyzer = None
                    print("⚠ LLM Video Analyzer service not available")
        except Exception as e:
            print(f"⚠ LLM Video Analyzer initialization failed: {str(e)}")

        # Initialize Continuous Analysis Manager
        self.continuous_analyzer = None
        try:
            from utils.vlm_frame_analyzer import create_vlm_analyzer
            
            from config import VLM_SCAN_INTERVAL

            # We need a VLM analyzer instance
            vlm_analyzer = create_vlm_analyzer(self.flask_app)
            
            if vlm_analyzer and vlm_analyzer.is_available():
                self.continuous_analyzer = ContinuousAnalysisManager(
                    vlm_analyzer=vlm_analyzer,
                    flask_app=self.flask_app,
                    interval_seconds=float(VLM_SCAN_INTERVAL),
                    motion_timeout=float(VLM_SCAN_INTERVAL)
                )
                print("✓ Continuous Analysis Manager initialized (5s interval)")
            else:
                print("⚠ VLM not available for continuous analysis")
        except Exception as e:
            print(f"⚠ Continuous Analysis Manager initialization failed: {str(e)}")
        
        # Initialize Self-Learning System
        self.learning_system = None
        self.vlm_verifier = None
        try:
            from config import LEARNING_ENABLED
            if LEARNING_ENABLED:
                from utils.learning_system import LearningSystem
                from utils.vlm_verifier import VLMVerifier
                
                self.learning_system = LearningSystem(flask_app=self.flask_app)
                self.vlm_verifier = VLMVerifier()
                
                # Start verification worker thread
                verification_thread = threading.Thread(
                    target=self._vlm_verification_worker,
                    daemon=True
                )
                verification_thread.start()
                
                print("✓ Self-Learning System initialized (autonomous VLM verification)")
            else:
                print("⚠ Self-Learning System disabled in configuration")
        except Exception as e:
            print(f"⚠ Self-Learning System initialization failed: {str(e)}")

    
    def add_camera(self, camera_id, source, name, autostart=True):
        """
        Add a camera to the pipeline
        
        Args:
            camera_id: Database ID of the camera
            source: Camera source (RTSP URL, device index, file path)
            name: Display name
            autostart: Whether to start the camera immediately
        
        Returns:
            bool: Success status
        """
        try:
            camera = self.camera_pool.add_camera(camera_id, source, name)
            
            if autostart:
                camera.start()
            
            # Create recorder for this camera
            self.recorder_pool.get_or_create_recorder(camera_id, name)
            
            self.logging_manager.log_camera_event(name, "ADDED", f"Source: {source}")
            return True
        
        except Exception as e:
            print(f"Failed to add camera {name}: {str(e)}")
            return False
    
    def remove_camera(self, camera_id):
        """Remove a camera from the pipeline"""
        self.stop_detection(camera_id)
        self.stop_recording(camera_id)
        self.camera_pool.remove_camera(camera_id)
        self.recorder_pool.remove_recorder(camera_id)
    
    def start_detection(self, camera_id, models=None):
        """
        Start detection for a camera
        
        Args:
            camera_id: Database ID of the camera
            models: List of model names to activate, or None for all loaded models
        """
        if self.multi_detector is None:
            print("No detection models loaded")
            return False
        
        with self.lock:
            # Set active models for this camera
            if models is None:
                models = self.multi_detector.get_loaded_models()
            
            # Always include 'person' model for crowd detection (person detection is always on)
            if 'person' not in models and 'person' in self.multi_detector.get_loaded_models():
                models = list(models) + ['person']
            
            self.active_detections[camera_id] = set(models)
            
            # Start detection thread if not already running
            if camera_id not in self.detection_threads or not self.detection_threads[camera_id].is_alive():
                thread = threading.Thread(
                    target=self._detection_worker,
                    args=(camera_id,),
                    daemon=True
                )
                thread.start()
                self.detection_threads[camera_id] = thread
            
            camera = self.camera_pool.get_camera(camera_id)
            if camera:
                self.logging_manager.log_camera_event(
                    camera.name, "DETECTION_STARTED", f"Models: {', '.join(models)}"
                )
            
            return True
    
    def stop_detection(self, camera_id):
        """Stop detection for a camera"""
        with self.lock:
            if camera_id in self.active_detections:
                del self.active_detections[camera_id]
            
            camera = self.camera_pool.get_camera(camera_id)
            if camera:
                self.logging_manager.log_camera_event(camera.name, "DETECTION_STOPPED", "")
    
    def start_global_detection(self, models=None):
        """Start detection for all cameras"""
        self.global_detection_enabled = True
        
        for camera_id in self.camera_pool.get_active_cameras():
            self.start_detection(camera_id, models)
    
    def stop_global_detection(self):
        """Stop detection for all cameras"""
        self.global_detection_enabled = False
        
        with self.lock:
            camera_ids = list(self.active_detections.keys())
        
        for camera_id in camera_ids:
            self.stop_detection(camera_id)
    
    # ==================== Phase 1: Helper Methods ====================
    
    def _apply_temporal_smoothing(self, camera_id, model_name, detected):
        """
        Apply temporal smoothing to reduce false positives
        
        Args:
            camera_id: Camera ID
            model_name: Model name
            detected: Whether detection occurred this frame
        
        Returns:
            bool: True if detection passes smoothing threshold
        """
        key = (camera_id, model_name)
        required_frames = DetectionConfig.get_required_frames(model_name)
        
        if detected:
            # Increment consecutive detection counter
            self.detection_frame_counter[key] = self.detection_frame_counter.get(key, 0) + 1
            
            # Check if we've reached the threshold
            if self.detection_frame_counter[key] >= required_frames:
                return True
        else:
            # Reset counter if no detection
            if key in self.detection_frame_counter:
                del self.detection_frame_counter[key]
        
        return False
    
    def _track_concurrent_detections(self, camera_id, model_name):
        """
        Track concurrent detections across multiple models for fusion
        
        Args:
            camera_id: Camera ID
            model_name: Model detected
        
        Returns:
            list: List of currently active model names
        """
        now = datetime.now()
        window_seconds = 2  # 2-second window for concurrent detection
        
        # Initialize camera tracking
        if camera_id not in self.concurrent_detections:
            self.concurrent_detections[camera_id] = {}
        
        # Add current detection
        self.concurrent_detections[camera_id][model_name] = now
        
        # Clean up old detections (outside window)
        active_models = []
        for model, timestamp in list(self.concurrent_detections[camera_id].items()):
            if (now - timestamp).total_seconds() <= window_seconds:
                active_models.append(model)
            else:
                del self.concurrent_detections[camera_id][model]
        
        return active_models
    
    def _calculate_detection_severity(self, camera_id, model_name, confidence, zone_id=None, concurrent_models=None):
        """
        Calculate severity score for a detection
        
        Args:
            camera_id: Camera ID
            model_name: Model name
            confidence: Detection confidence
            zone_id: Restricted zone ID if applicable
            concurrent_models: List of concurrent model detections
        
        Returns:
            dict: Severity information {score, level, factors}
        """
        detection_data = {}
        if concurrent_models and len(concurrent_models) > 1:
            detection_data['concurrent_models'] = concurrent_models
        
        severity = self.severity_scorer.calculate_severity(
            camera_id=camera_id,
            model_name=model_name,
            confidence=confidence,
            timestamp=datetime.now(),
            zone_id=zone_id,
            detection_data=detection_data
        )
        
        return severity
    
    def _detection_worker(self, camera_id):
        """
        Detection worker thread for a single camera
        
        Args:
            camera_id: Database ID of the camera
        """
        camera = self.camera_pool.get_camera(camera_id)
        if not camera:
            return
        
        recorder = self.recorder_pool.get_or_create_recorder(camera_id, camera.name)
        post_detection_frames = []  # Buffer for post-detection frames
        in_clip_mode = False
        clip_frame_count = 0
        clip_total_frames = int(VIDEO_CLIP_DURATION * VIDEO_FPS / 2)  # Half for post-detection
        last_detection_result = None
        
        # Frame skipping for video files (optimize performance)
        frame_counter = 0
        is_video_file = isinstance(camera.source, str) and camera.source.endswith(('.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv'))
        
        # Import video frame skip rate
        from config import VIDEO_FRAME_SKIP_RATE
        frame_skip_rate = VIDEO_FRAME_SKIP_RATE if is_video_file else 1
        
        if is_video_file:
            print(f"✓ Video file detected for {camera.name}, using frame skip rate: {frame_skip_rate}")
        
        while camera_id in self.active_detections:
            try:
                # Get frame
                frame = camera.get_frame(timeout=1.0)
                if frame is None:
                    time.sleep(0.1)
                    continue
                
                # Add timestamp overlay if enabled
                if TIMESTAMP_ENABLED:
                    # Create copy to preserve raw frame for VLM/Analysis (avoid in-place modification of last_frame)
                    frame = frame.copy()
                    
                    frame = add_timestamp_overlay(
                        frame,
                        camera_name=camera.name,
                        position=TIMESTAMP_POSITION,
                        timestamp_format=TIMESTAMP_FORMAT,
                        font_scale=TIMESTAMP_FONT_SCALE,
                        text_color=TIMESTAMP_COLOR,
                        bg_color=TIMESTAMP_BG_COLOR,
                        bg_alpha=TIMESTAMP_BG_ALPHA
                    )
                
                # Always add frame to recorder buffer
                recorder.write_frame(frame)
                
                # Increment frame counter
                frame_counter += 1
                
                # Skip frames for video files (process every Nth frame)
                if is_video_file and frame_skip_rate > 1 and frame_counter % frame_skip_rate != 0:
                    # Still collect post-detection frames if in clip mode
                    if in_clip_mode:
                        post_detection_frames.append(frame.copy())
                        clip_frame_count += 1
                    continue  # Skip detection for this frame
                
                # Run motion detection for continuous analysis
                motion_detected = False
                if self.continuous_analyzer:
                    # Initialize thread-local motion detector if needed
                    if not hasattr(recorder, 'motion_detector'):
                        from detection.motion_detector import create_motion_detector
                        recorder.motion_detector = create_motion_detector(sensitivity='medium')
                    
                    motion_detected, _, _ = recorder.motion_detector.detect_motion(frame)
                    
                    # Process for continuous analysis
                    self.continuous_analyzer.process_frame(camera_id, frame, motion_detected)

                # Get active models for this camera
                active_models = list(self.active_detections.get(camera_id, []))
                
                if not active_models:
                    time.sleep(0.1)
                    continue
                
                # Run detection
                detection_result = self.multi_detector.detect(frame, active_models)
                
                # Phase 1: Process each model's detections with temporal smoothing
                detection_occurred = False
                for model_name, result in detection_result['results'].items():
                    detected_this_frame = result.get('detection_count', 0) > 0
                    
                    # Apply temporal smoothing to reduce false positives
                    passes_smoothing = self._apply_temporal_smoothing(
                        camera_id, model_name, detected_this_frame
                    )
                    
                    # Only proceed if detection passes temporal smoothing threshold
                    if detected_this_frame and passes_smoothing:
                        detection_occurred = True
                        
                        # Track concurrent detections for multi-model fusion
                        concurrent_models = self._track_concurrent_detections(camera_id, model_name)
                        
                        # For person detection, check restricted zones
                        should_alert = True
                        zone_info = None
                        zone_id = None
                        
                        if model_name == 'person':
                            # Get restricted zones for this camera
                            restricted_zones = self._get_camera_restricted_zones(camera_id)
                            
                            if restricted_zones:
                                # Check if any detection is in a restricted zone
                                from detection.zone_utils import check_detection_in_zones
                                
                                # Get frame dimensions for coordinate normalization
                                frame_height, frame_width = frame.shape[:2]
                                
                                in_zone = False
                                for detection in result['detections']:
                                    zone_check = check_detection_in_zones(
                                        detection, restricted_zones, 
                                        frame_width=frame_width, 
                                        frame_height=frame_height
                                    )
                                    if zone_check['in_zone']:
                                        in_zone = True
                                        zone_info = zone_check
                                        zone_id = zone_check.get('zone_id')
                                        break
                                
                                # Only alert if person is in a restricted zone
                                should_alert = in_zone
                                
                                if not in_zone:
                                    # Log detection but don't alert
                                    self.logging_manager.log_detection(
                                        camera_id, camera.name, model_name,
                                        max([d['confidence'] for d in result['detections']]),
                                        result['detections'],
                                        note="Outside restricted zones - no alert"
                                    )
                            
                            # Check for crowd detection (always check regardless of zones)
                            person_count = result.get('detection_count', 0)
                            if person_count >= CROWD_THRESHOLD:
                                # Draw crowd detection overlay on frame
                                frame_height, frame_width = frame.shape[:2]
                                # Red border around frame
                                cv2.rectangle(frame, (5, 5), (frame_width - 5, frame_height - 5), (0, 0, 255), 4)
                                # Crowd detection text at top
                                crowd_text = f"CROWD DETECTED: {person_count} people"
                                text_size, _ = cv2.getTextSize(crowd_text, cv2.FONT_HERSHEY_SIMPLEX, 1.2, 3)
                                text_x = (frame_width - text_size[0]) // 2
                                # Background for text
                                cv2.rectangle(frame, (text_x - 10, 10), (text_x + text_size[0] + 10, 50 + text_size[1]), (0, 0, 255), -1)
                                cv2.putText(frame, crowd_text, (text_x, 40 + text_size[1] // 2), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 3)
                                
                                # Trigger crowd alert if threshold exceeded for more than 5 minutes
                                if self._should_trigger_crowd_alert(camera_id, person_count):
                                    # Create video clip for crowd event (recent frames)
                                    clip_path = None
                                    if recorder:
                                        clip_path = recorder.save_recent_clip(duration=5)
                                        if clip_path:
                                            self.logging_manager.log_camera_event(
                                                camera.name, "CLIP_CREATED", f"Crowd detection clip: {clip_path}"
                                            )

                                    # Queue crowd detection alert
                                    crowd_event = {
                                        'camera_id': camera_id,
                                        'camera_name': camera.name,
                                        'model_name': 'crowd',
                                        'confidence': max([d['confidence'] for d in result['detections']]),
                                        'detection_data': result['detections'],
                                        'timestamp': datetime.now(),
                                        'video_clip_path': clip_path,
                                        'severity_score': 8,  # High severity for crowd
                                        'severity_level': 'HIGH',
                                        'severity_factors': [f'Crowd accumulated for > 5 min ({person_count} people detected)'],
                                        'person_count': person_count
                                    }
                                    self.detection_queue.put(crowd_event)
                                    self.logging_manager.log_detection(
                                        camera_id, camera.name, 'crowd',
                                        max([d['confidence'] for d in result['detections']]),
                                        result['detections'],
                                        note=f"Crowd Alert: Persisted for > 5 min with {person_count} people"
                                    )
                            else:
                                # Reset crowd timer if count drops below threshold
                                if camera_id in self.crowd_start_times:
                                    del self.crowd_start_times[camera_id]
                        
                        # Heatmap disabled per user request
                        
                        # Calculate severity score for this detection (requires app context for DB rules)
                        max_confidence = max([d['confidence'] for d in result['detections']])
                        severity_info = {'score': 5, 'level': 'MEDIUM', 'factors': []}
                        
                        try:
                            if self.flask_app:
                                with self.flask_app.app_context():
                                    severity_info = self._calculate_detection_severity(
                                        camera_id, model_name, max_confidence,
                                        zone_id=zone_id,
                                        concurrent_models=concurrent_models if len(concurrent_models) > 1 else None
                                    )
                            else:
                                # Fallback if no app available (shouldn't happen in production)
                                severity_info = self._calculate_detection_severity(
                                    camera_id, model_name, max_confidence,
                                    zone_id=zone_id,
                                    concurrent_models=concurrent_models if len(concurrent_models) > 1 else None
                                )
                        except Exception as score_err:
                            print(f"Error calculating severity: {score_err}")
                        
                        # Check if we should trigger an alert (with throttling and zone check)
                        if should_alert and self._should_trigger_alert(camera_id, model_name):
                            last_detection_result = (model_name, result, zone_info, severity_info)
                            
                            # Start clip mode
                            if not in_clip_mode:
                                in_clip_mode = True
                                clip_frame_count = 0
                                post_detection_frames = []
                
                # Collect post-detection frames for clip
                if in_clip_mode:
                    post_detection_frames.append(frame.copy())
                    clip_frame_count += 1
                    
                    # Create clip after collecting enough frames
                    if clip_frame_count >= clip_total_frames:
                        in_clip_mode = False
                        
                        if last_detection_result:
                            model_name, result, zone_info, severity_info = last_detection_result
                            
                            # Create video clip
                            frame_height, frame_width = frame.shape[:2]
                            clip_path = recorder.create_clip(
                                post_detection_frames,
                                frame_width,
                                frame_height,
                                event_type=model_name
                            )
                            
                            # Queue detection event with video clip and severity for alert processing
                            event_data = {
                                'camera_id': camera_id,
                                'camera_name': camera.name,
                                'model_name': model_name,
                                'confidence': max([d['confidence'] for d in result['detections']]),
                                'detection_data': result['detections'],
                                'timestamp': datetime.now(),
                                'video_clip_path': clip_path,  # Include clip path for email attachment
                                'severity_score': severity_info['score'],
                                'severity_level': severity_info['level'],
                                'severity_factors': severity_info['factors']
                            }
                            
                            # Add zone info if available
                            if zone_info:
                                event_data['zone_name'] = zone_info.get('zone_name')
                                event_data['zone_id'] = zone_info.get('zone_id')
                            
                            # LLM Analysis: Analyze clip if LLM is available and enabled
                            if self.llm_analyzer and clip_path and model_name == 'fall':
                                try:
                                    from config import OLLAMA_ANALYSIS_MODE, OLLAMA_KEYFRAMES_PER_CLIP
                                    
                                    if OLLAMA_ANALYSIS_MODE in ['post_detection', 'clip_only']:
                                        print(f"  Analyzing clip with LLM ({OLLAMA_KEYFRAMES_PER_CLIP} frames)...")
                                        llm_result = self.llm_analyzer.analyze_clip(
                                            clip_path,
                                            num_frames=OLLAMA_KEYFRAMES_PER_CLIP,
                                            analysis_type='fall_detection'
                                        )
                                        
                                        if llm_result.get('success'):
                                            # Add LLM insights to event data
                                            event_data['llm_analysis'] = {
                                                'fall_detected': llm_result.get('fall_detected'),
                                                'confidence': llm_result.get('confidence'),
                                                'summary': llm_result.get('summary'),
                                                'analysis_time': llm_result.get('analysis_time')
                                            }
                                            
                                            # Boost/reduce severity based on LLM validation
                                            if llm_result.get('fall_detected'):
                                                if llm_result.get('confidence') == 'HIGH':
                                                    event_data['severity_score'] = min(10, event_data['severity_score'] + 2)
                                                    print(f"  ✓ LLM CONFIRMS fall with HIGH confidence")
                                                elif llm_result.get('confidence') == 'MEDIUM':
                                                    event_data['severity_score'] = min(10, event_data['severity_score'] + 1)
                                                    print(f"  ✓ LLM confirms fall with MEDIUM confidence")
                                            else:
                                                event_data['severity_score'] = max(1, event_data['severity_score'] - 2)
                                                print(f"  ⚠ LLM does not detect fall - reducing severity")
                                except Exception as llm_error:
                                    print(f"  ⚠ LLM analysis error: {llm_error}")
                            
                            self.detection_queue.put(event_data)
                            
                            last_detection_result = None
                
                # Increased sleep to significantly reduce CPU idle overhead
                from config import LOW_POWER_MODE
                time.sleep(0.1 if LOW_POWER_MODE else 0.05)
            
            except Exception as e:
                print(f"Error in detection worker for camera {camera_id}: {str(e)}")
                time.sleep(1)
    
    def _should_trigger_crowd_alert(self, camera_id):
        """
        Check if we should trigger a crowd alert based on cooldown
        
        Args:
            camera_id: Database ID of the camera
            
        Returns:
            bool: True if alert should be triggered
        """
        from config import CROWD_ALERT_COOLDOWN_SECONDS
        
        current_time = datetime.now()
        last_alert_time = self.last_crowd_alerts.get(camera_id)
        
        # If no previous alert or cooldown passed
        if last_alert_time is None or (current_time - last_alert_time).total_seconds() > CROWD_ALERT_COOLDOWN_SECONDS:
            self.last_crowd_alerts[camera_id] = current_time
            return True
            
        return False

    def _should_trigger_alert(self, camera_id, model_name):
        """
        Check if an alert should be triggered (with throttling)
        
        Args:
            camera_id: Database ID of the camera
            model_name: Name of the detection model
        
        Returns:
            bool: Whether to trigger an alert
        """
        from config import ALERT_COOLDOWN_SECONDS
        
        key = (camera_id, model_name)
        now = datetime.now()
        
        if key in self.last_detections:
            time_since_last = (now - self.last_detections[key]).total_seconds()
            if time_since_last < ALERT_COOLDOWN_SECONDS:
                return False
        
        self.last_detections[key] = now
        return True
    
    def _should_trigger_crowd_alert(self, camera_id, person_count):
        """
        Check if a crowd alert should be triggered (after 5 minutes of accumulation)
        
        Args:
            camera_id: Database ID of the camera
            person_count: Current person count
        
        Returns:
            bool: Whether to trigger a crowd alert
        """
        from config import CROWD_ACCUMULATION_TIMEOUT, CROWD_ALERT_COOLDOWN_SECONDS
        now = datetime.now()
        
        # 1. Track accumulation start
        if camera_id not in self.crowd_start_times:
            self.crowd_start_times[camera_id] = now
            print(f"  → Crowd accumulation started for camera {camera_id}")
            return False
            
        # 2. Check if enough time has passed
        duration = (now - self.crowd_start_times[camera_id]).total_seconds()
        if duration < CROWD_ACCUMULATION_TIMEOUT:
            # Not yet reached accumulation threshold
            return False
            
        # 3. Check cooldown to prevent alert spam
        if camera_id in self.last_crowd_alerts:
            time_since_last = (now - self.last_crowd_alerts[camera_id]).total_seconds()
            if time_since_last < CROWD_ALERT_COOLDOWN_SECONDS:
                return False
        
        self.last_crowd_alerts[camera_id] = now
        return True
    
    def _get_camera_restricted_zones(self, camera_id):
        """
        Get restricted zones for a camera
        
        Args:
            camera_id: Database ID of the camera
        
        Returns:
            list: List of zone dictionaries with coordinates and metadata
        """
        try:
            # Import Flask app to get application context
            from app import app
            from models import RestrictedZone
            
            # Use app context for database query (needed since we're in a worker thread)
            with app.app_context():
                zones = RestrictedZone.query.filter_by(
                    camera_id=camera_id,
                    enabled=True
                ).all()
                return [zone.to_dict() for zone in zones]
        except Exception as e:
            print(f"Error fetching restricted zones: {str(e)}")
            return []
    
    def start_recording(self, camera_id):
        """Start full recording for a camera"""
        camera = self.camera_pool.get_camera(camera_id)
        if not camera:
            return None
        
        recorder = self.recorder_pool.get_or_create_recorder(camera_id, camera.name)
        
        # Get frame dimensions
        frame = camera.get_last_frame()
        if frame is None:
            return None
        
        frame_height, frame_width = frame.shape[:2]
        return recorder.start_full_recording(frame_width, frame_height)
    
    def stop_recording(self, camera_id):
        """Stop full recording for a camera"""
        recorder = self.recorder_pool.recorders.get(camera_id)
        if recorder:
            return recorder.stop_full_recording()
        return None
    
    def get_latest_frame(self, camera_id, annotated=False):
        """
        Get the latest frame from a camera
        
        Args:
            camera_id: Database ID of the camera
            annotated: Whether to return annotated frame with detections
        
        Returns:
            frame: OpenCV frame, or None if unavailable
        """
        camera = self.camera_pool.get_camera(camera_id)
        if not camera:
            return None
        
        frame = camera.get_last_frame()
        
        if frame is None:
            return None
            
        # Create a copy to avoid modifying the original frame (which VLM uses)
        frame = frame.copy()
        
        # Add timestamp overlay if enabled (for live streaming)
        if frame is not None and TIMESTAMP_ENABLED:
            frame = add_timestamp_overlay(
                frame,
                camera_name=camera.name,
                position=TIMESTAMP_POSITION,
                timestamp_format=TIMESTAMP_FORMAT,
                font_scale=TIMESTAMP_FONT_SCALE,
                text_color=TIMESTAMP_COLOR,
                bg_color=TIMESTAMP_BG_COLOR,
                bg_alpha=TIMESTAMP_BG_ALPHA
            )
        
        # Write frame to recorder buffer for clip creation
        if frame is not None and camera_id in self.active_detections:
            recorder = self.recorder_pool.recorders.get(camera_id)
            if recorder:
                recorder.write_frame(frame)
                
        return frame
    
    def get_recent_clip(self, camera_id):
        """
        Get a video clip of the recent few seconds from a camera
        
        Args:
            camera_id: Database ID of the camera
            
        Returns:
            str: Path to the video clip, or None if unavailable
        """
        recorder = self.recorder_pool.recorders.get(camera_id)
        if not recorder:
            # Try to get or create just in case
            camera = self.camera_pool.get_camera(camera_id)
            if camera:
                recorder = self.recorder_pool.get_or_create_recorder(camera_id, camera.name)
            else:
                return None
                
        if recorder:
            return recorder.save_recent_clip(duration=5)
        
        return None

    def get_camera(self, camera_id):
        """Delegate get_camera to camera_pool"""
        if self.camera_pool:
            return self.camera_pool.get_camera(camera_id)
        return None
                # Legacy line removed

        
        if frame is not None and annotated and camera_id in self.active_detections:
            active_models = list(self.active_detections[camera_id])
            
            # Draw skeletal tracking if person or fall detection is active
            if self.pose_estimator and ('person' in active_models or 'fall' in active_models):
                try:
                    # Use state-tracking for fall detection
                    if 'fall' in active_models:
                        pose_result = self.pose_estimator.detect_with_state_tracking(
                            frame, 
                            camera_id,
                            draw_skeleton=False, 
                            draw_keypoints=False
                        )
                        
                        # Check for fall transitions and trigger alerts
                        fall_transitions = pose_result.get('fall_transitions', [])
                        for fall in fall_transitions:
                            camera_obj = camera
                            self._handle_fall_transition(camera_id, camera_obj.name, fall)
                    else:
                        # Regular pose detection without state tracking
                        pose_result = self.pose_estimator.detect_poses(
                            frame, 
                            draw_skeleton=False, 
                            draw_keypoints=False
                        )
                    
                    frame = pose_result.get('frame', frame)
                    
                    # Add person count overlay
                    person_count = pose_result.get('person_count', 0)
                    if person_count > 0:
                        cv2.putText(
                            frame, 
                            f"People: {person_count}", 
                            (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 
                            1.0, 
                            (0, 255, 0), 
                            2
                        )
                except Exception as e:
                    pass  # Silently fail if pose estimation fails
            
            # Run other detections for annotation
            if active_models and self.multi_detector:
                # Skip person and fall models since we already handled them with pose estimator
                skip_models = ['person']
                if self.pose_estimator and 'fall' in active_models:
                    skip_models.append('fall')
                models_to_run = [m for m in active_models if m not in skip_models] if self.pose_estimator else active_models
                if models_to_run:
                    # Run without annotation to keep "background"
                    result = self.multi_detector.detect(frame, models_to_run, annotate=False)
                    frame = result.get('frame', frame)
                    
                    # If we didn't use pose estimator (fallback), we still need to draw person count
                    if not self.pose_estimator and ('person' in models_to_run or 'fall' in models_to_run):
                        person_res = result.get('results', {}).get('person', {})
                        fall_res = result.get('results', {}).get('fall', {})
                        
                        # Get max count from person or fall detection
                        p_count = person_res.get('detection_count', 0)
                        f_count = fall_res.get('detection_count', 0)
                        final_count = max(p_count, f_count)
                        
                        if final_count > 0:
                             cv2.putText(
                                frame, 
                                f"People: {final_count}", 
                                (10, 30),
                                cv2.FONT_HERSHEY_SIMPLEX, 
                                1.0, 
                                (0, 255, 0), 
                                2
                            )
        
        return frame
    
    def _handle_fall_transition(self, camera_id, camera_name, fall_data):
        """Handle a fall state transition and trigger alert with video clip."""
        try:
            self.logging_manager.log_camera_event(
                camera_name,
                "FALL_TRANSITION",
                f"Person transitioned from standing to fallen (confidence: {fall_data.get('confidence', 0):.0%})"
            )
            
            # Create video clip for this fall event
            clip_path = None
            try:
                recorder = self.recorder_pool.recorders.get(camera_id)
                camera = self.camera_pool.get_camera(camera_id)
                
                if recorder and camera:
                    # Get current frame for dimensions
                    frame = camera.get_last_frame()
                    if frame is not None:
                        frame_height, frame_width = frame.shape[:2]
                        
                        # Get buffered frames and create clip
                        # Use the buffer frames we already have
                        clip_path = recorder.create_clip(
                            frames_after_detection=[],  # No additional frames needed
                            frame_width=frame_width,
                            frame_height=frame_height,
                            event_type="fall"
                        )
                        
                        if clip_path:
                            self.logging_manager.log_camera_event(
                                camera_name,
                                "CLIP_CREATED",
                                f"Fall detection clip saved: {clip_path}"
                            )
            except Exception as e:
                print(f"Error creating fall clip: {e}")
            
            # Queue fall detection event for alert processing
            self.detection_queue.put({
                'camera_id': camera_id,
                'camera_name': camera_name,
                'model_name': 'fall',
                'confidence': fall_data.get('confidence', 0),
                'detection_data': {
                    'bbox': fall_data.get('bbox', []),
                    'transition': 'standing_to_fallen',
                    'distance': fall_data.get('distance', 'unknown')
                },
                'video_clip_path': clip_path,
                'note': 'State transition: standing → fallen'
            })
        except Exception as e:
            print(f"Error handling fall transition: {e}")
    
    def _vlm_verification_worker(self):
        """Background worker that processes VLM verification queue"""
        import logging
        from config import VLM_BATCH_SIZE
        
        logger = logging.getLogger(__name__)
        logger.info("VLM Verification worker started")
        
        batch_size = VLM_BATCH_SIZE
        
        while True:
            try:
                if not self.learning_system or not self.vlm_verifier:
                    time.sleep(60)
                    continue
                
                # Get pending verifications from queue
                pending = self.learning_system.get_verification_queue(limit=batch_size)
                
                if not pending:
                    # No work to do, sleep for a minute
                    time.sleep(60)
                    continue
                
                logger.info(f"Processing {len(pending)} detection verifications...")
                
                # Process each verification
                successful = 0
                for item in pending:
                    try:
                        # Call VLM verifier
                        vlm_result = self.vlm_verifier.verify_detection(
                            image_path=item['image_path'],
                            model_name=item['model_name'],
                            detection_data=item['detection_data']
                        )
                        
                        if vlm_result:
                            # Add image path to result
                            vlm_result['image_path'] = item['image_path']
                            
                            # Store verification in database
                            self.learning_system.process_vlm_verification(
                                detection_log_id=item['detection_log_id'],
                                vlm_result=vlm_result,
                                flask_app=self.flask_app
                            )
                            
                            successful += 1
                            logger.info(f"  ✓ Verified detection {item['detection_log_id']}: {vlm_result['verification_result']}")
                        else:
                            logger.warning(f"  ✗ VLM verification failed for detection {item['detection_log_id']}")
                    
                    except Exception as e:
                        logger.error(f"Error verifying detection {item.get('detection_log_id')}: {str(e)}")
                
                # Remove processed items from queue
                self.learning_system.clear_verification_queue(count=len(pending))
                
                logger.info(f"VLM verification batch complete: {successful}/{len(pending)} successful")
                
                # Check if any models need retraining
                try:
                    from config import DETECTION_MODELS
                    for model_name in DETECTION_MODELS.keys():
                        if self.learning_system.check_retraining_needed(model_name, self.flask_app):
                            logger.info(f"Model '{model_name}' has enough verified samples for retraining")
                            self.learning_system.queue_for_retraining(
                                model_name=model_name,
                                priority='MEDIUM',
                                flask_app=self.flask_app
                            )
                except Exception as e:
                    logger.error(f"Error checking retraining status: {str(e)}")
                
                # Small sleep before next batch
                time.sleep(10)
            
            except Exception as e:
                logger.error(f"Error in VLM verification worker: {str(e)}")
                time.sleep(60)
    
    def _sample_detection_for_learning(self, camera_id, model_name, frame, detection_log_id, detection_data):
        """
        Randomly sample detection for VLM verification
        
        Args:
            camera_id: Camera ID
            model_name: Model that made detection
            frame: Detection frame
            detection_log_id: Database ID of detection log
            detection_data: Detection metadata (count, confidence, etc.)
        """
        if not self.learning_system:
            return
        
        # Check if should sample
        if self.learning_system.should_sample_detection(camera_id, model_name):
            try:
                from config import VERIFICATION_IMAGE_DIR
                import cv2
                import os
                from datetime import datetime
                
                # Create filename
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{model_name}_{camera_id}_{timestamp}_{detection_log_id}.jpg"
                image_path = os.path.join(VERIFICATION_IMAGE_DIR, filename)
                
                # Save frame
                cv2.imwrite(image_path, frame)
                
                # Queue for VLM verification
                self.learning_system.queue_for_vlm_verification(
                    detection_log_id=detection_log_id,
                    image_path=image_path,
                    model_name=model_name,
                    detection_data=detection_data
                )
                
                print(f"  → Sampled {model_name} detection for learning")
            
            except Exception as e:
                print(f"Error sampling detection for learning: {str(e)}")

    
    def process_detection_queue(self):
        """Process detection events and trigger alerts (run in separate thread)"""
        while self.is_running:
            try:
                # Get detection event (with timeout to allow checking is_running)
                if not self.detection_queue.empty():
                    event = self.detection_queue.get(timeout=1)
                    
                    # Create application context for the entire processing block
                    # This ensures both DB logging and AlertManager have access to the context
                    if self.flask_app:
                        context = self.flask_app.app_context()
                        context.push()
                    else:
                        context = None

                    try:
                        # Log detection to file
                        self.logging_manager.log_detection(
                            event['camera_id'],
                            event['camera_name'],
                            event['model_name'],
                            event['confidence'],
                            event['detection_data']
                        )
                        
                        # Save detection to database (for Recent Detections panel)
                        if self.flask_app:
                            try:
                                from models import DetectionLog, db
                                import json
                                
                                # Context is already active
                                detection_log = DetectionLog(
                                    camera_id=event['camera_id'],
                                    model_name=event['model_name'],
                                    confidence=event['confidence'],
                                    detection_data=json.dumps(event.get('detection_data', [])),
                                    severity_level=event.get('severity_level', 'MEDIUM'),
                                    severity_score=event.get('severity_score', 5)
                                )
                                db.session.add(detection_log)
                                db.session.commit()
                                
                                detection_log_id = detection_log.id
                                print(f"✓ Detection logged to database: {event['model_name']}")
                                
                                # Self-Learning: Randomly sample for VLM verification
                                try:
                                    # Get camera to access frame
                                    camera = self.camera_pool.get_camera(event['camera_id'])
                                    if camera:
                                        frame = camera.get_last_frame()
                                        if frame is not None:
                                            self._sample_detection_for_learning(
                                                camera_id=event['camera_id'],
                                                model_name=event['model_name'],
                                                frame=frame,
                                                detection_log_id=detection_log_id,
                                                detection_data={
                                                    'confidence': event['confidence'],
                                                    'count': len(event.get('detection_data', []))
                                                }
                                            )
                                except Exception as learning_error:
                                    # Don't let learning errors break detection
                                    pass
                            except Exception as db_error:
                                print(f"Error saving detection to DB: {db_error}")
                                import traceback
                                traceback.print_exc()
                        
                        # Trigger alert with video clip
                        # Now running within app context if available
                        self.alert_manager.send_detection_alert(
                            event['camera_id'],
                            event['camera_name'],
                            event['model_name'],
                            event['confidence'],
                            event['detection_data'],
                            video_clip_path=event.get('video_clip_path')  # Attach video clip
                        )
                        
                    finally:
                        if context:
                            context.pop()
                else:
                    time.sleep(0.5)
            
            except Exception as e:
                print(f"Error processing detection queue: {str(e)}")
                time.sleep(1)
    
    def start(self):
        """Start the detection pipeline"""
        self.is_running = True
        
        # Start queue processing thread
        self.queue_thread = threading.Thread(
            target=self.process_detection_queue,
            daemon=True
        )
        self.queue_thread.start()
        
        self.logging_manager.log_system_event("PIPELINE_STARTED", "Detection pipeline is running")
    
    def stop(self):
        """Stop the detection pipeline"""
        self.is_running = False
        self.stop_global_detection()
        self.recorder_pool.stop_all_recordings()
        self.camera_pool.stop_all()
        
        self.logging_manager.log_system_event("PIPELINE_STOPPED", "Detection pipeline stopped")
    
    def get_status(self):
        """Get pipeline status"""
        return {
            'is_running': self.is_running,
            'global_detection_enabled': self.global_detection_enabled,
            'active_cameras': len(self.camera_pool.get_active_cameras()),
            'active_detections': len(self.active_detections),
            'loaded_models': self.multi_detector.get_loaded_models() if self.multi_detector else []
        }
