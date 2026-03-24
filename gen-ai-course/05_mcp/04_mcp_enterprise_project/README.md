# Enterprise MCP Server (uv + Python)

Production-oriented MCP server starter with:
- MCP tools (`get_service_health`, `classify_incident`)
- HTTP runtime for deployment (`/mcp`)
- Auth middleware (JWT shared secret or Microsoft Entra/JWKS)
- OpenTelemetry tracing export (OTLP or console)
- Environment profiles (`dev`, `qa`, `prod`)
- Contract tests for MCP tool schemas

## 1. Project Structure

```text
04_mcp_enterprise_project/
  src/
    enterprise_mcp/
      __init__.py
      auth.py
      config.py
      http_app.py
      server.py
      telemetry.py
  tests/
    test_auth.py
    test_config.py
    test_contract_schemas.py
    test_server.py
  .env.example
  .env.dev
  .env.qa
  .env.prod
  .python-version
  Dockerfile
  pyproject.toml
  README.md
```

## 2. Setup Commands + Expected Output

### 2.1 Install dependencies

```powershell
cd 04_mcp_enterprise_project
uv sync
```

Expected output (example):

```text
Resolved <n> packages
Audited <n> packages
```

### 2.2 Lint

```powershell
uv run ruff check .
```

Expected output:

```text
All checks passed!
```

### 2.3 Run tests

```powershell
uv run pytest
```

Expected output (current project):

```text
collected 6 items
...
6 passed
```

## 3. Runtime Commands + Expected Output

### 3.1 MCP stdio mode (local client integrations)

```powershell
uv run enterprise-mcp-server
```

Expected output:

```text
Process stays running and waits for MCP stdio requests.
```

### 3.2 MCP HTTP mode (deployment mode)

```powershell
Copy-Item .env.dev .env
uv run enterprise-mcp-http
```

Expected output (uvicorn example):

```text
INFO:     Uvicorn running on http://0.0.0.0:8080
INFO:     Application startup complete.
```

## 4. Environment Profiles (`dev`, `qa`, `prod`)

Config loading behavior:
- `.env` is loaded first (if present)
- then `.env.<APP_ENV>` overrides values

### 4.1 Use dev

```powershell
$env:APP_ENV="dev"
Copy-Item .env.dev .env
uv run enterprise-mcp-http
```

Expected defaults:

```text
AUTH_ENABLED=false
OTEL_ENABLED=false
```

### 4.2 Use qa

```powershell
$env:APP_ENV="qa"
Copy-Item .env.qa .env
uv run enterprise-mcp-http
```

Expected defaults:

```text
AUTH_ENABLED=true
AUTH_MODE=entra
OTEL_ENABLED=true
```

### 4.3 Use prod

```powershell
$env:APP_ENV="prod"
Copy-Item .env.prod .env
uv run enterprise-mcp-http
```

Expected defaults:

```text
AUTH_ENABLED=true
AUTH_MODE=entra
OTEL_ENABLED=true
```

## 5. Authentication Functionality

Middleware file: `src/enterprise_mcp/auth.py`

### 5.1 JWT mode (shared secret)

```powershell
$env:AUTH_ENABLED="true"
$env:AUTH_MODE="jwt"
$env:JWT_SHARED_SECRET="replace-with-32-plus-byte-secret"
$env:JWT_AUDIENCE="api://enterprise-mcp-server"
$env:JWT_ISSUER="https://issuer.example.com"
uv run enterprise-mcp-http
```

Expected behavior:
- Bearer token required on `/mcp` requests
- Invalid/missing token returns JSON error with HTTP 401

### 5.2 Entra mode (JWKS)

```powershell
$env:AUTH_ENABLED="true"
$env:AUTH_MODE="entra"
$env:ENTRA_TENANT_ID="<tenant-id>"
$env:JWT_AUDIENCE="api://enterprise-mcp-server"
$env:JWT_ISSUER="https://login.microsoftonline.com/<tenant-id>/v2.0"
uv run enterprise-mcp-http
```

Expected behavior:
- Token signing key fetched from Entra JWKS
- Token `aud` and `iss` validated when configured

### 5.3 Validate auth implementation via tests

```powershell
uv run pytest tests/test_auth.py -q
```

Expected output:

```text
1 passed
```

## 6. Telemetry Functionality (OpenTelemetry)

Telemetry file: `src/enterprise_mcp/telemetry.py`

