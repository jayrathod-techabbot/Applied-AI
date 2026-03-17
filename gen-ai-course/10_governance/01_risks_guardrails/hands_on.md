# Hands-On: AI Guardrails Implementation

This guide provides practical hands-on examples for implementing AI guardrails.

---

## Table of Contents

1. [Guardrails AI Setup](#guardrails-ai-setup)
2. [Azure AI Content Safety](#azure-ai-content-safety)
3. [Use Case Examples](#use-case-examples)

---

## Guardrails AI Setup

### Installation

```bash
# Install Guardrails AI
pip install guardrails-ai

# Install additional validators
pip install guardrails-hub
```

### Basic Setup Steps

```python
# Step 1: Import Guardrails
from guardrails import Guard
from guardrails.hub import ToxicLanguage, SensitiveTopics, PII

# Step 2: Create a Guard with validators
guard = Guard().use(
    ToxicLanguage,
    threshold=0.5,
    on_fail="exception"
)

# Step 3: Use with your LLM
def safe_completion(prompt: str) -> str:
    # Validate input
    guard.validate(prompt)
    
    # Call your LLM
    response = llm_call(prompt)
    
    # Validate output
    guard.validate(response)
    
    return response
```

### Configuration File (rail.yml)

```yaml
# rail.yml
name: safe_ai_assistant
description: AI assistant with safety guardrails

prompts:
  - source: |
      You are a helpful assistant.
      {{prompt}}
    variables:
      - prompt

validators:
  toxic_language:
    hub: guardrails/ ToxicLanguage
    threshold: 0.5
    
  pii:
    hub: guardrails/PII
    entities: ["SSN", "EMAIL", "PHONE"]
    
output:
  type: string
```

---

## Azure AI Content Safety

### Prerequisites

1. Azure subscription
2. Azure AI Content Safety resource
3. API key and endpoint

### Installation

```bash
pip install azure-ai-contentsafety
```

### Configuration

```python
import os
from azure.ai.contentsafety import ContentSafetyClient
from azure.ai.contentsafety.models import TextCategory
from azure.core.credentials import AzureKeyCredential

# Environment variables
AZURE_CONTENT_SAFETY_KEY = os.getenv("AZURE_CONTENT_SAFETY_KEY")
AZURE_CONTENT_SAFETY_ENDPOINT = os.getenv("AZURE_CONTENT_SAFETY_ENDPOINT")

# Create client
client = ContentSafetyClient(
    endpoint=AZURE_CONTENT_SAFETY_ENDPOINT,
    credential=AzureKeyCredential(AZURE_CONTENT_SAFETY_KEY)
)
```

### Azure Content Safety Demo

```python
"""
Azure AI Content Safety - Hands-On Demo
"""

import os
from azure.ai.contentsafety import ContentSafetyClient
from azure.ai.contentsafety.models import TextCategory, AnalyzeTextOptions
from azure.core.credentials import AzureKeyCredential

class AzureContentSafety:
    """Azure Content Safety wrapper."""
    
    def __init__(self, endpoint: str, key: str):
        self.client = ContentSafetyClient(
            endpoint=endpoint,
            credential=AzureKeyCredential(key)
        )
    
    def analyze_text(self, text: str) -> dict:
        """Analyze text for harmful content."""
        request = AnalyzeTextOptions(text=text)
        
        response = self.client.analyze_text(request)
        
        results = {
            "hate_fairness": None,
            "self_harm": None,
            "sexual": None,
            "violence": None
        }
        
        for analysis in response.categories_analysis:
            if analysis.category == TextCategory.HATE_FAIRNESS:
                results["hate_fairness"] = analysis.severity
            elif analysis.category == TextCategory.SELF_HARM:
                results["self_harm"] = analysis.severity
            elif analysis.category == TextCategory.SEXUAL:
                results["sexual"] = analysis.severity
            elif analysis.category == TextCategory.VIOLENCE:
                results["violence"] = analysis.severity
        
        return results
    
    def is_safe(self, text: str, threshold: int = 2) -> tuple:
        """Check if text is safe."""
        results = self.analyze_text(text)
        
        # Check all categories
        for category, severity in results.items():
            if severity and severity >= threshold:
                return False, f"Unsafe: {category} (severity: {severity})"
        
        return True, "Safe"


def demo_azure_content_safety():
    """Demonstrate Azure Content Safety."""
    
    # Initialize (use environment variables in production)
    endpoint = os.getenv("AZURE_CONTENT_SAFETY_ENDPOINT", "https://your-resource.cognitiveservices.azure.com/")
    key = os.getenv("AZURE_CONTENT_SAFETY_KEY", "your-api-key")
    
    safety = AzureContentSafety(endpoint, key)
    
    # Test cases
    test_texts = [
        "Hello, how can I help you today?",
        "All people from that group are terrible",
        "I'm feeling really hopeless and want to hurt myself"
    ]
    
    for text in test_texts:
        is_safe, message = safety.is_safe(text)
        print(f"Text: {text}")
        print(f"Result: {message}")
        print("-" * 40)


if __name__ == "__main__":
    demo_azure_content_safety()
```

### Azure Deployment (ARM Template)

```json
{
  "$schema": "https://schema.management.azure.com/schemas/2019-04-01/deploymentTemplate.json#",
  "contentVersion": "1.0.0.0",
  "parameters": {
    "contentSafetyName": {
      "type": "string",
      "defaultValue": "contentSafety"
    },
    "location": {
      "type": "string",
      "defaultValue": "eastus"
    }
  },
  "resources": [
    {
      "type": "Microsoft.CognitiveServices/accounts",
      "apiVersion": "2023-05-01",
      "name": "[parameters('contentSafetyName')]",
      "location": "[parameters('location')]",
      "kind": "ContentSafety",
      "sku": {
        "name": "S0"
      },
      "properties": {
        "publicNetworkAccess": "Enabled"
      }
    }
  ]
}
```

---

## Use Case Examples

### Use Case 1: Customer Service Chatbot

```python
"""
Customer Service Chatbot with Guardrails
"""

from guardrails import Guard
from guardrails.hub import ToxicLanguage, PII, SensitiveTopics

class CustomerServiceGuardrails:
    """Guardrails for customer service chatbot."""
    
    def __init__(self):
        # Input guardrails
        self.input_guard = Guard().use(
            ToxicLanguage,
            threshold=0.6,
            on_fail="exception"
        ).use(
            SensitiveTopics,
            topics=["legal_advice", "medical_advice"],
            on_fail="exception"
        )
        
        # Output guardrails
        self.output_guard = Guard().use(
            PII,
            entities=["SSN", "CREDIT_CARD", "BANK_ACCOUNT"],
            on_fail="filter"
        )
    
    def validate_input(self, user_input: str):
        """Validate user input."""
        return self.input_guard.validate(user_input)
    
    def validate_output(self, response: str):
        """Validate AI response."""
        return self.output_guard.validate(response)
    
    def process_message(self, user_input: str, llm_response: str) -> str:
        """Process message with guardrails."""
        # Validate input
        self.validate_input(user_input)
        
        # Validate output
        self.validate_output(llm_response)
        
        return llm_response
```

### Use Case 2: Content Moderation

```python
"""
Content Moderation System
"""

class ContentModerator:
    """Moderate user-generated content."""
    
    def __init__(self, azure_safety=None, guardrails=None):
        self.azure_safety = azure_safety
        self.guardrails = guardrails
    
    def moderate(self, content: str) -> dict:
        """Moderate content and return result."""
        result = {
            "is_safe": True,
            "reasons": [],
            "severity_scores": {}
        }
        
        # Azure Content Safety check
        if self.azure_safety:
            is_safe, message = self.azure_safety.is_safe(content)
            if not is_safe:
                result["is_safe"] = False
                result["reasons"].append(message)
                
                # Get detailed scores
                scores = self.azure_safety.analyze_text(content)
                result["severity_scores"] = scores
        
        # Guardrails check
        if self.guardrails and result["is_safe"]:
            try:
                self.guardrails.validate(content)
            except Exception as e:
                result["is_safe"] = False
                result["reasons"].append(str(e))
        
        return result
```

### Use Case 3: Hiring Tool Bias Detection

```python
"""
Bias Detection for Hiring AI
"""

class BiasDetector:
    """Detect bias in hiring-related content."""
    
    BIAS_INDICATORS = {
        "gender": ["he", "she", "man", "woman", "male", "female"],
        "age": ["young", "old", "senior", "junior", "years experience"],
        "race": ["race", "ethnicity", "nationality", "color"],
        "disability": ["disability", "handicap", "able-bodied"]
    }
    
    def __init__(self):
        self.guard = Guard().use(
            SensitiveTopics,
            topics=["age_discrimination", "gender_discrimination"],
            on_fail="exception"
        )
    
    def check_for_bias(self, text: str) -> dict:
        """Check text for potential bias indicators."""
        text_lower = text.lower()
        
        detected_bias = {}
        
        for category, indicators in self.BIAS_INDICATORS.items():
            matches = [ind for ind in indicators if ind in text_lower]
            if matches:
                detected_bias[category] = matches
        
        return {
            "has_bias": len(detected_bias) > 0,
            "categories": detected_bias
        }
    
    def analyze_job_description(self, job_desc: str) -> dict:
        """Analyze job description for bias."""
        # Check for bias indicators
        bias_result = self.check_for_bias(job_desc)
        
        return {
            "job_description": job_desc[:100] + "...",
            "bias_analysis": bias_result,
            "recommendation": "Review for bias" if bias_result["has_bias"] else "No obvious bias detected"
        }
```

---

## Testing Guardrails

```python
"""
Test Suite for Guardrails
"""

import pytest

def test_toxic_content_blocked():
    """Test that toxic content is blocked."""
    guard = Guard().use(ToxicLanguage, threshold=0.5)
    
    toxic_input = "You are the worst person ever and everyone hates you"
    
    with pytest.raises(Exception):
        guard.validate(toxic_input)

def test_safe_content_allowed():
    """Test that safe content passes."""
    guard = Guard().use(ToxicLanguage, threshold=0.5)
    
    safe_input = "Can you help me with my homework?"
    
    result = guard.validate(safe_input)
    assert result is not None

def test_pii_filtering():
    """Test that PII is filtered."""
    guard = Guard().use(PII, on_fail="filter")
    
    input_with_pii = "My SSN is 123-45-6789 and email is test@example.com"
    
    result = guard.validate(input_with_pii)
    # Should filter or redact PII
```

---

## Best Practices

1. **Defense in Depth**: Use multiple guardrail layers
2. **Fail-Safe Defaults**: Default to blocking uncertain content
3. **Continuous Monitoring**: Log and analyze guardrail triggers
4. **Regular Updates**: Keep validators and thresholds current
5. **Human Oversight**: Have human review for edge cases
6. **Testing**: Regularly test with adversarial examples
