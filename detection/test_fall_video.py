import cv2
import sys
import os
from pathlib import Path
import time

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from detection.enhanced_fall_detector import create_enhanced_fall_detector

def test_video(video_path, output_path):
    print(f"Processing video: {video_path}")
    
    # Initialize detector
    try:
        detector = create_enhanced_fall_detector()
        print("Detector initialized successfully")
    except Exception as e:
        print(f"Failed to initialize detector: {e}")
        return

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Error: Could not open video {video_path}")
        return

    # Get video properties
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    
    # Create video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    frame_count = 0
    fall_count = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        frame_count += 1
        
        # Run detection
        start_time = time.time()
        result = detector.detect(frame)
        process_time = time.time() - start_time
        
        detections = result.get('detections', [])
        if detections:
            fall_count += 1
            print(f"Frame {frame_count}: Fall detected! ({len(detections)} occurrences)")
            for d in detections:
                print(f"  - Conf: {d['confidence']:.2f}, Source: {d.get('source', 'unknown')}")
        
        # Get annotated frame
        annotated_frame = result.get('frame', frame)
        
        # Write to output video
        out.write(annotated_frame)
        
        # Display progress every 30 frames
        if frame_count % 30 == 0:
            print(f"Processed {frame_count} frames. Recent process time: {process_time:.3f}s")

    cap.release()
    out.release()
    print(f"Processing complete.")
    print(f"Total frames: {frame_count}")
    print(f"Frames with falls: {fall_count}")
    print(f"Output saved to: {output_path}")

if __name__ == "__main__":
    video_path = r"c:\Users\anina\OneDrive\Desktop\Project\CEMSS\v11.1\video.mp4"
    output_path = r"c:\Users\anina\OneDrive\Desktop\Project\CEMSS\v11.1\video_output.mp4"
    
    if not os.path.exists(video_path):
        print(f"File not found: {video_path}")
    else:
        test_video(video_path, output_path)
