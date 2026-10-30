import pytest
from app.config import settings

@pytest.fixture(autouse=True)
def use_mock_mode_for_unit_tests(monkeypatch):
    # Unit tests must not consume external API credits or require credentials.
    monkeypatch.setattr(settings, "mock_mode", True)
