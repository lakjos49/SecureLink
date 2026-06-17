from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    MONGO_URI: str = "mongodb://localhost:27017"
    DB_NAME: str = "securelink"
    BASE_URL: str = "http://localhost:8000"
    QR_STORAGE_PATH: str = "storage/qr"

    model_config = {"env_file": ".env"}


settings = Settings()