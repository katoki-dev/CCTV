from config import DATABASE_PATH
import os

print(f"Configured DATABASE_PATH: {DATABASE_PATH}")
print(f"Exists: {os.path.exists(DATABASE_PATH)}")

# Try to list directory content from python
parent = os.path.dirname(DATABASE_PATH)
print(f"Contents of {parent}:")
try:
    print(os.listdir(parent))
except Exception as e:
    print(f"Error listing dir: {e}")
