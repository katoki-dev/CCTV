# CEMSS Model Training Guide

Complete guide for training crowd detection and violence detection models using the newly added datasets.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Crowd Detection Training](#crowd-detection-training)
4. [Violence Detection Training](#violence-detection-training)
5. [Testing and Integration](#testing-and-integration)
6. [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements

- **GPU**: NVIDIA GPU with CUDA support (recommended)
  - Minimum 4GB VRAM for training
  - Training on CPU is possible but much slower (hours → days)
- **RAM**: 8GB minimum, 16GB recommended
- **Storage**: ~15GB free space

### Software Requirements

- Python 3.8+
- PyTorch with CUDA (if using GPU)
- Ultralytics YOLOv8
- 7-Zip (for violence dataset extraction)

### Check Your Setup

```powershell
# Check GPU availability
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"

# Check YOLO installation
python -c "from ultralytics import YOLO; print('YOLO installed')"
```

## Quick Start

### Option 1: Train Both Models (Recommended)

```powershell
# Step 1: Prepare datasets
python utils/prepare_crowd_dataset.py
python utils/prepare_violence_dataset.py

# Step 2: Train models (GPU recommended)
python train_crowd_detection.py
python train_violence_detection.py
```

### Option 2: Train Individual Models

**Crowd Detection Only:**

```powershell
python utils/prepare_crowd_dataset.py
python train_crowd_detection.py
```

**Violence Detection Only:**

```powershell
python utils/prepare_violence_dataset.py
python train_violence_detection.py
```

## Crowd Detection Training

### Step 1: Prepare Dataset

```powershell
python utils/prepare_crowd_dataset.py
```

**What it does:**

- Converts JHU Crowd v2.0 annotations to YOLO format
- Creates train/val/test splits
- Generates `dataset.yaml` configuration

**Expected output:**

```
Processing TRAIN split...
  Processed 2272 images...
  Total annotations: 450,000+

Processing VAL split...
  Processed 500 images...

Processing TEST split...
  Processed 1600 images...

✓ Dataset ready for training!
```

**Output location:** `models/crowd_detection/yolo_format/`

### Step 2: Train Model

```powershell
python train_crowd_detection.py
```

**Training configuration:**

- Base model: YOLOv8n (pretrained)
- Epochs: 50
- Batch size: 16
- Image size: 640x640
- Expected time: 2-4 hours (GPU)

**What to expect:**

1. System checks (GPU availability)
2. Dataset validation
3. Model initialization
4. Training progress bars showing:
   - Loss metrics (box_loss, cls_loss, dfl_loss)
   - mAP scores
   - Precision/Recall

**Output location:** `models/crowd_detection/training_runs/crowd_yolov8n/`

**Key files:**

- `weights/best.pt` - Best model checkpoint
- `weights/last.pt` - Last epoch checkpoint
- `results.png` - Training curves
- `confusion_matrix.png` - Classification results

### Step 3: Evaluate Results

The script automatically evaluates on the test set after training:

```
Test Results:
  mAP50: 0.8234
  mAP50-95: 0.6789
  Precision: 0.8456
  Recall: 0.7892
```

## Violence Detection Training

### Step 1: Prepare Dataset

```powershell
python utils/prepare_violence_dataset.py
```

**What it does:**

- Extracts RWF-2000 archives (if not extracted)
- Organizes videos into Fight/NonFight categories
- Creates train/val/test splits
- Generates `dataset.yaml` configuration

**Important:**

- Requires 7-Zip to be installed
- Extraction takes 5-10 minutes
- Will use ~9GB of disk space

**Expected output:**

```
EXTRACTING RWF-2000 ARCHIVES
Found 13 archive parts
Extracting... This may take several minutes...
✓ Extraction complete!

ORGANIZING DATASET
TRAIN:
  Fight: 800
  NonFight: 800
VAL:
  Fight: 100
  NonFight: 100
TEST:
  Fight: 100
  NonFight: 100

✓ Dataset ready for training!
```

**Output location:** `models/violence_detection/prepared/`

### Step 2: Train Model

```powershell
python train_violence_detection.py
```

**Training configuration:**

- Base model: YOLOv8n-cls (classification)
- Epochs: 30
- Batch size: 8
- Image size: 224x224
- Expected time: 1-2 hours (GPU)

**What to expect:**

1. System checks
2. Dataset validation
3. Classification training with:
   - Accuracy metrics
   - Top-1 and Top-5 accuracy
   - Class-wise performance

**Output location:** `models/violence_detection/training_runs/violence_yolov8n_cls/`

**Key files:**

- `weights/best.pt` - Best model checkpoint
- `weights/last.pt` - Last epoch checkpoint
- `results.png` - Training curves
- `confusion_matrix.png` - Classification matrix

### Step 3: Evaluate Results

```
Test Results:
  Top-1 Accuracy: 0.9250
  Top-5 Accuracy: 0.9850
```

## Testing and Integration

### Update CEMSS Configuration

After training completes, update `config.py`:

```python
# For crowd detection (if trained)
DETECTION_MODELS = {
    'person': {
        'enabled': True,
        'model_path': str(MODELS_DIR / 'crowd_detection' / 'weights' / 'crowd_detection_best.pt'),
        'confidence_threshold': 0.5,
        'description': 'Person Detection (Crowd-trained)'
    },
    # ... other models ...
}

# For violence detection (if trained)
DETECTION_MODELS = {
    # ... existing models ...
    'violence': {
        'enabled': True,
        'model_path': str(MODELS_DIR / 'violence_detection' / 'weights' / 'violence_detection_best.pt'),
        'confidence_threshold': 0.65,
        'description': 'Violence/Fight Detection'
    },
}
```

### Test the Models

1. **Start CEMSS:**

   ```powershell
   .\CEMSS.bat
   ```

2. **Add a test video:**
   - Use a video with crowds for crowd detection
   - Use a video with fighting for violence detection

3. **Enable detection** for the test camera

4. **Monitor system logs** for detections

5. **Check database** for logged events:
   - Crowd alerts when person count ≥ CROWD_THRESHOLD (default: 5)
   - Violence alerts when fights are detected

### Verify Performance

**Crowd Detection:**

- Should trigger alerts in crowded scenes (5+ people)
- Better person detection in dense crowds
- Reduced false negatives

**Violence Detection:**

- Should detect fighting/violence in video
- Minimal false positives during normal activity
- Quick alert response (<1 second)

## Troubleshooting

### Dataset Preparation Issues

**Issue:** `Dataset not found`

```
✗ Dataset not found at: models/crowd_detection/jhu_crowd_v2.0/jhu_crowd_v2.0
```

**Solution:** Ensure dataset is in the correct location with proper folder structure.

**Issue:** `No annotations found`
**Solution:** Verify ground truth files exist in `gt/` folders.

**Issue:** `7-Zip not found` (violence dataset)
**Solution:**

1. Download 7-Zip: <https://www.7-zip.org/>
2. Install to default location
3. Or extract archives manually

### Training Issues

**Issue:** `CUDA out of memory`
**Solution:** Reduce batch size:

- Crowd detection: Try batch=8 or batch=4
- Violence detection: Try batch=4

Edit the CONFIG dict in training scripts.

**Issue:** Training is very slow
**Solution:**

- Verify GPU is being used: Check "Device: 0" in output
- If using CPU, consider:
  - Using a GPU-enabled machine
  - Reducing epochs
  - Using smaller batch size

**Issue:** `ModuleNotFoundError: No module named 'ultralytics'`
**Solution:**

```powershell
pip install ultralytics
```

**Issue:** Low accuracy after training
**Solution:**

- Train for more epochs
- Check dataset quality
- Adjust learning rate (reduce lr0 in CONFIG)
- Try data augmentation settings

### Integration Issues

**Issue:** Model not loading in CEMSS
**Solution:**

1. Check model path in config.py
2. Verify model file exists
3. Restart CEMSS completely

**Issue:** No detections after integration
**Solution:**

1. Check confidence threshold (try lowering it)
2. Verify model is enabled in config.py
3. Check system logs for errors

**Issue:** Too many false positives
**Solution:**

1. Increase confidence threshold
2. Retrain with more epochs
3. Adjust CROWD_THRESHOLD for crowd alerts

## Additional Resources

### Model Performance Monitoring

Check training results:

```
models/crowd_detection/training_runs/crowd_yolov8n/
models/violence_detection/training_runs/violence_yolov8n_cls/
```

Key files to review:

- `results.png` - Training curves
- `confusion_matrix.png` - Performance breakdown
- `F1_curve.png` - F1 scores
- `PR_curve.png` - Precision-Recall

### Re-training

To retrain with different parameters:

1. Edit CONFIG dictionary in training scripts
2. Change epochs, batch size, learning rate, etc.
3. Run training script again

### Dataset Citations

**JHU Crowd++:**

```
@inproceedings{sindagi2019pushing,
  title={Pushing the frontiers of unconstrained crowd counting},
  author={Sindagi, Vishwanath A and Yasarla, Rajeev and Patel, Vishal M},
  booktitle={ICCV},
  year={2019}
}
```

**RWF-2000:**

```
@inproceedings{cheng2021rwf,
  title={RWF-2000: An Open Large Scale Video Database for Violence Detection},
  author={Cheng, Ming and Cai, Kunjing and Li, Ming},
  booktitle={ICPR},
  year={2021}
}
```

## Support

For issues or questions:

1. Check system logs: `logs/session_*.log`
2. Review training outputs in `training_runs/` folders
3. Verify dataset preparation completed successfully
4. Test models independently before CEMSS integration

---

**Note:** Training times are estimates based on modern GPU (RTX 3060 or equivalent). Actual times may vary based on hardware.
