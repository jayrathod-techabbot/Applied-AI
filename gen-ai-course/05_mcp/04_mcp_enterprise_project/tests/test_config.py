from __future__ import annotations

from enterprise_mcp.config import AppConfig


def test_qa_defaults_to_auth_enabled(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "qa")
    monkeypatch.delenv("AUTH_ENABLED", raising=False)

    config = AppConfig.load()
    assert config.app_env == "qa"
    assert config.auth_enabled is True


def test_dev_defaults_to_auth_disabled(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "dev")
    monkeypatch.delenv("AUTH_ENABLED", raising=False)

    config = AppConfig.load()
    assert config.app_env == "dev"
    assert config.auth_enabled is False
