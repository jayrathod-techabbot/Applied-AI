# Module 8: CI/CD for AI — Quiz

## Instructions
- 20 multiple choice questions
- Each question has exactly one correct answer
- Click to reveal answers and explanations

---

## Questions

### Q1. What is the primary purpose of DVC (Data Version Control) in ML projects?

A) To replace Git entirely
B) To track large files like datasets and model weights alongside Git
C) To compile machine learning models
D) To deploy models to production

<details>
<summary><strong>Answer: B</strong></summary>

**Explanation:** DVC extends Git to handle large files (datasets, model weights) by storing them in remote storage while keeping lightweight `.dvc` metadata files in Git. It does not replace Git — it works alongside it. `dvc push` uploads data to remote storage; `git push` uploads the pointer files.

</details>

---

### Q2. Which MLflow function logs a trained model to the tracking server?

A) `mlflow.save_model()`
B) `mlflow.log_model()`
C) `mlflow.track_artifact()`
D) `mlflow.register_artifact()`

<details>
<summary><strong>Answer: B</strong></summary>

**Explanation:** `mlflow.log_model()` (and framework-specific variants like `mlflow.pytorch.log_model()`) logs a model artifact to the MLflow tracking server. `mlflow.save_model()` saves locally, while `register_model()` promotes to the Model Registry.

</details>

---

### Q3. What is the recommended strategy for versioning prompts in a production LLM application?

A) Hardcode prompts as string constants in the application code
B) Store prompts in a versioned registry or YAML files tracked in Git
C) Let each developer maintain their own prompt copy locally
D) Store prompts only in the model's training data

<details>
<summary><strong>Answer: B</strong></summary>

**Explanation:** Prompts should be treated as first-class versioned assets stored in YAML files tracked by Git or in a dedicated prompt registry. This enables audit trails, rollback, and collaborative refinement across teams.

</details>

---

### Q4. In a CI/CD pipeline for an LLM application, at which stage should AI evaluation benchmarks run?

A) Before linting
B) After unit/integration tests but before container build
C) Only after production deployment
D) During the Docker image build

<details>
<summary><strong>Answer: B</strong></summary>

**Explanation:** AI evaluation benchmarks run after unit/integration tests pass but before building and deploying the container. This acts as a quality gate — if the eval score is below threshold, the pipeline stops and deployment is blocked.

</details>

---

### Q5. What is a canary deployment?

A) Deploying to all users simultaneously
B) Routing a small percentage of traffic to the new version while the rest goes to the stable version
C) Running tests in a staging environment
D) Deploying without any rollback plan

<details>
<summary><strong>Answer: B</strong></summary>

**Explanation:** A canary deployment routes a small fraction (e.g., 5-10%) of traffic to the new version. If metrics remain healthy, traffic is gradually increased. If errors spike, traffic is shifted back to the stable version, limiting the blast radius.

</details>

---

### Q6. What does `dvc push` do?

A) Pushes code changes to GitHub
B) Pushes tracked data files to remote storage
C) Deploys the model to production
D) Pushes Docker images to a container registry

<details>
<summary><strong>Answer: B</strong></summary>

**Explanation:** `dvc push` uploads data files tracked by DVC to the configured remote storage (Azure Blob, S3, GCS, etc.). The corresponding Git commit contains only lightweight `.dvc` metadata pointer files.

</details>

---

### Q7. Which GitHub Actions keyword ensures a job only runs on pushes to the `main` branch?

A) `when: branch == 'main'`
B) `if: github.ref == 'refs/heads/main'`
C) `filter: main`
D) `only: [main]`

<details>
<summary><strong>Answer: B</strong></summary>

**Explanation:** In GitHub Actions, conditional execution uses the `if` keyword with GitHub context variables. `github.ref == 'refs/heads/main'` checks if the push is to the main branch. Options A, C, and D are not valid GitHub Actions syntax.

</details>

---

### Q8. What is the primary advantage of blue-green deployment over rolling deployment?

A) It uses less compute resources
B) Instant rollback by switching traffic to the previous environment
C) It requires no infrastructure
D) It automatically fixes bugs

<details>
<summary><strong>Answer: B</strong></summary>

**Explanation:** Blue-green deployment maintains two identical environments. Traffic switching is a single routing change, enabling instant rollback by flipping back to the previous environment. Rolling deployment updates instances incrementally and is harder to roll back quickly.

</details>

---

### Q9. In a Dockerfile for an LLM application, why use a multi-stage build?

A) To run the application in multiple containers
B) To reduce the final image size by separating build dependencies from runtime
C) To deploy to multiple cloud regions
D) To support multiple programming languages

<details>
<summary><strong>Answer: B</strong></summary>

**Explanation:** Multi-stage builds use a builder stage to compile/install dependencies, then copy only the necessary artifacts to a slim production stage. This significantly reduces the final image size, attack surface, and build cache layers.

</details>

---

### Q10. What should a prompt regression test verify?

A) That the prompt file is syntactically valid YAML
B) That LLM outputs remain semantically consistent after prompt changes
C) That the prompt is stored in Git
D) That the prompt contains no profanity

<details>
<summary><strong>Answer: B</strong></summary>

**Explanation:** Prompt regression tests compare LLM outputs before and after prompt modifications, checking that quality and semantic consistency are maintained. They catch unintended behavioral changes that pass code tests but degrade output quality.

</details>

---

### Q11. Which IaC tool is natively integrated with Azure and uses a declarative syntax?

