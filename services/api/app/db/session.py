from __future__ import annotations

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings

# Defensive dialect driver normalization
db_url = settings.database_url
if db_url.startswith('postgres://'):
    db_url = db_url.replace('postgres://', 'postgresql+psycopg://', 1)
elif db_url.startswith('postgresql://'):
    db_url = db_url.replace('postgresql://', 'postgresql+psycopg://', 1)
elif db_url.startswith('postgresql+psycopg2://'):
    db_url = db_url.replace('postgresql+psycopg2://', 'postgresql+psycopg://', 1)

if db_url.startswith('sqlite'):
    engine = create_engine(
        db_url,
        connect_args={'check_same_thread': False},
        pool_pre_ping=True,
    )
else:
    engine = create_engine(
        db_url,
        pool_pre_ping=True,
        pool_recycle=300,
        pool_size=5,
        max_overflow=10,
    )

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def set_engine(new_url: str):
    """
    Set and synchronize engine and SessionLocal across all loaded modules.
    Normalizes dialect prefixes, configures SessionLocal, and updates module references.
    """
    global engine, SessionLocal
    db_url = new_url
    if db_url.startswith('postgres://'):
        db_url = db_url.replace('postgres://', 'postgresql+psycopg://', 1)
    elif db_url.startswith('postgresql://'):
        db_url = db_url.replace('postgresql://', 'postgresql+psycopg://', 1)
    elif db_url.startswith('postgresql+psycopg2://'):
        db_url = db_url.replace('postgresql+psycopg2://', 'postgresql+psycopg://', 1)

    if engine is not None:
        try:
            engine.dispose()
        except Exception:
            pass

    if db_url.startswith('sqlite'):
        engine = create_engine(
            db_url,
            connect_args={'check_same_thread': False},
            pool_pre_ping=True,
        )
    else:
        engine = create_engine(
            db_url,
            pool_pre_ping=True,
            pool_recycle=300,
            pool_size=5,
            max_overflow=10,
        )

    SessionLocal.configure(bind=engine)
    settings.database_url = db_url

    import sys
    for mod in list(sys.modules.values()):
        if mod and getattr(mod, '__name__', '').startswith('app.'):
            curr = getattr(mod, 'engine', None)
            if curr is not engine and isinstance(curr, Engine):
                try:
                    setattr(mod, 'engine', engine)
                except Exception:
                    pass
    return engine
