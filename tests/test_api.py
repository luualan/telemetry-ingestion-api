# tests/test_api.py
from __future__ import annotations

from uuid import uuid4
from typing import Any, Dict

import pytest
from fastapi.testclient import TestClient

import app.main as main
from app.repository import EventRepository
from app.services import EventService

# Single shared TestClient for the test module
client = TestClient(main.app)


@pytest.fixture(autouse=True)
def reset_repo() -> None:
    """Reset the in-memory repository/service before each test."""
    main.repository = EventRepository()
    main.service = EventService(main.repository)
    yield


def make_event_payload(
    *,
    event_id: str | None = None,
    customer_id: str = "cust1",
    resource_id: str = "res1",
    metric_name: str = "m1",
    value: float = 1.0,
    source: str | None = None,
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "customer_id": customer_id,
        "resource_id": resource_id,
        "metric_name": metric_name,
        "value": value,
    }
    if event_id is not None:
        payload["event_id"] = event_id
    if source is not None:
        payload["source"] = source
    return payload


def post_event(payload: Dict[str, Any], expect_status: int = 201):
    resp = client.post("/events", json=payload)
    assert resp.status_code == expect_status, resp.text
    return resp


def test_health_endpoint():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_create_event_roundtrips():
    payload = make_event_payload(customer_id="alice", resource_id="r1", metric_name="cpu", value=12.5, source="agent")
    resp = post_event(payload)
    body = resp.json()

    assert body["customer_id"] == "alice"
    assert body["resource_id"] == "r1"
    assert body["metric_name"] == "cpu"
    assert float(body["value"]) == 12.5
    assert "event_id" in body
    assert "timestamp" in body


def test_duplicate_event_returns_409():
    uid = str(uuid4())
    payload = make_event_payload(event_id=uid, customer_id="bob", resource_id="r2", metric_name="mem", value=3.14)

    post_event(payload)  # first succeeds
    resp = client.post("/events", json=payload)
    assert resp.status_code == 409


def test_invalid_payload_returns_422():
    invalid_payload = {"resource_id": "r", "metric_name": "m", "value": 1.0}  # missing customer_id
    resp = client.post("/events", json=invalid_payload)
    assert resp.status_code == 422


def test_get_event_by_id():
    payload = make_event_payload(customer_id="carol", resource_id="rx", metric_name="disk", value=7.0)
    created = post_event(payload).json()
    event_id = created["event_id"]

    resp = client.get(f"/events/{event_id}")
    assert resp.status_code == 200
    fetched = resp.json()
    assert fetched["event_id"] == event_id
    assert fetched["customer_id"] == "carol"


def test_filter_events_by_customer_id():
    ev_a = make_event_payload(customer_id="custA", metric_name="m1", value=1)
    ev_b = make_event_payload(customer_id="custB", metric_name="m1", value=2)
    post_event(ev_a)
    post_event(ev_b)

    resp = client.get("/events", params={"customer_id": "custA"})
    assert resp.status_code == 200
    results = resp.json()
    assert isinstance(results, list)
    assert len(results) == 1
    assert results[0]["customer_id"] == "custA"


def test_filter_events_by_metric_name():
    post_event(make_event_payload(customer_id="c1", metric_name="cpu", value=1))
    post_event(make_event_payload(customer_id="c1", metric_name="memory", value=2))

    resp = client.get("/events", params={"metric_name": "cpu"})

    assert resp.status_code == 200
    results = resp.json()
    assert len(results) == 1
    assert results[0]["metric_name"] == "cpu"


def test_get_missing_event_returns_404():
    missing_id = str(uuid4())

    resp = client.get(f"/events/{missing_id}")

    assert resp.status_code == 404


def test_customer_summary_aggregates():
    post_event(make_event_payload(customer_id="c123", metric_name="mA", value=1.0))
    post_event(make_event_payload(customer_id="c123", metric_name="mA", value=2.0))
    post_event(make_event_payload(customer_id="c123", metric_name="mB", value=5.5))

    resp = client.get("/customers/c123/summary")
    assert resp.status_code == 200
    body = resp.json()

    assert body["customer_id"] == "c123"
    metrics = body["metrics"]

    mA = metrics["mA"]
    assert mA["count"] == 2
    assert pytest.approx(mA["total"], rel=1e-9) == 3.0
    assert pytest.approx(mA["avg"], rel=1e-9) == 1.5
    assert mA["min"] == 1.0
    assert mA["max"] == 2.0

    mB = metrics["mB"]
    assert mB["count"] == 1
    assert pytest.approx(mB["total"], rel=1e-9) == 5.5
    assert pytest.approx(mB["avg"], rel=1e-9) == 5.5
    assert mB["min"] == 5.5
    assert mB["max"] == 5.5