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
