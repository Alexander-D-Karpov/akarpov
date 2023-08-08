from pydantic_settings import BaseSettings


class AppSettings(BaseSettings):
    """General configuration of the app."""

    redirect_slug_cutoff: int = 3

    relative_base: str = "http://127.0.0.1:8000"
    database_url: str = "postgresql://postgres:postgres@127.0.0.1:5432/akarpov"

    class Config:
        env_prefix = ""
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "allow"


settings = AppSettings()
