# Module 8: CI/CD for AI — Core Concepts

## Table of Contents
- [8.1 Versioning AI Models and Prompts](#81-versioning-ai-models-and-prompts)
- [8.2 Automated Deployment Pipelines for LLM Apps](#82-automated-deployment-pipelines-for-llm-apps)

---

## 8.1 Versioning AI Models and Prompts

Versioning in AI systems extends beyond traditional code versioning. You must track model weights, training data, prompt templates, configurations, and evaluation metrics alongside application code. Without proper versioning, reproducing results, debugging regressions, and rolling back to stable states becomes impossible.

### 8.1.1 Git Versioning for ML/AI (DVC, Model Registry)

Standard Git workflows need adaptations for ML projects. Large files (model weights, datasets) require Git LFS or external storage. Branching strategies should account for experiment parallelism and model promotion lifecycles.

#### DVC (Data Version Control)

DVC extends Git to handle large files, datasets, and ML models by storing pointers in Git while the actual data lives in remote storage (S3, Azure Blob, GCS).

```bash
# Initialize DVC in a Git repo
git init
dvc init

# Track a model file
dvc add models/llm_finetuned.bin
git add models/llm_finetuned.bin.dvc .gitignore

# Configure remote storage
dvc remote add -d myremote azure://mycontainer/dvcstore
dvc push  # Push data to remote

# Reproduce a pipeline
dvc repro

# Compare experiments
dvc params diff
dvc metrics diff
```

**DVC Pipeline Definition (`dvc.yaml`):**

```yaml
stages:
  prepare:
    cmd: python src/prepare_data.py
    deps:
      - src/prepare_data.py
      - data/raw/
    outs:
      - data/processed/

  train:
    cmd: python src/train.py --config params.yaml
    deps:
      - src/train.py
      - data/processed/
    params:
      - train.learning_rate
      - train.epochs
      - train.lora_rank
    outs:
      - models/fine_tuned/
    metrics:
      - metrics/train.json:
          cache: false

  evaluate:
    cmd: python src/evaluate.py
    deps:
      - src/evaluate.py
      - models/fine_tuned/
    metrics:
      - metrics/eval.json:
          cache: false
    plots:
      - plots/confusion_matrix.json
```

#### Model Registry

A Model Registry is a centralized catalog for managing model versions, stages (staging, production, archived), and lineage tracking.

| Feature | DVC | Model Registry (MLflow/Azure ML) |
|---------|-----|----------------------------------|
| Large file storage | Yes (remote storage) | Yes (artifact store) |
| Version control integration | Git-native | API/SDK-based |
| Stage management | No | Yes (Staging, Production) |
| Lineage tracking | Pipeline-based | Experiment-based |
| Collaboration | Git workflows | UI + API access |
| Best for | Data science teams | MLOps/Production teams |

#### Git Versioning Best Practices

| Practice | Description |
|----------|-------------|
| Git LFS for binaries | Track `*.bin`, `*.safetensors`, `*.onnx` with LFS |
| DVC for datasets | Track large datasets and model artifacts separately |
| Branch strategy | Use feature branches for experiments, release branches for staging |
| Commit messages | Include experiment ID and key metrics |
| `.gitignore` | Exclude local model caches, virtual environments |

```bash
# Git LFS setup for model files
git lfs install
git lfs track "*.bin"
git lfs track "*.safetensors"
git lfs track "*.onnx"
git add .gitattributes

# DVC setup for dataset tracking
dvc init
dvc add data/training_dataset.csv
git add data/training_dataset.csv.dvc .gitignore
git commit -m "Track training dataset with DVC"

# Push data to remote storage
dvc remote add -d myremote azure://mycontainer/dvc-store
dvc push
```

#### Recommended Branch Strategy for AI Projects

```
main (production)
  ├── develop (integration)
  │     ├── feature/prompt-v3-experiments
  │     ├── feature/new-retrieval-strategy
  │     └── feature/evaluation-suite
  ├── release/v2.1 (staging)
  └── hotfix/prompt-regression (emergency fix)
```

**Key Takeaway:** Use DVC for experiment tracking and data versioning during development; use a Model Registry for production stage management and governance. Version models, data, prompts, and code together — they are all interdependent.

---

### 8.1.2 Model Versioning (MLflow, Azure ML)

Model versioning captures the complete lineage: which code, data, hyperparameters, and environment produced a given model artifact. This enables reproducibility and audit trails.

#### MLflow Model Versioning

```python
import mlflow
from mlflow.tracking import MlflowClient

# Set tracking URI
mlflow.set_tracking_uri("http://localhost:5000")

# Log a model
with mlflow.start_run(run_name="llm-v2.1"):
    mlflow.log_params({
        "base_model": "meta-llama/Llama-3-8B",
        "lora_rank": 16,
        "lora_alpha": 32,
        "learning_rate": 2e-4,
        "epochs": 3,
        "batch_size": 4,
    })

    # Training loop (simplified)
    for epoch in range(3):
        train_loss = train_one_epoch(model, train_loader)
        val_loss = evaluate(model, val_loader)
        mlflow.log_metrics({
            "train_loss": train_loss,
            "val_loss": val_loss,
        }, step=epoch)

    # Log the fine-tuned model
    mlflow.pytorch.log_model(
        model,
        artifact_path="model",
        registered_model_name="llama3-8b-lora"
    )

    mlflow.log_artifact("evaluation_results.json")

# Register model and transition to production
client = MlflowClient()
model_version = client.create_model_version(
    name="llama3-8b-lora",
    source="runs:/<run_id>/model",
    description="v2.1 - improved prompt templates"
)

client.transition_model_version_stage(
    name="llama3-8b-lora",
    version=model_version.version,
    stage="Production"
)
```

#### Azure ML Model Registry

```python
from azure.ai.ml import MLClient
from azure.ai.ml.entities import Model
from azure.identity import DefaultAzureCredential

credential = DefaultAzureCredential()
ml_client = MLClient(credential, subscription_id, resource_group, workspace_name)

# Register a model
model = Model(
    path="azureml://datastores/workspaceblobstore/paths/models/v2.1",
    name="llm-classifier",
    description="GPT-based text classifier v2.1",
    tags={"framework": "pytorch", "task": "classification"},
    version="3"
)
registered_model = ml_client.models.create_or_update(model)

# Get a specific version
prod_model = ml_client.models.get(name="llm-classifier", version="3")

# List all versions
all_versions = ml_client.models.list(name="llm-classifier")
```

#### Comparison: MLflow vs Azure ML

| Aspect | MLflow | Azure ML |
|--------|--------|----------|
| **Tracking** | `mlflow.log_metric()`, `mlflow.log_param()` | SDK + Studio UI |
| **Artifacts** | `mlflow.log_artifact()` | `MLClient.models.create()` |
| **Registry** | MLflow Model Registry (staging, production) | Azure ML Model Registry |
| **Reproducibility** | `mlflow.run()` with `MLproject` file | Pipeline jobs |
| **UI** | MLflow Tracking Server UI | Azure ML Studio |
| **Integration** | Framework-agnostic | Azure ecosystem |

#### Model Versioning Best Practices

| Practice | Description |
|----------|-------------|
| Semantic versioning | Use MAJOR.MINOR.PATCH (e.g., 2.1.3) |
| Metadata tagging | Include framework, dataset, hyperparameters |
| Stage transitions | Development → Staging → Production → Archived |
| Immutable versions | Never modify a registered version; create a new one |
| Lineage tracking | Link model → training data → code commit |
| A/B testing support | Register multiple versions for parallel evaluation |

**Key Takeaway:** Always register models with rich metadata and use stage transitions to enforce governance before production deployment.

---

### 8.1.3 Prompt Versioning Strategies

Prompt versioning is critical for LLM applications because prompt changes can dramatically affect output quality. Unlike code, prompts are "soft" assets that require their own versioning discipline.

#### Strategy 1: Git-Based Prompt Versioning

Store prompts as files in the repository with a structured directory layout:

```
prompts/
├── chatbot/
│   ├── system_prompt/
│   │   ├── v1.yaml    ← archived
│   │   ├── v2.yaml    ← production
│   │   └── v3.yaml    ← staging
│   └── summarization/
│       ├── v1.yaml
│       └── v2.yaml    ← production
└── support/
    └── triage/
        ├── v1.yaml
        └── v2.yaml    ← production
```

**Example YAML prompt file (`prompts/chatbot/system_prompt/v2.yaml`):**

```yaml
version: "2.0"
author: "team-nlp"
created: "2025-11-15"
model_target: "gpt-4o"
tags: ["chatbot", "production"]
eval_score: 0.87

system_prompt: |
  You are a precise summarization assistant. Given a document, produce a
  concise summary that captures the key points. Follow these rules:
  - Maximum 3 sentences
  - Include specific numbers and dates when present
  - Do not add information not in the source

user_template: |
  Summarize the following document:

  <document>
  {document_text}
  </document>

evaluation:
  metric: "rouge_l"
  threshold: 0.75
  test_set: "summarization_benchmark_v2"
```

#### Strategy 2: Database-Backed Prompt Registry

```python
import yaml
from pathlib import Path


class PromptRegistry:
    """A centralized prompt versioning registry backed by YAML files."""

    def __init__(self, prompts_dir: str = "prompts"):
        self.prompts_dir = Path(prompts_dir)
        self._cache: dict = {}

    def get_prompt(self, name: str, version: str = "latest") -> dict:
        if version == "latest":
            version = self._get_latest_version(name)

        prompt_path = self.prompts_dir / version / f"{name}.yaml"
        if not prompt_path.exists():
            raise FileNotFoundError(f"Prompt {name} v{version} not found")

        with open(prompt_path) as f:
            return yaml.safe_load(f)

    def _get_latest_version(self, name: str) -> str:
        versions = sorted(
            d.name for d in self.prompts_dir.iterdir() if d.is_dir()
        )
        return versions[-1]


# Usage
registry = PromptRegistry()
prompt_config = registry.get_prompt("summarization", "v2")
system_msg = prompt_config["system_prompt"]
user_msg = prompt_config["user_template"].format(document_text=doc_text)
```

#### Strategy 3: A/B Testing with Feature Flags

```python
class PromptFeatureFlag:
    """Route users to different prompt versions based on feature flags."""

    def get_prompt_version(self, user_id: str, prompt_name: str) -> str:
        flag = self.flags.get(f"prompt_{prompt_name}")

        if flag is None or not flag.enabled:
            return "v2"  # default

        if flag.rollout_percentage == 100:
            return flag.target_version

        # Deterministic bucketing based on user ID hash
        bucket = hash(user_id) % 100
        if bucket < flag.rollout_percentage:
            return flag.target_version

        return "v2"  # control group
```

#### Prompt Versioning Comparison

| Strategy | Pros | Cons |
|----------|------|------|
| Git-based | Simple, auditable, diff-able | No runtime promotion, manual tracking |
| Database-backed | Programmatic access, A/B testing, metrics | Requires infrastructure |
| Hybrid (Git + DB) | Best of both worlds | More complex setup |
| Feature flags | Gradual rollout, kill switches | Flag management overhead |
| Inline in code | Rapid prototyping | Not production-ready |

**Key Takeaway:** Treat prompts as first-class artifacts. Version them, test them, and promote them through stages just like code.

---

### 8.1.4 Automated Testing for LLM Apps

Testing AI applications requires both traditional software tests and AI-specific evaluations. Unlike deterministic code, LLM outputs are probabilistic, requiring statistical and semantic testing approaches.

| Test Type | What It Tests | Tools / Approaches |
|-----------|---------------|--------------------|
| **Unit tests** | Individual functions, parsers, validators | pytest, unittest |
| **Integration tests** | API endpoints, tool calls, chain execution | pytest + httpx, mock LLM calls |
| **Prompt regression tests** | Output quality doesn't degrade across prompt changes | Custom eval harness, promptfoo |
| **Semantic similarity tests** | Outputs are semantically equivalent to expected answers | Embedding cosine similarity, BERTScore |
| **Evaluation benchmarks** | Performance on standardized tasks | lm-eval-harness, custom datasets |
| **Guardrail tests** | Safety filters, output validation, PII detection | NeMo Guardrails, custom validators |
| **Load / performance tests** | Latency, throughput under concurrent requests | Locust, k6 |

#### Unit Tests (Deterministic Logic)

```python
import pytest
from src.prompts.builder import PromptBuilder


class TestPromptBuilder:
    def test_classification_prompt_structure(self):
        builder = PromptBuilder(template_file="prompts/classification/v2.0.txt")
        result = builder.build(
            text="This product is amazing!",
            categories=["positive", "negative", "neutral"],
        )
        assert "This product is amazing!" in result
        assert "positive" in result
        assert "negative" in result
        assert "neutral" in result

    def test_prompt_truncation(self):
        builder = PromptBuilder(
            template_file="prompts/classification/v2.0.txt", max_tokens=100
        )
        long_text = "word " * 500
        result = builder.build(text=long_text, categories=["a", "b"])
        token_count = builder.count_tokens(result)
        assert token_count <= 100

    def test_missing_required_variable_raises(self):
        builder = PromptBuilder(template_file="prompts/classification/v2.0.txt")
        with pytest.raises(KeyError):
            builder.build(categories=["a"])

    def test_response_parser_valid_json(self):
        from src.parsers.response_parser import ResponseParser

        parser = ResponseParser()
        raw = '{"label": "positive", "confidence": 0.95}'
        parsed = parser.parse_classification(raw)
        assert parsed["label"] == "positive"
        assert parsed["confidence"] == 0.95
```

#### Prompt Regression Tests

```python
from openai import OpenAI
from sentence_transformers import SentenceTransformer, util

client = OpenAI()
embedder = SentenceTransformer("all-MiniLM-L6-v2")

# Test cases with expected semantic content
SUMMARIZATION_TESTS = [
    {
        "input": "Q3 revenue was $4.2B, up 15% YoY. Operating margin improved to 28%.",
        "expected_keywords": ["$4.2B", "15%", "28%"],
        "expected_semantic": "Revenue grew 15% year over year to $4.2 billion with 28% operating margin",
        "max_tokens": 100,
    },
    {
        "input": "The model v2.1 reduced hallucination rate from 12% to 3.4% on the benchmark.",
        "expected_keywords": ["12%", "3.4%"],
        "expected_semantic": "Hallucination rate decreased from 12% to 3.4% with model v2.1",
        "max_tokens": 100,
    },
]

@pytest.mark.parametrize("test_case", SUMMARIZATION_TESTS)
def test_summarization_quality(test_case):
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "Summarize the input in 1-2 sentences."},
            {"role": "user", "content": test_case["input"]},
        ],
        max_tokens=test_case["max_tokens"],
        temperature=0.0,
    )
    output = response.choices[0].message.content

    # Check all expected keywords appear
    for keyword in test_case["expected_keywords"]:
        assert keyword in output, f"Missing keyword '{keyword}' in: {output}"

    # Check semantic similarity
    expected_emb = embedder.encode(
        test_case["expected_semantic"], convert_to_tensor=True
    )
    output_emb = embedder.encode(output, convert_to_tensor=True)
    similarity = util.cos_sim(expected_emb, output_emb).item()

    assert similarity > 0.75, (
        f"Semantic similarity {similarity:.3f} below threshold 0.75. "
        f"Expected: {test_case['expected_semantic']}. Got: {output}"
    )
```

#### Testing Pyramid for LLM Apps

| Layer | Speed | Coverage | Example |
|-------|-------|----------|---------|
| Unit tests | Milliseconds | Logic, parsing, validation | Prompt builder, response parser |
| Integration tests | Seconds | End-to-end with mock/stub API | Pipeline with mocked LLM |
| Prompt regression tests | Minutes | Quality with real LLM | Accuracy, confidence, categories |
| Manual evaluation | Hours | Edge cases, human judgment | Red-teaming, adversarial inputs |

**Key Takeaway:** Maintain a regression test suite of curated input-output pairs and run it on every prompt or model change.

---

## 8.2 Automated Deployment Pipelines for LLM Apps

CI/CD for AI applications extends traditional pipelines with model validation, prompt testing, evaluation gates, and gradual rollout strategies. The goal is to ship reliable AI features quickly while maintaining safety and quality.

### 8.2.1 CI/CD Pipelines (GitHub Actions, Azure DevOps)

A production AI pipeline has additional stages compared to standard web apps: model validation, evaluation benchmarks, prompt testing, and AI-specific security scanning.

#### Pipeline Stages

| Stage | Purpose | Key Actions |
|-------|---------|-------------|
| **Source** | Code and config changes trigger the pipeline | Git push, PR, scheduled trigger |
| **Build** | Compile, package, and containerize | Docker build, dependency install |
| **Test** | Validate code and AI behavior | Unit tests, integration tests, prompt regression tests |
| **Evaluate** | Run AI-specific quality benchmarks | Eval suite, semantic similarity, guardrail checks |
| **Package** | Create deployable artifacts | Container push, ARM/Bicep template validation |
| **Deploy (Staging)** | Deploy to pre-production environment | Blue-green or canary to staging slot |
| **Validate (Staging)** | Smoke tests and synthetic traffic | Hit health endpoints, run eval against live service |
| **Deploy (Production)** | Promote to production | Gradual traffic shift, canary rollout |
| **Monitor** | Observe production behavior | Latency, error rate, quality metrics, drift detection |
| **Rollback** | Revert to last known good version | Auto-rollback on threshold breach |

#### GitHub Actions CI/CD Pipeline

```yaml
# .github/workflows/llm-app-ci-cd.yml
name: LLM App CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

env:
  AZURE_CONTAINER_REGISTRY: myacr.azurecr.io
  IMAGE_NAME: llm-app
  AZURE_RESOURCE_GROUP: rg-llm-prod

jobs:
  # ────────────── STAGE 1: BUILD & TEST ──────────────
  build-and-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: "pip"

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt

      - name: Lint and type check
        run: |
          ruff check src/
          mypy src/ --ignore-missing-imports

      - name: Run unit tests
        run: pytest tests/unit/ -v --tb=short --junitxml=results/unit.xml

      - name: Run integration tests
        run: pytest tests/integration/ -v --tb=short --junitxml=results/integration.xml
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}

  # ────────────── STAGE 2: AI EVALUATION ──────────────
  evaluate:
    needs: build-and-test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: pip install -r requirements.txt -r requirements-eval.txt

      - name: Run prompt regression tests
        run: pytest tests/eval/ -v --tb=short --junitxml=results/eval.xml
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}

      - name: Run evaluation benchmarks
        run: |
          python scripts/run_eval_suite.py \
            --test-set data/eval/benchmark_v3.jsonl \
            --threshold 0.80 \
            --output results/eval_report.json
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}

      - name: Check evaluation gate
        run: |
          SCORE=$(jq '.overall_score' results/eval_report.json)
          THRESHOLD=0.80
          if (( $(echo "$SCORE < $THRESHOLD" | bc -l) )); then
            echo "Evaluation score $SCORE below threshold $THRESHOLD"
            exit 1
          fi
          echo "Evaluation passed: score=$SCORE"

      - name: Upload eval results
        uses: actions/upload-artifact@v4
        with:
          name: eval-results
          path: results/

  # ────────────── STAGE 3: BUILD & PUSH CONTAINER ──────────────
  build-container:
    needs: evaluate
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Log in to Azure Container Registry
        uses: azure/docker-login@v1
        with:
          login-server: ${{ env.AZURE_CONTAINER_REGISTRY }}
          username: ${{ secrets.ACR_USERNAME }}
          password: ${{ secrets.ACR_PASSWORD }}

      - name: Build and push Docker image
        run: |
          TAG=${{ github.sha }}
          docker build -t ${{ env.AZURE_CONTAINER_REGISTRY }}/${{ env.IMAGE_NAME }}:$TAG .
          docker push ${{ env.AZURE_CONTAINER_REGISTRY }}/${{ env.IMAGE_NAME }}:$TAG

  # ────────────── STAGE 4: DEPLOY TO STAGING ──────────────
  deploy-staging:
    needs: build-container
    runs-on: ubuntu-latest
    environment: staging
    steps:
      - uses: actions/checkout@v4

      - name: Deploy to Azure Container Apps (staging)
        uses: azure/container-apps-deploy-action@v1
        with:
          resourceGroup: ${{ env.AZURE_RESOURCE_GROUP }}
          containerAppName: llm-app-staging
          imageToDeploy: ${{ env.AZURE_CONTAINER_REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }}

      - name: Run staging smoke tests
        run: |
          sleep 30
          python tests/smoke/test_staging.py \
            --endpoint ${{ secrets.STAGING_ENDPOINT }} \
            --api-key ${{ secrets.STAGING_API_KEY }}

  # ────────────── STAGE 5: CANARY DEPLOY TO PRODUCTION ──────────────
  deploy-production:
    needs: deploy-staging
    runs-on: ubuntu-latest
    environment: production
    steps:
      - name: Canary deploy (10% traffic)
        run: |
          az containerapp revision copy \
            --name llm-app \
            --resource-group ${{ env.AZURE_RESOURCE_GROUP }} \
            --image ${{ env.AZURE_CONTAINER_REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }} \
            --revision-suffix canary-${{ github.sha }} \
            --traffic-weight 10

      - name: Monitor canary (5 min)
        run: python scripts/monitor_canary.py --duration 300 --error-threshold 0.01

      - name: Promote to 50%
        run: |
          az containerapp ingress traffic set \
            --name llm-app \
            --resource-group ${{ env.AZURE_RESOURCE_GROUP }} \
            --revision-weight llm-app-canary-${{ github.sha }}=50

      - name: Monitor at 50% (10 min)
        run: python scripts/monitor_canary.py --duration 600 --error-threshold 0.005

      - name: Full rollout (100%)
        run: |
          az containerapp ingress traffic set \
            --name llm-app \
            --resource-group ${{ env.AZURE_RESOURCE_GROUP }} \
            --revision-weight llm-app-canary-${{ github.sha }}=100
```

#### Azure DevOps CI/CD Pipeline

```yaml
# azure-pipelines.yml
trigger:
  branches:
    include:
      - main

pool:
  vmImage: "ubuntu-latest"

variables:
  - group: llm-app-variables
  - name: imageName
    value: "$(azureContainerRegistry)/llm-app:$(Build.BuildId)"

stages:
  - stage: Build
    jobs:
      - job: BuildAndTest
        steps:
          - task: UsePythonVersion@0
            inputs:
              versionSpec: "3.11"

          - script: |
              pip install -r requirements.txt
              pip install -r requirements-dev.txt
            displayName: "Install dependencies"

          - script: pytest tests/ --junitxml=test-results.xml
            displayName: "Run tests"

          - task: PublishTestResults@2
            inputs:
              testResultsFiles: "test-results.xml"

  - stage: Evaluate
    dependsOn: Build
    jobs:
      - job: RunEval
        steps:
          - script: |
              python scripts/run_eval_suite.py \
                --threshold 0.80 \
                --output eval-report.json
            displayName: "Run AI evaluation suite"

          - script: |
              SCORE=$(jq '.overall_score' eval-report.json)
              echo "##vso[task.setvariable variable=evalScore]$SCORE"
            displayName: "Extract eval score"

  - stage: Deploy
    dependsOn: Evaluate
    condition: and(succeeded(), gt(variables.evalScore, '0.80'))
    jobs:
      - deployment: DeployProduction
        environment: "production-llm"
        strategy:
          runOnce:
            deploy:
              steps:
                - task: AzureContainerApps@1
                  inputs:
                    azureSubscription: "$(serviceConnection)"
                    resourceGroup: "$(resourceGroup)"
                    containerAppName: "llm-app"
                    imageToDeploy: "$(imageName)"
```

#### GitHub Actions vs Azure DevOps

| Feature | GitHub Actions | Azure DevOps |
|---------|---------------|--------------|
| YAML syntax | `jobs.<id>.steps` | `stages → jobs → steps` |
| Conditional execution | `if:` on jobs/steps | `condition:` on stages/jobs |
| Environments | `environment:` with approval | `environment:` with gates |
| Secrets | Repository/organization secrets | Variable groups, Key Vault |
| Best for | Open source, GitHub-centric teams | Enterprise Azure ecosystems |

**Key Takeaway:** Every LLM app pipeline should include prompt regression tests and an AI evaluation gate alongside traditional code tests.

---

### 8.2.2 Automated Testing for LLM Apps

Testing LLM applications requires a layered strategy that goes beyond traditional unit tests. The testing pyramid for AI apps adds semantic evaluation layers on top of standard software testing.

#### Test Types Summary

| Test Type | What It Tests | Tools / Approaches |
|-----------|---------------|--------------------|
| **Unit tests** | Individual functions, parsers, validators | pytest, unittest |
| **Integration tests** | API endpoints, tool calls, chain execution | pytest + httpx, mock LLM calls |
| **Prompt regression tests** | Output quality doesn't degrade across prompt changes | Custom eval harness, promptfoo |
| **Semantic similarity tests** | Outputs are semantically equivalent to expected answers | Embedding cosine similarity, BERTScore |
| **Evaluation benchmarks** | Performance on standardized tasks | lm-eval-harness, custom datasets |
| **Guardrail tests** | Safety filters, output validation, PII detection | NeMo Guardrails, custom validators |
| **Load / performance tests** | Latency, throughput under concurrent requests | Locust, k6 |

#### Integration Tests (End-to-End Flows)

```python
import pytest
from src.pipelines.classification import ClassificationPipeline


@pytest.fixture
def pipeline():
    return ClassificationPipeline(
        model="gpt-4",
        prompt_version="v2.0",
        api_key="test-key",
    )


class TestClassificationPipeline:
    def test_end_to_end_positive_sentiment(self, pipeline):
        result = pipeline.classify("I absolutely love this product!")
        assert result["label"] in ("positive", "negative", "neutral")
        assert result["label"] == "positive"
        assert 0.0 <= result["confidence"] <= 1.0

    def test_end_to_end_empty_input(self, pipeline):
        result = pipeline.classify("")
        assert result["error"] is not None

    def test_batch_classification(self, pipeline):
        texts = ["Great!", "Terrible.", "It's okay."]
        results = pipeline.classify_batch(texts)
        assert len(results) == 3
        labels = {r["label"] for r in results}
        assert labels.issubset({"positive", "negative", "neutral"})
```

#### Key Differences: Traditional vs LLM Testing

| Aspect | Traditional Software | LLM Applications |
|--------|---------------------|------------------|
| **Output type** | Deterministic | Probabilistic |
| **Test assertions** | Exact equality | Semantic similarity, keyword checks |
| **Flakiness** | Rare (bugs) | Common (non-deterministic outputs) |
| **Failure modes** | Crashes, exceptions | Hallucinations, style drift, quality regression |
| **Performance testing** | Latency, throughput | Latency, throughput, token cost, quality |
| **Security testing** | SQL injection, XSS | Prompt injection, data leakage |

**Key Takeaway:** Maintain a layered testing strategy: unit tests for logic, integration tests for flows, and prompt regression tests for quality assurance.

---

### 8.2.3 Containerization (Docker for LLM Apps)

Docker packages the LLM application with its dependencies into a portable container. For LLM apps, consider model weight caching, layer optimization, and multi-stage builds to reduce image size.

#### Multi-Stage Dockerfile

```dockerfile
# Dockerfile for LLM application
# Multi-stage build for smaller production image

# ── Stage 1: Builder ──
FROM python:3.11-slim as builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ── Stage 2: Production ──
FROM python:3.11-slim as production

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY src/ ./src/
COPY prompts/ ./prompts/
COPY config/ ./config/

# Health check endpoint
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### Docker Compose for Local Development

```yaml
# docker-compose.yml
version: "3.9"

services:
  llm-app:
    build:
      context: .
      target: production
    ports:
      - "8000:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - PROMPT_VERSION=v2.0
      - LOG_LEVEL=info
    volumes:
      - ./prompts:/app/prompts:ro
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data

  test-runner:
    build:
      context: .
      target: production
    command: pytest tests/ -v
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - REDIS_URL=redis://redis:6379
    depends_on:
      - llm-app
      - redis

volumes:
  redis-data:
```

#### Model Weight Handling Strategies

| Strategy | How It Works | Trade-offs |
|----------|-------------|------------|
| **Fetch at build time** | Download model during Docker build, bake into image | Large image, slow builds, but self-contained |
| **Fetch at runtime** | Download model when container starts | Smaller image, slower cold start |
| **Init container** | K8s init container downloads before main container starts | Clean separation, but adds deployment complexity |
| **Shared volume** | Model stored in shared persistent volume | Fast startup, but requires volume management |

#### Container Security Best Practices

| Practice | Implementation |
|----------|----------------|
| Non-root user | `RUN useradd -r -g appuser appuser` |
| Minimal base image | Use `python:3.11-slim` or `distroless` |
| No secrets in image | Use environment variables or secret managers |
| Read-only filesystem | `--read-only` flag in production |
| Image scanning | `trivy image llm-service:latest` |
| Pin dependencies | `pip freeze > requirements.txt` |

**Key Takeaway:** Use multi-stage Docker builds, run as non-root, and never bake secrets into images.

---

### 8.2.4 Infrastructure as Code (Bicep, Terraform)

IaC ensures reproducible, auditable infrastructure deployments for LLM applications. For AI workloads, this includes container registries, compute, managed AI services, and monitoring.

#### Azure Bicep — LLM App Infrastructure

```bicep
// infra/main.bicep — Azure Container App for LLM service
@description('Location for all resources')
param location string = resourceGroup().location

@description('Container app name')
param containerAppName string = 'llm-app'

@description('Container image')
param containerImage string

@description('Azure OpenAI endpoint')
param openaiEndpoint string

resource containerAppEnvironment 'Microsoft.App/managedEnvironments@2024-03-01' existing = {
  name: 'cae-llm-shared'
}

resource containerApp 'Microsoft.App/containerApps@2024-03-01' = {
  name: containerAppName
  location: location
  properties: {
    environmentId: containerAppEnvironment.id
    configuration: {
      ingress: {
        external: true
        targetPort: 8000
      }
      secrets: [
        {
          name: 'openai-api-key'
          value: openaiApiKey
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'llm-app'
          image: containerImage
          resources: {
            cpu: 1
            memory: '2Gi'
          }
          env: [
            {
              name: 'OPENAI_API_BASE'
              value: openaiEndpoint
            }
            {
              name: 'OPENAI_API_KEY'
              secretRef: 'openai-api-key'
            }
          ]
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 10
        rules: [
          {
            name: 'http-scaling'
            http: {
              metadata: {
                concurrentRequests: '50'
              }
            }
          }
        ]
      }
    }
  }
}

output appUrl string = containerApp.properties.configuration.ingress.fqdn
```

#### Terraform — LLM App Infrastructure

```hcl
# infra/main.tf
terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.80"
    }
  }
  backend "azurerm" {
    resource_group_name  = "rg-terraform-state"
    storage_account_name = "stterraformstate"
    container_name       = "tfstate"
    key                  = "llm-app.tfstate"
  }
}

