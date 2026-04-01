# Module 8: CI/CD for AI — Interview Questions

## Quick Reference Table

| # | Question | Level | Topic |
|---|----------|-------|-------|
| 1 | What is CI/CD and why is it important for AI? | Beginner | CI/CD fundamentals |
| 2 | What is the difference between Git and DVC? | Beginner | Version control |
| 3 | What is MLflow and what does it provide? | Beginner | Experiment tracking |
| 4 | What is a Docker container and why deploy LLM apps in containers? | Beginner | Containerization |
| 5 | What is a CI/CD pipeline? | Beginner | Pipeline fundamentals |
| 6 | What is Infrastructure as Code? | Beginner | IaC concepts |
| 7 | What is a container registry? | Beginner | Container registries |
| 8 | Continuous delivery vs continuous deployment? | Beginner | CD strategies |
| 9 | How to design an evaluation gate for LLM pipelines? | Intermediate | Quality gates |
| 10 | Blue-green vs canary deployments for AI? | Intermediate | Deployment strategies |
| 11 | How to version prompts in a multi-team system? | Intermediate | Prompt versioning |
| 12 | What is a `.dvc` file? | Intermediate | DVC internals |
| 13 | Automated rollback triggered by quality degradation? | Intermediate | Rollback automation |
| 14 | Traditional software vs LLM application testing? | Intermediate | Testing differences |
| 15 | Feature flags for prompt versioning? | Intermediate | Feature flags |
| 16 | Design CI/CD for a RAG application? | Advanced | RAG pipelines |
| 17 | Multi-region deployment with region-specific models? | Advanced | Multi-region |
| 18 | Automated prompt optimization pipeline? | Advanced | Prompt optimization |
| 19 | Model weight updates with external storage? | Advanced | Model storage |
| 20 | Zero-downtime embedding model migration? | Advanced | Migration strategy |

---

## Beginner Level

### Q1: What is CI/CD and why is it important for AI applications?

**Answer:** CI/CD stands for Continuous Integration and Continuous Delivery/Deployment. It automates the process of building, testing, and deploying software. For AI applications, CI/CD is critical because:

- **Continuous Integration:** Automatically tests code and prompt changes, catching regressions early
- **Continuous Delivery:** Ensures every change that passes tests is ready for deployment
- **Continuous Deployment:** Automatically deploys validated changes to production

AI apps add unique challenges — model outputs are probabilistic, so testing must include semantic evaluation, not just unit tests. The pipeline must also validate prompt quality and model behavior before deployment.

---

### Q2: What is the difference between Git and DVC?

**Answer:**

| Aspect | Git | DVC |
|--------|-----|-----|
| **Tracks** | Code, text files | Large files (datasets, models) |
| **Storage** | Git repository | Remote storage (Azure Blob, S3, GCS) |
| **Metadata** | Full file content | Lightweight `.dvc` pointer files |
| **Commands** | `git add`, `git commit`, `git push` | `dvc add`, `dvc push`, `dvc pull` |
| **Use case** | Source code versioning | Data and model artifact versioning |

DVC works alongside Git — Git tracks the metadata pointers, DVC handles the large files in remote storage.

---

### Q3: What is MLflow and what does it provide?

**Answer:** MLflow is an open-source platform for managing the ML lifecycle. It provides four key components:

1. **MLflow Tracking:** Logs experiments (parameters, metrics, artifacts)
2. **MLflow Projects:** Packages ML code for reproducibility
3. **MLflow Models:** Standardized model packaging format
4. **MLflow Model Registry:** Centralized model store with stage management (staging, production, archived)

---

### Q4: What is a Docker container and why is it used for deploying LLM apps?

**Answer:** A Docker container packages an application with all its dependencies, runtime, and configuration into a portable unit. For LLM apps:

- **Consistency:** Same environment from dev to production
- **Isolation:** Each service runs in its own container
- **Scalability:** Containers can be replicated and orchestrated
- **Portability:** Runs on any Docker-compatible platform (Azure Container Apps, Kubernetes, etc.)

Multi-stage builds keep images small by separating build-time dependencies from the runtime image.

---

### Q5: What is a CI/CD pipeline?

