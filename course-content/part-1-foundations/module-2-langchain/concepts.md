# Module 2: LangChain Framework — Concepts

## Table of Contents
- [2.1 LangChain Overview and Architecture](#21-langchain-overview-and-architecture)
- [2.2 Building Blocks: Chains, Prompts, Parsers](#22-building-blocks-chains-prompts-parsers)
- [2.3 Chat Models and Chains](#23-chat-models-and-chains)
- [2.4 Memory, Tools, and Agents](#24-memory-tools-and-agents)
- [2.5 Patterns and Best Practices](#25-patterns-and-best-practices)
- [2.6 Mini-Projects](#26-mini-projects)

---

## 2.1 LangChain Overview and Architecture

### What is LangChain?

LangChain is an open-source framework for building applications powered by Large Language Models (LLMs). It provides abstractions and components that simplify the integration of LLMs into complex, multi-step workflows.

**Core Philosophy:** Compose LLM capabilities with external data sources, computation, and memory to build context-aware, reasoning applications.

### Architecture Overview

LangChain's architecture is modular and consists of several layers:

```
┌─────────────────────────────────────────────────────────┐
│                    Application Layer                     │
│              (Chatbots, Agents, RAG Systems)             │
├─────────────────────────────────────────────────────────┤
│                    Orchestration Layer                   │
│         (Chains, Agents, Graphs, Workflows)              │
├─────────────────────────────────────────────────────────┤
│                    Integration Layer                     │
│  (Models, Prompts, Memory, Tools, Vector Stores, etc.)  │
├─────────────────────────────────────────────────────────┤
│                    Provider Layer                        │
│    (OpenAI, Anthropic, Google, HuggingFace, etc.)       │
└─────────────────────────────────────────────────────────┘
```

### Key Components

| Component | Description |
|-----------|-------------|
| **Models** | LLM wrappers for chat and text completion models |
| **Prompts** | Templates and management for model inputs |
| **Output Parsers** | Structured extraction from model outputs |
| **Indexes** | Document loaders, splitters, retrievers, vector stores |
| **Chains** | Sequences of calls (linear or branching) |
| **Memory** | Short-term and long-term state management |
| **Agents** | LLMs that make decisions and take actions |
| **Tools** | Functions the agent can invoke |
| **Callbacks** | Hooks for logging, streaming, monitoring |

### Installation

```bash
# Core LangChain
pip install langchain

# OpenAI integration
pip install langchain-openai

# Community integrations (tools, vector stores, etc.)
pip install langchain-community

# Expression Language (LCEL) - built into langchain-core
pip install langchain-core
```

### LangChain Expression Language (LCEL)

LCEL is the modern way to compose chains in LangChain. It provides a declarative syntax with built-in streaming, async support, and parallel execution.

```python
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser

# Define components
prompt = ChatPromptTemplate.from_template("Tell me a joke about {topic}")
model = ChatOpenAI(model="gpt-4o-mini")
parser = StrOutputParser()

# Compose with LCEL using the pipe operator
chain = prompt | model | parser

# Invoke the chain
result = chain.invoke({"topic": "programming"})
print(result)
```

---

## 2.2 Building Blocks: Chains, Prompts, Parsers

### Prompt Templates

Prompt templates parameterize model inputs, enabling reuse and dynamic content injection.

```python
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate

# Simple PromptTemplate (for text completion models)
prompt = PromptTemplate(
    template="Translate the following English text to {language}: {text}",
    input_variables=["language", "text"],
)

# ChatPromptTemplate (for chat models)
chat_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful translator assistant."),
    ("human", "Translate this to {language}: {text}"),
])

# Format the prompt
formatted = chat_prompt.format_messages(language="French", text="Hello, how are you?")
```

#### Few-Shot Prompting

```python
from langchain_core.prompts import FewShotChatMessagePromptTemplate

examples = [
    {"input": "happy", "output": "sad"},
    {"input": "tall", "output": "short"},
    {"input": "fast", "output": "slow"},
]

example_prompt = ChatPromptTemplate.from_messages([
    ("human", "What is the opposite of {input}?"),
    ("ai", "{output}"),
])

few_shot_prompt = FewShotChatMessagePromptTemplate(
    examples=examples,
    example_prompt=example_prompt,
)

final_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are an antonym generator."),
    few_shot_prompt,
    ("human", "What is the opposite of {word}?"),
])
```

### Output Parsers

Output parsers transform raw LLM responses into structured formats.

#### String Output Parser

```python
from langchain_core.output_parsers import StrOutputParser

parser = StrOutputParser()
# Simply strips whitespace from the response
```

#### JSON Output Parser

```python
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

class PersonInfo(BaseModel):
    name: str = Field(description="Person's full name")
    age: int = Field(description="Person's age")
    occupation: str = Field(description="Person's job or profession")

parser = JsonOutputParser(pydantic_object=PersonInfo)

prompt = ChatPromptTemplate.from_messages([
    ("system", "Extract the person's information from the text."),
    ("human", "{text}\n\n{format_instructions}"),
])

prompt = prompt.partial(format_instructions=parser.get_format_instructions())

chain = prompt | ChatOpenAI(model="gpt-4o-mini", temperature=0) | parser

result = chain.invoke({"text": "John Smith is a 32-year-old software engineer."})
print(result)  # {'name': 'John Smith', 'age': 32, 'occupation': 'software engineer'}
```

#### Pydantic Output Parser

```python
from langchain_core.output_parsers import PydanticOutputParser

parser = PydanticOutputParser(pydantic_object=PersonInfo)
# Similar to JsonOutputParser but returns Pydantic model instances
```

#### Enum and List Parsers

```python
from langchain_core.output_parsers import ListOutputParser

list_parser = ListOutputParser()
# Parses comma-separated values into a Python list
```

### Chains

Chains combine multiple components into a single executable pipeline.

#### Legacy LLMChain

```python
from langchain.chains import LLMChain  # Legacy approach

chain = LLMChain(
    llm=ChatOpenAI(model="gpt-4o-mini"),
    prompt=ChatPromptTemplate.from_template("Explain {concept} in simple terms."),
)
result = chain.invoke({"concept": "quantum computing"})
```

#### Modern LCEL Chains

```python
# Simple chain
chain = (
    ChatPromptTemplate.from_template("Explain {concept} in simple terms.")
    | ChatOpenAI(model="gpt-4o-mini")
    | StrOutputParser()
)

# Chain with multiple steps
from langchain_core.runnables import RunnableParallel, RunnablePassthrough

chain = (
    RunnablePassthrough.assign(
        summary=lambda x: "Summarize: " + x["text"],
    )
    | ChatPromptTemplate.from_template("{summary}")
    | ChatOpenAI(model="gpt-4o-mini")
    | StrOutputParser()
)
```

#### Sequential Chains

```python
from langchain.chains import SequentialChain

# First chain: generate outline
outline_chain = (
    ChatPromptTemplate.from_template("Create an outline for an essay about {topic}.")
    | ChatOpenAI(model="gpt-4o-mini")
    | StrOutputParser()
)

# Second chain: write essay from outline
essay_chain = (
    ChatPromptTemplate.from_template("Write an essay based on this outline:\n{outline}")
    | ChatOpenAI(model="gpt-4o-mini")
    | StrOutputParser()
)

# Combine sequentially
full_chain = {"outline": outline_chain} | essay_chain
result = full_chain.invoke({"topic": "artificial intelligence"})
```

---

## 2.3 Chat Models and Chains

### Chat Models vs. LLMs

| Feature | LLM (Text Completion) | Chat Model |
|---------|----------------------|------------|
| Input | Raw text string | List of messages |
| Output | Text string | ChatMessage object |
| Use Case | Simple completions | Conversational AI |
| Examples | `text-davinci-003` | `gpt-4o`, `claude-3`, `gemini-pro` |

### Working with Chat Models

```python
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

# Initialize model
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.7,
    max_tokens=500,
    streaming=True,  # Enable streaming
)

# Invoke with messages
response = llm.invoke([
    SystemMessage(content="You are a helpful math tutor."),
    HumanMessage(content="What is the derivative of x^2?"),
])

print(response.content)
```

### Streaming Responses

```python
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4o-mini", streaming=True)

for chunk in llm.stream("Tell me a story in 3 sentences."):
    print(chunk.content, end="", flush=True)
```

### Async Invocation

```python
import asyncio
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4o-mini")

async def generate_responses():
    results = await asyncio.gather(
        llm.ainvoke("What is Python?"),
        llm.ainvoke("What is JavaScript?"),
        llm.ainvoke("What is Rust?"),
    )
    for r in results:
        print(r.content)

asyncio.run(generate_responses())
```

### Model Parameters

```python
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.7,       # Creativity (0 = deterministic, 1 = creative)
    max_tokens=1000,       # Maximum output tokens
    top_p=0.9,             # Nucleus sampling
    frequency_penalty=0.0, # Penalize repeated tokens
    presence_penalty=0.0,  # Penalize repeated topics
    seed=42,               # Reproducible outputs
    timeout=30,            # Request timeout in seconds
    max_retries=2,         # Retry on failure
)
```

### Chat Model Chains with Context

```python
from langchain_core.runnables import RunnableLambda

def format_context(inputs):
    context = inputs.get("context", "No context provided.")
    question = inputs["question"]
    return f"Context: {context}\n\nQuestion: {question}"

qa_chain = (
    RunnableLambda(format_context)
    | ChatPromptTemplate.from_template("Answer based on the context:\n\n{input}")
    | ChatOpenAI(model="gpt-4o-mini")
    | StrOutputParser()
)

result = qa_chain.invoke({
    "context": "Python was created by Guido van Rossum and released in 1991.",
    "question": "Who created Python?",
})
```

### Multi-Model Chains

```python
# Route to different models based on task
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI

openai_llm = ChatOpenAI(model="gpt-4o-mini")
anthropic_llm = ChatAnthropic(model="claude-3-haiku-20240307")
google_llm = ChatGoogleGenerativeAI(model="gemini-pro")

# Use different models for different steps
creative_chain = anthropic_llm  # Good for creative writing
factual_chain = openai_llm      # Good for factual Q&A
code_chain = google_llm         # Good for code generation
```

---

## 2.4 Memory, Tools, and Agents

### Memory Types

Memory enables conversational continuity across multiple interactions.

#### ConversationBufferMemory

Stores the complete conversation history.

```python
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationChain

memory = ConversationBufferMemory(
    return_messages=True,
    memory_key="chat_history",
)

chain = ConversationChain(
    llm=ChatOpenAI(model="gpt-4o-mini", temperature=0.7),
    memory=memory,
    verbose=True,
)

response = chain.invoke({"input": "Hi, my name is John."})
response = chain.invoke({"input": "What was my name again?"})
```

#### ConversationBufferWindowMemory

Stores only the last N exchanges.

```python
from langchain.memory import ConversationBufferWindowMemory

memory = ConversationBufferWindowMemory(
    k=5,  # Keep last 5 exchanges
    return_messages=True,
)
```

#### ConversationSummaryMemory

Maintains a running summary of the conversation.

```python
from langchain.memory import ConversationSummaryMemory

memory = ConversationSummaryMemory(
    llm=ChatOpenAI(model="gpt-4o-mini"),
    return_messages=True,
)
```

#### ConversationSummaryBufferMemory

Combines summarization with a buffer of recent messages.

```python
from langchain.memory import ConversationSummaryBufferMemory

memory = ConversationSummaryBufferMemory(
    llm=ChatOpenAI(model="gpt-4o-mini"),
    max_token_limit=1000,  # Summarize when exceeding this
    return_messages=True,
)
```

#### VectorStore-Retrieved Memory

Retrieves relevant past conversations using semantic search.

```python
from langchain.memory import VectorStoreRetrieverMemory
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings

# Create vector store
embeddings = OpenAIEmbeddings()
vectorstore = FAISS.from_texts([], embedding=embeddings)
retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

memory = VectorStoreRetrieverMemory(retriever=retriever)

# Save to memory
memory.save_context(
    {"input": "What is the capital of France?"},
    {"output": "The capital of France is Paris."},
)

# Retrieve relevant memories
relevant = memory.load_memory_variables({"input": "Tell me about France"})
```

### Tools

Tools are functions that agents can invoke to perform actions.

```python
from langchain.tools import tool
import requests
import math

@tool
def calculator(expression: str) -> str:
    """Evaluate a mathematical expression. Input should be a valid Python expression."""
    try:
        return str(eval(expression))
    except Exception as e:
        return f"Error: {e}"

@tool
def search_weather(city: str) -> str:
    """Get current weather for a given city."""
    # Simulated weather API call
    return f"The weather in {city} is sunny, 25°C"

@tool
def get_current_time() -> str:
    """Get the current date and time."""
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

tools = [calculator, search_weather, get_current_time]
```

### Agents

Agents use LLMs to decide which tools to invoke and in what order.

#### Creating an Agent with LCEL

```python
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.tools import tool

# Define tools
@tool
def multiply(a: int, b: int) -> int:
    """Multiply two numbers."""
    return a * b

@tool
def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b

tools = [multiply, add]

# Create agent
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful math assistant."),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
agent = create_tool_calling_agent(llm, tools, prompt)

# Create executor
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
    handle_parsing_errors=True,
)

result = agent_executor.invoke({"input": "What is 23 multiplied by 45, then add 100?"})
print(result["output"])
```

#### Agent with Memory

```python
from langchain.memory import ConversationBufferMemory

memory = ConversationBufferMemory(
    memory_key="chat_history",
    return_messages=True,
)

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant with memory."),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

agent = create_tool_calling_agent(llm, tools, prompt)

agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    memory=memory,
    verbose=True,
)
```

### Agent Types

| Agent Type | Description | Use Case |
|------------|-------------|----------|
| **Tool Calling Agent** | Uses native function calling | Modern LLMs with tool support |
| **ReAct Agent** | Reasoning + Acting loop | Complex multi-step tasks |
| **Plan-and-Execute Agent** | Plans first, then executes | Tasks requiring strategy |
| **Self-Ask Agent** | Asks follow-up questions | Multi-hop reasoning |

---

## 2.5 Patterns and Best Practices

### 1. Use LCEL Over Legacy Chains

LCEL provides better streaming, async support, and composability.

```python
# Preferred: LCEL
chain = prompt | model | parser

# Avoid: Legacy LLMChain
chain = LLMChain(llm=model, prompt=prompt)
```

### 2. Implement Proper Error Handling

```python
from langchain_core.runnables import RunnableLambda

def safe_parser(response):
    try:
        return response.json()
    except Exception as e:
        return {"error": str(e), "raw": response.content}

chain = prompt | model | RunnableLambda(safe_parser)
```

### 3. Use Fallbacks for Reliability

```python
primary_llm = ChatOpenAI(model="gpt-4o-mini")
fallback_llm = ChatOpenAI(model="gpt-3.5-turbo")

chain_with_fallback = (prompt | primary_llm | parser).with_fallbacks(
    [prompt | fallback_llm | parser]
)
```

### 4. Implement Retries

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def call_llm_with_retry(inputs):
    return chain.invoke(inputs)
```

### 5. Token Optimization

```python
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Chunk documents efficiently
splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50,
    length_function=len,
    separators=["\n\n", "\n", " ", ""]
)

chunks = splitter.split_documents(documents)
```

### 6. Structured Output with Pydantic

```python
from pydantic import BaseModel, Field
from typing import List

class SearchResult(BaseModel):
    title: str = Field(description="Title of the result")
    url: str = Field(description="URL of the result")
    snippet: str = Field(description="Brief description")

class SearchResponse(BaseModel):
    query: str = Field(description="Original search query")
    results: List[SearchResult] = Field(description="List of search results")

structured_llm = ChatOpenAI(model="gpt-4o-mini").with_structured_output(SearchResponse)
```

### 7. Callbacks for Monitoring

```python
from langchain_core.callbacks import BaseCallbackHandler

class TokenCounter(BaseCallbackHandler):
    def __init__(self):
        self.total_tokens = 0

    def on_llm_end(self, response, **kwargs):
        tokens = response.llm_output.get("token_usage", {}).get("total_tokens", 0)
        self.total_tokens += tokens
        print(f"Tokens used: {tokens}, Total: {self.total_tokens}")

chain = prompt | model | parser
result = chain.invoke({"topic": "AI"}, config={"callbacks": [TokenCounter()]})
```

### 8. Parallel Execution

```python
from langchain_core.runnables import RunnableParallel

# Run multiple chains in parallel
parallel_chain = RunnableParallel({
    "summary": summary_chain,
    "keywords": keyword_chain,
    "sentiment": sentiment_chain,
})

result = parallel_chain.invoke({"text": "Your input text here"})
```

### 9. Caching

```python
from langchain.globals import set_llm_cache
from langchain_community.cache import InMemoryCache, SQLiteCache

# In-memory cache (fast, volatile)
set_llm_cache(InMemoryCache())

# SQLite cache (persistent)
set_llm_cache(SQLiteCache(database_path=".langchain.db"))

# Now identical prompts will be cached
result = chain.invoke({"topic": "AI"})
```

### 10. Security Best Practices

```python
import os
from dotenv import load_dotenv

load_dotenv()

# Never hardcode API keys
llm = ChatOpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4o-mini",
)

# Validate inputs before passing to LLM
def sanitize_input(user_input: str) -> str:
    # Remove potentially harmful content
    return user_input.strip()[:5000]  # Limit length
```

---

## 2.6 Mini-Projects

### Project 1: Conversational Chatbot

A chatbot with memory and personality.

```python
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.memory import ConversationBufferMemory
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

# Setup
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)
memory = ConversationBufferMemory(return_messages=True, memory_key="chat_history")

prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a friendly AI assistant named BotAI.
Your personality is helpful, witty, and concise.
Always try to be informative while keeping responses engaging."""),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{input}"),
])

chain = prompt | llm | StrOutputParser()

def chat(user_input: str) -> str:
    # Load history
    history = memory.load_memory_variables({})["chat_history"]

    # Generate response
    response = chain.invoke({
        "input": user_input,
        "chat_history": history,
    })

    # Save to memory
    memory.save_context({"input": user_input}, {"output": response})

    return response

# Interactive loop
print("BotAI: Hello! I'm BotAI. Type 'quit' to exit.")
while True:
    user_input = input("You: ")
    if user_input.lower() in ["quit", "exit", "bye"]:
        print("BotAI: Goodbye!")
        break
    response = chat(user_input)
    print(f"BotAI: {response}")
```

### Project 2: Text Summarizer

Summarize long documents with customizable length.

```python
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_text_splitters import RecursiveCharacterTextSplitter

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

# Map-Reduce pattern for long documents
splitter = RecursiveCharacterTextSplitter(
    chunk_size=2000,
    chunk_overlap=200,
)

def summarize_chunk(chunk: str) -> str:
    prompt = ChatPromptTemplate.from_template(
        "Summarize the following text in 2-3 sentences:\n\n{text}"
    )
    chain = prompt | llm | StrOutputParser()
    return chain.invoke({"text": chunk})

def summarize_document(text: str, summary_length: str = "medium") -> str:
    chunks = splitter.split_text(text)

    # Map: Summarize each chunk
    chunk_summaries = [summarize_chunk(chunk) for chunk in chunks]

    if len(chunk_summaries) == 1:
        return chunk_summaries[0]

    # Reduce: Combine summaries
    combined = "\n\n".join(chunk_summaries)

    length_instructions = {
        "short": "Summarize in 1-2 sentences.",
        "medium": "Summarize in 3-5 sentences.",
        "long": "Summarize in a detailed paragraph.",
    }

    final_prompt = ChatPromptTemplate.from_template(
        f"Combine these summaries into one cohesive summary. {length_instructions.get(summary_length, length_instructions['medium'])}\n\n{{text}}"
    )
    final_chain = final_prompt | llm | StrOutputParser()

    return final_chain.invoke({"text": combined})

# Usage
long_text = """Your long document text here..."""
summary = summarize_document(long_text, summary_length="medium")
print(summary)
```

### Project 3: Document Q&A System

Answer questions based on provided documents.

```python
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableParallel, RunnablePassthrough

# Sample documents
documents = [
    Document(page_content="Python is a high-level programming language created by Guido van Rossum in 1991.", metadata={"source": "python_intro"}),
    Document(page_content="JavaScript was created by Brendan Eich in 1995 and is the most popular web programming language.", metadata={"source": "js_intro"}),
    Document(page_content="Rust is a systems programming language focused on safety and performance, developed by Mozilla.", metadata={"source": "rust_intro"}),
]

# Setup vector store
splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
chunks = splitter.split_documents(documents)

embeddings = OpenAIEmbeddings()
vectorstore = FAISS.from_documents(chunks, embeddings)
retriever = vectorstore.as_retriever(search_kwargs={"k": 2})

# QA Chain
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

prompt = ChatPromptTemplate.from_template("""Answer the question based only on the context provided.

Context:
{context}

Question: {question}

If the answer is not in the context, say "I don't have enough information to answer this question."
""")

def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

qa_chain = (
    RunnableParallel({
        "context": retriever | format_docs,
        "question": RunnablePassthrough(),
    })
    | prompt
    | llm
    | StrOutputParser()
)

# Usage
question = "Who created Python?"
answer = qa_chain.invoke(question)
print(f"Q: {question}")
print(f"A: {answer}")
```

### Project 4: Restaurant Waiter Bot

An agent that takes orders, checks menu, and calculates bills.

```python
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import create_tool_calling_agent, AgentExecutor

# Menu database
MENU = {
    "burger": 8.99,
    "pizza": 12.99,
    "pasta": 10.99,
    "salad": 7.99,
    "soup": 5.99,
    "steak": 18.99,
    "coke": 2.99,
    "water": 1.99,
    "coffee": 3.49,
    "cake": 6.99,
}

@tool
def check_menu(item: str = None) -> str:
    """Check the restaurant menu. Optionally search for a specific item."""
    if item:
        item = item.lower()
        matches = {k: v for k, v in MENU.items() if item in k}
        if matches:
            return "\n".join([f"{k}: ${v:.2f}" for k, v in matches.items()])
        return f"Sorry, we don't have '{item}' on our menu."
    return "\n".join([f"{k}: ${v:.2f}" for k, v in MENU.items()])

@tool
def calculate_bill(items: str) -> str:
    """Calculate the total bill for a list of items. Items should be comma-separated."""
    item_list = [item.strip().lower() for item in items.split(",")]
    total = 0
    receipt = []
    for item in item_list:
        if item in MENU:
            price = MENU[item]
            total += price
            receipt.append(f"{item}: ${price:.2f}")
        else:
            receipt.append(f"{item}: Not found")
    receipt.append(f"\nTotal: ${total:.2f}")
    return "\n".join(receipt)

@tool
def place_order(items: str) -> str:
    """Place an order for items. Items should be comma-separated."""
    item_list = [item.strip().lower() for item in items.split(",")]
    valid_items = [item for item in item_list if item in MENU]
    invalid_items = [item for item in item_list if item not in MENU]

    response = f"Order placed for: {', '.join(valid_items)}"
    if invalid_items:
        response += f"\nNote: These items are not available: {', '.join(invalid_items)}"
    response += "\nYour order will be ready shortly!"
    return response

tools = [check_menu, calculate_bill, place_order]

# Create agent
prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a friendly restaurant waiter bot.
Your job is to:
1. Greet customers and show the menu when asked
2. Take orders and confirm them
3. Calculate bills when requested
Always be polite and professional."""),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)
agent = create_tool_calling_agent(llm, tools, prompt)

agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
    handle_parsing_errors=True,
)

