import os
import tempfile
from datetime import datetime, timedelta, timezone

import jwt
import pytest

# Configure a throw-away environment BEFORE importing the app.
_tmp_db = os.path.join(tempfile.mkdtemp(), "test.db")
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["ALGORITHM"] = "HS256"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "30"
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp_db}"

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def register(client, email, username, password="password123"):
    return client.post(
        "/auth/register", json={"email": email, "username": username, "password": password}
    )


def login(client, username, password="password123"):
    return client.post("/auth/login", data={"username": username, "password": password})


def auth_header(client, username, password="password123"):
    token = login(client, username, password).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


EXPENSE = {
    "title": "Lunch",
    "description": "Biryani",
    "amount": 180.5,
    "category": "food",
    "expense_date": "2026-10-08",
}


def test_register_login_me(client):
    r = register(client, "alice@example.com", "alice")
    assert r.status_code == 201
    assert "hashed_password" not in r.json()

    assert register(client, "alice@example.com", "alice2").status_code == 409
    assert register(client, "other@example.com", "alice").status_code == 409

    assert login(client, "alice", "wrongpass").status_code == 401
    r = login(client, "alice")
    assert r.status_code == 200 and r.json()["token_type"] == "bearer"

    h = auth_header(client, "alice")
    me = client.get("/auth/me", headers=h)
    assert me.status_code == 200 and me.json()["username"] == "alice"


def test_password_is_hashed(client):
    from sqlalchemy import select

    from app.database import SessionLocal
    from app.models import User

    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.username == "alice"))
        assert user.hashed_password != "password123"
        assert user.hashed_password.startswith("$2")


def test_protected_routes_need_valid_token(client):
    assert client.get("/auth/me").status_code == 401
    assert client.get("/expenses").status_code == 401
    assert client.get("/expenses", headers={"Authorization": "Bearer junk"}).status_code == 401

    expired = jwt.encode(
        {"sub": "1", "exp": datetime.now(timezone.utc) - timedelta(minutes=1)},
        "test-secret-key",
        algorithm="HS256",
    )
    r = client.get("/auth/me", headers={"Authorization": f"Bearer {expired}"})
    assert r.status_code == 401


def test_crud_flow(client):
    h = auth_header(client, "alice")

    r = client.post("/expenses", json=EXPENSE, headers=h)
    assert r.status_code == 201
    eid = r.json()["id"]

    assert client.post("/expenses", json={**EXPENSE, "amount": -5}, headers=h).status_code == 422
    assert client.post("/expenses", json={"title": "x"}, headers=h).status_code == 422

    assert client.get(f"/expenses/{eid}", headers=h).json()["title"] == "Lunch"

    r = client.put(f"/expenses/{eid}", json={**EXPENSE, "title": "Dinner"}, headers=h)
    assert r.status_code == 200 and r.json()["title"] == "Dinner"
    assert client.put(f"/expenses/9999", json=EXPENSE, headers=h).status_code == 404

    assert client.delete(f"/expenses/{eid}", headers=h).status_code == 204
    assert client.get(f"/expenses/{eid}", headers=h).status_code == 404
    assert client.delete(f"/expenses/{eid}", headers=h).status_code == 404


def test_pagination(client):
    h = auth_header(client, "alice")
    for i in range(5):
        client.post("/expenses", json={**EXPENSE, "title": f"Item {i}"}, headers=h)
    assert len(client.get("/expenses?limit=2", headers=h).json()) == 2
    assert len(client.get("/expenses?skip=3&limit=10", headers=h).json()) >= 2
    assert client.get("/expenses?limit=0", headers=h).status_code == 422


def test_ownership(client):
    register(client, "bob@example.com", "bob")
    ha = auth_header(client, "alice")
    hb = auth_header(client, "bob")

    eid = client.post("/expenses", json=EXPENSE, headers=ha).json()["id"]

    assert client.get(f"/expenses/{eid}", headers=hb).status_code == 404
    assert client.put(f"/expenses/{eid}", json=EXPENSE, headers=hb).status_code == 404
    assert client.delete(f"/expenses/{eid}", headers=hb).status_code == 404
    assert all(e["id"] != eid for e in client.get("/expenses", headers=hb).json())
    assert client.get(f"/expenses/{eid}", headers=ha).status_code == 200