provider "azurerm" {
  features {}
}

variable "app_name" { default = "llm-service" }
variable "environment" { default = "production" }
variable "container_image" { description = "Docker image for the LLM app" }
variable "openai_api_key" { type = string; sensitive = true }

resource "azurerm_resource_group" "main" {
  name     = "rg-${var.app_name}-${var.environment}"
  location = "East US"
}

resource "azurerm_container_app_environment" "main" {
  name                       = "${var.app_name}-env-${var.environment}"
  location                   = azurerm_resource_group.main.location
  resource_group_name        = azurerm_resource_group.main.name
  log_analytics_workspace_id = azurerm_log_analytics_workspace.main.id
}

resource "azurerm_container_app" "main" {
  name                         = "${var.app_name}-${var.environment}"
  container_app_environment_id = azurerm_container_app_environment.main.id
  resource_group_name          = azurerm_resource_group.main.name
  revision_mode                = "Single"

  template {
    container {
      name   = var.app_name
      image  = var.container_image
      cpu    = "1.0"
      memory = "2Gi"
      env {
        name  = "ENVIRONMENT"
        value = var.environment
      }
      env {
        name        = "OPENAI_API_KEY"
        secret_name = "openai-api-key"
      }
      liveness_probe {
        path              = "/health"
        port              = 8000
        transport         = "HTTP"
        interval_seconds  = 30
      }
      readiness_probe {
        path              = "/ready"
        port              = 8000
        transport         = "HTTP"
        interval_seconds  = 10
      }
    }
    min_replicas = 2
    max_replicas = 10
    http_scale_rule {
      name                = "http-scaling"
      concurrent_requests = "50"
    }
  }

  secret {
    name  = "openai-api-key"
    value = var.openai_api_key
  }

  ingress {
    external_enabled = true
    target_port      = 8000
    traffic_weight {
      latest_revision = true
      percentage      = 100
    }
  }
}

