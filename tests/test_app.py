"""Unit tests for the Expense Tracker API. Run with:  pytest -v"""

import pytest

from app import create_app


@pytest.fixture
def client(tmp_path):
    # Every test gets a fresh, empty database in a temporary folder.
    app = create_app(db_path=str(tmp_path / "test.db"))
    app.config["TESTING"] = True
    return app.test_client()


def add(client, amount=100, category="Food", date="2026-10-01", note="lunch"):
    return client.post("/api/expenses", json={"amount": amount, "category": category, "date": date, "note": note})


# ---------- create ----------
def test_add_expense(client):
    res = add(client)
    assert res.status_code == 201
    data = res.get_json()
    assert data["id"] == 1
    assert data["amount"] == 100
    assert data["category"] == "Food"


def test_list_returns_added_expense(client):
    add(client)
    res = client.get("/api/expenses")
    assert res.status_code == 200
    assert len(res.get_json()) == 1


# ---------- validation ----------
@pytest.mark.parametrize(
    "payload, message",
    [
        ({"amount": -5, "category": "Food", "date": "2026-10-01"}, "greater than 0"),
        ({"amount": "abc", "category": "Food", "date": "2026-10-01"}, "must be a number"),
        ({"amount": 10, "category": "Rocket", "date": "2026-10-01"}, "Category"),
        ({"amount": 10, "category": "Food", "date": "01-10-2026"}, "YYYY-MM-DD"),
    ],
)
def test_invalid_input_is_rejected(client, payload, message):
    res = client.post("/api/expenses", json=payload)
    assert res.status_code == 400
    assert message in res.get_json()["error"]


def test_missing_json_body_is_rejected(client):
    res = client.post("/api/expenses", data="not json")
    assert res.status_code == 400


# ---------- update ----------
def test_update_expense(client):
    add(client)
    res = client.put("/api/expenses/1", json={"amount": 250, "category": "Travel", "date": "2026-10-02"})
    assert res.status_code == 200
    expense = client.get("/api/expenses").get_json()[0]
    assert expense["amount"] == 250
    assert expense["category"] == "Travel"


def test_update_missing_expense_returns_404(client):
    res = client.put("/api/expenses/99", json={"amount": 10, "category": "Food", "date": "2026-10-01"})
    assert res.status_code == 404


# ---------- delete ----------
def test_delete_expense(client):
    add(client)
    assert client.delete("/api/expenses/1").status_code == 200
    assert client.get("/api/expenses").get_json() == []


def test_delete_missing_expense_returns_404(client):
    assert client.delete("/api/expenses/99").status_code == 404


# ---------- filter ----------
def test_filter_by_category_and_month(client):
    add(client, category="Food", date="2026-10-01")
    add(client, category="Travel", date="2026-10-05")
    add(client, category="Food", date="2026-09-20")

    food = client.get("/api/expenses?category=Food").get_json()
    assert len(food) == 2

    october_food = client.get("/api/expenses?category=Food&month=2026-10").get_json()
    assert len(october_food) == 1


# ---------- summary ----------
def test_monthly_summary(client):
    add(client, amount=100, category="Food", date="2026-10-01")
    add(client, amount=50.5, category="Food", date="2026-10-03")
    add(client, amount=300, category="Travel", date="2026-10-04")
    add(client, amount=999, category="Bills", date="2026-09-30")  # different month, must be ignored

    summary = client.get("/api/summary?month=2026-10").get_json()
    assert summary["total"] == 450.5
    assert summary["by_category"] == {"Travel": 300, "Food": 150.5}


def test_summary_for_empty_month(client):
    summary = client.get("/api/summary?month=2020-01").get_json()
    assert summary["total"] == 0
    assert summary["by_category"] == {}
