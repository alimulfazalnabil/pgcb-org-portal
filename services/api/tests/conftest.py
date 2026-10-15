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
                if 'title' not in cols:
                    conn.execute(text("ALTER TABLE member_documents ADD COLUMN title VARCHAR(255)"))
                if 'file_size' not in cols:
                    conn.execute(text("ALTER TABLE member_documents ADD COLUMN file_size INTEGER DEFAULT 0"))
                if 'version' not in cols:
                    conn.execute(text("ALTER TABLE member_documents ADD COLUMN version INTEGER DEFAULT 1"))
                if 'verified_at' not in cols:
                    conn.execute(text("ALTER TABLE member_documents ADD COLUMN verified_at DATETIME"))
                if 'expires_at' not in cols:
                    conn.execute(text("ALTER TABLE member_documents ADD COLUMN expires_at DATETIME"))
                if 'deleted_at' not in cols:
                    conn.execute(text("ALTER TABLE member_documents ADD COLUMN deleted_at DATETIME"))
            if 'certificates' in inspector.get_table_names():
                cols = {c['name'] for c in inspector.get_columns('certificates')}
                if 'title_en' not in cols:
                    conn.execute(text("ALTER TABLE certificates ADD COLUMN title_en VARCHAR(500)"))
                if 'certificate_type' not in cols:
                    conn.execute(text("ALTER TABLE certificates ADD COLUMN certificate_type VARCHAR(50) DEFAULT 'MEMBERSHIP'"))
                if 'status' not in cols:
                    conn.execute(text("ALTER TABLE certificates ADD COLUMN status VARCHAR(30) DEFAULT 'VALID'"))
                if 'revoked_at' not in cols:
                    conn.execute(text("ALTER TABLE certificates ADD COLUMN revoked_at DATETIME"))
                if 'revoked_by_id' not in cols:
                    conn.execute(text("ALTER TABLE certificates ADD COLUMN revoked_by_id INTEGER"))
                if 'revocation_reason' not in cols:
                    conn.execute(text("ALTER TABLE certificates ADD COLUMN revocation_reason TEXT"))
            if 'events' in inspector.get_table_names():
                cols = {c['name'] for c in inspector.get_columns('events')}
                if 'category' not in cols:
                    conn.execute(text("ALTER TABLE events ADD COLUMN category VARCHAR(50) DEFAULT 'SEMINAR'"))
                if 'description_en' not in cols:
                    conn.execute(text("ALTER TABLE events ADD COLUMN description_en TEXT"))
                if 'start_date' not in cols:
                    conn.execute(text("ALTER TABLE events ADD COLUMN start_date DATETIME"))
                if 'end_date' not in cols:
                    conn.execute(text("ALTER TABLE events ADD COLUMN end_date DATETIME"))
                if 'start_time' not in cols:
                    conn.execute(text("ALTER TABLE events ADD COLUMN start_time VARCHAR(30)"))
                if 'end_time' not in cols:
                    conn.execute(text("ALTER TABLE events ADD COLUMN end_time VARCHAR(30)"))
                if 'venue' not in cols:
                    conn.execute(text("ALTER TABLE events ADD COLUMN venue VARCHAR(300)"))
                if 'location_en' not in cols:
                    conn.execute(text("ALTER TABLE events ADD COLUMN location_en VARCHAR(300)"))
                if 'is_online' not in cols:
                    conn.execute(text("ALTER TABLE events ADD COLUMN is_online BOOLEAN DEFAULT 0"))
                if 'meeting_link' not in cols:
                    conn.execute(text("ALTER TABLE events ADD COLUMN meeting_link VARCHAR(1000)"))
                if 'status' not in cols:
                    conn.execute(text("ALTER TABLE events ADD COLUMN status VARCHAR(30) DEFAULT 'PUBLISHED'"))
                if 'certificate_eligible' not in cols:
                    conn.execute(text("ALTER TABLE events ADD COLUMN certificate_eligible BOOLEAN DEFAULT 0"))
                if 'eligibility_criteria' not in cols:
                    conn.execute(text("ALTER TABLE events ADD COLUMN eligibility_criteria VARCHAR(50) DEFAULT 'ALL_MEMBERS'"))
                if 'updated_at' not in cols:
                    conn.execute(text("ALTER TABLE events ADD COLUMN updated_at DATETIME"))
            if 'event_registrations' in inspector.get_table_names():
                cols = {c['name'] for c in inspector.get_columns('event_registrations')}
                if 'member_id' not in cols:
                    conn.execute(text("ALTER TABLE event_registrations ADD COLUMN member_id INTEGER"))
                if 'waitlist_position' not in cols:
                    conn.execute(text("ALTER TABLE event_registrations ADD COLUMN waitlist_position INTEGER"))
                if 'qr_token' not in cols:
                    conn.execute(text("ALTER TABLE event_registrations ADD COLUMN qr_token VARCHAR(128)"))
                if 'cancelled_at' not in cols:
                    conn.execute(text("ALTER TABLE event_registrations ADD COLUMN cancelled_at DATETIME"))
                if 'cancellation_reason' not in cols:
                    conn.execute(text("ALTER TABLE event_registrations ADD COLUMN cancellation_reason TEXT"))
            if 'notifications' in inspector.get_table_names():
                cols = {c['name'] for c in inspector.get_columns('notifications')}
                if 'title_en' not in cols:
                    conn.execute(text("ALTER TABLE notifications ADD COLUMN title_en VARCHAR(300)"))
                if 'body_en' not in cols:
                    conn.execute(text("ALTER TABLE notifications ADD COLUMN body_en TEXT"))
                if 'data_json' not in cols:
                    conn.execute(text("ALTER TABLE notifications ADD COLUMN data_json JSON"))
                if 'priority' not in cols:
                    conn.execute(text("ALTER TABLE notifications ADD COLUMN priority VARCHAR(20) DEFAULT 'NORMAL'"))
                if 'expires_at' not in cols:
                    conn.execute(text("ALTER TABLE notifications ADD COLUMN expires_at DATETIME"))
            conn.commit()
    except Exception:
        pass
    seed_main()
    yield
