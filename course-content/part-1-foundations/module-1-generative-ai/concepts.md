# Module 1: Generative AI & Prompting — Core Concepts

## Table of Contents
- [1.1 What is Generative AI?](#11-what-is-generative-ai)
- [1.2 Prompt Engineering](#12-prompt-engineering)
- [1.3 Data Analysis with LLM Prompts](#13-data-analysis-with-llm-prompts)
- [1.4 Ethics, Considerations, and the Future of AI](#14-ethics-considerations-and-the-future-of-ai)

---

## 1.1 What is Generative AI?

Generative AI refers to artificial intelligence systems capable of creating novel content—text, images, code, audio, and video—by learning patterns from training data. Unlike discriminative models that classify or predict labels, generative models learn the underlying probability distribution of data and can sample from it to produce new outputs.

### Large Language Models (LLMs)

LLMs are transformer-based neural networks trained on massive text corpora using self-supervised learning. They predict the next token in a sequence, enabling fluent text generation, reasoning, and instruction following.

#### Key Architectural Components

| Component | Description |
|-----------|-------------|
| **Tokenizer** | Converts text into subword tokens (e.g., BPE, WordPiece) |
| **Embedding Layer** | Maps tokens to dense vector representations |
| **Transformer Blocks** | Stacked layers with self-attention and feed-forward networks |
| **Positional Encoding** | Injects sequence order information |
| **Attention Mechanism** | Computes weighted relevance between all token pairs |
| **Output Head** | Produces probability distribution over vocabulary |

```python
# Simplified transformer block structure
class TransformerBlock:
    def __init__(self, d_model, n_heads, d_ff):
        self.attention = MultiHeadAttention(d_model, n_heads)
        self.feed_forward = FeedForward(d_model, d_ff)
        self.norm1 = LayerNorm(d_model)
        self.norm2 = LayerNorm(d_model)
    
    def forward(self, x, mask=None):
        # Self-attention with residual connection
        attn_out = self.attention(x, x, x, mask)
        x = self.norm1(x + attn_out)
        
        # Feed-forward with residual connection
        ff_out = self.feed_forward(x)
        x = self.norm2(x + ff_out)
        return x
```

#### LLM Capabilities

| Capability | Examples |
|------------|----------|
| **Text Generation** | Articles, stories, code, emails |
| **Summarization** | Extractive and abstractive summarization |
| **Translation** | Cross-lingual text translation |
| **Question Answering** | Open-domain and closed-domain QA |
| **Code Generation** | Function synthesis, bug fixing, explanation |
| **Reasoning** | Mathematical, logical, and commonsense reasoning |
| **Instruction Following** | Task completion from natural language prompts |

#### LLM Limitations

| Limitation | Description | Mitigation |
|------------|-------------|------------|
| **Hallucinations** | Generates plausible but incorrect information | Ground with RAG, verification steps |
| **Knowledge Cutoff** | Training data has a fixed date | Use web search, fine-tune with recent data |
| **Context Window** | Limited input/output token capacity | Chunking, summarization, sliding windows |
| **Bias** | Reflects biases in training data | Careful prompting, output filtering, diverse data |
| **Reasoning Errors** | Struggles with complex multi-step logic | Chain-of-thought, decomposition, tool use |
| **Determinism** | Non-deterministic outputs (temperature) | Set temperature=0, use seed values |
| **Cost & Latency** | API calls can be expensive and slow | Caching, smaller models, batching |

```python
# Demonstrating temperature effect on outputs
from openai import OpenAI

client = OpenAI()

def generate_with_temperature(prompt, temperature):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
        max_tokens=50
    )
    return response.choices[0].message.content

# Low temperature: deterministic, focused
print(generate_with_temperature("List 3 benefits of exercise", temperature=0.1))

# High temperature: creative, varied
print(generate_with_temperature("Write a poem about exercise", temperature=0.9))
```

### Key Takeaways
- Generative AI creates novel content by learning data distributions
- LLMs use transformer architecture with self-attention mechanisms
- Capabilities span text generation, reasoning, coding, and more
- Limitations include hallucinations, bias, context limits, and knowledge cutoffs
- Understanding both capabilities and limitations is essential for production use

---

## 1.2 Prompt Engineering

Prompt engineering is the practice of designing inputs to guide LLMs toward desired outputs. It is both an art and a science—requiring understanding of model behavior, task decomposition, and iterative refinement.

### Core Principles

1. **Be Specific**: Clear, unambiguous instructions produce better results
2. **Provide Context**: Background information improves relevance
3. **Use Examples**: Demonstrations guide the model's output format
4. **Structure Prompts**: Use delimiters, sections, and formatting
5. **Iterate**: Test and refine prompts systematically

### Prompt Engineering Techniques

#### Zero-Shot Prompting

The model performs a task without any examples, relying solely on instructions.

```python
# Zero-shot classification
prompt = """Classify the sentiment of the following text as positive, negative, or neutral.

Text: "The product arrived late and was damaged during shipping."
Sentiment:"""

# Expected output: Negative
```

#### Few-Shot Prompting

Providing examples within the prompt to demonstrate the expected format and behavior.

```python
# Few-shot text classification
prompt = """Classify the intent of user queries:

Query: "What's the weather today?"
Intent: information_request

Query: "Reset my password"
Intent: account_action

Query: "Tell me a joke"
Intent: entertainment

Query: "Track my order #12345"
Intent: """

# Expected output: order_inquiry
```

#### Chain-of-Thought (CoT) Prompting

Encourages the model to break down reasoning steps before producing a final answer.

```python
# Chain-of-thought reasoning
prompt = """Solve this problem step by step:

A store has 120 apples. On Monday, they sell 1/4 of their stock. 
On Tuesday, they sell 1/3 of the remaining stock. 
How many apples are left?

Let's think step by step:
1. Initial stock: 120 apples
2. Monday sales: 120 × (1/4) = 30 apples sold
3. Remaining after Monday: 120 - 30 = 90 apples
4. Tuesday sales: 90 × (1/3) = 30 apples sold
5. Remaining after Tuesday: 90 - 30 = 60 apples

Answer: 60 apples

---

Now solve this:
A company has 500 employees. 20% work in engineering, 15% in sales, 
and the rest in other departments. How many employees work in other departments?

Let's think step by step:"""
```

#### ReAct (Reasoning + Acting)

Combines reasoning with tool use, alternating between thought and action steps.

```python
# ReAct prompt template
react_template = """You are an AI assistant that can use tools to answer questions.
Available tools: search, calculator, database_query

Answer the question by alternating between Thought and Action steps.
End with Final Answer.

Question: What is the population of Tokyo divided by 1000?

Thought: I need to find the population of Tokyo first.
Action: search("Tokyo population 2024")
Observation: Tokyo has approximately 14 million residents.

Thought: Now I need to divide 14,000,000 by 1000.
Action: calculator("14000000 / 1000")
Observation: 14000

Thought: I have the answer.
Final Answer: The population of Tokyo divided by 1000 is 14,000.

---

Question: {question}
"""
```

#### Role-Based Prompting

Assigning a specific role or persona to guide the model's behavior.

```python
# Role-based prompt
prompt = """You are a senior software engineer conducting a code review.
Your expertise includes Python, system design, and security best practices.

Review the following code for:
1. Potential bugs
2. Security vulnerabilities
3. Performance issues
4. Code style improvements

Code:
```python
def get_user_data(user_id):
    query = f"SELECT * FROM users WHERE id = {user_id}"
    result = db.execute(query)
    return result
```

Provide your review in a structured format."""
```

#### Structured Output Prompting

Forcing the model to produce parseable, structured output.

```python
# JSON output prompt
prompt = """Extract the following information from the text and return it as valid JSON:
- company_name (string)
- revenue (number)
- employees (number)
- industry (string)
- headquarters (string)

Text: "Apple Inc., headquartered in Cupertino, California, reported revenue of $383 billion 
in fiscal year 2023. The tech giant employs approximately 161,000 people worldwide."

JSON:"""

# Expected output:
# {
#   "company_name": "Apple Inc.",
#   "revenue": 383000000000,
#   "employees": 161000,
#   "industry": "Technology",
#   "headquarters": "Cupertino, California"
# }
```

### Advanced Prompt Patterns

#### Tree of Thoughts (ToT)

Explores multiple reasoning paths and selects the best one.

```python
# Tree of Thoughts pattern
prompt = """Consider multiple approaches to solve this problem:

Problem: Design a caching strategy for a high-traffic API.

Approach 1: [Describe first approach]
Pros: ...
Cons: ...

Approach 2: [Describe second approach]
Pros: ...
Cons: ...

Approach 3: [Describe third approach]
Pros: ...
Cons: ...

Evaluate each approach and recommend the best solution."""
```

#### Self-Consistency

Generate multiple outputs and select the most consistent answer.

```python
import openai

def self_consistency(prompt, n=5):
    """Generate multiple responses and find the most common answer."""
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        n=n,
        temperature=0.7
    )
    
    answers = [choice.message.content for choice in response.choices]
    
    # Find most common answer
    from collections import Counter
    most_common = Counter(answers).most_common(1)[0]
    return most_common
```

#### Prompt Chaining

Breaking complex tasks into sequential prompt steps.

```python
# Prompt chaining example
def analyze_document(document):
    # Step 1: Extract key sections
    extraction_prompt = f"Extract the main sections from this document:\n{document}"
    sections = call_llm(extraction_prompt)
    
    # Step 2: Summarize each section
    summaries = []
    for section in sections:
        summary_prompt = f"Summarize this section in 2-3 sentences:\n{section}"
        summaries.append(call_llm(summary_prompt))
    
    # Step 3: Generate overall analysis
    analysis_prompt = f"Based on these summaries, provide key insights:\n{summaries}"
    analysis = call_llm(analysis_prompt)
    
    return analysis
```

### Prompt Best Practices

| Practice | Description | Example |
|----------|-------------|---------|
| **Use delimiters** | Separate instructions from data | `"""`, `---`, `###` |
| **Specify format** | Define expected output structure | "Return as JSON with keys: ..." |
| **Set constraints** | Limit output scope | "In 3 bullet points..." |
| **Provide context** | Give background information | "You are analyzing Q3 financial data..." |
| **Use examples** | Show input-output pairs | Few-shot demonstrations |
| **Iterative refinement** | Test and improve prompts | A/B test prompt variants |
| **Handle edge cases** | Specify behavior for unusual inputs | "If uncertain, respond with..." |

### Key Takeaways
- Prompt engineering is essential for reliable LLM outputs
- Zero-shot, few-shot, and chain-of-thought are foundational techniques
- ReAct combines reasoning with tool use for complex tasks
- Structured output prompts enable programmatic integration
- Advanced patterns like ToT and self-consistency improve reliability
- Systematic testing and iteration are key to prompt optimization

---

## 1.3 Data Analysis with LLM Prompts

LLMs can serve as powerful data analysis assistants, helping with data exploration, transformation, visualization, and insight generation.

### Use Cases

| Use Case | Description |
|----------|-------------|
| **Data Cleaning** | Identify missing values, outliers, inconsistencies |
| **Data Transformation** | Generate code for reshaping, aggregating, merging |
| **Exploratory Analysis** | Suggest statistical tests, correlations, patterns |
| **Visualization** | Generate plotting code (matplotlib, seaborn, plotly) |
| **Insight Generation** | Summarize findings, identify trends |
| **SQL Generation** | Convert natural language to SQL queries |
| **Report Writing** | Create narrative summaries of analysis |

### Data Cleaning with LLMs

```python
# Data cleaning prompt
prompt = """You are a data engineer. Analyze the following CSV sample and suggest cleaning steps.

CSV Sample:
```csv
name,age,email,salary,join_date
John Smith,34,john@email.com,75000,2020-01-15
Jane Doe,,jane.doe@email,82000,2019-06-20
Bob Wilson,45,bob@email.com,,2021-03-10
Alice Brown,28,alice@email.com,65000,invalid_date
,31,missing@email.com,71000,2020-11-05
```

Issues found and recommended cleaning steps:
1. Missing values: ...
2. Format issues: ...
3. Data type corrections: ...

Provide Python pandas code to clean this data."""
```

### SQL Query Generation

```python
# Text-to-SQL prompt
prompt = """Given the following database schema, write a SQL query to answer the question.

Schema:
- employees (id, name, department_id, salary, hire_date)
- departments (id, name, location)
- projects (id, name, department_id, budget, start_date)

Question: "Find the average salary per department for departments located in New York, 
sorted by average salary in descending order."

SQL Query:"""

# Expected output:
# SELECT d.name, AVG(e.salary) as avg_salary
# FROM employees e
# JOIN departments d ON e.department_id = d.id
# WHERE d.location = 'New York'
# GROUP BY d.name
# ORDER BY avg_salary DESC;
```

### Data Visualization Code Generation

```python
# Visualization prompt
prompt = """Generate Python code using matplotlib and seaborn to create the following visualization:

Dataset: Monthly sales data for 2023
```python
import pandas as pd
data = {
    'month': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
              'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
    'sales': [45000, 52000, 48000, 61000, 55000, 67000,
              72000, 69000, 58000, 63000, 71000, 85000]
}
df = pd.DataFrame(data)
```

Requirements:
- Create a line chart with markers
- Add a trend line
- Include annotations for peak and lowest months
- Use a professional color scheme
- Add grid lines and proper labels
"""
```

### Statistical Analysis Assistant

```python
# Statistical analysis prompt
prompt = """You are a data scientist. Analyze the following dataset and provide statistical insights.

Dataset Summary:
- 10,000 customer records
- Features: age, income, purchase_frequency, customer_lifetime_value, churn_status
- Target: churn_status (binary: 0=retained, 1=churned)

Perform the following analysis:
1. Descriptive statistics for each feature
2. Correlation analysis between features and churn
3. Suggest appropriate statistical tests
4. Recommend a modeling approach for churn prediction

Provide Python code using pandas, scipy, and scikit-learn."""
```

### Best Practices for Data Analysis with LLMs

1. **Provide Schema Context**: Always include data structure, types, and sample rows
2. **Specify Output Format**: Request code, explanations, or both
3. **Validate Generated Code**: LLM-generated code should be tested before production use
4. **Use Iterative Refinement**: Start with exploratory prompts, then drill down
5. **Combine with Tools**: Use LLMs alongside actual data processing libraries
6. **Handle Sensitive Data**: Never send PII or confidential data to public LLM APIs

### Key Takeaways
- LLMs excel at generating data analysis code and explaining results
- Text-to-SQL and visualization code generation are high-value use cases
- Always validate LLM-generated code against actual data
- Combine LLM reasoning with proper data processing pipelines
- Be cautious with sensitive data when using cloud-based LLMs

---

## 1.4 Ethics, Considerations, and the Future of AI

As AI systems become more capable and widespread, ethical considerations are paramount for responsible development and deployment.

### Key Ethical Concerns

#### Bias and Fairness

LLMs can perpetuate and amplify biases present in training data.

| Bias Type | Description | Example |
|-----------|-------------|---------|
| **Representation Bias** | Under/over-representation of groups | Gender bias in profession associations |
| **Historical Bias** | Reflects past societal inequalities | Racial stereotypes in text generation |
| **Measurement Bias** | Flawed feature selection | Using zip codes as proxy for creditworthiness |
| **Aggregation Bias** | One-size-fits-all models | Medical models not accounting for demographic differences |
| **Evaluation Bias** | Biased benchmark datasets | NLP benchmarks skewed toward certain dialects |

```python
# Detecting bias in model outputs
def test_model_bias(prompt_template, demographic_groups):
    """Test model outputs for bias across demographic groups."""
    results = {}
    for group in demographic_groups:
        prompt = prompt_template.format(group=group)
        response = call_llm(prompt)
        results[group] = analyze_sentiment(response)
    
    # Compare results for disparity
    return check_statistical_parity(results)

# Example usage
prompt = "Write a short paragraph about a {group} person who is a doctor."
groups = ["young", "elderly", "male", "female"]
test_model_bias(prompt, groups)
```

#### Transparency and Explainability

| Principle | Description |
|-----------|-------------|
| **Model Transparency** | Disclose model capabilities, limitations, and training data |
| **Decision Explainability** | Provide reasoning for AI-generated decisions |
| **Uncertainty Communication** | Express confidence levels in outputs |
| **Auditability** | Enable third-party review of AI systems |

#### Privacy Concerns

| Risk | Mitigation |
|------|------------|
| **Training Data Leakage** | Differential privacy, data filtering |
| **Prompt Data Collection** | Review provider privacy policies, use enterprise options |
| **PII in Outputs** | Output filtering, redaction pipelines |
| **Membership Inference** | Regularization, access controls |

#### Misuse and Safety

| Concern | Examples | Mitigations |
|---------|----------|-------------|
| **Misinformation** | Fake news, deepfakes | Content watermarking, detection tools |
| **Malicious Use** | Phishing, malware generation | Usage monitoring, content filters |
| **Automation Bias** | Over-reliance on AI outputs | Human-in-the-loop, verification steps |
| **Job Displacement** | Workforce disruption | Reskilling programs, augmentation focus |

### Responsible AI Framework

```
Responsible AI Principles:
├── Fairness
│   ├── Bias detection and mitigation
│   ├── Diverse training data
│   └── Regular fairness audits
├── Transparency
│   ├── Model documentation
│   ├── Decision explainability
│   └── Clear AI disclosure
├── Accountability
│   ├── Human oversight
│   ├── Error reporting mechanisms
│   └── Clear responsibility chains
├── Privacy
│   ├── Data minimization
│   ├── Consent management
│   └── Secure data handling
└── Safety
    ├── Content filtering
    ├── Usage monitoring
    └── Incident response plans
```

### Regulatory Landscape

| Regulation | Region | Key Requirements |
|------------|--------|------------------|
| **EU AI Act** | European Union | Risk-based classification, transparency, human oversight |
| **NIST AI RMF** | United States | Voluntary framework for risk management |
| **China AI Regulations** | China | Algorithm registration, content controls |
| **UK AI Safety Framework** | United Kingdom | Pro-innovation approach, sector-specific guidance |
| **Canada AIDA** | Canada | Risk management, transparency, accountability |

### The Future of Generative AI

#### Emerging Trends

| Trend | Description | Impact |
|-------|-------------|--------|
| **Multimodal Models** | Unified models handling text, image, audio, video | Richer interactions, new applications |
| **Agentic AI** | Autonomous systems that plan and execute tasks | Workflow automation, complex problem solving |
| **Small Language Models** | Efficient, domain-specific models | Lower cost, privacy, edge deployment |
| **Neuro-Symbolic AI** | Combining neural networks with symbolic reasoning | Improved reasoning, verifiability |
| **AI Alignment** | Ensuring AI systems follow human intent | Safer, more reliable systems |
| **Open Source AI** | Community-driven model development | Democratization, transparency |

#### Skills for the AI Era

| Skill Category | Specific Skills |
|----------------|-----------------|
| **Technical** | Prompt engineering, RAG, fine-tuning, AI system design |
| **Analytical** | Critical evaluation, bias detection, output validation |
| **Ethical** | Responsible AI practices, regulatory compliance |
| **Domain** | Industry-specific AI applications, workflow integration |

### Key Takeaways
- AI bias can perpetuate and amplify societal inequalities
- Transparency, accountability, and privacy are core ethical principles
- Regulatory frameworks are evolving rapidly across jurisdictions
- Responsible AI requires technical, organizational, and governance measures
- The future of AI includes multimodal models, agentic systems, and improved alignment
- Developers must balance innovation with ethical responsibility

---

## Summary

This module covered the foundations of Generative AI and Prompting:

1. **Generative AI** creates novel content using learned patterns; LLMs are the most prominent examples with significant capabilities and important limitations
2. **Prompt Engineering** is essential for reliable outputs, with techniques ranging from zero-shot to advanced patterns like ReAct and Tree of Thoughts
3. **Data Analysis with LLMs** enables code generation, SQL queries, visualization, and insight extraction—but requires validation
4. **Ethics and Responsibility** must be central to AI development, addressing bias, transparency, privacy, and regulatory compliance

Master these foundations before proceeding to LangChain, RAG, and agentic systems in subsequent modules.
