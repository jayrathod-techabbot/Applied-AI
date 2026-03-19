# Deployment Strategies - Concepts

## Table of Contents
1. [Deployment Patterns](#deployment-patterns)
2. [Blue-Green Deployment](#blue-green-deployment)
3. [Canary Deployment](#canary-deployment)
4. [Rolling Deployment](#rolling-deployment)
5. [A/B Testing](#ab-testing)
6. [Feature Flags](#feature-flags)
7. [Rollback Strategies](#rollback-strategies)
8. [CI/CD Integration](#cicd-integration)

---

## Deployment Patterns

### Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                  LLM Deployment Strategies                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   Pattern          │ Complexity │ Risk    │ Rollback Speed      │
│   ─────────────────────────────────────────────────────────────  │
│   Blue-Green      │   Low     │  Low    │  Instant            │
│   Canary          │   Medium  │  Low    │  Fast               │
│   Rolling         │   Medium  │  Medium │  Gradual            │
│   A/B Testing     │   High    │  Medium │  Depends            │
│   Shadow          │   High    │  Low    │  Instant            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Blue-Green Deployment

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                  Blue-Green Deployment                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   Initial State                    After Switch                  │
│                                                                  │
│   ┌─────────────┐                 ┌─────────────┐               │
│   │   Blue     │                 │   Green     │               │
│   │  (Active)  │                 │  (Active)   │               │
│   │   v1.0     │    ──────▶     │   v1.1      │               │
│   │             │   Switch       │             │               │
│   │  Traffic:  │   Traffic      │  Traffic:   │               │
│   │   100%     │   ◀──────     │   100%      │               │
│   └─────────────┘                 └─────────────┘               │
│         │                               │                        │
│         ▼                               ▼                        │
│   ┌─────────────┐                 ┌─────────────┐               │
│   │  Green     │                 │   Blue     │               │
│   │  (Idle)    │                 │  (Idle)    │               │
│   │   v0.9     │                 │   v1.0     │               │
│   └─────────────┘                 └─────────────┘               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Implementation

```yaml
# kubernetes-blue-green.yaml
apiVersion: v1
kind: Service
metadata:
  name: llm-service
spec:
  selector:
    app: llm-api
    version: green
  ports:
  - port: 80
    targetPort: 8000
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: llm-deployment-blue
spec:
  replicas: 3
  selector:
    matchLabels:
      app: llm-api
      version: blue
  template:
    metadata:
      labels:
        app: llm-api
        version: blue
    spec:
      containers:
      - name: llm-api
        image: llm-api:v1.0
        resources:
          requests:
            memory: "4Gi"
            cpu: "2"
            nvidia.com/gpu: 1
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: llm-deployment-green
spec:
  replicas: 3
  selector:
    matchLabels:
      app: llm-api
      version: green
  template:
    metadata:
      labels:
        app: llm-api
        version: green
    spec:
      containers:
      - name: llm-api
        image: llm-api:v1.1
        resources:
          requests:
            memory: "4Gi"
            cpu: "2"
            nvidia.com/gpu: 1
```

```bash
# blue-green-deployment.sh
#!/bin/bash

# Deploy to green (new version)
kubectl apply -f llm-deployment-green.yaml

# Wait for green to be ready
kubectl rollout status deployment/llm-deployment-green

# Test green deployment
kubectl run test-green --image=curlimages/curl -- curl http://llm-service-green/health

# Switch traffic to green
kubectl patch service llm-service -p '{"spec":{"selector":{"version":"green"}}}'

# Keep blue for rollback
# If issue, switch back: kubectl patch service llm-service -p '{"spec":{"selector":{"version":"blue"}}}'
```

---

## Canary Deployment

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                  Canary Deployment                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   Phase 1: 90/10 Split           Phase 2: 50/50 Split          │
│                                                                  │
│   ┌─────────────────┐           ┌─────────────────┐             │
│   │ v1.0 (Production)│          │ v1.0 (Production)│            │
│   │    90%          │           │    50%          │             │
│   │    ███████████ │           │    ██████       │             │
│   └─────────────────┘           └─────────────────┘             │
│          │                             │                         │
│          ▼                             ▼                        │
│   ┌─────────────────┐           ┌─────────────────┐             │
│   │ v1.1 (Canary)  │           │ v1.1 (Canary)  │             │
│   │    10%         │           │    50%          │             │
│   │    █           │           │    ██████       │             │
│   └─────────────────┘           └─────────────────┘             │
│                                                                  │
│   Phase 3: 100% (Full Rollout)                                  │
│                                                                  │
│   ┌─────────────────┐                                           │
│   │ v1.1 (Production)│                                          │
│   │    100%         │                                           │
│   │    ████████████ │                                           │
│   └─────────────────┘                                           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Implementation with Argo Rollouts

```yaml
# canary-rollout.yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: llm-rollout
spec:
  replicas: 10
  strategy:
    canary:
      canaryService: llm-canary
      stableService: llm-stable
      trafficRouting:
        nginx:
          stableIngress: llm-ingress
          additionalIngressAnnotations:
            canary-by-header: X-Canary
      steps:
        - setWeight: 10
        - pause: {duration: 10m}
        - setWeight: 30
        - pause: {duration: 10m}
        - setWeight: 50
        - pause: {duration: 10m}
        - setWeight: 80
        - pause: {duration: 10m}
        - setWeight: 100
      analysis:
        templates:
          - templateName: success-rate
        startingStep: 1
        args:
          - name: service-name
            value: llm-canary
  selector:
    matchLabels:
      app: llm-api
  template:
    metadata:
      labels:
        app: llm-api
    spec:
      containers:
      - name: llm-api
        image: llm-api:v1.1
---
apiVersion: argoproj.io/v1alpha1
kind: AnalysisTemplate
metadata:
  name: success-rate
spec:
  args:
    - name: service-name
  metrics:
    - name: success-rate
      interval: 1m
      successCondition: result[0] >= 0.95
      failureLimit: 3
      provider:
        prometheus:
          address: http://prometheus:9090
          query: |
            sum(rate(http_requests_total{service="{{args.service-name}}",status=~"2.."}[5m])) 
            / 
            sum(rate(http_requests_total{service="{{args.service-name}}"}[5m]))
    - name: latency
      interval: 1m
      failureLimit: 3
      provider:
        prometheus:
          address: http://prometheus:9090
          query: |
            histogram_quantile(0.95, 
              sum(rate(http_request_duration_seconds_bucket{service="{{args.service-name}}"}[5m])) by (le)
            )
```

### Istio Canary Deployment

```yaml
# istio-canary.yaml
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: llm-virtual-service
spec:
  hosts:
  - llm-service
  http:
  - name: canary
    match:
    - headers:
        x-canary:
          exact: "true"
    route:
    - destination:
        host: llm-service-canary
      weight: 100
  - name: main
    route:
    - destination:
        host: llm-service-stable
        subset: v1.0
      weight: 90
    - destination:
        host: llm-service-canary
        subset: v1.1
      weight: 10
---
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: llm-destination
spec:
  host: llm-service
  subsets:
  - name: v1.0
    labels:
      version: "1.0"
  - name: v1.1
    labels:
      version: "1.1"
```

---

## Rolling Deployment

### Implementation

```yaml
# rolling-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: llm-deployment
spec:
  replicas: 10
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 2           # Allow 2 extra pods during update
      maxUnavailable: 2    # Max 2 pods can be unavailable
  selector:
    matchLabels:
      app: llm-api
  template:
    metadata:
      labels:
        app: llm-api
        version: v1.1
    spec:
      containers:
      - name: llm-api
        image: llm-api:v1.1
        resources:
          requests:
            memory: "4Gi"
            cpu: "2"
            nvidia.com/gpu: 1
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
```

```bash
# Rolling update commands
kubectl set image deployment/llm-deployment llm-api=llm-api:v1.1

# Watch rollout
kubectl rollout status deployment/llm-deployment

# Rollback if needed
kubectl rollout undo deployment/llm-deployment

# Check rollout history
kubectl rollout history deployment/llm-deployment

# Rollback to specific revision
kubectl rollout undo deployment/llm-deployment --to-revision=2
```

---

## A/B Testing

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    A/B Testing Architecture                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   User Request                                                   │
│        │                                                         │
│        ▼                                                         │
│   ┌─────────────┐                                                │
│   │  Splitter   │                                                │
│   │  (Traffic  │                                                │
│   │   Router)  │                                                │
│   └──────┬──────┘                                                │
│          │                                                       │
│    ┌─────┴─────┬────────────┐                                   │
│    ▼            ▼            ▼                                   │
│ ┌──────┐  ┌──────┐  ┌──────┐                                   │
│ │ A:   │  │ B:   │  │ C:   │                                   │
│ │ GPT4 │  │ GPT3.5│  │Claude│                                   │
│ │ 40%  │  │ 40%  │  │ 20%  │                                   │
│ └──────┘  └──────┘  └──────┘                                   │
│    │          │          │                                      │
│    └──────────┴──────────┘                                      │
│               │                                                  │
│               ▼                                                  │
│   ┌──────────────────────┐                                      │
│   │  Metrics Collection  │                                      │
│   │  - Latency           │                                      │
│   │  - Success Rate      │                                      │
│   │  - User Feedback     │                                      │
│   │  - Task Completion   │                                      │
│   └──────────────────────┘                                      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Implementation

```python
# ab_testing.py
from typing import Dict, List
import random
import hashlib
from dataclasses import dataclass

@dataclass
class Experiment:
    name: str
    variants: List[Dict]
    traffic_split: List[int]  # Percentages
    
    def get_variant(self, user_id: str) -> str:
        """Determine variant based on user ID for consistent assignment"""
        # Use hash for deterministic assignment
        hash_value = int(
            hashlib.md5(f"{self.name}:{user_id}".encode()).hexdigest(), 16
        )
        bucket = hash_value % 100
        
        cumulative = 0
        for i, split in enumerate(self.traffic_split):
            cumulative += split
            if bucket < cumulative:
                return self.variants[i]["name"]
        
        return self.variants[-1]["name"]

class ABTester:
    """
    A/B testing for LLM deployments
    """
    
    def __init__(self):
        self.experiments = {}
    
    def register_experiment(
        self,
        name: str,
        variants: List[Dict],
        traffic_split: List[int]
    ):
        """Register a new A/B test"""
        assert len(variants) == len(traffic_split)
        assert sum(traffic_split) == 100
        
        self.experiments[name] = Experiment(
            name=name,
            variants=variants,
            traffic_split=traffic_split
        )
    
    def get_variant(self, experiment_name: str, user_id: str) -> Dict:
        """Get the variant for a user"""
        exp = self.experiments.get(experiment_name)
        if not exp:
            raise ValueError(f"Experiment {experiment_name} not found")
        
        variant_name = exp.get_variant(user_id)
        return next(v for v in exp.variants if v["name"] == variant_name)
    
    def run_experiment(self, prompt: str, user_id: str, experiment_name: str):
        """Run A/B test and return results"""
        variant = self.get_variant(experiment_name, user_id)
        
        # Call LLM based on variant
        if variant["model"] == "gpt-4":
            result = call_gpt4(prompt)
        elif variant["model"] == "gpt-3.5-turbo":
            result = call_gpt35(prompt)
        else:
            result = call_claude(prompt)
        
        return {
            "variant": variant["name"],
            "model": variant["model"],
            "result": result
        }

# Usage
tester = ABTester()
tester.register_experiment(
    name="model_comparison",
    variants=[
        {"name": "control", "model": "gpt-4"},
        {"name": "variant_a", "model": "gpt-3.5-turbo"},
        {"name": "variant_b", "model": "claude-3-sonnet"}
    ],
    traffic_split=[40, 40, 20]
)
```

---

## Feature Flags

### Implementation

```python
# feature_flags.py
from typing import Dict, Callable, Any
import json
import os

class FeatureFlagManager:
    """
    Manage feature flags for LLM deployments
    """
    
    def __init__(self):
        self.flags: Dict[str, Dict] = {}
    
    def register_flag(
        self,
        name: str,
        default_value: Any = False,
        description: str = ""
    ):
        """Register a feature flag"""
        self.flags[name] = {
            "default": default_value,
            "description": description,
            "rules": []
        }
    
    def add_rule(
        self,
        flag_name: str,
        condition: Callable[[Dict], bool],
        value: Any
    ):
        """Add a targeting rule"""
        if flag_name not in self.flags:
            raise ValueError(f"Flag {flag_name} not registered")
        
        self.flags[flag_name]["rules"].append({
            "condition": condition,
            "value": value
        })
    
    def is_enabled(
        self,
        flag_name: str,
        context: Dict = None
    ) -> bool:
        """Check if feature flag is enabled"""
        if flag_name not in self.flags:
            return self.flags[flag_name]["default"]
        
        flag = self.flags[flag_name]
        context = context or {}
        
        # Check rules in order
        for rule in flag["rules"]:
            if rule["condition"](context):
                return rule["value"]
        
        return flag["default"]
    
    def get_value(
        self,
        flag_name: str,
        context: Dict = None,
        default: Any = None
    ) -> Any:
        """Get feature flag value"""
        if flag_name not in self.flags:
            return default
        
        if self.is_enabled(flag_name, context):
            return self.flags[flag_name].get("value", default)
        
        return default

# Usage
flags = FeatureFlagManager()

# Register flags
flags.register_flag("new_model", False, "Enable new GPT-4 model")
flags.register_flag("streaming_enabled", True, "Enable streaming responses")
flags.register_flag("enhanced_caching", False, "Enable semantic caching")

# Add targeting rules
flags.add_rule(
    "new_model",
    lambda ctx: ctx.get("user_tier") == "premium",
    True
)

flags.add_rule(
    "enhanced_caching",
    lambda ctx: ctx.get("request_count", 0) > 100,
    True
)

# Check flags in request
def handle_request(request: Dict):
    context = {
        "user_id": request["user_id"],
        "user_tier": get_user_tier(request["user_id"]),
        "request_count": get_request_count(request["user_id"])
    }
    
    # Use flags
    use_new_model = flags.is_enabled("new_model", context)
    use_streaming = flags.is_enabled("streaming_enabled", context)
    
    # Route accordingly
    if use_new_model:
        result = call_gpt4(request["prompt"])
    else:
        result = call_gpt35(request["prompt"])
    
    return result
```

---

## Rollback Strategies

### Automated Rollback

```python
# rollback_manager.py
from typing import Optional, Dict, List
from dataclasses import dataclass
from datetime import datetime
import time

@dataclass
class DeploymentSnapshot:
    version: str
    timestamp: datetime
    config: Dict
    metrics: Dict

class RollbackManager:
    """
    Manage deployment rollbacks
    """
    
    def __init__(self):
        self.snapshots: Dict[str, List[DeploymentSnapshot]] = {}
        self.thresholds = {
            "error_rate": 0.05,      # 5% error rate
            "latency_p99": 5.0,       # 5 seconds
            "success_rate": 0.95      # 95% success rate
        }
    
    def take_snapshot(
        self,
        version: str,
        config: Dict,
        metrics: Dict
    ):
        """Take a deployment snapshot"""
        if version not in self.snapshots:
            self.snapshots[version] = []
        
        snapshot = DeploymentSnapshot(
            version=version,
            timestamp=datetime.now(),
            config=config,
            metrics=metrics
        )
        self.snapshots[version].append(snapshot)
    
    def should_rollback(self, current_metrics: Dict) -> bool:
        """Determine if rollback is needed"""
        if current_metrics.get("error_rate", 0) > self.thresholds["error_rate"]:
            return True
        
        if current_metrics.get("latency_p99", 0) > self.thresholds["latency_p99"]:
            return True
        
        if current_metrics.get("success_rate", 1) < self.thresholds["success_rate"]:
            return True
        
        return False
    
    async def rollback(
        self,
        version: str,
        reason: str
    ) -> bool:
        """Execute rollback to previous version"""
        if version not in self.snapshots or not self.snapshots[version]:
            return False
        
        # Get previous version
        previous = self.snapshots[version][-1]
        
        # Execute rollback
        print(f"Rolling back to version: {previous.version}")
        print(f"Reason: {reason}")
        
        # Apply previous configuration
        await self._apply_config(previous.config)
        
        return True
    
    async def _apply_config(self, config: Dict):
        """Apply configuration (implementation depends on deployment method)"""
        # Kubernetes rollback
        # import subprocess
        # subprocess.run(["kubectl", "rollout", "undo", "deployment/llm-deployment"])
        pass
```

---

## CI/CD Integration

### GitHub Actions Workflow

```yaml
# .github/workflows/llm-deployment.yml
name: LLM Deployment

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov
      
      - name: Run tests
        run: |
          pytest tests/ --cov=llm
      
      - name: Run integration tests
        run: |
          pytest tests/integration/ -v

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v2
      
      - name: Build and push
        uses: docker/build-push-action@v4
        with:
          context: .
          push: true
          tags: |
            ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }}
            ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:latest

  deploy-staging:
    needs: build
    runs-on: ubuntu-latest
    environment: staging
    
    steps:
      - name: Deploy to staging
        run: |
          kubectl set image deployment/llm-staging \
            llm-api=${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }}
      
      - name: Wait for deployment
        run: |
          kubectl rollout status deployment/llm-staging --timeout=300s
      
      - name: Run smoke tests
        run: |
          curl -f https://staging.llm.example.com/health

  deploy-production:
    needs: deploy-staging
    runs-on: ubuntu-latest
    environment: production
    
    steps:
      - name: Deploy canary
        run: |
          # Deploy canary with 10% traffic
          kubectl apply -f canary-deployment.yaml
          kubectl argo rollouts set weighting llm-rollout --weight 10 -n argo-rollouts
      
      - name: Monitor canary
        run: |
          # Wait and check metrics
          sleep 600
          
          # Check error rate
          ERROR_RATE=$(curl -s http://prometheus/api/v1/query?query=sum(rate(llm_requests_total{status=~"5.."}[5m]))/sum(rate(llm_requests_total[5m])))
          
          if (( $(echo "$ERROR_RATE > 0.05" | bc -l) )); then
            echo "Error rate too high, rolling back"
            kubectl argo rollouts abort llm-rollout -n argo-rollouts
            exit 1
          fi
      
      - name: Promote canary
        run: |
          # Full rollout
          kubectl argo rollouts set weighting llm-rollout --weight 100 -n argo-rollouts
```

---

## Best Practices

1. **Start with Blue-Green**: For initial deployments
2. **Use Canary for Production**: Reduces risk significantly
3. **Automate Rollbacks**: Based on metrics and alerts
4. **Monitor Continuously**: Track key metrics during deployment
5. **Use Feature Flags**: For granular control
6. **A/B Test Intelligently**: Test model changes separately
7. **Keep Rollback Simple**: Always have a way to revert quickly
8. **Document Changes**: Track what changed and why
