# Frontend Composable Guidelines

> Vue 3 Composition API 的可复用逻辑封装。本项目术语统一为 **composable**（与 React hook 概念对应，但名称区分）。

---

## Core Composables

### useDict — 字典数据

```ts
// Correct: 业务字典走 API
const { options, labelOf } = useDict('approval_status')
```

- **业务字典**（运行时可配）：始终用 `useDict` + dict API
- **系统枚举**（仅发版变更）：在 `src/constants/` 集中
- 不确定时 → 用 dict API（更安全）

### Forbidden

```ts
// WRONG: 页面内硬编码映射
const STATUS_MAP: Record<string, string> = {
  DRAFT: '草稿',
  SUBMITTED: '已提交',
}
```

---

## 数据获取模式

### API 函数

```ts
// Correct: 泛型类型
export const getOrder = (id: number) => get<OrderVO>(`/api/orders/${id}`)

// WRONG: any 类型
export const getOrder = (id: number) => get<any>(`/api/orders/${id}`)
```

### 响应处理

Axios 拦截器已返回 `res.data`，**不要**再加 `.data`。

```ts
// Correct
const result = await getOrderList(params)

// WRONG: 双重拆包
const result = (await getOrderList(params)).data
```

---

## 系统枚举 vs 业务字典

| 类型 | 定义 | 前端做法 |
|---|---|---|
| 系统枚举 | 固定集合，仅发版变更（status, actions） | `src/constants/` 集中 |
| 业务字典 | 运行时可配（客户类型、地区） | dict API + `useDict` composable |

---

## 自定义 Composable 约定

- **命名**：`use` 前缀（`useLoading`, `usePagination`, `useConfirm`）
- **返回**：对象（具名属性），不是数组
- **清理**：用到 timer / listener 时处理 `onUnmounted`
- **位置**：`src/composables/` 共享；单点使用可放组件同级目录

### 示例

```ts
// src/composables/useOrderGrouped.ts
export function useOrderGrouped() {
  const list = ref<OrderGroupedVO[]>([])
  const loading = ref(false)
  const drawerVisible = ref(false)
  const currentRow = ref<OrderGroupedVO | null>(null)

  async function fetchData(params: OrderGroupedQuery) {
    loading.value = true
    try {
      list.value = await getOrderGrouped(params)
    } finally {
      loading.value = false
    }
  }

  function openDetail(row: OrderGroupedVO) {
    currentRow.value = row
    drawerVisible.value = true
  }

  return { list, loading, drawerVisible, currentRow, fetchData, openDetail }
}
```

---

## Composable 反模式

| 反模式 | 修法 |
|---|---|
| 返回数组（`return [a, b]`） | 改为对象 `return { a, b }`，便于解构与扩展 |
| 内部依赖 Pinia store 但未声明 | 在 composable 内显式 `const userStore = useUserStore()`，调用方一目了然 |
| 跨组件共享 ref（在模块顶层 `const x = ref(...)`） | 改为 store；composable 必须每次调用返回新实例 |
| `onMounted` 内部发请求但不清理 | 加 `onUnmounted` 或用 `AbortController` |
