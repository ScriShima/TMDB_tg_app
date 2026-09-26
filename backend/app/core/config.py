from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    bot_token: str
    tmdb_api_key: str
    database_url: str
    app_env: str = "development"
    webapp_url: str = "https://example.com"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    dev_auth_enabled: bool = False
    dev_user_id: int = 1

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

settings = Settings()