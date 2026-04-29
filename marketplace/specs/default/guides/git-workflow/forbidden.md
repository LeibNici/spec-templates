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
