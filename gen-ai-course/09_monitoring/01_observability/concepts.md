# Observability - Concepts

## Key Metrics for GenAI

### Performance Metrics
- **Latency**: Response time (P50, P95, P99)
- **Throughput**: Requests per second
- **Error Rate**: Failed requests percentage

### Cost Metrics
- **Token Usage**: Input and output tokens
- **API Costs**: Cost per request
- **Embedding Costs**: Vectorization costs

### Quality Metrics
- **Retrieval Precision**: Relevance of retrieved documents
- **Response Quality**: User satisfaction scores
- **Hallucination Rate**: Factually incorrect responses

## Logging Strategy

### Request Logging
- Timestamp
- User ID
- Request/Response
- Latency
- Cost

### Error Logging
- Stack traces
- Input validation failures
- API failures

## Tools

- **Prometheus/Grafana**: Metrics and dashboards
- **ELK Stack**: Log aggregation
- **LangSmith**: LLM-specific observability
- **OpenTelemetry**: Distributed tracing
