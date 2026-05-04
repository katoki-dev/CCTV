from app import app, db
from models import Camera
import sys
import os

# Ensure we are in the correct directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

try:
    with app.app_context():
        cameras = Camera.query.all()
        for cam in cameras:
            cam.detection_enabled = False
            print(f"Disabled detection for {cam.name}")
        db.session.commit()
        print("All cameras disabled successfully.")
except Exception as e:
    print(f"Error: {e}")
