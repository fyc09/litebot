"""Configuration for the Agent Application"""
import sys
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
from pathlib import Path
import shutil


_ENV_PATH = Path.cwd() / ".env"
_ENV_EXAMPLE_PATH = Path(__file__).parent / ".env.example"

if not _ENV_PATH.exists():
    shutil.copyfile(_ENV_EXAMPLE_PATH, _ENV_PATH)
    print(".env was missing, so .env.example has been copied. Please review and update .env with your own settings.")
    sys.exit(1)


class Settings(BaseSettings):
    """Application settings"""
    
    model_config = SettingsConfigDict(
        env_file=_ENV_PATH,
        case_sensitive=False,
        extra="ignore"
    )
    
    # OpenAI Configuration
    openai_api_key: str = ""
    openai_model: str = "gpt-4-vision-preview"
    openai_base_url: Optional[str] = None
    
    # Application Configuration
    debug: bool = False
    app_title: str = "Agent Application"
    
    # Shell Configuration
    bash_path: str = "bash"  # Path to bash executable, defaults to "bash" in PATH
    
    # CORS Configuration
    cors_origins: list = []


settings = Settings()
