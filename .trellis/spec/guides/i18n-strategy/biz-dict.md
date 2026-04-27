# Business Dictionary i18n

## 六、业务字典 i18n（默认不开）

### 6.1 默认策略

`sys_dict_data.dict_label` 仅维护**中文**。前端切到英文时：
- 业务字典值（如客户类型 `VIP` → `大客户`）保持中文显示
- 用户可在 dict 管理界面同时维护"英文 label"作为附属字段（可选）

**理由**：
- 字典是运营维护资产，强制双语会显著增加运营负担
- 多数业务场景下，dict_label 中文显示对英文用户也能理解（特别是行业术语）
- 真要英文版 → 启用 §6.2 扩展方案

### 6.2 扩展方案（按需启用）

新建关联表 `sys_dict_data_i18n`：

```sql
CREATE TABLE IF NOT EXISTS `sys_dict_data_i18n` (
  `id`           BIGINT      NOT NULL                COMMENT '主键ID（雪花）',
  `dict_data_id` BIGINT      NOT NULL                COMMENT '关联 sys_dict_data.id',
  `locale`       VARCHAR(10) NOT NULL                COMMENT 'BCP 47，如 zh-CN / en-US',
  `dict_label`   VARCHAR(64) NOT NULL                COMMENT '本地化标签',
  `create_time`  DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `update_time`  DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_dict_data_locale` (`dict_data_id`, `locale`),
  KEY `idx_dict_data_id` (`dict_data_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='字典数据多语言表';
```

**dict API 返回时按 Accept-Language 选 label**：

```java
List<DictDataVO> getDictData(String dictType, Locale locale) {
    List<SysDictData> dataList = dictDataMapper.selectByType(dictType);
    Map<Long, String> i18nLabels = dataList.isEmpty()
        ? Map.of()
        : i18nMapper.selectLabels(
            dataList.stream().map(SysDictData::getId).toList(),
            locale.toLanguageTag()
        );

    return dataList.stream().map(d -> DictDataVO.builder()
        .code(d.getDictCode())
        // 优先 i18n label，无 fallback 中文 dict_label
        .label(i18nLabels.getOrDefault(d.getId(), d.getDictLabel()))
        .build()).toList();
}
```

### 6.3 何时该启用扩展方案

满足任一项：
- ≥30% 用户使用英文界面
- 业务方明确要求字典英文化（如外贸订单系统）
- 已有外文用户反馈"看不懂中文标签"

否则**不启用**——保持默认。
