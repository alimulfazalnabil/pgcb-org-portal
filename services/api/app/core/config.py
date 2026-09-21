from __future__ import annotations

from urllib.parse import quote_plus

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = 'development'
    database_url: str = 'sqlite:///./pgcb_portal.db'
    db_host: str | None = None
    db_port: int = 5432
    db_name: str = 'pgcb_portal'
    db_user: str | None = None
    db_password: str | None = None
    jwt_secret: str = 'dev-only-secret-change-me-please-use-a-32-byte-random-secret'
    jwt_expire_minutes: int = 60
    cookie_name: str = 'pgcb_access_token'
    frontend_url: str = 'http://localhost:3000'
    allowed_origins: str | None = None
    password_reset_hours: int = 2
    email_verification_hours: int = 24
    require_email_verification: bool = False
    max_upload_mb: int = 10
    storage_backend: str = 'local'
    azure_storage_connection_string: str | None = None
    azure_storage_account_url: str | None = None
    azure_storage_container: str = 'pgcb-files'
    azure_storage_use_managed_identity: bool = True
    azure_key_vault_uri: str | None = None
    mfa_encryption_key: str | None = None
    rate_limit_enabled: bool = True
    redis_rate_limit_enabled: bool = True
    redis_url: str = 'redis://localhost:6379/0'
    redis_host: str | None = None
    redis_port: int = 6379
    redis_password: str | None = None
    redis_scheme: str = 'redis'
    redis_tls_verify: bool = True
    trusted_proxy_count: int = 1
    metrics_enabled: bool = True
    metrics_token: str | None = None
    log_level: str = 'INFO'
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')

    @model_validator(mode='after')
    def validate_production(self) -> 'Settings':
        if self.db_host and self.db_user and self.db_password:
            self.database_url = (
                f'postgresql+psycopg://{quote_plus(self.db_user)}:{quote_plus(self.db_password)}'
                f'@{self.db_host}:{self.db_port}/{self.db_name}?sslmode=require'
            )
        if self.redis_host and self.redis_password:
            self.redis_url = (
                f'{self.redis_scheme}://:{quote_plus(self.redis_password)}@{self.redis_host}:{self.redis_port}/0'
            )
        if self.app_env.lower() == 'production':
            if self.jwt_secret.startswith('dev-only-secret') or len(self.jwt_secret) < 32:
                raise ValueError('JWT_SECRET must be a strong 32+ character secret in production')
            if self.storage_backend == 'azure' and not (self.azure_storage_account_url or self.azure_storage_connection_string):
                raise ValueError('Azure Blob Storage requires AZURE_STORAGE_ACCOUNT_URL or connection string')
            if self.require_email_verification is False:
                # Explicitly allowed, but keep production configuration visible in docs/runbooks.
                pass
        return self


settings = Settings()
