"""
CEMSS - Campus Event management and Surveillance System
Video Overlay Utility Module

Provides functions to add overlays (timestamps, text, etc.) to video frames.
"""
import cv2
from datetime import datetime


def add_timestamp_overlay(frame, camera_name=None, position='top-right', 
                          timestamp_format="%Y-%m-%d %H:%M:%S",
                          font_scale=0.6, text_color=(255, 255, 255), 
                          bg_color=(0, 0, 0), bg_alpha=0.7):
    """
    Add timestamp overlay to a video frame
    
    Args:
        frame: OpenCV frame (numpy array)
        camera_name: Optional camera name to display
        position: Position of overlay ('top-left', 'top-right', 'bottom-left', 'bottom-right')
        timestamp_format: strftime format string for timestamp
        font_scale: Font size scale factor
        text_color: RGB tuple for text color (default: white)
        bg_color: RGB tuple for background box (default: black)
        bg_alpha: Background transparency (0.0 - 1.0, default: 0.7)
    
    Returns:
        Modified frame with timestamp overlay
    """
    if frame is None:
        return None
    
    # Get current timestamp
    current_time = datetime.now().strftime(timestamp_format)
    
    # Build overlay text
    if camera_name:
        overlay_text = f"{camera_name} | {current_time}"
    else:
        overlay_text = current_time
    
    # Font settings
    font = cv2.FONT_HERSHEY_SIMPLEX
    thickness = 2
    
    # Get text size
    (text_width, text_height), baseline = cv2.getTextSize(
        overlay_text, font, font_scale, thickness
    )
    
    # Calculate position
    frame_height, frame_width = frame.shape[:2]
    padding = 10
    
    if position == 'top-left':
        x = padding
        y = padding + text_height
    elif position == 'top-right':
        x = frame_width - text_width - padding
        y = padding + text_height
    elif position == 'bottom-left':
        x = padding
        y = frame_height - padding
    elif position == 'bottom-right':
        x = frame_width - text_width - padding
        y = frame_height - padding
    else:
        # Default to top-right
        x = frame_width - text_width - padding
        y = padding + text_height
    
    # Draw semi-transparent background box
    box_coords = (
        (x - 5, y - text_height - 5),
        (x + text_width + 5, y + baseline + 5)
    )
    
    # Create overlay for transparency effect
    overlay = frame.copy()
    cv2.rectangle(overlay, box_coords[0], box_coords[1], bg_color, -1)
    
    # Blend overlay with original frame
    cv2.addWeighted(overlay, bg_alpha, frame, 1 - bg_alpha, 0, frame)
    
    # Draw text on top
    cv2.putText(
        frame, 
        overlay_text, 
        (x, y),
        font,
        font_scale,
        text_color,
        thickness,
        lineType=cv2.LINE_AA
    )
    
    return frame


def add_custom_text_overlay(frame, text, position='bottom-left',
                            font_scale=0.8, text_color=(0, 255, 0),
                            bg_color=(0, 0, 0), bg_alpha=0.7):
    """
    Add custom text overlay to a video frame
    
    Args:
        frame: OpenCV frame (numpy array)
        text: Text to display
        position: Position of overlay ('top-left', 'top-right', 'bottom-left', 'bottom-right')
        font_scale: Font size scale factor
        text_color: RGB tuple for text color
        bg_color: RGB tuple for background box
        bg_alpha: Background transparency (0.0 - 1.0)
    
    Returns:
        Modified frame with text overlay
    """
    if frame is None or not text:
        return frame
    
    # Font settings
    font = cv2.FONT_HERSHEY_SIMPLEX
    thickness = 2
    
    # Get text size
    (text_width, text_height), baseline = cv2.getTextSize(
        text, font, font_scale, thickness
    )
    
    # Calculate position
    frame_height, frame_width = frame.shape[:2]
    padding = 10
    
    if position == 'top-left':
        x = padding
        y = padding + text_height
    elif position == 'top-right':
        x = frame_width - text_width - padding
        y = padding + text_height
    elif position == 'bottom-left':
        x = padding
        y = frame_height - padding
    elif position == 'bottom-right':
        x = frame_width - text_width - padding
        y = frame_height - padding
    else:
        x = padding
        y = frame_height - padding
    
    # Draw semi-transparent background box
    box_coords = (
        (x - 5, y - text_height - 5),
        (x + text_width + 5, y + baseline + 5)
    )
    
    # Create overlay for transparency effect
    overlay = frame.copy()
    cv2.rectangle(overlay, box_coords[0], box_coords[1], bg_color, -1)
    
    # Blend overlay with original frame
    cv2.addWeighted(overlay, bg_alpha, frame, 1 - bg_alpha, 0, frame)
    
    # Draw text
    cv2.putText(
        frame,
        text,
        (x, y),
        font,
        font_scale,
        text_color,
        thickness,
        lineType=cv2.LINE_AA
    )
    
    return frame


def draw_sleek_bounding_box(frame, bbox, label, color=(0, 255, 0), thickness=2):
    """
    Draw a premium-looking bounding box with corner highlights and a label
    """
    x1, y1, x2, y2 = bbox
    
    # 1. Draw subtle main rectangle (semi-transparent)
    overlay = frame.copy()
    cv2.rectangle(overlay, (x1, y1), (x2, y2), color, thickness)
    cv2.addWeighted(overlay, 0.4, frame, 0.6, 0, frame)
    
    # 2. Draw corner highlights (solid)
    length = min(20, (x2 - x1) // 4, (y2 - y1) // 4)
    
    # Top-Left
    cv2.line(frame, (x1, y1), (x1 + length, y1), color, thickness + 1)
    cv2.line(frame, (x1, y1), (x1, y1 + length), color, thickness + 1)
    
    # Top-Right
    cv2.line(frame, (x2, y1), (x2 - length, y1), color, thickness + 1)
    cv2.line(frame, (x2, y1), (x2, y1 + length), color, thickness + 1)
    
    # Bottom-Left
    cv2.line(frame, (x1, y2), (x1 + length, y2), color, thickness + 1)
    cv2.line(frame, (x1, y2), (x1, y2 - length), color, thickness + 1)
    
    # Bottom-Right
    cv2.line(frame, (x2, y2), (x2 - length, y2), color, thickness + 1)
    cv2.line(frame, (x2, y2), (x2, y2 - length), color, thickness + 1)
    
    # 3. Draw label with background
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.5
    (w, h), baseline = cv2.getTextSize(label, font, font_scale, 1)
    
    # Label background (top-left of box)
    cv2.rectangle(frame, (x1, y1 - h - 10), (x1 + w + 10, y1), color, -1)
    # Label text
    cv2.putText(frame, label, (x1 + 5, y1 - 5), font, font_scale, (0, 0, 0), 1, cv2.LINE_AA)
    
    return frame
