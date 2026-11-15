import pytest

from ecommerce_mcp.config import Settings


def test_local_http_allowed(monkeypatch):
    monkeypatch.setenv("STORE_API_URL", "http://localhost:8080")
    monkeypatch.setenv("STORE_API_KEY", "store_sk_test")
    monkeypatch.delenv("STORE_ALLOW_INSECURE_HTTP", raising=False)
    settings = Settings.from_env()
    assert settings.store_api_url == "http://localhost:8080"
    assert settings.store_api_key == "store_sk_test"


def test_external_http_not_allowed(monkeypatch):
    monkeypatch.setenv("STORE_API_URL", "http://test.example.com:8080")
    monkeypatch.setenv("STORE_API_KEY", "store_sk_test")
    monkeypatch.delenv("STORE_ALLOW_INSECURE_HTTP", raising=False)
    with pytest.raises(ValueError, match="unencrypted HTTP"):
        Settings.from_env()


def test_missing_key(monkeypatch):
    monkeypatch.setenv("STORE_API_URL", "https://test.example.com")
    monkeypatch.delenv("STORE_API_KEY", raising=False)
    with pytest.raises(ValueError, match="STORE_API_KEY"):
        Settings.from_env()
