"""
CASS - Input Validators
Validation utilities for user input and configuration
"""
import re
from pathlib import Path
from urllib.parse import urlparse


def validate_camera_source(source):
    """
    Validate camera source URL or device index
    
    Args:
        source: Camera source (RTSP URL, HTTP URL, or device index)
    
    Returns:
        tuple: (is_valid, error_message)
    """
    # Check if it's a device index (integer)
    try:
        device_idx = int(source)
        if device_idx < 0:
            return False, "Device index must be non-negative"
        return True, None
    except ValueError:
        pass
    
    # Check if it's a valid URL
    if isinstance(source, str):
        # RTSP URL pattern
        if source.startswith('rtsp://'):
            parsed = urlparse(source)
            if not parsed.netloc:
                return False, "Invalid RTSP URL format"
            return True, None
        
        # HTTP/HTTPS URL pattern (for IP cameras)
        if source.startswith(('http://', 'https://')):
            parsed = urlparse(source)
            if not parsed.netloc:
                return False, "Invalid HTTP URL format"
            return True, None
        
        # File path (for video files)
        path = Path(source)
        if path.exists():
            if path.suffix.lower() in ['.mp4', '.avi', '.mkv', '.mov', '.wmv']:
                return True, None
            return False, f"Unsupported video file format: {path.suffix}"
        
        return False, "Source must be a device index, RTSP URL, HTTP URL, or valid video file path"
    
    return False, "Invalid source format"


def validate_email(email):
    """
    Validate email address format
    
    Args:
        email: Email address string
    
    Returns:
        bool: True if valid, False otherwise
    """
    if not email:
        return False
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_username(username):
    """
    Validate username format
    
    Args:
        username: Username string
    
    Returns:
        tuple: (is_valid, error_message)
    """
    if not username:
        return False, "Username is required"
    
    if len(username) < 3:
        return False, "Username must be at least 3 characters"
    
    if len(username) > 80:
        return False, "Username must be at most 80 characters"
    
    # Only allow alphanumeric and underscore
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        return False, "Username can only contain letters, numbers, and underscores"
    
    return True, None


def validate_password(password):
    """
    Validate password strength
    
    Args:
        password: Password string
    
    Returns:
        tuple: (is_valid, error_message)
    """
    if not password:
        return False, "Password is required"
    
    if len(password) < 6:
        return False, "Password must be at least 6 characters"
    
    if len(password) > 128:
        return False, "Password must be at most 128 characters"
    
    # Optional: Add more strength requirements
    # has_upper = any(c.isupper() for c in password)
    # has_lower = any(c.islower() for c in password)
    # has_digit = any(c.isdigit() for c in password)
    
    return True, None


def validate_model_path(model_path):
    """
    Validate model file path
    
    Args:
        model_path: Path to model file
    
    Returns:
        tuple: (is_valid, error_message)
    """
    if not model_path:
        return False, "Model path is required"
    
    path = Path(model_path)
    
    # Check if file exists
    if not path.exists():
        return False, f"Model file not found: {model_path}"
    
    # Check if it's a file
    if not path.is_file():
        return False, f"Model path is not a file: {model_path}"
    
    # Check extension
    if path.suffix.lower() not in ['.pt', '.pth', '.onnx']:
        return False, f"Invalid model file format: {path.suffix} (expected .pt, .pth, or .onnx)"
    
    return True, None


def validate_zone_coordinates(coordinates):
    """
    Validate restricted zone coordinates
    
    Args:
        coordinates: List of [x, y] coordinate pairs
    
    Returns:
        tuple: (is_valid, error_message)
    """
    if not isinstance(coordinates, list):
        return False, "Coordinates must be a list"
    
    if len(coordinates) < 3:
        return False, "Zone must have at least 3 points"
    
    for i, point in enumerate(coordinates):
        if not isinstance(point, (list, tuple)) or len(point) != 2:
            return False, f"Point {i} must be an [x, y] coordinate pair"
        
        x, y = point
        if not isinstance(x, (int, float)) or not isinstance(y, (int, float)):
            return False, f"Point {i} coordinates must be numbers"
        
        if x < 0 or y < 0:
            return False, f"Point {i} coordinates must be non-negative"
    
    return True, None


def validate_confidence_threshold(threshold):
    """
    Validate confidence threshold value
    
    Args:
        threshold: Confidence threshold (0-1)
    
    Returns:
        tuple: (is_valid, error_message)
    """
    try:
        threshold = float(threshold)
        if threshold < 0 or threshold > 1:
            return False, "Confidence threshold must be between 0 and 1"
        return True, None
    except (ValueError, TypeError):
        return False, "Confidence threshold must be a number"


def sanitize_filename(filename):
    """
    Sanitize filename to prevent directory traversal and invalid characters
    
    Args:
        filename: Original filename
    
    Returns:
        str: Sanitized filename
    """
    # Remove path components
    filename = Path(filename).name
    
    # Remove or replace invalid characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # Limit length
    if len(filename) > 255:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        if ext:
            filename = name[:250] + '.' + ext
        else:
            filename = filename[:255]
    
    return filename
