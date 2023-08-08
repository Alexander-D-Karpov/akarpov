from redirect.db import SessionLocal


def get_db():
    """Route dependency that provides a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
