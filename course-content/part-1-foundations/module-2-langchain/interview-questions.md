# Module 2: LangChain Framework — Interview Questions

## Table of Contents
- [Beginner Questions (1-10)](#beginner-questions)
- [Intermediate Questions (11-20)](#intermediate-questions)
- [Advanced Questions (21-28)](#advanced-questions)

---

## Beginner Questions

### Q1: What is LangChain and why is it useful?

**Answer:** LangChain is an open-source framework designed to simplify the development of applications powered by Large Language Models (LLMs). It provides abstractions for common LLM operations including prompt management, chain orchestration, memory handling, and agent creation. It is useful because it reduces boilerplate code, enables modular composition of LLM workflows, and integrates with multiple model providers and external tools.

---

### Q2: What are the core components of LangChain?

**Answer:** The core components of LangChain are:

| Component | Purpose |
|-----------|---------|
| **Models** | Wrappers for LLMs (chat and text completion) |
| **Prompts** | Templates for structuring model inputs |
| **Output Parsers** | Extract structured data from model outputs |
| **Indexes** | Document loading, splitting, and retrieval |
| **Chains** | Sequences of operations |
| **Memory** | Conversation state management |
| **Agents** | LLM-driven decision-making with tools |
| **Callbacks** | Event hooks for monitoring and logging |

---

### Q3: What is the difference between an LLM and a Chat Model in LangChain?

**Answer:**

| Aspect | LLM | Chat Model |
|--------|-----|------------|
| Input | Plain text string | List of messages (System, Human, AI) |
| Output | Text string | ChatMessage object |
| Interface | `invoke("text")` | `invoke([messages])` |
| Use Case | Text completion | Conversational AI |

Example:
```python
# LLM (text completion)
from langchain_openai import OpenAI
llm = OpenAI(model="text-davinci-003")
response = llm.invoke("What is Python?")

# Chat Model
from langchain_openai import ChatOpenAI
chat_model = ChatOpenAI(model="gpt-4o-mini")
response = chat_model.invoke([HumanMessage(content="What is Python?")])
```

---

### Q4: What is a Prompt Template?

**Answer:** A Prompt Template is a parameterized way to construct prompts for LLMs. It allows you to define a prompt structure with placeholders that get filled with dynamic values at runtime.

```python
from langchain_core.prompts import PromptTemplate

prompt = PromptTemplate(
    template="Translate the following text to {language}: {text}",
    input_variables=["language", "text"],
)

formatted = prompt.format(language="French", text="Hello")
# Output: "Translate the following text to French: Hello"
```

---

### Q5: What is LCEL (LangChain Expression Language)?

**Answer:** LCEL is LangChain's declarative composition syntax using the pipe (`|`) operator. It enables chaining components together with built-in support for streaming, async execution, parallel execution, and fallbacks.

```python
chain = prompt | model | parser
result = chain.invoke({"topic": "AI"})
```

Key benefits:
- **Streaming**: Real-time token output
- **Async support**: `ainvoke()`, `astream()`
- **Parallel execution**: `RunnableParallel`
- **Fallbacks**: `.with_fallbacks()`
- **Retries**: `.with_retry()`

---

### Q6: What is a Chain in LangChain?

**Answer:** A Chain is a sequence of operations that process input and produce output. It combines components like prompts, models, and parsers into a reusable pipeline.

```python
# Using LCEL (modern approach)
chain = (
    ChatPromptTemplate.from_template("Explain {topic} simply.")
    | ChatOpenAI(model="gpt-4o-mini")
    | StrOutputParser()
)
result = chain.invoke({"topic": "machine learning"})
```

---

### Q7: What are Output Parsers and why are they needed?

**Answer:** Output Parsers transform raw LLM responses into structured formats. They are needed because LLMs return unstructured text, but applications often require structured data (JSON, lists, Pydantic objects).

Common parsers:
- `StrOutputParser`: Returns plain text
- `JsonOutputParser`: Returns parsed JSON
- `PydanticOutputParser`: Returns Pydantic model instances
- `ListOutputParser`: Returns comma-separated lists

---

### Q8: What is Memory in LangChain?

**Answer:** Memory enables LLM applications to retain context across multiple interactions. Without memory, each request is independent and the model has no awareness of previous conversations.

```python
from langchain.memory import ConversationBufferMemory

memory = ConversationBufferMemory(return_messages=True)
memory.save_context({"input": "Hi"}, {"output": "Hello!"})
history = memory.load_memory_variables({})
```

---

### Q9: What is the difference between `ConversationBufferMemory` and `ConversationBufferWindowMemory`?

**Answer:**

| Feature | ConversationBufferMemory | ConversationBufferWindowMemory |
|---------|-------------------------|-------------------------------|
| Storage | Stores entire conversation | Stores last N exchanges |
| Token Usage | Grows indefinitely | Bounded by window size |
| Use Case | Short conversations | Long-running conversations |
| Parameter | None | `k` (number of exchanges) |

---

### Q10: What is a Tool in LangChain?

**Answer:** A Tool is a function that an agent can invoke to perform actions beyond text generation. Tools enable agents to interact with external systems, APIs, databases, and perform computations.

```python
from langchain.tools import tool

@tool
def calculator(expression: str) -> str:
    """Evaluate a mathematical expression."""
    return str(eval(expression))
```

---

## Intermediate Questions

### Q11: Explain the difference between `LLMChain`, `SimpleSequentialChain`, and `SequentialChain`.

**Answer:**

| Chain Type | Description | Input/Output |
|------------|-------------|--------------|
| **LLMChain** | Single prompt + model | One input, one output |
| **SimpleSequentialChain** | Multiple chains in sequence, single input/output | One input, one output |
| **SequentialChain** | Multiple chains with multiple inputs/outputs | Multiple inputs, multiple outputs |

Example of `SequentialChain`:
```python
from langchain.chains import SequentialChain

# Chain 1: Generate outline
outline_chain = LLMChain(llm=llm, prompt=outline_prompt, output_key="outline")

# Chain 2: Write essay from outline
essay_chain = LLMChain(llm=llm, prompt=essay_prompt, output_key="essay")

# Combine
seq_chain = SequentialChain(
    chains=[outline_chain, essay_chain],
    input_variables=["topic"],
    output_variables=["outline", "essay"],
)
result = seq_chain.invoke({"topic": "AI ethics"})
```

---

### Q12: How does `ConversationSummaryMemory` work?

**Answer:** `ConversationSummaryMemory` uses an LLM to generate a running summary of the conversation instead of storing raw messages. This reduces token consumption while preserving context.

```python
from langchain.memory import ConversationSummaryMemory

memory = ConversationSummaryMemory(
    llm=ChatOpenAI(model="gpt-4o-mini"),
    return_messages=True,
)
```

How it works:
1. After each exchange, the memory calls the LLM to update the summary
2. The summary is passed to the model instead of raw conversation history
3. This keeps token usage bounded even for long conversations

---

### Q13: What is `ConversationSummaryBufferMemory` and when should you use it?

**Answer:** `ConversationSummaryBufferMemory` combines the benefits of buffer memory and summary memory. It keeps the most recent N tokens as raw messages and summarizes older messages.

```python
from langchain.memory import ConversationSummaryBufferMemory

memory = ConversationSummaryBufferMemory(
    llm=ChatOpenAI(model="gpt-4o-mini"),
    max_token_limit=1000,  # Summarize when exceeding this limit
    return_messages=True,
)
```

Use when:
- You need recent context in full detail
- Older context can be summarized
- You want to balance token usage with context quality

---

### Q14: How do you create a custom tool in LangChain?

**Answer:** There are two ways to create custom tools:

**Method 1: Using the `@tool` decorator**
```python
from langchain.tools import tool

@tool
def search_database(query: str) -> str:
    """Search the internal database for information."""
    results = database.search(query)
    return format_results(results)
```

**Method 2: Inheriting from `BaseTool`**
```python
from langchain.tools import BaseTool

class CustomSearchTool(BaseTool):
    name: str = "database_search"
    description: str = "Search the internal database"

    def _run(self, query: str) -> str:
        results = database.search(query)
        return format_results(results)

    async def _arun(self, query: str) -> str:
        return await database.asearch(query)
```

---

### Q15: What is an Agent Executor and how does it work?

**Answer:** `AgentExecutor` is the runtime that runs an agent. It handles the loop of:
1. Passing input to the agent
2. Agent decides which tool to use
3. Executing the tool
4. Feeding the result back to the agent
5. Repeating until the agent produces a final answer

```python
from langchain.agents import AgentExecutor, create_tool_calling_agent

agent = create_tool_calling_agent(llm, tools, prompt)
executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
    max_iterations=5,  # Prevent infinite loops
    handle_parsing_errors=True,
)
result = executor.invoke({"input": "What is 25 * 48?"})
```

---

### Q16: What is `VectorStoreRetrieverMemory`?

**Answer:** `VectorStoreRetrieverMemory` stores conversation history in a vector store and retrieves relevant past exchanges using semantic similarity. This enables long-term memory with context-aware retrieval.

```python
from langchain.memory import VectorStoreRetrieverMemory
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings

embeddings = OpenAIEmbeddings()
vectorstore = FAISS.from_texts([], embedding=embeddings)
retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

memory = VectorStoreRetrieverMemory(retriever=retriever)
memory.save_context(
    {"input": "What is the capital of France?"},
    {"output": "Paris"},
)
```

---

### Q17: How do you handle structured output with LangChain?

**Answer:** Use `with_structured_output()` or output parsers with Pydantic models:

```python
from pydantic import BaseModel, Field

class Person(BaseModel):
    name: str = Field(description="Full name")
    age: int = Field(description="Age in years")

# Method 1: with_structured_output (simplest)
llm = ChatOpenAI(model="gpt-4o-mini")
structured_llm = llm.with_structured_output(Person)
result = structured_llm.invoke("John is 30 years old.")

# Method 2: JsonOutputParser with Pydantic
from langchain_core.output_parsers import JsonOutputParser
parser = JsonOutputParser(pydantic_object=Person)
chain = prompt | llm | parser
```

---

### Q18: What are Callbacks in LangChain and how do you use them?

**Answer:** Callbacks are hooks that fire during chain/agent execution for monitoring, logging, or custom behavior.

```python
from langchain_core.callbacks import BaseCallbackHandler

class MyCallbackHandler(BaseCallbackHandler):
    def on_llm_start(self, serialized, prompts, **kwargs):
        print(f"LLM starting with prompt: {prompts[0][:50]}...")

    def on_llm_end(self, response, **kwargs):
        print(f"LLM finished. Tokens: {response.llm_output.get('token_usage', {})}")

    def on_chain_start(self, serialized, inputs, **kwargs):
        print(f"Chain starting with inputs: {inputs}")

chain = prompt | model | parser
result = chain.invoke(
    {"topic": "AI"},
    config={"callbacks": [MyCallbackHandler()]}
)
```

---

### Q19: How do you implement caching in LangChain?

**Answer:** LangChain supports caching to avoid redundant API calls for identical prompts:

```python
from langchain.globals import set_llm_cache
from langchain_community.cache import InMemoryCache, SQLiteCache

# In-memory cache (fast, lost on restart)
set_llm_cache(InMemoryCache())

# SQLite cache (persistent across restarts)
set_llm_cache(SQLiteCache(database_path="langchain_cache.db"))

# GPTCache for semantic similarity caching
from langchain_community.cache import GPTCache
set_llm_cache(GPTCache("./gptcache_data"))
```

---

### Q20: What is `RunnableParallel` and when should you use it?

**Answer:** `RunnableParallel` executes multiple runnables concurrently and combines their results. Use it when you need to run independent operations in parallel.

```python
from langchain_core.runnables import RunnableParallel

parallel_chain = RunnableParallel({
    "summary": summary_chain,
    "keywords": keyword_chain,
    "sentiment": sentiment_chain,
    "entities": entity_chain,
})

result = parallel_chain.invoke({"text": "Your input text"})
# Returns: {"summary": "...", "keywords": [...], "sentiment": "...", "entities": [...]}
```

---

## Advanced Questions

### Q21: Explain the ReAct pattern and how LangChain implements it.

**Answer:** ReAct (Reasoning + Acting) is an agent pattern where the LLM alternates between reasoning about what to do and taking actions using tools.

The loop:
1. **Thought**: LLM reasons about the current state
2. **Action**: LLM selects a tool to invoke
3. **Observation**: Tool returns a result
4. Repeat until **Final Answer** is reached

```python
from langchain.agents import create_react_agent

prompt = ChatPromptTemplate.from_template("""Answer the following questions as best you can.

You have access to the following tools: {tools}

Use the following format:
Question: the input question
Thought: your reasoning
Action: tool name
Action Input: tool input
Observation: tool result
... (repeat Thought/Action/Observation)
Thought: I now know the final answer
Final Answer: the final answer

Question: {input}
Thought: {agent_scratchpad}
""")

agent = create_react_agent(llm, tools, prompt)
```

---

### Q22: How do you implement fallbacks and retries in LangChain chains?

**Answer:**

```python
from tenacity import retry, stop_after_attempt, wait_exponential

# Fallbacks: Try alternative chains if primary fails
primary_chain = prompt | ChatOpenAI(model="gpt-4o") | parser
fallback_chain = prompt | ChatOpenAI(model="gpt-4o-mini") | parser

robust_chain = primary_chain.with_fallbacks([fallback_chain])

# Retries: Retry the same chain on failure
retry_chain = primary_chain.with_retry(
    retry_if_exception_type=(RateLimitError, APIError),
    wait_exponential_jitter=True,
    stop_after_attempt=3,
)

# Combined
robust_retry_chain = primary_chain.with_fallbacks([fallback_chain]).with_retry(
    stop_after_attempt=3
)
```

---

### Q23: How do you handle streaming responses in LangChain?

**Answer:**

```python
# Synchronous streaming
chain = prompt | ChatOpenAI(model="gpt-4o-mini", streaming=True) | StrOutputParser()

for chunk in chain.stream({"topic": "AI"}):
    print(chunk, end="", flush=True)

# Async streaming
async for chunk in chain.astream({"topic": "AI"}):
    print(chunk, end="", flush=True)

# With callbacks for events
from langchain_core.callbacks import StreamingStdOutCallbackHandler

chain = prompt | model | parser
chain.invoke(
    {"topic": "AI"},
    config={"callbacks": [StreamingStdOutCallbackHandler()]}
)
```

---

### Q24: Explain how to build a multi-agent system with LangChain.

**Answer:** LangGraph (part of the LangChain ecosystem) enables multi-agent orchestration:

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict

class AgentState(TypedDict):
    messages: list
    current_agent: str

# Define agent nodes
def researcher_node(state):
    # Research agent logic
    return {"messages": [...]}

def writer_node(state):
    # Writer agent logic
    return {"messages": [...]}

def reviewer_node(state):
    # Reviewer agent logic
    return {"messages": [...]}

# Build graph
graph = StateGraph(AgentState)
graph.add_node("researcher", researcher_node)
graph.add_node("writer", writer_node)
graph.add_node("reviewer", reviewer_node)

graph.add_edge("researcher", "writer")
graph.add_edge("writer", "reviewer")
graph.add_edge("reviewer", END)

graph.set_entry_point("researcher")
app = graph.compile()
```

---

### Q25: How do you optimize token usage in LangChain applications?

**Answer:**

1. **Use appropriate memory types:**
   - `ConversationSummaryMemory` for long conversations
   - `ConversationBufferWindowMemory` with limited `k`

2. **Efficient document chunking:**
   ```python
   splitter = RecursiveCharacterTextSplitter(
       chunk_size=500,
       chunk_overlap=50,
   )
   ```

3. **Prompt optimization:**
   - Remove redundant instructions
   - Use concise system prompts
   - Avoid unnecessary few-shot examples

4. **Model selection:**
   - Use smaller models for simpler tasks
   - Use `gpt-4o-mini` instead of `gpt-4o` when possible

5. **Caching:**
   ```python
   set_llm_cache(SQLiteCache(database_path="cache.db"))
   ```

6. **Response length control:**
   ```python
   llm = ChatOpenAI(model="gpt-4o-mini", max_tokens=200)
   ```

---

### Q26: What is the difference between `create_tool_calling_agent` and `create_react_agent`?

**Answer:**

| Feature | `create_tool_calling_agent` | `create_react_agent` |
|---------|----------------------------|---------------------|
| Mechanism | Uses native function calling | Uses ReAct prompt pattern |
| LLM Support | Requires tool-calling capable LLMs | Works with any LLM |
| Reliability | More reliable, structured | More flexible, prompt-dependent |
| Performance | Faster (native support) | Slower (text parsing) |
| Best For | Modern LLMs (GPT-4, Claude 3) | Legacy or open-source LLMs |

---

### Q27: How do you implement error handling and graceful degradation in LangChain?

**Answer:**

```python
from langchain_core.runnables import RunnableLambda
from langchain_core.exceptions import OutputParserException

# Custom error handler
def safe_invoke(chain, inputs, fallback_value="I couldn't process that request."):
    try:
        return chain.invoke(inputs)
    except OutputParserException as e:
        print(f"Parse error: {e}")
        return fallback_value
    except Exception as e:
        print(f"Unexpected error: {e}")
        return fallback_value

# Using with_fallbacks for graceful degradation
primary = prompt | ChatOpenAI(model="gpt-4o") | parser
fallback = prompt | ChatOpenAI(model="gpt-3.5-turbo") | parser
final_fallback = RunnableLambda(lambda x: "Service temporarily unavailable.")

robust_chain = primary.with_fallbacks([fallback, final_fallback])
```

---

### Q28: How would you design a production-ready LangChain application?

**Answer:** A production-ready LangChain application should include:

1. **Environment management:**
   ```python
   import os
   from dotenv import load_dotenv
   load_dotenv()
   ```

2. **Configuration management:**
   ```python
   from pydantic_settings import BaseSettings

   class Settings(BaseSettings):
       openai_api_key: str
       model_name: str = "gpt-4o-mini"
       max_tokens: int = 500
       temperature: float = 0.7
   ```

3. **Error handling and retries:**
   ```python
   from tenacity import retry, stop_after_attempt, wait_exponential

   @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
   def call_chain(inputs):
       return chain.invoke(inputs)
   ```

4. **Monitoring and logging:**
   ```python
   from langchain_core.callbacks import BaseCallbackHandler

   class MonitoringCallback(BaseCallbackHandler):
       def on_llm_end(self, response, **kwargs):
           log_token_usage(response.llm_output)
   ```

5. **Security:**
   - Input validation and sanitization
   - Rate limiting
   - API key management
   - Prompt injection protection

6. **Testing:**
   - Unit tests for individual components
   - Integration tests for chains
   - Mock LLM responses for deterministic testing

7. **Deployment:**
   - Containerization (Docker)
   - CI/CD pipelines
   - Health checks and monitoring
   - Scalable infrastructure

---

## Quick Reference Table

| Topic | Key Classes/Functions |
|-------|----------------------|
| Prompt Templates | `PromptTemplate`, `ChatPromptTemplate`, `FewShotPromptTemplate` |
| Output Parsers | `StrOutputParser`, `JsonOutputParser`, `PydanticOutputParser` |
| Memory | `ConversationBufferMemory`, `ConversationSummaryMemory`, `VectorStoreRetrieverMemory` |
| Chains | LCEL (`\|`), `RunnableParallel`, `RunnablePassthrough` |
| Tools | `@tool` decorator, `BaseTool` class |
| Agents | `create_tool_calling_agent`, `create_react_agent`, `AgentExecutor` |
| Caching | `InMemoryCache`, `SQLiteCache`, `set_llm_cache()` |
| Callbacks | `BaseCallbackHandler`, `StreamingStdOutCallbackHandler` |
| Error Handling | `.with_fallbacks()`, `.with_retry()` |
