"""M5 1-to-1 Personalization — tests (TDD).

Covers the ``ExperienceService.fetch`` decide-and-deliver core: audience-hit
gating, publish-state gating, deterministic + proportional variation
assignment, stable control hold-out, multi-language payload selection with
default fallback, multi-key fetches, and identifier resolution.

Reuses ``cohort_engine.sample_data`` (fixed ``now=2026-06-02``); the sample
KYC audience is {u1, u2, u4, u5} (u3 is not KYC).
"""
from __future__ import annotations

import pytest

from cohort_engine import CohortEngine
from cohort_engine.sample_data import NOW, build_sample_dataset
from growth_common import stable_fraction

from personalization import (
    CONTROL,
    Experience,
    ExperienceService,
    ExperienceStore,
    IdentifierError,
    Variation,
    assign,
)

# KYC audience rule (matches u1, u2, u4, u5 in the sample dataset)
KYC_SPEC = {
    "match": {"type": "attribute", "field": "is_kyc", "operator": "eq", "value": True}
}


# --- fixtures ----------------------------------------------------------------
@pytest.fixture
def dataset():
    return build_sample_dataset()


@pytest.fixture
def now():
    return NOW


@pytest.fixture
def engine(dataset, now):
    return CohortEngine(dataset, now=now)


@pytest.fixture
def store():
    return ExperienceStore()


@pytest.fixture
def service(engine, store):
    return ExperienceService(engine, store)


def _exp(key="home_card", control_pct=0.0, variations=None, audience_spec=None,
         status="draft"):
    return Experience(
        key=key,
        audience_spec=audience_spec or KYC_SPEC,
        variations=variations or [
            Variation("A", 1, {"en": {"title": "A-en"}, "ar": {"title": "A-ar"},
                                "hi": {"title": "A-hi"}}),
            Variation("B", 1, {"title": "B-flat"}),
        ],
        control_pct=control_pct,
        status=status,
    )


SYNTHETIC = [f"user{i}" for i in range(5000)]


# --- model validation --------------------------------------------------------
def test_variation_rejects_bad_weight_and_empty_name():
    with pytest.raises(ValueError):
        Variation("A", 0, {"title": "x"})
    with pytest.raises(ValueError):
        Variation("", 1, {"title": "x"})


def test_experience_rejects_dupe_variations_and_bad_control():
    with pytest.raises(ValueError):
        Experience("k", KYC_SPEC, [Variation("A", 1, {"t": "x"}),
                                   Variation("A", 1, {"t": "y"})])
    with pytest.raises(ValueError):
        Experience("k", KYC_SPEC, [Variation("A", 1, {"t": "x"})], control_pct=1.0)
    with pytest.raises(ValueError):
        Experience("k", KYC_SPEC, [])


def test_experience_rejects_reserved_control_name():
    with pytest.raises(ValueError):
        Experience("k", KYC_SPEC, [Variation("control", 1, {"t": "x"})])


def test_flat_payload_wrapped_under_default_locale():
    v = Variation("B", 1, {"title": "B-flat"})
    assert v.payload == {"default": {"title": "B-flat"}}
    assert v.payload_for("en") == {"title": "B-flat"}  # falls back to default


# --- audience hit ------------------------------------------------------------
def test_hit_returns_variation_payload(service, store, dataset, now):
    store.register(_exp())
    store.publish("home_card")
    res = service.fetch({"customer_id": "u1"}, ["home_card"], dataset, now)
    assert res["home_card"] is not None
    # u1 is KYC -> in audience; payload is one of the variation payloads
    assert "title" in res["home_card"]


def test_user_not_in_audience_returns_none(service, store, dataset, now):
    store.register(_exp())
    store.publish("home_card")
    # u3 is not KYC -> not in audience
    res = service.fetch({"customer_id": "u3"}, ["home_card"], dataset, now)
    assert res["home_card"] is None


# --- publish-state gating ----------------------------------------------------
def test_draft_experience_gated_even_for_audience_member(service, store, dataset, now):
    store.register(_exp(status="draft"))
    # u1 is in audience, but the experience is a draft -> gated to None
    res = service.fetch({"customer_id": "u1"}, ["home_card"], dataset, now)
    assert res["home_card"] is None


def test_publish_unlocks_payload(service, store, dataset, now):
    store.register(_exp(status="draft"))
    before = service.fetch({"customer_id": "u1"}, ["home_card"], dataset, now)
    assert before["home_card"] is None
    store.publish("home_card")
    after = service.fetch({"customer_id": "u1"}, ["home_card"], dataset, now)
    assert after["home_card"] is not None


def test_pause_re_gates_payload(service, store, dataset, now):
    store.register(_exp(status="draft"))
    store.publish("home_card")
    assert service.fetch({"customer_id": "u1"}, ["home_card"], dataset, now)["home_card"]
    store.pause("home_card")
    assert service.fetch({"customer_id": "u1"}, ["home_card"], dataset, now)["home_card"] is None


def test_list_published(store):
    store.register(_exp(key="a", status="draft"))
    store.register(_exp(key="b", status="draft"))
    store.publish("b")
    keys = [e.key for e in store.list_published()]
    assert keys == ["b"]


