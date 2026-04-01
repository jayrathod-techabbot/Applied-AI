# Module 13: LLMOps — Interview Questions

## Table of Contents
- [Beginner Level](#beginner-level)
- [Intermediate Level](#intermediate-level)
- [Advanced Level](#advanced-level)

---

## Beginner Level

### Q1: What is LLMOps and how does it differ from MLOps?

**Answer:** LLMOps (Large Language Model Operations) is the set of practices, tools, and processes for deploying, monitoring, and maintaining LLM-powered applications in production. It extends MLOps with LLM-specific concerns:

- **Artifacts shift:** From model weights and training pipelines to prompts, chains, agents, and fine-tuned adapters
- **Evaluation differs:** From accuracy/F1/AUC to hallucination rate, faithfulness, relevance, and toxicity
- **Iteration differs:** From retraining on new data to prompt tuning, RAG updates, and model swaps
- **Monitoring differs:** From data drift to token usage, cost per query, and safety scores

### Q2: What is the AI lifecycle for LLM applications?

**Answer:** The lifecycle consists of five iterative stages:

1. **Design:** Use case selection, architecture design (RAG vs. fine-tuning vs. agent)
2. **Build:** Prompt engineering, RAG pipeline implementation, chain/agent construction
3. **Evaluate:** Offline evaluations (test datasets), online evaluations (A/B tests)
4. **Deploy:** Canary, blue-green, or rolling deployments with feature flags
5. **Monitor:** Latency, cost, quality, safety, and user satisfaction tracking

The cycle is continuous — monitoring feeds back into design and build decisions.

### Q3: What is Infrastructure as Code (IaC) and why is it important for LLMOps?

**Answer:** IaC is the practice of managing and provisioning infrastructure through machine-readable definition files rather than manual processes. For LLMOps, it is important because:

- **Reproducibility:** Identical environments across dev, staging, and production
- **Version control:** Infrastructure changes are tracked in Git with code review
- **Automation:** Eliminates manual configuration errors
- **Compliance:** Auditable infrastructure configurations

Common tools include Bicep (Azure-native) and Terraform (cloud-agnostic).

### Q4: What is experiment tracking and why is it needed in LLMOps?

**Answer:** Experiment tracking records parameters, metrics, artifacts, and results for each experiment run. In LLMOps, this means logging:

- Prompt template versions
- Model name and parameters (temperature, max_tokens)
- Evaluation metrics (hallucination rate, latency, cost)
- Input/output samples

Tools like MLflow provide a central UI to compare runs and reproduce results.

### Q5: What are the key differences between blue-green and canary deployments?

**Answer:**

| Aspect | Blue-Green | Canary |
|--------|------------|--------|
| **Traffic switch** | Instant, atomic switch | Gradual percentage increase |
| **Risk** | All-or-nothing | Incremental validation |
| **Rollback** | Instant (switch back) | Fast (reduce percentage) |
| **Resource cost** | 2x infrastructure | Slightly more than baseline |
| **Use case** | Major version changes | Iterative improvements, prompt changes |

### Q6: What is a model registry?

**Answer:** A model registry is a central repository that tracks:

- **Model versions:** Each iteration of a model or prompt configuration
- **Metadata:** Parameters, training data references, author, date
- **Metrics:** Evaluation scores associated with each version
- **Lineage:** Which data and code produced each model
- **Stage tracking:** Development → Staging → Production → Archived

Azure ML and MLflow both provide model registry capabilities.

### Q7: What metrics should you monitor for an LLM application in production?

**Answer:** Key metrics span multiple layers:

- **Infrastructure:** CPU, memory, GPU utilization, pod health
- **Application:** Request rate, error rate, latency (P50/P95/P99)
- **LLM-specific:** Token count, cost per request, model latency
- **Quality:** Hallucination rate, faithfulness, relevance scores
- **Safety:** Toxicity, PII leakage, jailbreak attempt rate
- **Business:** User satisfaction, task completion rate, CSAT

### Q8: What is a feature flag and how is it used in LLMOps?

**Answer:** A feature flag is a runtime toggle that enables or disables functionality without redeployment. In LLMOps, feature flags gate:

- New prompt template versions
- Model version switches (e.g., GPT-4o-mini → GPT-4o)
- Agent behavior changes
- Experimental retrieval strategies

This enables instant rollback and safe experimentation with live traffic.

---

## Intermediate Level

### Q9: Explain model routing and its role in cost optimization.

**Answer:** Model routing dynamically directs queries to different model tiers based on query complexity:

1. A lightweight classifier (often GPT-4o-mini itself) assesses query complexity
2. Simple queries (classification, extraction) route to budget models (GPT-4o-mini)
3. Complex queries (multi-step reasoning, code generation) route to premium models (GPT-4o)

This can reduce costs by 40-70% while maintaining quality on tasks that require it. The routing logic must be fast enough not to add significant latency, and fallback logic handles classifier errors.

### Q10: How does semantic caching work and what are its trade-offs?

**Answer:** Semantic caching stores responses indexed by query embeddings rather than exact string matches:

1. Incoming query is embedded using a text embedding model
2. The embedding is compared against cached embeddings using cosine similarity
3. If similarity exceeds a threshold (e.g., 0.95), the cached response is returned
4. Otherwise, the LLM is called and the result is cached

**Trade-offs:**
- **Pro:** Eliminates redundant API calls for similar queries (20-50% cost savings)
- **Pro:** Reduces latency for cache hits
- **Con:** Embedding computation adds overhead on cache misses
- **Con:** Threshold tuning is critical — too low returns wrong cached answers, too high misses opportunities
- **Con:** Cache invalidation is challenging when the underlying data changes

### Q11: How would you implement A/B testing for a new prompt template?

**Answer:** Implementation steps:

1. **Define variants:** Control (current prompt) and treatment (new prompt)
2. **Assign users:** Use deterministic hash-based bucketing on user_id to ensure consistency
3. **Traffic split:** Configure weights (e.g., 80% control, 20% treatment)
4. **Log metrics:** Track latency, quality scores, user satisfaction per variant
5. **Statistical analysis:** After sufficient sample size, compare metrics using appropriate tests (t-test, chi-squared)
6. **Decision:** Promote treatment if statistically significant improvement, or iterate

Key considerations: ensure the assignment is sticky (same user always sees same variant), set minimum sample sizes before analyzing, and account for novelty effects.

### Q12: What is the role of distributed tracing in LLMOps?

**Answer:** Distributed tracing tracks a single request as it flows through multiple services. For LLM applications, this typically includes:

1. **API Gateway** → authentication, rate limiting
2. **Retrieval** → vector search, document fetching
3. **Prompt Assembly** → template rendering, context insertion
4. **LLM Inference** → API call to model endpoint
5. **Post-processing** → output parsing, guardrails, formatting

OpenTelemetry captures spans at each step with attributes like token count, retrieval document count, and model name. This enables identifying bottlenecks, debugging failures, and optimizing the full pipeline.

### Q13: How do you handle prompt injection attacks in production?

**Answer:** Multi-layer defense strategy:

1. **Input sanitization:** Detect and block known injection patterns ("ignore previous instructions", "system prompt")
2. **System prompt hardening:** Use delimiters, explicit boundaries, and role separation
3. **Input classification:** Use a lightweight model to classify inputs as potentially malicious
4. **Output validation:** Verify outputs don't contain system prompt content or unexpected formats
5. **Rate limiting:** Limit request frequency to prevent automated attacks
6. **Monitoring:** Log and alert on suspected injection attempts for investigation

No single layer is sufficient — defense in depth is essential.

### Q14: Explain the compliance requirements for deploying LLM applications under GDPR.

**Answer:** Key GDPR requirements for LLM applications:

1. **Data minimization:** Only send necessary data in prompts; strip PII before API calls
2. **Right to erasure:** Implement data deletion pipelines for user data in logs and caches
3. **Consent management:** Obtain explicit consent before processing personal data
4. **Data residency:** Ensure data stays within required geographic regions (Azure OpenAI supports regional deployment)
5. **Audit logging:** Maintain immutable logs of data processing activities
6. **Transparency:** Inform users when they are interacting with AI and how their data is used
7. **No training on customer data:** Azure OpenAI by default does not use customer data for training

### Q15: How would you set up a monitoring and alerting system for an LLM application?

**Answer:** A production monitoring setup includes:

1. **Instrumentation:** OpenTelemetry SDK in application code with auto-instrumentation for OpenAI calls
2. **Metrics collection:** Prometheus-style metrics for latency, token usage, cost, error rates
3. **Tracing:** Distributed traces across retrieval → generation → post-processing
4. **Dashboards:** Grafana dashboards showing real-time metrics, cost trends, and quality scores
5. **Alerts:**
   - P99 latency > 5s (Warning)
   - Error rate > 2% (Critical)
   - Daily token budget > 80% (Warning)
   - Hallucination rate > 5% (Critical)
   - Hourly cost > 2x expected (Warning)
6. **Log aggregation:** Centralized logs with query/response samples for debugging

---

## Advanced Level

### Q16: Design an end-to-end LLMOps pipeline for a customer support chatbot at scale.

**Answer:** Architecture:

```
Users → CDN/WAF → API Gateway → Load Balancer
                                      │
                         ┌────────────▼────────────┐
                         │    Application Service   │
                         │  (Container Apps / AKS)  │
                         └────────────┬────────────┘
                                      │
                    ┌─────────────────┼─────────────────┐
                    │                 │                 │
             ┌──────▼──────┐  ┌──────▼──────┐  ┌──────▼──────┐
             │  Semantic   │  │  Retrieval  │  │  Guardrails │
             │  Cache      │  │  (AI Search)│  │  Pipeline   │
             │  (Redis)    │  │             │  │             │
             └─────────────┘  └─────────────┘  └─────────────┘
                                      │
                         ┌────────────▼────────────┐
                         │     Model Router        │
                         │  (complexity classifier)│
                         └────────────┬────────────┘
                                      │
                         ┌────────────▼────────────┐
                         │    Azure OpenAI Service  │
                         │  gpt-4o / gpt-4o-mini   │
                         └─────────────────────────┘
```

**Key components:**
- **IaC:** Bicep templates for all resources, parameterized per environment
- **CI/CD:** GitHub Actions for prompt testing, evaluation, and deployment
- **Experiment tracking:** MLflow for prompt versioning and metric comparison
- **A/B testing:** Hash-based bucketing with feature flags for safe rollouts
- **Monitoring:** OpenTelemetry + Application Insights + custom quality evaluators
- **Cost optimization:** Semantic caching (Redis) + model routing (GPT-4o-mini for simple queries)
- **Security:** Azure Content Safety, PII detection, prompt injection detection
- **Compliance:** GDPR-compliant data handling, audit logging, data residency

### Q17: How would you implement a custom evaluation framework for LLM outputs?

**Answer:** A robust evaluation framework includes:

1. **Offline evaluation (pre-deployment):**
   - Golden dataset with human-annotated reference answers
   - Automated metrics: BLEU, ROUGE, BERTScore for similarity
   - LLM-as-judge: Use GPT-4o to evaluate faithfulness, relevance, coherence
   - Safety checks: Toxicity, bias, PII detection on outputs
   - Regression testing: Ensure new versions don't degrade on known-good queries

2. **Online evaluation (post-deployment):**
   - Sampling: Random sample of production queries for human review
   - User feedback: Thumbs up/down, free-text feedback
   - Implicit signals: Task completion, re-engagement, escalation rate
   - Automated quality scoring: Lightweight model scores outputs on faithfulness

3. **Evaluation pipeline:**
```python
async def evaluate_response(query, response, context, reference=None):
    scores = {}
    scores["faithfulness"] = await llm_judge_score(
        f"Rate faithfulness (0-1): Query: {query} Context: {context} Response: {response}"
    )
    scores["relevance"] = await llm_judge_score(
        f"Rate relevance (0-1): Query: {query} Response: {response}"
    )
    scores["toxicity"] = content_safety.check(response)
    scores["pii_detected"] = pii_detector.check(response)
    if reference:
        scores["bert_score"] = bert_score(response, reference)
    return scores
```

### Q18: Explain how you would implement a multi-region deployment for an LLM application with failover.

**Answer:** Multi-region deployment strategy:

1. **Regional Azure OpenAI deployments:** Deploy models in multiple regions (East US, West Europe, Southeast Asia) for latency and availability
2. **Traffic Manager / Front Door:** Azure Front Door routes to nearest healthy backend with automatic failover
3. **Data replication:** Vector index (AI Search) replicated across regions; prompt templates stored in globally replicated storage
4. **Stateless application:** Container Apps in each region; no session affinity required
5. **Health checks:** Application-level health checks verify LLM endpoint availability
6. **Failover logic:** If primary region OpenAI is unhealthy, route to secondary region

**Considerations:**
- Azure OpenAI capacity varies by region — check availability before deployment
- Data residency requirements may restrict which regions can process certain data
- Cost varies by region — balance latency requirements against cost
- Embedding consistency: Use the same embedding model version across regions

### Q19: How would you design a cost optimization system that automatically adjusts model routing based on real-time quality feedback?

**Answer:** Adaptive cost-quality optimization system:

1. **Query classification layer:**
   - Lightweight model classifies queries into complexity tiers
   - Historical data trains the classifier on which queries need premium models

2. **Dynamic routing with feedback loop:**
```python
class AdaptiveRouter:
    def __init__(self):
        self.quality_threshold = 0.8
        self.escalation_rate_budget = 0.15  # Max 15% escalation

    async def route(self, query: str, user_id: str) -> str:
        complexity = await self.classifier.predict(query)

        if complexity < 0.3:
            model = "gpt-4o-mini"
        elif complexity < 0.7:
            model = "gpt-4o"
        else:
            model = "gpt-4o"

        response = await self.call_model(model, query)

        # Async quality evaluation
        quality = await self.evaluate_async(query, response)

        # If quality is below threshold, escalate and re-answer
        if quality < self.quality_threshold and model != "gpt-4o":
            response = await self.call_model("gpt-4o", query)
            self.log_escalation(query, model, "gpt-4o")

        # Retrain classifier with feedback
        self.update_training_data(query, quality, model)

        return response
```

3. **Metrics and controls:**
   - Track escalation rate — if > budget, tighten classifier thresholds
   - Monitor quality by tier — ensure budget tier meets minimum quality
   - Cost dashboard shows savings from routing decisions
   - Weekly model performance review adjusts routing policies

### Q20: How would you implement compliance automation for an LLM application handling healthcare data (HIPAA)?

**Answer:** HIPAA-compliant LLMOps architecture:

1. **Data handling:**
   - PHI (Protected Health Information) detection and redaction before any LLM call
   - Use Azure OpenAI with data processing agreement — no training on customer data
   - Data encrypted at rest (AES-256) and in transit (TLS 1.2+)
   - Data residency: all processing within approved Azure regions

2. **Access control:**
   - Azure AD with RBAC for all resources
   - Service principals for application access — no shared keys
   - Just-in-time access for production debugging

3. **Audit logging:**
   - Immutable audit logs for every API call (who, when, what, from where)
   - Query and response logging with PHI redaction
   - Log retention aligned with HIPAA requirements (6 years)

4. **Automated compliance checks:**
```python
class HIPAAComplianceCheck:
    def pre_call_check(self, prompt: str, user_context: dict) -> dict:
        checks = {
            "phi_detected": self.detect_phi(prompt),
            "phi_redacted": self.redact_phi(prompt) if checks["phi_detected"] else prompt,
            "authorized": self.check_authorization(user_context),
            "encryption_in_transit": self.verify_tls(),
            "data_residency": self.verify_region(user_context["region"]),
            "audit_logged": self.log_audit_event(user_context, prompt)
        }
        return checks

    def post_call_check(self, response: str) -> dict:
        return {
            "phi_leaked": self.detect_phi(response),
            "response_filtered": self.filter_response(response),
            "audit_logged": self.log_audit_event(response=response)
        }
```

5. **Continuous compliance:**
   - Automated scans of logs for PHI leakage
   - Quarterly access reviews
   - Penetration testing of API endpoints
   - BAA (Business Associate Agreement) with all third-party services
