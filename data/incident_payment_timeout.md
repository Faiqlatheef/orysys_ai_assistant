<!-- department=payments;document_type=incident;access_level=internal;created_date=2026-02-12 -->
# Payment Gateway Incident: Upstream Timeout Spike
Incident: INC-2041 | Severity: SEV-2 | Date: 2026-02-12

## Summary
Payment authorization latency rose after an upstream certificate rotation. Requests timed out while the gateway attempted to establish connections to the acquiring partner.

## Root cause
The certificate bundle on two gateway instances was stale after a partial rollout. Health checks did not verify the full upstream TLS handshake.

## Resolution and prevention
The on-call team refreshed the bundle and restarted affected instances. Follow-up actions: validate certificate expiry in CI, test full TLS handshakes in readiness probes, and alert on upstream timeout rate.
