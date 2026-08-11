import os
import json
from pathlib import Path
from pydantic_settings import BaseSettings

CONFIG_FILE_PATH = Path(__file__).parent / "youparts_config.json"


class Settings(BaseSettings):
    PROJECT_NAME: str = "YouParts"
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")

    # Models
    RELEVANCE_MODEL: str = "llama-3.1-8b-instant"  # Fast screening
    EXTRACTION_MODEL: str = "llama-3.3-70b-versatile"  # Grounded BOM extraction

    # Rate Limiting & Cooldowns (Groq Free Tier)
    REQUEST_DELAY_SECONDS: float = 1.5
    MAX_RETRIES: int = 3

    # Regional Scraper Toggles
    ENABLE_ALIEXPRESS: bool = True
    ENABLE_SHOPEE: bool = True
    ENABLE_LAZADA: bool = True

    class Config:
        env_file = ".env"

    def save_user_config(self, updates: dict):
        """Updates runtime settings and persists them to config/youparts_config.json."""
        for key, value in updates.items():
            if hasattr(self, key):
                setattr(self, key, value)

        saved_data = {
            "GROQ_API_KEY": self.GROQ_API_KEY,
            "RELEVANCE_MODEL": self.RELEVANCE_MODEL,
            "EXTRACTION_MODEL": self.EXTRACTION_MODEL,
            "REQUEST_DELAY_SECONDS": self.REQUEST_DELAY_SECONDS,
            "MAX_RETRIES": self.MAX_RETRIES,
            "ENABLE_ALIEXPRESS": self.ENABLE_ALIEXPRESS,
            "ENABLE_SHOPEE": self.ENABLE_SHOPEE,
            "ENABLE_LAZADA": self.ENABLE_LAZADA,
        }

        CONFIG_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE_PATH, "w", encoding="utf-8") as f:
            json.dump(saved_data, f, indent=2)


def load_settings() -> Settings:
    base_settings = Settings()
    if CONFIG_FILE_PATH.exists():
        try:
            with open(CONFIG_FILE_PATH, "r", encoding="utf-8") as f:
                saved_data = json.load(f)
                for k, v in saved_data.items():
                    if hasattr(base_settings, k):
                        setattr(base_settings, k, v)
        except Exception as e:
            print(f"[YouParts] Error loading user config: {e}")
    return base_settings


settings = load_settings()
