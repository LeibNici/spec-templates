# External System Integration

> Use this when the backend calls ERP, CRM, payment, identity, message, storage, or any service outside the application boundary.

---

## Boundary Rule

Business modules call an adapter interface. They must not directly connect to an external database, SDK, HTTP endpoint, or file share.

```java
public interface PartnerAdapter {
    PartnerResult submit(PartnerCommand command);
}
```

The adapter owns transport details:

- URL, credentials, profile/account selection
- request headers and body shape
- timeout, retry, buffering, and serialization
- external error mapping
- idempotency and request tracing

---

## Request Contract

Every write or sync call must carry:

- `requestId` or `traceId`
- idempotency key when the external side can create records
- operation name
- sanitized business key
- explicit timeout

For HTTP integrations, propagate `X-Request-ID` or the project-standard tracing header. If both header and body contain a request id, they must match.

Secrets come from configuration or secret management, never constants.

---

## Error Contract

External failures must be mapped before crossing the adapter boundary.

| External Condition | Adapter Result |
|---|---|
| timeout or connection failure | retryable integration error |
| authentication failure | non-retryable configuration error |
| validation/business rejection | business-readable failure with external code |
| malformed response | integration protocol error |
| empty result | valid empty result only when transport and protocol succeeded |

Do not return hard-coded success when the external system was not called.

---

## Sync and Import Rules

For full or incremental sync tasks:

- use a per-domain lock to prevent concurrent full/incremental overlap
- schedule incremental jobs with configurable initial delay
- page through external data with stable cursors or update timestamps
- preload existing local rows in batches
- upsert in batches rather than per-row select/insert/update loops
- expose `BatchOperationResult` or equivalent observability for manual runs

High-volume sync must not enable stdout SQL logging in normal dev or test runs.

---

## Transport Rules

- Set connect, read, and write timeouts explicitly.
- Use bounded retries only for retryable errors.
- Preserve response error body in sanitized logs.
- If the server requires fixed-length bodies, use a buffering request factory or equivalent transport option.
- Keep external DTOs separate from internal VO/DTO types.

---

## Tests Required

- Unit test request mapping from internal command to external request.
- Unit test response mapping for success, business failure, and malformed response.
- Unit test idempotency key and request id propagation.
- Unit test lock contention for manual sync or scheduled sync.
- Static or slice test that scheduled incremental tasks have configurable initial delay.
- Smoke test against a simulator or dev endpoint before enabling production credentials.

---

## Review Checklist

- [ ] Business code depends on an adapter interface, not transport details.
- [ ] All credentials and endpoints are externalized.
- [ ] Request id and idempotency are present where needed.
- [ ] External errors keep code/message context without leaking secrets.
- [ ] Sync writes are batched and observable.
- [ ] Timeouts and retries are explicit.

---

## Related

- `batch-result-observability.md`
- `domain-event-pattern.md`
- `dev-test-code-policy.md`
- `../shared/error-contract.md`
