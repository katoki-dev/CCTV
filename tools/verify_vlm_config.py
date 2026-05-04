from utils.vlm_frame_analyzer import VLMFrameAnalyzer
import logging

logging.basicConfig(level=logging.INFO)

print("Initializing VLM Analyzer...")
try:
    from config import OLLAMA_HOST, VLM_TIER2_MODEL, OLLAMA_TIMEOUT
    analyzer = VLMFrameAnalyzer(
        ollama_host=OLLAMA_HOST,
        model=VLM_TIER2_MODEL,
        timeout=OLLAMA_TIMEOUT
    )
    print(f"Analyzer available: {analyzer.is_available()}")
    print(f"Model used: {analyzer.model}")
except Exception as e:
    print(f"Error: {e}")