# --- deterministic + proportional variation assignment -----------------------
def test_assignment_is_deterministic(service, store, dataset, now):
    store.register(_exp())
    store.publish("home_card")
    r1 = service.fetch({"customer_id": "u1"}, ["home_card"], dataset, now)
    r2 = service.fetch({"customer_id": "u1"}, ["home_card"], dataset, now)
    assert r1 == r2  # same identifiers + key -> same payload


def test_variation_split_roughly_proportional():
    # 3:1 split A:B over many synthetic users; assign directly (no audience gate)
    exp = Experience("split", KYC_SPEC,
                     [Variation("A", 3, {"t": "a"}), Variation("B", 1, {"t": "b"})])
    buckets = [assign(exp, cid) for cid in SYNTHETIC]
    a = buckets.count("A")
    b = buckets.count("B")
    assert a + b == len(SYNTHETIC)
    assert 0.70 <= a / len(SYNTHETIC) <= 0.80
    assert 0.20 <= b / len(SYNTHETIC) <= 0.30


# --- control hold-out --------------------------------------------------------
def test_control_holdout_returns_none_and_is_stable(service, store, dataset, now):
    # find a KYC audience member that lands in a 50% control hold-out
    exp = _exp(control_pct=0.5)
    store.register(exp)
    store.publish("home_card")
    held = [cid for cid in ("u1", "u2", "u4", "u5")
            if stable_fraction("home_card", cid) < 0.5]
    assert held, "expected at least one held-out audience member at 50% control"
    for cid in held:
        assert assign(exp, cid) == CONTROL
        r1 = service.fetch({"customer_id": cid}, ["home_card"], dataset, now)
        r2 = service.fetch({"customer_id": cid}, ["home_card"], dataset, now)
        assert r1["home_card"] is None  # control -> no personalization
        assert r1 == r2  # stable


def test_control_fraction_matches_stable_fraction():
    exp = Experience("c", KYC_SPEC, [Variation("A", 1, {"t": "a"})], control_pct=0.2)
    control = sum(1 for cid in SYNTHETIC if assign(exp, cid) == CONTROL)
    assert 0.17 <= control / len(SYNTHETIC) <= 0.23
    for cid in SYNTHETIC:
        if stable_fraction("c", cid) < 0.2:
            assert assign(exp, cid) == CONTROL
        else:
            assert assign(exp, cid) != CONTROL


# --- multi-language ----------------------------------------------------------
def _payload_for_locale(service, store, dataset, now, locale):
    """Helper: pick a KYC user that lands in variation A (localized payload)."""
    exp = _exp()
    store.register(exp)
    store.publish("home_card")
    for cid in ("u1", "u2", "u4", "u5"):
        if assign(exp, cid) == "A":
            return service.fetch({"customer_id": cid}, ["home_card"],
                                 dataset, now, locale=locale)["home_card"]
    pytest.skip("no KYC user landed in variation A")


def test_locale_ar_and_hi_select_that_payload(service, store, dataset, now):
    assert _payload_for_locale(service, store, dataset, now, "ar") == {"title": "A-ar"}


def test_locale_hi(service, store, dataset, now):
    assert _payload_for_locale(service, store, dataset, now, "hi") == {"title": "A-hi"}


def test_unknown_locale_falls_back_to_default(service, store, dataset, now):
    # variation A has no "fr"; its localized map has no "default" either, so
    # fallback yields None — assert via a variation that DOES carry a default.
    exp = Experience("fb", KYC_SPEC, [
        Variation("only", 1, {"default": {"title": "def"}, "ar": {"title": "ar"}}),
    ])
    store.register(exp)
    store.publish("fb")
    res = service.fetch({"customer_id": "u1"}, ["fb"], dataset, now, locale="zz")
    assert res["fb"] == {"title": "def"}  # unknown locale -> default


# --- multiple keys + unknown key ---------------------------------------------
def test_multiple_keys_and_unknown_key(service, store, dataset, now):
    store.register(_exp(key="home_card"))
    store.publish("home_card")
    res = service.fetch({"customer_id": "u1"},
                        ["home_card", "nope"], dataset, now)
    assert set(res) == {"home_card", "nope"}
    assert res["home_card"] is not None
    assert res["nope"] is None  # unknown key -> None


def test_only_requested_keys_returned(service, store, dataset, now):
    store.register(_exp(key="a"))
    store.register(_exp(key="b"))
    store.publish("a")
    store.publish("b")
    res = service.fetch({"customer_id": "u1"}, ["a"], dataset, now)
    assert set(res) == {"a"}


# --- identifier resolution ---------------------------------------------------
def test_missing_customer_id_raises(service, store, dataset, now):
    store.register(_exp())
    store.publish("home_card")
    with pytest.raises(IdentifierError):
        service.fetch({}, ["home_card"], dataset, now)


def test_identifier_fallback_to_u_mb(service, store, dataset, now):
    # map u_mb -> the customer_id "u1"; u1 is in audience
    exp = Experience("k", KYC_SPEC, [Variation("A", 1, {"title": "x"})])
    store.register(exp)
    store.publish("k")
    res = service.fetch({"u_mb": "u1"}, ["k"], dataset, now)
    assert res["k"] == {"title": "x"}
