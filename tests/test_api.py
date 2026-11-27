import pytest
from fastapi.testclient import TestClient
from app.main import app
from app import database


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", str(tmp_path / "test.db"))
    database.init_db()
    return TestClient(app)


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_account(client):
    response = client.post("/accounts", json={"owner": "Hila"})
    assert response.status_code == 201
    assert response.json() == {"id": 1, "owner": "Hila", "balance": 0}


def test_get_account(client):
    client.post("/accounts", json={"owner": "Hila"})

    response = client.get("/accounts/1")
    assert response.status_code == 200
    assert response.json() == {"id": 1, "owner": "Hila", "balance": 0}


def test_get_missing_account(client):
    response = client.get("/accounts/99")
    assert response.status_code == 404
    assert response.json() == {"detail": "Account not found"}


def test_deposit(client):
    client.post("/accounts", json={"owner": "Hila"})
    response = client.post("/accounts/1/deposits", json={"amount": 5000})
    assert response.status_code == 200
    assert response.json() == {"id": 1, "owner": "Hila", "balance": 5000}


def test_deposit_negative_amount(client):
    client.post("/accounts", json={"owner": "Hila"})
    response = client.post("/accounts/1/deposits", json={"amount": -500})
    assert response.status_code == 422
    assert response.json()["detail"][0]["type"] == "greater_than"


def test_deposit_missing_account(client):
    client.post("/accounts", json={"owner": "Hila"})
    response = client.post("/accounts/99/deposits", json={"amount": 5000})
    assert response.status_code == 404
    assert response.json() == {"detail": "Account not found"}
