# Hands-On: AI Compliance Implementation

This guide provides practical implementation examples for AI compliance.

---

## Table of Contents

1. [GDPR Compliance](#gdpr-compliance)
2. [EU AI Act Compliance](#eu-ai-act-compliance)
3. [Documentation Templates](#documentation-templates)
4. [Compliance Automation](#compliance-automation)

---

## GDPR Compliance

### Data Protection Impact Assessment (DPIA)

```python
"""
GDPR DPIA Template
"""

class DPIA:
    """Data Protection Impact Assessment."""
    
    def __init__(self, ai_system_name: str):
        self.system_name = ai_system_name
        self.processing_purpose = ""
        self.data_categories = []
        self.data_subjects = []
        self.risks = []
        self.measures = []
    
    def add_data_category(self, category: str, sensitive: bool = False):
        """Add a data category."""
        self.data_categories.append({
            "category": category,
            "sensitive": sensitive
        })
    
    def add_risk(self, risk: str, severity: str, likelihood: str):
        """Add a identified risk."""
        self.risks.append({
            "risk": risk,
            "severity": severity,  # Low, Medium, High
            "likelihood": likelihood  # Low, Medium, High
        })
    
    def add_measure(self, measure: str, addresses_risk: str):
        """Add a mitigating measure."""
        self.measures.append({
            "measure": measure,
            "addresses_risk": addresses_risk
        })
    
    def generate_report(self) -> str:
        """Generate DPIA report."""
        lines = [
            f"Data Protection Impact Assessment - {self.system_name}",
            "=" * 60,
            "",
            "1. Processing Purpose",
            self.processing_purpose,
            "",
            "2. Data Categories"
        ]
        
        for cat in self.data_categories:
            sensitive = " (SENSITIVE)" if cat["sensitive"] else ""
            lines.append(f"  - {cat['category']}{sensitive}")
        
        lines.extend(["", "3. Risks"])
        for r in self.risks:
            lines.append(f"  - {r['risk']} ({r['severity']}/{r['likelihood']})")
        
        lines.extend(["", "4. Measures"])
        for m in self.measures:
            lines.append(f"  - {m['measure']}")
        
        return "\n".join(lines)
```

### Data Subject Rights Handler

```python
"""
GDPR Data Subject Rights Handler
"""

from datetime import datetime
from typing import List, Dict, Optional
import json

class DataSubjectRights:
    """Handle data subject requests."""
    
    def __init__(self, data_store):
        self.data_store = data_store  # Your data storage
        self.request_log: List[Dict] = []
    
    def handle_access_request(self, subject_id: str) -> Dict:
        """Handle right to access (Article 15)."""
        request = {
            "type": "access",
            "subject_id": subject_id,
            "timestamp": datetime.now().isoformat(),
            "completed": False
        }
        
        # Retrieve subject's data
        data = self.data_store.get_by_subject(subject_id)
        
        request["data"] = data
        request["completed"] = True
        
        self.request_log.append(request)
        return request
    
    def handle_deletion_request(self, subject_id: str) -> Dict:
        """Handle right to erasure (Article 17)."""
        request = {
            "type": "erasure",
            "subject_id": subject_id,
            "timestamp": datetime.now().isoformat(),
            "completed": False
        }
        
        # Delete subject's data
        deleted = self.data_store.delete_by_subject(subject_id)
        
        request["completed"] = deleted
        request["records_deleted"] = deleted
        
        self.request_log.append(request)
        return request
    
    def handle_portability_request(self, subject_id: str) -> Dict:
        """Handle right to data portability (Article 20)."""
        request = {
            "type": "portability",
            "subject_id": subject_id,
            "timestamp": datetime.now().isoformat(),
            "completed": False
        }
        
        # Get data in machine-readable format
        data = self.data_store.get_by_subject(subject_id)
        
        # Format as JSON
        portable_data = json.dumps(data, indent=2)
        
        request["data"] = portable_data
        request["completed"] = True
        
        self.request_log.append(request)
        return request
```

---

## EU AI Act Compliance

### Risk Classification System

```python
"""
EU AI Act Risk Classifier
"""

from enum import Enum

class RiskCategory(Enum):
    UNACCEPTABLE = "Unacceptable"
    HIGH = "High"
    LIMITED = "Limited"
    MINIMAL = "Minimal"

# High-risk use cases under EU AI Act
HIGH_RISK_USE_CASES = [
    "employment",  # Recruit, promotion, termination
    "credit",  # Credit scoring
    "law_enforcement",  # Policing, justice
    "migration",  # Border control
    "education",  # Access to education
    "healthcare",  # Medical diagnosis
    "essential_services",  # Public benefits
    "biometrics",  # Facial recognition
]

# Prohibited use cases
PROHIBITED_USE_CASES = [
    "social_scoring",
    "manipulation",
    "real_time_biometrics"  # With exceptions
]

class EUAIActClassifier:
    """Classify AI systems under EU AI Act."""
    
    def classify(self, use_case: str) -> RiskCategory:
        """Classify an AI system by use case."""
        use_case_lower = use_case.lower()
        
        # Check prohibited
        for prohibited in PROHIBITED_USE_CASES:
            if prohibited in use_case_lower:
                return RiskCategory.UNACCEPTABLE
        
        # Check high risk
        for high_risk in HIGH_RISK_USE_CASES:
            if high_risk in use_case_lower:
                return RiskCategory.HIGH
        
        # Check limited risk
        limited_risk = ["chatbot", "deepfake", "emotion_recognition"]
        for limited in limited_risk:
            if limited in use_case_lower:
                return RiskCategory.LIMITED
        
        return RiskCategory.MINIMAL
    
    def get_requirements(self, risk_category: RiskCategory) -> List[str]:
        """Get compliance requirements by category."""
        requirements = {
            RiskCategory.UNACCEPTABLE: [
                "System must not be deployed",
                "Complete prohibition"
            ],
            RiskCategory.HIGH: [
                "Risk assessment required",
                "Data governance measures",
                "Technical documentation",
                "Record keeping",
                "Transparency requirements",
                "Human oversight measures",
                "Accuracy and robustness measures",
                "Conformity assessment",
                "CE marking required"
            ],
            RiskCategory.LIMITED: [
                "Transparency obligations",
                "Human oversight if applicable",
                "Disclosure requirements"
            ],
            RiskCategory.MINIMAL: [
                "No specific requirements",
                "General data protection applies"
            ]
        }
        
        return requirements.get(risk_category, [])
```

---

## Documentation Templates

### Model Card Template

```markdown
# Model Card: [Model Name]

## Model Overview
- **Model Name**: 
- **Model Version**: 
- **Model Type**: 
- **Release Date**: 

## Intended Use
- Primary use case:
- Intended users:
- Out of scope:

## Training Data
- Data sources:
- Data size:
- Data collection date:
- Any known biases:

## Performance
- Metrics:
- Results:
- Limitations:

## Ethical Considerations
- Known biases:
- Risks:
- Mitigations:

## Compliance
- GDPR:
- EU AI Act:
- Other:

## Contact
- Name:
- Email:
```

### System Documentation Template

```markdown
# AI System Documentation

## 1. System Overview
- Name:
- Description:
- Version:
- Owner:

## 2. Technical Description
- Architecture:
- Data flow:
- APIs:
- Integrations:

## 3. Use Case
- Purpose:
- Users:
- Business value:

## 4. Risk Assessment
- Risk category:
- Identified risks:
- Mitigation measures:

## 5. Governance
- Human oversight:
- Monitoring:
- Review process:

## 6. Compliance
- GDPR:
- EU AI Act:
- Industry-specific:
```

---

## Compliance Automation

### Compliance Checker

```python
"""
Automated Compliance Checker
"""

from typing import Dict, List
from datetime import datetime

class ComplianceChecker:
    """Automated compliance checking."""
    
    def __init__(self):
        self.checks: List[Dict] = []
    
    def add_check(self, name: str, regulation: str, check_func):
        """Add a compliance check."""
        self.checks.append({
            "name": name,
            "regulation": regulation,
            "check": check_func,
            "last_run": None,
            "last_result": None
        })
    
    def run_all_checks(self, system_state: Dict) -> Dict:
        """Run all compliance checks."""
        results = {
            "timestamp": datetime.now().isoformat(),
            "total_checks": len(self.checks),
            "passed": 0,
            "failed": 0,
            "details": []
        }
        
        for check in self.checks:
            try:
                result = check["check"](system_state)
                check["last_result"] = result
                check["last_run"] = datetime.now()
                
                results["details"].append({
                    "name": check["name"],
                    "regulation": check["regulation"],
                    "passed": result,
                    "timestamp": check["last_run"].isoformat()
                })
                
                if result:
                    results["passed"] += 1
                else:
                    results["failed"] += 1
                    
            except Exception as e:
                results["failed"] += 1
                results["details"].append({
                    "name": check["name"],
                    "error": str(e)
                })
        
        return results
```

---

## Best Practices

1. **Maintain a compliance inventory** - Track all AI systems
2. **Regular audits** - Schedule periodic compliance reviews
3. **Document everything** - Keep detailed records
4. **Train teams** - Ensure everyone understands requirements
5. **Monitor changes** - Stay updated on regulatory changes
6. **Engage experts** - Consult legal and compliance professionals
