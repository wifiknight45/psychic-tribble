import pytest
from datetime import datetime

from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker

from psychic_tribble.db.models import Base, User, Event, Timeslot

@pytest.fixture(scope="function")
def engine():
    # In-memory SQLite for testing
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)

@pytest.fixture(scope="function")
def db_session(engine):
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()

def test_tables_exist(engine):
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    assert "users" in tables
    assert "events" in tables
    assert "timeslots" in tables

def test_user_model_columns(engine):
    inspector = inspect(engine)
    cols = {col["name"] for col in inspector.get_columns("users")}
    expected = {"id", "name", "email"}
    assert expected.issubset(cols)

def test_event_model_columns(engine):
    inspector = inspect(engine)
    cols = {col["name"] for col in inspector.get_columns("events")}
    expected = {"id", "title", "description", "start_time", "end_time", "host_id"}
    assert expected.issubset(cols)

def test_timeslot_model_columns(engine):
    inspector = inspect(engine)
    cols = {col["name"] for col in inspector.get_columns("timeslots")}
    expected = {"id", "event_id", "start_time", "end_time"}
    assert expected.issubset(cols)

def test_user_event_relationship(db_session):
    # Create a user
    user = User(name="Alice", email="alice@example.com")
    db_session.add(user)
    db_session.commit()

    # Create an event linked to that user
    event = Event(
        title="Meeting",
        description="Discuss Q3 goals",
        start_time=datetime.utcnow(),
        end_time=datetime.utcnow(),
        host_id=user.id
    )
    db_session.add(event)
    db_session.commit()

    # Relationship should load the same user object
    assert event.host.id == user.id
    assert event.host.email == "alice@example.com"

def test_event_timeslot_relationship(db_session):
    # Create user and event
    user = User(name="Bob", email="bob@example.com")
    db_session.add(user)
    db_session.commit()

    event = Event(
        title="Workshop",
        description="Hands-on lab",
        start_time=datetime.utcnow(),
        end_time=datetime.utcnow(),
        host_id=user.id
    )
    db_session.add(event)
    db_session.commit()

    # Create a timeslot for that event
    slot = Timeslot(
        event_id=event.id,
        start_time=datetime.utcnow(),
        end_time=datetime.utcnow()
    )
    db_session.add(slot)
    db_session.commit()

    # Relationship should load the same event object
    assert slot.event.id == event.id
    assert slot.event.title == "Workshop"

def test_event_without_valid_host_id(db_session):
    # If host_id points to non-existent user, relationship returns None
    orphan_event = Event(
        title="Orphan",
        description="No host assigned",
        start_time=datetime.utcnow(),
        end_time=datetime.utcnow(),
        host_id=9999
    )
    db_session.add(orphan_event)
    db_session.commit()
    assert orphan_event.host is None
