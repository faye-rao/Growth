"""M2-A7: JSON DSL parsing & validation (MoEngage-syntax-compatible layer)."""
import pytest

from cohort_engine.models import AttributeCondition, EventCondition, Group
from cohort_engine.parser import RuleParseError, parse_segment


def test_parse_simple_attribute():
    seg = parse_segment({"name": "kyc", "match": {"type": "attribute", "field": "is_kyc", "operator": "eq", "value": True}})
    assert seg.name == "kyc"
    assert isinstance(seg.match, AttributeCondition)
    assert (seg.match.field, seg.match.operator, seg.match.value) == ("is_kyc", "eq", True)


def test_parse_nested_group():
    spec = {
        "match": {
            "op": "and",
            "children": [
                {"type": "attribute", "field": "is_kyc", "operator": "eq", "value": True},
                {"op": "or", "children": [
                    {"type": "attribute", "field": "balance", "operator": "gte", "value": 1000},
                    {"type": "attribute", "field": "country", "operator": "in", "value": ["AE"]},
                ]},
            ],
        }
    }
    seg = parse_segment(spec)
    assert isinstance(seg.match, Group) and seg.match.op == "and"
    assert isinstance(seg.match.children[1], Group) and seg.match.children[1].op == "or"


def test_parse_event_with_where():
    spec = {"match": {
        "type": "event", "event": "User Logout",
        "frequency": {"op": "predominantly"}, "within_days": 3,
        "where": {"type": "attribute", "field": "device_height", "operator": "eq", "value": 5},
    }}
    seg = parse_segment(spec)
    assert isinstance(seg.match, EventCondition)
    assert seg.match.frequency.op == "predominantly"
    assert isinstance(seg.match.where, AttributeCondition)


def test_parse_exclude():
    seg = parse_segment({
        "match": {"type": "attribute", "field": "is_kyc", "operator": "eq", "value": True},
        "exclude": {"type": "attribute", "field": "country", "operator": "in", "value": ["IN"]},
    })
    assert isinstance(seg.exclude, AttributeCondition)


# --- validation / error paths ---
def test_missing_match_raises():
    with pytest.raises(RuleParseError):
        parse_segment({"name": "x"})


def test_unknown_attribute_operator_raises():
    with pytest.raises(RuleParseError):
        parse_segment({"match": {"type": "attribute", "field": "f", "operator": "weird", "value": 1}})


def test_in_operator_requires_list():
    with pytest.raises(RuleParseError):
        parse_segment({"match": {"type": "attribute", "field": "country", "operator": "in", "value": "AE"}})


def test_between_requires_two_elements():
    with pytest.raises(RuleParseError):
        parse_segment({"match": {"type": "attribute", "field": "balance", "operator": "between", "value": [1]}})


def test_bad_frequency_op_raises():
    with pytest.raises(RuleParseError):
        parse_segment({"match": {"type": "event", "event": "X", "frequency": {"op": "sometimes"}}})


def test_at_least_requires_numeric_value():
    with pytest.raises(RuleParseError):
        parse_segment({"match": {"type": "event", "event": "X", "frequency": {"op": "at_least"}}})


def test_event_not_allowed_inside_where():
    spec = {"match": {
        "type": "event", "event": "User Logout", "frequency": {"op": "at_least", "value": 1},
        "where": {"type": "event", "event": "Nested", "frequency": {"op": "at_least", "value": 1}},
    }}
    with pytest.raises(RuleParseError):
        parse_segment(spec)


def test_negative_within_days_raises():
    with pytest.raises(RuleParseError):
        parse_segment({"match": {"type": "event", "event": "X", "frequency": {"op": "at_least", "value": 1}, "within_days": -3}})
