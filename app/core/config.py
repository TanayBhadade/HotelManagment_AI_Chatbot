from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # --- App Config ---
    PROJECT_NAME: str = "Grand Hotel AI"
    API_V1_STR: str = "/api/v1"

    # --- Database ---
    DATABASE_URL: str = "sqlite:///./hotel.db"

    # --- Security ---
    # This will read SECRET_KEY from .env
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # --- AI Credentials ---
    GROQ_API_KEY: str

    # --- Email Config (Matches your .env now) ---
    # We use aliases so python variables stay clean but map to your specific .env names
    EMAIL_SENDER: str | None = None
    EMAIL_MANAGER: str | None = None
    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 587

    class Config:
        env_file = ".env"
        # 🚨 THIS IS THE FIX:
        # It tells Pydantic: "If you see 'google_api_key' in .env but not here, just ignore it. Don't crash."
        extra = "ignore"

    # Create global instance


settings = Settings()