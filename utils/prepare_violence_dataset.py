"""
CASS - Violence Detection Dataset Preparation
Extracts and prepares RWF-2000 dataset for YOLO classification training
"""

import os
import json
import shutil
import subprocess
from pathlib import Path
import yaml

# Dataset paths
BASE_DIR = Path(__file__).parent.parent
VIOLENCE_DATASET_DIR = BASE_DIR / 'models' / 'violence_detection'
OUTPUT_DIR = BASE_DIR / 'models' / 'violence_detection' / 'prepared'

def extract_archives():
    """
    Extract RWF-2000 archives (.7z files)
    Requires 7-Zip to be installed
    """
    print("\n" + "="*60)
    print("EXTRACTING RWF-2000 ARCHIVES")
    print("="*60)
    
    archive_files = list(VIOLENCE_DATASET_DIR.glob('RWF-2000.7z.*'))
    
    if not archive_files:
        print("✓ No archives found - assuming already extracted")
        return True
    
    print(f"Found {len(archive_files)} archive parts")
    
    # Check if 7-Zip is available
    try:
        # Try common 7-Zip installation paths
        seven_zip_paths = [
            r"C:\Program Files\7-Zip\7z.exe",
            r"C:\Program Files (x86)\7-Zip\7z.exe",
            "7z"  # If in PATH
        ]
        
        seven_zip = None
        for path in seven_zip_paths:
            if os.path.exists(path) or path == "7z":
                seven_zip = path
                break
        
        if seven_zip is None:
            print("\n✗ 7-Zip not found!")
            print("Please install 7-Zip from: https://www.7-zip.org/")
            print("Or extract the archives manually and re-run this script.")
            return False
        
        # Extract the first archive (it will handle multi-part extraction)
        first_archive = VIOLENCE_DATASET_DIR / 'RWF-2000.7z.001'
        
        if not first_archive.exists():
            print(f"✗ First archive part not found: {first_archive}")
            return False
        
        print(f"\nExtracting {first_archive.name}...")
        print("This may take several minutes...")
        
        # Run 7-Zip extraction
        cmd = [seven_zip, 'x', str(first_archive), f'-o{VIOLENCE_DATASET_DIR}', '-y']
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✓ Extraction complete!")
            return True
        else:
            print(f"✗ Extraction failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"✗ Error during extraction: {e}")
        print("\nPlease extract the RWF-2000.7z archives manually:")
        print(f"  Location: {VIOLENCE_DATASET_DIR}")
        print("  Expected output: RWF-2000 folder with train/val folders")
        return False

def load_ground_truth():
    """
    Load ground-truth.json to get dataset splits
    """
    gt_file = VIOLENCE_DATASET_DIR / 'ground-truth.json'
    
    if not gt_file.exists():
        print(f"⚠ Ground truth file not found: {gt_file}")
        return {}
    
    try:
        with open(gt_file, 'r') as f:
            data = json.load(f)
        
        print(f"✓ Loaded ground truth for {len(data.get('database', {}))} videos")
        return data.get('database', {})
    except Exception as e:
        print(f"✗ Error loading ground truth: {e}")
        return {}

def organize_dataset():
    """
    Organize video frames into classification folder structure:
    - prepared/train/Fight
    - prepared/train/NonFight
    - prepared/val/Fight
    - prepared/val/NonFight
    - prepared/test/Fight
    - prepared/test/NonFight
    """
    print("\n" + "="*60)
    print("ORGANIZING DATASET")
    print("="*60)
    
    # Load ground truth
    ground_truth = load_ground_truth()
    
    # Check for existing data folders
    cctv_dir = VIOLENCE_DATASET_DIR / 'CCTV_DATA'
    non_cctv_dir = VIOLENCE_DATASET_DIR / 'NON_CCTV_DATA'
    
    # Also check for RWF-2000 folder (might be extracted there)
    rwf_dir = VIOLENCE_DATASET_DIR / 'RWF-2000'
    
    source_folders = []
    if cctv_dir.exists():
        source_folders.append(cctv_dir)
    if non_cctv_dir.exists():
        source_folders.append(non_cctv_dir)
    if rwf_dir.exists():
        # RWF-2000 typically has train/val structure
        if (rwf_dir / 'train').exists():
            source_folders.extend([rwf_dir / 'train', rwf_dir / 'val'])
    
    if not source_folders:
        print("✗ No source data folders found!")
        print("Expected: CCTV_DATA, NON_CCTV_DATA, or RWF-2000 folder")
        return
    
    print(f"Found {len(source_folders)} source folder(s)")
    
    # Create output directory structure
    for split in ['train', 'val', 'test']:
        for label in ['Fight', 'NonFight']:
            (OUTPUT_DIR / split / label).mkdir(parents=True, exist_ok=True)
    
    # Statistics
    stats = {
        'train': {'Fight': 0, 'NonFight': 0},
        'val': {'Fight': 0, 'NonFight': 0},
        'test': {'Fight': 0, 'NonFight': 0}
    }
    
    # Process videos using ground truth
    if ground_truth:
        for video_id, video_info in ground_truth.items():
            subset = video_info.get('subset', 'training')
            
            # Map subset names
            if subset == 'training':
                split = 'train'
            elif subset == 'validation':
                split = 'val'
            elif subset == 'testing':
                split = 'test'
            else:
                continue
            
            # Check if video has fight annotations
            annotations = video_info.get('annotations', [])
            has_fight = any(ann.get('label') == 'Fight' for ann in annotations)
            
            label = 'Fight' if has_fight else 'NonFight'
            
            # Find video folder in source directories
            video_found = False
            for source_dir in source_folders:
                video_path = source_dir / video_id
                
                if not video_path.exists():
                    # Try with different extensions/formats
                    possible_paths = [
                        source_dir / f"{video_id}.mp4",
                        source_dir / f"{video_id}.avi",
                        source_dir / video_id
                    ]
                    
                    for p in possible_paths:
                        if p.exists():
                            video_path = p
                            break
                
                if video_path.exists():
                    video_found = True
                    dest_dir = OUTPUT_DIR / split / label
                    
                    if video_path.is_dir():
                        # Copy entire folder (for frame sequences)
                        dest = dest_dir / video_id
                        if not dest.exists():
                            shutil.copytree(video_path, dest)
                            stats[split][label] += 1
                    else:
                        # Copy video file
                        dest = dest_dir / video_path.name
                        if not dest.exists():
                            shutil.copy2(video_path, dest)
                            stats[split][label] += 1
                    
                    break
            
            if not video_found and (stats['train']['Fight'] + stats['train']['NonFight'] + 
                                   stats['val']['Fight'] + stats['val']['NonFight'] +
                                   stats['test']['Fight'] + stats['test']['NonFight']) % 50 == 0:
                # Print occasional warnings, not for every missing file
                print(f"  ⚠ Video not found: {video_id}")
    
    else:
        # Fallback: organize based on folder structure if no ground truth
        print("⚠ No ground truth - organizing based on folder structure...")
        
        for source_dir in source_folders:
            if 'train' in source_dir.name.lower():
                split = 'train'
            elif 'val' in source_dir.name.lower():
                split = 'val'
            else:
                split = 'test'
            
            # Look for Fight/NonFight folders
            for label in ['Fight', 'NonFight']:
                label_dir = source_dir / label
                if label_dir.exists():
                    for item in label_dir.iterdir():
                        dest = OUTPUT_DIR / split / label / item.name
                        if not dest.exists():
                            if item.is_dir():
                                shutil.copytree(item, dest)
                            else:
                                shutil.copy2(item, dest)
                            stats[split][label] += 1
    
    # Print statistics
    print("\n" + "="*60)
    print("ORGANIZATION COMPLETE")
    print("="*60)
    
    for split in ['train', 'val', 'test']:
        total = stats[split]['Fight'] + stats[split]['NonFight']
        print(f"\n{split.upper()}:")
        print(f"  Fight: {stats[split]['Fight']}")
        print(f"  NonFight: {stats[split]['NonFight']}")
        print(f"  Total: {total}")
    
    return stats

def create_dataset_yaml():
    """
    Create dataset.yaml file for YOLO classification training
    """
    dataset_yaml = {
        'path': str(OUTPUT_DIR.absolute()),
        'train': 'train',
        'val': 'val',
        'test': 'test',
        'names': ['NonFight', 'Fight'],  # Class order matters!
        'nc': 2  # Number of classes
    }
    
    yaml_path = OUTPUT_DIR / 'dataset.yaml'
    with open(yaml_path, 'w') as f:
        yaml.dump(dataset_yaml, f, default_flow_style=False)
    
    print(f"\n✓ Created dataset.yaml at: {yaml_path}")
    return yaml_path

def main():
    """
    Main function to prepare RWF-2000 dataset for YOLO classification
    """
    print("\n" + "="*60)
    print("RWF-2000 VIOLENCE DETECTION DATASET PREPARATION")
    print("="*60)
    
    # Check if dataset directory exists
    if not VIOLENCE_DATASET_DIR.exists():
        print(f"\n✗ Dataset directory not found: {VIOLENCE_DATASET_DIR}")
        return
    
    print(f"\nDataset location: {VIOLENCE_DATASET_DIR}")
    print(f"Output location: {OUTPUT_DIR}")
    
    # Step 1: Extract archives if needed
    if not extract_archives():
        print("\n⚠ Continuing with existing data...")
    
    # Step 2: Organize dataset
    stats = organize_dataset()
    
    # Step 3: Create dataset.yaml
    if stats:
        yaml_path = create_dataset_yaml()
        
        # Final summary
        print("\n" + "="*60)
        print("DATASET PREPARATION COMPLETE")
        print("="*60)
        print(f"\nDataset ready for training!")
        print(f"Config file: {yaml_path}")
        print(f"\nNext step: Run train_violence_detection.py")
        print("="*60 + "\n")
    else:
        print("\n✗ Dataset organization failed!")
        print("Please check the error messages above.")

if __name__ == "__main__":
    main()
