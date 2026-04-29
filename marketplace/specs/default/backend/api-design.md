# REST API 设计规范

> 后端 REST API 的形态约定。覆盖路径风格、HTTP 方法、分页参数、批量操作、版本管理、幂等头。
> 与 `quality-guidelines.md` Controller 铁律配套（职责），本文件管 API **形态**。

---

## 一、URL 路径风格（资源型 RESTful）

### 路径前缀

```
/api/{module}/{resource}
```

| 段 | 规则 |
|---|---|
| `/api` | 固定前缀，区分静态资源与 API |
| `{module}` | 业务模块名（小写，单数）：`order` / `inventory` / `user` |
| `{resource}` | 资源名（**小写复数**）：`orders` / `customers` / `materials` |

```
✅ /api/order/orders
✅ /api/inventory/inventories
✅ /api/user/users

❌ /api/getOrders            ← 动作风格，不要
❌ /api/order/getOrderList   ← Java 方法名直接当 URL，不要
❌ /api/order/Orders         ← PascalCase 不要
❌ /api/Order/Order          ← 同上
```

### 资源 + 子资源

```
✅ /api/order/orders/{orderId}/items                ← 订单的明细
✅ /api/order/orders/{orderId}/items/{itemId}       ← 单个明细
```

子资源最多 2 层；超过 2 层考虑拆 module 或独立 resource。

---

## 二、HTTP 方法语义

| 方法 | 用途 | 幂等？ | 安全？ |
|---|---|---|---|
| `GET` | 查询（列表 / 详情 / 字典） | ✅ | ✅ 无副作用 |
| `POST` | 创建 / 命令型动作（审批 / 取消） | ❌ | ❌ |
| `PUT` | 整体替换（全量更新） | ✅ | ❌ |
| `PATCH` | 部分更新（单字段 / 状态变更） | ✅ | ❌ |
| `DELETE` | 删除（逻辑删 / 物理删） | ✅ | ❌ |

**铁律**：
- `GET` 必须无副作用（不允许 GET 路径写库，详见 `code-smell-prevention/06-method-design.md §6.1`）
- `PUT` 必须**全量字段**替换；只改一两个字段用 `PATCH`
- `POST` 用于无法用 CRUD 表达的命令（取消订单、生成报表）

### 标准 CRUD 模式

```
GET    /api/order/orders                  ← 分页列表
GET    /api/order/orders/{id}             ← 详情
POST   /api/order/orders                  ← 创建
PUT    /api/order/orders/{id}             ← 整体替换
PATCH  /api/order/orders/{id}             ← 部分更新（如改状态）
DELETE /api/order/orders/{id}             ← 删除
```

### 动作型（命令）API

资源 + 动作命名用 `:action`（Google AIP 风格）或 `/action`（更兼容）：

```
POST /api/order/orders/{id}:cancel        ← 取消（推荐）
POST /api/order/orders/{id}:confirm
POST /api/order/orders/{id}:approve

# 兼容性差时可用：
POST /api/order/orders/{id}/cancel
```

**禁止**：
- `POST /api/order/cancelOrder/{id}`（动词在前 = RPC 风格）
- `GET  /api/order/cancel?id=xxx`（GET 写库）
- `POST /api/order/orders/{id}` body 里带 `{action: "cancel"}`（隐藏动作）

---

## 三、分页 / 排序 / 筛选参数命名

### 前后端统一约定

| 参数 | 后端 Java | 前端 TS | 备注 |
|---|---|---|---|
| 页码 | `pageNum` | `pageNum` | 从 **1** 开始（业务习惯） |
| 每页 | `pageSize` | `pageSize` | 默认 20，最大 200 |
| 排序字段 | `sortField` | `sortField` | 单字段；多字段用 `sort=field1,field2` |
| 排序方向 | `sortOrder` | `sortOrder` | `asc` / `desc` |
| 关键词 | `keyword` | `keyword` | 模糊搜索 |
| 状态筛选 | `status` | `status` | 透传枚举 code |
| 时间区间 | `startDate` / `endDate` | 同 | ISO 8601 |

