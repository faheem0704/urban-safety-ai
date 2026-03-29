import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

os.makedirs("database", exist_ok=True)

DATABASE_URL = "sqlite:///database/safety_monitor.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # required for SQLite + async background tasks
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI dependency: yields a request-scoped DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables. Call once at startup."""
    from database import models  # noqa: F401 — ensures models are registered on Base
    Base.metadata.create_all(bind=engine)
