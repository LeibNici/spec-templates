# State Transition Pattern

> Use this when a domain object has non-trivial lifecycle states.

---

## When To Use

Create a centralized transition helper when any condition is true:

- The object has six or more states.
- The object has six or more transition actions.
- The same state field is written by more than one service.
- A transition writes both the parent row and child records.
- Some actions are allowed from one state but forbidden from another.

Do not introduce a state machine for a simple two- or three-state linear flow that is owned by one service.

---

## Convention: Three-Part Model

**Do**:

1. Define state constants that match persisted values.
2. Define an `Action` enum for transition triggers.
3. Define one `TRANSITIONS` table from current state to allowed target states.

**Good**:

```java
public final class DocumentStatus {
    public static final String DRAFT = "DRAFT";
    public static final String SUBMITTED = "SUBMITTED";
    public static final String APPROVED = "APPROVED";
    public static final String REJECTED = "REJECTED";

    private DocumentStatus() {
    }
}
```

```java
@Component
public class DocumentStateTransitions {

    public enum Action {
        SUBMIT, APPROVE, REJECT
    }

    private static final Map<String, Map<Action, String>> TRANSITIONS = new HashMap<>();

    static {
        Map<Action, String> draft = new EnumMap<>(Action.class);
        draft.put(Action.SUBMIT, DocumentStatus.SUBMITTED);
        TRANSITIONS.put(DocumentStatus.DRAFT, draft);

        Map<Action, String> submitted = new EnumMap<>(Action.class);
        submitted.put(Action.APPROVE, DocumentStatus.APPROVED);
        submitted.put(Action.REJECT, DocumentStatus.REJECTED);
        TRANSITIONS.put(DocumentStatus.SUBMITTED, submitted);

        TRANSITIONS.put(DocumentStatus.APPROVED, new EnumMap<>(Action.class));
        TRANSITIONS.put(DocumentStatus.REJECTED, new EnumMap<>(Action.class));
    }

    public String transition(String currentStatus, Action action) {
        String normalized = normalize(currentStatus);
        Map<Action, String> allowed = TRANSITIONS.get(normalized);
        if (allowed == null) {
            throw new BusinessException("Unknown status: " + currentStatus);
        }
        String target = allowed.get(action);
        if (target == null) {
            throw new BusinessException("Illegal transition: " + normalized + " -> " + action);
        }
        return target;
    }

    public String normalize(String rawStatus) {
        if (rawStatus == null) {
            return DocumentStatus.DRAFT;
        }
        return rawStatus;
    }
}
```

**Do Not**:

```java
if ("DRAFT".equals(document.getStatus())) {
    document.setStatus("SUBMITTED");
}
```

---

## Convention: Service Boundary

**Do**: Execute transition validation and state writes inside one transaction.

```java
@Transactional(rollbackFor = Exception.class)
public void approve(Long id) {
    Document document = requireDocument(id);
    String target = transitions.transition(document.getStatus(), Action.APPROVE);
    document.setStatus(target);
    documentMapper.updateById(document);
    auditMapper.insert(AuditRecord.approved(id));
}
```

**Do Not**:

- Write a status field from multiple services without the centralized transition helper.
- Let child tables become an independent source of truth for parent status.
- Trigger transitions from asynchronous code unless the transaction boundary is explicit.

---

## Convention: Output-Gated Transition

Actions named generate, publish, dispatch, complete, or close usually depend on real output.

**Do**: Write the terminal status only after required output exists.

```java
GenerationResult result = generateChildren(document);
if (result.totalCreated() == 0) {
    throw new BusinessException("No records were generated");
}
document.setStatus(transitions.transition(document.getStatus(), Action.GENERATE));
documentMapper.updateById(document);
```

**Do Not**:

```java
generateChildren(document);
document.setStatus(DocumentStatus.GENERATED);
documentMapper.updateById(document);
```

The bad version makes retry impossible when all child records were skipped or failed.

---

## Tests Required

- Valid transition from each non-terminal state.
- Illegal transition returns a business error.
- Terminal states reject further actions.
- Output-gated actions do not advance status when output count is zero.
- Historical values are covered when `normalize` maps legacy statuses.

---

## Related

- `quality-guidelines.md`
- `error-code.md`
- `domain-event-pattern.md`
