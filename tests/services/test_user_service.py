import pytest
from sqlalchemy.exc import NoResultFound

from psychic_tribble.services.user_service import (
    create_user,
    get_user_by_id,
    update_user,
    delete_user
)

def test_create_user_returns_model(db_session):
    user = create_user(db_session, name="Alice", email="alice@example.com")
    # Persisted model should have an id and match inputs
    assert user.id is not None
    assert user.name == "Alice"
    assert user.email == "alice@example.com"

def test_get_user_by_id_success(db_session):
    created = create_user(db_session, name="Bob", email="bob@example.com")
    fetched = get_user_by_id(db_session, created.id)
    assert fetched.id == created.id
    assert fetched.email == "bob@example.com"

def test_get_user_by_id_not_found_raises(db_session):
    with pytest.raises(NoResultFound):
        get_user_by_id(db_session, 9999)

def test_update_user_success(db_session):
    user = create_user(db_session, name="Carol", email="carol@example.com")
    updated = update_user(db_session, user.id, name="Caroline", email="caroline@example.com")
    # Session flushes changes; fetch fresh
    refreshed = get_user_by_id(db_session, user.id)
    assert refreshed.name == "Caroline"
    assert refreshed.email == "caroline@example.com"

def test_update_user_not_found_raises(db_session):
    with pytest.raises(NoResultFound):
        update_user(db_session, 8888, name="Zed")

def test_delete_user_success(db_session):
    user = create_user(db_session, name="Dave", email="dave@example.com")
    # Should not raise
    delete_user(db_session, user.id)
    # After deletion, fetching should error
    with pytest.raises(NoResultFound):
        get_user_by_id(db_session, user.id)

def test_delete_user_not_found_raises(db_session):
    with pytest.raises(NoResultFound):
        delete_user(db_session, 7777)
