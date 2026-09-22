from __future__ import annotations

import pytest
from app.db.session import Base, engine
from app.db.seed import main as seed_main


from app.core.config import settings
settings.app_env = 'test'
settings.rate_limit_enabled = False


@pytest.fixture(scope="session", autouse=True)
def initialize_test_database():
    """Ensure database schema and baseline demo fixtures exist before test suite runs."""
    Base.metadata.create_all(bind=engine)
    seed_main()
    yield
