from __future__ import annotations

import pytest
from app.db.session import Base, engine
from app.db.seed import main as seed_main


from app.core.config import settings
settings.app_env = 'test'
settings.rate_limit_enabled = False


from sqlalchemy import inspect, text

@pytest.fixture(scope="session", autouse=True)
def initialize_test_database():
    """Ensure database schema and baseline demo fixtures exist before test suite runs."""
    Base.metadata.create_all(bind=engine)
    try:
        inspector = inspect(engine)
        with engine.connect() as conn:
            if 'membership_renewals' in inspector.get_table_names():
                cols = {c['name'] for c in inspector.get_columns('membership_renewals')}
                if 'duration_years' not in cols:
                    conn.execute(text("ALTER TABLE membership_renewals ADD COLUMN duration_years INTEGER DEFAULT 1"))
                if 'notes' not in cols:
                    conn.execute(text("ALTER TABLE membership_renewals ADD COLUMN notes TEXT"))
            if 'member_documents' in inspector.get_table_names():
                cols = {c['name'] for c in inspector.get_columns('member_documents')}
                if 'reviewer_note' not in cols:
                    conn.execute(text("ALTER TABLE member_documents ADD COLUMN reviewer_note TEXT"))
            conn.commit()
    except Exception:
        pass
    seed_main()
    yield
