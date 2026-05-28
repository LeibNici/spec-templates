# 7. Effective Row Filters

> Use this for tables that contain historical versions, hierarchical rows, soft-deleted rows, tenant partitions, or time-effective records.

---

## Core Rule

Queries that need the current business view must include every effective-row predicate explicitly. A table can contain many physical rows for one logical item; missing one predicate causes row inflation, stale data, or mixed hierarchy levels.

---

## Common Predicates

| Table Pattern | Required Predicate Examples |
|---|---|
| Soft delete | `deleted = 0` |
| Versioned master data | `status = 'ACTIVE'` or `is_current = 1` |
| Draft/published workflow | `publish_status = 'PUBLISHED'` for consumer queries |
| Temporal validity | `valid_from <= now` and `(valid_to IS NULL OR valid_to > now)` |
| Tenant partition | `tenant_id = :tenantId` |
| Self-referencing hierarchy | `parent_id IS NULL` for root-level queries, or explicit `parent_id = :id` for child queries |
| Typed hierarchy | `node_type = :expectedType` plus the hierarchy predicate |

The exact column names are project-specific. The rule is not.

---

## Mapper Pattern

Prefer shared mapper fragments or helper methods for repeated current-row predicates.

```xml
<sql id="EffectiveItemPredicate">
  item.deleted = 0
  AND item.status = 'ACTIVE'
</sql>

SELECT item.id, item.code, item.name
  FROM item
 WHERE <include refid="EffectiveItemPredicate" />
   AND item.code = #{code}
```

For MyBatis-Plus wrappers, keep the predicate in a named method.

```java
private LambdaQueryWrapper<Item> effectiveItemQuery() {
    return Wrappers.lambdaQuery(Item.class)
            .eq(Item::getDeleted, 0)
            .eq(Item::getStatus, ItemStatus.ACTIVE);
}
```

---

## History Endpoints

History, audit, and version-management endpoints may intentionally return non-current rows. They must make that intent visible in the method name, route, and query object.

Examples:

- `GET /api/items/{id}/versions`
- `ItemVersionQuery`
- `selectItemHistoryPage`

Do not let a generic `page()` endpoint accidentally become a history query.

---

## Tests Required

For every mapper/service that reads a current business view from a stateful table, add a test with at least two physical rows for one logical item.

Required cases:

- active plus draft or archived version
- root row plus child row when querying root-level data
- deleted row plus active row
- tenant A row plus tenant B row when tenancy exists

The assertion must prove only the effective row is returned.

---

## Review Checklist

- [ ] Query intent is current view, history view, or hierarchy traversal.
- [ ] Current-view queries include all effective predicates.
- [ ] Repeated predicates are centralized in mapper XML fragments or helper methods.
- [ ] `LEFT JOIN` predicates are placed in the `ON` clause when they constrain the joined table.
- [ ] Tests include duplicate physical rows that would fail without the predicate.

---

## Related

- `01-sql-ownership.md`
- `06-soft-delete-unique.md`
- `../versioned-reference-pattern.md`
