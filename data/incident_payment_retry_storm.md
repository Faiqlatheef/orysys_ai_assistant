<!-- department=payments;document_type=incident;access_level=internal;created_date=2026-04-03 -->
# Payment Gateway Incident: Retry Storm During Failover
Incident: INC-2050 | Severity: SEV-1 | Date: 2026-04-03

## Summary
A database failover caused a spike in payment retries and elevated authorization latency. A subset of requests was retried without sufficient jitter, amplifying load on the recovering database.

## Root cause
Retry policy used a fixed short delay and did not cap concurrent retries. Circuit-breaker thresholds were too permissive during failover.

## Resolution and prevention
Operators reduced retry concurrency and restored service. Actions: exponential backoff with jitter, retry budgets, circuit-breaker tuning, and load tests for failover scenarios.