# Usage
print("Waiter Bot: Welcome to our restaurant! How can I help you today?")
while True:
    user_input = input("Customer: ")
    if user_input.lower() in ["quit", "exit", "bye"]:
        print("Waiter Bot: Thank you for dining with us. Goodbye!")
        break
    result = agent_executor.invoke({"input": user_input})
    print(f"Waiter Bot: {result['output']}")
```

### Project 5: Travel Planner Agent

An agent that helps plan trips with multiple tools.

```python
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import create_tool_calling_agent, AgentExecutor
from datetime import datetime, timedelta

# Simulated data
DESTINATIONS = {
    "paris": {"country": "France", "budget": "$$$", "best_season": "Spring/Fall", "attractions": "Eiffel Tower, Louvre, Notre-Dame"},
    "tokyo": {"country": "Japan", "budget": "$$$", "best_season": "Spring (Cherry Blossoms)", "attractions": "Shibuya, Senso-ji, Tokyo Tower"},
    "new york": {"country": "USA", "budget": "$$$$", "best_season": "Year-round", "attractions": "Statue of Liberty, Central Park, Times Square"},
    "bali": {"country": "Indonesia", "budget": "$$", "best_season": "Dry Season (Apr-Oct)", "attractions": "Ubud, Tanah Lot, Rice Terraces"},
    "rome": {"country": "Italy", "budget": "$$$", "best_season": "Spring/Fall", "attractions": "Colosseum, Vatican, Trevi Fountain"},
}

