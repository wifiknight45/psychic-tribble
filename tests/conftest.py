import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from psychic_tribble.db.models import Base

@pytest.fixture(scope="session")
def engine():
    """
    Create an in-memory SQLite engine for the entire test session.
    The database schema is created once and dropped at session end.
    """
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)

@pytest.fixture(scope="function")
def db_session(engine):
    """
    Provide a new database session for each test function.
    Ensures tests are isolated and the session is closed afterward.
    """
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()
