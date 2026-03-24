from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import jwt
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.status import HTTP_401_UNAUTHORIZED

from enterprise_mcp.config import AppConfig


@dataclass
class TokenValidator:
    config: AppConfig

    def validate(self, token: str) -> dict[str, Any]:
        if self.config.auth_mode == "jwt":
            return self._validate_jwt_shared_secret(token)
        if self.config.auth_mode == "entra":
            return self._validate_entra_token(token)
        raise ValueError(f"Unsupported AUTH_MODE: {self.config.auth_mode}")

    def _validate_jwt_shared_secret(self, token: str) -> dict[str, Any]:
        if not self.config.jwt_shared_secret:
            raise ValueError("JWT_SHARED_SECRET is required when AUTH_MODE=jwt")
        return jwt.decode(
            token,
            self.config.jwt_shared_secret,
            algorithms=["HS256"],
            audience=self.config.jwt_audience,
            issuer=self.config.jwt_issuer,
            options={
                "verify_signature": True,
                "verify_aud": bool(self.config.jwt_audience),
                "verify_iss": bool(self.config.jwt_issuer),
            },
        )

    def _validate_entra_token(self, token: str) -> dict[str, Any]:
        if not self.config.entra_jwks_url:
            raise ValueError("ENTRA_JWKS_URL or ENTRA_TENANT_ID is required when AUTH_MODE=entra")
        jwk_client = jwt.PyJWKClient(self.config.entra_jwks_url)
        signing_key = jwk_client.get_signing_key_from_jwt(token)
        return jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=self.config.jwt_audience,
            issuer=self.config.jwt_issuer,
            options={
                "verify_signature": True,
                "verify_aud": bool(self.config.jwt_audience),
                "verify_iss": bool(self.config.jwt_issuer),
            },
        )


class AuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: Any, validator: TokenValidator) -> None:
        super().__init__(app)
        self.validator = validator

    async def dispatch(self, request: Request, call_next: Any) -> Response:
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.lower().startswith("bearer "):
            return JSONResponse(
                {"error": "missing_bearer_token"},
                status_code=HTTP_401_UNAUTHORIZED,
            )

        token = auth_header[7:].strip()
        try:
            claims = self.validator.validate(token)
            request.state.token_claims = claims
        except Exception as exc:
            return JSONResponse(
                {"error": "invalid_token", "detail": str(exc)},
                status_code=HTTP_401_UNAUTHORIZED,
            )

        return await call_next(request)