**铁律**：前后端用**完全一致的字段名**，不做 axios 拦截器映射（`page` ↔ `pageNum`）—— 同名最稳。

### 列表请求示例

```
GET /api/order/orders?pageNum=1&pageSize=20&keyword=ABC&status=APPROVED&startDate=2026-01-01&sortField=createTime&sortOrder=desc
```

### 列表响应

```json
{
  "code": "0",
  "msg": "success",
  "data": {
    "records": [...],
    "total": 1234,
    "current": 1,
    "size": 20
  }
}
```

`PageResult<T>` 字段固定为 `records / total / current / size`（与 MyBatis-Plus `Page<T>` 一致）。

---

## 四、批量操作命名

```
POST   /api/order/orders:batch-create     ← 批量创建
POST   /api/order/orders:batch-delete     ← 批量删除（body: { ids: [1,2,3] }）
POST   /api/order/orders:batch-approve    ← 批量审批
POST   /api/order/orders:batch-export     ← 批量导出
```

**为什么不用 `DELETE /api/orders` + body？**
- 部分网关 / proxy 会丢 DELETE body
- 团队成员对"DELETE 带 body"理解不一致
- 用 POST + 显式动作更稳

**响应**：批量操作必须返回**成功 + 失败明细**：

```json
{
  "code": "0",
  "data": {
    "successCount": 8,
    "failureCount": 2,
    "failures": [
      { "id": 5, "reason": "订单已发货，无法取消" },
      { "id": 7, "reason": "无权限" }
    ]
  }
}
```

详见 `error-handling.md` "批量操作跳过规则"。

---

## 五、版本管理

### 默认不加版本

中后台项目大多数不需要 URL 版本（接口与前端同一发布周期）。

```
✅ /api/order/orders   ← 默认
```

### 何时加版本

满足以下任一即考虑：
- API 暴露给**外部客户端**（小程序 / 移动 App / 第三方）
- API 有**多版本并存**需求（旧版本不能立即下线）
- 业务进入**重大重构期**且回滚风险大

### 版本格式

```
/api/v1/order/orders
/api/v2/order/orders
```

URL path 版本（不用 header / query），**禁止**：
- `?v=1`（query 版本，缓存复杂）
- `Accept-Version: 1`（header 版本，难调试）

---

## 六、幂等保护

### 写操作（POST / PUT / DELETE）必须支持幂等

三种实现，按推荐度：

| 方案 | 适用 | 实现 |
|---|---|---|
| **业务幂等键** | 创建类 API（订单号 / 业务 No） | DB unique index + `select → insert → catch DuplicateKey → re-select` |
| **Idempotency-Key 头** | 通用方案 | 客户端发 `Idempotency-Key: {uuid}`，服务端 Redis 缓存结果 24h |
| **DB 唯一约束** | 简单场景 | 直接靠表 unique index 兜底 |

### Idempotency-Key 实现

```java
@PostMapping
public R<OrderVO> create(
    @RequestHeader(value = "Idempotency-Key", required = false) String idempotencyKey,
    @RequestBody @Valid OrderCreateDTO dto) {

    if (idempotencyKey != null) {
        Object cached = redis.opsForValue().get("idempotency:" + idempotencyKey);
        if (cached != null) return (R<OrderVO>) cached;
    }

    R<OrderVO> result = R.ok(orderService.create(dto));

    if (idempotencyKey != null) {
        redis.opsForValue().set("idempotency:" + idempotencyKey, result, Duration.ofHours(24));
    }
    return result;
}
```

抽成 AOP 注解 `@Idempotent` 复用更好。

---

## 七、HTTP 状态码 vs 业务码（双层模型）

### 本项目模型

```
HTTP 状态码 = 传输层语义
业务码（R.code）= 业务语义
```

