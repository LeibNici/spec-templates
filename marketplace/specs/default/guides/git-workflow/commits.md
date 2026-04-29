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
