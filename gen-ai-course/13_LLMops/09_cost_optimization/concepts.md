# Cost Optimization - Concepts

## Table of Contents
1. [Understanding LLM Costs](#understanding-llm-costs)
2. [Token Optimization](#token-optimization)
3. [Caching Strategies](#caching-strategies)
4. [Model Selection](#model-selection)
5. [Infrastructure Cost](#infrastructure-cost)
6. [Budget Management](#budget-management)
7. [Cost Monitoring](#cost-monitoring)
8. [Implementation](#implementation)

---

## Understanding LLM Costs

### Cost Structure

```
┌─────────────────────────────────────────────────────────────────┐
│                    LLM Cost Components                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   Total Cost = API Costs + Infrastructure Costs + OpEx           │
│                                                                  │
│   ┌──────────────────────────────────────────────────────────┐  │
│   │  API Costs (Typically 70-90% of total)                   │  │
│   │  ├── Input Tokens × Price per 1K tokens                 │  │
│   │  └── Output Tokens × Price per 1K tokens                │  │
│   └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│   ┌──────────────────────────────────────────────────────────┐  │
│   │  Infrastructure Costs (10-20% of total)                  │  │
│   │  ├── GPU instances (for self-hosted)                     │  │
│   │  ├── Cloud compute (API servers)                         │  │
│   │  ├── Storage (models, vector DB)                         │  │
│   │  └── Network bandwidth                                   │  │
│   └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│   ┌──────────────────────────────────────────────────────────┐  │
│   │  Operational Costs (5-10% of total)                      │  │
│   │  ├── Monitoring & logging                                │  │
│   │  ├── Engineering time                                   │  │
│   │  └── Compliance & security                               │  │
│   └──────────────────────────────────────────────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Provider Pricing Comparison

| Provider | Model | Input ($/1K) | Output ($/1K) | Context |
|----------|-------|--------------|---------------|---------|
| **OpenAI** | GPT-4 | $0.03 | $0.06 | 128K |
| **OpenAI** | GPT-4 Turbo | $0.01 | $0.03 | 128K |
| **OpenAI** | GPT-3.5 Turbo | $0.001 | $0.002 | 16K |
| **Anthropic** | Claude 3 Opus | $0.015 | $0.075 | 200K |
| **Anthropic** | Claude 3 Sonnet | $0.003 | $0.015 | 200K |
| **Anthropic** | Claude 3 Haiku | $0.00025 | $0.00125 | 200K |
| **Google** | Gemini Pro | $0.00125 | $0.005 | 32K |
| **Google** | Gemini Ultra | $0.0075 | $0.03 | 32K |

---

## Token Optimization

### Prompt Compression

```python
# prompt_optimizer.py
from typing import List, Dict, Optional
import re

class PromptOptimizer:
    """
    Optimize prompts to reduce token count
    """
    
    def __init__(self):
        self.compression_patterns = [
            # Remove extra whitespace
            (r'\s+', ' '),
            # Remove redundant newlines
            (r'\n\n+', '\n'),
            # Remove common filler words
            (r'\bplease\b', ''),
            (r'\bkindly\b', ''),
            (r'\bbasically\b', ''),
        ]
    
    def compress(self, prompt: str) -> str:
        """Compress prompt by removing unnecessary tokens"""
        compressed = prompt
        
        for pattern, replacement in self.compression_patterns:
            compressed = re.sub(pattern, replacement, compressed)
        
        # Remove leading/trailing whitespace
        compressed = compressed.strip()
        
        return compressed
    
    def extract_essentials(self, prompt: str) -> str:
        """Extract only essential parts of the prompt"""
        # Remove greetings and pleasantries
        essential = prompt
        
        # Remove common patterns
        patterns_to_remove = [
            r'^hi(,| |\.|$)',
            r'^hello(,| |\.|$)',
            r'^hey(,| |\.|$)',
            r'^good morning(,| |\.|$)',
            r'^good afternoon(,| |\.|$)',
            r'^thank you(,| |\.|$)',
            r'^thanks(,| |\.|$)',
        ]
        
        for pattern in patterns_to_remove:
            essential = re.sub(pattern, '', essential, flags=re.IGNORECASE)
        
        return essential.strip()
    
    def optimize_few_shot(self, examples: List[Dict]) -> List[Dict]:
        """Optimize few-shot examples to use fewer tokens"""
        optimized = []
        
        for example in examples:
            # Simplify inputs/outputs while maintaining clarity
            optimized_example = {
                "input": self.compress(example.get("input", "")),
                "output": self.compress(example.get("output", ""))
            }
            optimized.append(optimized_example)
        
        return optimized
    
    def use_abbreviations(self, text: str) -> str:
        """Replace common phrases with abbreviations"""
        abbreviations = {
            "information": "info",
            "example": "ex",
            "question": "Q",
            "answer": "A",
            "description": "desc",
            "approximately": "approx",
        }
        
        for full, abbr in abbreviations.items():
            text = re.sub(r'\b' + full + r'\b', abbr, text, flags=re.IGNORECASE)
        
        return text

# Token counting
def count_tokens(text: str, encoding_name: str = "cl100k_base") -> int:
    """Count tokens in text"""
    import tiktoken
    
    encoding = tiktoken.get_encoding(encoding_name)
    tokens = encoding.encode(text)
    
    return len(tokens)

def estimate_cost(
    input_tokens: int,
    output_tokens: int,
    model: str = "gpt-4"
) -> float:
    """Estimate cost for a request"""
    
    pricing = {
        "gpt-4": {"input": 0.03, "output": 0.06},
        "gpt-4-turbo": {"input": 0.01, "output": 0.03},
        "gpt-3.5-turbo": {"input": 0.001, "output": 0.002},
        "claude-3-opus": {"input": 0.015, "output": 0.075},
        "claude-3-sonnet": {"input": 0.003, "output": 0.015},
    }
    
    p = pricing.get(model, {"input": 0, "output": 0})
    
    return (input_tokens / 1000) * p["input"] + (output_tokens / 1000) * p["output"]
```

### Context Window Management

```python
# context_manager.py
from typing import List, Dict, Optional

class ContextManager:
    """
    Manage context window efficiently
    """
    
    def __init__(self, max_tokens: int = 8000, reserved_tokens: int = 1000):
        self.max_tokens = max_tokens
        self.reserved_tokens = reserved_tokens
        self.available_tokens = max_tokens - reserved_tokens
    
    def truncate_history(
        self,
        messages: List[Dict],
        keep_system: bool = True
    ) -> List[Dict]:
        """Truncate message history to fit within context"""
        truncated = []
        
        if keep_system and messages and messages[0].get("role") == "system":
            truncated.append(messages[0])
        
        total_tokens = 0
        
        # Process messages in reverse (keep most recent)
        for message in reversed(messages):
            if message.get("role") == "system" and keep_system:
                continue
            
            # Estimate tokens
            msg_tokens = self._estimate_tokens(message)
            
            if total_tokens + msg_tokens <= self.available_tokens:
                truncated.insert(0 if not truncated or truncated[0].get("role") != "system" else 1, message)
                total_tokens += msg_tokens
            else:
                break
        
        return truncated
    
    def summarize_older_messages(
        self,
        messages: List[Dict],
        summarize_fn
    ) -> List[Dict]:
        """Summarize older messages to save tokens"""
        if len(messages) <= 3:
            return messages
        
        # Keep recent messages
        recent = messages[-3:]
        
        # Summarize older ones
        older = messages[:-3]
        summary = summarize_fn(older)
        
        return [{"role": "system", "content": f"Previous conversation summary: {summary}"}] + recent
    
    def _estimate_tokens(self, message: Dict) -> int:
        """Rough estimate of tokens in a message"""
        content = message.get("content", "")
        # Rough estimate: 1 token ≈ 4 characters
        return len(content) // 4

# Streaming to reduce perceived latency
async def stream_response(prompt: str, model: str = "gpt-4"):
    """Stream response to reduce perceived latency"""
    from openai import AsyncOpenAI
    
    client = AsyncOpenAI()
    
    response = await client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        stream=True
    )
    
    async for chunk in response:
        if chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content
```

---

## Caching Strategies

### Multi-Level Caching

```
┌─────────────────────────────────────────────────────────────────┐
│                    Multi-Level Caching Architecture                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   Request                                                         │
│      │                                                            │
│      ▼                                                            │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │  L1: Exact Match Cache (In-Memory)                       │   │
│   │  - Redis                                                  │   │
│   │  - TTL: 1-5 minutes                                      │   │
│   │  - Hit Rate Target: 30-50%                               │   │
│   │  - Latency: <1ms                                         │   │
│   └───────────────────────┬───────────────────────────────────┘   │
│                           │ Miss                                   │
│                           ▼                                        │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │  L2: Semantic Cache (Vector Store)                      │   │
│   │  - Store embeddings of prompts                          │   │
│   │  - Similarity threshold: 0.85-0.95                      │   │
│   │  - TTL: 1-24 hours                                      │   │
│   │  - Hit Rate Target: 20-40%                               │   │
│   │  - Latency: 10-50ms                                      │   │
│   └───────────────────────┬───────────────────────────────────┘   │
│                           │ Miss                                   │
│                           ▼                                        │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │  L3: Provider Cache                                     │   │
│   │  - OpenAI/Anthropic built-in cache                      │   │
│   │  - Automatic for identical prompts                      │   │
│   │  - Varies by provider                                   │   │
│   └───────────────────────┬───────────────────────────────────┘   │
│                           │ Miss                                   │
│                           ▼                                        │
│                     LLM Call                                       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Semantic Cache Implementation

```python
# semantic_cache.py
from typing import Optional, Dict
import hashlib
import time

class SemanticCache:
    """
    Semantic cache for LLM responses using vector similarity
    """
    
    def __init__(
        self,
        similarity_threshold: float = 0.95,
        ttl_seconds: int = 3600,
        embedding_model: str = "text-embedding-ada-002"
    ):
        self.similarity_threshold = similarity_threshold
        self.ttl_seconds = ttl_seconds
        self.embedding_model = embedding_model
        
        # In production, use a proper vector store
        self._cache: Dict = {}
        self._embeddings: Dict = {}
    
    async def get(self, prompt: str) -> Optional[Dict]:
        """Get cached response for similar prompts"""
        # Get embedding for prompt
        embedding = await self._get_embedding(prompt)
        
        # Find similar cached prompts
        best_match = None
        best_similarity = 0
        
        for cached_prompt, cached_data in self._embeddings.items():
            similarity = self._cosine_similarity(embedding, cached_data["embedding"])
            
            if similarity > best_similarity:
                best_similarity = similarity
                best_match = cached_prompt
        
        # Check if similarity is above threshold
        if best_match and best_similarity >= self.similarity_threshold:
            cached_entry = self._cache[best_match]
            
            # Check TTL
            if time.time() - cached_entry["timestamp"] < self.ttl_seconds:
                # Update access time
                cached_entry["last_access"] = time.time()
                cached_entry["hit_count"] = cached_entry.get("hit_count", 0) + 1
                
                return {
                    "response": cached_entry["response"],
                    "similarity": best_similarity,
                    "cached_prompt": best_match
                }
        
        return None
    
    async def set(self, prompt: str, response: str, metadata: Dict = None):
        """Cache a response"""
        embedding = await self._get_embedding(prompt)
        
        # Store with hashed key
        key = hashlib.md5(prompt.encode()).hexdigest()
        
        self._cache[prompt] = {
            "response": response,
            "timestamp": time.time(),
            "last_access": time.time(),
            "hit_count": 0,
            "metadata": metadata or {}
        }
        
        self._embeddings[prompt] = {
            "embedding": embedding
        }
    
    async def _get_embedding(self, text: str) -> list:
        """Get embedding for text"""
        # Use OpenAI embeddings API in production
        from openai import AsyncOpenAI
        client = AsyncOpenAI()
        
        response = await client.embeddings.create(
            model=self.embedding_model,
            input=text
        )
        
        return response.data[0].embedding
    
    def _cosine_similarity(self, a: list, b: list) -> float:
        """Calculate cosine similarity between two vectors"""
        import numpy as np
        
        a = np.array(a)
        b = np.array(b)
        
        dot_product = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        
        return dot_product / (norm_a * norm_b)
    
    def get_stats(self) -> Dict:
        """Get cache statistics"""
        total_hits = sum(e.get("hit_count", 0) for e in self._cache.values())
        
        return {
            "total_entries": len(self._cache),
            "total_hits": total_hits,
            "cache_size_bytes": sum(
                len(str(v)) for v in self._cache.values()
            )
        }
```

---

## Model Selection

### Intelligent Model Routing

```python
# model_router.py
from typing import Dict, List, Optional
from dataclasses import dataclass
import re

@dataclass
class ModelConfig:
    name: str
    strength: str
    latency_ms: int
    cost_per_1k_input: float
    cost_per_1k_output: float
    context_window: int
    max_output_tokens: int

class ModelRouter:
    """
    Route requests to appropriate models based on task
    """
    
    MODEL_CONFIGS = {
        "gpt-4": ModelConfig(
            name="gpt-4",
            strength="complex reasoning, analysis",
            latency_ms=2000,
            cost_per_1k_input=0.03,
            cost_per_1k_output=0.06,
            context_window=128000,
            max_output_tokens=4096
        ),
        "gpt-3.5-turbo": ModelConfig(
            name="gpt-3.5-turbo",
            strength="simple tasks, high volume",
            latency_ms=500,
            cost_per_1k_input=0.001,
            cost_per_1k_output=0.002,
            context_window=16385,
            max_output_tokens=4096
        ),
        "claude-3-sonnet": ModelConfig(
            name="claude-3-sonnet",
            strength="balanced, long context",
            latency_ms=1000,
            cost_per_1k_input=0.003,
            cost_per_1k_output=0.015,
            context_window=200000,
            max_output_tokens=4096
        )
    }
    
    # Task classification patterns
    TASK_PATTERNS = {
        "simple": [
            r"^(what is|who is|when did|where is)",
            r"^(translate|convert|calculate)",
            r"^summarize",
            r"^list"
        ],
        "moderate": [
            r"explain",
            r"compare",
            r"describe",
            r"write (code|email|letter)"
        ],
        "complex": [
            r"analyze",
            r"design",
            r"architect",
            r"evaluate",
            r"create a comprehensive"
        ]
    }
    
    def classify_task(self, prompt: str) -> str:
        """Classify task complexity"""
        prompt_lower = prompt.lower()
        
        for complexity, patterns in self.TASK_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, prompt_lower):
                    return complexity
        
        return "moderate"  # Default
    
    def select_model(
        self,
        prompt: str,
        user_tier: str = "free",
        context_length: int = None
    ) -> str:
        """Select the best model for the task"""
        
        complexity = self.classify_task(prompt)
        
        # Check context length requirements
        if context_length and context_length > 16000:
            # Need long context model
            if context_length > 128000:
                return "claude-3-sonnet"
        
        # Route based on complexity and tier
        if user_tier == "free":
            # Free tier gets smaller model
            return "gpt-3.5-turbo"
        
        if complexity == "simple":
            return "gpt-3.5-turbo"
        
        if complexity == "moderate":
            return "claude-3-sonnet"
        
        if complexity == "complex":
            return "gpt-4"
        
        return "gpt-3.5-turbo"  # Default
    
    def estimate_cost(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int
    ) -> float:
        """Estimate cost for model usage"""
        config = self.MODEL_CONFIGS.get(model)
        
        if not config:
            return 0
        
        input_cost = (input_tokens / 1000) * config.cost_per_1k_input
        output_cost = (output_tokens / 1000) * config.cost_per_1k_output
        
        return input_cost + output_cost
    
    def get_cheapest_alternative(self, model: str) -> str:
        """Get cheaper alternative model"""
        alternatives = {
            "gpt-4": "gpt-3.5-turbo",
            "claude-3-opus": "claude-3-sonnet",
            "claude-3-sonnet": "gpt-3.5-turbo"
        }
        
        return alternatives.get(model, model)
```

---

## Budget Management

### Budget Implementation

```python
# budget_manager.py
from typing import Dict, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import time

@dataclass
class Budget:
    limit: float
    spent: float = 0
    period_start: datetime = None
    
    def reset_if_needed(self, period: str):
        """Reset budget for new period"""
        now = datetime.now()
        
        if self.period_start is None:
            self.period_start = now
            return
        
        should_reset = False
        
        if period == "daily":
            should_reset = (now - self.period_start).days >= 1
        elif period == "weekly":
            should_reset = (now - self.period_start).days >= 7
        elif period == "monthly":
            should_reset = (now - self.period_start).month != self.period_start.month
        
        if should_reset:
            self.spent = 0
            self.period_start = now

class BudgetManager:
    """
    Manage LLM usage budgets
    """
    
    def __init__(self, daily_limit: float, monthly_limit: float):
        self.daily_budget = Budget(limit=daily_limit)
        self.monthly_budget = Budget(limit=monthly_limit)
        self.cost_per_user: Dict[str, float] = {}
    
    def check_budget(
        self,
        user_id: str,
        estimated_cost: float
    ) -> tuple[bool, str]:
        """Check if request is within budget"""
        
        # Reset budgets if needed
        self.daily_budget.reset_if_needed("daily")
        self.monthly_budget.reset_if_needed("monthly")
        
        # Check daily budget
        if self.daily_budget.spent + estimated_cost > self.daily_budget.limit:
            return False, f"Daily budget exceeded. Limit: ${self.daily_budget.limit}"
        
        # Check monthly budget
        if self.monthly_budget.spent + estimated_cost > self.monthly_budget.limit:
            return False, f"Monthly budget exceeded. Limit: ${self.monthly_budget.limit}"
        
        # Check user-specific budget
        user_spent = self.cost_per_user.get(user_id, 0)
        user_limit = self._get_user_limit(user_id)
        
        if user_spent + estimated_cost > user_limit:
            return False, f"User budget exceeded. Limit: ${user_limit}"
        
        return True, "Budget check passed"
    
    def record_cost(
        self,
        user_id: str,
        cost: float,
        metadata: Dict = None
    ):
        """Record actual cost"""
        self.daily_budget.spent += cost
        self.monthly_budget.spent += cost
        
        if user_id not in self.cost_per_user:
            self.cost_per_user[user_id] = 0
        
        self.cost_per_user[user_id] += cost
        
        # Log for analytics
        self._log_cost(user_id, cost, metadata)
    
    def _get_user_limit(self, user_id: str) -> float:
        """Get user-specific limit (could be dynamic)"""
        # Simple implementation: 10% of monthly budget per user
        return self.monthly_budget.limit * 0.1
    
    def _log_cost(self, user_id: str, cost: float, metadata: Dict):
        """Log cost for analytics"""
        # Implementation: send to logging/analytics system
        pass
    
    def get_budget_status(self) -> Dict:
        """Get current budget status"""
        return {
            "daily": {
                "limit": self.daily_budget.limit,
                "spent": self.daily_budget.spent,
                "remaining": self.daily_budget.limit - self.daily_budget.spent,
                "utilization": (self.daily_budget.spent / self.daily_budget.limit) * 100
            },
            "monthly": {
                "limit": self.monthly_budget.limit,
                "spent": self.monthly_budget.spent,
                "remaining": self.monthly_budget.limit - self.monthly_budget.spent,
                "utilization": (self.monthly_budget.spent / self.monthly_budget.limit) * 100
            }
        }
```

---

## Cost Monitoring

### Cost Dashboard

```python
# cost_monitoring.py
from typing import Dict, List
from datetime import datetime, timedelta
import time

class CostMonitor:
    """
    Monitor and track LLM costs
    """
    
    def __init__(self):
        self.cost_by_model: Dict[str, float] = {}
        self.cost_by_user: Dict[str, float] = {}
        self.cost_by_endpoint: Dict[str, float] = {}
        self.cost_by_hour: Dict[int, float] = {}  # Hour of day
        
        self.total_tokens_by_model: Dict[str, Dict] = {}
    
    def record_request(
        self,
        model: str,
        user_id: str,
        endpoint: str,
        input_tokens: int,
        output_tokens: int,
        cost: float
    ):
        """Record a request's cost"""
        
        # By model
        self.cost_by_model[model] = self.cost_by_model.get(model, 0) + cost
        
        # By user
        self.cost_by_user[user_id] = self.cost_by_user.get(user_id, 0) + cost
        
        # By endpoint
        self.cost_by_endpoint[endpoint] = self.cost_by_endpoint.get(endpoint, 0) + cost
        
        # By hour
        hour = datetime.now().hour
        self.cost_by_hour[hour] = self.cost_by_hour.get(hour, 0) + cost
        
        # Track tokens
        if model not in self.total_tokens_by_model:
            self.total_tokens_by_model[model] = {
                "input": 0,
                "output": 0
            }
        
        self.total_tokens_by_model[model]["input"] += input_tokens
        self.total_tokens_by_model[model]["output"] += output_tokens
    
    def get_summary(self, period: str = "daily") -> Dict:
        """Get cost summary"""
        
        total_cost = sum(self.cost_by_model.values())
        
        # Calculate projections
        if period == "daily":
            hours_elapsed = datetime.now().hour + 1
        else:
            hours_elapsed = 24
        
        projected_daily = (total_cost / hours_elapsed) * 24
        
        return {
            "total_cost": total_cost,
            "by_model": self.cost_by_model,
            "by_user": dict(sorted(
                self.cost_by_user.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]),  # Top 10 users
            "by_endpoint": self.cost_by_endpoint,
            "total_tokens": self.total_tokens_by_model,
            "projected_daily": projected_daily
        }
    
    def get_anomalies(self) -> List[Dict]:
        """Detect cost anomalies"""
        anomalies = []
        
        # Check for unusually high user costs
        if self.cost_by_user:
            avg_cost = sum(self.cost_by_user.values()) / len(self.cost_by_user)
            
            for user_id, cost in self.cost_by_user.items():
                if cost > avg_cost * 10:
                    anomalies.append({
                        "type": "high_user_cost",
                        "user_id": user_id,
                        "cost": cost,
                        "avg_cost": avg_cost,
                        "multiplier": cost / avg_cost
                    })
        
        return anomalies
    
    def send_alert(self, message: str, severity: str = "warning"):
        """Send cost alert"""
        # Implementation: integrate with alerting system
        print(f"[{severity.upper()}] Cost Alert: {message}")
```

---

## Implementation

### Complete Cost Optimization Implementation

```python
# cost_optimization_service.py
from typing import Dict, Optional
import asyncio

class LLMServiceWithCostOptimization:
    """
    Complete LLM service with built-in cost optimization
    """
    
    def __init__(self):
        self.cache = SemanticCache(similarity_threshold=0.95)
        self.router = ModelRouter()
        self.budget_manager = BudgetManager(
            daily_limit=100.0,
            monthly_limit=2000.0
        )
        self.cost_monitor = CostMonitor()
        self.prompt_optimizer = PromptOptimizer()
    
    async def chat(
        self,
        prompt: str,
        user_id: str,
        endpoint: str = "chat",
        model_preference: Optional[str] = None
    ) -> Dict:
        """Chat with cost optimization"""
        
        # 1. Optimize prompt
        optimized_prompt = self.prompt_optimizer.compress(prompt)
        
        # 2. Check semantic cache
        cached = await self.cache.get(optimized_prompt)
        
        if cached:
            return {
                "response": cached["response"],
                "cached": True,
                "similarity": cached["similarity"]
            }
        
        # 3. Select model
        model = model_preference or self.router.select_model(optimized_prompt)
        
        # 4. Estimate tokens and cost
        input_tokens = count_tokens(optimized_prompt)
        estimated_output = 500  # Estimate
        estimated_cost = self.router.estimate_cost(model, input_tokens, estimated_output)
        
        # 5. Check budget
        allowed, message = self.budget_manager.check_budget(user_id, estimated_cost)
        
        if not allowed:
            # Try cheaper model
            cheaper_model = self.router.get_cheapest_alternative(model)
            estimated_cost = self.router.estimate_cost(
                cheaper_model, input_tokens, estimated_output
            )
            
            allowed, message = self.budget_manager.check_budget(user_id, estimated_cost)
            
            if not allowed:
                raise ValueError(message)
            
            model = cheaper_model
        
        # 6. Make request
        response = await self._call_model(model, optimized_prompt)
        
        # 7. Calculate actual cost
        output_tokens = count_tokens(response)
        actual_cost = self.router.estimate_cost(model, input_tokens, output_tokens)
        
        # 8. Record costs
        self.budget_manager.record_cost(user_id, actual_cost)
        self.cost_monitor.record_request(
            model=model,
            user_id=user_id,
            endpoint=endpoint,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost=actual_cost
        )
        
        # 9. Cache response
        await self.cache.set(optimized_prompt, response)
        
        return {
            "response": response,
            "model": model,
            "cost": actual_cost,
            "tokens": {
                "input": input_tokens,
                "output": output_tokens
            }
        }
    
    async def _call_model(self, model: str, prompt: str) -> str:
        """Make actual LLM call"""
        # Implementation: call OpenAI/Anthropic API
        pass

# Helper functions
def count_tokens(text: str) -> int:
    import tiktoken
    enc = tiktoken.get_encoding("cl100k_base")
    return len(enc.encode(text))
```

---

## Best Practices

1. **Start with Caching**: Biggest ROI for minimal effort
2. **Optimize Prompts**: Remove unnecessary tokens
3. **Use Right Model**: Don't use GPT-4 for simple tasks
4. **Set Budgets**: Prevent cost overruns
5. **Monitor Continuously**: Track costs in real-time
6. **Implement Rate Limits**: Control usage per user
7. **Consider Self-Hosting**: For very high volume
8. **Review and Iterate**: Regular cost audits
