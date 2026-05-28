# Versioned Reference Pattern

> Use this when a derived record must keep using the master-data version selected at creation time.

---

## Problem

Many business records depend on master data: templates, pricing rules, formulas, approval rules, routing definitions, configuration sets, or catalog entries. After a derived record is created, the master data may change.

You must choose whether the derived record should:

- Follow the latest master data.
- Freeze a full copy.
- Reference a specific version of the master data.

Mixing these semantics creates historical drift and hard-to-debug reports.

---

## Decision Matrix

| Pattern | How It Works | Use When | Avoid When |
|---|---|---|---|
| Reference | Store only `master_id`; read the current row | The derived record should always reflect the latest master data | Historical correctness matters |
| Snapshot | Copy all needed master fields into derived tables | The copied data is small and must be fully frozen | Master detail fields are large or change often |
| Versioned Reference | Store `master_id` + `master_version`; master keeps historical versions readable | The master data is versioned or can be versioned, and full copy is too heavy | The master data has no stable version identity |

---

## Convention: Versioned Reference

**Do**:

- Store both `master_id` and `master_version` on the derived record.
- Join by both fields.
- Keep referenced master versions readable.
- Reject destructive changes while a version is referenced.

**Good DDL**:

```sql
ALTER TABLE document_item
  ADD COLUMN master_id BIGINT NULL COMMENT 'Referenced master row',
  ADD COLUMN master_version VARCHAR(50) NULL COMMENT 'Referenced master version',
  ADD INDEX idx_document_item_master_version (master_id, master_version);
```

**Good query**:

```sql
SELECT d.id, m.name, m.rule_json
  FROM document_item d
  JOIN master_rule m
    ON m.id = d.master_id
   AND m.version_code = d.master_version
 WHERE d.id = #{id}
```

**Do Not**:

```sql
SELECT d.id, m.name
  FROM document_item d
  JOIN master_rule m ON m.id = d.master_id
 WHERE m.status = 'ACTIVE'
```

The bad query reads the current active master version, not the version selected when the derived record was created.

---

## Convention: Write Time

**Do**: Resolve and persist the selected master version at creation time.

```java
MasterVersionRef selected = masterRuleService.findActiveVersion(command.getRuleCode());
if (selected == null) {
    throw new BusinessException("No active rule version found");
}
item.setMasterId(selected.id());
item.setMasterVersion(selected.versionCode());
itemMapper.insert(item);
```

**Do Not**: Store only the master code and resolve the active version later unless the contract explicitly says the record follows latest.

---

## Convention: Reference Protection

**Do**: Block delete, physical purge, or incompatible update when a historical version is referenced.

```java
long referenced = documentItemMapper.countByMasterVersion(masterId, versionCode);
if (referenced > 0) {
    throw new BusinessException("This version is referenced and cannot be deleted");
}
```

**Allowed**:

- Creating a new master version.
- Archiving old versions while keeping them readable.
- Editing metadata that does not affect historical calculation or display.

**Forbidden**:

- Physically deleting a referenced version.
- Updating fields that historical derived records read for calculation.
- Querying a derived record through the latest active master row.

---

## Tests Required

- Create a derived record from version A, then create version B; the derived record still reads A.
- Referenced versions cannot be deleted or destructively changed.
- Query joins include both `master_id` and `master_version`.
- Legacy rows without version fields have an explicit fallback path and visible warning.

---

## Related

- `database-guidelines/04-entity-mapping.md`
- `database-guidelines/07-effective-row-filter.md`
- `code-smell-prevention/09-silent-skip.md`
