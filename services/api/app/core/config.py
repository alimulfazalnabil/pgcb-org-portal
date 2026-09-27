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
    if '.' in val:
        return f'https://{val}'
    # Bare Render service hostname from `fromService: property: host`
    return f'https://{val}.onrender.com'


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
    storage_root: str = './storage'
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

    @property
    def is_production_like(self) -> bool:
        return self.app_env.lower() in ('production', 'staging')

    @model_validator(mode='after')
    def validate_production(self) -> 'Settings':
        if self.db_host and self.db_user and self.db_password:
            self.database_url = (
                f'postgresql+psycopg://{quote_plus(self.db_user)}:{quote_plus(self.db_password)}'
                f'@{self.db_host}:{self.db_port}/{self.db_name}?sslmode=require'
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
                    'JWT_SECRET must be configured with at least 32 characters in staging/production. '
                    'Configure JWT_SECRET in your Render Environment or Blueprint shared-secrets.'
                )
            if self.storage_backend != 'persistent_disk':
                raise ValueError(
                    "Staging/Production storage configuration invalid: STORAGE_BACKEND must be set to 'persistent_disk' "
                    "for Render Persistent Disk storage."
                )
            if not self.storage_root or self.storage_root == './storage':
                self.storage_root = '/var/data/uploads'

        return self


settings = Settings()
