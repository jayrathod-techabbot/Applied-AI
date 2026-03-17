# Indicative Coverage

---

## Module 1: Generative AI & Prompting

### Sub-Module: Generative AI
**Duration: 1 hr**

- Artificial Intelligence (AI) from a birds-eye view
- Main components of AI – Machine Learning / Deep Learning / Cognitive Computing and Neural Networks / NLP
- Definition and overview of GenAI – how it differs from traditional AI
- Capabilities of Large Language Models
- Overview of their architecture *(Transformers)*
- Other generative models (Vision, Audio, Image)
- Discuss GenAI use cases across various industries

---

### Sub-Module: Prompt Engineering
**Duration: 3 hrs**

- Introduction to Prompt Engineering
- Key elements of an effective prompt (clarity, specificity, tone, instructions)
- Apply prompting techniques
- Enhance prompts using GenAI tools
- Context window: Why and How it matters?
- Evaluate Prompt responses
- Responsible use patterns
- FMA (Failure Mode Analysis)

---

### Sub-Module: Data Analysis with Prompts
**Duration: 3 hrs**

- Data Understanding via Prompts
- Prompt-to-EDA (Python-assisted)
- Prompting for Business Metrics
- Prompting for Insights & Storytelling
- Prompting for SQL Analytics
- Prompting for Forecasting & What-if
- Governance & Guardrails for Analysis

---

### Sub-Module: Considerations and Future Roadmap for GenAI Adoption
**Duration: 1 hr**

- Ethical implications of GenAI
- Risks and other considerations
- Data quality, Hallucinations, Data privacy, Fairness, Transparency, Accountability
- Governance and compliance in GenAI deployment

---

## Module 2: Frameworks and Tooling

### Sub-Module: LangChain
**Duration: 16 hrs**

- Introduction and Overview of LangChain, Crew AI and Pydantic AI Overview
- **Building blocks of LangChain**
  - Chat models, Chains, Memory, Tools, Agents, Parser

**Use LangChain Components**

- Learn core LangChain components like Chat models, Messages, Model I/O, Parsers, Chains, and memory types
- Parse LLM Outputs using Output parsers, Structured Output
- Work with LLMs — Response caching, response streaming, token usage tracking (optimize cost)
- Use Runnable to interact with various components within
- Test & Debug LangChain Workflows
- Understand prompt composition (String prompt and Chat prompt)
- Compose and reuse prompts together: PipelinePrompt
- Apply FewShotPromptTemplate for few shot prompting with Example Selectors
- Learn the art of conversational prompting with ConversationChain
- Augment agent capabilities with tool calling capabilities
- Learn about memory management techniques
- Demo: An Intelligent Agent with Tool Calling capabilities and memory

---

## Module 3: RAG & Vector Databases

### Sub-Module: Vector Database, RAG
**Duration: 24 hrs**

- Overview of RAG
- RAG Architecture
- Core components
- Common use cases
- Embeddings and Semantic search
- Chunking strategies and best practices
- Vector Databases: concept, types (pgvector)
- How to upload data into a vector database
- Query a vector database, generating the answer & concatenating the relevant documents
- Visualizing embedding spaces for similarity validation & debugging
- Postproduction maintenance and Troubleshooting
- **Hands-on:** Build a QA application using a policy document PDF
- Retrieval & Generation Loop
- **Other Retrieval and Filtering Techniques**
  - Top-k & Filtering
  - Metadata Filtering
  - Hybrid Search
- Retrieval Challenges and mitigation techniques

---

### Sub-Module: RAG Evaluation Techniques
**Duration: 12 hrs**

- Retrieval Quality (Intrinsic evaluation)
  - Recall@k, Precision@k, MAP (Mean Average Precision), MRR (Mean Reciprocal Rank) etc.
- End-to-End QA (Extrinsic evaluation)
  - Exact match, F1, ROUGE/BLEU etc.
- LLM-as-a-Judge technique

---

## Module 4: Agentic & Multi-agent Systems

### Sub-Module: Introduction to Agentic AI
**Duration: 2 hrs**

- Overview of Agentic AI systems
- **Foundational Capabilities**
  - Autonomy
  - Reasoning
  - Action
- Difference between a regular prompt and Agentic AI with an example
- Understanding Agentic AI with scenarios
- **Components of Agentic AI**
  - Goals
  - Perception
  - Reasoning
  - Plan
  - Act
  - Feedback
  - Memory
- Examples

---

### Sub-Module: Agentic AI Design Patterns
**Duration: 2 hrs**

- Reactive and Planning Agents
- Planning vs Reactive Agents
- **Reflection**
  - Introduction to Reflection
  - How Agents are implemented using Reflection loop
- **Tools**
  - Introduction to Tools and their uses
  - Designing tools and integrating with Agents
  - Invoking tools
- **Actions**
  - Introduction
  - Types of Actions
- **Memory Patterns**
  - Buffer, Sliding window, Summary memory, Vector memory, Scratchpad, Shared memory
- **Planning-ReAct**
  - What is Planning
  - What is ReAct? (Reasoning + Act)

---

### Sub-Module: Multi-Agent Collaboration
**Duration: 2 hrs**

- Definition of Multi Agents
- How they work
- Postproduction maintenance and Troubleshooting
- **Demo:** Demonstrate a multi-agent reflective planner application that uses all the above techniques

