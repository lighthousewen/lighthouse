from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://lighthouse:lighthouse_dev@localhost:5432/lighthouse"
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    max_context_messages: int = 50

    model_config = {
        "env_file": str(Path(__file__).parent.parent.parent / ".env"),
        "extra": "ignore",
    }


settings = Settings()
