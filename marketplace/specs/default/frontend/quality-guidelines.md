# Frontend Quality Guidelines

## 代码硬性上限（实战宽松档）

| 指标 | 上限 | 超限处理 |
|---|---|---|
| Vue 文件 | ≤ 500 行 | 抽 composable + 拆子组件 |
| 嵌套（template） | ≤ 4 层 | 拍平模板 |
| 函数 | ≤ 80 行 | 抽方法 |
| 位置参数 | ≤ 5 个 | 封装对象 |
| 魔法数字 | 0 | 提取常量 |

> 注释默认零；只在 WHY 非显然时加一行。

---

## HTTP 错误归因

原则：**按原因分类，告诉用户是否可重试**。

| 状态 | 用户消息 |
|---|---|
| 400 | 优先用后端 `msg`，兜底"请求参数有误" |
| 401 | "登录已过期" + 清 token + 跳登录 |
| 403 | "没有权限" |
| 404 | "资源不存在" |
| 500 | 优先用后端 `msg`，兜底"服务器异常" |
| 502 | "服务正在重启或维护中"（**不要**用"服务器内部错误"） |
| 503/504 | "服务暂不可用" / "响应超时" |
| 无响应 | 区分 `ECONNABORTED`（超时）vs 网络错误 |

502/503/504：**不要**用后端 msg（网关错误响应体不可靠）。

---

## 健壮性（Required）

### app.config.errorHandler

```ts
// main.ts
app.config.errorHandler = (err, instance, info) => {
  console.error('Vue Error:', err, info)
  // 上报监控
}
```

### window.onunhandledrejection

```ts
// main.ts
window.onunhandledrejection = (event) => {
  console.error('Unhandled rejection:', event.reason)
  event.preventDefault()
}
```

两者**必须**都配，防止白屏。

---

## Nginx 规则

- 独立 `nginx.conf` 文件；禁止：内联在 Dockerfile
- 静态资源：`Cache-Control: max-age=31536000`
- `package-lock.json` 必须提交到 git

---

## Forbidden Patterns

| Pattern | 原因 | 正确做法 |
|---|---|---|
| `<any>` 在 API 函数 | 失去类型安全 | 用具体 VO 类型 |
| `.data` 在 API 调用后 | 拦截器已拆包 | 直接用结果 |
| 硬编码 `Record<string,string>` 字典 | 不可维护 | `useDict` / `constants/` |
| `default-expand-all` 在 el-tree | 性能问题 | 懒加载或 `el-tree-v2` |
| 提交按钮无 `:loading` | 双提交风险 | 始终加 `:loading` |
| 搜索无 `debounce` | 服务端过载 | `debounce(300)` |
| Mock 数据 | 必须真接 API（详见下文 Mock 策略） | 删除所有 mock |

---

## Mock 策略（铁律）

> **本项目不使用任何前端 mock 工具**。前后端同期开发，后端先搭空接口比 mock 更快，且全程类型/路径/错误处理都走真路径。

### 严禁

- 在 `src/api/*.ts` 函数里 `return { mockData: ... }` 或 `return Promise.resolve(假数据)`
- 在 `src/views/*.vue` 业务组件里硬编码假数据列表（`const mockList = [...]`）
- 注释掉真 API 调用换上 `const data = [...]`
- 引入 `vite-plugin-mock` / `MSW` 等 mock 工具
- 装在 `mock/` 目录的"开发期 mock"

### 允许

- `src/test/` 内 vitest mock 函数（**仅单元测试**，不进 build）

### 推荐工作流（替代 mock）

```
DDL → 后端空接口契约（10min）→ 前端真 axios + 真类型 → 前后端并行实现 → 联调零切换
```

详见 `.trellis/spec/guides/full-stack-workflow.md`。

### CI 检测 Mock 残留

```bash
grep -rn -E "(mockData|mockList|fakeData|return Promise\.resolve\()" src/ \
  --exclude-dir=test --exclude="*.test.ts" \
  && echo "❌ 发现 mock 残留" && exit 1
```

---

## Code Review Checklist

- [ ] API 函数无 `<any>`
- [ ] 无冗余 `.data` 访问
- [ ] 无硬编码字典映射
- [ ] errorHandler + onunhandledrejection 已配置
- [ ] 提交按钮有 `:loading`
- [ ] 搜索框有 debounce
- [ ] Vue 文件 ≤ 500 行
- [ ] `npm run build` 通过
