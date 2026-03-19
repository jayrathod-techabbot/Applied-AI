# Security & Compliance - Concepts

## Table of Contents
1. [Security Overview](#security-overview)
2. [API Security](#api-security)
3. [Input/Output Security](#inputoutput-security)
4. [Data Privacy](#data-privacy)
5. [Compliance Frameworks](#compliance-frameworks)
6. [Authentication & Authorization](#authentication--authorization)
7. [Infrastructure Security](#infrastructure-security)
8. [Incident Response](#incident-response)

---

## Security Overview

### Security Layers

```
┌─────────────────────────────────────────────────────────────────┐
│                    Defense in Depth                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │  Layer 8: User Education & Policies                     │   │
│   └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │  Layer 7: Application Security (WAF, API Gateway)       │   │
│   └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │  Layer 6: Data Security (Encryption, Masking)          │   │
│   └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │  Layer 5: Network Security (VPC, Firewall)             │   │
│   └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │  Layer 4: Compute Security (Containers, VMs)           │   │
│   └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │  Layer 3: Identity & Access Management                 │   │
│   └─────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Common LLM Security Threats

| Threat | Description | Impact |
|--------|-------------|--------|
| **Prompt Injection** | Malicious input manipulates model | Data leak, unauthorized actions |
| **Data Exfiltration** | Extracting sensitive data from model | Privacy breach |
| **Denial of Service** | Resource exhaustion via large prompts | Service unavailability |
| **Model Extraction** | Replicating model through API abuse | IP theft |
| **Toxic Output** | Generating harmful content | Reputation damage |
| **Jailbreaking** | Bypassing safety measures | Compliance violation |

---

## API Security

### API Key Management

```python
# api_key_manager.py
import os
import hashlib
import secrets
from typing import Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass

@dataclass
class APIKey:
    key_hash: str
    user_id: str
    created_at: datetime
    expires_at: Optional[datetime]
    scopes: List[str]
    is_active: bool = True

class SecureKeyManager:
    """
    Secure management of API keys
    """
    
    def __init__(self):
        self._keys: dict = {}
        self._key_prefix = "sk-llm-"
    
    def generate_key(self, user_id: str, scopes: List[str], ttl_days: int = 90) -> str:
        """Generate a new API key"""
        # Generate random key
        raw_key = secrets.token_urlsafe(32)
        full_key = f"{self._key_prefix}{raw_key}"
        
        # Hash key for storage
        key_hash = hashlib.sha256(full_key.encode()).hexdigest()
        
        # Store with metadata
        self._keys[key_hash] = APIKey(
            key_hash=key_hash,
            user_id=user_id,
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(days=ttl_days),
            scopes=scopes
        )
        
        return full_key
    
    def validate_key(self, key: str) -> Optional[APIKey]:
        """Validate an API key"""
        if not key.startswith(self._key_prefix):
            return None
        
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        
        if key_hash not in self._keys:
            return None
        
        api_key = self._keys[key_hash]
        
        # Check if active and not expired
        if not api_key.is_active:
            return None
        
        if api_key.expires_at and api_key.expires_at < datetime.now():
            return None
        
        return api_key
    
    def revoke_key(self, key: str) -> bool:
        """Revoke an API key"""
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        
        if key_hash in self._keys:
            self._keys[key_hash].is_active = False
            return True
        
        return False
    
    def rotate_key(self, old_key: str) -> Optional[str]:
        """Rotate an API key"""
        old_key_data = self.validate_key(old_key)
        
        if not old_key_data:
            return None
        
        # Generate new key with same permissions
        new_key = self.generate_key(
            user_id=old_key_data.user_id,
            scopes=old_key_data.scopes
        )
        
        # Revoke old key
        self.revoke_key(old_key)
        
        return new_key
```

### Rate Limiting Implementation

```python
# rate_limiter.py
from typing import Dict, Optional
import time
from collections import defaultdict
import threading

class TokenBucket:
    """Token bucket algorithm for rate limiting"""
    
    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity
        self.refill_rate = refill_rate  # tokens per second
        self.tokens = capacity
        self.last_refill = time.time()
        self._lock = threading.Lock()
    
    def consume(self, tokens: int = 1) -> bool:
        """Try to consume tokens"""
        with self._lock:
            self._refill()
            
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            
            return False
    
    def _refill(self):
        """Refill tokens based on elapsed time"""
        now = time.time()
        elapsed = now - self.last_refill
        
        new_tokens = elapsed * self.refill_rate
        self.tokens = min(self.capacity, self.tokens + new_tokens)
        self.last_refill = now

class RateLimiter:
    """
    Rate limiter with multiple strategies
    """
    
    def __init__(self):
        self._user_buckets: Dict[str, TokenBucket] = {}
        self._default_limits = {
            "free": (10, 1),      # 10 requests/second
            "basic": (50, 5),     # 50 requests/second
            "premium": (200, 20), # 200 requests/second
            "enterprise": (1000, 100)  # 1000 requests/second
        }
    
    def check_rate_limit(
        self,
        user_id: str,
        tier: str = "free",
        endpoint: str = None
    ) -> tuple[bool, Dict]:
        """Check if request is within rate limit"""
        # Get limit for tier
        limit = self._default_limits.get(tier, self._default_limits["free"])
        
        # Create bucket if not exists
        key = f"{user_id}:{endpoint or 'default'}"
        
        if key not in self._user_buckets:
            self._user_buckets[key] = TokenBucket(limit[0], limit[1])
        
        bucket = self._user_buckets[key]
        
        # Try to consume
        allowed = bucket.consume()
        
        return allowed, {
            "tier": tier,
            "limit": limit[0],
            "remaining": int(bucket.tokens)
        }
```

---

## Input/Output Security

### Prompt Injection Prevention

```python
# prompt_injection_detector.py
import re
from typing import List, Tuple
import json

class PromptInjectionDetector:
    """
    Detect and prevent prompt injection attacks
    """
    
    # Known injection patterns
    INJECTION_PATTERNS = [
        # Ignore/dismiss instructions
        r"ignore\s+(previous|all|above|prior)\s+(instructions?|commands?|directives?)",
        r"disregard\s+(previous|all|above)\s+(instructions?|commands?)",
        r"forget\s+(your|all|everything)\s+(instructions?|system|training)",
        
        # System prompt extraction
        r"system\s*:\s*",
        r"<\|system\|>",
        r"show\s+(me\s+)?your\s+(system\s+)?prompt",
        r"what\s+(are|is)\s+your\s+(system\s+)?instructions",
        
        # Role playing/override
        r"you\s+are\s+now\s+(?:a|an)\s+",
        r"roleplay\s+as\s+",
        r"pretend\s+(to\s+be|you\s+are)",
        r"new\s+(system|role|persona):",
        
        # Delimiter injection
        r"---+\s*system\s*---+",
        r"<<<.*?>>>",
        r"====.*?====",
        
        # Code injection
        r"```system",
        r"<!--system-->",
    ]
    
    def __init__(self):
        self._patterns = [re.compile(p, re.IGNORECASE) for p in self.INJECTION_PATTERNS]
    
    def detect(self, text: str) -> Tuple[bool, List[str]]:
        """Detect potential prompt injection"""
        detections = []
        
        for i, pattern in enumerate(self._patterns):
            if pattern.search(text):
                detections.append(f"Pattern {i}: {self.INJECTION_PATTERNS[i]}")
        
        return len(detections) > 0, detections
    
    def sanitize(self, text: str) -> str:
        """Sanitize text by removing/detecting injection attempts"""
        sanitized = text
        
        # Replace detected patterns
        for pattern in self._patterns:
            sanitized = pattern.sub("[DETECTED]", sanitized)
        
        return sanitized
    
    def validate(self, text: str) -> Tuple[bool, str]:
        """Validate text and return validation result"""
        is_detected, detections = self.detect(text)
        
        if is_detected:
            return False, f"Potential prompt injection detected: {', '.join(detections[:3])}"
        
        return True, "Valid"

# Output filtering
class OutputFilter:
    """
    Filter sensitive information from LLM outputs
    """
    
    SENSITIVE_PATTERNS = {
        "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        "phone": r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
        "ssn": r'\b\d{3}-\d{2}-\d{4}\b',
        "credit_card": r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
        "api_key": r'(?:api[_-]?key|secret|token)["\s:=]+["\']?([a-zA-Z0-9_\-]{20,})["\']?',
    }
    
    def __init__(self):
        self._patterns = {
            k: re.compile(v) for k, v in self.SENSITIVE_PATTERNS.items()
        }
    
    def filter(self, text: str) -> str:
        """Filter sensitive information from text"""
        filtered = text
        
        for name, pattern in self._patterns.items():
            filtered = pattern.sub(f"[{name.upper()}_REDACTED]", filtered)
        
        return filtered
    
    def scan(self, text: str) -> List[dict]:
        """Scan for sensitive information"""
        findings = []
        
        for name, pattern in self._patterns.items():
            matches = pattern.finditer(text)
            for match in matches:
                findings.append({
                    "type": name,
                    "value": match.group(0),
                    "position": match.span()
                })
        
        return findings
```

---

## Data Privacy

### Data Handling Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Data Privacy Architecture                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   User Input                                                    │
│      │                                                          │
│      ▼                                                          │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │              PII Detection Layer                          │   │
│   │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │   │
│   │  │ Named Entity│  │ Pattern     │  │ Classification│    │   │
│   │  │ Recognition │  │ Matching    │  │ (ML Model)   │     │   │
│   │  └─────────────┘  └─────────────┘  └─────────────┘     │   │
│   └────────────────────────┬────────────────────────────────┘   │
│                            │                                     │
│              ┌─────────────┴─────────────┐                       │
│              ▼                           ▼                       │
│   ┌─────────────────────┐    ┌─────────────────────┐          │
│   │   PII Detected     │    │   No PII Detected   │          │
│   │                   │    │                     │          │
│   │  1. Redact/Mask  │    │  Pass to LLM       │          │
│   │  2. Log separately│    │  (or process       │          │
│   │  3. Don't send  │    │   normally)        │          │
│   │     to LLM     │    │                     │          │
│   └─────────────────────┘    └─────────────────────┘          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Data Retention

```python
# data_retention.py
from datetime import datetime, timedelta
from typing import Optional
from dataclasses import dataclass

@dataclass
class RetentionPolicy:
    name: str
    retention_days: int
    encryption_required: bool
    deletion_method: str  # "soft" or "hard"

class DataRetentionManager:
    """
    Manage data retention policies
    """
    
    DEFAULT_POLICIES = {
        "conversation_history": RetentionPolicy(
            name="conversation_history",
            retention_days=30,
            encryption_required=True,
            deletion_method="soft"
        ),
        "llm_requests": RetentionPolicy(
            name="llm_requests",
            retention_days=90,
            encryption_required=True,
            deletion_method="soft"
        ),
        "user_feedback": RetentionPolicy(
            name="user_feedback",
            retention_days=365,
            encryption_required=False,
            deletion_method="hard"
        ),
        "audit_logs": RetentionPolicy(
            name="audit_logs",
            retention_days=730,
            encryption_required=True,
            deletion_method="hard"
        )
    }
    
    def __init__(self, policies: dict = None):
        self.policies = policies or self.DEFAULT_POLICIES
    
    def should_delete(self, data_type: str, created_at: datetime) -> bool:
        """Check if data should be deleted based on retention policy"""
        policy = self.policies.get(data_type)
        
        if not policy:
            return False
        
        retention_end = created_at + timedelta(days=policy.retention_days)
        
        return datetime.now() > retention_end
    
    def delete_data(self, data_type: str, data_id: str, method: str = None):
        """Delete data according to policy"""
        policy = self.policies.get(data_type)
        
        if not policy:
            raise ValueError(f"No retention policy for {data_type}")
        
        deletion_method = method or policy.deletion_method
        
        if deletion_method == "soft":
            # Mark as deleted, keep for compliance
            self._soft_delete(data_type, data_id)
        else:
            # Permanent deletion
            self._hard_delete(data_type, data_id)
    
    def _soft_delete(self, data_type: str, data_id: str):
        # Implementation: Mark as deleted in database
        pass
    
    def _hard_delete(self, data_type: str, data_id: str):
        # Implementation: Permanently delete from storage
        pass
```

---

## Compliance Frameworks

### GDPR Compliance

```python
# gdpr_compliance.py
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class GDPRRequest:
    request_id: str
    request_type: str  # "access", "rectification", "erasure", "portability"
    user_id: str
    created_at: datetime
    status: str  # "pending", "completed", "rejected"

class GDPRComplianceManager:
    """
    Handle GDPR data subject requests
    """
    
    def __init__(self):
        self.data_processors: Dict[str, List[str]] = {}  # user_id -> list of data types
    
    def handle_access_request(self, user_id: str) -> Dict:
        """Handle right to access request"""
        # Gather all user data
        user_data = self._gather_user_data(user_id)
        
        return {
            "user_id": user_id,
            "data": user_data,
            "categories": list(user_data.keys()),
            "purposes": ["service_delivery", "analytics"],
            "recipients": ["self"],
            "retention_period": "See retention policy"
        }
    
    def handle_erasure_request(self, user_id: str, reason: str = None) -> bool:
        """Handle right to erasure request"""
        # Check for legal holds
        if self._has_legal_hold(user_id):
            raise ValueError("Cannot erase data due to legal hold")
        
        # Delete from all systems
        self._delete_from_all_systems(user_id)
        
        return True
    
    def handle_portability_request(self, user_id: str) -> Dict:
        """Handle right to data portability"""
        user_data = self._gather_user_data(user_id)
        
        # Format in machine-readable format
        return {
            "user_id": user_id,
            "format": "JSON",
            "data": user_data,
            "generated_at": datetime.now().isoformat()
        }
    
    def _gather_user_data(self, user_id: str) -> Dict:
        # Implementation: Gather data from all data stores
        return {
            "profile": {},
            "conversation_history": [],
            "preferences": {}
        }
    
    def _delete_from_all_systems(self, user_id: str):
        # Implementation: Delete from all data stores
        pass
    
    def _has_legal_hold(self, user_id: str) -> bool:
        # Implementation: Check for legal holds
        return False
```

### SOC 2 Compliance Checklist

```
┌─────────────────────────────────────────────────────────────────┐
│                    SOC 2 Compliance Checklist                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  CC1: Control Environment                                 │  │
│  │  □ Security policies documented                          │  │
│  │  □ Organizational structure defined                      │  │
│  │  □ Security awareness training                          │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  CC2: Communication and Information                       │  │
│  │  □ Security objectives communicated                      │  │
│  │  □ Risk assessment process established                   │  │
│  │  □ Internal communication channels                        │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  CC3: Risk Assessment                                     │  │
│  │  □ Annual risk assessment                                 │  │
│  │  □ Vulnerability scanning                                │  │
│  │  □ Penetration testing                                    │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  CC4: Monitoring Activities                               │  │
│  │  □ Log management                                        │  │
│  │  □ Anomaly detection                                      │  │
│  │  □ Incident response plan                                │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  CC5: Control Activities                                  │  │
│  │  □ Change management process                             │  │
│  │  □ Access control policies                               │  │
│  │  □ Data encryption                                       │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  CC6: Logical and Physical Access Controls               │  │
│  │  □ Multi-factor authentication                           │  │
│  │  □ Role-based access control                             │  │
│  │  □ Data center security                                  │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  CC7: System Operations                                   │  │
│  │  □ Backup and recovery                                  │  │
│  │  □ Disaster recovery plan                               │  │
│  │  □ Business continuity                                   │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Authentication & Authorization

### OAuth 2.0 Implementation

```python
# oauth_manager.py
from typing import Optional, Dict, List
from dataclasses import dataclass
from datetime import datetime, timedelta

@dataclass
class User:
    user_id: str
    email: str
    roles: List[str]
    scopes: List[str]
    tier: str

class OAuthManager:
    """
    OAuth 2.0 implementation for LLM API
    """
    
    def __init__(self):
        self._access_tokens: Dict[str, Dict] = {}
        self._refresh_tokens: Dict[str, Dict] = {}
    
    def generate_tokens(
        self,
        user: User,
        client_id: str,
        scope: List[str]
    ) -> Dict[str, str]:
        """Generate access and refresh tokens"""
        import secrets
        
        # Validate scope
        valid_scopes = [s for s in scope if s in user.scopes]
        
        # Access token (short-lived)
        access_token = secrets.token_urlsafe(32)
        access_token_data = {
            "user_id": user.user_id,
            "client_id": client_id,
            "scopes": valid_scopes,
            "issued_at": datetime.now(),
            "expires_at": datetime.now() + timedelta(hours=1)
        }
        self._access_tokens[access_token] = access_token_data
        
        # Refresh token (long-lived)
        refresh_token = secrets.token_urlsafe(32)
        refresh_token_data = {
            "user_id": user.user_id,
            "client_id": client_id,
            "scopes": valid_scopes,
            "issued_at": datetime.now(),
            "expires_at": datetime.now() + timedelta(days=30)
        }
        self._refresh_tokens[refresh_token] = refresh_token_data
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "Bearer",
            "expires_in": 3600
        }
    
    def validate_token(self, token: str) -> Optional[Dict]:
        """Validate access token"""
        if token not in self._access_tokens:
            return None
        
        token_data = self._access_tokens[token]
        
        # Check expiration
        if token_data["expires_at"] < datetime.now():
            del self._access_tokens[token]
            return None
        
        return token_data
    
    def refresh_access_token(self, refresh_token: str) -> Optional[Dict]:
        """Refresh access token"""
        if refresh_token not in self._refresh_tokens:
            return None
        
        token_data = self._refresh_tokens[refresh_token]
        
        # Check expiration
        if token_data["expires_at"] < datetime.now():
            del self._refresh_tokens[refresh_token]
            return None
        
        # Generate new tokens
        user = User(
            user_id=token_data["user_id"],
            email="",  # Would fetch from database
            roles=[],  # Would fetch from database
            scopes=token_data["scopes"],
            tier=""    # Would fetch from database
        )
        
        return self.generate_tokens(user, token_data["client_id"], token_data["scopes"])
```

---

## Infrastructure Security

### Network Security

```yaml
# Network policies for Kubernetes
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: llm-api-network-policy
spec:
  podSelector:
    matchLabels:
      app: llm-api
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: api-gateway
    ports:
    - protocol: TCP
      port: 8000
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: redis
    ports:
    - protocol: TCP
      port: 6379
  - to:
    - podSelector:
        matchLabels:
          app: database
    ports:
    - protocol: TCP
      port: 5432
  - to:
    - namespaceSelector: {}
      podSelector:
        matchLabels:
          k8s-app: kube-dns
    ports:
    - protocol: UDP
      port: 53
```

### Secret Management

```python
# secret_manager.py
import os
from typing import Optional
from abc import ABC, abstractmethod

class SecretStore(ABC):
    @abstractmethod
    def get_secret(self, name: str) -> Optional[str]:
        pass
    
    @abstractmethod
    def set_secret(self, name: str, value: str):
        pass

class VaultSecretStore(SecretStore):
    """HashiCorp Vault secret store"""
    
    def __init__(self, vault_url: str, vault_token: str):
        self.vault_url = vault_url
        self.vault_token = vault_token
    
    def get_secret(self, name: str) -> Optional[str]:
        import requests
        
        response = requests.get(
            f"{self.vault_url}/v1/secret/data/llmops/{name}",
            headers={"X-Vault-Token": self.vault_token}
        )
        
        if response.status_code == 200:
            return response.json()["data"]["data"]["value"]
        return None

class AWSSecretsManager(SecretStore):
    """AWS Secrets Manager"""
    
    def __init__(self, region_name: str):
        import boto3
        self.client = boto3.client("secretsmanager", region_name=region_name)
    
    def get_secret(self, name: str) -> Optional[str]:
        try:
            response = self.client.get_secret_value(SecretId=name)
            return response["SecretString"]
        except:
            return None

# Usage
def get_api_key():
    # Use environment variable as fallback
    api_key = os.environ.get("OPENAI_API_KEY")
    
    if not api_key:
        # Try vault
        vault = VaultSecretStore(
            os.environ["VAULT_ADDR"],
            os.environ["VAULT_TOKEN"]
        )
        api_key = vault.get_secret("openai-api-key")
    
    return api_key
```

---

## Incident Response

### Incident Response Plan

```python
# incident_response.py
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
import json

@dataclass
class SecurityIncident:
    incident_id: str
    severity: str  # "low", "medium", "high", "critical"
    category: str
    description: str
    detected_at: datetime
    status: str  # "open", "investigating", "contained", "resolved"
    affected_systems: List[str]

class IncidentResponseManager:
    """
    Manage security incidents
    """
    
    def __init__(self):
        self.incidents: Dict[str, SecurityIncident] = {}
        self.notification_channels = []
    
    def report_incident(
        self,
        severity: str,
        category: str,
        description: str,
        affected_systems: List[str]
    ) -> str:
        """Report a new security incident"""
        import uuid
        
        incident_id = f"INC-{uuid.uuid4().hex[:8].upper()}"
        
        incident = SecurityIncident(
            incident_id=incident_id,
            severity=severity,
            category=category,
            description=description,
            detected_at=datetime.now(),
            status="open",
            affected_systems=affected_systems
        )
        
        self.incidents[incident_id] = incident
        
        # Notify relevant parties
        self._notify(incident)
        
        return incident_id
    
    def escalate_incident(self, incident_id: str, reason: str):
        """Escalate an incident"""
        if incident_id not in self.incidents:
            raise ValueError(f"Incident {incident_id} not found")
        
        incident = self.incidents[incident_id]
        
        # Increase severity
        severity_map = {"low": "medium", "medium": "high", "high": "critical"}
        incident.severity = severity_map.get(incident.severity, "critical")
        incident.description += f"\n\nEscalation reason: {reason}"
        
        self._notify(incident)
    
    def resolve_incident(self, incident_id: str, resolution: str):
        """Resolve an incident"""
        if incident_id not in self.incidents:
            raise ValueError(f"Incident {incident_id} not found")
        
        incident = self.incidents[incident_id]
        incident.status = "resolved"
        
        # Log resolution
        self._log_resolution(incident, resolution)
    
    def _notify(self, incident: SecurityIncident):
        """Notify relevant parties"""
        for channel in self.notification_channels:
            try:
                channel.send(incident)
            except:
                pass
    
    def _log_resolution(self, incident: SecurityIncident, resolution: str):
        """Log incident resolution"""
        # Implementation
        pass

# Example usage
def handle_security_event(event_type: str, details: dict):
    """Handle security events"""
    
    response_manager = IncidentResponseManager()
    
    # Map events to incidents
    incident_mapping = {
        "prompt_injection": {
            "severity": "high",
            "category": "prompt_injection",
            "description": "Potential prompt injection detected"
        },
        "data_breach": {
            "severity": "critical",
            "category": "data_breach",
            "description": "Potential data breach detected"
        },
        "rate_limit_exceeded": {
            "severity": "low",
            "category": "abuse",
            "description": "Rate limit exceeded"
        }
    }
    
    if event_type in incident_mapping:
        config = incident_mapping[event_type]
        response_manager.report_incident(
            severity=config["severity"],
            category=config["category"],
            description=config["description"],
            affected_systems=details.get("systems", [])
        )
```

---

## Best Practices

1. **Defense in Depth**: Multiple security layers
2. **Least Privilege**: Minimal access required
3. **Encrypt Everything**: At rest and in transit
4. **Monitor Continuously**: Real-time threat detection
5. **Regular Audits**: Security assessments
6. **Incident Response Plan**: Prepared for breaches
7. **Compliance First**: Build for compliance
8. **User Education**: Security awareness
