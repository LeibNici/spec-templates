# Git 工作流 + Commit / PR 规范

> Trunk-based 简化版：单 main 分支 + 短生命周期 feature 分支。
> 适合 1~10 人团队 + AI 协助开发场景。

---

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

---

## 二、Commit 规范（Conventional Commits）

### 格式

```
<type>(<scope>): <subject>

<body>

<footer>
```

### type 类型

| type | 用途 | 是否触发 changelog |
|---|---|---|
| `feat` | 新功能 | ✅ |
| `fix` | bug 修复 | ✅ |
| `refactor` | 重构（不改行为） | ❌ |
| `perf` | 性能优化 | ✅ |
| `test` | 测试代码 | ❌ |
| `docs` | 文档 | ❌ |
| `style` | 格式（不改逻辑） | ❌ |
| `chore` | 工具链 / 构建 / 依赖 | ❌ |
| `ci` | CI 配置 | ❌ |
| `revert` | 回滚 | ✅ |

### scope（可选但推荐）

- 后端：模块名（`order` / `inventory` / `user` / `auth` / `framework` / `common`）
- 前端：页面或功能（`order-list` / `login` / `composables` / `api`）
- 跨层：`api` / `db` / `i18n` / `build`

### subject 规则

- ≤ 50 字符
- 用动词原型起头（`add` / `fix` / `update` / `remove`）
- 不结句号
- 中英文均可，团队内统一

### 示例

```
feat(order): 支持订单批量导出 Excel
fix(auth): 修复 token 过期后未跳登录页
refactor(inventory): 提取库存计算到 InventoryCalculator
chore(deps): 升级 mybatis-plus 3.5.6 → 3.5.7
docs(api): 补充批量删除接口文档
test(order): 加 OrderService.cancel 边界用例
```

### body / footer

```
feat(order): 支持订单批量导出 Excel

- 加 :batch-export 接口（详见 api-design.md 批量操作）
- 异步生成 + 返回 taskId
- 前端添加进度轮询

Closes T-1234
Co-Authored-By: Claude <noreply@anthropic.com>
```

---

## 三、Commit 频率与大小

### 单次 commit

- **小步提交**：每完成一个独立子任务就 commit，不积压
- **每次 ≤ 400 行变更**（含测试）
- **不混合无关变更**：feat + chore + refactor 分开 commit

### 反例

```
git commit -m "完成订单功能"   ❌ 太笼统
# 实际改了 50 个文件 + 2000 行 + 含 deps 升级 + 含格式化
```

### 正例

```
git log --oneline
abc123 feat(order): 加批量导出接口（后端）
def456 feat(order): 前端订单列表加导出按钮
ghi789 test(order): 补 batch-export 单测
jkl012 docs(order): 接口文档加导出说明
```

---

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

---

## 五、Merge 策略

### feature / fix / chore → main

**用 Squash and Merge**（推荐）：

- main 历史保持线性
- feature 分支多个 WIP commit 折叠为 1 个
- commit message 用 PR title

### main → feature（同步上游）

**用 Rebase**：

```bash
git checkout feature/xxx
git fetch origin
git rebase origin/main
git push --force-with-lease  # 仅 force 自己的 feature 分支
```

**禁止**：
- `git merge main` 进 feature 分支（会产生 merge commit 噪声）
- `git push --force` 不带 `--with-lease`（可能覆盖别人的 commit）
- 在 main 上 rebase 已发布 commit

### Hotfix → main + 当前 release

```bash
git checkout main
git checkout -b hotfix/v1.2.1-xxx
# 修复
git commit ...
# Squash merge 进 main
# 同时 cherry-pick 进 release/v1.2 分支（如有）
```

---

## 六、Force Push 规则

| 场景 | 允许？ | 命令 |
|---|---|---|
| 自己的 feature 分支 rebase 后 | ✅ | `git push --force-with-lease` |
| main 分支 | ❌ | 永禁 |
| 别人在用的共享分支 | ❌ | 用 revert commit |
| 已合并的 release 分支 | ❌ | 永禁 |

**铁律**：`--force-with-lease` 而非 `--force`，防覆盖别人的 push。

---

## 七、与 AI 协作的特别约定

### Co-Authored-By

AI 写的 commit 必须带：

```
Co-Authored-By: Claude <noreply@anthropic.com>
```

让 git history 可追溯哪些是 AI 主笔。

### AI 不应该做的 git 操作（除非用户明确批准）

- `git push`（让用户决定何时推送）
- `git push --force`
- `git rebase -i`（交互式不适合 AI）
- `git reset --hard`
- 修改已 push 的 commit
- merge / squash 进 main

详见根 CLAUDE.md "Git 规范"。

### AI 提交前必查

- [ ] 没有 `console.log` / `System.out.println` / `debugger` 残留
- [ ] 没有 mock 残留（详见 `full-stack-workflow.md`）
- [ ] 测试通过（或明确说明跳过原因）
- [ ] commit message 符合 Conventional Commits

---

## 八、Tag / Release（按需）

### 版本号方案：SemVer

```
v{major}.{minor}.{patch}
```

| 段 | 何时升 |
|---|---|
| `major` | 不兼容的 API 变更 |
| `minor` | 向后兼容的新功能 |
| `patch` | 向后兼容的 bug 修复 |

### Tag 命名

```
v1.0.0
v1.1.0
v1.1.1
v1.1.1-rc.1   ← 预发布
v1.1.1-hotfix.20260427   ← 紧急修复（罕见）
```

### Release Notes（自动生成）

用 `git log` + Conventional Commits 自动生成 changelog：

```bash
git log v1.0.0..HEAD --pretty=format:"%h %s" | grep -E "^(feat|fix|perf)"
```

工具：`conventional-changelog-cli` / `release-please` / GitHub Release auto-generate。

---

## 九、Forbidden Patterns

| 模式 | 反例 | 正例 |
|---|---|---|
| 直接 push main | `git push origin main` | 走 PR + review |
| 笼统 commit | `commit -m "update"` | `feat(order): add batch export` |
| 巨型 PR | 2000 行变更 | 拆成 5 个独立 PR |
| 混合 commit | feat + chore + refactor 一起 | 分多次 commit |
| force push main | `git push -f origin main` | 永禁 |
| amend 已 push commit | `git commit --amend && git push -f` | 加新 commit 修复 |
| `--no-verify` 跳过 hook | `git commit --no-verify` | 修 hook 错误，不绕过 |

---

## 十、Quick Reference

```bash
# 开新功能
git checkout main && git pull
git checkout -b feature/T-1234-add-batch-export

# 提交
git add specific-files       # 不用 -A，避免误提交
git commit -m "feat(order): add batch export"

# 同步上游
git fetch origin
git rebase origin/main

# 推送 + 开 PR
git push -u origin feature/T-1234-add-batch-export
gh pr create --fill            # 或 GitLab MR

# PR 通过后清理
git checkout main
git pull
git branch -d feature/T-1234-add-batch-export
```
