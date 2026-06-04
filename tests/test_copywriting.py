"""M6 AI Copywriting tests (TDD).

Covers: multilingual generation (per-locale, distinct seeds), fintech compliance
(banned claim / over-length truncation / disclaimer / shouting), the copy↔effect
feedback loop (rank / select_best / epsilon-greedy / /0 guard), M3 variant mapping
and end-to-end determinism.
"""
from datetime import datetime

import pytest

from growth_common import DeliveryRecord, DeliveryStatus

from copywriting import (
    CopyGenerator,
    CopyRequest,
    CopyVariant,
    TemplateProvider,
    check,
    epsilon_greedy,
    rank_by_performance,
    select_best,
)
from copywriting.compliance import CHANNEL_MAX_LEN, DISCLAIMER_TEXT

NOW = datetime(2026, 6, 4, 12, 0, 0)


# --- fixtures -----------------------------------------------------------------
@pytest.fixture
def provider():
    return TemplateProvider()


@pytest.fixture
def generator(provider):
    return CopyGenerator(provider)


def _rec(variant, *, sent=True, converted=False):
    return DeliveryRecord(
        customer_id="u",
        campaign_id="c",
        channel="push",
        content_id="copy",
        ts=NOW,
        status=DeliveryStatus.SENT if sent else DeliveryStatus.FAILED,
        variant=variant,
        converted=converted,
    )


# --- generation ---------------------------------------------------------------
def test_generate_one_variant_per_requested_locale(generator):
    req = CopyRequest(goal="activate_wallet", product="Wallet", locales=["en", "ar", "hi"])
    variants = generator.generate(req, n=1)
    locales = {v.locale for v in variants}
    assert locales == {"en", "ar", "hi"}
    assert all(isinstance(v, CopyVariant) and v.text for v in variants)


def test_different_locales_produce_different_text(generator):
    req = CopyRequest(goal="activate_wallet", product="Wallet", locales=["en", "ar", "hi", "tl"])
    variants = generator.generate(req, n=1)
    texts = {v.locale: v.text for v in variants}
    assert len(set(texts.values())) == 4  # all locales differ


def test_n_gt_1_yields_distinct_variants_per_locale(generator):
    req = CopyRequest(goal="activate_wallet", product="Wallet", locales=["en"])
    variants = generator.generate(req, n=3)
    assert len(variants) == 3
    seeds = sorted(v.meta["seed"] for v in variants)
    assert seeds == [0, 1, 2]
    assert len({v.text for v in variants}) == 3  # distinct seeds -> distinct text


def test_generate_n_times_locales(generator):
    req = CopyRequest(goal="activate_wallet", product="Wallet", locales=["en", "ar"])
    variants = generator.generate(req, n=2)
    assert len(variants) == 4  # 2 locales x 2 arms


# --- determinism --------------------------------------------------------------
def test_same_request_and_seed_identical_text(provider):
    req = CopyRequest(goal="activate_wallet", product="Wallet", locales=["en"])
    a = provider.generate(req, "en", seed=1)
    b = provider.generate(req, "en", seed=1)
    assert a == b


def test_generator_deterministic(generator):
    req = CopyRequest(goal="activate_wallet", product="Wallet", locales=["en", "ar"])
    first = [(v.locale, v.text) for v in generator.generate(req, n=2)]
    second = [(v.locale, v.text) for v in generator.generate(req, n=2)]
    assert first == second


# --- compliance ---------------------------------------------------------------
def test_compliance_banned_word_flagged():
    res = check("Get a guaranteed loan today!", product="Loan")
    assert res.ok is False
    assert any(v.startswith("banned_claim") for v in res.violations)


def test_compliance_over_length_truncated():
    long_text = "Activate your Botim Wallet now. " * 10  # well over push limit
    res = check(long_text, channel="push")
    assert any(v.startswith("over_length") for v in res.violations)
    assert len(res.fixed_text) <= CHANNEL_MAX_LEN["push"]


def test_compliance_loan_missing_disclaimer_appended_and_ok():
    res = check("Apply for a Botim Loan and get funds fast.", product="Loan")
    assert "missing_disclaimer" in res.violations
    assert DISCLAIMER_TEXT in res.fixed_text
    assert res.ok is True  # disclaimer auto-append is not a hard failure


def test_compliance_remittance_disclaimer():
    res = check("Send money home with Botim Remittance.", product="Remittance")
    assert DISCLAIMER_TEXT in res.fixed_text
    assert res.ok is True


def test_compliance_disclaimer_not_duplicated():
    text = f"Send money home with Botim. {DISCLAIMER_TEXT}"
    res = check(text, product="Remittance")
    assert "missing_disclaimer" not in res.violations
    assert res.fixed_text.count(DISCLAIMER_TEXT) == 1


def test_compliance_all_caps_flagged():
    res = check("ACTIVATE YOUR WALLET RIGHT NOW")
    assert res.ok is False
    assert "shouting_all_caps" in res.violations


def test_compliance_clean_text_ok():
    res = check("Activate your Botim Wallet and start sending money.", channel="in_app")
    assert res.ok is True
    assert res.violations == []


