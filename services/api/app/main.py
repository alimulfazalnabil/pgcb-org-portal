import logging
from contextlib import asynccontextmanager

from sqlalchemy import text
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from app.core.config import settings
from app.core.middleware import SecurityMiddleware
from app.db.session import Base, engine, SessionLocal
from app.models import *  # noqa: F401,F403
from app.routers import admin, auth, public, membership, card, notices, documents
from app.routers.event_registration import router as event_registration_router
from app.routers.events_public import router as event_public_router
from app.routers.payments import router as payments_router
from app.routers.payment_webhooks import router as payment_webhooks_router
from app.routers.certificates import router as certificates_router
from app.routers.workflows import router as workflows_router
from app.routers.secretariat import router as secretariat_router
from app.routers.helpdesk import router as helpdesk_router
from app.routers.cms import router as cms_router
from app.routers.ai import router as ai_router

from app.storage import get_storage

logger = logging.getLogger("pgcb.api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    db_target = "sqlite" if settings.database_url.startswith("sqlite") else getattr(engine.url, "host", "postgresql")
    logger.info(
        f"[STARTUP] PGCB Portal API v1.0.0-rc1 | Env: {settings.app_env} | "
        f"Storage: {settings.storage_backend} ({settings.storage_root}) | DB Host: {db_target}"
    )
    if settings.database_url.startswith("sqlite"):
        try:
            Base.metadata.create_all(bind=engine, checkfirst=True)
        except Exception as exc:
            logger.debug("SQLite table initialization notice: %s", exc)
    # Ensure storage root and subdirectories are created on persistent disk
    try:
        get_storage().ensure_root_exists()
    except Exception as exc:
        logger.warning(f"Storage root initialization warning: {exc}")

    yield
    logger.info("[SHUTDOWN] PGCB Portal API shutting down")


app = FastAPI(
    title='PGCB Organization Portal API',
    version='1.0.0-rc1',
    description='Institutional website, membership portal, CMS, events, payments, verification, observability and production API.',
    lifespan=lifespan,
)

from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    request_id = getattr(request.state, 'request_id', request.headers.get('X-Request-ID') or 'unknown')
    code_map = {
        400: 'BAD_REQUEST',
        401: 'UNAUTHORIZED',
        403: 'FORBIDDEN',
        404: 'NOT_FOUND',
        409: 'CONFLICT',
        422: 'VALIDATION_ERROR',
        429: 'RATE_LIMITED',
        500: 'INTERNAL_SERVER_ERROR',
    }
    return JSONResponse(
        status_code=exc.status_code,
        content={
            'detail': exc.detail,
            'error': {
                'code': code_map.get(exc.status_code, f'HTTP_{exc.status_code}'),
                'message': str(exc.detail),
                'request_id': request_id,
            },
        },
        headers=getattr(exc, 'headers', None),
    )


app.add_middleware(SecurityMiddleware)

# Explicit CORS origins: Never use wildcard regex in production
cors_origins = [settings.frontend_url.rstrip('/')]
if settings.allowed_origins:
    cors_origins.extend([o.strip().rstrip('/') for o in settings.allowed_origins.split(',') if o.strip()])
if settings.app_env.lower() in ('development', 'dev', 'test', 'testing', 'local'):
    cors_origins.extend(['http://localhost:3000', 'http://127.0.0.1:3000'])
cors_origins = list(dict.fromkeys(cors_origins))

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'],
    allow_headers=['Content-Type', 'Authorization', 'X-Requested-With', 'X-Request-ID'],
)

# In local/test runs with sqlite, provision tables automatically;
# Staging and production strictly use Alembic migrations (alembic upgrade head).
if settings.database_url.startswith('sqlite'):
    try:
        Base.metadata.create_all(bind=engine, checkfirst=True)
    except Exception as exc:
        logger.debug("Database schema auto-creation notice: %s", exc)


app.include_router(auth.router, prefix='/api/v1')
app.include_router(public.router, prefix='/api/v1')
app.include_router(membership.router, prefix='/api/v1')
app.include_router(card.router, prefix='/api/v1')
app.include_router(admin.router, prefix='/api/v1')
app.include_router(secretariat_router, prefix='/api/v1')
app.include_router(helpdesk_router, prefix='/api/v1')
app.include_router(event_registration_router, prefix='/api/v1')
app.include_router(event_public_router, prefix='/api/v1')
app.include_router(payments_router, prefix='/api/v1')
app.include_router(payment_webhooks_router, prefix='/api/v1')
app.include_router(certificates_router, prefix='/api/v1')
app.include_router(workflows_router, prefix='/api/v1')
app.include_router(notices.router, prefix='/api/v1')
app.include_router(documents.router, prefix='/api/v1')
app.include_router(cms_router, prefix='/api/v1')
app.include_router(ai_router, prefix='/api/v1')


@app.get('/')
@app.head('/')
def root():
    return {
        'service': 'PGCB Organization Portal API',
        'status': 'online',
        'version': '1.0.0-rc1',
        'documentation': '/docs',
        'health': '/health',
        'readiness': '/ready',
        'liveness': '/live',
    }


@app.get('/health')
def health():
    return {'status': 'ok', 'service': 'pgcb-api', 'version': '1.0.0-rc1', 'environment': settings.app_env}




@app.get('/live')
def live():
    return {'status': 'alive', 'service': 'pgcb-api', 'version': '1.0.0-rc1'}

@app.get('/metrics')
def metrics(request: Request):
    if not settings.metrics_enabled:
        return Response(status_code=404)
    if settings.is_production_like and settings.metrics_token:
        auth_hdr = request.headers.get('Authorization', '')
        if auth_hdr != f'Bearer {settings.metrics_token}':
            return Response(status_code=401)
    from app.core.metrics import render_metrics
    body, media_type = render_metrics()
    return Response(content=body, media_type=media_type)

@app.get('/ready')
def ready():
    db = SessionLocal()
    try:
        db.execute(text('SELECT 1'))
        return {'status': 'ready', 'database': 'ok'}
    except Exception as exc:
        logger.error(f"[READINESS ERROR] Database health check failed: {exc}")
        return Response(
            content='{"status":"not_ready","database":"error"}',
            status_code=503,
            media_type='application/json'
        )
    finally:
        db.close()