output "app_url" {
  value = azurerm_container_app.main.latest_revision_fqdn
}
```

#### Bicep vs Terraform Comparison

| Feature | Bicep | Terraform |
|---------|-------|-----------|
| Provider | Azure only | Multi-cloud |
| Language | Bicep DSL | HCL |
| State management | Azure-managed | Remote/local state files |
| Module ecosystem | Azure Verified Modules | Terraform Registry |
| Learning curve | Lower for Azure teams | Broader industry standard |
| Drift detection | Azure Resource Manager | `terraform plan` |

**Key Takeaway:** Use IaC for all infrastructure — never manually provision cloud resources for production LLM apps.

---

### 8.2.5 Blue-Green and Canary Deployments

AI applications benefit from gradual rollout strategies because model behavior can be unpredictable. Blue-green and canary deployments minimize the blast radius of regressions.

#### Deployment Strategy Comparison

| Strategy | Description | Rollback Speed | Risk |
|----------|-------------|----------------|------|
| **Blue-Green** | Two identical environments; switch traffic instantly | Instant (flip back) | All-or-nothing cutover |
| **Canary** | Route small % of traffic to new version; gradually increase | Fast (shift traffic) | Gradual exposure |
| **Shadow / Dark Launch** | New version receives duplicate traffic but doesn't serve users | N/A (no user impact) | Observability without risk |
| **Feature Flags** | Toggle features per user segment or percentage | Instant | Complexity of flag management |

#### Canary Deployment Monitoring

```python
import time
from dataclasses import dataclass


