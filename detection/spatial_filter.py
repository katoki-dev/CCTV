"""
CEMSS - Spatial Filtering Utilities
Prevents false positives by filtering conflicting detections
"""
import numpy as np
from typing import List, Dict, Tuple, Any


def calculate_iou(box1: List[int], box2: List[int]) -> float:
    """
    Calculate Intersection over Union (IoU) between two bounding boxes
    
    Args:
        box1: Bounding box [x1, y1, x2, y2]
        box2: Bounding box [x1, y1, x2, y2]
        
    Returns:
        float: IoU value between 0 and 1
    """
    # Extract coordinates
    x1_1, y1_1, x2_1, y2_1 = box1
    x1_2, y1_2, x2_2, y2_2 = box2
    
    # Calculate intersection area
    x1_i = max(x1_1, x1_2)
    y1_i = max(y1_1, y1_2)
    x2_i = min(x2_1, x2_2)
    y2_i = min(y2_1, y2_2)
    
    if x2_i < x1_i or y2_i < y1_i:
        return 0.0
    
    intersection_area = (x2_i - x1_i) * (y2_i - y1_i)
    
    # Calculate union area
    box1_area = (x2_1 - x1_1) * (y2_1 - y1_1)
    box2_area = (x2_2 - x1_2) * (y2_2 - y1_2)
    union_area = box1_area + box2_area - intersection_area
    
    if union_area == 0:
        return 0.0
    
    return intersection_area / union_area


def get_head_region(person_bbox: List[int], head_ratio: float = 0.35) -> List[int]:
    """
    Extract head region from person bounding box
    
    Args:
        person_bbox: Person bounding box [x1, y1, x2, y2]
        head_ratio: Ratio of bbox height considered as head region (default 35%)
        
    Returns:
        List[int]: Head region bounding box [x1, y1, x2, y2]
    """
    x1, y1, x2, y2 = person_bbox
    height = y2 - y1
    
    # Head region is top portion of person bbox
    head_height = int(height * head_ratio)
    head_bbox = [x1, y1, x2, y1 + head_height]
    
    return head_bbox


def filter_phone_detections(
    person_detections: List[Dict[str, Any]],
    phone_detections: List[Dict[str, Any]],
    iou_threshold: float = 0.25,
    head_ratio: float = 0.35,
    min_distance: int = 30
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Filter phone detections that overlap with person head regions
    
    Args:
        person_detections: List of person detection dicts with 'bbox' key
        phone_detections: List of phone detection dicts with 'bbox' key
        iou_threshold: IoU threshold for filtering (default 0.25 = 25% overlap)
        head_ratio: Ratio of person height considered as head (default 0.35 = 35%)
        min_distance: Minimum pixel distance from face center (default 30 pixels)
        
    Returns:
        Tuple containing:
            - List of valid phone detections (not in head regions)
            - List of filtered phone detections (false positives)
    """
    if not person_detections or not phone_detections:
        return phone_detections, []
    
    valid_phones = []
    filtered_phones = []
    
    for phone in phone_detections:
        phone_bbox = phone.get('bbox')
        if not phone_bbox:
            valid_phones.append(phone)
            continue
        
        # Get phone center
        phone_center_x = (phone_bbox[0] + phone_bbox[2]) / 2
        phone_center_y = (phone_bbox[1] + phone_bbox[3]) / 2
        
        is_in_head_region = False
        filter_reason = None
        
        # Check against all person head regions
        for person in person_detections:
            person_bbox = person.get('bbox')
            if not person_bbox:
                continue
            
            # Get head region for this person
            head_bbox = get_head_region(person_bbox, head_ratio)
            
            # Get head center (approximate face location)
            head_center_x = (head_bbox[0] + head_bbox[2]) / 2
            head_center_y = (head_bbox[1] + head_bbox[3]) / 2
            
            # Calculate distance from phone center to face center
            distance = ((phone_center_x - head_center_x)**2 + (phone_center_y - head_center_y)**2)**0.5
            
            # Calculate IoU between phone and head region
            iou = calculate_iou(phone_bbox, head_bbox)
            
            # Filter if BOTH conditions are met:
            # 1. Significant overlap with head region (IoU)
            # 2. Phone center is very close to face center (distance)
            if iou >= iou_threshold and distance < min_distance:
                is_in_head_region = True
                filter_reason = f'face_overlap_iou={iou:.2f}_dist={distance:.0f}px'
                phone['filtered_reason'] = filter_reason
                phone['iou_with_head'] = iou
                phone['distance_from_face'] = distance
                break
        
        if is_in_head_region:
            filtered_phones.append(phone)
        else:
            valid_phones.append(phone)
    
    return valid_phones, filtered_phones


def calculate_overlap_ratio(small_box: List[int], large_box: List[int]) -> float:
    """
    Calculate what percentage of small_box is overlapped by large_box
    
    Args:
        small_box: Smaller bounding box [x1, y1, x2, y2]
        large_box: Larger bounding box [x1, y1, x2, y2]
        
    Returns:
        float: Overlap ratio (0 to 1)
    """
    x1_1, y1_1, x2_1, y2_1 = small_box
    x1_2, y1_2, x2_2, y2_2 = large_box
    
    # Calculate intersection
    x1_i = max(x1_1, x1_2)
    y1_i = max(y1_1, y1_2)
    x2_i = min(x2_1, x2_2)
    y2_i = min(y2_1, y2_2)
    
    if x2_i < x1_i or y2_i < y1_i:
        return 0.0
    
    intersection_area = (x2_i - x1_i) * (y2_i - y1_i)
    small_box_area = (x2_1 - x1_1) * (y2_1 - y1_1)
    
    if small_box_area == 0:
        return 0.0
    
    return intersection_area / small_box_area
