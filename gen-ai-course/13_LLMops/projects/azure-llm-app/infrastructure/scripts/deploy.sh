#!/usr/bin/env bash
# ============================================================
# deploy.sh — Build, push, and deploy the LLM App to Azure
# Usage: ./infrastructure/scripts/deploy.sh [dev|staging|prod]
# ============================================================
set -euo pipefail

ENVIRONMENT="${1:-dev}"
APP_NAME="llmapp"
RESOURCE_GROUP="${APP_NAME}-${ENVIRONMENT}-rg"
LOCATION="eastus"
IMAGE_TAG=$(git rev-parse --short HEAD)

echo "========================================"
echo "  Deploying ${APP_NAME} to ${ENVIRONMENT}"
echo "  Image tag: ${IMAGE_TAG}"
echo "  Resource group: ${RESOURCE_GROUP}"
echo "========================================"

# ── Step 1: Ensure Azure CLI is logged in ────────────────────────────────────
echo "[1/7] Checking Azure login..."
az account show --query name -o tsv || { echo "ERROR: Not logged in. Run 'az login' first."; exit 1; }

# ── Step 2: Create resource group (idempotent) ───────────────────────────────
echo "[2/7] Creating resource group..."
az group create \
  --name "$RESOURCE_GROUP" \
  --location "$LOCATION" \
  --tags "environment=$ENVIRONMENT" "application=$APP_NAME" \
  --output none

# ── Step 3: Deploy Bicep infrastructure ─────────────────────────────────────
echo "[3/7] Deploying Azure infrastructure via Bicep..."
DEPLOY_OUTPUT=$(az deployment group create \
  --resource-group "$RESOURCE_GROUP" \
  --template-file infrastructure/bicep/main.bicep \
  --parameters \
      environment="$ENVIRONMENT" \
      appName="$APP_NAME" \
      location="$LOCATION" \
      imageTag="$IMAGE_TAG" \
  --query properties.outputs \
  --output json)

ACR_SERVER=$(echo "$DEPLOY_OUTPUT" | jq -r '.acrLoginServer.value')
APP_URL=$(echo "$DEPLOY_OUTPUT" | jq -r '.containerAppUrl.value')

echo "  ACR: $ACR_SERVER"
echo "  App URL: $APP_URL"

# ── Step 4: Build and push Docker image ──────────────────────────────────────
echo "[4/7] Logging into ACR..."
az acr login --name "${ACR_SERVER%%.*}"

echo "[5/7] Building Docker image..."
docker build \
  --platform linux/amd64 \
  --build-arg BUILD_DATE="$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --build-arg GIT_COMMIT="$IMAGE_TAG" \
  -t "${ACR_SERVER}/llm-app:${IMAGE_TAG}" \
  -t "${ACR_SERVER}/llm-app:latest" \
  .

echo "[6/7] Pushing image to ACR..."
docker push "${ACR_SERVER}/llm-app:${IMAGE_TAG}"
docker push "${ACR_SERVER}/llm-app:latest"

# ── Step 5: Store secrets in Key Vault ───────────────────────────────────────
echo "[7/7] Storing Azure OpenAI API key in Key Vault..."
KV_URI=$(echo "$DEPLOY_OUTPUT" | jq -r '.keyVaultUri.value')
KV_NAME=$(basename "$KV_URI" /)

if [ -n "${AZURE_OPENAI_API_KEY:-}" ]; then
  az keyvault secret set \
    --vault-name "$KV_NAME" \
    --name "azure-openai-api-key" \
    --value "$AZURE_OPENAI_API_KEY" \
    --output none
  echo "  API key stored in Key Vault."
else
  echo "  WARNING: AZURE_OPENAI_API_KEY not set — skipping Key Vault secret."
fi

echo ""
echo "========================================"
echo "  Deployment complete!"
echo "  Environment : $ENVIRONMENT"
echo "  Image tag   : $IMAGE_TAG"
echo "  App URL     : $APP_URL"
echo "  Health check: $APP_URL/health"
echo "========================================"
