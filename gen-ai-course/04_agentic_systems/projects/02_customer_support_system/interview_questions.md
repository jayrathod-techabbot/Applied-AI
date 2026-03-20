# Interview Questions — Multi-Agent Customer Support System

20 interview questions with detailed answers covering architecture design,
implementation trade-offs, and scaling scenarios from this project.

---

## Basic Questions

### Q1. What is Hub-and-Spoke architecture in multi-agent systems, and how does this project implement it?

**A:** Hub-and-Spoke is a topology where one central agent (the hub) coordinates multiple specialist agents (the spokes). All communication flows through the hub — spokes do not communicate directly with each other.

In this project:
- **Hub**: The `intent_classifier` + `router` node pair acts as the orchestrator. It receives every ticket, classifies intent, and dispatches to the correct spoke.
- **Spokes**: `billing_agent`, `tech_agent`, `general_agent` — each handles one domain independently.
- **Benefit**: Adding a new specialist (e.g., `legal_agent`) requires only adding a new node and a new routing edge. No existing agents change.
- **Contrast**: A mesh architecture would allow, say, the billing agent to query the tech agent. More flexible, but exponentially harder to debug and monitor.

---

### Q2. What is intent classification, and why is it the critical first step in this pipeline?

**A:** Intent classification is the task of mapping a user's natural language message to a predefined category that determines how the system should respond. Here the categories are: `billing`, `technical`, `general`, and `escalate`.

It is the critical first step because:
1. **Routing accuracy**: Wrong classification sends a billing question to the tech agent, which has no billing KB — lowering confidence and triggering unnecessary escalation.
2. **Efficiency**: We avoid running all three specialist agents on every ticket (expensive). Instead, only one relevant specialist is invoked.
3. **Context-awareness**: By including the conversation history in the classifier prompt, we handle follow-up messages correctly (e.g., "And what about the refund?" correctly maps to billing even without the word "billing").

---

### Q3. What is a LangGraph StateGraph, and why is it used instead of a simple if/else routing function?

**A:** LangGraph's `StateGraph` is a directed graph where nodes are Python functions and edges are transitions between them. It provides:

1. **Persistent checkpointing**: Every node's output is checkpointed to `MemorySaver`, enabling pause/resume (critical for HITL).
2. **Conditional routing**: Edges can be dynamic functions (`route_by_intent`) rather than hardcoded if/else.
3. **State management**: A shared `TicketState` TypedDict flows through all nodes. No global variables or side-channel communication.
4. **Observability**: The graph structure is inspectable and renderable as a diagram.
5. **Interrupt support**: `interrupt_before=["escalation_handler"]` pauses execution for human review.

A plain if/else function could do routing but cannot checkpoint state, support HITL pauses, or be visualized.

---

### Q4. What is HITL (Human-in-the-Loop) and when is it triggered in this system?

**A:** HITL is a pattern where an AI system pauses execution and waits for a human to review or augment the AI's output before continuing. It is essential for high-stakes domains where AI errors are costly.

**Trigger condition**: `confidence_score < CONFIDENCE_THRESHOLD` (default: 0.6).

**How it works here**:
1. The specialist agent runs and computes a confidence score from KB retrieval.
2. `confidence_check` evaluates the score.
3. If below threshold, the conditional edge routes to `escalation_handler`.
4. In production, LangGraph is compiled with `interrupt_before=["escalation_handler"]`, pausing the graph.
5. A human agent reviews the ticket, adds notes via `POST /escalation/resolve/{ticket_id}`.
6. The API calls `resume_after_escalation()`, which injects the notes and resumes via `hitl_resume`.

---

### Q5. What is TF-IDF, and why was it chosen over FAISS for this project?

**A:** TF-IDF (Term Frequency-Inverse Document Frequency) is a statistical measure that scores how relevant a term is to a document relative to the entire corpus. Cosine similarity between query and document TF-IDF vectors gives a relevance score.

**Why TF-IDF here (not FAISS)**:
- **Zero dependencies**: No GPU, no embedding model API key, works purely offline.
- **Transparency**: Scores are interpretable — we can explain why a result ranked highly.
- **Sufficient for short queries**: Support tickets are keyword-rich ("refund", "401 error", "invoice") — keyword matching works well.
- **Identical interface**: The `KnowledgeBaseMemory.search()` signature is identical to what a FAISS implementation would expose, making the upgrade a pure internal change.

