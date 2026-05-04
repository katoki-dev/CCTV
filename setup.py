"""
CEMSS - Setup and Installation Script
Checks dependencies, initializes database, and prepares the system
"""
import sys
import os
import subprocess
import importlib.util

def print_header(text):
    """Print a formatted header"""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)

def print_status(status, message):
    """Print status message with icon"""
    icons = {
        'success': '✓',
        'error': '✗',
        'warning': '⚠',
        'info': 'ℹ'
    }
    icon = icons.get(status, '•')
    print(f"{icon} {message}")

def check_python_version():
    """Check if Python version is compatible"""
    print_header("Checking Python Version")
    
    version = sys.version_info
    if version.major == 3 and version.minor >= 8:
        print_status('success', f"Python {version.major}.{version.minor}.{version.micro} - Compatible")
        return True
    else:
        print_status('error', f"Python {version.major}.{version.minor}.{version.micro} - Incompatible")
        print_status('error', "CEMSS requires Python 3.8 or higher")
        return False

def check_package_installed(package_name):
    """Check if a Python package is installed"""
    spec = importlib.util.find_spec(package_name)
    return spec is not None

def install_requirements():
    """Install required Python packages"""
    print_header("Installing Python Dependencies")
    
    if not os.path.exists('requirements.txt'):
        print_status('error', "requirements.txt not found")
        return False
    
    try:
        print_status('info', "Installing packages from requirements.txt...")
        print_status('info', "This may take several minutes...")
        
        subprocess.check_call([
            sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'
        ])
        
        print_status('success', "All dependencies installed successfully")
        return True
    except subprocess.CalledProcessError:
        print_status('error', "Failed to install dependencies")
        print_status('warning', "Try running: pip install -r requirements.txt")
        return False

def check_critical_packages():
    """Check if critical packages are installed"""
    print_header("Checking Critical Dependencies")
    
    critical_packages = {
        'flask': 'Flask',
        'flask_login': 'Flask-Login',
        'flask_sqlalchemy': 'Flask-SQLAlchemy',
        'flask_socketio': 'Flask-SocketIO',
        'cv2': 'opencv-python',
        'ultralytics': 'ultralytics',
        'torch': 'torch',
        'dotenv': 'python-dotenv'
    }
    
    missing_packages = []
    
    for module_name, package_name in critical_packages.items():
        if check_package_installed(module_name):
            print_status('success', f"{package_name} - Installed")
        else:
            print_status('error', f"{package_name} - Missing")
            missing_packages.append(package_name)
    
    if missing_packages:
        print_status('warning', f"Missing packages: {', '.join(missing_packages)}")
        return False
    
    return True

def setup_environment():
    """Setup .env file from template"""
    print_header("Setting Up Environment Configuration")
    
    if os.path.exists('.env'):
        print_status('info', ".env file already exists")
        response = input("  Do you want to overwrite it? (y/N): ").strip().lower()
        if response != 'y':
            print_status('info', "Keeping existing .env file")
            return True
    
    if not os.path.exists('.env.example'):
        print_status('error', ".env.example template not found")
        return False
    
    try:
        with open('.env.example', 'r') as example:
            content = example.read()
        
        with open('.env', 'w') as env_file:
            env_file.write(content)
        
        print_status('success', "Created .env file from template")
        print_status('warning', "IMPORTANT: Edit .env file to configure your settings")
        return True
    except Exception as e:
        print_status('error', f"Failed to create .env file: {str(e)}")
        return False

def initialize_database():
    """Initialize the database"""
    print_header("Initializing Database")
    
    try:
        # Import after checking dependencies
        from database import init_database
        from config import DATABASE_PATH
        
        if os.path.exists(DATABASE_PATH):
            print_status('info', f"Database already exists at: {DATABASE_PATH}")
            response = input("  Do you want to reinitialize it? (y/N): ").strip().lower()
            if response != 'y':
                print_status('info', "Keeping existing database")
                return True
            else:
                os.remove(DATABASE_PATH)
                print_status('warning', "Existing database removed")
        
        init_database()
        print_status('success', f"Database initialized at: {DATABASE_PATH}")
        print_status('info', "Default admin user created (admin/admin)")
        return True
    except Exception as e:
        print_status('error', f"Database initialization failed: {str(e)}")
        return False

