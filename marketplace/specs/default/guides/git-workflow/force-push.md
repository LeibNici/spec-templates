## 六、Force Push 规则

| 场景 | 允许？ | 命令 |
|---|---|---|
| 自己的 feature 分支 rebase 后 | ✅ | `git push --force-with-lease` |
| main 分支 | ❌ | 永禁 |
| 别人在用的共享分支 | ❌ | 用 revert commit |
| 已合并的 release 分支 | ❌ | 永禁 |

**铁律**：`--force-with-lease` 而非 `--force`，防覆盖别人的 push。
