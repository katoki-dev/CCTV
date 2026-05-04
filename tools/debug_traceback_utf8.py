import traceback
import sys
import os

try:
    import app
    print("App imported successfully")
except Exception:
    with open("full_traceback.txt", "w", encoding="utf-8") as f:
        traceback.print_exc(file=f)
    sys.exit(1)
