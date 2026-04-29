## 四、PR / Merge Request 规范

### PR 大小

- **目标**：< 400 行变更（含测试）
- **超过 400 行**：拆成多个 PR
- **超过 1000 行**：必须分阶段，否则 review 不可能仔细看

### PR 标题

与 commit subject 同格式：

```
feat(order): 支持订单批量导出 Excel
```

### PR 描述模板

```markdown
## 变更摘要
- 一句话说明核心变更

## 关联 Ticket
Closes T-1234

## 测试 Checklist
- [ ] 单元测试已加 / 已更新
- [ ] 集成测试已跑（或不需要）
- [ ] 本地手动验证通过
- [ ] CI 全绿

## Breaking Change
- [ ] 无
- [ ] 有：DB schema / API 契约 / 配置变更，已在描述中说明影响

## 相关 spec
- 涉及 `.trellis/spec/...` 哪些规范

## 截图（前端 PR 必填）
（截关键交互前后对比）
```

### Review 要求

| 团队规模 | Approve 数 | Approver 来源 |
|---|---|---|
| 2 人 | 1 | 另一人 |
| 3-5 人 | 1 | 任一同事 |
| ≥ 6 人 | 2 | 至少 1 个领域负责人 |
| Hotfix | 1（紧急时事后补 review） | 任一可用同事 |

**铁律**：
- 自己 PR 不能 self-approve
- AI 代写的 PR 必须由人 review
- review 30 分钟内回 / 24 小时内 approve（团队约定）

### Review 评论分级

```
[BLOCK]  必须改才能 merge
[NIT]    建议改但不阻塞 merge
[?]      问题 / 不理解，请回复
[+1]     赞同 / 学到了
```
