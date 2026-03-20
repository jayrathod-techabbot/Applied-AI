# Runbook: High Error Rate / Error Spike

**Severity**: High / Critical
**Service**: API services, microservices
**Last Updated**: 2024-01-15
**Owner**: Application SRE Team

---

## Overview

An error rate spike (HTTP 5xx errors > 5% of requests, or > 10 errors/minute)
indicates a service degradation that is directly impacting users. Error spikes
may be caused by: bad deployments, dependency failures, database issues,
resource exhaustion, or external API timeouts.

---

## Symptoms

- HTTP 500 / 502 / 503 / 504 error rate elevated
- Error count > 10/minute (warning) or > 50/minute (critical)
- Spike in exception logs (NullPointerException, ConnectionRefusedException, TimeoutException)
- Circuit breaker OPEN state for downstream dependencies
- Elevated p99/p999 response latency
- User-facing errors (checkout failures, login failures, payment failures)
- PagerDuty / alerting system triggered
- Revenue impact alerts

---

## Immediate Triage (First 2 minutes)

1. Confirm scope of impact:
   ```bash
   # What percentage of requests are failing?
   # Check your APM dashboard (Datadog/New Relic/Prometheus)
   curl -s "http://prometheus:9090/api/v1/query?query=rate(http_requests_total{status=~'5..'}[5m])"
   ```

2. Check if a recent deployment triggered the spike:
   ```bash
   kubectl rollout history deployment/payment-service
   git log --oneline -5
   ```

3. Check if the error is in ONE service or cascading:
   ```bash
   kubectl get pods --all-namespaces | grep -v Running
   kubectl top pods --sort-by=memory | head -10
   ```

---

## Diagnosis Steps

### Step 1: Examine error logs for root cause
```bash
kubectl logs deployment/payment-service --tail=100 | grep -E "ERROR|EXCEPTION|FATAL"
# Or for Docker:
docker logs payment-service --tail=100 2>&1 | grep -E "ERROR|Exception"
```

### Step 2: Check database connectivity
```bash
# Test DB connection from the service pod
kubectl exec -it $(kubectl get pod -l app=payment-service -o name | head -1) -- \
    python -c "import psycopg2; psycopg2.connect(os.environ['DATABASE_URL'])"
# Check DB replication lag
psql -h payment-db -c "SELECT now() - pg_last_xact_replay_timestamp() AS lag;"
```

### Step 3: Check external dependency health
```bash
# Check external API availability
curl -I --max-time 5 https://api.stripe.com/v1/
# Check internal service dependencies
kubectl get endpoints payment-service
```

### Step 4: Check for database deadlocks or slow queries
```bash
# PostgreSQL
psql -h payment-db -c "SELECT pid, query, wait_event_type, wait_event, state FROM pg_stat_activity WHERE state != 'idle' ORDER BY query_start;"
psql -h payment-db -c "SELECT * FROM pg_locks WHERE NOT granted;"
```

### Step 5: Review circuit breaker status
```bash
# Check if resilience4j / hystrix has opened the circuit
curl http://payment-service:8080/actuator/health | jq '.components.circuitBreakers'
```

### Step 6: Check for resource exhaustion
```bash
kubectl top pod -l app=payment-service
kubectl describe pod $(kubectl get pod -l app=payment-service -o name | head -1) | grep -A 5 "Limits\|Requests"
```

---

## Remediation

### Option A: Rollback bad deployment (if deployment-triggered)
```bash
kubectl rollout undo deployment/payment-service
# Verify rollback:
kubectl rollout status deployment/payment-service
```
**Risk**: Low if previous version is known-stable.

**Rollback**: Re-deploy the new version after fixing the bug.

### Option B: Restart the affected service
```bash
kubectl rollout restart deployment/payment-service
# Monitor pod restart:
kubectl get pods -l app=payment-service -w
```
**Risk**: Medium. Brief traffic disruption during restart.
**When to use**: Memory leaks, connection pool exhaustion, thread deadlocks.

### Option C: Scale up to handle increased load
```bash
kubectl scale deployment payment-service --replicas=5
# Wait for pods to be ready:
kubectl rollout status deployment/payment-service
```
**Risk**: Low. Increases resource consumption.
**When to use**: Traffic surge overwhelming the service.

### Option D: Kill and restart a specific unhealthy pod
```bash
# Identify the bad pod
kubectl get pods -l app=payment-service
kubectl describe pod payment-service-xxx | grep -A 10 "Events"
# Delete it (Kubernetes will restart it automatically)
kubectl delete pod payment-service-xxx
```
**Risk**: Low. Kubernetes restarts the pod automatically.

### Option E: Redirect traffic away from affected instance
```bash
# If using Kubernetes, remove the pod from service endpoints temporarily
kubectl label pod payment-service-xxx app=payment-service-quarantine
# Traffic will stop routing to this pod
```
**Risk**: Low. Reduces capacity but isolates the problematic instance.

---

## Circuit Breaker Management

If a circuit breaker is OPEN due to the error spike:
```bash
# Reset the circuit breaker manually (if Resilience4j)
curl -X POST http://payment-service:8080/actuator/circuitbreakers/payment-db/reset
# Verify state:
curl http://payment-service:8080/actuator/health | jq '.components.circuitBreakers'
```

---

## Verification

```bash
# Watch error rate return to normal (should drop within 2-3 minutes of fix)
watch -n 5 "kubectl logs deployment/payment-service --tail=10 | grep -c ERROR"

# Test an end-to-end payment flow
curl -X POST http://payment-service/api/v2/payments/health-check

# Confirm error rate in monitoring
# Error rate should be < 1% within 5 minutes
```

---

## Prevention

1. **Canary deployments**: Deploy to 5% of traffic first. Monitor error rate for
   5 minutes before proceeding to full rollout.

2. **Circuit breakers**: Configure Resilience4j/Hystrix with:
   - `failureRateThreshold: 50`
   - `waitDurationInOpenState: 60s`
   - `permittedNumberOfCallsInHalfOpenState: 10`

3. **Timeout configuration**: Set explicit timeouts for all external API calls.
   Never use infinite timeout.

4. **Database connection pooling**: Use PgBouncer or HikariCP. Set pool size
   to `max_connections / num_instances`.

5. **Load testing**: Run chaos engineering tests (Chaos Monkey / Gremlin) to
   validate circuit breakers and fallback behavior.

6. **SLO alerting**: Alert at 99.5% availability (1-hour window) to catch
   error spikes early before SLA is breached.

---

## Escalation

- **Error rate > 10% for 5 minutes**: Declare P1 incident, join war room
- **Revenue-impacting service (payments, checkout)**: Escalate immediately
- **Cannot identify root cause within 15 minutes**: Rollback last deployment
- **Database data loss suspected**: Escalate to DBA and Data Engineering leads
