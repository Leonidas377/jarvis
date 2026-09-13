# ==========================================================================
# JARVIS Server Configuration
# ==========================================================================

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings:
    PROJECT_NAME: str = "J.A.R.V.I.S. Core Backend"
    VERSION: str = "14.8.0"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
# Security
    JWT_SECRET: str = os.getenv("JARVIS_JWT_SECRET", "stark-quantum-neural-secret-key-0499-omega")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    LLM_ENCRYPTION_KEY: str = os.getenv("JARVIS_LLM_ENCRYPTION_KEY", "")
    
    # Database
    DATABASE_FILE: Path = BASE_DIR / "jarvis_vault.db"
    
    # AI Provider
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    DEFAULT_MODEL: str = os.getenv("JARVIS_DEFAULT_MODEL", "meta/llama-3.2-11b-vision-instruct")
    USE_LOCAL_AI_FALLBACK: bool = True

# Auto-load .env file if present
env_file = BASE_DIR / ".env"
if env_file.exists():
    try:
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    k, v = k.strip(), v.strip().strip("'\"")
                    if k not in os.environ:
                        os.environ[k] = v
    except Exception:
        pass

settings = Settings()

