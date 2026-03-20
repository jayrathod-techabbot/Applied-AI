# Runbook: Disk Full / Low Disk Space

**Severity**: High / Critical
**Service**: All services with local disk I/O
**Last Updated**: 2024-01-15
**Owner**: Infrastructure SRE Team

---

## Overview

Disk full conditions (ENOSPC) cause I/O failures, application crashes, data
corruption, and database write failures. This is one of the most impactful
infrastructure incidents because virtually every service writes to disk.

---

## Symptoms

- Filesystem at > 95% capacity
- Application errors containing "No space left on device" (ENOSPC)
- Failed log writes — applications stop logging (silent failure)
- Database write failures — data loss risk
- WAL (Write-Ahead Log) failures in PostgreSQL/MySQL — corruption risk
- Core dumps and crash reports cannot be written
- Health checks failing because health status files cannot be updated

---

## Immediate Triage (First 2 minutes)

1. Confirm which filesystem is full:
   ```bash
   df -h
   df -ih  # Check inode exhaustion too
   ```

2. Find the largest directories:
   ```bash
   du -sh /* 2>/dev/null | sort -rh | head -20
   du -sh /var/* 2>/dev/null | sort -rh | head -10
   ```

3. Check if it is a log volume or data volume (different remediation paths).

---

## Diagnosis Steps

### Step 1: Identify disk usage breakdown
```bash
df -h
du -sh /var/log/* | sort -rh | head -20
du -sh /tmp/*
du -sh /var/lib/docker/* 2>/dev/null | sort -rh | head -10
```

### Step 2: Find largest individual files
```bash
find / -type f -size +100M 2>/dev/null | head -20
find /var/log -type f -name "*.log" -size +50M
```

### Step 3: Check for deleted-but-open files (holding space)
```bash
# Files deleted but still held open by processes consume disk space
lsof | grep deleted | grep -v proc
# These files won't be released until the process releases them (restart)
```

### Step 4: Check Docker images and containers
```bash
docker system df
docker images | sort -k7 -rh | head -10
```

### Step 5: Check database WAL/journal size
```bash
# PostgreSQL
du -sh /var/lib/postgresql/*/pg_wal/
ls -lh /var/lib/postgresql/*/pg_wal/ | tail -20
```

---

## Remediation

### Option A: Rotate application logs (safest, fastest)
```bash
rotate_logs app-service
# OR manually:
logrotate -f /etc/logrotate.d/app-service
```
**Risk**: None. Log rotation is a standard safe operation.

### Option B: Remove old log files (> 7 days)
```bash
free_disk_space /var/log
# OR manually:
find /var/log -name "*.log.*" -mtime +7 -delete
find /var/log -name "*.gz" -mtime +7 -delete
# Verify space recovered:
df -h /var/log
```
**Risk**: Low. Old compressed logs are removed.

### Option C: Clean Docker artifacts
```bash
docker system prune -f
docker image prune -a -f --filter "until=168h"
```
**Risk**: Low-Medium. Running containers and used images are not affected.

### Option D: Remove temporary files
```bash
find /tmp -mtime +1 -delete
find /var/tmp -mtime +7 -delete
```
**Risk**: Low. Temp files older than 1 day should not be actively used.

### Option E: Restart service to release deleted-but-open file handles
```bash
# Identify which service holds the deleted file
lsof | grep deleted | awk '{print $1}' | sort -u
# Restart that service
systemctl restart app-service
```
**Risk**: Medium. Brief service interruption.

---

## Verification

```bash
df -h  # Filesystem should be below 80%
# Test that the application can write:
touch /var/log/app/test-write-$(date +%s).tmp && echo "Write OK" && rm $_
# Restart monitoring:
systemctl status disk-monitor
```

---

## Prevention

1. **Log rotation**: Ensure logrotate runs daily with `compress` and `dateext` options.
   Keep logs for maximum 14 days.

2. **Alerting thresholds**: Page at 80% (warning), 90% (high), 95% (critical).
   Do NOT wait until 95% to act — recovery is harder at that point.

3. **Separate log volumes**: Mount `/var/log` on a dedicated volume separate
   from the OS and application data volumes.

4. **Log shipping**: Ship logs to centralized logging (ELK, Splunk, CloudWatch)
   and reduce local retention to 3 days.

5. **Docker cleanup cron**: Schedule `docker system prune -f` weekly.

6. **Capacity planning**: Review disk growth trends monthly. Provision 30%
   headroom above peak observed usage.

---

## Escalation

- **Filesystem > 99%**: Escalate immediately — applications are likely crashing
- **Database disk full**: Escalate to DBA team immediately — data loss risk
- **Cannot recover space**: Request emergency volume expansion from cloud team
