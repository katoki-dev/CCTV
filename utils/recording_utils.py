"""
CASS - Recording Utility Functions
Helper functions for managing video recordings
"""
import os
from datetime import datetime
from config import RECORDING_BASE_DIR


def get_recording_path(camera_name, recording_type='continuous'):
    """
    Generate save path for a recording
    
    Args:
        camera_name: Name of the camera
        recording_type: 'detection' or 'continuous'
    
    Returns:
        Full directory path for saving the recording
    """
    # Sanitize camera name for filesystem
    safe_camera_name = "".join(c for c in camera_name if c.isalnum() or c in (' ', '_', '-')).strip()
    safe_camera_name = safe_camera_name.replace(' ', '_')
    
    # Build path: recordings/detection/camera_name or recordings/continuous/camera_name
    recording_dir = os.path.join(RECORDING_BASE_DIR, recording_type, safe_camera_name)
    
    return recording_dir


def ensure_recording_directory(path):
    """
    Create recording directory if it doesn't exist
    
    Args:
        path: Directory path to create
    
    Returns:
        True if successful, False otherwise
    """
    try:
        os.makedirs(path, exist_ok=True)
        return True
    except Exception as e:
        print(f"Error creating recording directory {path}: {e}")
        return False


def get_file_size(filepath):
    """
    Get file size in bytes
    
    Args:
        filepath: Path to the file
    
    Returns:
        File size in bytes, or None if file doesn't exist
    """
    try:
        if os.path.exists(filepath):
            return os.path.getsize(filepath)
        return None
    except Exception as e:
        print(f"Error getting file size for {filepath}: {e}")
        return None


def format_recording_filename(camera_name, recording_type='continuous', detection_model=None):
    """
    Generate standardized filename for recording
    
    Args:
        camera_name: Name of the camera
        recording_type: 'detection' or 'continuous'
        detection_model: Optional detection model name (e.g., 'fall', 'phone')
    
    Returns:
        Formatted filename (e.g., '2026-01-06_12-30-45_fall.mp4')
    """
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    
    if recording_type == 'detection' and detection_model:
        # Include detection type in filename
        filename = f"{timestamp}_{detection_model}.mp4"
    else:
        filename = f"{timestamp}.mp4"
    
    return filename


def format_file_size_display(size_bytes):
    """
    Format file size for display
    
    Args:
        size_bytes: Size in bytes
    
    Returns:
        Formatted string (e.g., '1.5 MB')
    """
    if size_bytes is None:
        return 'Unknown'
    
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    
    return f"{size_bytes:.1f} TB"


def format_duration_display(seconds):
    """
    Format duration for display
    
    Args:
        seconds: Duration in seconds
    
    Returns:
        Formatted string (e.g., '1:23' or '1:02:34')
    """
    if seconds is None:
        return '0:00'
    
    seconds = int(seconds)
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    
    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes}:{secs:02d}"


def get_relative_recording_path(full_path, recording_base_dir=None):
    """
    Convert absolute path to relative path from recordings base directory
    
    Args:
        full_path: Absolute path to recording file
        recording_base_dir: Base recordings directory (defaults to RECORDING_BASE_DIR)
    
    Returns:
        Relative path from recordings base
    """
    if recording_base_dir is None:
        recording_base_dir = RECORDING_BASE_DIR
    
    try:
        # Normalize paths
        full_path = os.path.normpath(full_path)
        recording_base_dir = os.path.normpath(recording_base_dir)
        
        # Get relative path
        rel_path = os.path.relpath(full_path, recording_base_dir)
        
        return rel_path
    except Exception as e:
        print(f"Error getting relative path: {e}")
        return full_path
