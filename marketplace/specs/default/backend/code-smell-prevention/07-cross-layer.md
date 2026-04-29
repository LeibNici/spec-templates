## 7. 前后端一致性补充

| 规则 | 说明 |
|---|---|
| 成功码统一 | 后端 `code: 0` = 成功，前端判断 `code === 0` |
| 日期格式统一 | 后端 `LocalDateTime` → JSON ISO 8601 字符串，前端 dayjs 解析 |
| 枚举值来源统一 | 系统枚举 → 前端 `src/constants/`；业务字典 → dict API |
| 金额精度统一 | 后端 `BigDecimal` → JSON number，前端显示时 `toFixed(2)` |
| 分页参数统一 | `{ page: 1, size: 20 }` → 后端 `pageNum` / `pageSize` |
| 主键占位不预置 | 前端 `emptyForm()` 主键字段必须 `undefined`，禁止 `id: 0` / `id: ''`；否则 MP `@TableId(IdType.ASSIGN_ID)` 会被击穿，首次 INSERT id=0，第二次主键冲突 |
