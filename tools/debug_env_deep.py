import dotenv
import os
import traceback
import sys

print(f"Current Directory: {os.getcwd()}")
env_path = dotenv.find_dotenv()
print(f"Found .env at: {env_path}")

try:
    print("Attempting import app...")
    import app
    print("App imported successfully")
except Exception:
    traceback.print_exc()
    # Check os.environ for nulls
    for k, v in os.environ.items():
        if '\0' in k or '\0' in str(v):
            print(f"NULL IN ENV: {k}")
