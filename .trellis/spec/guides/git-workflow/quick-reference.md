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
