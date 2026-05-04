"""
CEMSS - Campus Event management and Surveillance System
Camera Manager Module
"""
import cv2
import threading
import time
from queue import Queue, Empty
from config import CAMERA_RECONNECT_ATTEMPTS, CAMERA_RECONNECT_DELAY


class CameraManager:
    """Manages OpenCV VideoCapture for a single camera"""
    
    def __init__(self, camera_id, source, name="Camera"):
        """
        Initialize camera manager
        
        Args:
            camera_id: Database ID of the camera
            source: Camera source (RTSP URL, device index, or file path)
            name: Display name for the camera
        """
        self.camera_id = camera_id
        self.source = source
        self.name = name
        self.capture = None
        self.is_running = False
        self.frame_queue = Queue(maxsize=2)  # Small buffer to prevent lag
        self.read_thread = None
        self.last_frame = None
        self.reconnect_attempts = 0
        self.lock = threading.Lock()
        
        # Try to parse source as integer (for device index)
        try:
            self.source = int(source)
        except ValueError:
            pass  # Keep as string (RTSP URL or file path)
        
        self._connect()
    
    def _connect(self):
        """Connect to the camera"""
        try:
            # On Windows, use CAP_DSHOW for local cameras to improve compatibility
            import platform
            if isinstance(self.source, int) and platform.system() == "Windows":
                self.capture = cv2.VideoCapture(self.source, cv2.CAP_DSHOW)
            else:
                self.capture = cv2.VideoCapture(self.source)
            
            # Set buffer size to 1 to reduce latency
            self.capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            
            if not self.capture.isOpened():
                raise Exception(f"Failed to open camera: {self.source}")
            
            print(f"✓ Connected to camera: {self.name} ({self.source})")
            self.reconnect_attempts = 0
            return True
        
        except Exception as e:
            print(f"✗ Failed to connect to {self.name}: {str(e)}")
            self.capture = None
            return False
    
    def start(self):
        """Start reading frames in a separate thread"""
        if self.is_running:
            return
        
        if self.capture is None or not self.capture.isOpened():
            if not self._connect():
                return False
        
        self.is_running = True
        self.read_thread = threading.Thread(target=self._read_frames, daemon=True)
        self.read_thread.start()
        print(f"✓ Started frame reading for {self.name}")
        return True
    
    def _read_frames(self):
        """Continuously read frames from the camera (runs in thread)"""
        while self.is_running:
            try:
                if self.capture is None or not self.capture.isOpened():
                    self._attempt_reconnect()
                    continue
                
                ret, frame = self.capture.read()
                
                if not ret:
                    # Check if this is a video file (not a camera/RTSP stream)
                    # Video files can be looped, whereas cameras need reconnection
                    is_video_file = isinstance(self.source, str) and (
                        self.source.endswith(('.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv'))
                    )
                    
                    if is_video_file:
                        # Loop video file back to the beginning
                        print(f"Video {self.name} reached end, looping...")
                        self.capture.set(cv2.CAP_PROP_POS_FRAMES, 0)
                        continue
                    else:
                        # For cameras/RTSP, attempt reconnect
                        print(f"✗ Failed to read frame from {self.name}, attempting reconnect...")
                        self._attempt_reconnect()
                        continue
                
                # Update last frame
                with self.lock:
                    self.last_frame = frame
                
                # Try to put in queue (non-blocking)
                try:
                    self.frame_queue.put_nowait(frame)
                except:
                    # Queue full, skip this frame
                    pass
                
                # Small sleep to prevent CPU overuse
                time.sleep(0.001)
            
            except Exception as e:
                print(f"Error reading from {self.name}: {str(e)}")
                time.sleep(1)
    
    def _attempt_reconnect(self):
        """Attempt to reconnect to the camera"""
        if self.reconnect_attempts >= CAMERA_RECONNECT_ATTEMPTS:
            print(f"✗ Max reconnect attempts reached for {self.name}")
            self.is_running = False
            return
        
        self.reconnect_attempts += 1
        print(f"Reconnecting to {self.name} (attempt {self.reconnect_attempts}/{CAMERA_RECONNECT_ATTEMPTS})...")
        
        # Release old capture
        if self.capture:
            self.capture.release()
        
        time.sleep(CAMERA_RECONNECT_DELAY)
        self._connect()
    
    def get_frame(self, timeout=1.0):
        """
        Get the latest frame from the queue
        
        Args:
            timeout: Maximum time to wait for a frame (seconds)
        
        Returns:
            frame: OpenCV frame, or None if unavailable
        """
        try:
            return self.frame_queue.get(timeout=timeout)
        except Empty:
            # Return last known frame if queue is empty
            with self.lock:
                return self.last_frame
    
    def get_last_frame(self):
        """Get the last captured frame (non-blocking)"""
        with self.lock:
            return self.last_frame
    
    def stop(self):
        """Stop the camera and release resources"""
        self.is_running = False
        
        if self.read_thread and self.read_thread.is_alive():
            self.read_thread.join(timeout=2)
        
        if self.capture:
            self.capture.release()
            self.capture = None
        
        print(f"✓ Stopped camera: {self.name}")
    
    def is_connected(self):
        """Check if camera is connected and running"""
        return self.is_running and self.capture is not None and self.capture.isOpened()
    
    def get_properties(self):
        """Get camera properties"""
        if self.capture and self.capture.isOpened():
            return {
                'width': int(self.capture.get(cv2.CAP_PROP_FRAME_WIDTH)),
                'height': int(self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                'fps': int(self.capture.get(cv2.CAP_PROP_FPS)),
                'codec': int(self.capture.get(cv2.CAP_PROP_FOURCC))
            }
        return None


class CameraPool:
    """Manages multiple cameras"""
    
    def __init__(self):
        """Initialize camera pool"""
        self.cameras = {}  # camera_id -> CameraManager
        self.lock = threading.Lock()
    
    def add_camera(self, camera_id, source, name="Camera"):
        """Add a camera to the pool"""
        with self.lock:
            if camera_id in self.cameras:
                print(f"Camera {camera_id} already exists, stopping old instance...")
                self.remove_camera(camera_id)
            
            camera = CameraManager(camera_id, source, name)
            self.cameras[camera_id] = camera
            return camera
    
    def remove_camera(self, camera_id):
        """Remove a camera from the pool"""
        with self.lock:
            if camera_id in self.cameras:
                self.cameras[camera_id].stop()
                del self.cameras[camera_id]
    
    def get_camera(self, camera_id):
        """Get a camera by ID"""
        return self.cameras.get(camera_id)
    
    def start_all(self):
        """Start all cameras"""
        with self.lock:
            for camera in self.cameras.values():
                camera.start()
    
    def stop_all(self):
        """Stop all cameras"""
        with self.lock:
            for camera in self.cameras.values():
                camera.stop()
    
    def get_active_cameras(self):
        """Get list of active camera IDs"""
        return [cid for cid, cam in self.cameras.items() if cam.is_connected()]
