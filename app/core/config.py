import json
from typing import List, Union
from pydantic import BeforeValidator, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing_extensions import Annotated

def parse_cors(v: Union[str, List[str]]) -> List[str]:
    if isinstance(v, str) and not v.startswith("["):
        return [i.strip() for i in v.split(",")]
    elif isinstance(v, (list, str)):
        try:
            return json.loads(v) if isinstance(v, str) else v
        except Exception:
            return []
    return v

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_ignore_empty=True, extra="ignore"
    )

    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "EDULAB"

    # CORS
    BACKEND_CORS_ORIGINS: Annotated[
        List[str], BeforeValidator(parse_cors)
    ] = [
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "https://main.d19ospd1qs6k2p.amplifyapp.com",
        "https://d19ospd1qs6k2p.amplifyapp.com"
    ]

    # Database URLs
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/edulab"
    SYNC_DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/edulab"

    # Firebase Authentication
    FIREBASE_CREDENTIALS_PATH: str | None = None
    FIREBASE_CREDENTIALS_JSON: str | None = None
    
    # Development Flags
    DEV_MODE: bool = True
    MOCK_FIREBASE_AUTH: bool = False

    @field_validator("DATABASE_URL")
    @classmethod
    def assemble_db_connection(cls, v: str) -> str:
        # If psycopg2 is specified in .env, automatically replace it with asyncpg for async pooling
        if v.startswith("postgresql+psycopg2://"):
            return v.replace("postgresql+psycopg2://", "postgresql+asyncpg://", 1)
        if v.startswith("postgresql://"):
            return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v

settings = Settings()
