import pytest


@pytest.fixture(autouse=True)
def isolated_environment(monkeypatch):
    """Local credentials must not change offline tests or send test traces."""
    monkeypatch.delenv("API_ACCESS_TOKEN", raising=False)
    monkeypatch.setenv("LANGSMITH_TRACING", "false")
