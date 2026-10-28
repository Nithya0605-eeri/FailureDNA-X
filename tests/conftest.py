import os
import sys
from pathlib import Path

# Tests never call the real API: an empty key makes the app use the offline mock.
os.environ["NEBIUS_API_KEY"] = ""
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))