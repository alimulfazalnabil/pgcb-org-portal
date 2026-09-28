from __future__ import annotations

from urllib.parse import quote_plus

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _normalize_origin_url(raw: str) -> str:
    val = (raw or '').strip().rstrip('/')
    if not val:
        return val
    if val.startswith(('http://', 'https://')):
        return val
    if val.startswith(('localhost', '127.0.0.1')):
        return f'http://{val}'
    return f'https://{val}'


class Settings(BaseSettings):
    app_env: str = 'development'
    database_url: str = 'sqlite:///./pgcb_portal.db'
    db_host: str | None = None
    db_port: int = 5432
    db_name: str = 'pgcb_portal'
    db_user: str | None = None
    db_password: str | None = None
    db_sslmode: str = 'prefer'
    secret_key: str | None = None
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
    storage_root: str = './storage'
    mfa_encryption_key: str | None = None
    rate_limit_enabled: bool = True
    redis_rate_limit_enabled: bool = False
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
    payment_mode: str = 'sandbox'
    bkash_app_key: str | None = None
    bkash_app_secret: str | None = None
    bkash_username: str | None = None
    bkash_password: str | None = None
    nagad_merchant_id: str | None = None
    sslcommerz_store_id: str | None = None
    sslcommerz_store_password: str | None = None
    payment_webhook_secret: str | None = None
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')

    @property
    def is_production_like(self) -> bool:
        return self.app_env.lower() in ('production', 'staging')

    @model_validator(mode='after')
    def validate_production(self) -> 'Settings':
        if self.db_host and self.db_user and self.db_password:
            sslmode = self.db_sslmode or ('disable' if self.db_host in ('localhost', '127.0.0.1') else 'require')
            self.database_url = (
                f'postgresql+psycopg://{quote_plus(self.db_user)}:{quote_plus(self.db_password)}'
                f'@{self.db_host}:{self.db_port}/{self.db_name}?sslmode={sslmode}'
            )
        if self.database_url:
            if self.database_url.startswith('postgres://'):
                self.database_url = self.database_url.replace('postgres://', 'postgresql+psycopg://', 1)
            elif self.database_url.startswith('postgresql://'):
                self.database_url = self.database_url.replace('postgresql://', 'postgresql+psycopg://', 1)
            elif self.database_url.startswith('postgresql+psycopg2://'):
                self.database_url = self.database_url.replace('postgresql+psycopg2://', 'postgresql+psycopg://', 1)

        if self.redis_host and self.redis_password:
            self.redis_url = (
                f'{self.redis_scheme}://:{quote_plus(self.redis_password)}@{self.redis_host}:{self.redis_port}/0'
            )

        if self.frontend_url:
            self.frontend_url = _normalize_origin_url(self.frontend_url)

        if self.allowed_origins:
            normalized_list = [
                _normalize_origin_url(origin)
                for origin in self.allowed_origins.split(',')
                if origin.strip()
            ]
            self.allowed_origins = ','.join(normalized_list)

        if self.app_env.lower() in ('production', 'staging'):
            if self.jwt_secret.startswith('dev-only-secret') or len(self.jwt_secret) < 32:
                raise ValueError(
                    'JWT_SECRET must be configured with at least 32 characters in staging/production.'
                )
            if self.storage_backend.lower() not in ('local', 'filesystem', 'persistent_disk'):
                raise ValueError(
                    "Staging/Production storage configuration invalid: STORAGE_BACKEND must be 'local', 'filesystem', or 'persistent_disk'."
                )
            if self.storage_backend.lower() == 'persistent_disk' and (not self.storage_root or self.storage_root == './storage'):
                self.storage_root = '/var/data/uploads'
            elif not self.storage_root:
                self.storage_root = './storage'

        return self



settings = Settings()
