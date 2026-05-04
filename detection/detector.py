"""
CEMSS - Campus Event management and Surveillance System
YOLO Detector Module
"""
import cv2
import numpy as np
from pathlib import Path
from ultralytics import YOLO
import torch
from config import (
    DETECTION_MODELS, YOLO_DEVICE, YOLO_IMG_SIZE, 
    YOLO_IOU_THRESHOLD, MODELS_DIR
)
from detection.video_overlay import draw_sleek_bounding_box


class YOLODetector:
    """YOLO-based object detection"""
    
    def __init__(self, model_name='person'):
        """
        Initialize YOLO detector
        
        Args:
            model_name: Name of the detection model (person, fall, phone, etc.)
        """
        self.model_name = model_name
        self.model_config = DETECTION_MODELS.get(model_name, {})
        self.confidence_threshold = self.model_config.get('confidence_threshold', 0.5)
        self.model = None
        self.device = YOLO_DEVICE
        
        # Load model
        self._load_model()
    
    def _load_model(self):
        """Load the YOLO model"""
        model_path = self.model_config.get('model_path')
        
        if not model_path:
            raise ValueError(f"No model path configured for '{self.model_name}'")
        
        model_path = Path(model_path)
        
        # If model doesn't exist, download default YOLOv8n for person detection
        if not model_path.exists() and self.model_name == 'person':
            print(f"Downloading default YOLOv8n model to {model_path}...")
            MODELS_DIR.mkdir(exist_ok=True)
            self.model = YOLO('yolov8n.pt')  # This will download the model
            self.model.save(str(model_path))
        elif not model_path.exists():
            raise FileNotFoundError(
                f"Model file not found: {model_path}\n"
                f"Please ensure the model exists or train it first."
            )
        else:
            self.model = YOLO(str(model_path))
        
        # Set device and optimize
        if torch.cuda.is_available() and self.device == '0':
            # Enable half precision (FP16) for GPU if configured
            from config import ENABLE_HALF_PRECISION, ENABLE_MODEL_WARMUP
            if ENABLE_HALF_PRECISION:
                try:
                    self.model.model.half()  # Convert model to FP16
                    self.use_half_precision = True
                    print(f"✓ {self.model_name} detector loaded on GPU with FP16")
                except Exception as e:
                    print(f"⚠️  Failed to enable FP16, using FP32: {e}")
                    self.use_half_precision = False
                    print(f"✓ {self.model_name} detector loaded on GPU")
            else:
                self.use_half_precision = False
                print(f"✓ {self.model_name} detector loaded on GPU")
            
            # Warmup model for better first inference performance
            if ENABLE_MODEL_WARMUP:
                self._warmup_model()
        else:
            self.device = 'cpu'
            self.use_half_precision = False
            print(f"✓ {self.model_name} detector loaded on CPU (slower)")
    
    def _warmup_model(self):
        """Warmup model with dummy inference to optimize first real inference"""
        try:
            import numpy as np
            from config import YOLO_IMG_SIZE
            
            # Create dummy frame
            dummy_frame = np.random.randint(0, 255, (YOLO_IMG_SIZE, YOLO_IMG_SIZE, 3), dtype=np.uint8)
            
            # Run a few warmup inferences
            print(f"  Warming up {self.model_name} model...")
            for _ in range(3):
                _ = self.model(dummy_frame, device=self.device, verbose=False)
            print(f"  ✓ Warmup complete")
        except Exception as e:
            print(f"  ⚠️  Warmup failed: {e}")
    
    def detect(self, frame, annotate=True):
        """
        Run detection on a frame
        
        Args:
            frame: OpenCV frame (BGR format)
            annotate: Whether to draw annotations on frame
        
        Returns:
            dict: Detection results with boxes, confidences, and classes
        """
        if self.model is None:
            return {'detections': [], 'frame': frame}
        
        try:
            # Run inference
            results = self.model(
                frame,
                device=self.device,
                conf=self.confidence_threshold,
                iou=YOLO_IOU_THRESHOLD,
                imgsz=YOLO_IMG_SIZE,
                verbose=False,
                half=getattr(self, 'use_half_precision', False)  # Use FP16 if available
            )
            
            detections = []
            annotated_frame = frame.copy() if annotate else frame
            
            # Parse results
            for result in results:
                # Handle classification results (e.g. violence detection)
                if hasattr(result, 'probs') and result.probs is not None:
                    probs = result.probs
                    class_id = int(probs.top1)
                    confidence = float(probs.top1conf)
                    class_name = result.names[class_id]
                    
                    # Only report if above threshold
                    if confidence >= self.confidence_threshold:
                        # For classification, we treat the whole frame as the "box"
                        h, w = frame.shape[:2]
                        detection = {
                            'bbox': [0, 0, w, h],
                            'confidence': confidence,
                            'class_id': class_id,
                            'class_name': class_name
                        }
                        detections.append(detection)
                        
                        if annotate:
                            # Use premium label for classification
                            color = (0, 0, 255) # Red for violence
                            label = f"ALERT: {class_name.upper()} {confidence:.2f}"
                            
                            # Draw prominent status bar at the top
                            h, w = frame.shape[:2]
                            cv2.rectangle(annotated_frame, (0, 0), (w, 50), color, -1)
                            cv2.putText(annotated_frame, label, (20, 35),
                                      cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2, cv2.LINE_AA)
                
                # Handle object detection results
                elif hasattr(result, 'boxes') and result.boxes is not None:
                    boxes = result.boxes
                    
                    for box in boxes:
                        # Get box coordinates
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                        confidence = float(box.conf[0])
                        class_id = int(box.cls[0])
                        
                        # Get class name
                        class_name = self.model.names[class_id] if hasattr(self.model, 'names') else str(class_id)
                        
                        # Normalize phone class names (YOLO may detect as 'cell phone' or 'phone')
                        if self.model_name == 'phone' and class_name.lower() in ['cell phone', 'cellphone', 'mobile', 'mobile phone']:
                            class_name = 'phone'
                        
                        detection = {
                            'bbox': [int(x1), int(y1), int(x2), int(y2)],
                            'confidence': confidence,
                            'class_id': class_id,
                            'class_name': class_name
                        }
                        detections.append(detection)
                        
                        # Draw on frame only if requested
                        if annotate:
                            # Use different colors for different types
                            color = (0, 255, 0) # Green for general
                            if self.model_name == 'person':
                                color = (255, 165, 0) # Orange for crowd
                            elif self.model_name == 'fall':
                                color = (0, 0, 255) # Red for fall
                            elif self.model_name == 'phone':
                                color = (255, 0, 255) # Magenta for phone
                            
                            label = f"{class_name.upper()} {confidence:.2f}"
                            annotated_frame = draw_sleek_bounding_box(
                                annotated_frame, [int(x1), int(y1), int(x2), int(y2)], 
                                label, color=color
                            )
            
            return {
                'detections': detections,
                'frame': annotated_frame,
                'detection_count': len(detections)
            }
        
        except Exception as e:
            print(f"Error during detection with model '{self.model_name}': {str(e)}")
            return {'detections': [], 'frame': frame, 'detection_count': 0}
    
    def is_enabled(self):
        """Check if this model is enabled in config"""
        return self.model_config.get('enabled', False)
    
    def get_description(self):
        """Get model description"""
        return self.model_config.get('description', self.model_name)


