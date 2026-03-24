from __future__ import annotations

import uvicorn
from starlette.applications import Starlette

from enterprise_mcp.auth import AuthMiddleware, TokenValidator
from enterprise_mcp.config import AppConfig
from enterprise_mcp.server import mcp
from enterprise_mcp.telemetry import configure_telemetry


def create_app(config: AppConfig | None = None) -> Starlette:
    active_config = config or AppConfig.load()
    app = mcp.streamable_http_app()

    if active_config.auth_enabled:
        app.add_middleware(AuthMiddleware, validator=TokenValidator(active_config))

    configure_telemetry(app, active_config)
    return app


def main() -> None:
    config = AppConfig.load()
    uvicorn.run(
        "enterprise_mcp.http_app:create_app",
        factory=True,
        host=config.http_host,
        port=config.http_port,
    )