---

### Sub-Module: Agent 2 Agent (A2A)
**Duration: 2 hrs**

- Fundaments of A2A
- A2A Architecture and Design Patterns
- Agent Roles, Contracts and Interfaces
- A2A Messaging
- Orchestration strategies
- Inter-Agent tooling
- Memory and Shared Context in A2A
- External Memory Integration (RAG, Knowledge Systems)
- Parsing, Structured outputs, Validations
- Tracing and Observability
- Hands-on: Building a multi-Agent A2A workflow

---

### Sub-Module: LangGraph Framework
**Duration: 16 hrs**

**Introduction to LangGraph**

- LangGraph intro: What, Why, and Where to use
- Key concepts: Nodes, Edges, State
- Retry logic, Conditional routing, Event-driven flows
- LangChain vs LangGraph
- Full walkthrough of building a LangGraph-based agent

**Hands-on**

- Walkthrough a Python code that shows the LangGraph components (Nodes, Edges)
- As an additional requirement, visualize the graph

**Implementing Agentic Design Patterns in LangGraph**

- Reflection
- Tools
- Planning-ReAct
- Multi-Agent collaboration

**Working with Memory and State**

- Storing and retrieving conversation state
- Using Vector Stores for persistent memory
- Balancing short-term vs. long-term memory
- Implementing contextual persistence between nodes
- **Hands-on:** Stateful Conversational Agent

**Integrating Tools and Human-in-the-Loop (HITL)**

- Registering and using external tools (Search, Math, File APIs)
- Designing interruptible workflows
- Implementing HITL checkpoints
- **Hands-on:** Reflective Research Agent with HITL Interrupt

---

## Module 5: Model Context Protocol (MCP) Techniques

### Sub-Module: MCP
**Duration: 8 hrs**

**Introduction to Model Context Protocol (MCP)**

- Need for a standard interface between LLMs and tools

**Core Components**

- Servers
- Client
- Transport Layer

**Examples of MCP Servers**

- Weather API, UK Carbon Intensity, Databases, Filesystem, Finance API

**Creating an MCP Server:** Carbon Intensity

- Tool definition
- Tool Registration
- Running the server

**Creating the MCP Client**

- Client testing

---

## Module 6: MLOps Foundations for GenAI Systems

### Sub-Module: MLOps in the Context of GenAI & Agents
**Duration: 2 hrs**

- Why GenAI and Agentic systems require MLOps
- MLOps vs DevOps vs traditional SDLC (GenAI lens)
- End-to-end lifecycle for GenAI, RAG, and Agentic systems
- Enterprise MLOps reference architecture: training, inference, orchestration, monitoring layers
- How RAG pipelines, embeddings, prompts, and agent workflows fit into MLOps
- Overview of cloud-native MLOps platforms (AWS, Azure, GCP)

---

## Module 7: Designing MLOps-Ready GenAI Architectures

### Sub-Module: Architecture & Lifecycle Design
**Duration: 2 hrs**

- Identify MLOps touchpoints in RAG and multi-agent systems
- Separation of training vs inference vs orchestration layers
- Batch vs real-time vs agent-driven inference patterns
- Designing embedding refresh and data ingestion workflows
- Mapping agent workflows to deployment and monitoring pipelines
- Creating MLOps-aware architecture and lifecycle diagrams

---

## Module 8: CI/CD & Lifecycle Management for GenAI

### Sub-Module: Versioning & Deployment Strategy
**Duration: 2 hrs**

- What to version in GenAI systems: code, models, prompts, embeddings, agent graphs
- CI/CD differences for software vs ML vs GenAI systems
- Designing promotion flows (Dev → Staging → Prod) for GenAI solutions
- Rollback strategies for faulty prompts, models, and agent behaviors
- Change management for agent logic and retrieval pipelines

---

## Module 9: Monitoring, Drift & Governance for RAG & Agents

### Sub-Module: Observability & Trust
**Duration: 2 hrs**

- Why ML monitoring differs from application monitoring in GenAI systems
- Operational metrics vs AI-specific metrics (retrieval quality, hallucination rate)
- Data drift, embedding drift, and knowledge base staleness in RAG systems
- Monitoring agent behavior, failures, and escalation paths
- Human-in-the-Loop (HITL) checkpoints and governance controls
- A/B testing strategies for prompts and agent workflows

---

## Module 10: AI Governance

### Sub-Module: Why Governance Matters
**Duration: 4 hrs**

**Why Governance Matters**

- Risks in GenAI systems (hallucination, bias, prompt injection, data leakage)
- Enterprise risk: compliance, security, reputation
- Real-world failure examples

**Guardrails**

- Prompt filtering & validation
- Prompt injection detection
- Toxicity & content moderation
- Rate limiting & abuse prevention
- PII redaction & masking
- Structured output validation (schema enforcement)
- Role-based access in RAG
- Metadata filtering & access boundaries

**Responsible AI Principles**

- Fairness & bias mitigation
- Transparency & explainability
- Human-in-the-loop design
- Accountability

**PII & Data Protection**

- Definition of PII & sensitive data
- Data minimization principle
- Encryption & secure storage
- Logging without storing sensitive data

**Monitoring, Audit & Compliance**

- Logging prompts & responses
- Safety evaluation metrics
- Drift detection, Audit trails & incident response
