"""
Copy CEMSS v11.1 to v11.2 - production ready without datasets
Excludes: training datasets, raw data, logs, temp files
Includes: code, configs, trained models, documentation
"""

import shutil
from pathlib import Path

SOURCE = Path(r"c:\Users\anina\OneDrive\Desktop\Project\CEMSS\v11.1")
DEST = Path(r"c:\Users\anina\OneDrive\Desktop\Project\CEMSS\v11.2")

# Directories to exclude completely
EXCLUDE_DIRS = {
    'jhu_crowd_v2.0',  # Crowd training dataset
    'yolo_format',  # Prepared crowd dataset
    'prepared_github',  # Prepared violence videos
    'prepared_frames',  # Extracted violence frames
    'github_dataset',  # Raw GitHub violence dataset
    'CCTV_DATA',  # Violence videos
    'NON_CCTV_DATA',  # Violence videos
    'training_runs',  # Training outputs (keep only final models)
    'runs',  # YOLO run outputs
    'cache',  # Cache files
    '__pycache__',  # Python cache
    '.git',  # Git data
    'logs',  # Log files
    'recordings',  # Video recordings
    'whatsapp_session',  # WhatsApp session (has lockfile)
}

# File patterns to exclude
EXCLUDE_PATTERNS = {
    '*.7z*',  # Compressed archives
    '*.zip',  # Zip files
    '*.log',  # Log files
    '*.db',  # Database files (will be recreated)
    '*.db-journal',  # DB journal
    'ground-truth.json',  # Dataset metadata
    'dataset.yaml',  # Dataset configs (not needed for production)
    '*_error.log',  # Error logs
}

# Files to keep even if in excluded locations
KEEP_FILES = {
    'crowd_detection_best.pt',  # Trained crowd model
    'violence_detection_github.pt',  # Trained violence model
    'fall_detection.pt',  # Fall model
    'phone_detection.pt',  # Phone model
    'yolov8n.pt',  # Base YOLO model
}

def should_exclude(path, rel_path):
    """Check if path should be excluded"""
    # Check directory exclusions
    for part in rel_path.parts:
        if part in EXCLUDE_DIRS:
            # But keep specific model files
            if path.is_file() and path.name in KEEP_FILES:
                return False
            return True
    
    # Check file pattern exclusions
    for pattern in EXCLUDE_PATTERNS:
        if path.match(pattern):
            return True
    
    return False

def copy_cemss():
    """Copy CEMSS system to v11.2"""
    print("\n" + "="*70)
    print("CREATING CEMSS v11.2 - PRODUCTION COPY")
    print("="*70)
    
    copied_files = 0
    copied_size = 0
    skipped_files = 0
    skipped_size = 0
    
    # Walk through source
    for src_path in SOURCE.rglob('*'):
        if not src_path.is_file():
            continue
        
        rel_path = src_path.relative_to(SOURCE)
        
        if should_exclude(src_path, rel_path):
            skipped_files += 1
            skipped_size += src_path.stat().st_size
            continue
        
        # Create destination path
        dest_path = DEST / rel_path
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Copy file
        try:
            shutil.copy2(src_path, dest_path)
            copied_files += 1
            copied_size += src_path.stat().st_size
        except PermissionError:
            # Skip locked files
            skipped_files += 1
            skipped_size += src_path.stat().st_size
            continue
    
    print(f"\n✓ Copied: {copied_files} files ({copied_size / 1024**2:.1f} MB)")
    print(f"✓ Skipped: {skipped_files} files ({skipped_size / 1024**3:.2f} GB)")
    
    # Create empty directories for runtime
    (DEST / 'logs').mkdir(exist_ok=True)
    (DEST / 'recordings' / 'detection').mkdir(parents=True, exist_ok=True)
    (DEST / 'recordings' / 'continuous').mkdir(parents=True, exist_ok=True)
    (DEST / 'cache' / 'frames').mkdir(parents=True, exist_ok=True)
    
    print(f"\n✓ Created runtime directories")
    
    print("\n" + "="*70)
    print("COPY COMPLETE - v11.2 READY")
    print("="*70)
    print(f"\nLocation: {DEST}")
    print("\nNext steps:")
    print("1. cd to v11.2 folder")
    print("2. Run: .\\CEMSS.bat")
    print("3. System will create new database and logs")
    print("="*70 + "\n")

if __name__ == "__main__":
    copy_cemss()
