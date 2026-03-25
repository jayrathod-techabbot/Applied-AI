# INTERVIEW.md — Multi-Agent Researcher

## Q1: What problem does this system solve?

**A:** Standard RAG retrieves once and answers once — there's no mechanism to catch factual errors or verify claims against multiple sources. This system models research the way a human analyst would: one agent collects raw data, a second challenges it and flags contradictions, and a third synthesizes only the verified claims into the final report. The result is more trustworthy than a single-pass RAG chain, especially for queries where accuracy matters more than speed.

---

## Q2: Why CrewAI over LangChain multi-agent or AutoGen?

**A:** CrewAI gave us a clean role-based abstraction — you define agents by their role, goal, and backstory, which shapes their prompting without us hand-crafting every system prompt. The built-in crew-level shared memory (backed by Cosmos DB in our case) meant each agent could read what the previous agent had done without us manually injecting context. With LangChain AgentExecutor, we would have had to manage that state injection ourselves. AutoGen was also a candidate but its conversational back-and-forth model was noisier than CrewAI's sequential task execution for our use case.

---

## Q3: How does the Critic agent actually verify facts?

**A:** The Critic agent receives the Researcher's raw findings and runs each factual claim through two checks: (1) it uses an LLM-as-judge prompt that asks GPT-4o to rate the claim's credibility given the provided sources, and (2) it checks for internal contradictions across the retrieved chunks using embedding similarity — claims that are semantically distant from all retrieved chunks get flagged. Flagged claims trigger a re-search loop where the Researcher is tasked with finding additional corroborating or refuting evidence.

---

## Q4: How did you manage context window limits with long research tasks?

**A:** Each task is bounded — the Researcher is limited to returning top-5 most relevant chunks per query, not the full retrieved set. We also use a summarization step between the Researcher and Critic: long retrieved documents are condensed to key claims before passing to the Critic agent. The crew's shared memory stores summaries, not raw text, so the context stays manageable even across multi-turn research tasks.

---

## Q5: How is this deployed?

**A:** FastAPI app in a Docker container deployed to Azure Container Apps. Cosmos DB handles shared crew memory and report persistence. Azure AI Search is the retrieval backend. We use Managed Identity for all Azure service auth. Azure Monitor captures per-crew-run telemetry: number of agent iterations, token usage, and final confidence metrics.

---

## Q6: What would you improve?

**A:** I'd add a human-in-the-loop checkpoint between the Critic and Writer stages for high-stakes queries — before the Writer generates the final report, a confidence threshold check either auto-approves or routes to a human reviewer. CrewAI's `human_input=True` flag supports this natively, so the implementation is straightforward.

---

## Key Terms to Use

- **Role-based agent delegation** (CrewAI's model vs ReAct loops)
- **Crew-level shared memory** 
- **LLM-as-judge** for fact verification
- **Sequential task execution** with conditional re-research loops
- **Cosmos DB** for persistent agent memory
