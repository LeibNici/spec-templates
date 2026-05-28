# ID & Time Contract

> IDs and time values cross Java, JavaScript, JSON, database, and UI boundaries. They must be explicit.

---

## Convention: Large IDs

**Do**: Serialize Snowflake, BIGINT-like, and other precision-sensitive IDs as strings.

**Good**:

```json
{
  "id": "1830000000000000001",
  "parentId": "1830000000000000000"
}
```

**Bad**:

```json
{
  "id": 1830000000000000001
}
```

**Validation**: Frontend types use `string` for these IDs and table row keys do not coerce them with `Number(...)`.

---

## Convention: Time Format

**Do**: Use one documented timestamp format for API payloads.

Recommended baseline:

```json
{
  "createdAt": "2026-05-28 09:30:00"
}
```

**Do Not**: Mix epoch milliseconds, local strings, and ISO strings in the same API family.

**Validation**: Backend JSON serialization config and frontend formatting utilities agree on timezone and display format.

---

## Convention: Date Ranges

**Do**: Name range boundaries explicitly, such as `startTime` and `endTime`.

**Do Not**: Send ambiguous arrays unless the API contract already standardizes array ranges.

**Validation**: Query DTO, frontend form model, and mapper SQL use the same inclusive/exclusive boundary semantics.
