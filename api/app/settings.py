from pydantic import BaseSettings


class Settings(BaseSettings):
    """Переменные `APP_*` перезаписывают поля этого класса."""

    postgres_host = "localhost"
    postgres_port = 5432
    postgres_user = "user"
    postgres_password = "secret"
    postgres_db = "db"
    subtract_interval = 600

    @property
    def pg_dsn(self) -> str:
        return (
            f"postgres://{self.postgres_user}:{self.postgres_password}@"
            f"{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )
