# 06 · Soft Delete and Unique Keys

> Applies to tables that use MyBatis-Plus logical delete fields such as `deleted`.

---

## Problem

Database unique indexes still see logically deleted rows. MyBatis-Plus queries usually filter `deleted = 0`.

If a table has `UNIQUE KEY uk_code (code)`, this sequence fails:

1. User deletes row `code = A`.
2. MyBatis-Plus marks it as `deleted = 1`.
3. The service checks active rows and sees no `code = A`.
4. Insert of a new active `code = A` hits the physical unique index.

The user sees a database conflict for a value that is no longer visible in the UI.

---

## Pattern A: Master Table With Reusable Code

Use this when a single master-data row owns a business code that users may reuse after deletion.

### DDL

**Do**:

```sql
CREATE TABLE md_item (
  id BIGINT NOT NULL,
  item_code VARCHAR(80) NOT NULL,
  item_name VARCHAR(200) NOT NULL,
  deleted TINYINT NOT NULL DEFAULT 0,
  PRIMARY KEY (id),
  UNIQUE KEY uk_item_code_deleted (item_code, deleted)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
```

### Delete Path

**Do**: Rename the business code before logical delete.

```java
@Transactional(rollbackFor = Exception.class)
public void deleteItem(Long id) {
    Item item = requireItem(id);
    String deletedCode = item.getItemCode() + "-DEL-" + id;
    itemMapper.updateCode(id, deletedCode);
    itemMapper.deleteById(id);
}
```

**Do Not**:

```java
itemMapper.deleteById(id);
```

Direct logical delete leaves the original code in the physical unique index.

### Checklist

- [ ] Unique key includes the logical delete column.
- [ ] Delete and batch-delete paths both rename the business code before delete.
- [ ] Code column length reserves suffix space.
- [ ] Create/update duplicate checks still query active rows only.

---

## Pattern B: Sync Relation Table

Use this when a relation table is overwritten by "delete active rows, then insert the new set" logic.

**Do**: Use a normal index and deduplicate in Java.

```sql
CREATE TABLE item_tag_rel (
  id BIGINT NOT NULL,
  item_id BIGINT NOT NULL,
  tag_id BIGINT NOT NULL,
  deleted TINYINT NOT NULL DEFAULT 0,
  PRIMARY KEY (id),
  INDEX idx_item_tag_active (item_id, tag_id, deleted)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
```

```java
List<Long> tagIds = new ArrayList<>(new LinkedHashSet<>(command.getTagIds()));
relationMapper.deleteActiveByItemId(itemId);
for (Long tagId : tagIds) {
    relationMapper.insert(new ItemTagRelation(itemId, tagId));
}
```

**Do Not**:

```sql
UNIQUE KEY uk_item_tag_deleted (item_id, tag_id, deleted)
```

On repeated sync, multiple deleted historical rows with the same key can collide on `deleted = 1`.

---

## Convention: Do Not Assume Uniqueness On Normal Indexes

Once a relation table uses a normal index, `selectOne(...)` is not a valid uniqueness strategy.

**Do**:

```java
List<ItemTagRelation> rows = relationMapper.selectList(activeByItemAndTag(itemId, tagId));
if (rows.size() > 1) {
    throw new BusinessException("Duplicate active relation rows found");
}
```

**Do Not**:

```java
ItemTagRelation row = relationMapper.selectOne(activeByItemAndTag(itemId, tagId));
```

Historical data, manual SQL, retries, or concurrency can create duplicates. Handle the list explicitly.

---

## Tests Required

- Master table: delete `code=A`, recreate `code=A`, expect success.
- Master table: delete path renames the code before logical delete.
- Relation table: sync the same relation set twice, expect no database unique conflict.
- Relation table: duplicate active rows return a business error instead of a framework exception.

---

## Related

- `02-ddl-standard.md`
- `04-entity-mapping.md`
- `05-pagination-aggregation.md`
