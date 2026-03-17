# Production Issues - Exercise

## Objective

Implement debugging and monitoring solutions for a production RAG system.

## Setup

```python
# Required imports
import time
import logging
from typing import List, Dict, Any
from dataclasses import dataclass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
```

## Exercise 1: Implement Request Tracing

Create a request tracing system to track requests through the RAG pipeline.

```python
@dataclass
class RequestSpan:
    """Represents a single span in request tracing."""
    operation: str
    start_time: float
    end_time: float = 0.0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    @property
    def duration(self) -> float:
        return self.end_time - self.start_time


class RequestTracer:
    """Trace requests through the RAG pipeline."""
    
    def __init__(self):
        self.spans: List[RequestSpan] = []
        self.current_span: RequestSpan = None
    
    # TODO: Implement context manager to track span
    def start_span(self, operation: str):
        """Start tracking a new operation."""
        pass
    
    def end_span(self, **metadata):
        """End the current span and add metadata."""
        pass
    
    def get_timeline(self) -> List[Dict]:
        """Get the timeline of all spans."""
        pass
```

### Solution

```python
class RequestTracer:
    """Trace requests through the RAG pipeline."""
    
    def __init__(self):
        self.spans: List[RequestSpan] = []
        self.current_span: RequestSpan = None
    
    def start_span(self, operation: str):
        """Start tracking a new operation."""
        self.current_span = RequestSpan(
            operation=operation,
            start_time=time.time()
        )
    
    def end_span(self, **metadata):
        """End the current span and add metadata."""
        if self.current_span:
            self.current_span.end_time = time.time()
            self.current_span.metadata.update(metadata)
            self.spans.append(self.current_span)
            self.current_span = None
    
    def get_timeline(self) -> List[Dict]:
        """Get the timeline of all spans."""
        return [
            {
                'operation': span.operation,
                'start': span.start_time,
                'duration_ms': span.duration * 1000,
                'metadata': span.metadata
            }
            for span in self.spans
        ]
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.current_span:
            self.end_span(error=str(exc_val) if exc_val else None)
```

## Exercise 2: Implement Health Checks

Create a health check system for RAG components.

```python
class ComponentHealth:
    """Health status of a component."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class RAGHealthChecker:
    """Check health of RAG system components."""
    
    def __init__(self, vector_store, llm, embedding_model):
        self.vector_store = vector_store
        self.llm = llm
        self.embedding_model = embedding_model
    
    async def check_vector_store(self) -> Dict[str, Any]:
        """Check vector store health."""
        # TODO: Implement health check
        pass
    
    async def check_llm(self) -> Dict[str, Any]:
        """Check LLM health."""
        # TODO: Implement health check
        pass
    
    async def check_embedding_model(self) -> Dict[str, Any]:
        """Check embedding model health."""
        # TODO: Implement health check
        pass
    
    async def check_all(self) -> Dict[str, Any]:
        """Run all health checks."""
        # TODO: Implement combined health check
        pass
```

### Solution

```python
class RAGHealthChecker:
    """Check health of RAG system components."""
    
    def __init__(self, vector_store, llm, embedding_model):
        self.vector_store = vector_store
        self.llm = llm
        self.embedding_model = embedding_model
    
    async def check_vector_store(self) -> Dict[str, Any]:
        """Check vector store health."""
        try:
            start = time.time()
            # Simple test query
            await self.vector_store.health_check()
            latency = time.time() - start
            
            return {
                'status': ComponentHealth.HEALTHY,
                'latency_ms': latency * 1000
            }
        except Exception as e:
            return {
                'status': ComponentHealth.UNHEALTHY,
                'error': str(e)
            }
    
    async def check_llm(self) -> Dict[str, Any]:
        """Check LLM health."""
        try:
            start = time.time()
            # Simple test prompt
            response = await self.llm.agenerate(["Hello"])
            latency = time.time() - start
            
            return {
                'status': ComponentHealth.HEALTHY,
                'latency_ms': latency * 1000
            }
        except Exception as e:
            return {
                'status': ComponentHealth.UNHEALTHY,
                'error': str(e)
            }
    
    async def check_embedding_model(self) -> Dict[str, Any]:
        """Check embedding model health."""
        try:
            start = time.time()
            embedding = self.embedding_model.encode("test")
            latency = time.time() - start
            
            return {
                'status': ComponentHealth.HEALTHY,
                'latency_ms': latency * 1000,
                'embedding_dim': len(embedding)
            }
        except Exception as e:
            return {
                'status': ComponentHealth.UNHEALTHY,
                'error': str(e)
            }
    
    async def check_all(self) -> Dict[str, Any]:
        """Run all health checks."""
        results = {
            'vector_store': await self.check_vector_store(),
            'llm': await self.check_llm(),
            'embedding_model': await self.check_embedding_model()
        }
        
        # Determine overall status
        statuses = [r['status'] for r in results.values()]
        
        if all(s == ComponentHealth.HEALTHY for s in statuses):
            overall = ComponentHealth.HEALTHY
        elif any(s == ComponentHealth.UNHEALTHY for s in statuses):
            overall = ComponentHealth.UNHEALTHY
        else:
            overall = ComponentHealth.DEGRADED
        
        return {
            'status': overall,
            'components': results,
            'timestamp': time.time()
        }
```