**Answer:** A CI/CD pipeline is an automated sequence of stages that code changes pass through before reaching production. Typical stages:

```
Code Push → Build → Test → Package → Deploy to Staging → Validate → Deploy to Production → Monitor
```

For AI applications, an additional **Evaluate** stage runs quality benchmarks (prompt regression, semantic similarity) before packaging, acting as a quality gate.

---

### Q6: What is Infrastructure as Code (IaC)?

**Answer:** IaC manages and provisions infrastructure through machine-readable configuration files rather than manual processes. Benefits include:

- **Reproducibility:** Same infrastructure every time
- **Version control:** Infrastructure changes tracked in Git
- **Automation:** No manual click-through in portals
- **Consistency:** Dev, staging, and prod use identical templates

Examples: Bicep (Azure-native), Terraform (cloud-agnostic), Pulumi (general-purpose languages).

---

### Q7: What is a container registry?

**Answer:** A container registry stores and distributes Docker images. Examples include:

- **Azure Container Registry (ACR):** Azure-managed, integrated with Azure services
- **Docker Hub:** Public registry with official images
- **Amazon ECR:** AWS-managed registry
- **Google Artifact Registry:** GCP-managed registry

The CI/CD pipeline pushes built images to the registry, and the deployment platform (e.g., Azure Container Apps) pulls them during deployment.

---

### Q8: What is the difference between continuous delivery and continuous deployment?

**Answer:**

| Aspect | Continuous Delivery | Continuous Deployment |
|--------|--------------------|-----------------------|
| **Deployment to prod** | Manual approval required | Fully automated |
| **Staging** | Auto-deploy to staging | Auto-deploy to staging |
| **Production gate** | Human review | Automated tests/evals only |
| **Risk** | Lower (human checkpoint) | Higher (fully automated) |
| **Speed** | Faster than manual | Fastest |

For AI applications, continuous delivery is more common because human review of evaluation results is often desired before production rollout.

---

## Intermediate Level

### Q9: How would you design an evaluation gate for a CI/CD pipeline that deploys an LLM application?

**Answer:** An evaluation gate blocks deployment if AI quality metrics fall below a threshold. The design includes:

1. **Test suite:** Curated dataset of input/expected-output pairs
2. **Metrics:** Semantic similarity (cosine similarity of embeddings), keyword presence, structured output validation, or custom rubric scoring
3. **Threshold:** Minimum acceptable score (e.g., 0.80)
4. **Integration:** Run after unit tests, before container packaging

```python
def evaluation_gate(eval_report_path: str, threshold: float = 0.80) -> bool:
    with open(eval_report_path) as f:
        report = json.load(f)

    score = report["overall_score"]
    if score < threshold:
        print(f"FAIL: Score {score:.3f} < threshold {threshold}")
        return False

    for category, cat_score in report["category_scores"].items():
        if cat_score < 0.70:
            print(f"FAIL: Category '{category}' score {cat_score:.3f} < 0.70")
            return False

    return True
```

Pipeline YAML integration: `condition: and(succeeded(), gt(stageDependencies.Evaluate.outputs['evalScore'], '0.80'))`

---

### Q10: Explain the difference between blue-green and canary deployments. When would you choose each for an AI application?

**Answer:**

| Aspect | Blue-Green | Canary |
|--------|------------|--------|
| **Traffic split** | 100% → 0% (instant switch) | Gradual: 5% → 25% → 50% → 100% |
| **Rollback** | Instant (switch back) | Fast (shift traffic back) |
| **Resource cost** | 2× infrastructure | 1× + small extra |
| **Risk exposure** | All users at once | Small subset first |
| **Observability window** | Short (switch time) | Extended (monitor at each stage) |

**For AI apps, canary is generally preferred** because model behavior can be unpredictable — a model may pass eval benchmarks but degrade on specific real-world inputs. Canary lets you monitor quality metrics (hallucination rate, user feedback) on a small traffic slice before full rollout.

**Blue-green is suitable** when the change is low-risk (infrastructure update, prompt template that passed extensive testing) and instant rollback is the priority.

---

### Q11: How do you version prompts in a production system with multiple teams?

**Answer:** A production prompt versioning system requires:

