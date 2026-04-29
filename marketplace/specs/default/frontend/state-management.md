# Frontend State Management

## Pinia Stores

- `stores/user.ts` — 用户信息、权限、token
- `stores/app.ts` — 侧边栏折叠、主题、全局设置
- `stores/dict.ts` — 业务字典缓存（避免重复请求）

> Store 只放**真正全局共享**的状态。临时页面状态用 `ref` / `reactive`。

---

## Reactivity 选择指南

| 数据类型 | 响应式 API | 何时 |
|---|---|---|
| Dialog 表单字段 | `reactive({})` | 仅表单字段，不是整行数据 |
| 大列表数据 | `shallowRef([])` | 表格、树（避免深度响应开销） |
| 简单开关 | `ref(false)` | loading / visible 等 |
| 派生值 | `computed(() => ...)` | 计算属性 |

---

## Forbidden

- 大数组用 `ref([])`（100+ 项 → 用 `shallowRef`）
- 把临时页面状态塞进 store（用本地 `ref` / `reactive`）
- 在 actions 外直接 mutate store

---

## Store 模板（Setup Store 风格）

> 推荐用 **Setup Store**（Composition API 风格 defineStore），与 `<script setup>` 一致，TS 推断更好，逻辑可拆分到 composable。

```ts
// stores/user.ts
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { UserInfo } from '@/types/user'
import { loginApi } from '@/api/auth'

export const useUserStore = defineStore('user', () => {
  // state
  const token = ref('')
  const userInfo = ref<UserInfo | null>(null)
  const permissions = ref<string[]>([])

  // getters（用 computed）
  const isLoggedIn = computed(() => !!token.value)
  const hasPermission = (code: string) => permissions.value.includes(code)

  // actions（普通函数）
  async function login(username: string, password: string) {
    const result = await loginApi({ username, password })
    token.value = result.token
    userInfo.value = result.userInfo
    permissions.value = result.permissions
  }

  function logout() {
    token.value = ''
    userInfo.value = null
    permissions.value = []
  }

  return { token, userInfo, permissions, isLoggedIn, hasPermission, login, logout }
})
```

### 为什么不用 Options Store

老的 Options 风格（`{ state: () => ({...}), actions: {...} }`）也能跑，但有几个问题：

- 需要 `this` 绑定，TS 类型推断比 Setup 风格弱
- `actions` 内调 composable（如 `useRouter()`）需要绕过 this
- 跟项目 `<script setup>` 风格分裂
- 持久化插件（pinia-plugin-persistedstate）两种风格写法不同

**保留兼容**：已有 Options 风格 store 不强制重写；新建 store 用 Setup 风格。

---

## 持久化

- token 等需跨刷新保留 → `pinia-plugin-persistedstate`（仅 user 维度）
- 业务字典等可重新请求的数据 → 不持久化，登录后重新拉
- 禁止：把整个 store 一刀切持久化（增加 localStorage 体积，且数据可能脏）