**When to upgrade to FAISS**: When queries are semantically complex ("my payment didn't go through" should match "transaction failure") — FAISS with sentence embeddings handles synonyms and paraphrases better.

---

## Intermediate Questions

### Q6. How does FAISS enable semantic knowledge base search, and what would an upgrade look like?

**A:** FAISS (Facebook AI Similarity Search) stores dense vector embeddings and retrieves the nearest neighbors by L2 distance or inner product. Semantic search works because:
1. A sentence transformer model (e.g., `all-MiniLM-L6-v2`) encodes both the query and documents into 384-dimensional vectors.
2. Semantically similar text clusters together in this vector space.
3. "Payment didn't go through" and "transaction failed" have high cosine similarity even without shared keywords.

**Upgrade path for this project** (drop-in replacement):
```python
# Replace _build_index() with:
from sentence_transformers import SentenceTransformer
import faiss, numpy as np

model = SentenceTransformer("all-MiniLM-L6-v2")
embeddings = model.encode(self._chunks).astype("float32")
faiss.normalize_L2(embeddings)
self._index = faiss.IndexFlatIP(embeddings.shape[1])
self._index.add(embeddings)

# Replace search() with:
query_vec = model.encode([query]).astype("float32")
faiss.normalize_L2(query_vec)
scores, indices = self._index.search(query_vec, top_k)
```

The `KBResult` return type and all downstream code remain unchanged.

---

### Q7. How is session memory implemented, and what are its limitations at scale?

**A:** `SessionMemory` is an in-memory Python dict: `{session_id: List[BaseMessage]}`. Each `add_message()` call appends a `HumanMessage` or `AIMessage` to the list for that session. `get_context()` formats the last N messages as a plain string for injection into LLM prompts.

**Current limitations**:
- **Not persistent**: A server restart wipes all sessions.
- **Not distributed**: If you run 3 FastAPI instances, each has its own session store — a user could route to a different instance and lose history.
- **Memory leak risk**: Sessions that are never cleared accumulate indefinitely.

**Production upgrades**:
- Replace the dict with **Redis** (TTL-based expiry, distributed, persistent).
- Use LangGraph's **SqliteSaver** or **PostgresSaver** as the checkpoint backend instead of MemorySaver for persistent graph state.
- Add a session TTL: sessions inactive for > 24 hours are automatically expired.

---

### Q8. Why is Groq llama-3.3-70b specifically chosen for customer support?

**A:** Three key reasons:

1. **Latency**: Groq's LPU (Language Processing Unit) hardware delivers ~200–300ms inference for a 1k-token response from llama-3.3-70b. This is critical for real-time support chat where users expect < 2 second responses.

2. **Instruction following**: llama-3.3-70b scores near the top of open-source models on instruction-following benchmarks. For our use case, this means reliable JSON output from the intent classifier and the ability to follow KB-grounding instructions ("only use information from the provided excerpts").

3. **Context length**: 8k token context handles long conversation histories and large KB excerpts without truncation.

**Alternative**: GPT-4o for higher accuracy, Claude-3.5-Sonnet for long context (200k tokens). Groq is preferred when latency is the primary constraint.

---

### Q9. How is confidence scoring implemented, and why is it derived from KB retrieval rather than LLM self-assessment?

**A:** Confidence is computed in `_compute_confidence()`:
```
confidence = (score_1 * 0.6 + score_2 * 0.3 + score_3 * 0.1) * 2.5, capped at 1.0
```

**Why KB-derived, not LLM self-assessed**:
1. **LLM overconfidence**: LLMs often express high confidence even when hallucinating. Asking the LLM "how confident are you?" is unreliable.
2. **Auditability**: A KB score of 0.0 means "no relevant article found" — unambiguous and debuggable.
3. **Determinism**: The same query on the same KB always yields the same score, regardless of LLM temperature.
4. **Speed**: No extra LLM call needed.

**Calibration insight**: TF-IDF cosine similarity rarely exceeds 0.4 for reasonable queries, so we scale by 2.5 to map a "good" match (score 0.3) to ~0.75 confidence. This scaling factor should be tuned based on real-world data.

---

### Q10. Explain the TicketState TypedDict. Why TypedDict instead of a Pydantic BaseModel?