1. **Centralized registry:** A service or directory structure that stores all prompt versions with metadata
2. **Naming convention:** `{service}/{prompt_name}/v{version}` (e.g., `chatbot/summarization/v3`)
3. **Metadata:** Author, date, model target, evaluation score, tags
4. **API/SDK:** Programmatic access for applications to fetch the correct version
5. **Stage management:** Draft → Reviewed → Staging → Production → Deprecated

```yaml
# Directory structure
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
        └── v1.yaml
```

```python
class PromptClient:
    def get(self, service: str, prompt_name: str, stage: str = "production") -> PromptConfig:
        version = self._resolve_version(service, prompt_name, stage)
        return self._fetch(service, prompt_name, version)
```

---

### Q12: What is a `.dvc` file and what does it contain?

**Answer:** A `.dvc` file is a lightweight metadata file that DVC creates when you track a large file. It replaces the actual file in the Git repository.

```yaml
# data/training_dataset.csv.dvc
outs:
- md5: a3042db89c1f45d9e32a74d0c5cd7b09
  size: 524288000
  path: training_dataset.csv
  remote: myremote
```

It contains:
- **md5:** Hash of the file for integrity checking
- **size:** File size in bytes
- **path:** Relative path to the original file
- **remote:** Which DVC remote stores the actual data

Running `dvc pull` downloads the actual file using this metadata. Running `dvc checkout` restores the file from the local cache.

---

### Q13: How would you implement automated rollback triggered by production quality degradation?

**Answer:** Automated rollback requires three components:

1. **Real-time monitoring:** Track error rate, latency, and AI-specific metrics (quality scores, user ratings)
2. **Threshold definitions:** Define acceptable ranges for each metric
3. **Rollback trigger:** Automated action when thresholds are breached

```python
class AutoRollback:
    def __init__(self, config: RollbackConfig):
        self.error_threshold = config.max_error_rate       # e.g., 0.01 (1%)
        self.latency_threshold = config.max_latency_ms     # e.g., 2000
        self.quality_threshold = config.min_quality_score  # e.g., 0.80
        self.window_seconds = config.evaluation_window     # e.g., 300

    def evaluate(self, metrics: ProductionMetrics) -> RollbackDecision:
        if metrics.error_rate > self.error_threshold:
            return RollbackDecision.TRIGGER_ROLLBACK, "Error rate exceeded"

        if metrics.p95_latency_ms > self.latency_threshold:
            return RollbackDecision.TRIGGER_ROLLBACK, "Latency exceeded"

        if metrics.avg_quality_score < self.quality_threshold:
            return RollbackDecision.TRIGGER_ROLLBACK, "Quality below threshold"

        return RollbackDecision.HEALTHY, "All metrics within bounds"
```

The monitor runs as a sidecar or separate service. On trigger, it calls the rollback API (e.g., `az containerapp revision rollback` or shifts canary traffic to 0%).

---

### Q14: What are the key differences between testing traditional software and testing LLM applications?

**Answer:**

| Aspect | Traditional Software | LLM Applications |
|--------|---------------------|------------------|
| **Output type** | Deterministic | Probabilistic |
| **Test assertions** | Exact equality (`assert result == expected`) | Semantic similarity, keyword checks |
| **Flakiness** | Rare (bugs) | Common (non-deterministic outputs) |
| **Failure modes** | Crashes, exceptions | Hallucinations, style drift, quality regression |
| **Performance testing** | Latency, throughput | Latency, throughput, token cost, quality |
| **Security testing** | SQL injection, XSS | Prompt injection, data leakage |
| **Tools** | pytest, JUnit | pytest + semantic similarity libs, promptfoo |

---

### Q15: Explain how feature flags can be used for prompt versioning in production.

**Answer:** Feature flags route users to different prompt versions based on rules, enabling:

- **A/B testing:** Compare prompt v2 vs v3 with different user segments
- **Gradual rollout:** 5% of users get the new prompt, monitor quality
- **Kill switch:** Instantly disable a problematic prompt without redeploying
- **Segment-specific prompts:** Premium users get a more capable prompt

