## 8. 历史违规文件的修正义务（铁律）

**铁律：修改任何文件前，必须先核对该文件是否已违反当前规范；若有违规，当次变更必须把整个文件按现行规范整体修正，不允许仅改新增部分、沿用旧写法、或以"preexisting tech debt / 不在本次范围"为理由保留违规代码。**

### Why

新代码跟随旧模式是规范漂移最大的根源。旧文件里的 `JdbcTemplate`、SQL 字符串、`Map<String,Object>` 等违规写法被当作参考模板，导致违规面持续扩散。长此以往，规范文档的权威性被稀释。

### 触发场景（非穷举）

- Service/Controller 内持有 `JdbcTemplate` 字段或出现 SQL 字符串
- Adapter / Service 方法签名回退到 `Map<String,Object>` / `JSONObject`
- 实体未继承 `BaseEntity`、手动维护 `id/createTime/...`
- Controller 内调用 `@Scheduled` / 注入 Mapper
- `@Select("...")` / `@Update("...")` 注解形式 SQL
- 跨模块直连他人 Entity / Mapper

### Forbidden

```java
// 文件已经持有 JdbcTemplate，我只改我新增的分支，不动老的 → 不允许
class XxxAdapterImpl {
    private final JdbcTemplate jdbcTemplate;           // 历史违规
    void oldMethod() { jdbcTemplate.update("INSERT..."); }   // 历史违规（不改）
    void newMethod() { jdbcTemplate.update("INSERT..."); }   // 新增但沿用旧写法 ❌
}
```

### Required

```java
// 新增 Mapper + XML，把整个文件里的 JDBC 写法一次性迁完
class XxxAdapterImpl {
    private final XxxBridgeMapper xxxBridgeMapper;
    void oldMethod() { xxxBridgeMapper.insertX(param); }  // 整体修正 ✓
    void newMethod() { xxxBridgeMapper.updateY(param); }  // 新增亦合规 ✓
}
```

### 执行检查清单

- [ ] 动某文件前先 grep：`JdbcTemplate` / `jdbcTemplate\.` / `"SELECT |"INSERT |"UPDATE |"DELETE ` / `Map<String,\s*Object>` 作为 Controller/Service 方法签名 / `@Select\(` / `@Update\(`
- [ ] 命中任一项即判定该文件违规，当次变更必须整体修正
- [ ] 若本次变更确实无法完成整体修正（如影响面过大），必须在 PR 描述中用独立任务挂起并给出修正计划
- [ ] 修正完成后再次 grep 同一批 pattern，确认该文件零命中
