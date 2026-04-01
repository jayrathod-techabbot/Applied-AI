# Module 13: LLMOps — Quiz

## Instructions
- 20 multiple choice questions
- Each question has one correct answer
- Click on the answer to reveal the explanation

---

## Questions

### Q1. What is LLMOps?

A) Training large language models from scratch  
B) A set of practices for deploying, monitoring, and maintaining LLM applications in production  
C) A programming language for writing prompts  
D) A cloud service for hosting open-source models  

<details>
<summary>Answer</summary>

**B)** LLMOps encompasses the practices, tools, and processes for deploying, monitoring, and maintaining LLM-powered applications in production. It extends traditional MLOps with LLM-specific concerns like prompt management and token-level observability.

</details>

---

### Q2. How does LLMOps differ from traditional MLOps?

A) LLMOps does not require monitoring  
B) LLMOps focuses on pre-trained foundation models and prompt management rather than custom model training  
C) LLMOps is only applicable to open-source models  
D) LLMOps replaces the need for CI/CD pipelines  

<details>
<summary>Answer</summary>

**B)** In LLMOps, the core artifacts shift from model weights and training pipelines to prompts, chains, agents, and fine-tuned adapters. Evaluation focuses on hallucination rates and faithfulness rather than traditional accuracy metrics.

</details>

---

### Q3. Which tool is commonly used for experiment tracking in LLMOps?

A) Docker  
B) MLflow  
C) Kubernetes  
D) Terraform  

<details>
<summary>Answer</summary>

**B)** MLflow is a platform for tracking experiments, logging parameters, metrics, and artifacts. It supports logging OpenAI model configurations, prompt templates, and evaluation metrics for reproducibility.

</details>

---

### Q4. What is Infrastructure as Code (IaC)?

A) Writing application logic inside infrastructure configurations  
B) Managing and provisioning infrastructure through machine-readable definition files  
C) Using AI to generate infrastructure code automatically  
D) A type of programming language for cloud services  

<details>
<summary>Answer</summary>

**B)** IaC is the practice of managing and provisioning infrastructure through code and automation rather than manual processes. Tools like Bicep and Terraform enable version-controlled, reproducible infrastructure deployments.

</details>

---

### Q5. Which Azure service provides hosted LLM inference endpoints?

A) Azure Functions  
B) Azure OpenAI Service  
C) Azure Blob Storage  
D) Azure DevOps  

<details>
<summary>Answer</summary>

**B)** Azure OpenAI Service provides access to OpenAI models (GPT-4o, GPT-4o-mini, embeddings) through managed API endpoints with enterprise security, compliance, and regional availability.

</details>

---

### Q6. What deployment strategy routes a small percentage of traffic to a new version before full rollout?

A) Blue-Green deployment  
B) Rolling deployment  
C) Canary deployment  
D) Shadow deployment  

<details>
<summary>Answer</summary>

**C)** Canary deployment gradually shifts a small percentage of traffic to the new version while monitoring for issues. If metrics remain healthy, traffic is progressively increased to 100%.

</details>

---

### Q7. In A/B testing for LLMs, what ensures a user consistently receives the same variant?

A) Random assignment on each request  
B) Deterministic hash-based bucketing using user ID  
C) Round-robin assignment  
D) Assigning based on time of day  

<details>
<summary>Answer</summary>

**B)** Hash-based bucketing computes a deterministic hash of the user ID to assign them to a variant. This ensures the same user always sees the same variant across sessions, which is critical for meaningful A/B test results.

</details>

---

### Q8. What is a feature flag in the context of LLMOps?

A) A database schema for storing features  
B) A runtime toggle that gates new prompts or models without redeployment  
C) A machine learning feature engineering technique  
D) A flag in the model weights indicating importance  

<details>
<summary>Answer</summary>

**B)** Feature flags (or feature toggles) allow operators to enable or disable functionality at runtime. In LLMOps, they gate new prompt templates, model versions, or agent behaviors without requiring code deployment.

</details>

---

### Q9. Which layer of monitoring tracks hallucination rates and faithfulness scores?

A) Infrastructure monitoring  
B) Application monitoring  
C) LLM quality monitoring  
D) Business monitoring  

<details>
<summary>Answer</summary>

**C)** LLM quality monitoring tracks metrics specific to language model outputs, including hallucination rate, faithfulness to source documents, relevance scores, and toxicity levels.

</details>

---

### Q10. What is OpenTelemetry used for in LLMOps?

A) Training language models  
B) Distributed tracing and observability across services  
C) Storing vector embeddings  
D) Managing API keys  

<details>
<summary>Answer</summary>

