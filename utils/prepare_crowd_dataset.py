"""
CASS - Crowd Detection Dataset Preparation
Converts JHU Crowd v2.0 dataset to YOLO format for training
"""

import os
import shutil
from pathlib import Path
import yaml

# Dataset paths
BASE_DIR = Path(__file__).parent.parent
CROWD_DATASET_DIR = BASE_DIR / 'models' / 'crowd_detection' / 'archive(6)'
OUTPUT_DIR = BASE_DIR / 'models' / 'crowd_detection' / 'yolo_format'

def parse_ground_truth(gt_file):
    """
    Parse JHU Crowd ground truth file
    Format: x y w h occlusion blur (space separated)
    Returns list of bounding boxes in YOLO format
    """
    bboxes = []
    
    try:
        with open(gt_file, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                    
                parts = line.split()
                if len(parts) < 4:
                    continue
                
                # Extract coordinates (x, y, w, h)
                x, y, w, h = map(float, parts[:4])
                
                # YOLO format uses center coordinates and normalized values
                # We'll normalize later when we know image dimensions
                bboxes.append({
                    'x': x,
                    'y': y, 
                    'w': w,
                    'h': h
                })
    except Exception as e:
        print(f"Error parsing {gt_file}: {e}")
        
    return bboxes

def convert_to_yolo_format(bboxes, img_width, img_height):
    """
    Convert bounding boxes to YOLO format:
    class_id x_center y_center width height (all normalized 0-1)
    
    For crowd detection, class_id is always 0 (person)
    """
    yolo_annotations = []
    
    for bbox in bboxes:
        # Calculate center coordinates
        x_center = bbox['x'] + (bbox['w'] / 2)
        y_center = bbox['y'] + (bbox['h'] / 2)
        
        # Normalize to 0-1 range
        x_center_norm = x_center / img_width
        y_center_norm = y_center / img_height
        width_norm = bbox['w'] / img_width
        height_norm = bbox['h'] / img_height
        
        # Ensure values are within bounds
        x_center_norm = max(0, min(1, x_center_norm))
        y_center_norm = max(0, min(1, y_center_norm))
        width_norm = max(0, min(1, width_norm))
        height_norm = max(0, min(1, height_norm))
        
        # Class 0 for person
        yolo_annotations.append(f"0 {x_center_norm:.6f} {y_center_norm:.6f} {width_norm:.6f} {height_norm:.6f}")
    
    return yolo_annotations

def get_image_dimensions(image_path):
    """Get image dimensions using PIL or cv2"""
    try:
        from PIL import Image
        with Image.open(image_path) as img:
            return img.size  # Returns (width, height)
    except ImportError:
        import cv2
        img = cv2.imread(str(image_path))
        if img is not None:
            return (img.shape[1], img.shape[0])  # (width, height)
    return None

def prepare_split(split_name):
    """
    Prepare dataset for a specific split (train/val/test)
    """
    print(f"\n{'='*60}")
    print(f"Processing {split_name.upper()} split...")
    print(f"{'='*60}")
    
    split_dir = CROWD_DATASET_DIR / split_name
    images_dir = split_dir / 'images'
    gt_dir = split_dir / 'gt'
    
    # Create output directories
    output_images_dir = OUTPUT_DIR / 'images' / split_name
    output_labels_dir = OUTPUT_DIR / 'labels' / split_name
    
    output_images_dir.mkdir(parents=True, exist_ok=True)
    output_labels_dir.mkdir(parents=True, exist_ok=True)
    
    processed_count = 0
    error_count = 0
    total_annotations = 0
    
    # Process each image
    for gt_file in gt_dir.glob('*.txt'):
        image_name = gt_file.stem + '.jpg'
        image_path = images_dir / image_name
        
        if not image_path.exists():
            # Try .png extension
            image_name = gt_file.stem + '.png'
            image_path = images_dir / image_name
            
        if not image_path.exists():
            print(f"⚠ Image not found for {gt_file.name}")
            error_count += 1
            continue
        
        # Get image dimensions
        dimensions = get_image_dimensions(image_path)
        if dimensions is None:
            print(f"⚠ Could not read image: {image_path}")
            error_count += 1
            continue
            
        img_width, img_height = dimensions
        
        # Parse ground truth
        bboxes = parse_ground_truth(gt_file)
        
        if not bboxes:
            print(f"⚠ No annotations found in {gt_file.name}")
            # Still copy the image but create empty label file
        
        # Convert to YOLO format
        yolo_annotations = convert_to_yolo_format(bboxes, img_width, img_height)
        total_annotations += len(yolo_annotations)
        
        # Copy image
        dest_image = output_images_dir / image_name
        shutil.copy2(image_path, dest_image)
        
        # Write YOLO annotations
        label_file = output_labels_dir / (gt_file.stem + '.txt')
        with open(label_file, 'w') as f:
            f.write('\n'.join(yolo_annotations))
        
        processed_count += 1
        
        if processed_count % 100 == 0:
            print(f"  Processed {processed_count} images...")
    
    print(f"\n✓ {split_name.upper()} split complete:")
    print(f"  - Images processed: {processed_count}")
    print(f"  - Total annotations: {total_annotations}")
    print(f"  - Avg annotations/image: {total_annotations/processed_count:.1f}" if processed_count > 0 else "")
    print(f"  - Errors: {error_count}")
    
    return processed_count, total_annotations

def create_dataset_yaml():
    """
    Create dataset.yaml file for YOLO training
    """
    dataset_yaml = {
        'path': str(OUTPUT_DIR.absolute()),
        'train': 'images/train',
        'val': 'images/val',
        'test': 'images/test',
        'names': {
            0: 'person'
        },
        'nc': 1  # Number of classes
    }
    
    yaml_path = OUTPUT_DIR / 'dataset.yaml'
    with open(yaml_path, 'w') as f:
        yaml.dump(dataset_yaml, f, default_flow_style=False)
    
    print(f"\n✓ Created dataset.yaml at: {yaml_path}")
    return yaml_path

def main():
    """
    Main function to prepare JHU Crowd dataset for YOLO training
    """
    print("\n" + "="*60)
    print("JHU CROWD DATASET PREPARATION FOR YOLO")
    print("="*60)
    
    # Check if dataset exists
    if not CROWD_DATASET_DIR.exists():
        print(f"\n✗ Dataset not found at: {CROWD_DATASET_DIR}")
        print("Please ensure the JHU Crowd v2.0 dataset is in the correct location.")
        return
    
    print(f"\nDataset location: {CROWD_DATASET_DIR}")
    print(f"Output location: {OUTPUT_DIR}")
    
    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Process each split
    total_images = 0
    total_annots = 0
    
    for split in ['train', 'val', 'test']:
        if (CROWD_DATASET_DIR / split).exists():
            img_count, annot_count = prepare_split(split)
            total_images += img_count
            total_annots += annot_count
    
    # Create dataset.yaml
    yaml_path = create_dataset_yaml()
    
    # Final summary
    print("\n" + "="*60)
    print("DATASET PREPARATION COMPLETE")
    print("="*60)
    print(f"Total images processed: {total_images}")
    print(f"Total annotations created: {total_annots}")
    print(f"\nDataset ready for training!")
    print(f"Config file: {yaml_path}")
    print(f"\nNext step: Run train_crowd_detection.py")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