@dataclass
class CanaryMetrics:
    total_requests: int = 0
    error_count: int = 0
    avg_latency_ms: float = 0.0
    quality_score: float = 0.0

    @property
    def error_rate(self) -> float:
        return self.error_count / max(self.total_requests, 1)


def monitor_canary(
    endpoint: str,
    duration_seconds: int = 300,
    error_threshold: float = 0.01,
    latency_threshold_ms: float = 2000,
    check_interval: int = 30,
) -> bool:
    """Monitor canary deployment. Returns True if healthy."""
    start = time.time()

    while time.time() - start < duration_seconds:
        metrics = collect_metrics(endpoint, check_interval)

        if metrics.error_rate > error_threshold:
            print(f"ERROR: Error rate {metrics.error_rate:.4f} exceeds threshold")
            return False

        if metrics.avg_latency_ms > latency_threshold_ms:
            print(f"ERROR: Latency {metrics.avg_latency_ms:.0f}ms exceeds threshold")
            return False

        print(
            f"Canary OK: requests={metrics.total_requests}, "
            f"errors={metrics.error_rate:.4f}, "
            f"latency={metrics.avg_latency_ms:.0f}ms"
        )

    return True
```

**Key Takeaway:** Use canary deployments for LLM apps to catch quality regressions that may not trigger traditional health checks.

---

### 8.2.6 Rollback Strategies

Rollback mechanisms must be pre-planned and automated. For AI applications, rollback means reverting to a previous model version, prompt version, or application code version.

#### Rollback Triggers

| Trigger | Threshold | Detection Method |
|---------|-----------|------------------|
| Error rate spike | > 5% in 5 min | HTTP 5xx count / total requests |
| P99 latency | > 3000ms | Percentile calculation from APM |
| Prompt quality drop | < 80% accuracy | Regression test suite on live traffic |
| Cost anomaly | > 2x baseline | Token usage / API cost tracking |
| Manual trigger | N/A | Human operator decision |

#### Rollback Scenarios

| Scenario | Rollback Action | Mechanism |
|----------|----------------|-----------|
| **Model quality regression** | Revert to previous model version in registry | MLflow model stage transition, container image tag |
| **Prompt regression** | Revert prompt YAML file, redeploy | Git revert + CI trigger |
| **Application bug** | Roll back container image | `az containerapp revision rollback` |
| **Infrastructure failure** | Revert IaC deployment | `terraform apply` previous state |
| **High latency / errors** | Shift traffic away from canary | Canary weight → 0% |

```bash
# Azure Container Apps rollback
az containerapp revision list --name llm-app --resource-group rg-llm-prod -o table
az containerapp revision activate --name llm-app --resource-group rg-llm-prod --revision llm-app--previous-stable
az containerapp ingress traffic set --name llm-app --resource-group rg-llm-prod --revision-weight llm-app--previous-stable=100
```

#### GitHub Actions Rollback Workflow

```yaml
# .github/workflows/rollback.yml
name: Rollback LLM App

