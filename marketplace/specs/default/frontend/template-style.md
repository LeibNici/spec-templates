# Vue Template & Script Style

> Vue 3 单文件组件 (SFC) 写法约定 — `<template>` / `<script setup>` / `<style>`。

---

## SFC 顺序

```vue
<template>
  <!-- 模板 -->
</template>

<script setup lang="ts">
// 逻辑
</script>

<style scoped>
/* 样式 */
</style>
```

**约定**：新代码统一用 `<script setup>`。Options API（`export default { data() {} }`）仍合法但不再推荐——已有 Options 组件无需强制重写，渐进迁移即可。

---

## `<script setup>` 内部顺序

按**职责依赖关系**排列，便于阅读：

```ts
<script setup lang="ts">
// 1. 导入
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { listOrders } from '@/api/order'
import type { OrderVO, OrderQuery } from '@/types/oms/order'
import OrderDetailDrawer from './OrderDetailDrawer.vue'

// 2. defineProps / defineEmits / defineExpose
const props = defineProps<{ orderId: number }>()
const emit = defineEmits<{ (e: 'updated', id: number): void }>()

// 3. 路由 / store / composable
const route = useRoute()
const userStore = useUserStore()
const { options: statusOptions } = useDict('order_status')

// 4. 响应式状态
const list = ref<OrderVO[]>([])
const loading = ref(false)
const query = reactive<OrderQuery>({ page: 1, size: 20 })

// 5. computed
const isManager = computed(() => userStore.hasPermission('order:manage'))

// 6. 函数（按调用顺序）
async function fetchData() { ... }
function handleEdit(row: OrderVO) { ... }

// 7. watch / lifecycle
watch(() => query.status, fetchData)
onMounted(fetchData)
</script>
```

---

## 命名约定（Vue 3 官方）

| 对象 | 约定 | 示例 |
|---|---|---|
| `.vue` 文件名 | **PascalCase** | `OrderList.vue`、`UserCard.vue`（与 import 一致） |
| 模板中的组件名 | **PascalCase** | `<OrderList />`，**不要** `<order-list />` |
| 模板中的属性 | **kebab-case** | `<el-button :is-disabled="loading" :data-row-id="row.id">` |
| 自定义事件名 | **kebab-case**（emit + 监听） | `emit('row-click')` / `<Foo @row-click="..." />` |
| Boolean prop 在模板 | 简写不带值 | `<el-input disabled>`，不写 `disabled="true"` |

> macOS 文件系统大小写不敏感，部署 Linux 时若 `.vue` 文件名大小写与 import 不一致会触发 `Cannot find module` —— PascalCase 是防线。
>
> 属性 kebab-case 是 Vue 官方 Style Guide 与 Element Plus 文档主流写法；camelCase 也能跑但与社区代码风格不一致。

---

## Template 写法

### Required

- 用 `<script setup>` 自动暴露的变量，不要再写 `methods` / `data`
- 多个根节点（Vue 3 支持），但建议保留单根 `<div>` 便于样式作用
- 复杂条件抽 `computed`，不要在模板写多层三元
- 长属性列表换行，每行一个属性

### Forbidden

```vue
<!-- WRONG: 模板里内联三元嵌套 -->
<el-tag :type="row.status === 'A' ? 'success' : row.status === 'B' ? 'warning' : 'info'">
  {{ row.status === 'A' ? '通过' : row.status === 'B' ? '待审' : '其他' }}
</el-tag>

<!-- WRONG: v-for 不带 :key -->
<div v-for="item in list">{{ item.name }}</div>

<!-- WRONG: 模板里直接 console.log / 改 store -->
<el-button @click="userStore.token = ''">退出</el-button>
```

### Correct

```vue
<!-- 状态用 StatusTag 组件 + dict -->
<StatusTag :value="row.status" dict-type="order_status" />

<!-- v-for 必须 :key -->
<div v-for="item in list" :key="item.id">{{ item.name }}</div>

<!-- 事件走 handler 函数 -->
<el-button @click="handleLogout">退出</el-button>
```

---

## Composition API 选择指南

| 数据类型 | API | 何时 |
|---|---|---|
| 单值 | `ref` | 数字/布尔/字符串 |
| 单值（不深度响应） | `shallowRef` | 大数组、复杂对象 |
| 对象（多字段） | `reactive` | 表单 |
| 派生值 | `computed` | 计算属性 |
| 监听变化 | `watch` / `watchEffect` | 副作用 |
| 引用 DOM/组件 | `ref` + `<el-input ref="inputRef">` | 不要用 `$refs` |

---

## defineProps / defineEmits（TypeScript）

**优先用基于类型的写法**，不用 runtime 声明：

```ts
// CORRECT: type-based
const props = defineProps<{
  orderId: number
  title?: string
}>()

const emit = defineEmits<{
  (e: 'updated', id: number): void
  (e: 'closed'): void
}>()

// FORBIDDEN: runtime declaration（除非确实需要默认值/校验）
const props = defineProps({
  orderId: { type: Number, required: true },
})
```

需要默认值时用 `withDefaults`：

```ts
const props = withDefaults(defineProps<{
  size?: 'small' | 'medium' | 'large'
}>(), {
  size: 'medium',
})
```

---

## Style

### Scoped 默认

```vue
<style scoped>
.order-list { padding: 16px; }
</style>
```

- **默认 `scoped`**（绝大多数组件级样式用 scoped）
- 全局样式（如 `:root`、Element Plus 主题穿透）放 `src/styles/`，由 `main.ts` 统一引入
- 用 `<style module>` 也合法（适合复杂样式映射），但项目内保持单一选择
- BEM 命名风格优先：`.order-list__item--active`
- 禁止：`!important`（除非覆盖第三方组件库且注释说明）

### 深度选择器（覆盖 Element Plus）

Vue 3 推荐 `:deep()` 而非 `/deep/` 或 `>>>`：

```vue
<style scoped>
.order-list :deep(.el-table__row) {
  background: #fafafa;
}
</style>
```

---

## i18n / 文案

- 用户可见文案**禁止**直接硬编码到模板（除非项目明确不做 i18n）
- 走 `$t('...')` 或集中在 `src/locales/zh-CN.ts`
- 错误消息按"业务可读"原则（参见 `quality-guidelines.md` HTTP 错误归因）

---

## 反模式索引

| 反模式 | 修法 |
|---|---|
| 单文件 > 500 行 | 抽 composable + 拆子组件 |
| `<script setup>` 内顶部直接 `console.log` 调试 | 必须删除后再提交 |
| Options API 与 `<script setup>` 混用 | 统一 `<script setup>` |
| `<style>` 不写 `scoped` 又不在文件头注释"intentionally global" | 加 `scoped` 或加注释 |
| `v-html` 渲染未脱敏的用户输入 | 用 DOMPurify 或换组件 |
| `:key` 用 index | 用稳定业务 id |
