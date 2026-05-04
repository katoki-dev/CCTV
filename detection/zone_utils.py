"""
CEMSS - Campus Event management and Surveillance System
Zone Intersection Utilities
"""
import json


def point_in_polygon(point, polygon):
    """
    Check if a point is inside a polygon using ray casting algorithm
    
    Args:
        point: Tuple (x, y)
        polygon: List of [x, y] coordinates defining the polygon
    
    Returns:
        bool: True if point is inside polygon
    """
    x, y = point
    n = len(polygon)
    inside = False
    
    p1x, p1y = polygon[0]
    for i in range(1, n + 1):
        p2x, p2y = polygon[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y
    
    return inside


def bbox_center(bbox):
    """
    Calculate center point of a bounding box
    
    Args:
        bbox: Dictionary with keys 'x1', 'y1', 'x2', 'y2' or list [x1, y1, x2, y2]
    
    Returns:
        tuple: (center_x, center_y)
    """
    if isinstance(bbox, dict):
        x1, y1, x2, y2 = bbox['x1'], bbox['y1'], bbox['x2'], bbox['y2']
    else:
        x1, y1, x2, y2 = bbox
    
    center_x = (x1 + x2) / 2
    center_y = (y1 + y2) / 2
    return (center_x, center_y)


def check_detection_in_zones(detection, zones, frame_width=None, frame_height=None):
    """
    Check if a detection bounding box intersects with any restricted zone
    
    Args:
        detection: Detection dictionary with 'bbox' key (in pixel coordinates)
        zones: List of zone dictionaries with 'coordinates' (normalized 0-1) and 'enabled' keys
        frame_width: Video frame width (required for normalization)
        frame_height: Video frame height (required for normalization)
    
    Returns:
        dict: {'in_zone': bool, 'zone_name': str or None}
    """
    if not zones:
        return {'in_zone': False, 'zone_name': None}
    
    # Get detection bounding box center
    bbox = detection.get('bbox', detection)
    center = bbox_center(bbox)
    
    # Normalize center point if frame dimensions provided
    # Zone coordinates are stored as normalized (0-1), so we need to normalize detection too
    if frame_width and frame_height:
        center = (center[0] / frame_width, center[1] / frame_height)
    
    # Check each enabled zone
    for zone in zones:
        if not zone.get('enabled', True):
            continue
        
        coordinates = zone.get('coordinates', [])
        if len(coordinates) < 3:  # Need at least 3 points for a polygon
            continue
        
        if point_in_polygon(center, coordinates):
            return {
                'in_zone': True,
                'zone_name': zone.get('name', 'Unknown Zone'),
                'zone_id': zone.get('id')
            }
    
    return {'in_zone': False, 'zone_name': None}


def normalize_coordinates(coordinates, frame_width, frame_height):
    """
    Normalize pixel coordinates to 0-1 range for resolution independence
    
    Args:
        coordinates: List of [x, y] pixel coordinates
        frame_width: Video frame width
        frame_height: Video frame height
    
    Returns:
        list: Normalized coordinates
    """
    return [[x / frame_width, y / frame_height] for x, y in coordinates]


def denormalize_coordinates(coordinates, frame_width, frame_height):
    """
    Convert normalized coordinates back to pixel coordinates
    
    Args:
        coordinates: List of [x, y] normalized (0-1) coordinates
        frame_width: Video frame width
        frame_height: Video frame height
    
    Returns:
        list: Pixel coordinates
    """
    return [[x * frame_width, y * frame_height] for x, y in coordinates]
