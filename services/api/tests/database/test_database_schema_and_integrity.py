from sqlalchemy import inspect as sa_inspect, select
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import engine, SessionLocal
from app.models import Circle, User

# Trigger lifespan startup / table creation + seed
client = TestClient(app)


def test_core_14_database_entities_and_indexes():
    client.get('/health')
    inspector = sa_inspect(engine)
    existing_tables = set(inspector.get_table_names())
    required_tables = {
        'users',
        'members',
        'roles',
        'circles',
        'membership_renewals',
        'membership_applications',
        'payment_transactions',
        'documents',
        'certificates',
        'events',
        'notices',
        'circulars',
        'notifications',
        'audit_logs',
    }
    missing = required_tables - existing_tables
    assert not missing, f'Missing core database tables: {missing}'

    with SessionLocal() as db:
        circles = db.scalars(select(Circle)).all()
        assert len(circles) >= 1
        admin_user = db.scalar(select(User).where(User.email == 'admin@pgcb.gov.bd'))
        assert admin_user is not None