@tool
def get_destination_info(destination: str) -> str:
    """Get information about a travel destination including country, budget, best season, and attractions."""
    dest = destination.lower()
    if dest in DESTINATIONS:
        info = DESTINATIONS[dest]
        return f"""Destination: {destination.title()}
Country: {info['country']}
Budget Level: {info['budget']}
Best Time to Visit: {info['best_season']}
Top Attractions: {info['attractions']}"""
    return f"Sorry, I don't have information about {destination}. Try: Paris, Tokyo, New York, Bali, or Rome."

@tool
def estimate_trip_cost(destination: str, days: int, travelers: int = 1) -> str:
    """Estimate trip cost based on destination, duration, and number of travelers."""
    dest = destination.lower()
    if dest not in DESTINATIONS:
        return f"I don't have pricing for {destination}."

    budget_levels = {"$$": 100, "$$$": 200, "$$$$": 350}
    daily_rate = budget_levels.get(DESTINATIONS[dest]["budget"], 150)

    accommodation = daily_rate * 0.6 * days * travelers
    food = daily_rate * 0.25 * days * travelers
    activities = daily_rate * 0.15 * days * travelers
    total = accommodation + food + activities

    return f"""Estimated Cost for {destination.title()} ({days} days, {travelers} traveler(s)):
Accommodation: ${accommodation:.0f}
Food & Dining: ${food:.0f}
Activities: ${activities:.0f}
Estimated Total: ${total:.0f}
*Excludes flights and travel insurance*"""

