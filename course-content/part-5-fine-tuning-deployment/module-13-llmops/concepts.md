# Module 13: LLMOps — Core Concepts

## Table of Contents
- [13.1 LLMOps Overview and the AI Lifecycle](#131-llmops-overview-and-the-ai-lifecycle)
- [13.2 Infrastructure Setup](#132-infrastructure-setup)
- [13.3 Deployment Strategies at Scale](#133-deployment-strategies-at-scale)
- [13.4 Monitoring and Observability in LLMOps](#134-monitoring-and-observability-in-llmops)
- [13.5 Security and Compliance for AI Systems](#135-security-and-compliance-for-ai-systems)
- [13.6 Cost Optimization Strategies](#136-cost-optimization-strategies)

---

## 13.1 LLMOps Overview and the AI Lifecycle

LLMOps (Large Language Model Operations) is the set of practices, tools, and processes for deploying, monitoring, and maintaining LLM-powered applications in production. It extends MLOps with LLM-specific concerns such as prompt management, token-level observability, hallucination detection, and model routing.

### LLMOps vs MLOps

| Aspect | MLOps | LLMOps |
|--------|-------|--------|
| **Model Source** | Custom-trained models | Pre-trained foundation models (API or self-hosted) |
| **Core Artifact** | Model weights + training pipeline | Prompts, chains, agents, fine-tuned adapters |
| **Evaluation** | Accuracy, F1, AUC | Hallucination rate, faithfulness, relevance, toxicity |
| **Data Management** | Feature stores, labeled datasets | Prompt templates, RAG corpora, evaluation datasets |
| **Deployment** | Model serving (ONNX, TorchServe) | API gateway, model routing, inference endpoints |
| **Monitoring** | Data drift, prediction drift | Token usage, latency P99, cost per query, safety scores |
| **Iteration Cycle** | Retrain on new data | Prompt tuning, RAG updates, fine-tuning, model swaps |

### The AI Lifecycle for LLM Applications

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│  Design  │───▶│  Build   │───▶│ Evaluate │───▶│  Deploy  │───▶│ Monitor  │
│          │    │          │    │          │    │          │    │          │
│ Use case │    │ Prompt   │    │ Offline  │    │ Canary / │    │ Latency  │
│ selection│    │ eng.     │    │ evals    │    │ Blue-    │    │ Cost     │
│ Arch.    │    │ RAG      │    │ Online   │    │ Green    │    │ Quality  │
│ design   │    │ chains   │    │ A/B      │    │ Rollout  │    │ Safety   │
└──────────┘    └──────────┘    └──────────┘    └──────────┘    └─────┬────┘
      ▲                                                              │
      └──────────────────────────────────────────────────────────────┘
                              Feedback Loop
```

### Key LLMOps Concepts

| Concept | Description |
|---------|-------------|
| **Model Registry** | Central repository for tracking model versions, metadata, and lineage (MLflow, Azure ML) |
| **Experiment Tracking** | Log prompts, parameters, metrics, and artifacts for reproducibility |
| **Pipeline Orchestration** | Automate the flow from data prep → inference → evaluation → deployment |
| **Feature Store for LLMs** | Manage RAG document chunks, embedding indexes, and prompt templates |
| **A/B Testing** | Compare model versions or prompt variants on live traffic |
| **Guard Rails** | Input/output validation, content filtering, and safety classifiers |

### Experiment Tracking with MLflow

```python
import mlflow
import mlflow.openai

mlflow.set_experiment("customer-support-bot")

with mlflow.start_run(run_name="gpt-4o-mini-baseline"):
    # Log parameters
    mlflow.log_param("model", "gpt-4o-mini")
    mlflow.log_param("temperature", 0.3)
    mlflow.log_param("max_tokens", 512)
    mlflow.log_param("prompt_version", "v2.1")

    # Log metrics
    mlflow.log_metric("latency_p50_ms", 420)
    mlflow.log_metric("latency_p99_ms", 1800)
    mlflow.log_metric("hallucination_rate", 0.03)
    mlflow.log_metric("user_satisfaction", 4.2)

    # Log the prompt template as an artifact
    mlflow.log_text(prompt_template, "prompt_template.txt")

    # Log the model (for OpenAI API-based models)
    mlflow.openai.log_model(
        model="gpt-4o-mini",
        task="chat.completions",
        artifact_path="model",
        pip_requirements=["openai", "mlflow"]
    )
```

### Key Takeaways
- LLMOps extends MLOps with prompt management, token observability, and safety monitoring
- The AI lifecycle is iterative: Design → Build → Evaluate → Deploy → Monitor → (repeat)
- Experiment tracking (MLflow) enables reproducibility across prompt and model versions
- A/B testing and model registries are critical for safe, incremental rollouts

---

## 13.2 Infrastructure Setup

LLM application infrastructure spans cloud services for model hosting, vector databases, caching layers, and orchestration. This section covers Azure-native and cloud-agnostic approaches.

### Infrastructure as Code (IaC)

IaC enables reproducible, version-controlled infrastructure provisioning. For LLMOps, this includes AI model endpoints, vector databases, monitoring dashboards, and networking.

#### Bicep (Azure-native)

```bicep
// main.bicep — Azure OpenAI + AI Search + App Service
param location string = resourceGroup().location
param openAiName string = 'contoso-openai-${uniqueString(resourceGroup().id)}'
param searchName string = 'contoso-search-${uniqueString(resourceGroup().id)}'

resource openAi 'Microsoft.CognitiveServices/accounts@2024-06-01-preview' = {
  name: openAiName
  location: location
  kind: 'OpenAI'
  sku: { name: 'S0' }
  properties: {
    publicNetworkAccess: 'Enabled'
    customSubDomainName: openAiName
  }
}

resource gpt4oDeployment 'Microsoft.CognitiveServices/accounts/deployments@2024-06-01-preview' = {
  parent: openAi
  name: 'gpt-4o'
  properties: {
    model: {
      format: 'OpenAI'
      name: 'gpt-4o'
      version: '2024-11-20'
    }
    sku: {
      name: 'Standard'
      capacity: 10
    }
  }
}

resource searchService 'Microsoft.Search/searchServices@2024-03-01-preview' = {
  name: searchName
  location: location
  sku: { name: 'standard' }
  properties: {
    hostingMode: 'default'
    partitionCount: 1
    replicaCount: 1
  }
}

output openAiEndpoint string = openAi.properties.endpoint
output searchEndpoint string = 'https://${searchName}.search.windows.net'
```

#### Terraform (Cloud-agnostic)

```hcl
# main.tf — Multi-cloud LLM infrastructure
terraform {
  required_providers {
    azurerm = { source = "hashicorp/azurerm", version = "~> 3.80" }
  }
}

provider "azurerm" { features {} }

resource "azurerm_cognitive_account" "openai" {
  name                = "contoso-openai"
  location            = "eastus2"
  resource_group_name = azurerm_resource_group.rg.name
  kind                = "OpenAI"
  sku_name            = "S0"

  custom_subdomain_name = "contoso-openai"
}

resource "azurerm_cognitive_deployment" "gpt4o" {
  name                 = "gpt-4o"
  cognitive_account_id = azurerm_cognitive_account.openai.id

  model {
    format  = "OpenAI"
    name    = "gpt-4o"
    version = "2024-11-20"
  }

  sku {
    name     = "Standard"
    capacity = 10
  }
}

resource "azurerm_search_service" "search" {
  name                = "contoso-search"
  resource_group_name = azurerm_resource_group.rg.name
  location            = "eastus2"
  sku                 = "standard"
  replica_count       = 1
  partition_count     = 1
}
```

### Azure AI Infrastructure Components

| Component | Azure Service | Purpose |
|-----------|---------------|---------|
| **LLM Inference** | Azure OpenAI Service | Hosted GPT-4o, GPT-4o-mini, embeddings |
| **Vector Database** | Azure AI Search | Hybrid search + vector similarity |
| **Orchestration** | Azure Container Apps | Host LangChain/LlamaIndex APIs |
| **Caching** | Azure Redis Cache | Semantic cache for repeated queries |
| **Monitoring** | Azure Monitor + App Insights | Traces, metrics, log analytics |
| **Secrets** | Azure Key Vault | API keys, connection strings |
| **CI/CD** | GitHub Actions / Azure DevOps | Automated build, test, deploy pipelines |
| **Container Registry** | Azure Container Registry | Store Docker images for inference |

### Key Takeaways
- Use IaC (Bicep or Terraform) for reproducible, auditable infrastructure
- Azure OpenAI + AI Search + Redis Cache is a common reference architecture
- Separate environments (dev/staging/prod) with parameterized templates
- Store secrets in Key Vault, never in code or config files

---

## 13.3 Deployment Strategies at Scale

Deploying LLM applications requires strategies that minimize risk, manage latency, and handle variable load.

### Deployment Patterns

| Strategy | Description | Risk | Rollback Speed |
|----------|-------------|------|----------------|
| **Blue-Green** | Run two identical environments; switch traffic atomically | Low | Instant (switch DNS) |
| **Canary** | Route small % of traffic to new version; monitor before full rollout | Very Low | Fast (adjust weights) |
| **Rolling** | Update instances incrementally | Medium | Medium |
| **Shadow / Dark Launch** | New version receives mirrored traffic but responses are not served | None | N/A (no user impact) |
| **Feature Flags** | Gate new prompts/models behind runtime toggles | Low | Instant |

### A/B Testing for LLMs

```python
import hashlib
from dataclasses import dataclass
from typing import Literal

@dataclass
class ExperimentConfig:
    experiment_id: str
    variants: dict[str, float]  # variant_name -> traffic_weight
    model_map: dict[str, str]   # variant_name -> model_name

# Define experiment
support_experiment = ExperimentConfig(
    experiment_id="support-bot-v2",
    variants={"control": 0.8, "treatment": 0.2},
    model_map={"control": "gpt-4o-mini", "treatment": "gpt-4o"}
)

def assign_variant(user_id: str, experiment: ExperimentConfig) -> str:
    """Deterministically assign a user to a variant based on user_id hash."""
    hash_val = int(hashlib.sha256(user_id.encode()).hexdigest(), 16)
    bucket = (hash_val % 1000) / 1000.0

    cumulative = 0.0
    for variant, weight in experiment.variants.items():
        cumulative += weight
        if bucket < cumulative:
            return variant
    return list(experiment.variants.keys())[-1]

def get_model_for_user(user_id: str, experiment: ExperimentConfig) -> str:
    variant = assign_variant(user_id, experiment)
    return experiment.model_map[variant]
```

### Model Routing Architecture

```
                         ┌─────────────────┐
                         │   API Gateway    │
                         │  (Rate Limiting, │
                         │   Auth, Routing) │
                         └────────┬────────┘
                                  │
                         ┌────────▼────────┐
                         │  Model Router   │
                         │  - A/B assign   │
                         │  - Fallback     │
                         │  - Cost routing │
                         └────────┬────────┘
                    ┌─────────────┼─────────────┐
                    │             │             │
             ┌──────▼──────┐ ┌───▼────┐ ┌──────▼──────┐
             │  GPT-4o     │ │GPT-4o  │ │ GPT-4o-mini │
             │  (Premium)  │ │-mini   │ │  (Budget)   │
             └─────────────┘ └────────┘ └─────────────┘
```

### Key Takeaways
- Use canary deployments to validate new prompts/models with minimal risk
- A/B testing requires deterministic user assignment (hash-based bucketing)
- Feature flags enable instant rollback without redeployment
- Model routing directs traffic based on cost, quality, and latency requirements

---

## 13.4 Monitoring and Observability in LLMOps

Production LLM applications require observability beyond traditional metrics. Token-level tracing, hallucination detection, and semantic drift monitoring are essential.

### Monitoring Stack

| Layer | What to Monitor | Tools |
|-------|----------------|-------|
| **Infrastructure** | CPU, memory, GPU utilization, pod health | Azure Monitor, Prometheus, Grafana |
| **Application** | Request rate, error rate, latency (P50/P95/P99) | Application Insights, OpenTelemetry |
| **LLM-Specific** | Token count, cost per request, model latency | Custom metrics, Langfuse, Phoenix |
| **Quality** | Hallucination rate, faithfulness, relevance scores | RAGAS, custom evaluators |
| **Safety** | Toxicity, PII leakage, jailbreak attempts | Azure Content Safety, Guardrails AI |
| **Business** | User satisfaction, task completion rate, CSAT | Product analytics, surveys |

### Distributed Tracing with OpenTelemetry

```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.openai import OpenAIInstrumentor

# Setup tracing
provider = TracerProvider()
processor = BatchSpanProcessor(
    OTLPSpanExporter(endpoint="http://localhost:4317")
)
provider.add_span_processor(processor)
trace.set_tracer_provider(provider)

# Auto-instrument OpenAI calls
OpenAIInstrumentor().instrument()

tracer = trace.get_tracer(__name__)

async def handle_query(user_query: str) -> str:
    with tracer.start_as_current_span("llm_query") as span:
        span.set_attribute("user.query_length", len(user_query))
        span.set_attribute("model.name", "gpt-4o-mini")

        # Retrieval step
        with tracer.start_as_current_span("retrieval"):
            docs = await retrieve_documents(user_query)
            span.set_attribute("retrieval.num_docs", len(docs))

        # Generation step
        with tracer.start_as_current_span("generation"):
            response = await generate_response(user_query, docs)
            span.set_attribute("generation.token_count", response.usage.total_tokens)
            span.set_attribute("generation.latency_ms", response.latency_ms)

        return response.content
```

### Key LLMOps Metrics

```python
# Custom metrics collection example
from prometheus_client import Histogram, Counter, Gauge

llm_latency = Histogram(
    "llm_request_duration_seconds",
    "LLM API request latency",
    ["model", "endpoint"],
    buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

llm_tokens = Histogram(
    "llm_tokens_used",
    "Token usage per request",
    ["model", "direction"],  # direction: prompt, completion
    buckets=[10, 50, 100, 250, 500, 1000, 2000, 4000]
)

llm_cost = Counter(
    "llm_cost_usd_total",
    "Cumulative LLM cost in USD",
    ["model"]
)

hallucination_score = Gauge(
    "llm_hallucination_rate",
    "Rolling hallucination detection rate",
    ["model", "evaluator"]
)
```

### Alerting Rules

| Alert | Condition | Severity |
|-------|-----------|----------|
| High Latency | P99 > 5s for 5 min | Warning |
| Elevated Error Rate | 5xx rate > 2% for 3 min | Critical |
| Token Budget Exceeded | Daily tokens > 80% of limit | Warning |
| Hallucination Spike | Hallucination rate > 5% for 15 min | Critical |
| Cost Anomaly | Hourly cost > 2x expected | Warning |
| Safety Violation | Toxicity score > 0.8 on any request | Critical |

### Key Takeaways
- Monitor at infrastructure, application, LLM, quality, safety, and business layers
- Use OpenTelemetry for distributed tracing across retrieval and generation steps
- Track token usage, cost, and latency as first-class metrics
- Set alerts on hallucination rate, safety violations, and cost anomalies

---

## 13.5 Security and Compliance for AI Systems

LLM applications introduce unique security risks including prompt injection, data leakage, and adversarial inputs. Compliance requires handling PII, audit logging, and regulatory alignment.

### Security Threat Model for LLMs

| Threat | Description | Mitigation |
|--------|-------------|------------|
| **Prompt Injection** | Malicious instructions embedded in user input | Input sanitization, system prompt hardening, guardrails |
| **Data Exfiltration** | Model reveals training data or system prompts | Output filtering, differential privacy, canary tokens |
| **PII Leakage** | User PII appears in model outputs | PII detection + redaction, data minimization |
| **Jailbreaking** | Bypassing safety guardrails via adversarial prompts | Content classifiers, multi-layer filtering |
| **Indirect Prompt Injection** | Malicious content in RAG documents triggers unsafe behavior | Document validation, output verification |
| **Model Theft** | Extracting model weights or capabilities via API queries | Rate limiting, query monitoring, watermarking |

### Security Best Practices

```python
from azure.ai.contentsafety import ContentSafetyClient
from azure.ai.contentsafety.models import AnalyzeTextOptions
from azure.core.credentials import AzureKeyCredential

class LLMSafetyPipeline:
    def __init__(self):
        self.content_safety = ContentSafetyClient(
            endpoint="https://contoso.contentsafety.cognitiveservices.azure.com/",
            credential=AzureKeyCredential("<key>")
        )

    def check_input(self, user_input: str) -> dict:
        """Pre-inference safety check."""
        result = {}

        # Content safety analysis
        response = self.content_safety.analyze_text(
            AnalyzeTextOptions(text=user_input)
        )
        result["hate_severity"] = response.hate_result.severity
        result["self_harm_severity"] = response.self_harm_result.severity
        result["sexual_severity"] = response.sexual_result.severity
        result["violence_severity"] = response.violence_result.severity

        # PII detection
        result["pii_detected"] = self._detect_pii(user_input)

        # Prompt injection detection
        result["injection_risk"] = self._detect_injection(user_input)

        return result

    def check_output(self, model_output: str) -> dict:
        """Post-inference safety check."""
        result = {}
        result["hallucination_score"] = self._check_hallucination(model_output)
        result["pii_leaked"] = self._detect_pii(model_output)
        return result

    def _detect_pii(self, text: str) -> bool:
        import re
        patterns = {
            "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            "ssn": r'\b\d{3}-\d{2}-\d{4}\b',
            "phone": r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
            "credit_card": r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'
        }
        return any(re.search(p, text) for p in patterns.values())

    def _detect_injection(self, text: str) -> str:
        injection_signals = [
            "ignore previous instructions",
            "ignore all previous",
            "system prompt",
            "you are now",
            "disregard safety",
            "act as if",
            "pretend you are"
        ]
        text_lower = text.lower()
        matches = [s for s in injection_signals if s in text_lower]
        if matches:
            return "high"
        return "low"
```

### Compliance Framework Mapping

| Regulation | Requirement | LLMOps Implementation |
|------------|-------------|----------------------|
| **GDPR** | Right to erasure, data minimization | Log retention policies, PII redaction in prompts |
| **SOC 2** | Access control, audit logging | RBAC, immutable audit trails, Key Vault for secrets |
| **HIPAA** | PHI protection, encryption at rest | Azure OpenAI data residency, no training on customer data |
| **EU AI Act** | Risk classification, transparency | Model cards, bias audits, human-in-the-loop for high-risk |
| **CCPA** | Consumer data rights, opt-out | Data deletion pipelines, consent management |

### Key Takeaways
- Implement multi-layer defense: input filtering → prompt hardening → output validation
- Use Azure Content Safety or similar services for automated content classification
- PII detection must run on both inputs and outputs
- Compliance requires audit logging, data residency controls, and model documentation

---

## 13.6 Cost Optimization Strategies

LLM costs scale with token usage, model tier, and request volume. Effective optimization reduces spend without sacrificing quality.

### Cost Model Comparison

| Model | Input ($/1M tokens) | Output ($/1M tokens) | Use Case |
|-------|--------------------|-----------------------|----------|
| GPT-4o | $2.50 | $10.00 | Complex reasoning, high-quality generation |
| GPT-4o-mini | $0.15 | $0.60 | Simple tasks, classification, extraction |
| GPT-3.5-turbo | $0.50 | $1.50 | Legacy, high-throughput simple tasks |
| text-embedding-3-small | $0.02 | — | Embeddings for RAG |
| text-embedding-3-large | $0.13 | — | High-quality embeddings |

### Optimization Techniques

| Technique | Description | Savings Potential |
|-----------|-------------|-------------------|
| **Model Routing** | Use cheaper models for simple tasks, premium for complex | 40-70% |
| **Semantic Caching** | Cache responses for semantically similar queries | 20-50% |
| **Prompt Compression** | Reduce prompt token count without losing meaning | 10-30% |
| **Batch Processing** | Group non-real-time requests into batches | 15-25% |
| **Token Budgets** | Set per-user/per-team token limits | Variable |
| **Streaming** | Reduce perceived latency without reducing actual cost | UX improvement |

### Model Routing Implementation

```python
from enum import Enum
from openai import AsyncOpenAI

class ModelTier(Enum):
    BUDGET = "gpt-4o-mini"
    STANDARD = "gpt-4o"
    PREMIUM = "gpt-4o"

async def classify_complexity(query: str) -> ModelTier:
    """Route queries to appropriate model tier based on complexity."""
    # Use a cheap model to classify query complexity
    client = AsyncOpenAI()
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{
            "role": "system",
            "content": "Classify query complexity. Respond with ONLY: simple, moderate, or complex."
        }, {
            "role": "user",
            "content": query
        }],
        max_tokens=10,
        temperature=0
    )
    complexity = response.choices[0].message.content.strip().lower()

    if complexity == "simple":
        return ModelTier.BUDGET
    elif complexity == "moderate":
        return ModelTier.STANDARD
    return ModelTier.PREMIUM

async def route_query(query: str) -> str:
    """Route query to the appropriate model."""
    tier = await classify_complexity(query)
    client = AsyncOpenAI()

    response = await client.chat.completions.create(
        model=tier.value,
        messages=[{"role": "user", "content": query}],
        max_tokens=1024
    )
    return response.choices[0].message.content
```

### Semantic Caching

```python
import hashlib
import numpy as np
from openai import AsyncOpenAI

class SemanticCache:
    def __init__(self, similarity_threshold: float = 0.95):
        self.cache: dict[str, tuple[np.ndarray, str]] = {}
        self.threshold = similarity_threshold
        self.client = AsyncOpenAI()

    async def _get_embedding(self, text: str) -> np.ndarray:
        response = await self.client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return np.array(response.data[0].embedding)

    async def get(self, query: str) -> str | None:
        embedding = await self._get_embedding(query)
        for key, (cached_emb, response) in self.cache.items():
            similarity = np.dot(embedding, cached_emb) / (
                np.linalg.norm(embedding) * np.linalg.norm(cached_emb)
            )
            if similarity >= self.threshold:
                return response
        return None

    async def set(self, query: str, response: str):
        embedding = await self._get_embedding(query)
        key = hashlib.sha256(query.encode()).hexdigest()
        self.cache[key] = (embedding, response)

# Usage
cache = SemanticCache(similarity_threshold=0.95)

async def get_response(query: str) -> str:
    # Check cache first
    cached = await cache.get(query)
    if cached:
        return cached  # Zero LLM cost

    # Generate response
    client = AsyncOpenAI()
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": query}]
    )
    result = response.choices[0].message.content

    # Store in cache
    await cache.set(query, result)
    return result
```

### Cost Monitoring Dashboard Metrics

| Metric | Description | Alert Threshold |
|--------|-------------|-----------------|
| **Daily Spend** | Total API cost per day | > 120% of budget |
| **Cost per Query** | Average cost per user query | Trending up > 20% |
| **Token Utilization** | Prompt tokens vs completion tokens ratio | Completion > 80% of total |
| **Cache Hit Rate** | % of queries served from cache | < 30% (low effectiveness) |
| **Model Distribution** | % of requests per model tier | Premium > 40% (over-use) |

### Key Takeaways
- Model routing can reduce costs by 40-70% without quality loss on simple tasks
- Semantic caching eliminates redundant API calls for similar queries
- Monitor cost per query and cache hit rate as primary efficiency metrics
- Use token budgets to prevent runaway costs from individual users or teams
