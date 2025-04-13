from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    SANSAD_BASE_PATH: str = "/sansad"

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
