from sqlalchemy.orm import Session

from .base import SessionLocal


def get_db() -> Session:
    """Database dependency for FastAPI"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
