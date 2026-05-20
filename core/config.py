import os

class Settings:
    SECRET_KEY: str = os.getenv("SECRET_KEY", "fallback-secret")
    DATABASE_URL: str = os.getenv("DATABASE_URL")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60))

    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "/uploads")

settings = Settings()