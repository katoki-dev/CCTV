"""
CEMSS - Detection System Checkup
Comprehensive validation of all detection models and configurations
"""
import os
import sys
from pathlib import Path
import json
from datetime import datetime

print("="*70)
print("CEMSS DETECTION SYSTEM - COMPREHENSIVE CHECKUP")
print("="*70)

results = {
    'timestamp': datetime.now().isoformat(),
    'checks_passed': 0,
    'checks_failed': 0,
    'warnings': 0,
    'models': {},
    'configuration': {},
    'system': {}
}

# 1. Configuration Check
print("\n[1/5] Checking Configuration...")
try:
    from config import DETECTION_MODELS, TEMPORAL_SMOOTHING_FRAMES, CHATBOT_ENABLED
    from config import PHONE_FACE_FILTER_ENABLED, YOLO_DEVICE
    
    results['configuration']['chatbot_enabled'] = CHATBOT_ENABLED
    results['configuration']['phone_filter_enabled'] = PHONE_FACE_FILTER_ENABLED
    results['configuration']['yolo_device'] = YOLO_DEVICE
    results['configuration']['temporal_smoothing'] = TEMPORAL_SMOOTHING_FRAMES
    
    print(f"  ✓ Configuration loaded successfully")
    print(f"  - Chatbot: {'Enabled' if CHATBOT_ENABLED else 'DISABLED'}")
    print(f"  - Phone Filter: {'Enabled' if PHONE_FACE_FILTER_ENABLED else 'DISABLED'}")
    print(f"  - YOLO Device: {YOLO_DEVICE}")
    results['checks_passed'] += 1
except Exception as e:
    print(f"  ✗ Configuration error: {e}")
    results['checks_failed'] += 1
    results['configuration']['error'] = str(e)

# 2. Model Files Check
print("\n[2/5] Checking Model Files...")
try:
    from config import DETECTION_MODELS
    
    for model_name, config in DETECTION_MODELS.items():
        model_path = Path(config.get('model_path', ''))
        enabled = config.get('enabled', False)
        
        result = {
            'enabled': enabled,
            'path': str(model_path),
            'exists': model_path.exists() if model_path else False,
            'confidence': config.get('confidence_threshold', 'N/A'),
            'required_frames': config.get('required_frames', 'N/A')
        }
        
        if enabled and model_path:
            if model_path.exists():
                size_mb = model_path.stat().st_size / (1024*1024)
                result['size_mb'] = round(size_mb, 2)
                print(f"  ✓ {model_name}: {size_mb:.1f}MB - READY")
                results['checks_passed'] += 1
            else:
                print(f"  ✗ {model_name}: FILE NOT FOUND - {model_path}")
                results['checks_failed'] += 1
                result['error'] = 'File not found'
        elif enabled:
            print(f"  ⚠ {model_name}: Enabled but no model path")
            results['warnings'] += 1
        else:
            print(f"  - {model_name}: DISABLED")
        
        results['models'][model_name] = result

except Exception as e:
    print(f"  ✗ Model file check failed: {e}")
    results['checks_failed'] += 1

# 3. Detector Loading Test
print("\n[3/5] Testing Detector Loading...")
try:
    from detection.detector import MultiModelDetector
    
    detector = MultiModelDetector()
    loaded_models = detector.get_loaded_models()
    
    results['system']['loaded_models'] = loaded_models
    results['system']['model_count'] = len(loaded_models)
    
    print(f"  ✓ MultiModelDetector initialized")
    print(f"  - Loaded models: {', '.join(loaded_models)}")
    print(f"  - Total: {len(loaded_models)} models")
    results['checks_passed'] += 1
    
    # Check for missing models
    enabled_models = [name for name, cfg in DETECTION_MODELS.items() 
                     if cfg.get('enabled', False) and name != 'motion']
    missing = set(enabled_models) - set(loaded_models)
    if missing:
        print(f"  ⚠ Enabled but not loaded: {', '.join(missing)}")
        results['warnings'] += 1
        results['system']['missing_models'] = list(missing)
    
except Exception as e:
    print(f"  ✗ Detector loading failed: {e}")
    results['checks_failed'] += 1
    results['system']['error'] = str(e)

# 4. Enhanced Fall Detector Check
print("\n[4/5] Testing Enhanced Fall Detector...")
try:
    from detection.enhanced_fall_detector import create_enhanced_fall_detector
    
    fall_detector = create_enhanced_fall_detector()
    
    results['system']['fall_detector'] = {
        'mode': fall_detector.mode,
        'yolo_available': fall_detector.fall_detector is not None,
        'pose_available': fall_detector.pose_estimator is not None,
        'yolo_threshold': fall_detector.yolo_min_confidence,
        'pose_threshold': fall_detector.pose_min_confidence,
        'dual_threshold': fall_detector.combined_min_confidence,
        'high_conf_threshold': fall_detector.high_confidence_threshold
    }
    
    print(f"  ✓ Enhanced fall detector loaded")
    print(f"  - Mode: {fall_detector.mode}")
    print(f"  - YOLO: {'Available' if fall_detector.fall_detector else 'Missing'}")
    print(f"  - Pose: {'Available' if fall_detector.pose_estimator else 'Missing'}")
    print(f"  - Thresholds: YOLO≥{fall_detector.yolo_min_confidence}, Pose≥{fall_detector.pose_min_confidence}, Dual≥{fall_detector.combined_min_confidence}")
    results['checks_passed'] += 1
    
except Exception as e:
    print(f"  ✗ Enhanced fall detector failed: {e}")
    results['checks_failed'] += 1
    results['system']['fall_detector_error'] = str(e)

# 5. Motion Detector Check
print("\n[5/5] Testing Motion Detector...")
try:
    from detection.motion_detector import create_motion_detector
    
    motion_detector = create_motion_detector()
    
    results['system']['motion_detector'] = {
        'available': True,
        'sensitivity': motion_detector.sensitivity if hasattr(motion_detector, 'sensitivity') else 'unknown'
    }
    
    print(f"  ✓ Motion detector loaded")
    results['checks_passed'] += 1
    
except Exception as e:
    print(f"  ✗ Motion detector failed: {e}")
    results['checks_failed'] += 1
    results['system']['motion_detector_error'] = str(e)

# Summary
print("\n" + "="*70)
print("CHECKUP SUMMARY")
print("="*70)
print(f"Checks Passed: {results['checks_passed']}")
print(f"Checks Failed: {results['checks_failed']}")
print(f"Warnings: {results['warnings']}")

overall_status = "✓ PASS" if results['checks_failed'] == 0 else "✗ FAIL"
print(f"\nOverall Status: {overall_status}")

# Save results
output_file = 'detection_checkup_results.json'
with open(output_file, 'w') as f:
    json.dump(results, f, indent=2)

print(f"\n✓ Detailed results saved to {output_file}")
print("="*70)

# Exit with appropriate code
sys.exit(0 if results['checks_failed'] == 0 else 1)
