"""
Simple script to organize existing violence detection videos
Since CC TV_DATA and NON_CCTV_DATA only contain fight videos,
we'll organize them as Fight class and use existing prepared structure
"""

import shutil
from pathlib import Path

BASE_DIR = Path(__file__).parent
VIOLENCE_DIR = BASE_DIR / 'models' / 'violence_detection'
CCTV_DIR = VIOLENCE_DIR / 'CCTV_DATA'
NON_CCTV_DIR = VIOLENCE_DIR / 'NON_CCTV_DATA'
OUTPUT_DIR = VIOLENCE_DIR / 'organized'

# Create output structure
for split in ['train', 'val', 'test']:
    for label in ['Fight', 'NonFight']:
        (OUTPUT_DIR / split / label).mkdir(parents=True, exist_ok=True)

print("Organizing CCTV_DATA videos...")
# CCTV Training - all are fights
cctv_train = list((CCTV_DIR / 'training').glob('*.mpeg'))
print(f"Found {len(cctv_train)} CCTV training videos")
for video in cctv_train:
    shutil.copy2(video, OUTPUT_DIR / 'train' / 'Fight' / video.name)

# CCTV Validation
cctv_val = list((CCTV_DIR / 'validation').glob('*.mpeg'))
print(f"Found {len(cctv_val)} CCTV validation videos")
for video in cctv_val:
    shutil.copy2(video, OUTPUT_DIR / 'val' / 'Fight' / video.name)

# CCTV Testing
cctv_test = list((CCTV_DIR / 'testing').glob('*.mpeg'))
print(f"Found {len(cctv_test)} CCTV testing videos")
for video in cctv_test:
    shutil.copy2(video, OUTPUT_DIR / 'test' / 'Fight' / video.name)

print("\nOrganizing NON_CCTV_DATA videos...")
# NON-CCTV Training - all are fights
non_cctv_train = list((NON_CCTV_DIR / 'training').glob('*.mpeg'))
print(f"Found {len(non_cctv_train)} NON-CCTV training videos")
for video in non_cctv_train:
    shutil.copy2(video, OUTPUT_DIR / 'train' / 'Fight' / video.name.replace('fight_', 'noncctv_fight_'))

# NON-CCTV Validation
non_cctv_val = list((NON_CCTV_DIR / 'validation').glob('*.mpeg'))
print(f"Found {len(non_cctv_val)} NON-CCTV validation videos")
for video in non_cctv_val:
    shutil.copy2(video, OUTPUT_DIR / 'val' / 'Fight' / video.name.replace('fight_', 'noncctv_fight_'))

# NON-CCTV Testing  
non_cctv_test = list((NON_CCTV_DIR / 'testing').glob('*.mpeg'))
print(f"Found {len(non_cctv_test)} NON-CCTV testing videos")
for video in non_cctv_test:
    shutil.copy2(video, OUTPUT_DIR / 'test' / 'Fight' / video.name.replace('fight_', 'noncctv_fight_'))

print("\n" + "="*60)
print("ORGANIZATION COMPLETE")
print("="*60)
print(f"\nTrain Fight videos: {len(cctv_train) + len(non_cctv_train)}")
print(f"Val Fight videos: {len(cctv_val) + len(non_cctv_val)}")
print(f"Test Fight videos: {len(cctv_test) + len(non_cctv_test)}")
print(f"\nWarning: No NonFight videos available!")
print("The dataset only contains Fight videos.")
print("For binary classification, you need non-fight/normal videos as well.")
print("\nYou can:")
print("1. Manually add normal CCTV footage to \\NonFight\\ folders")
print("2. Use a different dataset with both classes")
print("3. Train on existing violence_detection.pt model")