on:
  workflow_dispatch:
    inputs:
      target_revision:
        description: 'Target revision suffix to roll back to'
        required: true
      reason:
        description: 'Reason for rollback'
        required: true

jobs:
  rollback:
    runs-on: ubuntu-latest
    environment: production
    steps:
      - name: Rollback to target revision
        run: |
          az containerapp ingress traffic set \
            --name llm-app \
            --resource-group rg-llm-prod \
            --revision-weight ${{ inputs.target_revision }}=100

      - name: Notify team
        uses: slackapi/slack-github-action@v1
        with:
          payload: |
            {
              "text": "ROLLBACK: llm-app rolled back to ${{ inputs.target_revision }}. Reason: ${{ inputs.reason }}"
            }
        env:
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK }}
```

**Key Takeaway:** Automate rollback decisions based on both technical metrics (error rate, latency) and domain-specific metrics (prompt quality, cost).

---

### 8.2.7 Environment Management

#### Environment Configuration

| Aspect | Development | Staging | Production |
|--------|-------------|---------|------------|
| Model | gpt-4o-mini | gpt-4o | gpt-4o |
| Rate limits | Relaxed | Moderate | Strict |
| Logging level | DEBUG | INFO | WARNING |
| Secrets source | .env file | Azure Key Vault | Azure Key Vault |
| Replicas | 1 | 1 | 2-10 (autoscaled) |
| Approval required | No | No | Yes |
| Prompt version | Latest (HEAD) | Candidate release | Active (promoted) |
| Monitoring | Basic | Full | Full + alerts |

#### Environment-Aware Configuration

```python
from pydantic_settings import BaseSettings
from pydantic import Field
from enum import Enum


