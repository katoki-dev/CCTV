"""
CEMSS - Campus Event management and Surveillance System
Video Recorder Module
"""
import cv2
import threading
import time
from datetime import datetime
from pathlib import Path
from collections import deque
from config import (
    VIDEOS_DIR, VIDEO_CLIP_DURATION, VIDEO_CODEC, 
    VIDEO_FPS, PRE_DETECTION_BUFFER_SECONDS
)


class VideoRecorder:
    """Records video clips and full recordings"""
    
    def __init__(self, camera_id, camera_name, fps=VIDEO_FPS):
        """
        Initialize video recorder
        
        Args:
            camera_id: Database ID of the camera
            camera_name: Display name for the camera
            fps: Frames per second for recording
        """
        self.camera_id = camera_id
        self.camera_name = camera_name
        self.fps = fps
        self.is_recording = False
        self.writer = None
        self.current_file = None
        self.lock = threading.Lock()
        
        # Circular buffer for pre-detection frames
        buffer_size = int(PRE_DETECTION_BUFFER_SECONDS * fps)
        self.frame_buffer = deque(maxlen=buffer_size)
        
        # Ensure video directory exists
        VIDEOS_DIR.mkdir(exist_ok=True)
    
    def start_full_recording(self, frame_width, frame_height):
        """
        Start continuous recording
        
        Args:
            frame_width: Width of video frames
            frame_height: Height of video frames
        
        Returns:
            str: Path to the recording file
        """
        if self.is_recording:
            print(f"Camera {self.camera_name} is already recording")
            return self.current_file
        
        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{self.camera_name.replace(' ', '_')}_full_{timestamp}.avi"
        filepath = VIDEOS_DIR / filename
        
        # Create video writer
        fourcc = cv2.VideoWriter_fourcc(*VIDEO_CODEC)
        self.writer = cv2.VideoWriter(
            str(filepath),
            fourcc,
            self.fps,
            (frame_width, frame_height)
        )
        
        if not self.writer.isOpened():
            print(f"Failed to start recording for {self.camera_name}")
            return None
        
        self.is_recording = True
        self.current_file = str(filepath)
        print(f"✓ Started full recording for {self.camera_name}: {filename}")
        return self.current_file
    
    def stop_full_recording(self):
        """Stop continuous recording"""
        with self.lock:
            if not self.is_recording:
                return
            
            if self.writer:
                self.writer.release()
                self.writer = None
            
            print(f"✓ Stopped full recording for {self.camera_name}")
            file_path = self.current_file
            self.is_recording = False
            self.current_file = None
            return file_path
    
    def add_frame_to_buffer(self, frame):
        """
        Add a frame to the circular buffer (for pre-detection recording)
        
        Args:
            frame: OpenCV frame
        """
        with self.lock:
            self.frame_buffer.append(frame.copy())
    
    def write_frame(self, frame):
        """
        Write a frame to the active recording
        
        Args:
            frame: OpenCV frame
        """
        # Add to buffer for potential clip creation
        self.add_frame_to_buffer(frame)
        
        # Write to full recording if active
        if self.is_recording and self.writer:
            with self.lock:
                self.writer.write(frame)
    
    def create_clip(self, frames_after_detection, frame_width, frame_height, 
                   event_type="detection"):
        """
        Create a short video clip around a detection event
        
        Args:
            frames_after_detection: Additional frames to append after detection
            frame_width: Width of video frames
            frame_height: Height of video frames
            event_type: Type of event (detection, manual, etc.)
        
        Returns:
            str: Path to the clip file
        """
        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{self.camera_name.replace(' ', '_')}_{event_type}_{timestamp}.avi"
        filepath = VIDEOS_DIR / filename
        
        # Create video writer for clip
        fourcc = cv2.VideoWriter_fourcc(*VIDEO_CODEC)
        clip_writer = cv2.VideoWriter(
            str(filepath),
            fourcc,
            self.fps,
            (frame_width, frame_height)
        )
        
        if not clip_writer.isOpened():
            print(f"Failed to create clip for {self.camera_name}")
            return None
        
        # Write pre-detection frames from buffer
        frames_written = 0
        with self.lock:
            # Create a copy or iterate under lock
            buffer_frames = list(self.frame_buffer)
            
        for frame in buffer_frames:
            clip_writer.write(frame)
            frames_written += 1
        
        # Write post-detection frames
        for frame in frames_after_detection:
            clip_writer.write(frame)
            frames_written += 1
        
        clip_writer.release()
        
        print(f"✓ Created {VIDEO_CLIP_DURATION}s clip for {self.camera_name}: {filename} ({frames_written} frames)")
        return str(filepath)
    
    def save_recent_clip(self, duration=5):
        """
        Save the recent frames from buffer as a video clip
        
        Args:
            duration: Duration in seconds (limited by buffer size)
            
        Returns:
            str: Path to the clip file
        """
        # Calculate how many frames we need
        frames_needed = int(duration * self.fps)
        buffer_len = len(self.frame_buffer)
        
        if buffer_len == 0:
            return None
            
        # Get frames from buffer (it's a deque, so list() keeps order)
        with self.lock:
            all_frames = list(self.frame_buffer)
        
        # Take at most frames_needed, from the end
        frames_to_save = all_frames[-frames_needed:] if buffer_len > frames_needed else all_frames
        
        if not frames_to_save:
            return None
            
        # Use first frame to get dimensions
        h, w = frames_to_save[0].shape[:2]
        
        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{self.camera_name.replace(' ', '_')}_ondemand_{timestamp}.avi"
        filepath = VIDEOS_DIR / filename
        
        # Create writer
        fourcc = cv2.VideoWriter_fourcc(*VIDEO_CODEC)
        writer = cv2.VideoWriter(
            str(filepath),
            fourcc,
            self.fps,
            (w, h)
        )
        
        if not writer.isOpened():
            print(f"Failed to create on-demand clip for {self.camera_name}")
            return None
            
        # Write frames
        for frame in frames_to_save:
            writer.write(frame)
            
        writer.release()
        print(f"✓ Created on-demand clip for {self.camera_name}: {filename}")
        return str(filepath)
    
    def release(self):
        """Release all resources"""
        self.stop_full_recording()
        self.frame_buffer.clear()


class VideoRecorderPool:
    """Manages video recorders for multiple cameras"""
    
    def __init__(self):
        """Initialize recorder pool"""
        self.recorders = {}  # camera_id -> VideoRecorder
        self.lock = threading.Lock()
    
    def get_or_create_recorder(self, camera_id, camera_name):
        """Get existing recorder or create a new one"""
        with self.lock:
            if camera_id not in self.recorders:
                self.recorders[camera_id] = VideoRecorder(camera_id, camera_name)
            return self.recorders[camera_id]
    
    def remove_recorder(self, camera_id):
        """Remove and release a recorder"""
        with self.lock:
            if camera_id in self.recorders:
                self.recorders[camera_id].release()
                del self.recorders[camera_id]
    
    def stop_all_recordings(self):
        """Stop all active recordings"""
        with self.lock:
            for recorder in self.recorders.values():
                recorder.stop_full_recording()
    
    def release_all(self):
        """Release all recorders"""
        with self.lock:
            for recorder in self.recorders.values():
                recorder.release()
            self.recorders.clear()