A) Terraform
B) Bicep
C) Pulumi
D) Ansible

<details>
<summary><strong>Answer: B</strong></summary>

**Explanation:** Bicep is Microsoft's domain-specific language for deploying Azure resources. It compiles to ARM templates and is natively integrated with Azure deployment tooling. Terraform is cloud-agnostic but requires providers for each cloud.

</details>

---

### Q12. What is the purpose of an evaluation gate in a CI/CD pipeline?

A) To check if the code compiles
B) To block deployment if AI quality metrics fall below a threshold
C) To verify that Docker builds successfully
D) To ensure the team has approval from management

<details>
<summary><strong>Answer: B</strong></summary>

**Explanation:** An evaluation gate checks metrics like accuracy, semantic similarity, or hallucination rate against a predefined threshold. If the score is too low, the pipeline fails and deployment is blocked — acting as an automated quality control point.

</details>

---

### Q13. In MLflow, what is the Model Registry used for?

A) Storing training data
B) Managing model versions with stages (staging, production, archived)
C) Hosting the model inference API
D) Logging training metrics

<details>
<summary><strong>Answer: B</strong></summary>

**Explanation:** The MLflow Model Registry provides a centralized store for model versions with stage transitions (None → Staging → Production → Archived). It enables governance workflows, version comparison, and controlled promotion to production.

</details>

---

### Q14. What is shadow (dark launch) deployment?

A) Deploying without monitoring
B) Routing duplicate traffic to the new version without serving its responses to users
C) Deploying to a hidden production environment
D) Running the application in debug mode

<details>
<summary><strong>Answer: B</strong></summary>

**Explanation:** Shadow deployment sends a copy of live traffic to the new version for observation, but users still receive responses from the stable version. This allows testing the new version with real traffic without any user impact or risk.

</details>

---

### Q15. Which command rolls back an Azure Container App to a previous revision?

A) `az containerapp delete`
B) `az containerapp revision rollback`
C) `az containerapp restart`
D) `az containerapp update --rollback`

<details>
<summary><strong>Answer: B</strong></summary>

**Explanation:** `az containerapp revision rollback` reverts the container app to a previous revision. You can also use `az containerapp ingress traffic set` to shift traffic to an older revision without technically "rolling back" the active revision.

</details>

---

### Q16. What is the key difference between unit tests and semantic similarity tests for LLM applications?

A) Unit tests are faster; semantic tests are slower
B) Unit tests check deterministic function behavior; semantic tests check probabilistic output equivalence
C) Unit tests require a GPU; semantic tests do not
D) There is no difference

<details>
<summary><strong>Answer: B</strong></summary>

**Explanation:** Unit tests verify deterministic behavior (parsers, validators, API contracts). Semantic similarity tests compare LLM outputs to expected answers using embedding cosine similarity or BERTScore, accounting for the probabilistic nature of LLM outputs.

</details>

---

### Q17. What information should be logged alongside a model version in an experiment tracker?

A) Only the model weights
B) Hyperparameters, training data hash, evaluation metrics, code commit hash, and environment details
C) Only the final accuracy score
D) Only the developer's name

<details>
<summary><strong>Answer: B</strong></summary>

**Explanation:** Full lineage logging includes hyperparameters, data version/hash, all evaluation metrics, the Git commit hash, and environment details. This enables reproducibility — anyone can reconstruct exactly how a model was trained.

</details>

---

### Q18. In a GitHub Actions workflow, what does the `needs` keyword do?

A) Specifies which files trigger the workflow
B) Defines job dependencies, ensuring a job runs only after specified jobs succeed
C) Sets environment variables
D) Defines the runner OS

<details>
<summary><strong>Answer: B</strong></summary>

**Explanation:** The `needs` keyword creates a dependency graph between jobs. A job with `needs: [build-and-test]` will only run after the `build-and-test` job completes successfully. This ensures proper sequencing of pipeline stages.

</details>

---

### Q19. Why is automated rollback critical for AI applications specifically?

A) AI applications never fail
B) Model behavior is non-deterministic and quality regressions may not surface in tests
C) Rollback is only needed for web applications
D) AI models degrade over time automatically

<details>
<summary><strong>Answer: B</strong></summary>

**Explanation:** LLM outputs are probabilistic — a prompt or model change may pass tests but degrade quality on real-world inputs. Automated rollback detects production metric anomalies (error rate, latency, quality scores) and reverts before users are significantly impacted.

</details>

---

### Q20. What is the correct order of stages in a production AI CI/CD pipeline?

A) Build → Deploy → Test → Monitor
B) Source → Build → Test → Evaluate → Package → Deploy Staging → Validate → Deploy Production → Monitor
C) Deploy → Test → Evaluate → Build
D) Evaluate → Source → Build → Deploy

<details>
<summary><strong>Answer: B</strong></summary>

**Explanation:** A production AI pipeline follows: Source → Build → Test → Evaluate (AI quality gate) → Package → Deploy to Staging → Validate → Deploy to Production → Monitor. The Evaluate stage is unique to AI pipelines and acts as a quality gate before packaging.

</details>

---

## Score Interpretation

| Score | Level | Recommendation |
|-------|-------|----------------|
| 18–20 | Excellent | Ready for Module 9 — Monitoring & Observability |
| 14–17 | Good | Review weak areas before proceeding |
| 10–13 | Fair | Re-read `concepts.md` and retry the quiz |
| Below 10 | Needs Work | Study the module thoroughly before advancing |