## Exercise 3: Implement Metrics Collection

Create a metrics collection system.

```python
from collections import defaultdict
import time

class RAGMetricsCollector:
    """Collect and aggregate RAG metrics."""
    
    def __init__(self):
        self.counters = defaultdict(int)
        self.histograms = defaultdict(list)
        self.gauges = {}
    
    def increment(self, name: str, value: int = 1):
        """Increment a counter."""
        pass
    
    def observe(self, name: str, value: float):
        """Add to histogram."""
        pass
    
    def set_gauge(self, name: str, value: float):
        """Set a gauge value."""
        pass
    
    def get_summary(self) -> Dict:
        """Get metrics summary."""
        pass
```

### Solution

```python
class RAGMetricsCollector:
    """Collect and aggregate RAG metrics."""
    
    def __init__(self):
        self.counters = defaultdict(int)
        self.histograms = defaultdict(list)
        self.gauges = {}
    
    def increment(self, name: str, value: int = 1):
        """Increment a counter."""
        self.counters[name] += value
    
    def observe(self, name: str, value: float):
        """Add to histogram."""
        self.histograms[name].append(value)
    
    def set_gauge(self, name: str, value: float):
        """Set a gauge value."""
        self.gauges[name] = value
    
    def get_summary(self) -> Dict:
        """Get metrics summary."""
        summary = {
            'counters': dict(self.counters),
            'gauges': dict(self.gauges),
            'histograms': {}
        }
        
        # Calculate histogram statistics
        for name, values in self.histograms.items():
            if values:
                summary['histograms'][name] = {
                    'count': len(values),
                    'min': min(values),
                    'max': max(values),
                    'mean': sum(values) / len(values),
                    'p50': sorted(values)[len(values) // 2],
                    'p95': sorted(values)[int(len(values) * 0.95)],
                    'p99': sorted(values)[int(len(values) * 0.99)]
                }
        
        return summary
    
    def reset(self):
        """Reset all metrics."""
        self.counters.clear()
        self.histograms.clear()
        self.gauges.clear()
```

## Exercise 4: Test Your Implementation

```python
# Test the tracing
with tracer as t:
    t.start_span("embed_query")
    time.sleep(0.1)  # Simulate work
    t.end_span(embedding_dim=384)
    
    t.start_span("retrieve")
    time.sleep(0.05)
    t.end_span(documents_found=10)
    
    t.start_span("generate")
    time.sleep(0.5)
    t.end_span(tokens=150)

print(tracer.get_timeline())

# Test health checker
import asyncio
results = asyncio.run(checker.check_all())
print(results)

# Test metrics
metrics.increment("requests_total")
metrics.observe("latency_ms", 150.5)
metrics.set_gauge("queue_size", 5)
print(metrics.get_summary())
```

## Expected Output

```json
[
  {
    "operation": "embed_query",
    "duration_ms": 100.0,
    "metadata": {"embedding_dim": 384}
  },
  {
    "operation": "retrieve", 
    "duration_ms": 50.0,
    "metadata": {"documents_found": 10}
  },
  {
    "operation": "generate",
    "duration_ms": 500.0,
    "metadata": {"tokens": 150}
  }
]
```

## Next Steps

- Add more sophisticated error handling
- Integrate with Prometheus/Grafana
- Add distributed tracing with OpenTelemetry
- Implement alerting based on metrics
