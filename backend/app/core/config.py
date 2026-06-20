from functools import lru_cache
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    # Application
    APP_NAME: str = "SlashSure"
    APP_ENV: str = "development"
    SECRET_KEY: str
    DEBUG: bool = False
    VERSION: str = "1.0.0"

    # Database
    DATABASE_URL: str
    DATABASE_SYNC_URL: str

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # JWT
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # Wallet Encryption
    WALLET_MASTER_KEY: str

    # GenLayer
    GENLAYER_RPC_URL: str = "https://studio.genlayer.com:8443/api"
    GENLAYER_CONTRACT_ADDRESS: str = ""
    GENLAYER_DEPLOYER_PRIVATE_KEY: str = ""

    # Brevo (email)
    BREVO_API_KEY: str = ""
    BREVO_SENDER_EMAIL: str = "preciousmofeoluwa@gmail.com"
    BREVO_SENDER_NAME: str = "SlashSure"

    # Slack
    SLACK_BOT_TOKEN: str = ""
    SLACK_DEFAULT_CHANNEL: str = "#slashsure-alerts"

    # Frontend URL (for email links)
    FRONTEND_URL: str = "http://localhost:3000"

    # Network RPCs
    ETHEREUM_RPC_URL: str = ""
    BEACON_API_URL: str = "https://beaconcha.in/api/v1"
    COSMOS_RPC_URL: str = "https://rpc.cosmos.network"
    BABYLON_RPC_URL: str = "https://rpc.babylonchain.io"

    # CORS
    ALLOWED_ORIGINS: str = "http://localhost:3000"

    @property
    def cors_origins(self) -> List[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",")]

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60

    # Webhooks
    WEBHOOK_SECRET: str = ""

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
