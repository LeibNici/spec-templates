# Audit Log Pattern

> Use this for user-visible writes, security-sensitive actions, state changes, and integration commands that need traceability.

---

## Core Rule

Audit logging records what happened after the business result is known. It must not become hidden business logic, and it must not make successful business transactions roll back because the audit sink is temporarily unavailable unless the domain explicitly requires strict audit durability.

---

## What to Capture

Minimum fields:

- `requestId` or `traceId`
- actor id/name and actor type
- action
- resource type and resource id
- result: success or failure
- happened time
- client ip or channel when available
- sanitized request summary
- failure code/message when failed

Optional fields:

- before/after diff
- tenant or organization id
- external system name
- correlation id from a message or integration call

Never store secrets, raw tokens, passwords, private keys, or full personal identifiers unless the project has an explicit compliance rule for them.

---

## Write Path

Recommended pattern:

1. Controller/service executes the business command.
2. An annotation, explicit publisher, or domain event builds an audit event.
3. A listener writes the audit row after commit.
4. The audit writer uses a dedicated executor and bounded queue.
5. Failures are logged and counted with metrics.

For strict compliance domains, define the exception explicitly: audit write failure may fail the business command only when the product/security requirement says so.

---

## Table and Query Design

Audit and operation-log tables are high-volume tables. Apply:

- redundant searchable columns for common filters
- time-range required queries
- indexes for actor, resource, action, and time
- retention and archival policy
- no unbounded payload column queries

Follow `high-volume-tables/_index.md` for DDL, write path, query, and archival rules.

---

## Forbidden Patterns

- Writing audit logs inside the main transaction with no reason.
- Logging only free-form text with no resource id or action.
- Swallowing audit writer failures without metrics.
- Storing raw request/response bodies that contain secrets.
- Using audit tables as the source of truth for business state.
- Building reports from JSON payload scans instead of indexed columns.

---

## Tests Required

- Successful write produces an audit event with actor, action, resource, and result.
- Failed command records a failure audit when required by the domain.
- Business rollback does not create a success audit row.
- Sanitization removes secrets from payload summaries.
- Audit writer failure is observable and does not break business flow unless strict mode is configured.

---

## Related

- `domain-event-pattern.md`
- `high-volume-tables/_index.md`
- `logging-guidelines.md`
