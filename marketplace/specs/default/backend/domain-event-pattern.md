# Domain Event Pattern

> Use this for same-process cross-module notifications after a transaction commits.

---

## When To Use

Use Spring domain events when:

- Module A writes data and module B should react after commit.
- The publisher does not need the listener's return value.
- The listener can run independently and be retried or compensated.

Do not use Spring events when:

- The publisher requires a synchronous result.
- The work must be strongly consistent in the same transaction.
- The consumer is another process or service. Use a message queue or outbox pattern instead.

---

## Convention: Event Shape

**Do**: Publish small immutable events with IDs and minimal context.

```java
public record DocumentApprovedEvent(
        Long documentId,
        Long operatorId,
        String requestId
) {
}
```

**Do Not**:

```java
public record DocumentApprovedEvent(DocumentEntity entity) {
}
```

Passing full entities couples modules, leaks lazy fields, and makes event serialization harder if the event later moves to an outbox or queue.

---

## Convention: Publish Inside Transaction

**Do**: Publish after the core write, inside the service transaction.

```java
@Transactional(rollbackFor = Exception.class)
public void approve(Long id) {
    Document document = requireDocument(id);
    document.setStatus(DocumentStatus.APPROVED);
    documentMapper.updateById(document);
    publisher.publishEvent(new DocumentApprovedEvent(id, currentUserId(), requestId()));
}
```

Listeners use `AFTER_COMMIT`, so they run only after the publisher transaction succeeds.

---

## Convention: Listen After Commit

**Do**:

```java
@Component
@RequiredArgsConstructor
public class DocumentApprovedListener {

    private static final Logger log = LoggerFactory.getLogger(DocumentApprovedListener.class);

    private final NotificationService notificationService;

    @TransactionalEventListener(phase = TransactionPhase.AFTER_COMMIT)
    public void onApproved(DocumentApprovedEvent event) {
        if (event.documentId() == null) {
            log.warn("document approved event skipped: documentId is null");
            return;
        }
        try {
            notificationService.notifyApproved(event.documentId());
        } catch (Exception ex) {
            log.warn("document approved listener failed: {}", ex.getMessage());
        }
    }
}
```

**Do Not**:

- Use synchronous `@EventListener` for business side effects.
- Throw listener exceptions back to the publisher for fire-and-forget workflows.
- Put multiple unrelated event handlers in one listener class.
- Make listeners non-idempotent.

---

## Failure Handling

| Failure Type | Expected Handling |
|---|---|
| Optional side effect failed | Log a warning with IDs and keep publisher committed |
| Critical side effect failed | Write an audit/compensation record and alert operators |
| Listener may run twice | Make writes idempotent with unique keys or status checks |
| Cross-process delivery needed | Replace or extend with outbox/MQ, not in-memory events |

---

## Tests Required

- Publisher transaction publishes the event after the core write path.
- Listener ignores events that do not match its responsibility.
- Listener handles duplicate events idempotently.
- Listener failure does not roll back the publisher transaction when the contract is fire-and-forget.

---

## Related

- `state-transition-pattern.md`
- `high-volume-tables/03-write-path.md`
- `topology-agnostic.md`