```python
class PromptFeatureFlag:
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

---

## Advanced Level

### Q16: Design a complete CI/CD pipeline for a RAG application that uses Azure OpenAI, a vector database, and prompt templates. What are the unique challenges?

**Answer:** A RAG application pipeline must validate retrieval quality, generation quality, and the interaction between them.

**Pipeline stages:**

1. **Source:** Code, prompt templates, eval dataset changes trigger the pipeline
2. **Build:** Lint, type-check, unit test retrieval and generation components separately
3. **Integration Test:** Test the full RAG chain with a mock LLM (deterministic responses)
4. **Evaluate — Retrieval:** Measure retrieval precision/recall against labeled queries
5. **Evaluate — Generation:** Measure answer quality (factuality, completeness, faithfulness)
6. **Evaluate — End-to-End:** Run the full pipeline on a benchmark set
7. **Build Container:** Package the application
8. **Deploy Staging:** Deploy with production vector DB (read-only replica) for realistic testing
9. **Validate Staging:** Smoke tests against live endpoint
10. **Deploy Production:** Canary rollout with quality monitoring

**Unique challenges:**

- **Vector DB state:** The vector index must be compatible with the application version. Schema changes require migration strategies.
- **Data freshness:** Retrieval quality depends on the indexed data. Pipeline must account for data update frequency.
- **Embedding model versioning:** If the embedding model changes, the entire vector index must be re-embedded.
- **Cost:** Evaluation with real LLM calls is expensive. Use a mix of mock tests (fast, cheap) and real eval (thorough, costly).
- **Faithfulness testing:** The generated answer must be grounded in retrieved documents — not just semantically similar to an expected answer.

---

### Q17: How would you implement multi-region deployment for an LLM application with region-specific model deployments?

**Answer:** Multi-region deployment for LLM apps adds complexity because model availability, latency, and compliance vary by region.

**Architecture:**

```yaml
# Bicep — multi-region deployment
module eastus 'modules/container-app.bicep' = {
  name: 'deploy-eastus'
  params: {
    location: 'eastus'
    openaiEndpoint: openaiEastUS.properties.endpoint
    modelName: 'gpt-4o'
  }
}

module westeurope 'modules/container-app.bicep' = {
  name: 'deploy-westeurope'
  params: {
    location: 'westeurope'
    openaiEndpoint: openaiWestEurope.properties.endpoint
    modelName: 'gpt-4o'
  }
}
```

**Key considerations:**

- **Model availability:** Not all models are available in all regions. The pipeline must validate model availability per region.
- **Data residency:** EU data may need to stay in EU regions. Route requests by user geography.
- **Prompt consistency:** Same prompt versions must deploy to all regions simultaneously or with controlled drift.
- **Global evaluation:** Run eval benchmarks against each regional endpoint to detect region-specific quality differences.
- **Failover:** If one region's OpenAI service is degraded, route to the next-closest region.

---

### Q18: Explain how to build an automated prompt optimization pipeline that integrates with CI/CD.

**Answer:** An automated prompt optimization pipeline iteratively improves prompts using evaluation feedback, and can be triggered as part of CI/CD when a prompt change is proposed.

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Prompt Change  │────▶│  Optimization    │────▶│  Evaluation     │
│  (PR/commit)    │     │  Pipeline        │     │  Gate           │
└─────────────────┘     └──────────────────┘     └────────┬────────┘
                              │                           │
                              ▼                           ▼
                    ┌──────────────────┐        ┌─────────────────┐
                    │  LLM generates   │        │  Score >=       │
                    │  prompt variants │        │  threshold?     │
                    └──────────────────┘        └────────┬────────┘
                                                         │
                                              ┌──────────┴──────────┐
                                              │                     │
                                              ▼                     ▼
                                     ┌──────────────┐    ┌──────────────┐
                                     │  Promote to  │    │  Report      │
                                     │  staging     │    │  failure     │
                                     └──────────────┘    └──────────────┘
```

```python
class PromptOptimizer:
    def optimize(
        self,
        base_prompt: str,
        eval_dataset: list[dict],
        max_iterations: int = 5,
        improvement_threshold: float = 0.02,
    ) -> OptimizedPrompt:

        best_prompt = base_prompt
        best_score = self.evaluate(base_prompt, eval_dataset)

        for i in range(max_iterations):
            failures = self.get_failure_cases(best_prompt, eval_dataset)
            candidate = self.llm_improve(best_prompt, failures)
            score = self.evaluate(candidate, eval_dataset)

            if score > best_score + improvement_threshold:
                best_prompt = candidate
                best_score = score
            else:
                break

        return OptimizedPrompt(prompt=best_prompt, score=best_score, iterations=i + 1)
```

