# Shared Contract Specs

> Applies to features that cross backend and frontend boundaries.

---

## Applies To

- Backend API request/response contracts.
- Frontend API clients, VO/DTO types, route guards, and error handling.
- Shared enum, ID, timestamp, pagination, and error-code semantics.

---

## Pre-Development Checklist

Before implementing a cross-layer feature, read the files that match the change:

- **All cross-layer tasks**: `api-contract.md` + `id-time-contract.md`
- **Enum / status / dictionary changes**: `enum-transport-contract.md`
- **Error response / error-code changes**: `error-contract.md`
- **Backend implementation**: also read `../backend/index.md`
- **Frontend implementation**: also read `../frontend/index.md`
- **Full-stack workflow**: also read `../guides/full-stack-workflow.md`

---

## Quality Checklist

- [ ] Backend response fields match frontend types exactly.
- [ ] Snowflake/BIGINT-like IDs are serialized as strings across the boundary.
- [ ] Time fields have one documented format and timezone assumption.
- [ ] Enums expose stable machine values and user-facing labels separately.
- [ ] Error responses include stable codes and safe messages.
- [ ] Contract changes include backend tests and frontend type/API call updates.

---

## Spec Map

| File | When to Read | Status |
|---|---|---|
| [API Contract](./api-contract.md) | Adding or changing request/response shape, pagination, or HTTP semantics | Filled |
| [Enum Transport Contract](./enum-transport-contract.md) | Adding or changing status, enum, dictionary, or select-option values | Filled |
| [ID & Time Contract](./id-time-contract.md) | Adding IDs, timestamps, date ranges, or frontend table keys | Filled |
| [Error Contract](./error-contract.md) | Adding business errors, validation errors, or global error handling | Filled |

---

**Language**: 中英混排（术语英文，铁律中文）。