@tool
def generate_itinerary(destination: str, days: int) -> str:
    """Generate a day-by-day itinerary suggestion for a destination."""
    dest = destination.lower()
    if dest not in DESTINATIONS:
        return f"I can't generate an itinerary for {destination}."

    attractions = DESTINATIONS[dest]["attractions"].split(", ")
    itinerary = [f"Suggested {days}-Day Itinerary for {destination.title()}:"]

    for day in range(1, days + 1):
        attraction = attractions[(day - 1) % len(attractions)]
        itinerary.append(f"Day {day}: Visit {attraction} and explore the surrounding area.")

    return "\n".join(itinerary)

@tool
def get_travel_tips(destination: str) -> str:
    """Get general travel tips for a destination."""
    tips = {
        "paris": "Learn basic French phrases. Use metro for transport. Visit museums on first Sunday of the month for free entry.",
        "tokyo": "Get a JR Pass for trains. Learn basic Japanese etiquette. Cash is still preferred in many places.",
        "new york": "Get a CityPASS for attractions. Use subway for transport. Walk as much as possible.",
        "bali": "Respect temple dress codes. Use scooter for local transport. Stay hydrated.",
        "rome": "Validate train tickets. Dress modestly for churches. Book Colosseum tickets in advance.",
    }
    return tips.get(destination.lower(), f"Research local customs and always carry travel insurance.")

