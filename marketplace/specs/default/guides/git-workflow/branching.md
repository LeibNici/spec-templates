## 一、分支模型

### 长期分支（仅 1 个）

```
main      ← 主分支，永远可发布
```

**铁律**：
- `main` 不允许直接 push（GitHub branch protection 开起来）
- `main` 上的每次 commit 都必须**通过 CI**
- `main` 不 force push

### 短期分支（按需开）

```
feature/{ticket-id}-{kebab-case-desc}    ← 新功能
fix/{ticket-id}-{kebab-case-desc}        ← bug 修复
chore/{kebab-case-desc}                  ← 重构 / 文档 / 工具链
hotfix/v{x.y.z}-{kebab-case-desc}        ← 生产紧急修复
release/v{x.y}                           ← 发布准备（按需，多版本并存才用）
```

**示例**：

```
feature/T-1234-order-batch-export
fix/T-2345-login-403-on-firefox
chore/upgrade-mybatis-plus-3.5.7
hotfix/v1.2.1-critical-payment-loss
```

**铁律**：
- 分支生命周期 ≤ **1 周**（更长的 PR 一定会出 conflict）
- 分支命名**全小写 + kebab-case**，不写中文
- 关联 ticket id（无 ticket 用关键词）

### 分支保护规则（GitHub / GitLab）

`main` 必须配：
- [ ] 禁止直接 push
- [ ] 必须经过 PR 合并
- [ ] PR 必须有 ≥ 1 approve（团队 ≥ 2 人时）
- [ ] PR 必须 CI 全绿
- [ ] 必须 up-to-date with main 才能 merge
