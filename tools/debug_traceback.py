import traceback
import sys
try:
    import app
    print("App imported successfully")
except Exception:
    traceback.print_exc()
    sys.exit(1)
