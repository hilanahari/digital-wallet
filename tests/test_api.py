import pytest
from fastapi.testclient import TestClient
from app.main import app
from app import database


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", str(tmp_path / "test.db"))
    database.init_db()
    return TestClient(app)


@pytest.fixture
def two_accounts(client):
    client.post("/accounts", json={"owner": "Hila"})
    client.post("/accounts", json={"owner": "Dana"})
    client.post("/accounts/1/deposits", json={"amount": 5000})
    return client


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


def test_transfer(two_accounts):
    response = two_accounts.post(
        "/transfers", json={"from_account_id": 1, "to_account_id": 2, "amount": 3000}
    )
    assert response.status_code == 200
    assert response.json() == {"id": 1, "owner": "Hila", "balance": 2000}

    response_2 = two_accounts.get("/accounts/2")
    assert response_2.json() == {"id": 2, "owner": "Dana", "balance": 3000}


def test_transfer_same_account(two_accounts):
    response = two_accounts.post("/transfers", json={"from_account_id": 1, "to_account_id": 1, "amount": 500})
    assert response.status_code == 400
    assert response.json() == {"detail": "Cannot transfer to the same account"}

    response_2 = two_accounts.get("/accounts/1")
    assert response_2.json() == {"id": 1, "owner": "Hila", "balance": 5000}


def test_transfer_missing_source(two_accounts):
    response = two_accounts.post("/transfers", json={"from_account_id": 99, "to_account_id": 1, "amount": 500})
    assert response.status_code == 404
    assert response.json() == {"detail": "Source account not found"}

    response_2 = two_accounts.get("/accounts/1")
    assert response_2.json() == {"id": 1, "owner": "Hila", "balance": 5000}


def test_transfer_missing_target(two_accounts):
    response = two_accounts.post("/transfers", json={"from_account_id": 1, "to_account_id": 99, "amount": 500})
    assert response.status_code == 404
    assert response.json() == {"detail": "Target account not found"}

    response_2 = two_accounts.get("/accounts/1")
    assert response_2.json() == {"id": 1, "owner": "Hila", "balance": 5000}


def test_transfer_insufficient_funds(two_accounts):
    response = two_accounts.post("/transfers", json={"from_account_id": 1, "to_account_id": 2, "amount": 8000})
    assert response.status_code == 400
    assert response.json() == {"detail": "Insufficient funds"}

    response_2 = two_accounts.get("/accounts/1")
    response_3 = two_accounts.get("/accounts/2")
    assert response_2.json() == {"id": 1, "owner": "Hila", "balance": 5000}
    assert response_3.json() == {"id": 2, "owner": "Dana", "balance": 0}

        