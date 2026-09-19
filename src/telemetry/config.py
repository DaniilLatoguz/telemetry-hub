from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="TELEMETRY_")

    database_url: str = "postgresql+psycopg://telemetry:telemetry@localhost:5432/telemetry"
    serial_port: str = "/dev/pts/4"
    serial_baud: int = 115200
    batch_size: int = 50
    batch_timeout: float = 1.0

settings = Settings()