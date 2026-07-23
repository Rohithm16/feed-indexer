"""
Database setup using SQLAlchemy.

SQLite is used for the MVP — swapping to Postgres requires only changing
DATABASE_URL in .env (e.g. postgresql://user:pass@localhost/feedindexer).
The models and queries stay exactly the same.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from app.config import settings

# SQLite needs check_same_thread=False for use with FastAPI
connect_args = {}
if settings.database_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(settings.database_url, connect_args=connect_args)

# Each request gets its own session via get_db()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """All models inherit from this."""
    pass


def get_db():
    """FastAPI dependency — yields a DB session and closes it when done."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables. Called once at startup."""
    # Import models here so SQLAlchemy registers them before create_all
    from app.models import event, article, user_prefs  # noqa: F401
    Base.metadata.create_all(bind=engine)
