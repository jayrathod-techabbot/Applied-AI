# Hands-On: Responsible AI Implementation

This guide provides practical implementation examples for responsible AI.

---

## Table of Contents

1. [Fairness Implementation](#fairness-implementation)
2. [Bias Detection](#bias-detection)
3. [Transparency Tools](#transparency-tools)
4. [Audit Logging](#audit-logging)

---

## Fairness Implementation

### Using Fairlearn

```python
"""
Fairness with Fairlearn
"""
from fairlearn.metrics import MetricFrame, selection_rate, equalized_odds_difference
from sklearn.metrics import accuracy_score

# Example data
y_true = [0, 1, 0, 1, 0, 1, 0, 1]
y_pred = [0, 1, 0, 0, 0, 1, 1, 1]
sensitive_features = ["A", "A", "B", "B", "A", "B", "A", "B"]

# Calculate metrics by group
metric_frame = MetricFrame(
    metrics={"accuracy": accuracy_score, "selection_rate": selection_rate},
    y_true=y_true,
    y_pred=y_pred,
    sensitive_features=sensitive_features
)

print("Metrics by group:")
print(metric_frame.by_group)

# Calculate fairness metrics
eodd = equalized_odds_difference(y_true, y_pred, sensitive_features=sensitive_features)
print(f"\nEqualized Odds Difference: {eodd:.3f}")
```

### Bias Mitigation with Fairlearn

```python
"""
Bias Mitigation Example
"""
from fairlearn.reductions import ExponentiatedGradient, DemographicParity
from sklearn.linear_model import LogisticRegression

# Setup
constraint = DemographicParity()
classifier = LogisticRegression()

# Apply ExponentiatedGradient
eg = ExponentiatedGradient(classifier, constraint)
eg.fit(X_train, y_train, sensitive_features=sensitive_features)

# Get predictions
y_predMitigated = eg.predict(X_test)
```

---

## Bias Detection

### Text Bias Detection

```python
"""
Bias Detection in Text
"""
import re
from typing import Dict, List

class TextBiasDetector:
    """Detect potential bias in text."""
    
    # Common bias indicators
    BIAS_PATTERNS = {
        "gender": {
            "patterns": [r"\bhe\b", r"\bshe\b", r"\bman\b", r"\bwoman\b"],
            "neutral": ["they", "person", "individual"]
        },
        "age": {
            "patterns": [r"\byoung\b", r"\bold\b", r"\bsenior\b", r"\bjunior\b"],
            "neutral": ["person", "individual"]
        },
        "disability": {
            "patterns": [r"\bdisabled\b", r"\bhandicap\b", r"\bable-bodied\b"],
            "neutral": ["person with a disability"]
        }
    }
    
    def detect_bias(self, text: str) -> Dict:
        """Detect potential bias in text."""
        text_lower = text.lower()
        findings = {}
        
        for category, info in self.BIAS_PATTERNS.items():
            matches = []
            for pattern in info["patterns"]:
                if re.search(pattern, text_lower):
                    matches.append(pattern)
            
            if matches:
                findings[category] = {
                    "matches": matches,
                    "suggestion": f"Consider using: {', '.join(info['neutral'])}"
                }
        
        return {
            "has_bias": len(findings) > 0,
            "findings": findings
        }

# Usage
detector = TextBiasDetector()
result = detector.detect_bias("The engineer should be strong and handle the physical work.")
print(result)
```

---

## Transparency Tools

### Model Card Generator

```python
"""
Model Card Generator
"""
from datetime import datetime
from typing import Dict, Any, List
import json

class ModelCardGenerator:
    """Generate model cards for AI systems."""
    
    def __init__(self, model_name: str):
        self.model_name = model_name
        self.card = {
            "model_name": model_name,
            "version": "1.0.0",
            "created": datetime.now().isoformat(),
            "overview": {},
            "training_data": {},
            "performance": {},
            "ethical_considerations": {},
            "limitations": [],
            "known_biases": []
        }
    
    def set_overview(self, description: str, use_cases: List[str], users: List[str]):
        """Set model overview."""
        self.card["overview"] = {
            "description": description,
            "use_cases": use_cases,
            "intended_users": users
        }
    
    def set_training_data(self, data_sources: List[str], size: str, date: str):
        """Set training data information."""
        self.card["training_data"] = {
            "sources": data_sources,
            "size": size,
            "collection_date": date
        }
    
    def add_known_bias(self, bias: str, description: str):
        """Add known bias."""
        self.card["known_biases"].append({
            "bias": bias,
            "description": description
        })
    
    def add_limitation(self, limitation: str):
        """Add model limitation."""
        self.card["limitations"].append(limitation)
    
    def generate(self) -> str:
        """Generate markdown model card."""
        md = []
        md.append(f"# Model Card: {self.model_name}")
        md.append("")
        
        # Overview
        if self.card["overview"]:
            md.append("## Overview")
            md.append(self.card["overview"]["description"])
            md.append(f"\n**Use Cases:** {', '.join(self.card['overview']['use_cases'])}")
            md.append("")
        
        # Known Biases
        if self.card["known_biases"]:
            md.append("## Known Biases")
            for bias in self.card["known_biases"]:
                md.append(f"- **{bias['bias']}**: {bias['description']}")
            md.append("")
        
        # Limitations
        if self.card["limitations"]:
            md.append("## Limitations")
            for lim in self.card["limitations"]:
                md.append(f"- {lim}")
            md.append("")
        
        return "\n".join(md)

# Usage
card_gen = ModelCardGenerator("Customer Sentiment Analyzer")
card_gen.set_overview(
    "Analyzes customer feedback for sentiment",
    ["Customer service", "Product feedback"],
    ["Support teams", "Product managers"]
)
card_gen.add_known_bias(
    "Geographic bias",
    "Training data over-represents North American English"
)
card_gen.add_limitation("May not accurately detect sarcasm")

print(card_gen.generate())
```

---

## Audit Logging

### AI Decision Logger

```python
"""
AI Decision Audit Logger
"""
from datetime import datetime
from typing import Any, Dict, Optional
import json
import hashlib

class AuditLogger:
    """Log AI decisions for accountability."""
    
    def __init__(self, log_file: str = "audit.log"):
        self.log_file = log_file
    
    def log_decision(
        self,
        decision_id: str,
        input_data: Any,
        output_data: Any,
        model_name: str,
        user_id: Optional[str] = None,
        metadata: Optional[Dict] = None
    ):
        """Log an AI decision."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "decision_id": decision_id,
            "model_name": model_name,
            "user_id": user_id,
            "input_hash": self._hash_data(input_data),
            "output_hash": self._hash_data(output_data),
            "metadata": metadata or {}
        }
        
        # Append to log file
        with open(self.log_file, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
        
        return log_entry
    
    def _hash_data(self, data: Any) -> str:
        """Create hash of data for privacy."""
        data_str = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(data_str.encode()).hexdigest()[:16]
    
    def get_logs(self, limit: int = 100) -> list:
        """Retrieve recent logs."""
        logs = []
        try:
            with open(self.log_file, "r") as f:
                for line in f:
                    logs.append(json.loads(line))
                    if len(logs) >= limit:
                        break
        except FileNotFoundError:
            pass
        return logs

# Usage
logger = AuditLogger("ai_audit.log")
logger.log_decision(
    decision_id="dec_12345",
    input_data={"text": "I love this product!"},
    output_data={"sentiment": "positive", "confidence": 0.95},
    model_name="sentiment-v2",
    user_id="user_789",
    metadata={"api_version": "v1"}
)

print("Decision logged successfully")
```

---

## Best Practices

1. **Start early** - Consider ethics from design phase
2. **Be transparent** - Document model limitations
3. **Test regularly** - Continuously check for bias
4. **Engage stakeholders** - Include diverse perspectives
5. **Monitor in production** - Track fairness metrics
6. **Iterate** - Improve based on feedback
