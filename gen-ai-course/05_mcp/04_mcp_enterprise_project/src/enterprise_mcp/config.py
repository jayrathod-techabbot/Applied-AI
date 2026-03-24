from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


def _as_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _load_env_files() -> str:
    project_root = Path(__file__).resolve().parents[2]
    base_file = project_root / ".env"
    if base_file.exists():
        load_dotenv(base_file, override=False)

    app_env = os.getenv("APP_ENV", "dev").strip().lower()
    env_file = project_root / f".env.{app_env}"
    if env_file.exists():
        load_dotenv(env_file, override=True)
    return app_env


@dataclass(frozen=True)
class AppConfig:
    app_env: str
    auth_enabled: bool
    auth_mode: str
    jwt_audience: str | None
    jwt_issuer: str | None
    jwt_shared_secret: str | None
    entra_tenant_id: str | None
    entra_jwks_url: str | None
    http_host: str
    http_port: int
    otel_enabled: bool
    otel_exporter: str
    otel_service_name: str
    otel_otlp_endpoint: str

    @staticmethod
    def load() -> "AppConfig":
        env = _load_env_files()
        default_auth = env in {"qa", "prod"}
        tenant_id = os.getenv("ENTRA_TENANT_ID")
        jwks_url = os.getenv("ENTRA_JWKS_URL")
        if not jwks_url and tenant_id:
            jwks_url = (
                f"https://login.microsoftonline.com/{tenant_id}/discovery/v2.0/keys"
            )

        return AppConfig(
            app_env=env,
            auth_enabled=_as_bool(os.getenv("AUTH_ENABLED"), default_auth),
            auth_mode=os.getenv("AUTH_MODE", "jwt").strip().lower(),
            jwt_audience=os.getenv("JWT_AUDIENCE"),
            jwt_issuer=os.getenv("JWT_ISSUER"),
            jwt_shared_secret=os.getenv("JWT_SHARED_SECRET"),
            entra_tenant_id=tenant_id,
            entra_jwks_url=jwks_url,
            http_host=os.getenv("HTTP_HOST", "0.0.0.0"),
            http_port=int(os.getenv("HTTP_PORT", "8080")),
            otel_enabled=_as_bool(os.getenv("OTEL_ENABLED"), default=False),
            otel_exporter=os.getenv("OTEL_EXPORTER", "otlp").strip().lower(),
            otel_service_name=os.getenv("OTEL_SERVICE_NAME", "enterprise-mcp-server"),
            otel_otlp_endpoint=os.getenv(
                "OTEL_OTLP_ENDPOINT", "http://localhost:4318/v1/traces"
            ),
        )
