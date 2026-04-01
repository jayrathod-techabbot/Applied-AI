# Module 4: Agentic Systems

## Table of Contents
- [4.1 Introduction to Agentic AI](#41-introduction-to-agentic-ai)
- [4.2 Agent Design Patterns](#42-agent-design-patterns)
- [4.3 Multi-Agent Systems and Coordination](#43-multi-agent-systems-and-coordination)
- [4.4 Agent-to-Agent (A2A) Protocol](#44-agent-to-agent-a2a-protocol)
- [4.5 Building Agents with LangGraph](#45-building-agents-with-langgraph)

---

## 4.1 Introduction to Agentic AI

### What Makes an Agent?

An AI agent is a system that can **perceive**, **reason**, **act**, and **learn** to achieve goals autonomously. Unlike traditional LLM applications that simply respond to prompts, agents maintain agency over their actions.

#### Core Components of an AI Agent

| Component | Description | Example |
|-----------|-------------|---------|
| **Perception** | Input processing from environment | Reading user queries, API responses, files |
| **Memory** | Short-term and long-term context | Conversation history, knowledge base |
| **Reasoning** | Decision-making and planning | Chain-of-thought, ReAct, planning algorithms |
| **Action** | Executing operations via tools | API calls, database queries, code execution |
| **Reflection** | Self-evaluation and correction | Output validation, error recovery |

### The Autonomy Spectrum

Agents exist on a spectrum from fully human-controlled to fully autonomous:

```
Level 0: No Autonomy          → Simple LLM completion
Level 1: Assisted             → LLM with human review (copilot)
Level 2: Semi-Autonomous      → Agent proposes, human approves
Level 3: Conditional          → Agent acts within defined boundaries
Level 4: High Autonomy        → Agent acts independently, human oversight
Level 5: Full Autonomy        → Agent operates without human intervention
```

### Agent Architecture

```python
from typing import Any, Callable, List, Optional
from pydantic import BaseModel

class Tool(BaseModel):
    """A tool that an agent can use."""
    name: str
    description: str
    func: Callable[..., Any]

class AgentMemory(BaseModel):
    """Memory system for maintaining context."""
    short_term: List[dict] = []  # Conversation history
    long_term: dict = {}         # Persistent knowledge
    
    def add_message(self, role: str, content: str):
        self.short_term.append({"role": role, "content": content})
    
    def get_context(self, max_messages: int = 10) -> List[dict]:
        return self.short_term[-max_messages:]

class Agent:
    """Base agent class with core capabilities."""
    
    def __init__(self, llm, tools: List[Tool], memory: Optional[AgentMemory] = None):
        self.llm = llm
        self.tools = {tool.name: tool for tool in tools}
        self.memory = memory or AgentMemory()
        self.max_iterations = 10
    
    def perceive(self, input_data: str) -> str:
        """Process input from the environment."""
        self.memory.add_message("user", input_data)
        return input_data
    
    def reason(self, context: str) -> dict:
        """Generate reasoning and action plan."""
        prompt = self._build_prompt(context)
        response = self.llm.invoke(prompt)
        return self._parse_response(response)
    
    def act(self, tool_name: str, tool_input: str) -> Any:
        """Execute a tool and return results."""
        if tool_name not in self.tools:
            raise ValueError(f"Unknown tool: {tool_name}")
        return self.tools[tool_name].func(tool_input)
    
    def reflect(self, result: Any, goal: str) -> bool:
        """Evaluate if the result satisfies the goal."""
        evaluation = self.llm.invoke(
            f"Goal: {goal}\nResult: {result}\n"
            f"Does the result satisfy the goal? Answer YES or NO with explanation."
        )
        return "YES" in evaluation.content.upper()
    
    def run(self, goal: str) -> str:
        """Main agent loop."""
        self.perceive(goal)
        
        for iteration in range(self.max_iterations):
            context = self.memory.get_context()
            decision = self.reason(str(context))
            
            if decision.get("action") == "final_answer":
                self.memory.add_message("assistant", decision["answer"])
                return decision["answer"]
            
            # Execute tool
            observation = self.act(decision["action"], decision["input"])
            self.memory.add_message("system", f"Tool result: {observation}")
            
            # Reflect
            if self.reflect(observation, goal):
                return f"Completed: {observation}"
        
        return "Max iterations reached without completion."
```

### Real-World Use Cases

| Use Case | Autonomy Level | Tools Used |
|----------|---------------|------------|
| Customer Support Bot | Level 3 | CRM, Knowledge Base, Ticketing |
| Code Review Agent | Level 2 | Git, Linter, Static Analyzer |
| Research Assistant | Level 4 | Web Search, PDF Parser, Summarizer |
| Trading Agent | Level 5 | Market Data API, Order Execution |
| DevOps Agent | Level 3 | CI/CD APIs, Cloud SDKs, Monitoring |

---

## 4.2 Agent Design Patterns

### 1. ReAct (Reasoning + Acting)

ReAct interleaves reasoning traces with action executions, enabling agents to think before acting and learn from observations.

```python
def react_agent(llm, tools: dict, query: str, max_steps: int = 10) -> str:
    """
    ReAct Pattern: Reason → Act → Observe → Repeat
    """
    prompt_template = """Answer the following question by thinking step by step.
You have access to these tools: {tools}

Use the following format:
Question: the input question
Thought: your reasoning about what to do
Action: the action to take (one of: {tool_names})
Action Input: the input to the action
Observation: the result of the action
... (repeat Thought/Action/Observation as needed)
Thought: I now know the final answer
Final Answer: the final answer

Question: {query}
{history}"""
    
    history = ""
    
    for step in range(max_steps):
        prompt = prompt_template.format(
            tools="\n".join(f"- {name}: {desc}" for name, desc in tools.items()),
            tool_names=", ".join(tools.keys()),
            query=query,
            history=history
        )
        
        response = llm.invoke(prompt).content
        history += f"\n{response}\n"
        
        # Check for final answer
        if "Final Answer:" in response:
            return response.split("Final Answer:")[-1].strip()
        
        # Parse action
        if "Action:" in response and "Action Input:" in response:
            action = response.split("Action:")[1].split("Action Input:")[0].strip()
            action_input = response.split("Action Input:")[1].split("\n")[0].strip()
            
            if action in tools:
                observation = tools[action](action_input)
                history += f"Observation: {observation}\n"
            else:
                history += f"Observation: Tool '{action}' not found\n"
    
    return "Could not determine answer within step limit."


# Example usage
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4", temperature=0)

tools = {
    "search": lambda q: f"Search results for: {q}",
    "calculator": lambda expr: f"Result: {eval(expr)}",
    "database_query": lambda q: f"Query result for: {q}"
}

result = react_agent(llm, tools, "What is the population of Tokyo multiplied by 2?")
print(result)
```

### 2. Plan-and-Execute

This pattern separates planning from execution, allowing for better control and verification.

```python
from typing import List, Dict
from pydantic import BaseModel

class PlanStep(BaseModel):
    step_number: int
    description: str
    tool: str
    tool_input: str
    depends_on: List[int] = []

class Plan(BaseModel):
    goal: str
    steps: List[PlanStep]

def plan_and_execute(llm, tools: dict, goal: str) -> str:
    """
    Plan-and-Execute Pattern: Plan → Execute Steps → Verify
    """
    # Phase 1: Planning
    plan_prompt = f"""Create a detailed plan to achieve this goal: {goal}

Available tools: {list(tools.keys())}

Return a JSON plan with steps in execution order."""
    
    plan_response = llm.invoke(plan_prompt)
    # In practice, use structured output parsing
    plan = parse_plan(plan_response.content)
    
    # Phase 2: Execution
    step_results = {}
    
    for step in plan.steps:
        # Resolve dependencies
        resolved_input = step.tool_input
        for dep in step.depends_on:
            if dep in step_results:
                resolved_input = resolved_input.replace(
                    f"{{step_{dep}}}", str(step_results[dep])
                )
        
        # Execute step
        if step.tool in tools:
            result = tools[step.tool](resolved_input)
            step_results[step.step_number] = result
        else:
            raise ValueError(f"Unknown tool: {step.tool}")
    
    # Phase 3: Synthesis
    synthesis_prompt = f"""Goal: {goal}
Step Results: {step_results}

Synthesize a final answer from the step results."""
    
    return llm.invoke(synthesis_prompt).content


# Real-world example: Research report generation
research_tools = {
    "search_web": search_web,
    "extract_article": extract_article_content,
    "summarize_text": summarize,
    "compare_sources": compare_sources,
    "generate_report": generate_markdown_report
}

plan = plan_and_execute(
    llm,
    research_tools,
    "Research the current state of quantum computing and write a 500-word report"
)
```

### 3. Tool Use Pattern

Agents select and compose tools dynamically based on context.

```python
from langchain.tools import Tool
from langchain.agents import AgentExecutor, create_openai_tools_agent

def create_tool_use_agent(llm, tools: List[Tool]):
    """
    Tool Use Pattern with LangChain
    """
    from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a helpful assistant with access to tools.
        Use tools to help answer user questions. Always explain your reasoning."""),
        ("user", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])
    
    agent = create_openai_tools_agent(llm, tools, prompt)
    return AgentExecutor(agent=agent, tools=tools, verbose=True, handle_parsing_errors=True)


# Define custom tools
from langchain_community.tools import DuckDuckGoSearchRun
from langchain.tools import tool

@tool
def calculate(expression: str) -> str:
    """Evaluate a mathematical expression safely."""
    import ast
    allowed_nodes = (ast.Expression, ast.BinOp, ast.UnaryOp, ast.operator,
                     ast.Num, ast.Constant)
    tree = ast.parse(expression, mode='eval')
    for node in ast.walk(tree):
        if not isinstance(node, allowed_nodes):
            return "Error: Unsafe expression"
    return str(eval(compile(tree, '<string>', 'eval')))

@tool
def get_current_time() -> str:
    """Get the current date and time."""
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

@tool
def read_file(file_path: str) -> str:
    """Read the contents of a file."""
    try:
        with open(file_path, 'r') as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {str(e)}"

tools = [DuckDuckGoSearchRun(), calculate, get_current_time, read_file]
agent = create_tool_use_agent(ChatOpenAI(model="gpt-4"), tools)
```

### 4. Reflection Pattern

Agents critique and improve their own outputs through self-reflection loops.

```python
def reflection_agent(llm, task: str, max_iterations: int = 3) -> str:
    """
    Reflection Pattern: Generate → Critique → Refine → Repeat
    """
    # Initial generation
    generate_prompt = f"""Complete this task: {task}
Provide your best attempt."""
    
    current_output = llm.invoke(generate_prompt).content
    
    for iteration in range(max_iterations):
        # Critique phase
        critique_prompt = f"""Task: {task}
Current Output: {current_output}

Critique the output above. Identify:
1. Strengths
2. Weaknesses or gaps
3. Specific improvements needed
4. Factual errors if any

Be thorough and specific."""
        
        critique = llm.invoke(critique_prompt).content
        
        # Check if improvement is needed
        improvement_check = llm.invoke(
            f"Based on this critique, is significant improvement needed? "
            f"Answer YES or NO.\n\nCritique: {critique}"
        ).content
        
        if "NO" in improvement_check.upper():
            break
        
        # Refine phase
        refine_prompt = f"""Task: {task}
Current Output: {current_output}
Critique: {critique}

Generate an improved version that addresses all the critique points."""
        
        current_output = llm.invoke(refine_prompt).content
    
    return current_output


# Example: Code generation with reflection
code = reflection_agent(
    llm,
    "Write a Python function that implements binary search on a sorted array",
    max_iterations=3
)
```

### Pattern Comparison

| Pattern | Strengths | Weaknesses | Best For |
|---------|-----------|------------|----------|
| ReAct | Transparent reasoning, adaptive | Can be verbose, step-heavy | Open-ended Q&A, research |
| Plan-and-Execute | Structured, verifiable | Inflexible to changes | Complex multi-step tasks |
| Tool Use | Flexible, composable | Tool selection challenges | Task automation |
| Reflection | High quality output | Computationally expensive | Content generation, code |

---

## 4.3 Multi-Agent Systems and Coordination

### Why Multi-Agent Systems?

Single agents have limitations: context windows, tool constraints, and single-threaded execution. Multi-agent systems overcome these through:
- **Specialization**: Each agent focuses on a specific domain
- **Parallelism**: Multiple agents work simultaneously
- **Verification**: Agents can cross-check each other
- **Scalability**: Add agents to handle increased load

### Orchestration Patterns

#### 1. Supervisor Pattern

A central coordinator delegates tasks to specialized agents.

```python
from typing import Literal
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import StateGraph, END

class SupervisorState(dict):
    """State for supervisor-based multi-agent system."""
    pass

def create_supervisor_system(llm, agents: dict):
    """
    Supervisor Pattern Implementation
    """
    supervisor_prompt = f"""You are a supervisor managing these specialized agents:
{chr(10).join(f'- {name}: {desc}' for name, desc in agents.items())}

Based on the user request, decide which agent should handle it next.
Respond with just the agent name, or 'FINISH' if the task is complete."""
    
    def supervisor_node(state):
        messages = state.get("messages", [])
        response = llm.invoke([
            {"role": "system", "content": supervisor_prompt},
            *messages
        ])
        next_agent = response.content.strip()
        
        if next_agent in agents or next_agent == "FINISH":
            return {"next": next_agent}
        return {"next": "FINISH"}
    
    return supervisor_node


def agent_node_factory(name: str, agent_llm, tools: list):
    """Create a node function for a specialized agent."""
    def node(state):
        messages = state.get("messages", [])
        # Add system prompt for this agent's specialty
        system_msg = {"role": "system", "content": f"You are the {name} agent."}
        response = agent_llm.invoke([system_msg, *messages])
        return {"messages": [response], "sender": name}
    return node
```

#### 2. Hierarchical Pattern

Agents are organized in a tree structure with managers and workers.

```python
class HierarchicalAgent:
    """Multi-level agent hierarchy."""
    
    def __init__(self, name: str, role: str, subordinates: List['HierarchicalAgent'] = None):
        self.name = name
        self.role = role
        self.subordinates = subordinates or []
        self.llm = ChatOpenAI(model="gpt-4")
    
    def delegate(self, task: str, level: int = 0) -> str:
        """Delegate task to appropriate subordinate or handle it."""
        if not self.subordinates or level >= 2:
            return self.execute(task)
        
        # Select best subordinate for task
        selection = self.llm.invoke(f"""
        Task: {task}
        Available subordinates: {[s.name + ' (' + s.role + ')' for s in self.subordinates]}
        Which subordinate should handle this? Respond with just the name.""")
        
        chosen = next((s for s in self.subordinates if s.name in selection.content), None)
        if chosen:
            return chosen.delegate(task, level + 1)
        return self.execute(task)
    
    def execute(self, task: str) -> str:
        """Execute task at this level."""
        return self.llm.invoke(f"Task: {task}\nRole: {self.role}\nExecute and provide result.").content

# Example hierarchy
ceo = HierarchicalAgent("CEO", "Strategic Planning", [
    HierarchicalAgent("CTO", "Technical Architecture", [
        HierarchicalAgent("BackendDev", "Backend Development"),
        HierarchicalAgent("FrontendDev", "Frontend Development"),
    ]),
    HierarchicalAgent("CMO", "Marketing Strategy", [
        HierarchicalAgent("ContentWriter", "Content Creation"),
        HierarchicalAgent("SEOAnalyst", "SEO Analysis"),
    ])
])

result = ceo.delegate("Build a web application for inventory management")
```

#### 3. Collaborative Debate Pattern

Multiple agents with different perspectives debate to reach optimal solutions.

```python
def debate_pattern(llm, topic: str, num_rounds: int = 3) -> str:
    """
    Debate Pattern: Multiple agents argue different perspectives
    """
    perspectives = ["Proponent", "Opponent", "Moderator"]
    
    messages = [
        {"role": "system", "content": f"Topic for debate: {topic}"},
        {"role": "user", "content": f"Begin the debate. Proponent, present your case first."}
    ]
    
    debate_log = []
    
    for round_num in range(num_rounds):
        for perspective in perspectives:
            if perspective == "Moderator" and round_num < num_rounds - 1:
                prompt = f"""As the moderator, summarize the current debate and prompt the next speaker.
                Current debate: {chr(10).join(debate_log)}"""
            elif perspective == "Proponent":
                prompt = f"""As the proponent, argue in favor of: {topic}
                Previous debate: {chr(10).join(debate_log[-4:]) if debate_log else "Start the argument."}"""
            else:  # Opponent
                prompt = f"""As the opponent, argue against: {topic}
                Previous debate: {chr(10).join(debate_log[-4:]) if debate_log else "Start the counter-argument."}"""
            
            messages.append({"role": "user", "content": prompt})
            response = llm.invoke(messages).content
            messages.append({"role": "assistant", "content": response})
            debate_log.append(f"{perspective}: {response}")
    
    # Final synthesis
    synthesis = llm.invoke(f"""
    Based on this debate, provide a balanced conclusion:
    {chr(10).join(debate_log)}
    
    Synthesize the key points and provide a final verdict.""")
    
    return synthesis.content
```

#### 4. Swarm Pattern

Autonomous agents work in parallel with emergent coordination.

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

async def swarm_pattern(llm, task: str, num_agents: int = 5) -> str:
    """
    Swarm Pattern: Multiple agents work independently, results are aggregated
    """
    async def agent_work(agent_id: int, task: str) -> str:
        prompt = f"""You are agent #{agent_id} in a swarm.
        Task: {task}
        Provide your independent analysis and solution.
        Include your unique perspective and reasoning."""
        
        response = await llm.ainvoke(prompt)
        return f"Agent #{agent_id}: {response.content}"
    
    # Run all agents in parallel
    tasks = [agent_work(i, task) for i in range(num_agents)]
    results = await asyncio.gather(*tasks)
    
    # Aggregate results
    aggregator_prompt = f"""Synthesize these independent analyses into a cohesive answer:
    {chr(10).join(results)}
    
    Identify common themes, unique insights, and provide a unified conclusion."""
    
    synthesis = await llm.ainvoke(aggregator_prompt)
    return synthesis.content

# Usage
# result = asyncio.run(swarm_pattern(llm, "Analyze the impact of AI on software development"))
```

### Real-World Multi-Agent Architectures

| Architecture | Agents | Coordination | Use Case |
|-------------|--------|--------------|----------|
| CrewAI Crew | Role-based | Sequential/Hierarchical | Research, Content Creation |
| AutoGen Group | Conversable | Event-driven | Code Generation, Analysis |
| LangGraph Graph | Node-based | State machine | Complex Workflows |
| MetaGPT | SOP-driven | Structured | Software Development |

---

## 4.4 Agent-to-Agent (A2A) Protocol

### Overview

The Agent-to-Agent (A2A) protocol defines standardized communication patterns between autonomous agents, enabling interoperability across different frameworks and implementations.

### Communication Patterns

#### 1. Request-Response Pattern

```python
from pydantic import BaseModel
from typing import Any, Optional
import uuid
from datetime import datetime

class A2AMessage(BaseModel):
    """Standard A2A message format."""
    message_id: str = str(uuid.uuid4())
    timestamp: str = datetime.now().isoformat()
    sender: str
    receiver: str
    intent: str  # "query", "task", "response", "error", "status"
    payload: dict
    metadata: dict = {}
    correlation_id: Optional[str] = None  # For request-response matching

class A2AChannel:
    """Communication channel between agents."""
    
    def __init__(self):
        self.message_queue: list[A2AMessage] = []
        self.handlers: dict[str, callable] = {}
    
    def register_handler(self, intent: str, handler: callable):
        """Register a handler for a specific message intent."""
        self.handlers[intent] = handler
    
    def send(self, message: A2AMessage) -> str:
        """Send a message to the channel."""
        self.message_queue.append(message)
        return message.message_id
    
    async def process_next(self) -> Optional[A2AMessage]:
        """Process the next message in the queue."""
        if not self.message_queue:
            return None
        
        message = self.message_queue.pop(0)
        handler = self.handlers.get(message.intent)
        
        if handler:
            response = await handler(message)
            if response:
                return response
        return None

# Example: Agent requesting data from another agent
async def data_request_handler(message: A2AMessage) -> A2AMessage:
    """Handle data requests from other agents."""
    query = message.payload.get("query", "")
    
    # Process the query
    result = {"data": f"Results for: {query}", "count": 42}
    
    return A2AMessage(
        sender="DataProviderAgent",
        receiver=message.sender,
        intent="response",
        payload=result,
        correlation_id=message.message_id
    )

# Usage
channel = A2AChannel()
channel.register_handler("query", data_request_handler)

request = A2AMessage(
    sender="AnalystAgent",
    receiver="DataProviderAgent",
    intent="query",
    payload={"query": "Q4 sales data"}
)
channel.send(request)
```

#### 2. Publish-Subscribe Pattern

```python
from typing import List, Callable
import asyncio

class PubSubA2AChannel:
    """Publish-Subscribe communication for multi-agent systems."""
    
    def __init__(self):
        self.subscribers: dict[str, List[Callable]] = {}
        self.event_log: List[dict] = []
    
    def subscribe(self, topic: str, callback: Callable):
        """Subscribe to a topic."""
        if topic not in self.subscribers:
            self.subscribers[topic] = []
        self.subscribers[topic].append(callback)
    
    def publish(self, topic: str, publisher: str, data: dict):
        """Publish an event to all subscribers."""
        event = {
            "topic": topic,
            "publisher": publisher,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        self.event_log.append(event)
        
        callbacks = self.subscribers.get(topic, [])
        for callback in callbacks:
            callback(event)

# Example: Event-driven multi-agent system
bus = PubSubA2AChannel()

def monitoring_agent_handler(event):
    print(f"[Monitor] Detected: {event['data'].get('action')}")

def logging_agent_handler(event):
    print(f"[Logger] Event from {event['publisher']}: {event['topic']}")

bus.subscribe("task.completed", monitoring_agent_handler)
bus.subscribe("task.completed", logging_agent_handler)
bus.subscribe("error.occurred", monitoring_agent_handler)

# Agents publish events
bus.publish("task.completed", "ResearchAgent", {"action": "data_collected", "items": 150})
```

#### 3. Streaming Pattern

```python
class StreamingA2AChannel:
    """Real-time streaming communication between agents."""
    
    def __init__(self):
        self.streams: dict[str, asyncio.Queue] = {}
    
    async def create_stream(self, stream_id: str):
        """Create a new communication stream."""
        self.streams[stream_id] = asyncio.Queue()
    
    async def send_to_stream(self, stream_id: str, chunk: dict):
        """Send a chunk to a stream."""
        if stream_id in self.streams:
            await self.streams[stream_id].put(chunk)
    
    async def receive_from_stream(self, stream_id: str):
        """Receive chunks from a stream."""
        if stream_id in self.streams:
            while True:
                chunk = await self.streams[stream_id].get()
                yield chunk
                if chunk.get("end_of_stream"):
                    break

# Example: Streaming analysis results
async def stream_analysis():
    stream = StreamingA2AChannel()
    await stream.create_stream("analysis-results")
    
    # Producer agent
    async def producer():
        for i in range(5):
            await stream.send_to_stream("analysis-results", {
                "chunk": i,
                "data": f"Analysis batch {i} complete",
                "end_of_stream": i == 4
            })
    
    # Consumer agent
    async def consumer():
        async for chunk in stream.receive_from_stream("analysis-results"):
            print(f"Received: {chunk['data']}")
    
    await asyncio.gather(producer(), consumer())
```

### Message Format Standards

```python
# Complete A2A Message Schema
class TaskPayload(BaseModel):
    """Payload for task-based messages."""
    task_id: str
    description: str
    parameters: dict
    expected_output: str
    constraints: dict = {}
    priority: int = 1  # 1-5, 5 being highest
    deadline: Optional[str] = None

class StatusPayload(BaseModel):
    """Payload for status updates."""
    task_id: str
    status: str  # "started", "in_progress", "completed", "failed", "blocked"
    progress: float = 0.0  # 0.0 to 1.0
    message: Optional[str] = None

class ErrorResponse(BaseModel):
    """Standard error response."""
    error_code: str
    message: str
    details: Optional[dict] = None
    retryable: bool = True

# Example: Complete message exchange
messages = [
    # Task assignment
    A2AMessage(
        sender="Orchestrator",
        receiver="ResearchAgent",
        intent="task",
        payload=TaskPayload(
            task_id="task-001",
            description="Research quantum computing trends",
            parameters={"timeframe": "2024-2026", "sources": 10},
            expected_output="Summary report",
            priority=3
        ).model_dump()
    ),
    # Status update
    A2AMessage(
        sender="ResearchAgent",
        receiver="Orchestrator",
        intent="status",
        payload=StatusPayload(
            task_id="task-001",
            status="in_progress",
            progress=0.6,
            message="Completed literature review"
        ).model_dump(),
        correlation_id="task-001"
    ),
    # Task completion
    A2AMessage(
        sender="ResearchAgent",
        receiver="Orchestrator",
        intent="response",
        payload={"task_id": "task-001", "result": "...", "sources": [...]},
        correlation_id="task-001"
    )
]
```

### A2A Security Considerations

| Concern | Mitigation |
|---------|-----------|
| Authentication | Agent identity tokens, mutual TLS |
| Authorization | Role-based access control per agent |
| Message Integrity | Digital signatures, HMAC |
| Replay Attacks | Nonce, timestamp validation |
| Data Leakage | Encryption at rest and in transit |
| Rate Limiting | Per-agent quotas, backpressure |

---

## 4.5 Building Agents with LangGraph

### LangGraph Fundamentals

LangGraph extends LangChain with graph-based state management, enabling complex agent workflows with cycles, branching, and persistence.

#### Core Concepts

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated, List
from langgraph.graph.message import add_messages

# 1. Define State
class AgentState(TypedDict):
    """State schema for the agent."""
    messages: Annotated[List, add_messages]
    next_node: str
    iterations: int
    result: str

# 2. Define Nodes
def research_node(state: AgentState) -> dict:
    """Research node - gathers information."""
    llm = ChatOpenAI(model="gpt-4")
    messages = state["messages"]
    
    response = llm.invoke([
        {"role": "system", "content": "You are a research assistant. Provide detailed information."},
        *messages
    ])
    
    return {
        "messages": [response],
        "iterations": state.get("iterations", 0) + 1
    }

def analysis_node(state: AgentState) -> dict:
    """Analysis node - processes research findings."""
    llm = ChatOpenAI(model="gpt-4")
    
    response = llm.invoke([
        {"role": "system", "content": "Analyze the research findings and draw conclusions."},
        *state["messages"]
    ])
    
    return {
        "messages": [response],
        "iterations": state.get("iterations", 0) + 1
    }

def synthesis_node(state: AgentState) -> dict:
    """Synthesis node - creates final output."""
    llm = ChatOpenAI(model="gpt-4")
    
    response = llm.invoke([
        {"role": "system", "content": "Synthesize a comprehensive final answer."},
        *state["messages"]
    ])
    
    return {
        "result": response.content,
        "iterations": state.get("iterations", 0) + 1
    }

# 3. Define Edges (Routing Logic)
def route_next(state: AgentState) -> str:
    """Determine which node to visit next."""
    iterations = state.get("iterations", 0)
    
    if iterations == 0:
        return "research"
    elif iterations == 1:
        return "analysis"
    elif iterations == 2:
        return "synthesis"
    else:
        return END

# 4. Build Graph
graph = StateGraph(AgentState)

# Add nodes
graph.add_node("research", research_node)
graph.add_node("analysis", analysis_node)
graph.add_node("synthesis", synthesis_node)

# Add edges
graph.add_conditional_edges(
    "research",
    lambda state: "analysis",
    {"analysis": "analysis"}
)
graph.add_conditional_edges(
    "analysis",
    lambda state: "synthesis",
    {"synthesis": "synthesis"}
)
graph.add_edge("synthesis", END)

# Set entry point
graph.set_entry_point("research")

# Compile
app = graph.compile()

# Execute
result = app.invoke({
    "messages": [{"role": "user", "content": "Explain quantum entanglement"}],
    "iterations": 0
})

print(result["result"])
```

### State Machine Agent

```python
from langgraph.graph import StateGraph, END
from enum import Enum

class AgentPhase(Enum):
    UNDERSTAND = "understand"
    PLAN = "plan"
    EXECUTE = "execute"
    REVIEW = "review"
    COMPLETE = "complete"

class StateMachineState(TypedDict):
    phase: str
    query: str
    plan: list
    current_step: int
    results: list
    messages: Annotated[List, add_messages]
    final_answer: str

def create_state_machine_agent(llm):
    """Build a state machine-based agent."""
    
    def understand(state: StateMachineState) -> dict:
        """Understand the user query."""
        response = llm.invoke([
            {"role": "system", "content": "Analyze the query and identify key requirements."},
            *state["messages"]
        ])
        return {
            "phase": "plan",
            "messages": [response]
        }
    
    def plan(state: StateMachineState) -> dict:
        """Create an execution plan."""
        response = llm.invoke([
            {"role": "system", "content": "Create a step-by-step plan to address the query."},
            *state["messages"]
        ])
        return {
            "phase": "execute",
            "current_step": 0,
            "messages": [response]
        }
    
    def execute(state: StateMachineState) -> dict:
        """Execute the current plan step."""
        step = state.get("current_step", 0)
        response = llm.invoke([
            {"role": "system", "content": f"Execute step {step + 1} of the plan."},
            *state["messages"]
        ])
        results = state.get("results", [])
        results.append(response.content)
        return {
            "current_step": step + 1,
            "results": results,
            "messages": [response]
        }
    
    def review(state: StateMachineState) -> dict:
        """Review results and determine if complete."""
        response = llm.invoke([
            {"role": "system", "content": "Review the results. Are we done? Answer YES or NO."},
            *state["messages"]
        ])
        is_complete = "YES" in response.content.upper()
        return {
            "phase": "complete" if is_complete else "execute",
            "messages": [response]
        }
    
    def complete(state: StateMachineState) -> dict:
        """Generate final answer."""
        response = llm.invoke([
            {"role": "system", "content": "Generate the final comprehensive answer."},
            *state["messages"]
        ])
        return {"final_answer": response.content}
    
    # Routing logic
    def route_after_understand(state): return "plan"
    def route_after_plan(state): return "execute"
    
    def route_after_execute(state):
        return "review"
    
    def route_after_review(state):
        return state.get("phase", "execute")
    
    # Build graph
    workflow = StateGraph(StateMachineState)
    
    workflow.add_node("understand", understand)
    workflow.add_node("plan", plan)
    workflow.add_node("execute", execute)
    workflow.add_node("review", review)
    workflow.add_node("complete", complete)
    
    workflow.set_entry_point("understand")
    workflow.add_edge("understand", "plan")
    workflow.add_edge("plan", "execute")
    workflow.add_edge("execute", "review")
    workflow.add_conditional_edges("review", route_after_review)
    workflow.add_edge("complete", END)
    
    return workflow.compile()

# Usage
agent = create_state_machine_agent(ChatOpenAI(model="gpt-4"))
result = agent.invoke({
    "phase": "understand",
    "query": "Build a REST API for user management",
    "messages": [{"role": "user", "content": "Build a REST API for user management"}],
    "current_step": 0,
    "results": []
})
```

### Tool-Using Agent with LangGraph

```python
from langgraph.prebuilt import ToolNode, create_react_agent
from langchain_core.tools import tool

@tool
def search(query: str) -> str:
    """Search for information online."""
    # In production, use actual search API
    return f"Search results for: {query}"

@tool
def calculator(expression: str) -> str:
    """Calculate mathematical expressions."""
    try:
        return str(eval(expression, {"__builtins__": {}}, {}))
    except:
        return "Error calculating expression"

@tool
def file_reader(path: str) -> str:
    """Read file contents."""
    try:
        with open(path, 'r') as f:
            return f.read()[:1000]
    except Exception as e:
        return f"Error: {str(e)}"

# Create ReAct agent with tools
tools = [search, calculator, file_reader]
llm = ChatOpenAI(model="gpt-4o")

# Using the prebuilt create_react_agent
react_agent = create_react_agent(llm, tools)

# Execute
result = react_agent.invoke({
    "messages": [{"role": "user", "content": "What is 2^10? Then search for applications of this number in computing."}]
})

print(result["messages"][-1].content)
```

### Human-in-the-Loop Agent

```python
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt

def human_approval_agent():
    """Agent that requires human approval at critical steps."""
    
    def node_with_approval(state: AgentState) -> dict:
        # Interrupt for human approval
        approval = interrupt({
            "action": "approve_deployment",
            "details": state.get("result", ""),
            "question": "Do you approve this action?"
        })
        
        if approval.get("approved"):
            return {"result": f"Approved: {state['result']}"}
        else:
            return {"result": "Action rejected by human reviewer"}
    
    workflow = StateGraph(AgentState)
    workflow.add_node("generate", research_node)
    workflow.add_node("approval", node_with_approval)
    workflow.add_edge("generate", "approval")
    workflow.add_edge("approval", END)
    workflow.set_entry_point("generate")
    
    # With checkpointing for persistence
    checkpointer = MemorySaver()
    return workflow.compile(checkpointer=checkpointer)

# Usage with human interaction
agent = human_approval_agent()

# First run - will interrupt
thread_config = {"configurable": {"thread_id": "approval-1"}}

# Run until interruption
for event in agent.stream(
    {"messages": [{"role": "user", "content": "Analyze this code for deployment"}]},
    thread_config,
    stream_mode="values"
):
    print(event)

# Resume with human approval
result = agent.invoke(
    Command(resume={"approved": True}),
    thread_config
)
```

### Multi-Agent Graph with LangGraph

```python
from langgraph.graph import StateGraph, END

class MultiAgentState(TypedDict):
    messages: Annotated[List, add_messages]
    next: str
    final_output: str

def create_multi_agent_graph():
    """Create a multi-agent system with LangGraph."""
    
    # Define specialized agents
    def researcher(state: MultiAgentState) -> dict:
        llm = ChatOpenAI(model="gpt-4")
        response = llm.invoke([
            {"role": "system", "content": "You are a researcher. Gather relevant information."},
            *state["messages"]
        ])
        return {"messages": [response], "next": "analyst"}
    
    def analyst(state: MultiAgentState) -> dict:
        llm = ChatOpenAI(model="gpt-4")
        response = llm.invoke([
            {"role": "system", "content": "You are an analyst. Interpret the research findings."},
            *state["messages"]
        ])
        return {"messages": [response], "next": "writer"}
    
    def writer(state: MultiAgentState) -> dict:
        llm = ChatOpenAI(model="gpt-4")
        response = llm.invoke([
            {"role": "system", "content": "You are a writer. Create a clear, comprehensive response."},
            *state["messages"]
        ])
        return {"messages": [response], "next": "END", "final_output": response.content}
    
    def router(state: MultiAgentState) -> str:
        return state.get("next", "END")
    
    # Build graph
    graph = StateGraph(MultiAgentState)
    
    graph.add_node("researcher", researcher)
    graph.add_node("analyst", analyst)
    graph.add_node("writer", writer)
    
    graph.set_entry_point("researcher")
    graph.add_conditional_edges("researcher", router)
    graph.add_conditional_edges("analyst", router)
    graph.add_conditional_edges("writer", router)
    
    return graph.compile()

# Usage
multi_agent = create_multi_agent_graph()
result = multi_agent.invoke({
    "messages": [{"role": "user", "content": "Explain blockchain technology"}],
    "next": "researcher"
})
print(result["final_output"])
```

### LangGraph Best Practices

| Practice | Description |
|----------|-------------|
| State Design | Keep state minimal and use TypedDict for type safety |
| Checkpointing | Always use checkpointer for production agents |
| Error Handling | Add error nodes for graceful failure recovery |
| Streaming | Use `stream_mode="messages"` for real-time output |
| Human-in-Loop | Use `interrupt()` for critical decision points |
| Subgraphs | Use subgraphs for modular, reusable agent components |
| Persistence | Store conversation history and agent state externally |

---

## Summary

This module covered the foundations of Agentic AI systems:

1. **Agent Fundamentals**: Core components (perception, memory, reasoning, action, reflection) and the autonomy spectrum
2. **Design Patterns**: ReAct, Plan-and-Execute, Tool Use, and Reflection patterns with implementations
3. **Multi-Agent Systems**: Supervisor, hierarchical, debate, and swarm coordination patterns
4. **A2A Protocol**: Standardized communication patterns including request-response, pub-sub, and streaming
5. **LangGraph**: State machines, tool-using agents, human-in-the-loop, and multi-agent graphs

These patterns form the foundation for building production-ready agentic systems that can handle complex, multi-step tasks autonomously.
