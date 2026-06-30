import os
from pathlib import Path
#  NEW WAY (Works in Pydantic v2)
from pydantic import Field
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent
UPLOADS_DIR = BASE_DIR.parent / 'uploads'
RESULTS_DIR = BASE_DIR.parent / 'results'

class Settings(BaseSettings):
    redis_url: str = Field('redis://localhost:6379/0', env='REDIS_URL')
    model_provider: str = Field('openai', env='MODEL_PROVIDER')
    openai_api_key: str | None = Field(None, env='OPENAI_API_KEY')
    anthropic_api_key: str | None = Field(None, env='ANTHROPIC_API_KEY')
    groq_api_key: str | None = Field(None, env='GROQ_API_KEY')
    # Optional: specify a Groq model name and base URL via env
    groq_model: str | None = Field(None, env='GROQ_MODEL')
    groq_base_url: str = Field('https://api.groq.com', env='GROQ_BASE_URL')
    uploads_dir: Path = UPLOADS_DIR
    results_dir: Path = RESULTS_DIR

    class Config:
        # Load .env from the repository root (two levels up from this file)
        env_file = str(Path(__file__).resolve().parents[2] / '.env')
        env_file_encoding = 'utf-8'

settings = Settings()
settings.uploads_dir.mkdir(parents=True, exist_ok=True)
settings.results_dir.mkdir(parents=True, exist_ok=True)
