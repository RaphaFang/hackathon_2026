from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

OLLAMA_MODEL = "llama3:8b"

# Set to False to disable all Ollama/AI calls (useful when Ollama is not running)
AI_ENABLED = True
