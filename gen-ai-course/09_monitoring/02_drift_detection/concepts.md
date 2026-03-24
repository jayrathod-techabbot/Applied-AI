# Drift Detection - Concepts

## What is Drift?

Drift refers to the gradual change in data distributions, model behavior, or system performance over time. In Generative AI systems, drift can significantly impact response quality and accuracy.

## Types of Drift

### 1. Data Drift

Data drift occurs when the input data distribution changes over time.

**Types:**
- **Feature Drift**: Changes in the statistical properties of input features
- **Target Drift**: Changes in the expected output distribution
- **Label Drift**: Changes in ground truth labels

**Examples:**
- User queries becoming more complex
- Document format changes
- New vocabulary or terminology emerging

### 2. Concept Drift

Concept drift happens when the relationship between input data and target variable changes.

**Types:**
- **Sudden Drift**: Abrupt changes (e.g., new policy, news event)
- **Gradual Drift**: Slow progressive changes (e.g., user behavior evolution)
- **Recurring Drift**: Periodic patterns (e.g., seasonal changes)
- **Blip Drift**: Temporary anomalies

### 3. Embedding Drift

Embedding drift occurs when vector representations change due to model updates.

**Causes:**
- Embedding model version changes
- Tokenizer updates
- Model fine-tuning

**Detection:**
- Monitor cluster structure over time
- Track retrieval result stability
- Compare embeddings before/after updates

### 4. Knowledge Base Staleness

Knowledge base staleness happens when indexed documents become outdated.

**Indicators:**
- Retrieval returns irrelevant results
- User feedback indicates outdated information
- Query topics expand beyond indexed content

## Drift Detection Methods

### Statistical Methods

| Method | Description | Use Case |
|--------|-------------|----------|
| Population Stability Index (PSI) | Measures distribution shift | Feature drift detection |
| Kolmogorov-Smirnov Test | Compares distributions | Continuous monitoring |
| Chi-Squared Test | Tests categorical changes | Class distribution changes |
| KL Divergence | Measures information loss | Distribution comparison |

### Monitoring Metrics

**Retrieval Metrics:**
- Recall@k changes
- Precision@k degradation
- Average similarity score decline
- Zero-result rate increase

**Generation Metrics:**
- Response length changes
- Token usage patterns
- Error rate variations
- User satisfaction scores

### Practical Detection Approaches

1. **Baseline Comparison**: Compare current distributions against established baselines
2. **Windowed Analysis**: Compare recent data windows against historical windows
3. **Ensemble Detection**: Use multiple detection methods for robustness
4. **User Feedback Integration**: Leverage explicit/implicit user signals

## Handling Drift

### Reactive Strategies

- **Retraining Triggers**: Automatically trigger model retraining when drift is detected
- **Fallback Systems**: Switch to simpler models when quality degrades
- **Human Escalation**: Route complex cases to humans

### Proactive Strategies

- **Continuous Monitoring**: Always track drift metrics
- **Canary Deployments**: Test changes with small user segments
- **A/B Testing**: Compare new and old versions in production
- **Versioned Knowledge Bases**: Maintain multiple document versions

## Tools for Drift Detection

- **Evidently AI**: Open-source drift detection
- **Amazon SageMaker Model Monitor**: AWS ML monitoring
- **Google Vertex AI Model Monitoring**: GCP ML monitoring
- **Seldon**: Open-source ML deployment and monitoring
- **Fiddler**: ML model explainability and monitoring

## Best Practices

1. **Establish Baselines**: Create reference distributions during stable periods
2. **Set Thresholds**: Define actionable drift thresholds
3. **Monitor Continuously**: Implement real-time drift detection
4. **Alert Appropriately**: Create alerts for significant drift
5. **Document Patterns**: Track drift patterns for better understanding
6. **Automate Responses**: Implement automated handling where possible

## Key Metrics to Track

- **Feature Distribution Statistics**: Mean, std, percentiles
- **Drift Scores**: PSI, KL divergence, Wasserstein distance
- **Retrieval Quality**: Recall, precision, similarity scores
- **User Engagement**: Click-through rates, session duration
- **Error Patterns**: Error types, frequency, severity
