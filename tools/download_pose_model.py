from ultralytics import YOLO
import os

model_path = 'models/yolov8n-pose.pt'

print(f"Downloading {model_path}...")
try:
    model = YOLO('yolov8n-pose.pt')
    model.save(model_path)
    print("Download complete.")
except Exception as e:
    print(f"Error downloading model: {e}")
