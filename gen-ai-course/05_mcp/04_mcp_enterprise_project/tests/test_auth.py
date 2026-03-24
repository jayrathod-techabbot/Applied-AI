from __future__ import annotations

import jwt

from enterprise_mcp.auth import TokenValidator
from enterprise_mcp.config import AppConfig


def test_jwt_token_validation_shared_secret() -> None:
    config = AppConfig(
        app_env="dev",
        auth_enabled=True,
        auth_mode="jwt",
        jwt_audience="api://enterprise-mcp-server",
        jwt_issuer="https://issuer.example.com",
        jwt_shared_secret="unit-test-secret-which-is-at-least-32-bytes",
        entra_tenant_id=None,
        entra_jwks_url=None,
        http_host="0.0.0.0",
        http_port=8080,
        otel_enabled=False,
        otel_exporter="console",
        otel_service_name="enterprise-mcp-server",
        otel_otlp_endpoint="http://localhost:4318/v1/traces",
    )

    token = jwt.encode(
        {
            "sub": "user-123",
            "aud": "api://enterprise-mcp-server",
            "iss": "https://issuer.example.com",
        },
        "unit-test-secret-which-is-at-least-32-bytes",
        algorithm="HS256",
    )

    claims = TokenValidator(config).validate(token)
    assert claims["sub"] == "user-123"
