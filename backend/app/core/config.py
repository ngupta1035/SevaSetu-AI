from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    UPLOAD_DIR: str = "uploads"
    MODEL_PATH: str = "../ai/models/sevasetu_road_damage.pt"
    AI_CONF_THRESHOLD: float = 0.25

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
