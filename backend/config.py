import os
from pydantic_settings import BaseSettings

# Load .env from project root
ENV_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")


class Settings(BaseSettings):
    ANTHROPIC_API_KEY: str
    FAL_KEY: str
    ELEVENLABS_API_KEY: str
    KIE_AI_API_KEY: str = ""
    ELEVENLABS_VOICE_ID: str = "JBFqnCBsd6RMkjVDRZzb"
    WHISPER_MODEL_SIZE: str = "base"
    WORK_DIR: str = os.path.join(os.path.dirname(__file__), "workspace")

    # Supabase (optional — history features disabled if not set)
    SUPABASE_URL: str = ""
    SUPABASE_SERVICE_KEY: str = ""

    model_config = {"env_file": ENV_PATH, "env_file_encoding": "utf-8"}


settings = Settings()

# fal.ai reads FAL_KEY from environment
os.environ["FAL_KEY"] = settings.FAL_KEY
