"""REST API tests via FastAPI TestClient (in-process, no running server)."""
import pytest

fastapi = pytest.importorskip("fastapi")
from fastapi.testclient import TestClient  # noqa: E402

from cohort_engine.api import app  # noqa: E402

client = TestClient(app)


def test_health():
    assert client.get("/health").json() == {"status": "ok"}


def test_evaluate_endpoint():
    spec = {"match": {"type": "attribute", "field": "is_kyc", "operator": "eq", "value": True}}
    r = client.post("/segments/evaluate", json=spec)
    assert r.status_code == 200
    body = r.json()
    assert body["size"] == 4
    assert body["customer_ids"] == ["u1", "u2", "u4", "u5"]


def test_size_endpoint():
    spec = {"match": {"type": "attribute", "field": "country", "operator": "in", "value": ["AE"]}}
    assert client.post("/segments/size", json=spec).json() == {"size": 3}


def test_compile_endpoint():
    spec = {"match": {"type": "attribute", "field": "is_kyc", "operator": "eq", "value": True}}
    sql = client.post("/segments/compile", json=spec).json()["sql"]
    assert "u.is_kyc = TRUE" in sql


def test_invalid_rule_returns_422():
    spec = {"match": {"type": "attribute", "field": "x", "operator": "bogus", "value": 1}}
    assert client.post("/segments/evaluate", json=spec).status_code == 422


def test_nl2sql_endpoint():
    r = client.post("/nl2sql", json={"text": "KYC users with balance over 1000 and wallet not activated"})
    assert r.status_code == 200
    body = r.json()
    assert body["confidence"] == 1.0
    assert body["requires_review"] is False
    # the returned DSL should evaluate to {u1, u4}
    ev = client.post("/segments/evaluate", json=body["dsl"]).json()
    assert set(ev["customer_ids"]) == {"u1", "u4"}


def test_nl2sql_missing_text_422():
    assert client.post("/nl2sql", json={}).status_code == 422


def test_list_templates():
    body = client.get("/templates").json()
    assert "high_value_wallet_inactive" in body["templates"]


def test_run_template():
    r = client.post("/templates/kyc_no_transfer", json={"days": 90})
    assert r.status_code == 200
    assert set(r.json()["customer_ids"]) == {"u1", "u4"}


def test_run_unknown_template_404():
    assert client.post("/templates/nope", json={}).status_code == 404
