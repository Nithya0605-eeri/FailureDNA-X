"""All settings, read from environment variables or the .env file in the repo root."""
import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

# Load .env from the repo root (one folder above backend/). Real environment variables win.
load_dotenv(Path(__file__).resolve().parent.parent / ".env")


def _origins() -> list[str]:
    raw = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
    return [o.strip() for o in raw.split(",") if o.strip()]


@dataclass
class Settings:
    # --- Nemotron on Nebius Token Factory ---
    nebius_api_key: str = os.getenv("NEBIUS_API_KEY", "")
    nebius_base_url: str = os.getenv("NEBIUS_BASE_URL", "https://api.tokenfactory.nebius.com/v1/")
    nemotron_model: str = os.getenv("NEMOTRON_MODEL", "nvidia/nemotron-3-super-120b-a12b")
    llm_temperature: float = float(os.getenv("LLM_TEMPERATURE", "0.2"))
    llm_max_tokens: int = int(os.getenv("LLM_MAX_TOKENS", "2048"))
    llm_timeout_s: float = float(os.getenv("LLM_TIMEOUT_S", "60"))
    # --- investigation rules (shared with your teammate's engine) ---
    stop_threshold: float = float(os.getenv("STOP_THRESHOLD", "0.9"))
    max_steps: int = int(os.getenv("MAX_STEPS", "6"))
    max_cost: int = int(os.getenv("MAX_COST", "18"))
    # --- web ---
    cors_origins: list[str] = field(default_factory=_origins)

    @property
    def llm_mode(self) -> str:
        """'nemotron' when a key is set, otherwise the offline 'mock_llm'."""
        return "nemotron" if self.nebius_api_key else "mock_llm"


settings = Settings()