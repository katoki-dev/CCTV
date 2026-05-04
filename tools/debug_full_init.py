import dotenv
import os
import traceback
import sys

print(f"Current Directory: {os.getcwd()}")
env_path = dotenv.find_dotenv()
print(f"Found .env at: {env_path}")

try:
    print("Attempting import app...")
    from app import app, init_components
    print("App imported successfully")
    
    print("Attempting init_components()...")
    with app.app_context():
        init_components()
    print("init_components() successful")
    
    # Keep it running for a few seconds to see if threads crash
    import time
    time.sleep(5)
    print("Still running...")
    
except Exception:
    traceback.print_exc()
    sys.exit(1)