**B)** OpenTelemetry is an open-source observability framework for distributed tracing, metrics, and logs. In LLMOps, it traces requests across retrieval and generation steps, capturing latency, token usage, and error information.

</details>

---

### Q11. What is prompt injection?

A) A technique for optimizing prompt length  
B) A security attack where malicious instructions are embedded in user input to alter model behavior  
C) A method for inserting system prompts automatically  
D) A way to inject new training data into a model  

<details>
<summary>Answer</summary>

**B)** Prompt injection is a security threat where attackers embed adversarial instructions in user input that attempt to override the system prompt or extract sensitive information. Mitigation includes input sanitization and multi-layer filtering.

</details>

---

### Q12. Which Azure service provides automated content safety classification?

A) Azure Monitor  
B) Azure Content Safety  
C) Azure Key Vault  
D) Azure Container Registry  

<details>
<summary>Answer</summary>

**B)** Azure Content Safety is an AI service that analyzes text and images for harmful content across categories including hate, sexual content, violence, and self-harm, returning severity scores for each category.

</details>

---

### Q13. What is PII in the context of LLM security?

A) Prompt Injection Indicator  
B) Personally Identifiable Information  
C) Private Interface Identifier  
D) Performance Impact Index  

<details>
<summary>Answer</summary>

**B)** PII (Personally Identifiable Information) includes data like emails, SSNs, phone numbers, and credit card numbers. LLM applications must detect and redact PII in both inputs and outputs to comply with privacy regulations.

</details>

---

### Q14. Which regulation requires the right to erasure and data minimization for AI systems?

A) SOC 2  
B) HIPAA  
C) GDPR  
D) PCI DSS  

<details>
<summary>Answer</summary>

**C)** GDPR (General Data Protection Regulation) mandates data minimization, the right to erasure, and explicit consent for data processing. LLM applications must implement log retention policies and PII redaction to comply.

</details>

---

### Q15. What is model routing in the context of cost optimization?

A) Routing network traffic to the nearest data center  
B) Dynamically selecting model tiers based on query complexity to optimize cost-quality tradeoff  
C) Redirecting failed API calls to backup models  
D) Loading model weights from different storage locations  

<details>
<summary>Answer</summary>

**B)** Model routing analyzes incoming queries and directs them to the appropriate model tier—using cheaper models (e.g., GPT-4o-mini) for simple tasks and premium models (e.g., GPT-4o) for complex reasoning, reducing costs by 40-70%.

</details>

---

### Q16. What is semantic caching in LLM applications?

A) Caching HTTP responses based on URL  
B) Storing and retrieving responses for semantically similar queries to avoid redundant API calls  
C) Caching model weights in GPU memory  
D) Storing embeddings in a vector database  

<details>
<summary>Answer</summary>

**B)** Semantic caching compares the embedding of an incoming query against cached query embeddings. If a sufficiently similar query is found (above a similarity threshold), the cached response is returned without making an LLM API call.

</details>

---

### Q17. What metric indicates the effectiveness of a semantic cache?

A) Token count per request  
B) Cache hit rate  
C) Model accuracy  
D) API latency  

<details>
<summary>Answer</summary>

**B)** Cache hit rate measures the percentage of queries served from cache versus requiring a new LLM API call. A low hit rate (< 30%) suggests the cache is not effectively capturing similar queries.

</details>

---

### Q18. What is the purpose of a model registry in LLMOps?

A) To store user data securely  
B) To track model versions, metadata, and lineage for reproducibility  
C) To register new Azure subscriptions  
D) To manage API rate limits  

<details>
<summary>Answer</summary>

**B)** A model registry is a central repository that tracks model versions, associated metadata (parameters, metrics, tags), and lineage. This enables reproducibility, rollback, and governance across the model lifecycle.

</details>

---

### Q19. In a blue-green deployment, how is traffic switched to the new version?

A) Gradually over several hours  
B) Atomically by switching the load balancer or DNS  
C) By restarting each server individually  
D) By updating the database schema  

<details>
<summary>Answer</summary>

**B)** Blue-green deployment runs two identical environments simultaneously. Traffic is switched atomically (via load balancer or DNS change) from the old version to the new version, enabling instant rollback by switching back.

</details>

---

### Q20. What is the primary purpose of token budgets in LLMOps?

A) To increase model accuracy  
B) To prevent runaway costs by limiting tokens consumed per user or team  
C) To improve inference speed  
D) To store tokens securely  

<details>
<summary>Answer</summary>

**B)** Token budgets set limits on the number of tokens that can be consumed by a user, team, or application within a time period. This prevents unexpected cost spikes from high-volume usage or adversarial inputs.

</details>
