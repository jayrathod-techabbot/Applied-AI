# Exercise: Implementing Structured AI Logging

## Task

Implement a structured logging system for a RAG application with PII handling and cost tracking.

## Requirements

1. Create a structured logger for AI requests
2. Implement PII masking for user data
3. Track token usage and calculate costs
4. Add agent execution tracing

## Starter Code

```python
import json
import logging
import re
import hashlib
from datetime import datetime
from typing import Dict, Any, Optional
import uuid

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)

class AILogger:
    def __init__(self, log_file: str = "ai_logs.json"):
        self.log_file = log_file
        self.logger = logging.getLogger("ai_logger")
        
    def mask_pii(self, text: str) -> str:
        """Mask PII in text"""
        # Mask email
        text = re.sub(r'[\w.-]+@[\w.-]+\.\w+', '[EMAIL]', text)
        # Mask phone
        text = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[PHONE]', text)
        # Mask SSN
        text = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', '[SSN]', text)
        return text
    
    def hash_user_id(self, user_id: str) -> str:
        """Hash user ID for privacy"""
        return hashlib.sha256(user_id.encode()).hexdigest()[:12]
    
    def log_request(self, 
                   user_id: str,
                   prompt: str,
                   model: str,
                   metadata: Dict[str, Any]):
        """Log an AI request"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": str(uuid.uuid4()),
            "user_id_hash": self.hash_user_id(user_id),
            "model": model,
            "prompt": self.mask_pii(prompt),
            "prompt_tokens": metadata.get("prompt_tokens", 0),
            "completion_tokens": metadata.get("completion_tokens", 0),
            "latency_ms": metadata.get("latency_ms", 0)
        }
        
        self.logger.info(json.dumps(log_entry))
        return log_entry["request_id"]
    
    def log_retrieval(self,
                     request_id: str,
                     query: str,
                     retrieved_docs: list):
        """Log retrieval stage"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": request_id,
            "stage": "retrieval",
            "query": self.mask_pii(query),
            "num_retrieved": len(retrieved_docs),
            "top_score": retrieved_docs[0].get("score", 0) if retrieved_docs else 0
        }
        
        self.logger.info(json.dumps(log_entry))
    
    def log_agent_trace(self,
                       request_id: str,
                       steps: list):
        """Log agent execution trace"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": request_id,
            "stage": "agent_execution",
            "steps": steps,
            "total_steps": len(steps)
        }
        
        self.logger.info(json.dumps(log_entry))
    
    def calculate_cost(self, 
                      prompt_tokens: int, 
                      completion_tokens: int,
                      model: str) -> float:
        """Calculate API cost"""
        pricing = {
            "gpt-4": {"input": 0.03, "output": 0.06},
            "gpt-3.5-turbo": {"input": 0.0015, "output": 0.002},
            "claude-3": {"input": 0.015, "output": 0.075}
        }
        
        if model not in pricing:
            return 0.0
            
        rates = pricing[model]
        input_cost = (prompt_tokens / 1000) * rates["input"]
        output_cost = (completion_tokens / 1000) * rates["output"]
        
        return input_cost + output_cost


# Test the logger
if __name__ == "__main__":
    logger = AILogger()
    
    # Log a request
    request_id = logger.log_request(
        user_id="user_123",
        prompt="What is john.doe@email.com's account balance?",
        model="gpt-4",
        metadata={
            "prompt_tokens": 150,
            "completion_tokens": 200,
            "latency_ms": 1500
        }
    )
    
    # Log retrieval
    logger.log_retrieval(
        request_id=request_id,
        query="account balance for john",
        retrieved_docs=[
            {"doc_id": "doc_1", "score": 0.95},
            {"doc_id": "doc_2", "score": 0.88}
        ]
    )
    
    # Calculate cost
    cost = logger.calculate_cost(150, 200, "gpt-4")
    print(f"Request cost: ${cost:.4f}")
```

## Deliverable

Create a complete logging module with:
- Structured JSON logging
- PII masking
- Cost tracking
- Agent trace logging
- Log aggregation ready format

## Solution

See solution.py for a complete implementation.
