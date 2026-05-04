"""
Extract frames from violence detection videos for YOLO classification training
"""
import cv2
from pathlib import Path
from tqdm import tqdm

BASE_DIR = Path(__file__).parent
VIDEO_DIR = BASE_DIR / 'models' / 'violence_detection' / 'prepared_github'
OUTPUT_DIR = BASE_DIR / 'models' / 'violence_detection' / 'prepared_frames'

# Extract every Nth frame to avoid too many similar frames
FRAME_SKIP = 15  # Extract 1 frame every 15 frames (for 30fps video = 2 frames/sec)

def extract_frames(video_path, output_dir, max_frames=10):
    """Extract frames from a video"""
    cap = cv2.VideoCapture(str(video_path))
    frame_count = 0
    saved_count = 0
    
    while saved_count < max_frames:
        ret, frame = cap.read()
        if not ret:
            break
            
        if frame_count % FRAME_SKIP == 0:
            output_path = output_dir / f"{video_path.stem}_frame{saved_count:03d}.jpg"
            cv2.imwrite(str(output_path), frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
            saved_count += 1
            
        frame_count += 1
    
    cap.release()
    return saved_count

def process_dataset():
    """Process all videos and extract frames"""
    print("\n" + "="*70)
    print("EXTRACTING FRAMES FROM VIDEOS")
    print("="*70)
    
    total_frames = 0
    
    for split in ['train', 'val', 'test']:
        for class_name in ['Violence', 'NonViolence']:
            video_dir = VIDEO_DIR / split / class_name
            output_dir = OUTPUT_DIR / split / class_name
            output_dir.mkdir(parents=True, exist_ok=True)
            
            videos = list(video_dir.glob('*.mp4'))
            print(f"\n{split}/{class_name}: {len(videos)} videos")
            
            frames_extracted = 0
            for video in tqdm(videos, desc=f"Processing {split}/{class_name}"):
                count = extract_frames(video, output_dir, max_frames=10)
                frames_extracted += count
            
            print(f"  Extracted {frames_extracted} frames")
            total_frames += frames_extracted
    
    # Create dataset.yaml
    import yaml
    dataset_yaml = {
        'path': str(OUTPUT_DIR.absolute()),
        'train': 'train',
        'val': 'val',
        'test': 'test',   
        'names': {
            0: 'NonViolence',
            1: 'Violence'
        },
        'nc': 2
    }
    
    yaml_path = OUTPUT_DIR / 'dataset.yaml'
    with open(yaml_path, 'w') as f:
        yaml.dump(dataset_yaml, f, default_flow_style=False)
    
    print("\n" + "="*70)
    print("FRAME EXTRACTION COMPLETE")
    print("="*70)
    print(f"Total frames extracted: {total_frames}")
    print(f"Dataset ready: {OUTPUT_DIR}")
    print(f"Config file: {yaml_path}")
    print("="*70 + "\n")

if __name__ == "__main__":
    process_dataset()
