# Module 9: Monitoring & Observability — Quiz

## Instructions
- Answer all 20 questions
- Each question has only one correct answer
- Click on each question to reveal the answer
- Score yourself at the end using the interpretation table

---

### Q1. Which of the following is NOT one of the three pillars of observability?

- A) Logs
- B) Metrics
- C) Traces
- D) Dashboards

<details>
<summary>Answer</summary>

**D) Dashboards**

Dashboards are a *visualization* tool built on top of the three pillars (logs, metrics, traces). They are not a pillar of observability themselves.

</details>

---

### Q2. What metric should you primarily monitor to detect a cost spike in an LLM service?

- A) Request latency
- B) Token usage per request
- C) Error rate
- D) CPU utilization

<details>
<summary>Answer</summary>

**B) Token usage per request**

Cost is directly proportional to token usage (input + output tokens). A spike in tokens per request indicates a cost increase, which could be caused by longer prompts, verbose outputs, or prompt injection.

</details>

---

### Q3. What is "embedding drift" in the context of LLM systems?

- A) The LLM model weights change over time
- B) The semantic distribution of input text embeddings shifts from the calibration period
- C) The embedding model is replaced with a different one
- D) The vector database runs out of storage

<details>
<summary>Answer</summary>

**B) The semantic distribution of input text embeddings shifts from the calibration period**

Embedding drift occurs when the distribution of input embeddings moves away from the reference distribution, indicating that the types of queries the system receives have changed semantically.

</details>

---

### Q4. Which statistical test is commonly used for Population Stability Index (PSI) in drift detection?

- A) Chi-squared test
- B) Kolmogorov-Smirnov test
- C) It computes the divergence between binned probability distributions
- D) Student's t-test

<details>
<summary>Answer</summary>

**C) It computes the divergence between binned probability distributions**

PSI bins both reference and current distributions, computes the proportion in each bin, and measures divergence as: PSI = Σ(current% - reference%) × ln(current% / reference%).

</details>

---

### Q5. In structured logging, why is it important to include a `trace_id` in each log entry?

- A) To compress the log file size
- B) To correlate log entries across distributed services for the same request
- C) To encrypt sensitive log data
- D) To filter out duplicate log entries

<details>
<summary>Answer</summary>

**B) To correlate log entries across distributed services for the same request**

The `trace_id` propagates across all services handling a single request, allowing you to reconstruct the full lifecycle of a request across multiple microservices.

</details>

---

### Q6. What is the recommended approach for handling PII in production logs?

- A) Log PII only during business hours
- B) Redact, tokenize, or hash PII before logs leave the application
- C) Store PII logs in a separate database
- D) Only log PII for error events

<details>
<summary>Answer</summary>

**B) Redact, tokenize, or hash PII before logs leave the application**

PII should be handled at the application boundary using redaction (permanent removal), tokenization (reversible replacement), or hashing (one-way transformation) before logs are sent to any external system.

</details>

---

### Q7. What does p99 latency represent?

- A) The average response time across all requests
- B) The response time that 99% of requests are faster than
- C) The slowest response time ever recorded
- D) The response time of the 99th request

<details>
<summary>Answer</summary>

**B) The response time that 99% of requests are faster than**

p99 (99th percentile) latency means that 99% of requests complete within this time. It captures tail latency — the experience of the slowest 1% of users.

</details>

---

### Q8. Which tool provides vendor-neutral distributed tracing instrumentation?

- A) Prometheus
- B) Grafana
- C) OpenTelemetry
- D) ELK Stack

<details>
<summary>Answer</summary>

**C) OpenTelemetry**

OpenTelemetry is a CNCF project that provides vendor-neutral APIs, SDKs, and tools for instrumenting, generating, collecting, and exporting telemetry data (traces, metrics, logs).

</details>

---

### Q9. What is "hallucination rate" in LLM monitoring?

- A) The percentage of requests that time out
- B) The proportion of LLM outputs containing factually incorrect information
- C) The rate at which the model generates nonsensical tokens
- D) The frequency of API errors from the LLM provider

<details>
<summary>Answer</summary>

**B) The proportion of LLM outputs containing factually incorrect information**

Hallucination rate measures how often the LLM generates plausible-sounding but factually incorrect or fabricated content. It's typically measured via LLM-as-judge evaluation or human review.

</details>

---

### Q10. In a Prometheus alert rule, what does `for: 5m` mean?

- A) The alert will fire for 5 minutes and then auto-resolve
- B) The condition must be continuously true for 5 minutes before the alert fires
- C) The alert will send notifications every 5 minutes
- D) The alert was created 5 minutes ago

<details>
<summary>Answer</summary>

**B) The condition must be continuously true for 5 minutes before the alert fires**

The `for` clause specifies a pending duration. The alert transitions from `pending` to `firing` only if the condition remains true for the entire duration, preventing alert flapping.

</details>

---

### Q11. What is the purpose of a "canary deployment" in LLM monitoring?

- A) To test the LLM on bird-related queries
- B) To route a small percentage of traffic to a new version and compare metrics against baseline
- C) To automatically roll back all deployments after errors
- D) To pre-warm the model cache before full deployment

<details>
<summary>Answer</summary>

**B) To route a small percentage of traffic to a new version and compare metrics against baseline**

Canary deployments gradually expose a new model/prompt version to a small subset of users, allowing comparison of latency, error rates, and quality metrics against the production baseline before full rollout.

</details>

---

### Q12. Which log retention policy is most appropriate for audit logs in a regulated industry?

- A) 30 days hot, no archive
- B) 7 days hot, 30 days cold, delete after
- C) 90 days hot, 1 year warm, 7 years cold archive
- D) No retention — delete immediately after processing

