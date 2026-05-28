# Batch Result Observability

> Use this for imports, sync jobs, dispatch flows, bulk commands, and any loop where one item can fail while the batch continues.

---

## Core Rule

`log.warn + continue` is not an outcome contract. If a row is skipped, failed, deduplicated, or downgraded, the caller and operators must be able to see:

- how many items were processed
- how many succeeded
- how many were skipped or failed
- which business key or row caused each problem
- whether the issue is retryable

This applies to manual APIs, scheduled jobs, message consumers, and integration sync tasks.

---

## Result Shape

Use a typed result object instead of a loose `Map`.

```java
public record BatchOperationResult<T>(
        int totalCount,
        int successCount,
        int skippedCount,
        int failedCount,
        List<T> items,
        List<FailureDetail> failureDetails) {
}

public record FailureDetail(
        Integer rowNo,
        String businessKey,
        String reasonCode,
        String message,
        boolean retryable) {
}
```

Rules:

- `totalCount = successCount + skippedCount + failedCount` unless the source stream is unknown length.
- `failureDetails` must be bounded when batches can be large. Keep a summary counter even if details are truncated.
- `reasonCode` is stable and machine-readable; `message` is human-readable.
- Business keys must be sanitized before being returned to the frontend.

---

## Error Semantics

| Situation | Required Behavior |
|---|---|
| One independent item invalid | collect `FailureDetail`, continue if the command is explicitly partial-success capable |
| Systemic precondition missing | fail the whole command before the loop |
| Database schema, network, or programming error | throw and fail the command; do not turn it into a skip |
| Duplicate input row | count as skipped or failed according to the API contract, never ignore silently |
| All rows skipped | return an explicit zero-success result with reasons, not a generic success toast |

If partial success is not an accepted product behavior, fail fast and roll back the whole command.

---

## Metrics and Logs

Every repeated skip/failure category must have a low-cardinality metric.

```java
Counter.builder("batch.item.skipped")
        .tag("operation", "itemImport")
        .tag("reason", "missing_required_field")
        .register(meterRegistry)
        .increment();
```

Do:

- tag by operation and reason code
- include `traceId` or `requestId` in logs
- log the first few representative details at `warn`

Do not:

- tag metrics with unbounded values such as item id, user id, or raw message
- log only the item and continue
- hide `DuplicateKeyException`, timeout, or mapper errors as business skips

---

## API Contract

For API-driven batches:

- The response body must contain the batch result even when the transport status is `200`.
- Partial success must be visible to the UI. Do not rely on a generic success toast.
- A fully rejected request should use the standard error response from `../shared/error-contract.md`.
- The frontend should render `failureDetails` or provide a downloadable detail file for large batches.

---

## Review Checklist

- [ ] All `continue`, `return null`, and default branches in the batch loop are observable.
- [ ] The caller can distinguish empty input, all skipped, partial success, and full success.
- [ ] Metrics use stable low-cardinality tags.
- [ ] Failure details include row number or business key where available.
- [ ] Systemic failures still fail loudly.
- [ ] Tests cover one success, one skipped, one failed, and all skipped.

---

## Related

- `error-handling.md`
- `code-smell-prevention/09-silent-skip.md`
- `../shared/error-contract.md`
