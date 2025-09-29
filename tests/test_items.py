import sys
import os
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pytest

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.main import app
from app.database import Base
from app.routers.items import get_db


SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """
    Create a new database session for a test.
    """
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def override_get_db():
    """
    Dependency override for database sessions.
    """
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


def test_create_item(db_session):
    """
    Test item creation.
    """
    response = client.post(
        "/items/",
        json={"name": "Foo", "description": "A lovely item"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Foo"
    assert data["description"] == "A lovely item"
    assert "id" in data


def test_read_items(db_session):
    """
    Test reading a list of items.
    """
    client.post("/items/", json={"name": "Foo", "description": "A lovely item"})
    client.post("/items/", json={"name": "Bar", "description": "Another lovely item"})

    response = client.get("/items/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["name"] == "Foo"
    assert data[1]["name"] == "Bar"