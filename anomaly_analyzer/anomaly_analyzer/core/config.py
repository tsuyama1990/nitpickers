from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    jquants_mail_address: str
    jquants_password: str

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


settings = Settings()
