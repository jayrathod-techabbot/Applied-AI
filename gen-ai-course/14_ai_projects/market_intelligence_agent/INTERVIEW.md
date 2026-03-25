# INTERVIEW.md — Market Intelligence Agent

## Q1: Walk me through this project at a high level.

**A:** We built a multi-agent platform that autonomously monitors market signals and produces executive-ready competitive intelligence. The system has four agents — an Orchestrator that plans the workflow, a Retrieval Agent that queries Azure AI Search, a Reasoning Agent using GPT-4o to synthesize analysis, and a Validation Agent that scores confidence by comparing claim embeddings against source chunk embeddings. The final output is a structured narrative with a 0–1 confidence score so stakeholders know exactly how grounded each insight is.

---

## Q2: Why multi-agent instead of a single RAG chain?

**A:** A single RAG chain collapses retrieval and reasoning into one step, which makes it hard to audit where a hallucination originated. By separating retrieval, reasoning, and validation into distinct agents, we get three things: (1) each agent can be independently tested and improved, (2) the validation agent can catch reasoning drift before it reaches the user, and (3) we can swap the retrieval backend (e.g., from Azure AI Search to a different vector DB) without touching the reasoning layer.

---

## Q3: How does the confidence scoring work?

**A:** We embed both the final output (split into sentences) and the source chunks that were retrieved. We then compute cosine similarity between each output sentence and every source chunk, taking the max similarity per sentence. The confidence score is the mean across all sentences. A score above 0.75 means the claim is well-supported. Below 0.50 we flag it as a hallucination risk and optionally suppress that section from the executive report.

---

## Q4: How did you handle the RAG chunking strategy?

**A:** Market data comes from diverse formats — news articles, earnings calls, analyst PDFs. We used a hybrid chunking approach: sentence-aware chunking for long-form documents (splitting at sentence boundaries, targeting 512 tokens per chunk with 64-token overlap), and document-level chunking for short structured data like press releases. We stored both the chunk and the parent document ID so we could reconstruct full context if needed.

---

## Q5: How is this deployed and what does the production setup look like?

**A:** The orchestrator is exposed as a FastAPI endpoint, containerized with Docker, and deployed on Azure Container Apps. Azure AI Search handles vector + keyword hybrid retrieval. Reports are persisted to Azure Blob Storage. We use Azure Managed Identity for auth — no secrets in environment variables in production. We also set up Application Insights for latency and token usage monitoring per agent invocation.

---

## Q6: What would you change if you were building this again?

**A:** Two things. First, I'd add a structured output layer (Pydantic models with `with_structured_output`) so the Reasoning Agent always returns JSON instead of free text — it removes a lot of downstream parsing fragility. Second, I'd use LangGraph instead of AgentExecutor for the orchestration layer, because explicit state graphs make conditional branching (e.g., "if confidence < 0.5, re-retrieve with a broader query") far cleaner than the current hack of checking intermediate steps post-hoc.

---

## Key Terms to Use in Interview

- **Hybrid retrieval** (vector + BM25 keyword in Azure AI Search)
- **Confidence scoring via embedding cosine similarity**
- **Agent-level separation of concerns**
- **Managed Identity** (not API keys in production)
- **Azure Container Apps** for serverless container deployment
- **Application Insights** for observability
