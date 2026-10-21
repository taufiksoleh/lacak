import pytest
from fastapi.testclient import TestClient

from app import db as dbmod
from app.config import get_settings


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    for var in (
        "YOUTUBE_API_KEY",
        "X_BEARER_TOKEN",
        "META_ACCESS_TOKEN",
        "IG_BUSINESS_ACCOUNT_ID",
        "THREADS_ACCESS_TOKEN",
        "ANTHROPIC_API_KEY",
    ):
        monkeypatch.setenv(var, "")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def client(tmp_path):
    dbmod.configure(f"sqlite:///{tmp_path / 'test.db'}")
    from app.main import app

    with TestClient(app) as c:
        yield c
