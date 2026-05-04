import time
import os
import logging
from datetime import datetime, timedelta
from collections import deque
import cv2
import threading
from concurrent.futures import ThreadPoolExecutor
from models import db, AnalysisLog

class ContinuousAnalysisManager:
    """
    Manages continuous VLM analysis state for multiple cameras.
    
    Logic:
    - Buffers frames for 5 seconds.
    - Checks motion status.
    - If motion detected (or within 5s timeout), triggers VLM analysis on a background thread.
    - Logs results to "logs/continuous_analysis.log" and DB.
    """
    def __init__(self, vlm_analyzer, flask_app, interval_seconds=5.0, motion_timeout=5.0):
        self.vlm_analyzer = vlm_analyzer
        self.flask_app = flask_app
        self.interval = interval_seconds
        self.timeout = motion_timeout
        self.logger = logging.getLogger(__name__)
        
        # Thread pool for background analysis (max 2 workers to prevent overload)
        self.executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="VLM_Continuous")
        
        # State tracking per camera
        # { camera_id: { 
        #     'last_analysis_time': timestamp, 
        #     'last_motion_time': timestamp,
        #     'frame_buffer': deque(),   # Stores (timestamp, frame) tuples
        #     'is_active': bool,         # True if motion recently detected
        #     'analyzing': bool          # True if currently running an analysis task
        #   }
        # }
        self.camera_states = {}
        self.lock = threading.Lock()
        
        # Ensure log directory exists
        self.log_file = os.path.join("logs", "continuous_analysis.log")
        os.makedirs("logs", exist_ok=True)
        
        print(f"✓ Continuous Analysis initialized (Interval: {self.interval}s, Motion Timeout: {self.timeout}s)")
    
    def get_state(self, camera_id):
        with self.lock:
            if camera_id not in self.camera_states:
                self.camera_states[camera_id] = {
                    'last_analysis_time': 0,
                    'last_motion_time': 0,
                    'frame_buffer': deque(), 
                    'is_active': False,
                    'analyzing': False
                }
            return self.camera_states[camera_id]

    def process_frame(self, camera_id, frame, motion_detected):
        """
        Process a frame for continuous analysis.
        Should be called for every processed frame in the pipeline.
        """
        if not self.vlm_analyzer or not self.vlm_analyzer.is_available():
            return

        current_time = time.time()
        state = self.get_state(camera_id)
        
        # Update motion timestamp
        if motion_detected:
            state['last_motion_time'] = current_time
            state['is_active'] = True
        
        # Check timeout (stop buffering if no motion for `timeout` seconds)
        if current_time - state['last_motion_time'] > self.timeout:
            state['is_active'] = False
            # Clear buffer if inactive to save memory and avoid stale context
            if len(state['frame_buffer']) > 0:
                print(f"DEBUG: Camera {camera_id} inactive. Clearing buffer.")
                state['frame_buffer'].clear()
            return
        
        # If active, accumulate frames
        if state['is_active']:
            # Append (time, frame_copy)
            # Resize frame to reduce memory usage (e.g., 640 width)
            h, w = frame.shape[:2]
            scale = 640 / w if w > 640 else 1.0
            if scale < 1.0:
                small_frame = cv2.resize(frame, (0, 0), fx=scale, fy=scale)
            else:
                small_frame = frame.copy()
                
            state['frame_buffer'].append((current_time, small_frame))
            
            # Remove frames older than interval (sliding window or accumulation?)
            # Requirement: "passing clips of 5 secs continuously"
            # We will accumulate until we span 5 seconds, then flush and analyze.
            
            # Check if we have enough duration in buffer
            if len(state['frame_buffer']) > 2:
                start_time = state['frame_buffer'][0][0]
                duration = current_time - start_time
                
                # If we hit the interval and not currently analyzing
                if duration >= self.interval:
                    if not state['analyzing']:
                        # Extract frames and trigger analysis
                        frames_to_process = list(state['frame_buffer'])
                        state['frame_buffer'].clear() # Clear buffer for next batch
                        
                        # Mark as analyzing
                        state['analyzing'] = True
                        state['last_analysis_time'] = current_time
                        
                        # Submit to thread pool
                        self.executor.submit(self._run_analysis_task, camera_id, frames_to_process)
                    else:
                        # If already analyzing, we might skip this batch or just clear to catch up
                        # For continuous "log", skipping is better than lagging.
                        # But user said "continuously", so maybe we should just overlap?
                        # Let's drop this batch if busy to prevent queue buildup.
                        # print(f"DEBUG: Camera {camera_id} busy analyzing. Skipping batch.")
                        state['frame_buffer'].clear()
    
    def _run_analysis_task(self, camera_id, time_frame_pairs):
        """
        Background task to clean frames, run VLM, and log results.
        Inside ThreadPool.
        """
        try:
            if not time_frame_pairs:
                return

            # Select keyframes (e.g., 2 frames instead of 5 to reduce VLM load)
            num_frames = len(time_frame_pairs)
            if num_frames > 2:
                indices = [0, num_frames - 1] # Start and end frames
                selected_pairs = [time_frame_pairs[i] for i in indices]
            else:
                selected_pairs = time_frame_pairs
            
            frames = [p[1] for p in selected_pairs]
            
            # Save temporary files
            frame_paths = []
            timestamp_str = datetime.now().strftime('%H%M%S_%f')
            
            for i, frame in enumerate(frames):
                path = os.path.join(self.vlm_analyzer.cache_dir, f"cont_{camera_id}_{timestamp_str}_{i}.jpg")
                cv2.imwrite(path, frame)
                frame_paths.append(path)
            
            # Construct Prompt - STRICT OBSERVATION ONLY (Anti-Hallucination)
            # These prompts ensure VLM only describes what's directly visible
            system_prompt = (
                f"You are CEMSS monitoring Camera {camera_id}. "
                "STRICT RULES: "
                "1) ONLY describe what you can DIRECTLY SEE. "
                "2) NEVER speculate or assume. "
                "3) Do NOT use 'appears', 'seems', 'might be', 'possibly'. "
                "4) Count visible people. State positions and movements. "
                "5) Note visible objects and clothing colors. "
                "6) One concise sentence only. English only."
            )
            
            question = (
                "Describe ONLY what is directly visible: "
                "count of people, their positions, movements, and visible objects. "
                "No speculation or assumptions."
            )
            
            # Run Analysis (Non-blocking attempt)
            with self.flask_app.app_context():
                # Use try_analyze_frame to skip if VLM is busy with user request
                result = self.vlm_analyzer.try_analyze_frame(
                    frame_path=frame_paths,
                    question=question,
                    context=f"Continuous monitoring Camera {camera_id}",
                    system_prompt=system_prompt
                )
                
                if result.get('success'):
                    summary = result.get('response', 'No summary.')
                    self._log_analysis(camera_id, summary)
                elif result.get('error') == 'VLM busy':
                    self.logger.info(f"Skipping background analysis for Camera {camera_id} - VLM is busy")
                else:
                    self.logger.warning(f"Continuous VLM failed: {result.get('error')}")

        except Exception as e:
            self.logger.error(f"Error in continuous VLM task: {e}")
        finally:
            # Mark analysis as done
            with self.lock:
                if camera_id in self.camera_states:
                    self.camera_states[camera_id]['analyzing'] = False

    def _log_analysis(self, camera_id, summary):
        """Log analysis result to file and database"""
        timestamp = datetime.now()
        log_entry = f"[{timestamp.strftime('%Y-%m-%d %H:%M:%S')}] CAM_{camera_id}: {summary}"
        
        # File Logging
        try:
            with open(self.log_file, "a", encoding='utf-8') as f:
                f.write(log_entry + "\n")
        except Exception as e:
            self.logger.error(f"Failed to write to log file: {e}")
            
        # Database Logging
        try:
            # Note: AnalysisLog model might need to be imported inside function if circular import issues
            # But we imported at top, so it should be fine.
            log = AnalysisLog(
                camera_id=camera_id,
                timestamp=timestamp,
                summary=summary,
                motion_detected=True
            )
            db.session.add(log)
            db.session.commit()
            print(f"CONTINUOUS LOG: {log_entry}") # Console feedback
        except Exception as e:
            self.logger.error(f"Failed to save analysis to DB: {e}")
            db.session.rollback()
