import pytest

from squad.store import Store
from tests.fakes import TZ, FakeLLM


@pytest.fixture
def tz():
    return TZ


@pytest.fixture
def store(tmp_path):
    return Store(tmp_path / "squad.json")


@pytest.fixture
def fake_llm():
    return FakeLLM()
