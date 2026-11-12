from decimal import Decimal
from uuid import UUID

from fastapi.testclient import TestClient

from app import database
from app.main import app


def test_bank_flow(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "test_bank.db")

    with TestClient(app) as client:
        response = client.post("/accounts", json={"holder_name": "Maria da Silva"})
        assert response.status_code == 201
        account = response.json()
        account_id = account["id"]
        assert Decimal(account["balance"]) == Decimal("0.00")

        response = client.post(
            f"/accounts/{account_id}/deposit",
            json={"amount": "250.75", "description": "Depósito inicial"},
        )
        assert response.status_code == 200
        assert Decimal(response.json()["balance"]) == Decimal("250.75")

        response = client.post(
            f"/accounts/{account_id}/withdraw",
            json={"amount": "50.25"},
        )
        assert response.status_code == 200
        assert Decimal(response.json()["balance"]) == Decimal("200.50")

        response = client.post(
            f"/accounts/{account_id}/withdraw",
            json={"amount": "999.00"},
        )
        assert response.status_code == 409

        second = client.post("/accounts", json={"holder_name": "João Souza"}).json()
        response = client.post(
            f"/accounts/{account_id}/transfers",
            json={
                "destination_account_id": second["id"],
                "amount": "100.00",
            },
        )
        assert response.status_code == 200
        assert Decimal(response.json()["balance"]) == Decimal("100.50")

        destination = client.get(f"/accounts/{second['id']}").json()
        assert Decimal(destination["balance"]) == Decimal("100.00")

        statement = client.get(f"/accounts/{account_id}/transactions")
        assert statement.status_code == 200
        assert len(statement.json()) == 3


def test_rejects_amount_with_more_than_two_decimal_places(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "validation.db")

    with TestClient(app) as client:
        account_id = client.post(
            "/accounts", json={"holder_name": "Carlos Pereira"}
        ).json()["id"]
        response = client.post(
            f"/accounts/{account_id}/deposit", json={"amount": "10.999"}
        )
        assert response.status_code == 422
