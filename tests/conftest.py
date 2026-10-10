import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.config import settings
from backend.app.database import Base, get_db
from backend.app.main import app
from backend.app.services.seed import seed_database

# Configure test SQLite database
TEST_DB_FILE = os.path.join(os.path.dirname(__file__), "test_secureshop.db")
TEST_DB_URL = f"sqlite:///{TEST_DB_FILE}"

test_engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    db = TestingSessionLocal()
    seed_database(db)
    db.close()
    yield
    Base.metadata.drop_all(bind=test_engine)
    if os.path.exists(TEST_DB_FILE):
        try:
            os.remove(TEST_DB_FILE)
        except Exception:
            pass

@pytest.fixture
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture
def auth_headers_alice(client):
    """Log in as normal user alice and return authorization header."""
    res = client.post("/api/auth/login", json={"username": "alice", "password": "AlicePass123!"})
    token = res.json().get("token")
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def auth_headers_bob(client):
    """Log in as normal user bob and return authorization header."""
    res = client.post("/api/auth/login", json={"username": "bob", "password": "BobPass123!"})
    token = res.json().get("token")
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def auth_headers_admin(client):
    """Log in as admin and return authorization header."""
    res = client.post("/api/auth/login", json={"username": "admin", "password": "AdminPass123!"})
    token = res.json().get("token")
    return {"Authorization": f"Bearer {token}"}
