"""
Organize GitHub violence detection dataset for YOLO classification training
Dataset: 350 videos (230 violent, 120 non-violent) from two cameras
"""

import shutil
from pathlib import Path
import random

BASE_DIR = Path(__file__).parent
DATASET_DIR = BASE_DIR / 'models' / 'violence_detection' / 'github_dataset' / 'violence-detection-dataset'
OUTPUT_DIR = BASE_DIR / 'models' / 'violence_detection' / 'prepared_github'

# Train/Val/Test split ratios
TRAIN_RATIO = 0.7
VAL_RATIO = 0.15
TEST_RATIO = 0.15

def organize_dataset():
    """
    Organize videos into YOLO classification format:
    - train/Violence and train/NonViolence
    - val/Violence and val/NonViolence  
    - test/Violence and test/NonViolence
    """
    print("\n" + "="*70)
    print("GITHUB VIOLENCE DETECTION DATASET PREPARATION")
    print("="*70)
    
    # Create output structure
    for split in ['train', 'val', 'test']:
        for label in ['Violence', 'NonViolence']:
            (OUTPUT_DIR / split / label).mkdir(parents=True, exist_ok=True)
    
    # Process violent videos
    print("\nProcessing Violent videos...")
    violent_videos = []
    for cam in ['cam1', 'cam2']:
        cam_dir = DATASET_DIR / 'violent' / cam
        violent_videos.extend(list(cam_dir.glob('*.mp4')))
    
    print(f"Found {len(violent_videos)} violent videos")
    
    # Shuffle and split
    random.shuffle(violent_videos)
    n_violent = len(violent_videos)
    n_train = int(n_violent * TRAIN_RATIO)
    n_val = int(n_violent * VAL_RATIO)
    
    train_violent = violent_videos[:n_train]
    val_violent = violent_videos[n_train:n_train+n_val]
    test_violent = violent_videos[n_train+n_val:]
    
    # Copy to output
    for idx, video in enumerate(train_violent):
        dest = OUTPUT_DIR / 'train' / 'Violence' / f"violent_{idx:03d}.mp4"
        shutil.copy2(video, dest)
    
    for idx, video in enumerate(val_violent):
        dest = OUTPUT_DIR / 'val' / 'Violence' / f"violent_{idx:03d}.mp4"
        shutil.copy2(video, dest)
    
    for idx, video in enumerate(test_violent):
        dest = OUTPUT_DIR / 'test' / 'Violence' / f"violent_{idx:03d}.mp4"
        shutil.copy2(video, dest)
    
    print(f"  Train: {len(train_violent)}")
    print(f"  Val: {len(val_violent)}")
    print(f"  Test: {len(test_violent)}")
    
    # Process non-violent videos
    print("\nProcessing Non-Violent videos...")
    nonviolent_videos = []
    for cam in ['cam1', 'cam2']:
        cam_dir = DATASET_DIR / 'non-violent' / cam
        nonviolent_videos.extend(list(cam_dir.glob('*.mp4')))
    
    print(f"Found {len(nonviolent_videos)} non-violent videos")
    
    # Shuffle and split
    random.shuffle(nonviolent_videos)
    n_nonviolent = len(nonviolent_videos)
    n_train = int(n_nonviolent * TRAIN_RATIO)
    n_val = int(n_nonviolent * VAL_RATIO)
    
    train_nonviolent = nonviolent_videos[:n_train]
    val_nonviolent = nonviolent_videos[n_train:n_train+n_val]
    test_nonviolent = nonviolent_videos[n_train+n_val:]
    
    # Copy to output
    for idx, video in enumerate(train_nonviolent):
        dest = OUTPUT_DIR / 'train' / 'NonViolence' / f"nonviolent_{idx:03d}.mp4"
        shutil.copy2(video, dest)
    
    for idx, video in enumerate(val_nonviolent):
        dest = OUTPUT_DIR / 'val' / 'NonViolence' / f"nonviolent_{idx:03d}.mp4"
        shutil.copy2(video, dest)
    
    for idx, video in enumerate(test_nonviolent):
        dest = OUTPUT_DIR / 'test' / 'NonViolence' / f"nonviolent_{idx:03d}.mp4"
        shutil.copy2(video, dest)
    
    print(f"  Train: {len(train_nonviolent)}")
    print(f"  Val: {len(val_nonviolent)}")
    print(f"  Test: {len(test_nonviolent)}")
    
    # Create dataset.yaml
    import yaml
    
    dataset_yaml = {
        'path': str(OUTPUT_DIR.absolute()),
        'train': 'train',
        'val': 'val',
        'test': 'test',
        'names': ['NonViolence', 'Violence'],  # Class order
        'nc': 2
    }
    
    yaml_path = OUTPUT_DIR / 'dataset.yaml'
    with open(yaml_path, 'w') as f:
        yaml.dump(dataset_yaml, f, default_flow_style=False)
    
    # Summary
    print("\n" + "="*70)
    print("DATASET PREPARATION COMPLETE")
    print("="*70)
    print(f"\nTRAIN:")
    print(f"  Violence: {len(train_violent)}")
    print(f"  NonViolence: {len(train_nonviolent)}")
    print(f"  Total: {len(train_violent) + len(train_nonviolent)}")
    
    print(f"\nVAL:")
    print(f"  Violence: {len(val_violent)}")
    print(f"  NonViolence: {len(val_nonviolent)}")
    print(f"  Total: {len(val_violent) + len(val_nonviolent)}")
    
    print(f"\nTEST:")
    print(f"  Violence: {len(test_violent)}")
    print(f"  NonViolence: {len(test_nonviolent)}")
    print(f"  Total: {len(test_violent) + len(test_nonviolent)}")
    
    print(f"\n✓ Dataset ready for training!")
    print(f"✓ Config file: {yaml_path}")
    print(f"\nNext step: Run train_violence_detection.py")
    print("="*70 + "\n")

if __name__ == "__main__":
    random.seed(42)  # For reproducibility
    organize_dataset()
