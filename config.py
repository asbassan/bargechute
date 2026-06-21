import os
from pathlib import Path

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "bargechute.db"

# Path to the Barge repository — override with BARGE_PATH env var
BARGE_PATH = Path(os.getenv("BARGE_PATH", r"D:\AIResearchAndStudies\AICoding\Barge"))

# Ollama settings
MODEL = os.getenv("BARGECHUTE_MODEL", "qwen2.5-coder:7b")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
