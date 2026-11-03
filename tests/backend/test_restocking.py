"""
Tests for restocking order API endpoints.
"""
import os
import sys
from datetime import datetime, timedelta

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'server'))
import mock_data


@pytest.fixture(autouse=True)
def clear_restocking_orders():
    """Reset submitted orders around each test.

    The app and mock_data are imported once per pytest session, so orders
    posted by one test would otherwise be visible to every later test.
    """
    mock_data.restocking_orders.clear()
    yield
    mock_data.restocking_orders.clear()


def get_forecasts(client):
    return {f["item_sku"]: f for f in client.get("/api/demand").json()}


class TestRestockingForecastFields:
    """Demand forecasts must carry the data restocking needs."""

    def test_demand_forecasts_have_cost_and_lead_time(self, client):
        """Test that every forecast has a unit cost and lead time."""
        data = client.get("/api/demand").json()
        assert len(data) > 0

        for forecast in data:
            assert isinstance(forecast["unit_cost"], (int, float))
            assert forecast["unit_cost"] > 0
            assert isinstance(forecast["lead_time_days"], int)
            assert forecast["lead_time_days"] > 0


class TestRestockingOrderEndpoints:
    """Test suite for restocking order endpoints."""

    def test_get_restocking_orders_initially_empty(self, client):
        """Test that no orders exist before any are submitted."""
        response = client.get("/api/restocking-orders")
        assert response.status_code == 200
        assert response.json() == []

    def test_create_restocking_order(self, client):
        """Test submitting an order returns 201 with the expected structure."""
        response = client.post(
            "/api/restocking-orders",
            json={"budget": 50000, "items": [{"sku": "WDG-001", "quantity": 10}]},
        )
        assert response.status_code == 201

        order = response.json()
        for field in ["id", "order_number", "items", "total_cost", "budget",
                      "status", "submitted_date", "lead_time_days", "expected_delivery"]:
            assert field in order
        assert order["status"] == "Submitted"
        assert order["order_number"].startswith("RST-")
        assert order["budget"] == 50000

    def test_order_is_priced_from_server_data(self, client):
        """Test that unit cost and total come from the forecast data."""
        forecast = get_forecasts(client)["WDG-001"]
        response = client.post(
            "/api/restocking-orders",
            json={"budget": 50000, "items": [{"sku": "WDG-001", "quantity": 10}]},
        )
        order = response.json()

        item = order["items"][0]
        assert item["name"] == forecast["item_name"]
        assert item["unit_cost"] == forecast["unit_cost"]
        assert item["lead_time_days"] == forecast["lead_time_days"]
        assert abs(order["total_cost"] - 10 * forecast["unit_cost"]) < 0.01

    def test_order_lead_time_is_longest_item(self, client):
        """Test that the order lead time is the slowest item's lead time."""
        forecasts = get_forecasts(client)
        response = client.post(
            "/api/restocking-orders",
            json={"budget": 100000, "items": [
                {"sku": "FLT-405", "quantity": 5},
                {"sku": "GSK-203", "quantity": 5},
            ]},
        )
        order = response.json()

        expected = max(forecasts["FLT-405"]["lead_time_days"], forecasts["GSK-203"]["lead_time_days"])
        assert order["lead_time_days"] == expected

    def test_order_expected_delivery_matches_lead_time(self, client):
        """Test that expected delivery is the submitted date plus the lead time."""
        order = client.post(
            "/api/restocking-orders",
            json={"budget": 50000, "items": [{"sku": "WDG-001", "quantity": 1}]},
        ).json()

        submitted = datetime.fromisoformat(order["submitted_date"])
        expected = datetime.fromisoformat(order["expected_delivery"])
        assert expected - submitted == timedelta(days=order["lead_time_days"])

    def test_created_order_appears_in_list(self, client):
        """Test that a submitted order can be read back."""
        created = client.post(
            "/api/restocking-orders",
            json={"budget": 50000, "items": [{"sku": "WDG-001", "quantity": 1}]},
        ).json()

        orders = client.get("/api/restocking-orders").json()
        assert len(orders) == 1
        assert orders[0]["id"] == created["id"]

    def test_restocking_orders_newest_first(self, client):
        """Test that orders are returned newest first."""
        first = client.post(
            "/api/restocking-orders",
            json={"budget": 50000, "items": [{"sku": "WDG-001", "quantity": 1}]},
        ).json()
        second = client.post(
            "/api/restocking-orders",
            json={"budget": 50000, "items": [{"sku": "FLT-405", "quantity": 1}]},
        ).json()

        orders = client.get("/api/restocking-orders").json()
        assert [o["id"] for o in orders] == [second["id"], first["id"]]

    def test_restocking_order_does_not_change_customer_orders(self, client):
        """Test that restocking orders stay out of the customer orders list."""
        before = len(client.get("/api/orders").json())
        client.post(
            "/api/restocking-orders",
            json={"budget": 50000, "items": [{"sku": "WDG-001", "quantity": 1}]},
        )
        assert len(client.get("/api/orders").json()) == before

    def test_create_order_with_no_items(self, client):
        """Test that an empty order is rejected."""
        response = client.post("/api/restocking-orders", json={"budget": 1000, "items": []})
        assert response.status_code == 400
        assert "detail" in response.json()

    @pytest.mark.parametrize("quantity", [0, -5])
    def test_create_order_with_non_positive_quantity(self, client, quantity):
        """Test that zero or negative quantities are rejected."""
        response = client.post(
            "/api/restocking-orders",
            json={"budget": 50000, "items": [{"sku": "WDG-001", "quantity": quantity}]},
        )
        assert response.status_code == 400

    def test_create_order_with_unknown_sku(self, client):
        """Test that an unknown SKU is rejected."""
        response = client.post(
            "/api/restocking-orders",
            json={"budget": 50000, "items": [{"sku": "NOPE-999", "quantity": 1}]},
        )
        assert response.status_code == 400
        assert "unknown sku" in response.json()["detail"].lower()

    def test_create_order_over_budget(self, client):
        """Test that an order costing more than the budget is rejected."""
        unit_cost = get_forecasts(client)["WDG-001"]["unit_cost"]
        response = client.post(
            "/api/restocking-orders",
            json={"budget": unit_cost * 10 - 1, "items": [{"sku": "WDG-001", "quantity": 10}]},
        )
        assert response.status_code == 400
        assert "budget" in response.json()["detail"].lower()
        assert client.get("/api/restocking-orders").json() == []

    def test_create_order_exactly_at_budget(self, client):
        """Test that an order costing exactly the budget is accepted."""
        unit_cost = get_forecasts(client)["WDG-001"]["unit_cost"]
        response = client.post(
            "/api/restocking-orders",
            json={"budget": unit_cost * 10, "items": [{"sku": "WDG-001", "quantity": 10}]},
        )
        assert response.status_code == 201

    def test_create_order_with_invalid_body(self, client):
        """Test that a malformed body fails validation."""
        response = client.post("/api/restocking-orders", json={"items": []})
        assert response.status_code == 422