| 场景 | HTTP | R.code | 说明 |
|---|---|---|---|
| 业务正常 | 200 | `"0"` 或 `"common.success"` | 标准响应 |
| 业务规则失败（订单不存在 / 库存不足） | 200 | `"order.notfound"` 等业务码 | 用 R.fail，不抛 HTTP 错 |
| 参数校验失败（@Valid） | 400 | `"validation.xxx"` | Spring 自动 |
| 鉴权失败 | 401 | `"auth.unauthorized"` | Security 拦截 |
| 权限失败 | 403 | `"auth.forbidden"` | Security 拦截 |
| 路由不存在 | 404 | — | Spring 默认 |
| 系统异常 | 500 | `"common.error.system"` | GlobalExceptionHandler 兜底 |
| 限流 | 429 | `"rate.limit"` | 限流组件返回 |

**铁律**：业务规则失败用 **HTTP 200 + R.fail**，不要 HTTP 4xx —— 让前端统一在拦截器里判 `R.code`，简化处理。

### 错误码体系

详见 `error-code.md`。

---

## 八、请求 / 响应规范

### 请求

| 项 | 约定 |
|---|---|
| Content-Type | `application/json; charset=UTF-8` |
| Authorization | `Bearer {token}`（JWT） |
| Accept-Language | `zh-CN` / `en-US`（详见 `i18n-strategy/_index.md`） |
| Idempotency-Key | UUID（写操作可选） |
| 入参对象 | DTO + `@Valid`（Controller 铁律） |

### 响应

固定结构（`R<T>` / `CommonResult<T>`）：

```json
{
  "code": "0",                    // 业务码（成功为 "0"）
  "msg": "操作成功",                // 已本地化的消息
  "data": { /* T 类型 */ },
  "timestamp": 1714198800000      // 服务端时间戳（可选）
}
```

**禁止**：
- 不同接口返回结构不一致（有的有 `data`，有的没）
- 响应字段下划线命名（统一 camelCase）
- `data` 直接返字符串 / 数字（永远是对象 / 数组）

---

## 九、Forbidden Patterns

| 模式 | 反例 | 正例 |
|---|---|---|
| 动词在 URL 中 | `POST /api/createOrder` | `POST /api/order/orders` |
| GET 写库 | `GET /api/order/cancel?id=1` | `POST /api/order/orders/1:cancel` |
| Map 入参 | `void create(@RequestBody Map params)` | `void create(@RequestBody @Valid OrderCreateDTO dto)` |
| 路径含动词混合 | `/api/order/getList` | `GET /api/order/orders` |
| 路径包含状态 | `/api/order/active-orders` | `GET /api/order/orders?status=ACTIVE` |
| 不分页的列表 API | `GET /api/order/all` | `GET /api/order/orders?pageNum=1&pageSize=20` |
| 业务码 + HTTP 错误码混用 | 200 + R.code=200 表示业务码 | 200 + R.code="0" 表示成功 |
| 单次请求超过 200 行入参（批量） | `[{ ... 1000 个 ... }]` | 走异步：返回 taskId，前端轮询 |

---

## 十、Code Review Checklist（API 设计专项）

- [ ] URL 是资源型 RESTful（小写复数 + 子资源），不是 RPC 风格
- [ ] HTTP 方法语义正确（GET 不写库，PUT 全量，PATCH 部分）
- [ ] 分页参数前后端命名一致（`pageNum` / `pageSize` / `sortField` / `sortOrder`）
- [ ] 列表 API 必分页
- [ ] 写 API 支持幂等（业务键 / Idempotency-Key / DB 唯一约束）
- [ ] 批量操作返回成功 / 失败明细
- [ ] 业务规则失败用 HTTP 200 + R.fail（不用 4xx）
- [ ] 入参 DTO + `@Valid`，出参 VO（详见 Controller 铁律）
- [ ] 路径无动词；命令型动作用 `:action`
- [ ] 异步路径有 `taskId` + `async=true` + `status=QUEUED`（详见 `quality-guidelines.md` 异步规则）
