"""
CEMSS - OpenCV YOLO Detector Bridge
High-performance YOLOv8 inference using OpenCV DNN module (ONNX)
"""
import cv2
import numpy as np
from pathlib import Path

class OpenCVYOLODetector:
    """YOLOv8 detector implementation using OpenCV DNN"""
    
    def __init__(self, model_path, config_dict=None):
        """
        Initialize detector
        Args:
            model_path: Path to .onnx model file
            config_dict: Optional configuration (confidence, NMS thresholds)
        """
        self.model_path = Path(model_path)
        self.config = config_dict or {}
        self.conf_threshold = self.config.get('confidence_threshold', 0.5)
        self.nms_threshold = self.config.get('nms_threshold', 0.45)
        self.input_size = self.config.get('imgsz', 640)
        
        if not self.model_path.exists():
            raise FileNotFoundError(f"ONNX model not found: {self.model_path}")
            
        # Load the network
        self.net = cv2.dnn.readNetFromONNX(str(self.model_path))
        
        # Determine acceleration
        try:
            # Check for CUDA availability in OpenCV
            count = cv2.cuda.getCudaEnabledDeviceCount()
            if count > 0:
                self.net.setPreferableBackend(cv2.dnn.DNN_BACKEND_CUDA)
                self.net.setPreferableTarget(cv2.dnn.DNN_TARGET_CUDA)
                print(f"✓ OpenCV YOLO Bridge: Using CUDA acceleration")
            else:
                self.net.setPreferableBackend(cv2.dnn.DNN_BACKEND_DEFAULT)
                self.net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)
                print(f"✓ OpenCV YOLO Bridge: Using CPU backend")
        except Exception:
            self.net.setPreferableBackend(cv2.dnn.DNN_BACKEND_DEFAULT)
            self.net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)
            print(f"✓ OpenCV YOLO Bridge: Falling back to CPU")

    def detect(self, frame):
        """
        Run inference on a frame
        Args:
            frame: BGR image
        Returns:
            list: List of detections {'bbox': [x1, y1, x2, y2], 'confidence': float, 'class_id': int}
        """
        [height, width, _] = frame.shape
        length = max(height, width)
        image = np.zeros((length, length, 3), np.uint8)
        image[0:height, 0:width] = frame
        
        scale = length / self.input_size
        
        blob = cv2.dnn.blobFromImage(image, 1/255, (self.input_size, self.input_size), [0,0,0], 1, crop=False)
        self.net.setInput(blob)
        outputs = self.net.forward()
        
        # YOLOv8 output: [1, 84, 8400] -> [84, 8400]
        outputs = np.array([cv2.transpose(outputs[0])])
        rows = outputs.shape[1]
        
        boxes = []
        confidences = []
        class_ids = []
        
        for i in range(rows):
            classes_scores = outputs[0][i][4:]
            (minScore, maxScore, minClassLoc, (x, maxClassIndex)) = cv2.minMaxLoc(classes_scores)
            
            if maxScore >= self.conf_threshold:
                box = [
                    outputs[0][i][0] - (0.5 * outputs[0][i][2]), 
                    outputs[0][i][1] - (0.5 * outputs[0][i][3]),
                    outputs[0][i][2], 
                    outputs[0][i][3]
                ]
                boxes.append(box)
                confidences.append(maxScore)
                class_ids.append(maxClassIndex)
        
        # Non-maximum suppression
        result_indices = cv2.dnn.NMSBoxes(boxes, confidences, self.conf_threshold, self.nms_threshold)
        
        detections = []
        for i in result_indices:
            box = boxes[i]
            x1 = int(box[0] * scale)
            y1 = int(box[1] * scale)
            x2 = int((box[0] + box[2]) * scale)
            y2 = int((box[1] + box[3]) * scale)
            
            # Clip to frame boundaries
            x1 = max(0, min(x1, width))
            y1 = max(0, min(y1, height))
            x2 = max(0, min(x2, width))
            y2 = max(0, min(y2, height))
            
            detections.append({
                'bbox': [x1, y1, x2, y2],
                'confidence': float(confidences[i]),
                'class_id': int(class_ids[i])
            })
            
        return detections

def generate_crowd_heatmap(frame, detections):
    """
    Generate a density heatmap based on detections
    Args:
        frame: Original frame
        detections: List of detection bboxes
    Returns:
        numpy.ndarray: Combined frame with heatmap overlay
    """
    if not detections:
        return frame
        
    height, width = frame.shape[:2]
    # Create low-res density map
    density_map = np.zeros((height // 8, width // 8), dtype=np.float32)
    
    for det in detections:
        x1, y1, x2, y2 = det['bbox']
        # Map to low-res coordinates
        cx = (x1 + x2) // 16
        cy = (y1 + y2) // 16
        
        if 0 <= cx < density_map.shape[1] and 0 <= cy < density_map.shape[0]:
            # Use Gaussian-like spread
            cv2.circle(density_map, (cx, cy), 2, (1.0), -1)
            
    # Smooth the map
    density_map = cv2.GaussianBlur(density_map, (15, 15), 0)
    
    # Normalize and colorize
    density_map_norm = cv2.normalize(density_map, None, 0, 255, cv2.NORM_MINMAX, cv2.CV_8U)
    heatmap = cv2.applyColorMap(density_map_norm, cv2.COLORMAP_JET)
    
    # Resize back to original
    heatmap = cv2.resize(heatmap, (width, height))
    
    # Blend with original frame
    overlay = cv2.addWeighted(frame, 0.7, heatmap, 0.3, 0)
    return overlay
