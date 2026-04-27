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
