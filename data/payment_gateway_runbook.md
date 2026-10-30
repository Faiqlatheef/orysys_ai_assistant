<!-- department=payments;document_type=runbook;access_level=internal;created_date=2026-01-18 -->
# Payment Gateway Operations Runbook

## First response
1. Check authorization success rate, p95 latency, and upstream timeout rate.
2. Compare errors across gateway instances and partner endpoints.
3. Inspect recent certificate, network, and configuration changes.
4. For retry spikes, inspect queue depth, retry rate, database health, and circuit-breaker state.

## Safety
Do not disable fraud checks or bypass idempotency controls to restore throughput. Escalate to the Payments on-call lead for any customer-impacting SEV-1 event.
