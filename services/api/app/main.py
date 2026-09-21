from sqlalchemy import text
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from app.core.config import settings
from app.core.middleware import SecurityMiddleware
from app.db.session import Base, engine, SessionLocal
from app.models import *  # noqa: F401,F403
from app.routers import admin, auth, public, membership, card
from app.routers.event_registration import router as event_registration_router
from app.routers.events_public import router as event_public_router
from app.routers.payments import router as payments_router
from app.routers.payment_webhooks import router as payment_webhooks_router
from app.routers.certificates import router as certificates_router
from app.routers.workflows import router as workflows_router

app = FastAPI(
    title='PGCB Organization Portal API',
    version='1.0.0-rc1',
    description='Institutional website, membership portal, CMS, events, payments, verification, observability and Azure production API.',
)

app.add_middleware(SecurityMiddleware)

cors_origins = [
    settings.frontend_url.rstrip('/'),
    'http://localhost:3000',
    'http://127.0.0.1:3000',
]
if settings.allowed_origins:
    cors_origins.extend([o.strip().rstrip('/') for o in settings.allowed_origins.split(',') if o.strip()])
cors_origins = list(dict.fromkeys(cors_origins))

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_origin_regex=r'https://.*\.onrender\.com',
    allow_credentials=True,
    allow_methods=['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'],
    allow_headers=['Content-Type', 'Authorization', 'X-Requested-With', 'X-Request-ID'],
)

# In test and local sqlite environments, automatically provision tables for test suites;
# Production environments use Alembic preDeployCommand (alembic upgrade head).
if settings.app_env.lower() in ('development', 'test') and settings.database_url.startswith('sqlite'):
    Base.metadata.create_all(bind=engine)

app.include_router(auth.router, prefix='/api/v1')
app.include_router(public.router, prefix='/api/v1')
app.include_router(membership.router, prefix='/api/v1')
app.include_router(card.router, prefix='/api/v1')
app.include_router(admin.router, prefix='/api/v1')
app.include_router(event_registration_router, prefix='/api/v1')
app.include_router(event_public_router, prefix='/api/v1')
app.include_router(payments_router, prefix='/api/v1')
app.include_router(payment_webhooks_router, prefix='/api/v1')
app.include_router(certificates_router, prefix='/api/v1')
app.include_router(workflows_router, prefix='/api/v1')

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
    if settings.app_env.lower() == 'production' and settings.metrics_token:
        auth = request.headers.get('Authorization', '')
        if auth != f'Bearer {settings.metrics_token}':
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
    finally:
        db.close()