def check_ollama_installation():
    """Check if Ollama is installed on the system"""
    try:
        # Try to run ollama command to check if it's installed
        result = subprocess.run(
            ['ollama', '--version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            version = result.stdout.strip()
            return True, version
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    
    return False, None

def check_ollama_running():
    """Check if Ollama server is running"""
    try:
        import requests
        response = requests.get('http://localhost:11434/api/version', timeout=2)
        if response.status_code == 200:
            return True
    except:
        pass
    return False

def check_ollama_models():
    """Check if required Ollama models are installed"""
    try:
        import requests
        response = requests.get('http://localhost:11434/api/tags', timeout=5)
        if response.status_code == 200:
            models_data = response.json()
            installed_models = [m['name'] for m in models_data.get('models', [])]
            return installed_models
    except:
        return []

def setup_ollama():
    """Guide user through Ollama setup for LLM/VLM features"""
    print_header("Ollama Setup (LLM/VLM AI Features)")
    
    # Step 1: Check if Ollama is installed
    is_installed, version = check_ollama_installation()
    
    if not is_installed:
        print_status('warning', "Ollama is not installed")
        print()
        print("  Ollama provides AI chatbot and VLM (Vision Language Model) features.")
        print("  Without Ollama, these features will be disabled.")
        print()
        print("  To install Ollama:")
        print("    1. Visit: https://ollama.ai")
        print("    2. Download the installer for your OS")
        print("    3. Run the installer")
        print("    4. Restart this setup script")
        print()
        
        response = input("  Continue setup without Ollama? (Y/n): ").strip().lower()
        if response == 'n':
            print_status('info', "Setup paused. Install Ollama and run setup again.")
            return False
        else:
            print_status('info', "Continuing without Ollama (AI features disabled)")
            return False
    
    print_status('success', f"Ollama is installed ({version})")
    
    # Step 2: Check if Ollama is running
    if not check_ollama_running():
        print_status('warning', "Ollama server is not running")
        print()
        print("  Starting Ollama server...")
        print("  Run this command in a separate terminal:")
        print()
        print("    ollama serve")
        print()
        print("  Or Ollama may start automatically after installation.")
        print()
        
        response = input("  Is Ollama running now? (y/N): ").strip().lower()
        if response != 'y':
            print_status('info', "Continuing without Ollama server")
            print_status('info', "Start Ollama later to enable AI features")
            return False
    
    print_status('success', "Ollama server is running")
    
    # Step 3: Check required models
    print()
    print_status('info', "Checking required AI models...")
    print()
    
    installed_models = check_ollama_models()
    
    required_models = {
        'qwen2.5:0.5b': 'Chatbot LLM (fast, 400MB)',
        'moondream': 'VLM for camera analysis (2GB)',
        'llava:7b': 'Advanced VLM (optional, 4.5GB)'
    }
    
    missing_models = []
    
    for model, description in required_models.items():
        model_base = model.split(':')[0]
        # Check both exact match and base name match
        if model in installed_models or any(model_base in m for m in installed_models):
            print_status('success', f"{model} - Installed ({description})")
        else:
            print_status('warning', f"{model} - Not installed ({description})")
            missing_models.append(model)
    
    if missing_models:
        print()
        print_status('warning', f"{len(missing_models)} model(s) missing")
        print()
        print("  To install missing models, run:")
        print()
        for model in missing_models:
            print(f"    ollama pull {model}")
        print()
        
        response = input("  Install missing models now? (Y/n): ").strip().lower()
        if response != 'n':
            print()
            for model in missing_models:
                print(f"  Installing {model}...")
                try:
                    result = subprocess.run(
                        ['ollama', 'pull', model],
                        capture_output=False,
                        text=True,
                        timeout=600  # 10 minutes max per model
                    )
                    if result.returncode == 0:
                        print_status('success', f"{model} installed")
                    else:
                        print_status('error', f"Failed to install {model}")
                except subprocess.TimeoutExpired:
                    print_status('error', f"Timeout installing {model}")
                except Exception as e:
                    print_status('error', f"Error installing {model}: {e}")
                print()
        else:
            print_status('info', "Model installation skipped")
            print_status('info', "Install models later to enable full AI features")
            return False
    else:
        print_status('success', "All required models are installed")
    
    print()
    print_status('success', "Ollama setup complete - AI features enabled!")
    return True


def check_model_files():
    """Check if detection model files exist"""
    print_header("Checking Detection Models")
    
    model_dir = 'models'
    if not os.path.exists(model_dir):
        os.makedirs(model_dir)
        print_status('info', f"Created {model_dir} directory")
    
    required_models = {
        'yolov8n.pt': 'Person detection (will auto-download)',
        'fall_detection.pt': 'Fall detection (custom trained)',
        'violence_detection.pt': 'Violence detection (custom trained)',
        'phone_detection.pt': 'Phone detection (custom trained)'
    }
    
    for model_file, description in required_models.items():
        model_path = os.path.join(model_dir, model_file)
        if os.path.exists(model_path):
            size_mb = os.path.getsize(model_path) / (1024 * 1024)
            print_status('success', f"{model_file} - Found ({size_mb:.1f}MB)")
        else:
            print_status('warning', f"{model_file} - Not found ({description})")
    
    print_status('info', "Base YOLOv8 models will auto-download on first run")
    return True

def create_directories():
    """Create necessary directories"""
    print_header("Creating Directory Structure")
    
    directories = [
        'logs',
        'recordings/detection',
        'recordings/continuous',
        'videos',
        'cache/frames',
        'models'
    ]
    
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print_status('success', f"Created: {directory}/")
        else:
            print_status('info', f"Exists: {directory}/")
    
    return True

def main():
    """Main setup routine"""
    print()
    print("=" * 60)
    print("     CEMSS - Campus Event management and Surveillance System")
    print("           Setup & Installation Script")
    print("                    v11.1")
    print("=" * 60)
    
    # Track setup success
    all_success = True
    
    # 1. Check Python version
    if not check_python_version():
        return 1
    
    # 2. Create directories
    create_directories()
    
    # 3. Check critical packages
    packages_ok = check_critical_packages()
    
    if not packages_ok:
        print_status('warning', "Some dependencies are missing")
        response = input("\n  Install dependencies now? (Y/n): ").strip().lower()
        if response != 'n':
            if not install_requirements():
                all_success = False
        else:
            print_status('info', "Dependencies installation skipped")
            all_success = False
    
    # 4. Setup environment
    if not setup_environment():
        all_success = False
    
    # 5. Initialize database
    if packages_ok or check_critical_packages():
        response = input("\n  Initialize database now? (Y/n): ").strip().lower()
        if response != 'n':
            if not initialize_database():
                all_success = False
        else:
            print_status('info', "Database initialization skipped")
    
    # 6. Setup Ollama and AI models (optional but recommended)
    setup_ollama()
    
    # 7. Check model files
    check_model_files()
    
    # Final summary
    print_header("Setup Summary")
    
    if all_success:
        print_status('success', "CEMSS setup completed successfully!")
        print()
        print("Next Steps:")
        print("  1. Edit .env file with your configuration")
        print("  2. Run 'start_cemss.bat' to start the system")
        print("  3. Access dashboard at http://localhost:5000")
        print("  4. Default login: admin / admin")
        print()
        print_status('warning', "IMPORTANT: Change default admin password after first login!")
        return 0
    else:
        print_status('warning', "Setup completed with some issues")
        print()
        print("Please resolve the issues above before starting CEMSS")
        return 1

if __name__ == '__main__':
    try:
        exit_code = main()
        input("\nPress Enter to exit...")
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        input("\nPress Enter to exit...")
        sys.exit(1)
