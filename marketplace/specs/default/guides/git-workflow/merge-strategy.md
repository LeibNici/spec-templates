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