class MultiModelDetector:
    """Manages multiple YOLO detection models with enhanced fall detection"""
    
    def __init__(self, enabled_models=None):
        """
        Initialize multiple detection models
        
        Args:
            enabled_models: List of model names to enable, or None for all enabled in config
        """
        self.detectors = {}
        self.enhanced_fall_detector = None
        
        # Determine which models to load
        if enabled_models is None:
            enabled_models = [name for name, config in DETECTION_MODELS.items() 
                            if config.get('enabled', False)]
        
        # Load each model
        for model_name in enabled_models:
            try:
                print(f"Loading {model_name} detector...")
                self.detectors[model_name] = YOLODetector(model_name)
            except Exception as e:
                print(f"Failed to load {model_name} detector: {str(e)}")
        
        # Enhanced fall detector DISABLED - Using YOLO-only fall detection
        # Pose estimation removed per user request
        self.enhanced_fall_detector = None
        
        # Original enhanced fall detector code (disabled):
        # if 'fall' in enabled_models or 'fall' in self.detectors:
        #     try:
        #         from detection.pose_estimator import PoseEstimator
        #         from detection.enhanced_fall_detector import EnhancedFallDetector
        #         
        #         pose_estimator = PoseEstimator()
        #         fall_detector = self.detectors.get('fall')
        #         
        #         self.enhanced_fall_detector = EnhancedFallDetector(
        #             fall_detector=fall_detector,
        #             pose_estimator=pose_estimator
        #         )
        #         print("✓ Enhanced fall detection with pose estimation enabled")
        #     except Exception as e:
        #         print(f"⚠ Could not initialize enhanced fall detector: {e}")
        #         print("  Falling back to standard YOLO fall detection")
        
        print("ℹ Using YOLO-only fall detection (enhanced detector disabled)")
    
    def detect(self, frame, active_models=None, annotate=True):
        """
        Run detection with multiple models
        
        Args:
            frame: OpenCV frame
            active_models: List of model names to run, or None for all loaded
            annotate: Whether to draw annotations
        """
        if active_models is None:
            active_models = list(self.detectors.keys())
        
        all_results = {}
        annotated_frame = frame.copy() if annotate else frame
        
        for model_name in active_models:
            if model_name == 'fall' and self.enhanced_fall_detector:
                # Use enhanced fall detector for better accuracy
                result = self.enhanced_fall_detector.detect(frame, annotate=annotate)
                all_results[model_name] = result
                
                if annotate and result.get('detection_count', 0) > 0:
                    annotated_frame = result['frame']
            elif model_name in self.detectors:
                result = self.detectors[model_name].detect(frame, annotate=annotate)
                all_results[model_name] = result
                
                # Use the annotated frame from the last detector
                if annotate and result.get('detection_count', 0) > 0:
                    annotated_frame = result['frame']
        
        return {
            'results': all_results,
            'frame': annotated_frame
        }
    
    def get_loaded_models(self):
        """Get list of loaded model names"""
        return list(self.detectors.keys())