tools = [get_destination_info, estimate_trip_cost, generate_itinerary, get_travel_tips]

prompt = ChatPromptTemplate.from_messages([
    ("system", """You are an expert travel planner assistant.
Help users plan their trips by providing destination information, cost estimates, itineraries, and travel tips.
Be enthusiastic and helpful. Always ask clarifying questions if needed."""),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.5)
agent = create_tool_calling_agent(llm, tools, prompt)

agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
    handle_parsing_errors=True,
)

print("Travel Planner: Welcome! I'm your travel planning assistant. Where would you like to go?")
while True:
    user_input = input("You: ")
    if user_input.lower() in ["quit", "exit", "bye"]:
        print("Travel Planner: Happy travels! Goodbye!")
        break
    result = agent_executor.invoke({"input": user_input})
    print(f"Travel Planner: {result['output']}")
```

---

## Summary

This module covered the LangChain framework comprehensively:

- **Architecture**: Modular design with models, prompts, chains, memory, tools, and agents
- **Building Blocks**: Prompt templates, output parsers, and chain composition with LCEL
- **Chat Models**: Working with conversational models, streaming, and async execution
- **Memory**: Various memory types for maintaining conversation state
- **Tools & Agents**: Creating tools and building agents that use them intelligently
- **Best Practices**: Error handling, caching, parallelism, security, and token optimization
- **Mini-Projects**: Practical implementations of chatbots, summarizers, Q&A systems, and agents

The next module will build on these foundations to explore more advanced LangChain patterns and real-world applications.
