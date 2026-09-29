from datetime import datetime
import pytest
from sqlalchemy import inspect as sa_inspect, select
from sqlalchemy.exc import IntegrityError
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import engine, SessionLocal
from app.models import Circle, Member, Membership, MembershipApplication, Payment, User
from scripts.load_test_pgcb import run_concurrency_tiers, run_realistic_db_benchmark


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


def test_unique_constraints_and_transaction_atomicity():
    """Verify unique constraints and full transaction rollback on integrity violation."""
    with SessionLocal() as db:
        first_user = db.scalar(select(User).limit(1))
        assert first_user is not None
        duplicate_email = first_user.email

        # Attempting to insert a user with duplicate email must fail and roll back cleanly
        with pytest.raises(IntegrityError):
            dup_user = User(
                name_bn='ডুপ্লিকেট ব্যবহারকারী',
                email=duplicate_email,
                phone='01799998888',
                password_hash='invalid-hash',
                role_id=first_user.role_id,
                is_active=True,
            )
            db.add(dup_user)
            db.flush()
        db.rollback()

        # Verify database session remains usable and no partial row was persisted
        count_with_email = len(db.scalars(select(User).where(User.email == duplicate_email)).all())
        assert count_with_email == 1


def test_1500_member_capacity_and_250_user_concurrency():
    """
    Validate RC1 synthetic capacity & concurrency targets:
    - 1,500 members
    - 500+ applications
    - 2,000+ payment records
    - 5,000+ notifications
    - 1,000+ documents
    - 10,000+ audit records
    - Concurrency tiers: 50, 100, and 250 concurrent users with 0% error rate
    """
    db_report = run_realistic_db_benchmark(scale=1.0)
    counts = db_report['dataset_counts']
    assert counts['members'] == 1500
    assert counts['membership_records'] == 1500
    assert counts['applications'] >= 500
    assert counts['payments'] >= 2000
    assert counts['notifications'] >= 5000
    assert counts['documents'] >= 1000
    assert counts['audit_logs'] >= 10000
    assert db_report['slow_queries_count'] == 0

    with TestClient(app) as client:
        concurrency_report = run_concurrency_tiers(client, concurrency_tiers=(50, 100, 250))

    for tier_key, expected_users in (
        ('50_concurrent_users', 50),
        ('100_concurrent_users', 100),
        ('250_concurrent_users', 250),
    ):
        tier_data = concurrency_report[tier_key]
        assert tier_data['concurrent_users'] == expected_users
        assert tier_data['requests_completed'] == expected_users
        assert tier_data['error_rate'] == 0.0

