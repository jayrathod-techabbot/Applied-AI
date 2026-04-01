# Module 10: AI Governance & Compliance — Core Concepts

## Table of Contents
- [10.1 Risks and Guardrails in Production AI](#101-risks-and-guardrails-in-production-ai)
- [10.2 Responsible AI Principles](#102-responsible-ai-principles)
- [10.3 Regulatory Compliance](#103-regulatory-compliance)

---

## 10.1 Risks and Guardrails in Production AI

### AI Risk Taxonomy

Production AI systems face a unique set of risks that traditional software does not. Understanding this taxonomy is the first step toward building trustworthy systems.

| Risk Category | Description | Example | Severity |
|---|---|---|---|
| **Hallucination** | Model generates plausible but factually incorrect output | LLM cites non-existent research papers | High |
| **Bias** | Systematic unfairness toward certain groups | Hiring model penalizes resumes from specific demographics | High |
| **Prompt Injection** | Malicious input manipulates model behavior | User inserts "ignore previous instructions" to bypass filters | Critical |
| **Data Leakage** | Sensitive training data exposed in outputs | Model reproduces PII from its training set | Critical |
| **Toxicity** | Generation of harmful, offensive, or dangerous content | Chatbot produces hate speech or self-harm instructions | High |
| **Over-reliance** | Users blindly trust AI outputs without verification | Doctor follows incorrect AI diagnosis without review | Medium |
| **Model Drift** | Performance degrades as data distributions shift | Fraud detection model loses accuracy over time | Medium |
| **Adversarial Attacks** | Crafted inputs designed to fool the model | Slightly perturbed image misclassified by vision model | High |

### Content Filtering

Content filtering acts as a safety layer between the model and the end user.

```python
# Example: Content filtering pipeline using OpenAI's Moderation API
import openai

class ContentFilter:
    def __init__(self):
        self.blocked_categories = {
            "hate": 0.5,
            "self-harm": 0.3,
            "sexual": 0.5,
            "violence": 0.5,
        }

    def check_input(self, user_input: str) -> dict:
        """Pre-screen user input before it reaches the LLM."""
        response = openai.moderations.create(input=user_input)
        result = response.results[0]

        flagged = False
        reasons = []

        for category, threshold in self.blocked_categories.items():
            score = getattr(result.category_scores, category, 0)
            if score > threshold:
                flagged = True
                reasons.append(category)

        return {
            "flagged": flagged,
            "reasons": reasons,
            "scores": result.category_scores.model_dump(),
        }

    def check_output(self, model_output: str) -> dict:
        """Post-screen model output before it reaches the user."""
        return self.check_input(model_output)
```

### Guardrails Architecture

Guardrails are programmatic constraints that enforce safe, predictable AI behavior. They operate at both input and output stages.

#### Input Guardrails
- **Length validation** — reject excessively long prompts
- **Sanitization** — strip injection patterns and control characters
- **Topic filtering** — block disallowed domains
- **PII detection** — redact personal information before processing

#### Output Guardrails
- **Format validation** — ensure structured output conforms to schema
- **Factuality checks** — cross-reference claims against knowledge bases
- **Toxicity screening** — filter harmful content from responses
- **Compliance tagging** — flag outputs that may violate regulations

```python
# Example: Input/Output validation guardrail
import re
from pydantic import BaseModel, ValidationError
from typing import Optional

class GuardrailConfig(BaseModel):
    max_input_length: int = 4096
    blocked_patterns: list[str] = [
        r"ignore\s+(all\s+)?previous\s+instructions",
        r"system\s*prompt\s*:",
        r"reveal\s+(your\s+)?instructions",
    ]
    pii_patterns: dict[str, str] = {
        "email": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
        "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
        "phone": r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",
    }

class GuardrailsEngine:
    def __init__(self, config: GuardrailConfig = None):
        self.config = config or GuardrailConfig()

    def validate_input(self, user_input: str) -> tuple[bool, str]:
        # Length check
        if len(user_input) > self.config.max_input_length:
            return False, "Input exceeds maximum length"

        # Prompt injection detection
        for pattern in self.config.blocked_patterns:
            if re.search(pattern, user_input, re.IGNORECASE):
                return False, "Input contains disallowed pattern"

        return True, user_input

    def redact_pii(self, text: str) -> str:
        for pii_type, pattern in self.config.pii_patterns.items():
            text = re.sub(pattern, f"[REDACTED_{pii_type.upper()}]", text)
        return text

    def validate_output(self, output: str, expected_format: Optional[str] = None) -> tuple[bool, str]:
        # Basic safety checks
        if not output or not output.strip():
            return False, "Empty output"

        # PII redaction on output
        sanitized = self.redact_pii(output)
        return True, sanitized
```

### NeMo Guardrails

NVIDIA's NeMo Guardrails is an open-source toolkit for adding programmable guardrails to LLM-based applications.

```yaml
# Colang configuration for NeMo Guardrails
define user greeting
  "hello"
  "hi"
  "hey"

define flow greeting
  user greeting
  bot greeting_message

define bot greeting_message
  "Hello! How can I help you today?"

define flow self_check_input
  user said something
  $input_check = execute self_check_input_action
  if $input_check == "blocked"
    bot refuse_responding

define bot refuse_responding
  "I'm sorry, I cannot process that request."

define flow self_check_output
  bot will say something
  $output_check = execute self_check_output_action
  if $output_check == "blocked"
    bot refuse_responding
```

```python
# Python integration with NeMo Guardrails
from nemoguardrails import RailsConfig, LLMRails

config = RailsConfig.from_path("./config")
rails = LLMRails(config)

# The rails automatically apply input/output guardrails
response = await rails.generate_async(
    messages=[{"role": "user", "content": "Tell me about AI governance"}]
)
```

---

## 10.2 Responsible AI Principles

### The Five Pillars of Responsible AI

| Principle | Definition | Implementation |
|---|---|---|
| **Fairness** | AI systems should treat all individuals and groups equitably | Bias testing, demographic parity, equalized odds |
| **Transparency** | AI decision-making should be explainable and understandable | Model cards, explanation APIs, documentation |
| **Accountability** | Clear ownership and responsibility for AI outcomes | Audit trails, human-in-the-loop, governance boards |
| **Privacy** | Personal data must be protected throughout the AI lifecycle | Data minimization, differential privacy, consent management |
| **Safety** | AI must not cause harm to individuals or society | Red-teaming, safety evaluations, kill switches |

### Fairness Metrics

```python
# Example: Computing fairness metrics for a classification model
import numpy as np
from sklearn.metrics import accuracy_score

class FairnessEvaluator:
    def __init__(self, y_true, y_pred, sensitive_attr):
        self.y_true = np.array(y_true)
        self.y_pred = np.array(y_pred)
        self.sensitive_attr = np.array(sensitive_attr)

    def demographic_parity(self) -> dict:
        """Check if positive prediction rates are similar across groups."""
        groups = np.unique(self.sensitive_attr)
        rates = {}
        for group in groups:
            mask = self.sensitive_attr == group
            rates[str(group)] = np.mean(self.y_pred[mask])
        return rates

    def equalized_odds(self) -> dict:
        """Check if TPR and FPR are similar across groups."""
        groups = np.unique(self.sensitive_attr)
        results = {}
        for group in groups:
            mask = self.sensitive_attr == group
            tp = np.sum((self.y_pred[mask] == 1) & (self.y_true[mask] == 1))
            fn = np.sum((self.y_pred[mask] == 0) & (self.y_true[mask] == 1))
            fp = np.sum((self.y_pred[mask] == 1) & (self.y_true[mask] == 0))
            tn = np.sum((self.y_pred[mask] == 0) & (self.y_true[mask] == 0))

            tpr = tp / (tp + fn) if (tp + fn) > 0 else 0
            fpr = fp / (fp + tn) if (fp + tn) > 0 else 0
            results[str(group)] = {"tpr": tpr, "fpr": fpr}
        return results

    def disparate_impact_ratio(self) -> float:
        """Ratio of positive rates between privileged and unprivileged groups."""
        rates = self.demographic_parity()
        groups = sorted(rates.keys())
        if len(groups) < 2:
            return 1.0
        return rates[groups[1]] / rates[groups[0]] if rates[groups[0]] > 0 else float("inf")
```

### Model Cards

Model cards are standardized documents that provide transparency about a model's capabilities, limitations, and intended use.

```markdown
# Model Card: Customer Churn Prediction v2.1

## Model Details
- **Owner**: Data Science Team
- **Date**: 2026-03-15
- **Version**: 2.1
- **Type**: Gradient Boosted Classifier (XGBoost)
- **License**: Internal Use Only

## Intended Use
- Predict customer churn risk for proactive retention campaigns
- Used by marketing team to prioritize outreach

## Performance Metrics
| Metric | Value |
|---|---|
| Accuracy | 0.87 |
| Precision | 0.83 |
| Recall | 0.79 |
| F1 Score | 0.81 |
| AUC-ROC | 0.91 |

## Fairness Evaluation
| Group | Positive Rate | TPR | FPR |
|---|---|---|---|
| Age 18-30 | 0.24 | 0.81 | 0.12 |
| Age 31-50 | 0.22 | 0.78 | 0.10 |
| Age 51+ | 0.20 | 0.76 | 0.09 |

## Limitations
- Trained on data from 2023-2025; may not generalize to new market conditions
- Lower accuracy for customers with < 3 months of history
- Does not account for seasonal purchasing patterns

## Ethical Considerations
- Model should NOT be used to deny services or increase prices
- Human review required before any automated action
- Regular bias audits scheduled quarterly
```

### AI Audit Framework

```
AI AUDIT CHECKLIST
==================

Phase 1: Pre-Deployment
  [ ] Bias testing completed across protected attributes
  [ ] Model card documented and reviewed
  [ ] Data lineage and provenance recorded
  [ ] Privacy impact assessment completed
  [ ] Red-team adversarial testing performed
  [ ] Explainability methods validated (SHAP, LIME)

Phase 2: Deployment
  [ ] Monitoring dashboards configured
  [ ] Alerting thresholds set for drift and bias
  [ ] Human-in-the-loop approval workflow active
  [ ] Rollback mechanism tested
  [ ] Access controls and audit logging enabled

Phase 3: Post-Deployment
  [ ] Monthly performance reviews scheduled
  [ ] Quarterly bias audits scheduled
  [ ] User feedback collection mechanism in place
  [ ] Incident response plan documented
  [ ] Retraining triggers defined and monitored
```

---

## 10.3 Regulatory Compliance

### GDPR Compliance for AI

The General Data Protection Regulation (GDPR) imposes specific requirements on automated decision-making systems.

| GDPR Article | Requirement | AI Impact |
|---|---|---|
| **Art. 13-14** | Right to information | Must disclose AI involvement in decisions |
| **Art. 15** | Right of access | Individuals can request their data and how it's used |
| **Art. 16-17** | Right to rectification/erasure | Must handle data correction and deletion in training sets |
| **Art. 21** | Right to object | Users can opt out of automated decision-making |
| **Art. 22** | Right to human intervention | No solely automated decisions with legal effects without consent |
| **Art. 35** | Data Protection Impact Assessment | Required for high-risk AI processing |

```python
# Example: GDPR-compliant data handling for AI systems
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
import hashlib

class ConsentStatus(Enum):
    GRANTED = "granted"
    WITHDRAWN = "withdrawn"
    NOT_REQUESTED = "not_requested"

@dataclass
class GDPRCompliantDataStore:
    """Data store that enforces GDPR requirements for AI training data."""

    records: dict = field(default_factory=dict)
    consent_log: list = field(default_factory=list)
    audit_trail: list = field(default_factory=list)

    def add_record(self, user_id: str, data: dict, consent: ConsentStatus) -> bool:
        if consent != ConsentStatus.GRANTED:
            self._log_action(user_id, "REJECTED", "No valid consent")
            return False

        self.records[user_id] = {
            "data": data,
            "consent": consent,
            "added_at": datetime.utcnow().isoformat(),
            "last_accessed": None,
        }
        self._log_action(user_id, "ADDED", "Record added with consent")
        return True

    def handle_erasure_request(self, user_id: str) -> bool:
        """GDPR Art. 17 - Right to erasure (right to be forgotten)."""
        if user_id in self.records:
            del self.records[user_id]
            self._log_action(user_id, "ERASED", "Data erased per user request")
            return True
        return False

    def handle_access_request(self, user_id: str) -> Optional[dict]:
        """GDPR Art. 15 - Right of access."""
        if user_id in self.records:
            self.records[user_id]["last_accessed"] = datetime.utcnow().isoformat()
            self._log_action(user_id, "ACCESSED", "Data access request fulfilled")
            return self.records[user_id]
        return None

    def generate_dpiat_report(self) -> dict:
        """Generate Data Protection Impact Assessment report (Art. 35)."""
        return {
            "total_records": len(self.records),
            "consent_status": {
                "granted": sum(1 for r in self.records.values()
                              if r["consent"] == ConsentStatus.GRANTED),
            },
            "audit_entries": len(self.audit_trail),
            "generated_at": datetime.utcnow().isoformat(),
        }

    def _log_action(self, user_id: str, action: str, detail: str):
        self.audit_trail.append({
            "user_hash": hashlib.sha256(user_id.encode()).hexdigest()[:12],
            "action": action,
            "detail": detail,
            "timestamp": datetime.utcnow().isoformat(),
        })
```

### HIPAA Requirements for AI

Healthcare AI systems processing Protected Health Information (PHI) must comply with HIPAA regulations.

| HIPAA Rule | Requirement | AI Implementation |
|---|---|---|
| **Privacy Rule** | Limit use/disclosure of PHI | Data minimization, role-based access |
| **Security Rule** | Administrative, physical, technical safeguards | Encryption at rest/transit, audit logging |
| **Breach Notification** | Notify affected parties of breaches | Automated breach detection and alerting |
| **Minimum Necessary** | Use only minimum required PHI | Feature selection to exclude unnecessary fields |
| **Business Associate** | BAAs with all vendors processing PHI | Ensure all AI vendors have signed BAAs |

```python
# Example: HIPAA-compliant data pipeline
import hashlib
import json
from cryptography.fernet import Fernet

class HIPAACompliantPipeline:
    def __init__(self):
        self.encryption_key = Fernet.generate_key()
        self.cipher = Fernet(self.encryption_key)
        self.access_log = []

    def deidentify_safe_harbor(self, record: dict) -> dict:
        """Remove 18 HIPAA identifiers using Safe Harbor method."""
        hipaa_identifiers = [
            "name", "address", "date_of_birth", "ssn", "phone",
            "fax", "email", "medical_record_number", "health_plan_id",
            "account_number", "certificate_number", "vehicle_id",
            "device_id", "url", "ip_address", "biometric_id",
            "photo", "any_other_unique_id",
        ]

        safe_record = {}
        for key, value in record.items():
            if key.lower() in hipaa_identifiers:
                safe_record[key] = hashlib.sha256(
                    str(value).encode()
                ).hexdigest()[:8]
            else:
                safe_record[key] = value

        return safe_record

    def encrypt_phi(self, data: str) -> bytes:
        """Encrypt PHI data at rest."""
        return self.cipher.encrypt(data.encode())

    def decrypt_phi(self, encrypted_data: bytes) -> str:
        """Decrypt PHI data with audit logging."""
        self.access_log.append({
            "action": "DECRYPT",
            "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
        })
        return self.cipher.decrypt(encrypted_data).decode()
```

### EU AI Act Risk Classification

The EU AI Act classifies AI systems into four risk tiers with corresponding obligations.

```
┌─────────────────────────────────────────────────────────┐
│                   EU AI ACT RISK TIERS                   │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  UNACCEPTABLE RISK (Prohibited)                         │
│  ├── Social scoring by governments                      │
│  ├── Real-time biometric surveillance (public spaces)   │
│  ├── Manipulation of vulnerable groups                  │
│  └── Emotion recognition in workplaces/education        │
│                                                         │
│  HIGH RISK (Regulated)                                  │
│  ├── Biometric identification systems                   │
│  ├── Critical infrastructure management                 │
│  ├── Educational/vocational access                      │
│  ├── Employment/worker management                       │
│  ├── Essential services (credit scoring, insurance)     │
│  ├── Law enforcement                                    │
│  ├── Migration/border control                           │
│  └── Justice and democratic processes                   │
│                                                         │
│  LIMITED RISK (Transparency obligations)                │
│  ├── Chatbots (must disclose AI nature)                 │
│  ├── Deepfake generators (must label output)            │
│  └── Emotion recognition systems (must inform)          │
│                                                         │
│  MINIMAL RISK (No specific obligations)                 │
│  ├── Spam filters                                       │
│  ├── AI-enabled games                                   │
│  └── Inventory management systems                       │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

```python
# Example: EU AI Act risk classifier
from enum import Enum
from dataclasses import dataclass

class RiskTier(Enum):
    UNACCEPTABLE = "unacceptable"
    HIGH = "high"
    LIMITED = "limited"
    MINIMAL = "minimal"

class Domain(Enum):
    BIOMETRICS = "biometrics"
    CRITICAL_INFRA = "critical_infrastructure"
    EDUCATION = "education"
    EMPLOYMENT = "employment"
    ESSENTIAL_SERVICES = "essential_services"
    LAW_ENFORCEMENT = "law_enforcement"
    MIGRATION = "migration"
    JUSTICE = "justice"
    GENERAL = "general"

@dataclass
class AISystemAssessment:
    name: str
    domain: Domain
    is_biometric: bool = False
    affects_fundamental_rights: bool = False
    is_real_time_surveillance: bool = False
    targets_vulnerable_groups: bool = False
    is_chatbot: bool = False
    generates_deepfakes: bool = False

    def classify_risk(self) -> RiskTier:
        # Check for prohibited practices
        if self.is_real_time_surveillance and self.domain == Domain.LAW_ENFORCEMENT:
            return RiskTier.UNACCEPTABLE
        if self.targets_vulnerable_groups and self.affects_fundamental_rights:
            return RiskTier.UNACCEPTABLE

        # Check for high-risk domains
        high_risk_domains = {
            Domain.BIOMETRICS, Domain.CRITICAL_INFRA, Domain.EDUCATION,
            Domain.EMPLOYMENT, Domain.ESSENTIAL_SERVICES,
            Domain.LAW_ENFORCEMENT, Domain.MIGRATION, Domain.JUSTICE,
        }
        if self.domain in high_risk_domains or self.is_biometric:
            return RiskTier.HIGH

        # Check for limited risk
        if self.is_chatbot or self.generates_deepfakes:
            return RiskTier.LIMITED

        return RiskTier.MINIMAL

    def get_obligations(self) -> list[str]:
        tier = self.classify_risk()
        obligations = {
            RiskTier.UNACCEPTABLE: ["Must not be placed on the market or deployed"],
            RiskTier.HIGH: [
                "Conformity assessment required",
                "Risk management system",
                "Data governance and documentation",
                "Technical documentation",
                "Record-keeping and audit trail",
                "Transparency and user information",
                "Human oversight measures",
                "Accuracy, robustness, and cybersecurity standards",
                "Registration in EU database",
            ],
            RiskTier.LIMITED: [
                "Transparency obligation — inform users of AI interaction",
                "Label deepfake and synthetic content",
            ],
            RiskTier.MINIMAL: ["No specific regulatory obligations"],
        }
        return obligations[tier]
```

### Data Privacy Patterns

| Pattern | Description | Use Case |
|---|---|---|
| **Anonymization** | Irreversibly remove identifying information | Sharing datasets publicly |
| **Pseudonymization** | Replace identifiers with reversible tokens | Internal analytics with re-identification capability |
| **Differential Privacy** | Add calibrated noise to prevent individual inference | Aggregate statistics, federated learning |
| **Data Minimization** | Collect only what is strictly necessary | All AI data collection |
| **Purpose Limitation** | Use data only for stated purpose | Cross-project data reuse |
| **K-Anonymity** | Ensure each record is indistinguishable from k-1 others | Dataset releases |

```python
# Example: Differential privacy implementation
import numpy as np

class DifferentialPrivacy:
    def __init__(self, epsilon: float = 1.0):
        self.epsilon = epsilon

    def laplace_mechanism(self, true_value: float, sensitivity: float) -> float:
        """Add Laplace noise to a numeric value."""
        scale = sensitivity / self.epsilon
        noise = np.random.laplace(0, scale)
        return true_value + noise

    def private_mean(self, data: list[float], bounds: tuple[float, float]) -> float:
        """Compute differentially private mean."""
        sensitivity = (bounds[1] - bounds[0]) / len(data)
        true_mean = np.mean(data)
        return self.laplace_mechanism(true_mean, sensitivity)

    def private_count(self, data: list, target_value) -> int:
        """Compute differentially private count."""
        true_count = sum(1 for x in data if x == target_value)
        return max(0, round(self.laplace_mechanism(true_count, 1.0)))
```

---

## Key Takeaways

1. **AI risk taxonomy** categorizes threats from hallucination to adversarial attacks, each requiring specific mitigation strategies.
2. **Guardrails** must operate at both input (sanitization, injection detection) and output (factuality checks, PII redaction) layers.
3. **Responsible AI** rests on five pillars: fairness, transparency, accountability, privacy, and safety — all requiring measurable metrics.
4. **Model cards** provide standardized transparency documentation and should be mandatory for every production model.
5. **GDPR Art. 22** grants individuals the right not to be subject to solely automated decisions with legal or significant effects.
6. **HIPAA Safe Harbor** de-identification removes 18 identifier categories and is the most common approach for healthcare AI.
7. **EU AI Act** creates a four-tier risk classification — high-risk systems face the most extensive compliance obligations.
8. **Differential privacy** provides mathematical guarantees that individual records cannot be inferred from aggregate outputs.
9. **Continuous monitoring** — governance is not a one-time activity but an ongoing process of auditing, measuring, and improving.
10. **Human oversight** remains essential — no AI system should operate without meaningful human control mechanisms.