def test_generated_copy_passes_through_compliance(generator):
    req = CopyRequest(goal="activate_wallet", product="Loan", locales=["en"], channel="push")
    variants = generator.generate(req, n=1)
    v = variants[0]
    # disclaimer required for Loan; final text carries it and stays within limit
    assert DISCLAIMER_TEXT in v.text
    assert len(v.text) <= CHANNEL_MAX_LEN["push"]
    assert "violations" in v.meta and "compliant" in v.meta


# --- to_orchestration_variants ------------------------------------------------
def test_to_orchestration_variants_shape(generator):
    req = CopyRequest(goal="activate_wallet", product="Wallet", locales=["en", "ar"])
    variants = generator.generate(req, n=2)
    arms = generator.to_orchestration_variants(variants)
    assert [a["name"] for a in arms] == ["A", "B"]
    for a in arms:
        assert a["weight"] == 1.0
        assert a["content_id"]
        assert set(a["payload"].keys()) == {"en", "ar"}


def test_to_orchestration_variants_custom_ids_and_weights(generator):
    req = CopyRequest(goal="activate_wallet", product="Wallet", locales=["en"])
    variants = generator.generate(req, n=2)
    arms = generator.to_orchestration_variants(
        variants, content_ids=["c1", "c2"], weights=[3.0, 1.0]
    )
    assert arms[0]["content_id"] == "c1" and arms[0]["weight"] == 3.0
    assert arms[1]["content_id"] == "c2" and arms[1]["weight"] == 1.0


def test_to_orchestration_variants_feed_m3_variant(generator):
    from orchestration.models import Variant

    req = CopyRequest(goal="activate_wallet", product="Wallet", locales=["en"])
    arms = generator.to_orchestration_variants(generator.generate(req, n=2))
    m3 = [Variant(name=a["name"], weight=a["weight"], content_id=a["content_id"]) for a in arms]
    assert [v.name for v in m3] == ["A", "B"]


# --- feedback loop ------------------------------------------------------------
def test_rank_orders_by_cvr():
    records = (
        [_rec("A", converted=True)] * 3 + [_rec("A")] * 7          # CVR 0.3
        + [_rec("B", converted=True)] * 6 + [_rec("B")] * 4         # CVR 0.6
    )
    ranked = rank_by_performance(records)
    assert ranked[0][0] == "B"
    assert ranked[1][0] == "A"
    assert ranked[0][3] == pytest.approx(0.6)
    assert ranked[1][3] == pytest.approx(0.3)


def test_select_best_picks_highest_cvr():
    records = [_rec("A", converted=True)] + [_rec("A")] * 9 + [_rec("B", converted=True)] * 5 + [_rec("B")] * 5
    assert select_best(records) == "B"


def test_rank_zero_sent_guard():
    # only FAILED records -> nothing sent -> no rows, no ZeroDivisionError
    records = [_rec("A", sent=False), _rec("B", sent=False)]
    assert rank_by_performance(records) == []
    assert select_best(records) is None


def test_rank_variant_with_sent_no_conversions():
    records = [_rec("A")] * 5  # sent, none converted
    ranked = rank_by_performance(records)
    assert ranked == [("A", 5, 0, 0.0)]


def test_epsilon_greedy_exploit_when_epsilon_zero():
    records = [_rec("A")] * 10 + [_rec("B", converted=True)] * 5 + [_rec("B")] * 5
    assert epsilon_greedy(records, epsilon=0.0) == "B"  # best CVR


def test_epsilon_greedy_explore_when_epsilon_one_is_deterministic():
    records = [_rec("A", converted=True)] * 5 + [_rec("A")] * 5 + [_rec("B")] * 10
    # epsilon=1 -> explore; deterministic and stable across calls
    first = epsilon_greedy(records, epsilon=1.0)
    second = epsilon_greedy(records, epsilon=1.0)
    assert first == second
    assert first != select_best(records)  # explores away from the best arm


def test_epsilon_greedy_explore_with_tie_breaker():
    records = [_rec("A", converted=True)] * 5 + [_rec("A")] * 5 + [_rec("B")] * 10
    assert epsilon_greedy(records, epsilon=1.0, tie_breaker="B") == "B"


def test_epsilon_greedy_no_records():
    assert epsilon_greedy([], epsilon=0.5) is None


# --- request validation -------------------------------------------------------
def test_copyrequest_rejects_unsupported_locale():
    with pytest.raises(ValueError):
        CopyRequest(goal="g", product="Wallet", locales=["en", "zz"])


def test_copyrequest_requires_locale():
    with pytest.raises(ValueError):
        CopyRequest(goal="g", product="Wallet", locales=[])


# --- review regression: disclaimer must survive truncation (compliance) -------
def test_disclaimer_survives_truncation_for_fintech_push():
    from copywriting.compliance import check, CHANNEL_MAX_LEN, DISCLAIMER_TEXT

    limit = CHANNEL_MAX_LEN["push"]
    long_loan_copy = "Get an instant loan today " * 20  # well over the push limit
    res = check(long_loan_copy, channel="push", product="Loan")

    assert len(res.fixed_text) <= limit
    # the legally-required disclaimer must still be present after truncation
    assert DISCLAIMER_TEXT.lower() in res.fixed_text.lower()
    assert res.ok is True
    assert any(v.startswith("over_length") for v in res.violations)
