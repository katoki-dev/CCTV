import os
import psutil
import config

class SystemOptimizer:
    """Extracts system details and auto-optimizes application configuration."""
    
    @staticmethod
    def extract_specs():
        """Retrieve system hardware specifications."""
        try:
            # Memory in GB
            ram_bytes = psutil.virtual_memory().total
            ram_gb = round(ram_bytes / (1024 ** 3), 2)
            
            # CPU Cores
            cpu_physical = psutil.cpu_count(logical=False)
            cpu_logical = psutil.cpu_count(logical=True)
            
            specs = {
                "ram_gb": ram_gb,
                "cpu_physical": cpu_physical,
                "cpu_logical": cpu_logical
            }
            return specs
        except Exception as e:
            print(f"⚠️ Warning: Could not extract system specs: {e}")
            return {"ram_gb": 8.0, "cpu_physical": 4, "cpu_logical": 8} # Fallback defaults

    @staticmethod
    def apply_auto_optimization():
        """Apply dynamic configuration based on system specs."""
        specs = SystemOptimizer.extract_specs()
        
        print("\n" + "="*50)
        print("SYSTEM DETAIL EXTRACTOR & AUTO-OPTIMIZATION")
        print("="*50)
        print(f"Detected RAM: {specs['ram_gb']} GB")
        print(f"Detected CPU Cores: {specs['cpu_physical']} Physical / {specs['cpu_logical']} Logical")
        
        # Check for low-end hardware (<= 8GB RAM is considered low for this AI workload)
        is_low_end = specs['ram_gb'] <= 8.5
        
        print("\n--- Applying Optimizations ---")
        if is_low_end:
            print("WARNING: LOW-RESOURCE HARDWARE DETECTED (<= 8GB RAM)")
            print("Applying strict performance limits to prevent lag and crashes...")
            
            # Force config overrides
            config.LOW_POWER_MODE = True
            config.MAX_CONCURRENT_DETECTIONS = 1
            config.FRAME_SKIP_RATE = max(config.FRAME_SKIP_RATE, 10)
            config.VIDEO_FRAME_SKIP_RATE = max(config.VIDEO_FRAME_SKIP_RATE, 12)
            
            # Ensure heavy AI models are disabled
            config.OLLAMA_ENABLED = False
            config.VLM_ENABLED = False
            config.LEARNING_ENABLED = False
            
            print("-> Forced LOW_POWER_MODE = True")
            print("-> Enforced 1-Camera Maximum Limit")
            print(f"-> Frame Skip Rate set to {config.FRAME_SKIP_RATE}")
            print("-> Disabled VLM, LLM, and Self-Learning modules")
        else:
            print("SUCCESS: SUFFICIENT HARDWARE DETECTED (> 8GB RAM)")
            print("System will use standard configuration values.")
            
        print("="*50 + "\n")
        
        return specs
