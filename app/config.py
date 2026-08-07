from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables or .env file."""

    # Telegram Bot
    TELEGRAM_BOT_TOKEN: str = Field(default="123456789:AAG_MockBotTokenForTestingPurpose", description="Telegram Bot API Token")

    # Firebase Credentials
    FIREBASE_PROJECT_ID: Optional[str] = Field(default=None, description="Firebase Project ID")
    FIREBASE_CLIENT_EMAIL: Optional[str] = Field(default=None, description="Firebase Client Email")
    FIREBASE_PRIVATE_KEY: Optional[str] = Field(default=None, description="Firebase Private Key")
    FIREBASE_STORAGE_BUCKET: Optional[str] = Field(default=None, description="Firebase Storage Bucket")
    FIREBASE_DATABASE_URL: Optional[str] = Field(default=None, description="Firebase Realtime Database URL")
    FIREBASE_CREDENTIALS_PATH: Optional[str] = Field(default=None, description="Path to serviceAccountKey.json if used")

    # AI API Keys
    AI_API_KEY: Optional[str] = Field(default=None, description="Gemini / AI Provider API Key")
    AI_MODEL_NAME: str = Field(default="gemini-1.5-flash", description="Default Vision & Text AI Model")

    # Application Behavior
    TIMEZONE: str = Field(default="Asia/Jakarta", description="Default user timezone")
    DEBUG: bool = Field(default=False, description="Debug mode")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
