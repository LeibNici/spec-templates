# Enum Transport Contract

> Enum values are API contracts. Labels are presentation data.

---

## Convention: Value and Label Separation

**Do**: Transport stable machine values and expose labels separately.

**Good**:

```json
{
  "status": "PENDING",
  "statusLabel": "待处理"
}
```

**Bad**:

```json
{
  "status": "待处理"
}
```

**Why**: Labels change with i18n and product wording. Machine values must remain stable for filters, permissions, imports, and integrations.

---

## Convention: Frontend Constants

**Do**: Define frontend enum constants in one module and reuse them in tables, filters, forms, and API adapters.

**Do Not**: Scatter string literals such as `"PENDING"` or `"DONE"` across components.

**Validation**: Search the changed enum value and confirm all references use the shared constant.

---

## Convention: Backend Enum Ownership

**Do**: Keep backend enum values, dictionary rows, and API response fields aligned.

**Do Not**: Add a frontend-only enum value unless backend also documents how it is produced or accepted.

**Validation**: Add a backend serialization test or API contract assertion when enum transport changes.