The CI/CD integration runs this optimizer when a prompt PR is opened, comparing the optimized prompt against the current production prompt.

---

### Q19: How do you handle model weight updates in a CI/CD pipeline when models are stored externally (Azure Blob, Hugging Face Hub)?

**Answer:** Model weights are too large for Git. The pipeline must fetch them from external storage during build/deploy, with caching to avoid redundant downloads.

**Strategies:**

| Strategy | How It Works | Trade-offs |
|----------|-------------|------------|
| **Fetch at build time** | Download model during Docker build, bake into image | Large image, slow builds, but self-contained |
| **Fetch at runtime** | Download model when container starts | Smaller image, slower cold start |
| **Init container** | K8s init container downloads before main container starts | Clean separation, but adds deployment complexity |
| **Shared volume** | Model stored in shared persistent volume | Fast startup, but requires volume management |

```dockerfile
# Fetch at build time
FROM python:3.11-slim as builder
RUN pip install huggingface_hub
RUN python -c "from huggingface_hub import snapshot_download; snapshot_download('meta-llama/Llama-3-8B', local_dir='/models/llama-3-8b')"

FROM python:3.11-slim
COPY --from=builder /models /models
COPY src/ /app/src/
CMD ["uvicorn", "src.main:app"]
```

```python
# Fetch at runtime
from huggingface_hub import snapshot_download

def load_model(model_name: str, revision: str = "main"):
    local_path = snapshot_download(
        repo_id=model_name,
        revision=revision,
        cache_dir="/tmp/models",
    )
    return load_from_path(local_path)
```

**CI/CD integration:** The pipeline validates that the model hash in the `dvc.lock` or `MLmodel` file matches the external storage version. If the model changes without a code change, the pipeline still triggers.

---

### Q20: Describe a strategy for zero-downtime migration when changing the embedding model in a RAG application.

**Answer:** Changing the embedding model requires re-embedding the entire vector index because embeddings from different models are not comparable. This is a high-risk operation.

**Strategy: Dual-index migration**

```
Phase 1: Deploy new embedding model alongside old
Phase 2: Re-embed entire corpus into new index
Phase 3: Canary test new index
Phase 4: Switch traffic to new index
Phase 5: Decommission old index
```

```yaml
# CI/CD pipeline for embedding model migration
stages:
  - stage: PrepareNewIndex
    steps:
      - script: |
          python scripts/reembed_corpus.py \
            --source-index old-index \
            --dest-index new-index \
            --embedding-model sentence-transformers/all-mpnet-base-v2 \
            --batch-size 256
        displayName: "Re-embed corpus with new model"

      - script: |
          python scripts/validate_index.py --index new-index --expected-count 1000000
        displayName: "Validate new index integrity"

  - stage: CanaryNewIndex
    dependsOn: PrepareNewIndex
    steps:
      - script: |
          az containerapp ingress traffic set \
            --name rag-app \
            --resource-group rg-rag \
            --revision-weight rag-app-new-embedding=5
        displayName: "Canary 5% to new index"

      - script: |
          python scripts/compare_indices.py \
            --old-index old-index \
            --new-index new-index \
            --test-queries data/eval/retrieval_benchmark.jsonl
        displayName: "Compare retrieval quality"

  - stage: FullMigration
    dependsOn: CanaryNewIndex
    steps:
      - script: |
          az containerapp ingress traffic set \
            --name rag-app \
            --resource-group rg-rag \
            --revision-weight rag-app-new-embedding=100
        displayName: "Switch all traffic to new index"
```

**Key challenges:**
- **Cost:** Re-embedding millions of documents is expensive (compute + API calls)
- **Index compatibility:** Different embedding dimensions may require index format changes
- **Query routing:** The application must support routing to multiple indices during migration
- **Rollback plan:** Keep the old index alive until the new index is proven stable for at least 24 hours
