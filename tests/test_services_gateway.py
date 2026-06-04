"""Service decomposition + API gateway tests (in-process, no running servers).

Two concerns:

1. **Independent deployability** — each service app responds correctly to a
   representative endpoint through its OWN ``TestClient`` (proving it runs
   stand-alone, not only behind the gateway).
2. **Gateway edge behaviors** — discovery (``/health``), auth (``MOE-APPKEY``),
   rate limiting (``429``) and routing to an unknown prefix (``404``).
"""
import pytest

fastapi = pytest.importorskip("fastapi")
from fastapi.testclient import TestClient  # noqa: E402

import api_gateway  # noqa: E402
from services import SERVICES  # noqa: E402
from services import (  # noqa: E402
    analytics,
    audience,
    campaign,
    content,
    data_platform,
    experiment,
    personalization,
)

# A high-value cohort spec that selects w1..w5 from the demo world.
HV_SPEC = {
    "name": "hv",
    "match": {
        "op": "and",
        "children": [
            {"type": "attribute", "field": "is_kyc", "operator": "eq", "value": True},
            {"type": "attribute", "field": "balance", "operator": "gte", "value": 1000},
            {"type": "attribute", "field": "wallet_activated", "operator": "eq", "value": False},
        ],
    },
}


# --------------------------------------------------------------------------- #
# 1. each service is independently deployable (own TestClient)
# --------------------------------------------------------------------------- #
def test_data_platform_identity_resolve():
    c = TestClient(data_platform.app)
    body = c.post("/identity/resolve", json={"identifiers": {"customer_id": "w1"}}).json()
    assert body == {"canonical_id": "w1", "resolved": True}


def test_audience_evaluate():
    c = TestClient(audience.app)
    r = c.post("/segments/evaluate", json=HV_SPEC)
    assert r.status_code == 200
    body = r.json()
    assert body["size"] == 5
    assert body["customer_ids"] == ["w1", "w2", "w3", "w4", "w5"]


def test_audience_invalid_rule_is_422():
    c = TestClient(audience.app)
    bad = {"match": {"type": "attribute", "field": "x", "operator": "bogus", "value": 1}}
    assert c.post("/segments/evaluate", json=bad).status_code == 422


def test_personalization_fetch_after_register_and_publish():
    c = TestClient(personalization.app)
    reg = c.post(
        "/experiences",
        json={
            "key": "home_card",
            "audience_spec": HV_SPEC,
            "variations": [{"name": "A", "weight": 1, "payload": {"title": "Hi"}}],
        },
    )
    assert reg.status_code == 201
    # before publish: gated out -> None
    pre = c.post(
        "/experiences/fetch",
        json={"identifiers": {"customer_id": "w1"}, "experience_keys": ["home_card"]},
    ).json()
    assert pre["experiences"]["home_card"] is None

    assert c.post("/experiences/home_card/publish").status_code == 200

    post = c.post(
        "/experiences/fetch",
        json={"identifiers": {"customer_id": "w1"}, "experience_keys": ["home_card"]},
    ).json()
    assert post["experiences"]["home_card"] == {"title": "Hi"}


def test_campaign_run_summary_balances():
    c = TestClient(campaign.app)
    r = c.post("/campaigns/run", json={})
    assert r.status_code == 200
    body = r.json()
    assert body["audience_size"] == 5          # w1..w5
    assert body["sent_count"] == 2             # w1, w5 reachable; w2 opt-out, w3/w4 unreachable
    assert body["balances"] is True


def test_content_generate():
    c = TestClient(content.app)
    r = c.post(
        "/copy/generate",
        json={"goal": "activate_wallet", "product": "Wallet", "locales": ["en", "ar"], "n": 2},
    )
    assert r.status_code == 200
    variants = r.json()["variants"]
    assert len(variants) == 4                  # 2 arms x 2 locales
    assert {v["locale"] for v in variants} == {"en", "ar"}


def test_analytics_funnel():
    c = TestClient(analytics.app)
    body = c.post("/funnel", json={"steps": ["App Opened", "Transfer"]}).json()
    assert body["step_counts"] == [5, 3]
    assert body["overall_conversion"] == pytest.approx(0.6)


def test_experiment_split_is_disjoint_and_covers_all():
    c = TestClient(experiment.app)
    ids = ["w1", "w2", "w3", "w4", "w5"]
    body = c.post("/shadow/split", json={"customer_ids": ids, "shadow_pct": 0.5}).json()
    shadow, control = set(body["shadow"]), set(body["control"])
    assert shadow.isdisjoint(control)
    assert shadow | control == set(ids)


# --------------------------------------------------------------------------- #
# 2. gateway edge behaviors
# --------------------------------------------------------------------------- #
def test_gateway_health_lists_services():
    g = TestClient(api_gateway.app)
    body = g.get("/health").json()
    assert body["status"] == "ok"
    assert set(body["services"]) == set(SERVICES)
    assert body["services"]["audience"] == "/api/audience"


def test_gateway_routes_with_appkey():
    g = TestClient(api_gateway.app)
    r = g.post("/api/audience/segments/size", headers={"MOE-APPKEY": "k1"}, json=HV_SPEC)
    assert r.status_code == 200
    assert r.json() == {"size": 5}


def test_gateway_rejects_missing_appkey():
    g = TestClient(api_gateway.app)
    r = g.post("/api/audience/segments/size", json=HV_SPEC)
    assert r.status_code == 401


def test_gateway_rejects_empty_appkey():
    g = TestClient(api_gateway.app)
    r = g.post("/api/audience/segments/size", headers={"MOE-APPKEY": ""}, json=HV_SPEC)
    assert r.status_code == 401


def test_gateway_unknown_prefix_is_404():
    g = TestClient(api_gateway.app)
    assert g.get("/api/nope/whatever", headers={"MOE-APPKEY": "k1"}).status_code == 404


def test_gateway_low_limit_trips_429():
    g = TestClient(api_gateway.create_gateway(rate_limit=2))
    codes = [
        g.post("/api/audience/segments/size", headers={"MOE-APPKEY": "k1"}, json=HV_SPEC).status_code
        for _ in range(5)
    ]
    assert codes[:2] == [200, 200]
    assert 429 in codes


def test_gateway_health_is_unauthenticated():
    g = TestClient(api_gateway.create_gateway(rate_limit=1))
    # /health needs no key and is not rate-limited as an /api/* path
    assert g.get("/health").status_code == 200
    assert g.get("/health").status_code == 200
