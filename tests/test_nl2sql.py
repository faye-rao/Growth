"""M2-B1~B4: NL2SQL translation + end-to-end (NL -> DSL -> evaluate) parity."""
import pytest

from cohort_engine import CohortEngine
from cohort_engine.nl2sql import translate
from cohort_engine.sample_data import NOW, build_sample_dataset


@pytest.fixture
def engine():
    return CohortEngine(build_sample_dataset(), now=NOW)


# --- B1: natural language -> DSL, then evaluate to the expected audience -------
@pytest.mark.parametrize("text, expected_ids", [
    ("KYC users with balance over 1000 and wallet not activated", {"u1", "u4"}),
    ("android users in UAE", {"u4"}),
    ("users who have not transferred in the last 90 days and are kyc", {"u1", "u4"}),
    ("users who logged out at least 2 times in the last 3 days", {"u1"}),
    ("users in India", {"u2"}),
    ("users with balance under 1000", {"u2", "u3"}),
])
def test_nl_to_audience(engine, text, expected_ids):
    res = translate(text)
    assert engine.evaluate(res.dsl) == expected_ids


# --- B2: DSL is returned transparently for preview/edit ------------------------
def test_dsl_is_previewable():
    res = translate("KYC users")
    assert res.dsl == {"match": {"type": "attribute", "field": "is_kyc", "operator": "eq", "value": True}}


def test_multi_condition_single_clause_ands():
    res = translate("KYC users with balance over 1000")
    node = res.dsl["match"]
    assert node["op"] == "and"
    fields = {c["field"] for c in node["children"]}
    assert fields == {"is_kyc", "balance"}


# --- B3: confidence + human-review fallback ------------------------------------
def test_full_confidence_when_all_clauses_matched():
    res = translate("KYC users and android users")
    assert res.confidence == 1.0
    assert res.requires_review is False
    assert res.unmatched == []


def test_low_confidence_flags_review():
    res = translate("KYC users and flying purple elephants")
    assert 0.0 < res.confidence < 1.0
    assert res.requires_review is True
    assert res.unmatched  # the nonsense clause is reported back


def test_no_match_yields_zero_confidence_empty_match():
    res = translate("completely unintelligible gibberish")
    assert res.confidence == 0.0
    assert res.requires_review is True
    assert res.dsl["match"] == {"op": "and", "children": []}


# --- negation handling ---------------------------------------------------------
def test_negated_event_becomes_not_group():
    res = translate("users who have not transferred in the last 90 days")
    node = res.dsl["match"]
    assert node["op"] == "not"
    assert node["children"][0]["event"] == "Transfer"


def test_or_connector():
    res = translate("users in India or users in Philippines")
    node = res.dsl["match"]
    assert node["op"] == "or"
