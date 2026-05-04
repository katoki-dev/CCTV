"""
CEMSS Deployment Package Creator
Creates a clean copy of CEMSS with only essential files
"""

import os
import shutil
from pathlib import Path

# Source and destination paths
SOURCE = r"c:\Users\anina\OneDrive\Desktop\Project\CEMSS\v11.2"
DEST = r"c:\Users\anina\OneDrive\Desktop\Project\CEMSS_Deployment"

# Essential files to copy
ESSENTIAL_FILES = [
    # Core application files
    "app.py",
    "config.py",
    "database.py",
    "models.py",
    "logging_manager.py",
    "health_monitor.py",
    "start.py",
    
    # Configuration files
    ".env.example",
    ".gitignore",
    "requirements.txt",
    "Dockerfile",
    "docker-compose.yml",
    "cemss.service",
    
    # Batch files for Windows
    "install.bat",
    "setup_and_run.bat",
    "start_cemss.bat",
    "CEMSS.bat",
    
    # Documentation
    "README.md",
    "INSTALLATION.md",
    "QUICK_START.md",
    "USER_MANUAL.md",
    "ADMIN_GUIDE.md",
    "EMAIL_SETUP.md",
    "LICENSE",
]

# Essential directories to copy (with all contents)
ESSENTIAL_DIRS = [
    "detection",
    "utils",
    "alerts",
    "analytics",
    "templates",
    "static",
    "modelfiles",
]

# Directories to create empty (for runtime)
RUNTIME_DIRS = [
    "logs",
    "recordings",
    "learning_data",
    "cache",
    "instance",
]

# Model files to copy (if they exist)
MODEL_FILES = [
    "yolov8n.pt",
    "yolov8n-pose.pt",
    "yolo11n.pt",
]

def copy_file(src, dest):
    """Copy a single file"""
    try:
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        shutil.copy2(src, dest)
        print(f"✓ Copied: {os.path.basename(src)}")
        return True
    except Exception as e:
        print(f"✗ Failed to copy {os.path.basename(src)}: {e}")
        return False

def copy_directory(src, dest, exclude_patterns=None):
    """Copy directory recursively, excluding certain patterns"""
    if exclude_patterns is None:
        exclude_patterns = ["__pycache__", "*.pyc", ".pytest_cache", "*.log"]
    
    def ignore_patterns(directory, files):
        ignored = []
        for pattern in exclude_patterns:
            if '*' in pattern:
                import fnmatch
                ignored.extend([f for f in files if fnmatch.fnmatch(f, pattern)])
            else:
                if pattern in files:
                    ignored.append(pattern)
        return ignored
    
    try:
        if os.path.exists(dest):
            shutil.rmtree(dest)
        shutil.copytree(src, dest, ignore=ignore_patterns)
        print(f"✓ Copied directory: {os.path.basename(src)}/")
        return True
    except Exception as e:
        print(f"✗ Failed to copy directory {os.path.basename(src)}: {e}")
        return False

def create_deployment_package():
    """Create the clean deployment package"""
    
    print("="*60)
    print("CEMSS Deployment Package Creator")
    print("="*60)
    print(f"\nSource: {SOURCE}")
    print(f"Destination: {DEST}\n")
    
    # Clean destination if it exists
    if os.path.exists(DEST):
        print("Cleaning existing deployment directory...")
        shutil.rmtree(DEST)
    
    os.makedirs(DEST, exist_ok=True)
    print(f"✓ Created deployment directory\n")
    
    # Copy essential files
    print("Copying essential files...")
    print("-" * 60)
    copied_files = 0
    for file in ESSENTIAL_FILES:
        src_path = os.path.join(SOURCE, file)
        dest_path = os.path.join(DEST, file)
        if os.path.exists(src_path):
            if copy_file(src_path, dest_path):
                copied_files += 1
        else:
            print(f"⚠ Not found: {file}")
    
    print(f"\n✓ Copied {copied_files}/{len(ESSENTIAL_FILES)} essential files\n")
    
    # Copy essential directories
    print("Copying essential directories...")
    print("-" * 60)
    copied_dirs = 0
    for dir_name in ESSENTIAL_DIRS:
        src_path = os.path.join(SOURCE, dir_name)
        dest_path = os.path.join(DEST, dir_name)
        if os.path.exists(src_path):
            if copy_directory(src_path, dest_path):
                copied_dirs += 1
        else:
            print(f"⚠ Not found: {dir_name}/")
    
    print(f"\n✓ Copied {copied_dirs}/{len(ESSENTIAL_DIRS)} directories\n")
    
    # Copy model files (if available)
    print("Copying model files...")
    print("-" * 60)
    models_dir = os.path.join(DEST, "models")
    os.makedirs(models_dir, exist_ok=True)
    
    copied_models = 0
    for model_file in MODEL_FILES:
        src_path = os.path.join(SOURCE, model_file)
        dest_path = os.path.join(DEST, model_file)
        if os.path.exists(src_path):
            if copy_file(src_path, dest_path):
                copied_models += 1
        else:
            print(f"⚠ Model not found: {model_file}")
    
    print(f"\n✓ Copied {copied_models} model files\n")
    
    # Create runtime directories
    print("Creating runtime directories...")
    print("-" * 60)
    for dir_name in RUNTIME_DIRS:
        dir_path = os.path.join(DEST, dir_name)
        os.makedirs(dir_path, exist_ok=True)
        
        # Create .gitkeep file
        gitkeep_path = os.path.join(dir_path, ".gitkeep")
        with open(gitkeep_path, 'w') as f:
            f.write("")
        print(f"✓ Created: {dir_name}/")
    
    print(f"\n✓ Created {len(RUNTIME_DIRS)} runtime directories\n")
    
    # Create database placeholder
    print("Creating database placeholder...")
    db_path = os.path.join(DEST, "database.db")
    open(db_path, 'w').close()
    print("✓ Created empty database.db (will be initialized on first run)\n")
    
    print("="*60)
    print("✅ Deployment package created successfully!")
    print("="*60)
    print(f"\nLocation: {DEST}")
    print("\nNext steps:")
    print("1. Navigate to the deployment folder")
    print("2. Copy .env.example to .env and configure")
    print("3. Run install.bat (Windows) or follow INSTALLATION.md")
    print("4. Run start_cemss.bat or python app.py")
    print("\n" + "="*60)

if __name__ == "__main__":
    create_deployment_package()
