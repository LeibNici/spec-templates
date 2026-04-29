# Frontend Type Safety

## API 函数类型

每个 API 函数必须声明返回类型泛型。无例外。

### Correct

```ts
import { get, post } from './request'
import type { OrderVO, OrderCreateDTO } from '@/types/oms/order'

export const getOrder = (id: number) => get<OrderVO>(`/api/orders/${id}`)
export const listOrders = (params: OrderQuery) => get<PageResult<OrderVO>>('/api/orders', { params })
export const createOrder = (data: OrderCreateDTO) => post<OrderVO>('/api/orders', data)
```

### Forbidden

```ts
// WRONG: any 类型
export const getOrder = (id: number) => get<any>(`/api/orders/${id}`)

// WRONG: 无泛型
export const getOrder = (id: number) => get(`/api/orders/${id}`)
```

---

## VO / DTO 类型定义

为所有 API 契约定义 interface：

```ts
// types/oms/order.ts
export interface OrderVO {
  id: number
  orderNo: string
  status: string
  customerName: string
  totalAmount: number
  createTime: string
}

export interface OrderCreateDTO {
  customerName: string
  items: OrderItemDTO[]
}

export interface OrderQuery {
  status?: string
  keyword?: string
  page: number
  size: number
}
```

---

## any 类型治理

消除 `any` 的优先顺序：

1. **API 层** — 所有 `get<any>` / `post<any>` → 具体 VO 类型
2. **核心组件** — props、emits、slot 类型
3. **Composables** — 返回类型
4. **页面组件** — 局部变量

---

## Generic 模式

```ts
// 分页结果
interface PageResult<T> {
  records: T[]
  total: number
  current: number
  size: number
}

// R 包装（如客户端需用）
interface R<T> {
  code: number
  msg: string
  data: T
}
```

---

## Forbidden

- `as any` 类型断言（用类型收窄）
- 表单数据 `reactive({})` 不带类型（必须定义 interface）
- `// @ts-ignore` 没注释解释

---

## 前后端契约对齐

### 铁律

**前端 TypeScript interface 必须与后端 Java VO/DTO 字段一一对应。** 任何后端字段变更必须同步更新前端类型定义。

### 命名映射

| Backend (Java) | Frontend (TypeScript) | 规则 |
|---|---|---|
| `orderNo` (String) | `orderNo: string` | 名称完全一致（camelCase） |
| `totalAmount` (BigDecimal) | `totalAmount: number` | Java BigDecimal → TS number |
| `createTime` (LocalDateTime) | `createTime: string` | Java 时间类型 → TS string |
| `deleted` (Integer) | 不暴露 | 逻辑删除字段不出现在 VO/TS 中 |

### Type 文件组织

```
src/types/
  ├── {biz}/        # 对应后端业务模块
  │   ├── order.ts  # OrderVO, OrderCreateDTO, OrderQuery
  │   └── ...
  └── common.ts     # PageResult<T>, R<T>, 公共类型
```

### 契约同步检查清单

修改后端 VO/DTO 时：
- [ ] 找到对应的 `src/types/` 下的 TS interface
- [ ] 同步增删改字段（名称、类型、可选性）
- [ ] 检查所有引用该类型的组件是否兼容
- [ ] API 函数泛型参数与新 VO 类型一致

### Forbidden

- 前端 interface 字段名与后端 VO 字段名不一致（如后端 `orderNo`，前端 `order_no`）
- 前端 interface 缺少后端 VO 必需字段
- 前端 interface 包含后端 VO 不存在的字段（幽灵字段）
- 前端使用 `Record<string, any>` 代替具体 interface

---

## Data Consistency 规则

| 规则 | 后端 | 前端 |
|---|---|---|
| 成功码 | `R.ok()` → `code: 0` | 判断 `code === 0`，禁止 `code === 200` |
| 日期格式 | `LocalDateTime` → Jackson ISO 8601 | dayjs 解析，禁止 `new Date()` 直接解析 |
| 枚举值 | 返回 **code**（如 `WAITING_PRODUCTION`），禁止返回 label | 收到 code，通过 `src/constants/*-status.ts` 映射 label 显示；逻辑用 `row.status === STATUS.X` 比较；TS 类型用 union literal 而非 `string` |
| 金额精度 | `BigDecimal` → JSON number | 显示 `toFixed(2)`，计算用原始值 |
| 分页参数 | `pageNum` / `pageSize` | 请求 `{ page, size }`，与后端命名映射一致 |
| 逻辑删除 | `deleted` 字段 | VO 不暴露，TS interface 不定义 |

---

## 反模式：Silent Drift

后端改了 VO 字段名，前端 TS 类型不同步时不会编译报错（JSON 弱类型），但运行时字段变 `undefined`。

**Prevention**:
- 每次后端 VO/DTO 变更 → 搜索 `src/types/` 同步 TS interface
- 禁止用 `as any` 绕过类型不匹配
- 禁止前端枚举硬编码 `{1: '待审核', 2: '已通过'}` → 走 dict API 或 constants
