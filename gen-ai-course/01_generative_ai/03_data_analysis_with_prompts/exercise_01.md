# Exercise 01: Building an LLM-Powered Data Analysis Pipeline

## Task

Create a Python script that builds a complete data analysis pipeline using LLMs.

### Requirements

1. **Data Loader**: Load data from CSV/JSON files
2. **Prompt Builder**: Create prompts for different analysis types
3. **Batch Processor**: Handle large datasets in chunks
4. **Results Aggregator**: Combine and summarize results

### Features to Implement

1. **Sentiment Analysis Pipeline**
   - Load customer reviews
   - Analyze sentiment
   - Categorize by sentiment score

2. **Trend Analysis Pipeline**
   - Extract time-series data
   - Identify patterns
   - Generate insights

3. **Data Cleaning Pipeline**
   - Detect anomalies
   - Suggest corrections
   - Validate results

### Deliverable

A Python module with:
- Data loader functions
- Analysis prompt templates
- Batch processing logic
- Results aggregation
- Error handling

### Example Usage

```python
from analyzer import DataAnalyzer

analyzer = DataAnalyzer()
results = analyzer.analyze_csv("reviews.csv", "sentiment")
print(results.summary)
```
