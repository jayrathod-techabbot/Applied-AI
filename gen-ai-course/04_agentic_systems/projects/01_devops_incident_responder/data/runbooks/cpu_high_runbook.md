# Runbook: High CPU Utilization

**Severity**: High / Critical
**Service**: Any application server
**Last Updated**: 2024-01-15
**Owner**: Platform SRE Team

---

## Overview

This runbook covers diagnosis and remediation of sustained high CPU utilization
(> 90%) on application servers. High CPU typically causes increased latency,
request timeouts, and cascading failures to dependent services.

---

## Symptoms

- CPU utilization > 90% for more than 5 minutes
- System load average > 2× number of CPU cores
- Increased request response times (p99 latency spike)
- HTTP 503 / 502 errors from upstream load balancer
- Worker thread pool exhaustion in application servers
- GC (garbage collection) pause times increasing
- Memory pressure co-occurring with CPU spike

---

## Immediate Triage (First 2 minutes)

1. Confirm the alert is real (not a monitoring glitch):
   ```
   top -b -n 1 | head -20
   uptime
   ```

2. Identify if it is isolated to one host or affecting the cluster:
   ```
   kubectl top nodes
   kubectl top pods --all-namespaces --sort-by=cpu | head -20
   ```

3. Notify the on-call team via PagerDuty if not already paged.

---

## Diagnosis Steps

### Step 1: Identify top CPU-consuming processes
```bash
top -b -n 1 -H
ps aux --sort=-%cpu | head -20
```

### Step 2: Check for runaway or zombie processes
```bash
ps aux --sort=-%cpu | awk '$8 ~ /Z/ {print $0}'
# Look for processes with CPU% > 50 sustained
```

### Step 3: Check application thread dumps (Java/JVM)
```bash
# For Java applications
jstack $(pgrep -f app-server) > /tmp/thread_dump_$(date +%s).txt
# Look for BLOCKED threads and deadlocks
```

### Step 4: Check recent deployments
```bash
git log --oneline -10  # Recent code changes
kubectl rollout history deployment/app-server
```

### Step 5: Check for infinite loops or tight retry loops in logs
```bash
grep -E "retry|loop|recursion" /var/log/app/*.log | tail -50
```

### Step 6: Verify auto-scaling status
```bash
kubectl get hpa
kubectl describe hpa app-server
```

---

## Remediation

### Option A: Restart the affected service (quick fix)
```bash
systemctl restart app-service
# OR for Kubernetes:
kubectl rollout restart deployment/app-server
```
**Risk**: Brief service interruption (30–60 seconds). Health checks will
redirect traffic during restart.

**Rollback**: Service auto-starts. If it fails to start:
```bash
kubectl rollout undo deployment/app-server
```

### Option B: Scale horizontally to distribute load
```bash
kubectl scale deployment app-server --replicas=3
# Verify pods are running:
kubectl get pods -l app=app-server
```
**Risk**: Low. Increases cluster resource consumption.

**Rollback**:
```bash
kubectl scale deployment app-server --replicas=1
```

### Option C: Kill the runaway process (last resort)
```bash
# Identify the PID
ps aux --sort=-%cpu | head -5
# Kill gracefully first
kill -TERM <PID>
# If it doesn't stop within 30s:
kill -KILL <PID>
```
**Risk**: High. Data loss possible if process is mid-transaction.

---

## Verification

After applying remediation, confirm resolution:
```bash
watch -n 5 "top -b -n 1 | head -5"
# CPU should drop below 70% within 2–3 minutes
kubectl get pods  # All pods should be Running
curl -s http://app-server/health | jq .  # Health endpoint should return 200
```

---

## Prevention

1. **Auto-scaling**: Configure Kubernetes HPA with CPU target 70%:
   ```yaml
   targetCPUUtilizationPercentage: 70
   ```

2. **Resource limits**: Set CPU limits on all pods to prevent one pod consuming all node CPU.

3. **Load testing**: Run load tests before deployments to detect CPU regressions.

4. **Profiling**: Use async-profiler or py-spy to identify hot code paths.

5. **Circuit breakers**: Implement circuit breakers to prevent cascading retry storms.

---

## Escalation

- **15 minutes with no improvement** → Escalate to application development team
- **30 minutes**: Consider rollback to previous stable deployment
- **Service down > 1 hour**: Invoke incident commander protocol