<details>
<summary>Answer</summary>

**C) 90 days hot, 1 year warm, 7 years cold archive**

Regulated industries (healthcare, finance, government) typically require audit logs to be retained for extended periods (often 7+ years). Hot storage enables immediate queries, while cold archive satisfies compliance at lower cost.

</details>

---

### Q13. What is the Page-Hinkley test used for in drift detection?

- A) Measuring the cosine similarity between embeddings
- B) Detecting change points in a sequence of values
- C) Computing the population stability index
- D) A/B testing two model versions

<details>
<summary>Answer</summary>

**B) Detecting change points in a sequence of values**

The Page-Hinkley test monitors cumulative sums of deviations from the mean and detects when the mean of a signal has changed. It's used for online (real-time) concept drift detection.

</details>

---

### Q14. In OpenTelemetry, what is the relationship between traces, spans, and context?

- A) Traces contain spans, and context propagates between spans across services
- B) Spans contain traces, and context is stored in the database
- C) Context contains traces, and spans are optional
- D) They are three independent concepts with no relationship

<details>
<summary>Answer</summary>

**A) Traces contain spans, and context propagates between spans across services**

A **trace** represents the end-to-end journey of a request. A **trace** is composed of **spans** (individual operations). **Context** (trace ID, span ID, baggage) propagates across service boundaries to link spans into a complete trace.

</details>

---

### Q15. What is the primary advantage of "shadow mode evaluation" over A/B testing?

- A) It uses less compute resources
- B) It allows testing a new model on production traffic without affecting user experience
- C) It is more statistically rigorous
- D) It automatically selects the best model

<details>
<summary>Answer</summary>

**B) It allows testing a new model on production traffic without affecting user experience**

Shadow mode runs the new model alongside the production model on the same traffic, but only returns the production model's output to users. This eliminates user-facing risk while providing comparison data.

</details>

---

### Q16. What does Maximum Mean Discrepancy (MMD) measure in drift detection?

- A) The maximum distance between individual data points
- B) The distance between the means of two distributions in a reproducing kernel Hilbert space
- C) The maximum number of misclassified samples
- D) The memory usage difference between two models

<details>
<summary>Answer</summary>

**B) The distance between the means of two distributions in a reproducing kernel Hilbert space**

MMD measures distributional distance by embedding distributions into a reproducing kernel Hilbert space (RKHS) and computing the distance between their means. It can detect any distributional difference given a characteristic kernel.

</details>

---

### Q17. Which Grafana panel type is most suitable for displaying the distribution of LLM response latencies?

- A) Stat panel (single number)
- B) Heatmap panel
- C) Table panel
- D) Bar gauge

<details>
<summary>Answer</summary>

**B) Heatmap panel**

A heatmap displays the distribution of values over time, making it ideal for latency distributions. You can visually identify p50/p95/p99 percentiles, bimodal distributions, and latency spikes.

</details>

---

### Q18. What is the recommended sampling strategy for real-time LLM quality evaluation?

- A) Evaluate every single request
- B) Evaluate a random sample (e.g., 5%) of requests using LLM-as-judge
- C) Only evaluate requests that resulted in errors
- D) Evaluate only the first request of each hour

<details>
<summary>Answer</summary>

**B) Evaluate a random sample (e.g., 5%) of requests using LLM-as-judge**

Evaluating every request is too expensive. A random sample provides statistically meaningful quality visibility while controlling costs. LLM-as-judge (using a cheaper model to evaluate a more expensive one) balances quality and cost.

</details>

---

### Q19. What happens when you set `for: 0m` in a Prometheus alert rule?

- A) The alert is disabled
- B) The alert fires immediately when the condition is met, with no pending period
- C) The alert fires once per minute
- D) The alert fires after 0 seconds, which causes an error

<details>
<summary>Answer</summary>

**B) The alert fires immediately when the condition is met, with no pending period**

Setting `for: 0m` (or omitting the `for` clause) means the alert transitions to `firing` as soon as the expression evaluates to true. This is suitable for critical alerts where immediate notification is needed.

</details>

---

### Q20. In a Langfuse trace, what is the hierarchy of elements?

- A) Trace → Generation → Span
- B) Trace → Span → Generation/Observation
- C) Span → Trace → Generation
- D) Generation → Span → Trace

<details>
<summary>Answer</summary>

**B) Trace → Span → Generation/Observation**

In Langfuse, a **Trace** is the top-level container. Within a trace, you have **Spans** (generic operations) and **Generations** (LLM-specific calls with token usage). Both spans and generations are types of **Observations** within a trace.

</details>

---

## Score Interpretation

| Score | Level | Recommendation |
|-------|-------|----------------|
| **18-20** | Expert | Ready for production monitoring roles. Consider contributing to observability tooling. |
| **14-17** | Proficient | Strong foundation. Focus on hands-on practice with OpenTelemetry and Grafana. |
| **10-13** | Developing | Review the drift detection and distributed tracing sections. Build a monitoring prototype. |
| **6-9** | Foundational | Re-read core concepts, especially the three pillars and structured logging. |
| **0-5** | Beginner | Start with Section 9.1 and work through each concept with code examples. |

### Recommended Next Steps by Score

**< 10**: Focus on setting up a basic monitoring stack (Prometheus + Grafana) and instrumenting a simple LLM application.

**10-14**: Implement drift detection on an embedding-based system and practice interpreting traces in Jaeger or Tempo.

**14-17**: Build a canary deployment pipeline with automated metric comparison and alerting.

**17-20**: Design a complete observability platform for a multi-model LLM service with quality sampling and cost attribution.