### 6.1 Console exporter (local)

```powershell
$env:OTEL_ENABLED="true"
$env:OTEL_EXPORTER="console"
uv run enterprise-mcp-http
```

Expected behavior:
- Trace spans printed in console after HTTP requests

### 6.2 OTLP exporter (collector)

```powershell
$env:OTEL_ENABLED="true"
$env:OTEL_EXPORTER="otlp"
$env:OTEL_OTLP_ENDPOINT="http://localhost:4318/v1/traces"
uv run enterprise-mcp-http
```

Expected behavior:
- Spans are exported to configured OTLP endpoint

## 7. MCP Tool Functionality

Tool definitions: `src/enterprise_mcp/server.py`

### 7.1 `get_service_health`
Returns:
- `service`
- `status`
- `timestamp_utc`
- `environment`
- `transport`

### 7.2 `classify_incident`
Input:
- `severity` (string)
- `impact` (string)

Output:
- `priority` (`P1`..`P4`)
- normalized severity/impact
- `owner_team`

### 7.3 Validate tool schema contracts

```powershell
uv run pytest tests/test_contract_schemas.py -q
```

Expected output:

```text
1 passed
```

## 8. Docker Commands + Expected Output

### 8.1 Build image

```powershell
docker build -t enterprise-mcp-server:0.1.0 .
```

Expected output:

```text
Successfully built <image-id>
Successfully tagged enterprise-mcp-server:0.1.0
```

### 8.2 Run container

```powershell
docker run --rm -p 8080:8080 --env-file .env.prod enterprise-mcp-server:0.1.0
```

Expected output:

```text
Uvicorn startup logs
Server listening on port 8080
```

## 9. Azure Container Apps Deployment Commands + Expected Output

### 9.1 Create resources

```powershell
az login
az account set --subscription "<SUBSCRIPTION_ID>"
az group create --name rg-enterprise-mcp --location eastus
az acr create --resource-group rg-enterprise-mcp --name <UNIQUE_ACR_NAME> --sku Standard
az acr login --name <UNIQUE_ACR_NAME>
```

Expected output:

```text
JSON response for each created resource
```

### 9.2 Push image

```powershell
docker tag enterprise-mcp-server:0.1.0 <UNIQUE_ACR_NAME>.azurecr.io/enterprise-mcp-server:0.1.0
docker push <UNIQUE_ACR_NAME>.azurecr.io/enterprise-mcp-server:0.1.0
```

Expected output:

```text
Pushed layers and digest for enterprise-mcp-server:0.1.0
```

### 9.3 Deploy container app

```powershell
az extension add --name containerapp --upgrade
az containerapp env create --name cae-enterprise-mcp --resource-group rg-enterprise-mcp --location eastus
az containerapp create `
  --name ca-enterprise-mcp `
  --resource-group rg-enterprise-mcp `
  --environment cae-enterprise-mcp `
  --image <UNIQUE_ACR_NAME>.azurecr.io/enterprise-mcp-server:0.1.0 `
  --registry-server <UNIQUE_ACR_NAME>.azurecr.io `
  --target-port 8080 `
  --ingress external `
  --cpu 0.5 `
  --memory 1.0Gi `
  --min-replicas 1 `
  --max-replicas 5
```

Expected output:

```text
Container app created with FQDN in properties.configuration.ingress.fqdn
```

### 9.4 Set runtime env vars

```powershell
az containerapp update `
  --name ca-enterprise-mcp `
  --resource-group rg-enterprise-mcp `
  --set-env-vars `
    APP_ENV=prod `
    AUTH_ENABLED=true `
    AUTH_MODE=entra `
    ENTRA_TENANT_ID=<tenant-id> `
    JWT_AUDIENCE=api://enterprise-mcp-server `
    JWT_ISSUER=https://login.microsoftonline.com/<tenant-id>/v2.0 `
    OTEL_ENABLED=true `
    OTEL_EXPORTER=otlp `
    OTEL_OTLP_ENDPOINT=http://otel-collector:4318/v1/traces
```

Expected output:

```text
Container app revision updated successfully
```

## 10. Enterprise Notes

- Use Managed Identity + Key Vault for secrets
- Restrict ingress (private networking or allowlists)
- Send logs/metrics/traces to Azure Monitor
- Keep separate `dev`, `qa`, `prod` revisions and rollout gates
