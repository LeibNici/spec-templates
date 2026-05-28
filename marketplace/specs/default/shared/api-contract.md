# API Contract

> Backend and frontend must treat API shape as a shared contract, not as implementation detail.

---

## Convention: Response Shape

**Do**: Return one stable envelope shape for normal API responses.

**Do Not**: Mix raw objects, arrays, and custom envelopes for similar endpoints.

**Good**:

```json
{
  "code": "0",
  "message": "OK",
  "data": {
    "id": "1830000000000000001",
    "name": "Example"
  }
}
```

**Bad**:

```json
{
  "success": true,
  "result": {
    "id": 1830000000000000001
  }
}
```

**Validation**: Backend controller tests assert response fields; frontend API functions declare typed return values instead of `any`.

---

## Convention: Pagination

**Do**: Keep list response field names stable across backend and frontend.

**Good**:

```json
{
  "records": [],
  "total": 0,
  "pageNum": 1,
  "pageSize": 20
}
```

**Do Not**: Return database-specific pagination internals or rename fields per module.

**Validation**: Table pages map only contract fields; no page reads framework-internal names such as `list`, `rows`, or `items` unless the project contract says so.

---

## Convention: Request DTOs

**Do**: Separate create, update, and query DTOs when validation rules differ.

**Do Not**: Reuse a VO as a write DTO.

**Validation**: Backend validation annotations match frontend form required rules and frontend types mirror the DTO fields.
