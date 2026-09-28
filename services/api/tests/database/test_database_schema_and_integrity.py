from sqlalchemy import inspect as sa_inspect, select
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import engine, SessionLocal
from app.models import Circle, User


def test_core_21_database_entities_and_indexes():
    with TestClient(app) as client:
        res = client.get('/health')
        assert res.status_code == 200

    inspector = sa_inspect(engine)
    existing_tables = set(inspector.get_table_names())
    required_tables = {
        'users',
        'roles',
        'permissions',
        'members',
        'grid_circles',
        'memberships',
        'membership_applications',
        'application_reviews',
        'payments',
        'payment_transactions',
        'documents',
        'certificates',
        'events',
        'event_registrations',
        'news',
        'notices',
        'circulars',
        'media_assets',
        'notifications',
        'notification_templates',
        'audit_logs',
    }
    missing = required_tables - existing_tables
    assert not missing, f'Missing core database tables: {missing}'

    with SessionLocal() as db:
        circles = db.scalars(select(Circle)).all()
        assert len(circles) >= 1
        users = db.scalars(select(User)).all()
        assert len(users) >= 1
