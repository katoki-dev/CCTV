"""
CEMSS - Simple startup script
"""
import os
import sys

# Change to project directory
# Change to project directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)

print("\n" + "="*60)
print("CEMSS - Campus Event management and Surveillance System")
print("="*60)
print("Starting server...")
print("=" *60 + "\n")

# Run the Flask app with direct execution
if __name__ == '__main__':
    # This ensures models are imported correctly
    from app import app, socketio, init_components
    from config import FLASK_HOST, FLASK_PORT, DEBUG
    
    print(f"Server starting at: http://{FLASK_HOST}:{FLASK_PORT}")
    print("Default Login: admin / admin")
    print("="*60 + "\n")
    
    # Initialize components (cameras, detection) before starting server
    with app.app_context():
        init_components()
    
    socketio.run(app, host=FLASK_HOST, port=FLASK_PORT, debug=DEBUG, allow_unsafe_werkzeug=True)
