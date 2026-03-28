from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://app:app@localhost:5432/app"
    app_name: str = "{{ project_slug }}"
    debug: bool = True

    model_config = {% raw %}{"env_file": ".env"}{% endraw %}


settings = Settings()