**A:** `TicketState` is a `TypedDict` — a Python type hint for dicts with known string keys. LangGraph's `StateGraph` requires TypedDict (or compatible dict subclass) for state schemas because:

1. **Merge semantics**: LangGraph merges node return dicts into the current state dict. Pydantic models have different merge semantics (they validate on assignment, don't support partial updates).
2. **No instantiation overhead**: TypedDict is a pure type hint — no constructor call per node.
3. **Reducer support**: LangGraph supports custom reducers (e.g., append-only for lists) via `Annotated[List[str], operator.add]` — this works with TypedDict but not Pydantic.
4. **Standard dict access**: All LangGraph internals use `state["key"]` — TypedDict documents this without adding a class hierarchy.

In contrast, Pydantic is used for the FastAPI request/response models (where validation and serialization matter most).

---

## Advanced Questions

### Q11. How do you handle ambiguous intents? For example: "I can't access my account and need to dispute a charge."

**A:** This message spans both `technical` (account access) and `billing` (dispute a charge). Current strategies:

1. **Priority classification**: The classifier picks the highest-priority intent. Billing disputes are higher-stakes, so "billing" wins. The billing agent's system prompt explicitly mentions: "If the user has access issues, acknowledge them and provide the billing resolution."

2. **Multi-intent routing** (enhancement): Parse the LLM output as a ranked list: `{"intents": ["billing", "technical"], "primary": "billing"}`. Route to billing_agent but also fetch from tech_kb for the response.

3. **Confidence floor**: If both billing and technical KBs return similarly low scores, the system escalates to human — the safest fallback for ambiguous cases.

4. **Follow-up routing**: After billing_agent answers the dispute, the user can ask "and how do I regain access?" — this gets re-classified as `technical` in the next turn, routing to tech_agent naturally.

The current implementation chooses option 1 + 3 as the simplest correct behavior.

---

### Q12. What prevents the orchestrator from becoming a bottleneck in a high-traffic system?

**A:** The orchestrator (intent_classifier + router) is the only mandatory sequential step before specialist dispatch. To prevent it from being a bottleneck:

1. **Groq's low latency (~200ms)**: The LLM classification call is fast enough that it rarely delays specialist execution measurably.

2. **Stateless design**: The orchestrator nodes are pure functions with no shared mutable state — they can run on multiple workers simultaneously with no synchronization needed.

3. **Async FastAPI**: Each request runs in its own async task. `await graph.astream()` (LangGraph async API) enables concurrency without thread blocking.

4. **Caching**: Identical or highly similar messages (e.g., "I need a refund" — a common query) could be classified from a cache rather than calling the LLM. LangChain's `set_llm_cache()` with Redis provides this transparently.

5. **Horizontal scaling**: Run multiple FastAPI instances behind a load balancer. Since each ticket is independent (different thread_id), there is no shared state between requests.

6. **Lightweight fallback**: If the LLM is slow, the classifier falls back to a keyword-based heuristic (e.g., "refund/invoice/charge" → billing) in under 1ms.

---

### Q13. How would you A/B test different routing strategies?

**A:** Three-layer A/B testing strategy:

**Layer 1 — Routing algorithm comparison**:
Deploy two graph variants: one using the current LLM-based classifier, one using a fine-tuned BERT classifier. Route 10% of traffic to BERT. Compare: classification accuracy (requires labeled test set), escalation rate, session resolution rate.

**Layer 2 — Specialist agent comparison**:
For the billing agent, test two system prompts. Use `random.choice()` in the `billing_agent` node based on the session_id hash (ensures same user always gets the same variant). Metric: user satisfaction score, CSAT (post-ticket survey).

**Layer 3 — Threshold tuning**:
Test `CONFIDENCE_THRESHOLD = 0.5` vs `0.6` vs `0.7`. Track: escalation rate vs first-contact resolution rate. The optimal threshold minimizes the product of (wrong answers given × human agent cost).

**Infrastructure**:
- Log every ticket's variant assignment, intent, agent, confidence, and resolved status to a data warehouse (BigQuery, Snowflake).
- Use a feature flag service (LaunchDarkly, Flagsmith) to control variant assignment without code deploys.

---

### Q14. How does LangGraph's interrupt_before mechanism work for HITL?

**A:** LangGraph compiles the graph with `interrupt_before=["escalation_handler"]`. Under the hood:

1. When the graph is about to execute `escalation_handler`, it saves the full `TicketState` to the `MemorySaver` checkpoint under the current `thread_id`.
2. Execution stops. The `graph.stream()` generator returns without completing.
3. Calling code detects the interrupt (the graph did not reach `END`) and surfaces the `ticket_id` to the API caller.
4. The API returns a response with `escalated=True` and `ticket_id` to the frontend.
5. A human agent reviews, then calls `POST /escalation/resolve/{ticket_id}` with their notes.
6. The API calls `graph.update_state(config, {"human_agent_notes": notes})` to inject notes into the checkpoint.
7. `graph.stream(None, config)` resumes execution from the last checkpoint — the graph runs `hitl_resume` next (because `escalation_handler` was the interrupt point, the state is now updated and the graph continues to the next node).

This is analogous to `await` in async programming: execution pauses at a well-defined point and resumes with new information.

---

### Q15. How would you evaluate the quality of agent responses at scale?

**A:** A three-tier evaluation approach:

**Tier 1 — Automated metrics (real-time)**:
- **Confidence score distribution**: Track p50/p95 confidence. A sudden drop in median confidence indicates KB drift (new product features not yet in the KB).
- **Escalation rate per agent**: A spike in billing_agent escalation rate suggests a new pricing change is not documented.
- **Resolution rate**: Ticket closed without follow-up = resolved.

**Tier 2 — LLM-as-Judge (batch, daily)**:
Use a separate LLM (GPT-4o) to evaluate response quality on a sample of tickets:
```
Given: user_message, kb_results, agent_response
Rate 1-5: accuracy, helpfulness, tone, KB-groundedness
Flag hallucinations: response claims KB content not present in kb_results
```

**Tier 3 — Human evaluation (weekly)**:
Randomly sample 50 tickets/week for human agent review. Annotate: correct/incorrect/partially correct. Use these annotations to calibrate the LLM judge and update the KB.

**Closing the loop**: KB gaps identified by low confidence or human flagging are automatically suggested as new KB articles (using the ticket message as a draft).

---

## Scenario-Based Questions

### Q16. "The billing agent keeps misclassifying technical questions about billing APIs." How do you fix this?

**A:** This is a domain overlap problem. When a user asks "my API returns 402 on billing endpoint," both billing (billing) and technical (API) are plausible intents.

**Step 1 — Diagnose**: Pull misclassified tickets from logs. Identify common patterns in the messages that were misrouted.

**Step 2 — Classifier improvements**:
- Add explicit examples to the intent classifier prompt:
  ```
  - "I get a 402 error from your payment API" → technical (API error about billing)
  - "I was charged incorrectly" → billing (billing policy question)
  ```
- Consider a two-stage classifier: first classify as technical vs non-technical, then as billing vs general.

**Step 3 — Agent fallback**:
- Add tech_kb lookup to the billing_agent for responses. If the user question mentions HTTP codes or API endpoints, the billing agent can still provide a useful technical answer.

**Step 4 — Cross-agent KB**:
- Create a `billing_api_kb.md` document covering billing-related API errors (402, 403, subscription checks) and add it to BOTH billing_kb and tech_kb.

**Step 5 — Measure**: Re-run the labeled test set after changes. Target: < 5% misclassification rate on billing-API crossover questions.

---

### Q17. "The system is handling 10,000 tickets/hour and latency is climbing above 5 seconds. How do you scale?"

**A:** Systematic scaling analysis:

**Identify the bottleneck first** (add timing logs per node):
- Is it the LLM call? (Groq P99 latency)
- Is it the TF-IDF search? (should be < 5ms for our corpus size)
- Is it the FastAPI server? (thread pool exhaustion)

**Scaling solutions by layer**:

1. **LLM (most likely bottleneck at 10k/hr)**:
   - Enable Groq's batch API for non-real-time tickets (email channel).
   - Add LLM response caching: LangChain's `set_llm_cache(RedisCache())` caches identical prompts.
   - Use a lightweight classifier (fine-tuned BERT, 50ms) for simple intents; LLM only for ambiguous cases.

2. **FastAPI (second likely bottleneck)**:
   - Switch to async graph execution: `await graph.ainvoke()`.
   - Horizontal scaling: 10 FastAPI instances behind a load balancer (Nginx/HAProxy).
   - Use uvicorn workers: `uvicorn api.routes:app --workers 8`.

3. **Session Memory (third)**:
   - Replace in-memory dict with Redis cluster. Redis handles 100k+ ops/sec.
   - Use Redis Streams for asynchronous ticket processing (decouple ingestion from processing).

4. **Queue-based architecture** (for sustained 10k/hr):
   - `POST /ticket` enqueues to a Celery/RQ worker queue, returns a `ticket_id` immediately.
   - Workers process tickets asynchronously.
   - Client polls `GET /ticket/{ticket_id}` or receives a webhook when done.

**Target**: < 1 second end-to-end (excluding LLM) at 10k/hr with 8 workers + Redis.

---

### Q18. "A customer is extremely angry and threatening legal action. How does the system handle this?"

**A:** The intent classifier is trained to detect this pattern with the `escalate` intent:

```
- escalate: expressions of extreme frustration, legal threats, abuse, or requests for a manager
```

**Flow**:
1. Message like "This is outrageous! I'm calling my lawyer if this isn't fixed NOW!" → `intent=escalate`.
2. `router` maps escalate → `escalation_handler` (bypassing all specialists).
3. `escalation_handler` calls `escalate_to_human` with `priority="urgent"`.
4. The user receives: "I understand how frustrating this situation must be. Your case has been immediately escalated to a senior specialist who will contact you within 15 minutes."
5. The human agent receives a high-priority alert.

**Additional safeguards**:
- Even if the classifier misses the legal threat and routes to billing_agent, the low-confidence path can still catch it if the KB has no relevant content.
- The `escalation_handler` generates an empathetic, non-defensive response (important for de-escalation).
- The ticket is marked `priority=urgent` so it jumps to the front of the human agent queue.

---

### Q19. "How would you add a new specialist agent (e.g., LegalAgent) to this system?"

**A:** The hub-and-spoke architecture makes this a clean, 5-step process:

1. **Create KB**: Add `data/knowledge_base/legal_kb.md` with legal policy, ToS, compliance content.

2. **Add KB instance** in `agent/memory.py`:
   ```python
   legal_kb = KnowledgeBaseMemory(domain="legal", kb_dir=_KB_DIR)
   ```

3. **Add tool** in `agent/tools.py`:
   ```python
   @tool
   def lookup_legal_kb(query: str) -> List[Dict]:
       return legal_kb.search(query, top_k=3)
   ```

4. **Add node** in `agent/nodes.py`:
   ```python
   def legal_agent(state): return _run_specialist(state, lookup_legal_kb, "LegalAgent", ...)
   ```

5. **Register in graph** `agent/graph.py`:
   ```python
   workflow.add_node("legal_agent", legal_agent)
   workflow.add_edge("legal_agent", "confidence_check")
   # Update route_by_intent to map "legal" → "legal_agent"
   ```

6. **Update intent classifier prompt** to include "legal" as a valid intent.

No existing nodes change. This is the core benefit of hub-and-spoke.

---

### Q20. "How do you ensure the system is secure — that one customer can't see another's ticket data?"

**A:** Multi-layer security approach:

1. **Session isolation**: `SessionMemory` and the ticket store are keyed by `session_id` and `ticket_id`. No endpoint returns data without requiring the correct ID.

2. **Authentication** (production requirement):
   - Add JWT/OAuth2 authentication to FastAPI using `fastapi-users` or Auth0.
   - Every endpoint validates that the authenticated `user_id` matches the ticket's `user_id`.
   - `GET /ticket/{ticket_id}` returns 403 if the requester's user_id != ticket's user_id.

3. **Input validation**: Pydantic models validate all inputs (no SQL injection in a dict-based store; parameterize if using a DB).

4. **Data minimization**: Conversation history is not returned in `POST /ticket` responses — only in `GET /session/{session_id}/history` (which requires auth).

5. **Audit logging**: Every data access is logged with `user_id`, `ticket_id`, timestamp, and action. Unusual access patterns (e.g., one user fetching many ticket IDs) trigger alerts.

6. **KB isolation**: Domain KBs contain only non-sensitive, company-wide knowledge. Customer-specific data is never written to the KB.

7. **LLM data privacy**: Groq processes prompts but we do not include PII in prompts when avoidable. Ticket messages are pseudonymized in logs (replace names/emails with tokens before logging to a data warehouse).
