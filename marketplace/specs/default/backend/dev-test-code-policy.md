# Dev/Test Code Policy

> Code under `dev`, `test`, `mock`, local profile, and test fixtures follows the same architecture rules as production code.

---

## Core Rule

Environment labels do not create a relaxed zone. A class named `Dev*`, `Mock*`, `Fake*`, or annotated with `@Profile("dev")` can still corrupt data, hide integration drift, or ship into an artifact. Apply the same layer boundaries, type safety, error handling, and dependency rules.

---

## Allowed Patterns

| Need | Allowed Pattern |
|---|---|
| Local-only seed data | idempotent SQL script or test fixture, never a startup bean mutating business tables |
| External dependency unavailable in dev | implement the same adapter interface with a local adapter or simulator |
| Unit test collaborator | mock the collaborator inside the test scope |
| Integration test data | create through mapper/service/test fixture and clean up per test |
| Feature flag in dev | config property plus `@ConditionalOnProperty` |

---

## Forbidden Patterns

```java
@Profile("dev")
@Component
public class DevDataInitializer {
    @PostConstruct
    void init() {
        jdbcTemplate.update("insert into item(id, name) values(1, 'demo')");
    }
}
```

Forbidden:

- startup hooks that insert/update/delete business rows
- `JdbcTemplate` string SQL bypassing mapper ownership for business data
- direct cross-module table access from dev/test helpers
- hard-coded success responses that bypass a real adapter contract
- manual id generation such as `MAX(id) + 1`
- dev profile code that disables validation, permission, or state checks without a documented property and tests

---

## Mock Boundary

Mocks are allowed only at boundaries:

- external HTTP/RPC adapters
- message brokers
- object storage
- payment, email, SMS, identity provider, and other third-party services

Mocks are not allowed as application data sources for normal frontend flows. A Vue page should call the real backend endpoint, even if the backend initially returns an empty but valid response.

---

## Test Fixture Rules

- Fixtures must be deterministic and isolated per test.
- Tests must not depend on execution order.
- Cleanup must be explicit or transactional.
- Test builders should fill fields that the UI/API displays, not only required database columns.
- Test code must fail loudly on setup errors.

---

## Review Checklist

- [ ] No dev/test startup bean mutates business data.
- [ ] Dev adapters implement the same interface and response/error shape as production adapters.
- [ ] Test fixtures use supported mapper/service paths or test-only schema setup.
- [ ] No profile-specific branch bypasses validation, permission, or state transition rules.
- [ ] Mock data is confined to tests or external adapter simulation.

---

## Related

- `code-smell-prevention/10-dev-mock.md`
- `../guides/full-stack-workflow.md`
- `test-strategy/_index.md`