class Environment(str, Enum):
    DEV = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class Settings(BaseSettings):
    app_name: str = "llm-service"
    environment: Environment = Environment.DEV

    # LLM Configuration
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    default_model: str = "gpt-4o"
    temperature: float = 0.0
    max_tokens: int = 4096

    # Prompt Configuration
    prompt_version: str = "v2.0"
    prompt_dir: str = "prompts"

    # Monitoring
    log_level: str = "INFO"
    enable_tracing: bool = True
    metrics_port: int = 9090

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    @property
    def is_production(self) -> bool:
        return self.environment == Environment.PRODUCTION


settings = Settings()
```

**Key Takeaway:** Use environment-specific configurations with strict secret management and progressively tighter controls from dev to production.

---

## Module Summary

| Topic | Key Principle |
|-------|--------------|
| Model versioning | Semantic versions, stage transitions, rich metadata |
| Prompt versioning | Version as first-class artifacts, A/B test variants |
| CI/CD pipelines | Automate build → test → deploy with prompt regression gates |
| Testing | Layered: unit → integration → prompt regression |
| Containerization | Multi-stage builds, non-root, no secrets in images |
| IaC | Bicep/Terraform for reproducible, auditable infrastructure |
| Deployment strategies | Canary for LLM apps (catch quality regressions) |
| Rollback | Automated triggers on error rate, latency, quality, cost |
| Environment management | Progressive strictness, managed secrets |
