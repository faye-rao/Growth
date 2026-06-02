import pytest

from cohort_engine import CohortEngine
from cohort_engine.sample_data import NOW, build_sample_dataset


@pytest.fixture
def dataset():
    return build_sample_dataset()


@pytest.fixture
def now():
    return NOW


@pytest.fixture
def engine(dataset, now):
    return CohortEngine(dataset, now=now)
