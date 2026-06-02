"""M2-D2: high-frequency cohort templates evaluate to the expected audiences."""
import pytest

from cohort_engine import CohortEngine
from cohort_engine import templates as T
from cohort_engine.sample_data import NOW, build_sample_dataset


@pytest.fixture
def engine():
    return CohortEngine(build_sample_dataset(), now=NOW)


def test_high_value_wallet_inactive(engine):
    assert engine.evaluate(T.high_value_wallet_inactive(min_balance=1000)) == {"u1", "u4"}
    # raise the bar -> only u1 (5000) qualifies, u4 (1500) drops at >=2000
    assert engine.evaluate(T.high_value_wallet_inactive(min_balance=2000)) == {"u1"}


def test_kyc_no_transfer(engine):
    assert engine.evaluate(T.kyc_no_transfer(days=90)) == {"u1", "u4"}


def test_dormant_users(engine):
    # App Opened in last 30d: u2, u5 -> dormant = everyone else
    assert engine.evaluate(T.dormant_users(event="App Opened", days=30)) == {"u1", "u3", "u4"}


def test_country_segment(engine):
    assert engine.evaluate(T.country_segment(["AE"])) == {"u1", "u4", "u5"}


def test_frequent_event(engine):
    # User Logout >= 2 in last 3 days -> u1 (3 logouts)
    assert engine.evaluate(T.frequent_event("User Logout", times=2, days=3)) == {"u1"}


def test_build_by_name_and_registry(engine):
    spec = T.build("country_segment", codes=["IN"])
    assert engine.evaluate(spec) == {"u2"}
    assert set(T.TEMPLATES) >= {"high_value_wallet_inactive", "kyc_no_transfer", "dormant_users"}


def test_build_unknown_raises():
    with pytest.raises(KeyError):
        T.build("does_not_exist")
