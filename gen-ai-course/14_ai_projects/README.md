# AI Projects — Master Guide

## Projects in this Repository

| Project | Stack | Azure Services | Folder |
|---|---|---|---|
| Market Intelligence Agent | LangChain, RAG | OpenAI, AI Search, Blob, Container Apps | `market_intelligence_agent/` |
| Multi-Agent Researcher | CrewAI, LangChain | OpenAI, AI Search, Cosmos DB, Container Apps | `multi_agent_researcher/` |
| LLM Book Recommender | LangChain, Embeddings | OpenAI, AI Search, Container Apps | `book_recommender/` |
| Customer Support Engine | LangGraph, RAG | OpenAI, AI Search, Cosmos DB, Container Apps | `customer_support_engine/` |

---

## Shared Azure Setup (Do This Once)

### Prerequisites

```bash
# 1. Install Azure CLI
# https://learn.microsoft.com/en-us/cli/azure/install-azure-cli

# 2. Login
az login

# 3. Set your subscription
az account set --subscription "<your-subscription-id>"

# 4. Register required providers
az provider register --namespace Microsoft.App            # Container Apps
az provider register --namespace Microsoft.CognitiveServices  # OpenAI
az provider register --namespace Microsoft.Search         # AI Search
az provider register --namespace Microsoft.DocumentDB     # Cosmos DB
az provider register --namespace Microsoft.ContainerRegistry
```

### Create Shared Resources

```bash
# Resource group (all projects can share one for dev)
az group create --name rg-ai-projects --location eastus

# Azure Container Registry (shared across all projects)
az acr create \
  --resource-group rg-ai-projects \
  --name <your-acr-name> \
  --sku Basic \
  --admin-enabled true

# Azure OpenAI (shared)
az cognitiveservices account create \
  --name ai-projects-openai \
  --resource-group rg-ai-projects \
  --kind OpenAI \
  --sku S0 \
  --location eastus

# Deploy GPT-4o
az cognitiveservices account deployment create \
  --name ai-projects-openai \
  --resource-group rg-ai-projects \
  --deployment-name gpt-4o \
  --model-name gpt-4o \
  --model-version "2024-05-13" \
  --model-format OpenAI \
  --sku-capacity 10 \
  --sku-name Standard

# Deploy ada-002 embeddings
az cognitiveservices account deployment create \
  --name ai-projects-openai \
  --resource-group rg-ai-projects \
  --deployment-name text-embedding-ada-002 \
  --model-name text-embedding-ada-002 \
  --model-version "2" \
  --model-format OpenAI \
  --sku-capacity 10 \
  --sku-name Standard

# Container Apps Environment (shared)
az containerapp env create \
  --name ai-projects-env \
  --resource-group rg-ai-projects \
  --location eastus
```

---

## Per-Project Azure Resource Setup

### Market Intelligence Agent

```bash
# Azure AI Search
az search service create \
  --name market-intel-search \
  --resource-group rg-ai-projects \
  --sku basic \
  --location eastus

# Azure Blob Storage
az storage account create \
  --name marketintelreports \
  --resource-group rg-ai-projects \
  --sku Standard_LRS

az storage container create \
  --name reports \
  --account-name marketintelreports
```

### Multi-Agent Researcher

```bash
# Azure AI Search
az search service create \
  --name researcher-search \
  --resource-group rg-ai-projects \
  --sku basic \
  --location eastus

# Azure Cosmos DB
az cosmosdb create \
  --name researcher-cosmos \
  --resource-group rg-ai-projects \
  --kind GlobalDocumentDB \
  --locations regionName=eastus

az cosmosdb sql database create \
  --account-name researcher-cosmos \
  --resource-group rg-ai-projects \
  --name researcher_db

az cosmosdb sql container create \
  --account-name researcher-cosmos \
  --resource-group rg-ai-projects \
  --database-name researcher_db \
  --name memory \
  --partition-key-path "/session_id"
```

### Book Recommender

```bash
# Azure AI Search
az search service create \
  --name book-recommender-search \
  --resource-group rg-ai-projects \
  --sku basic \
  --location eastus
```

### Customer Support Engine

```bash
# Azure AI Search (Knowledge Base)
az search service create \
  --name support-kb-search \
  --resource-group rg-ai-projects \
  --sku basic \
  --location eastus

# Azure Cosmos DB (conversation state)
az cosmosdb create \
  --name support-cosmos \
  --resource-group rg-ai-projects \
  --kind GlobalDocumentDB \
  --locations regionName=eastus

az cosmosdb sql database create \
  --account-name support-cosmos \
  --resource-group rg-ai-projects \
  --name support_db

az cosmosdb sql container create \
  --account-name support-cosmos \
  --resource-group rg-ai-projects \
  --database-name support_db \
  --name conversations \
  --partition-key-path "/conversation_id"

# Application Insights (observability)
az monitor app-insights component create \
  --app support-engine-insights \
  --location eastus \
  --resource-group rg-ai-projects
```

---

## Deploying Any Project to Container Apps

```bash
# 1. Build and push image
PROJECT=market_intelligence_agent   # change per project
IMAGE_NAME=market-intel             # change per project
PORT=8000                           # 8000 / 8001 / 8002 / 8003

cd $PROJECT
az acr build \
  --registry <your-acr-name> \
  --image $IMAGE_NAME:latest .

# 2. Create Container App
az containerapp create \
  --name $IMAGE_NAME-app \
  --resource-group rg-ai-projects \
  --environment ai-projects-env \
  --image <your-acr-name>.azurecr.io/$IMAGE_NAME:latest \
  --target-port $PORT \
  --ingress external \
  --min-replicas 1 \
  --max-replicas 3 \
  --env-vars \
    AZURE_OPENAI_ENDPOINT=<value> \
    AZURE_OPENAI_API_KEY=secretref:openai-key \
    APP_ENV=production
```

---

## UV Quickstart (all projects)

```bash
# Install UV (if not already)
curl -LsSf https://astral.sh/uv/install.sh | sh

# In any project folder:
uv venv                  # creates .venv
uv sync                  # installs all deps from pyproject.toml
uv sync --extra dev      # includes dev/test dependencies

# Run any command in the venv
uv run uvicorn src/<module>/main:app --reload
uv run pytest tests/ -v
uv run ruff check .
```

---

## Project Documentation Index

| File | Purpose |
|---|---|
| `README.md` | Architecture diagram, setup instructions, project structure |
| `INTERVIEW.md` | Prepared Q&A for technical interviews |
| `pyproject.toml` | UV project config and dependencies |
| `.env.example` | All required environment variables with descriptions |
| `infra/main.bicep` | Azure infrastructure as code |
