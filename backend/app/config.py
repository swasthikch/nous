"""Application Configuration Module for NOUS."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Base directory paths
BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BACKEND_DIR.parent
ENV_FILE = BACKEND_DIR / ".env"

# Load .env if present
if ENV_FILE.exists():
    load_dotenv(dotenv_path=ENV_FILE)
else:
    load_dotenv()


class Settings:
    PROJECT_NAME: str = "NOUS - Personal AI Assistant"
    PROJECT_ROOT: Path = PROJECT_ROOT
    BACKEND_DIR: Path = BACKEND_DIR
    VERSION: str = "0.1.0"
    HOST: str = os.getenv("HOST", "127.0.0.1")
    PORT: int = int(os.getenv("PORT", "8000"))

    # Ollama settings
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")

    # CORS settings
    CORS_ORIGINS: list[str] = [
        origin.strip()
        for origin in os.getenv(
            "CORS_ORIGINS",
            "http://localhost:8000,http://127.0.0.1:8000,http://localhost:3000,http://127.0.0.1:5500",
        ).split(",")
        if origin.strip()
    ]

    # Google OAuth / Gmail settings
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET", "")
    GOOGLE_REDIRECT_URI: str = os.getenv("GOOGLE_REDIRECT_URI", "http://127.0.0.1:8000/api/email/auth/callback")
    GOOGLE_TOKEN_FILE: Path = PROJECT_ROOT / "data" / "credentials" / "google_token.json"

    # GitHub & Project settings (Phase 9)
    GITHUB_TOKEN: str = os.getenv("GITHUB_TOKEN", "")
    GITHUB_DEFAULT_REPO: str = os.getenv("GITHUB_DEFAULT_REPO", "nous-assistant/core")

    # Financial Market Intelligence settings (Phase 10 & 11)
    MARKET_DB_PATH: Path = PROJECT_ROOT / "data" / "database" / "nous_market.db"
    MARKET_CACHE_TTL: int = int(os.getenv("MARKET_CACHE_TTL", "60"))
    MARKET_DEMO_MODE: bool = os.getenv("MARKET_DEMO_MODE", "false").lower() in ("true", "1", "yes")

    # Web Research Engine settings (Phase 12)
    RESEARCH_DB_PATH: Path = PROJECT_ROOT / "data" / "database" / "nous_research.db"
    TAVILY_API_KEY: str = os.getenv("TAVILY_API_KEY", "")
    BRAVE_API_KEY: str = os.getenv("BRAVE_API_KEY", "")

    # Computer & Task Automation settings (Phase 13)
    WORKSPACE_DIR: Path = PROJECT_ROOT / "workspace"
    AUTOMATION_DB_PATH: Path = PROJECT_ROOT / "data" / "database" / "nous_automation.db"
    COMMAND_TIMEOUT_SECONDS: int = int(os.getenv("COMMAND_TIMEOUT_SECONDS", "10"))
    REQUIRE_COMMAND_APPROVAL: bool = os.getenv("REQUIRE_COMMAND_APPROVAL", "true").lower() in ("true", "1", "yes")

    # Security Vault & Privacy settings (Phase 14)
    SECURITY_DB_PATH: Path = PROJECT_ROOT / "data" / "database" / "nous_security.db"
    PRIVACY_SETTINGS_FILE: Path = PROJECT_ROOT / "data" / "privacy_settings.json"
    OFFLINE_LOCKDOWN: bool = os.getenv("OFFLINE_LOCKDOWN", "false").lower() in ("true", "1", "yes")
    STRICT_PII_REDACTION: bool = os.getenv("STRICT_PII_REDACTION", "true").lower() in ("true", "1", "yes")


settings = Settings()
