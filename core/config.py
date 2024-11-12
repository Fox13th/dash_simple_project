import os
from functools import lru_cache
from pydantic_settings import BaseSettings

from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    redis_host: str = '127.0.0.1'
    redis_port: int = 6379
    redis_expiration: int = 300

    socket_host: str = '127.0.0.1'
    socket_port: int = 5002

    docs_directory: str
    lang_model: str
    lang_list: str

    clear_queue: bool = True

    debug: bool = os.environ.get('DEBUG')

    class Config:
        env_file = "../.env"
        extra = "ignore"


@lru_cache(maxsize=None)
def get_settings(env_file: str = None):
    """Получаем настройки приложения, сохраняя в кэш."""
    return Settings(_env_file=env_file)
