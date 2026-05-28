# 错误码体系

> 错误码 = `R<T>` 中 `code` 字段的取值规则。与 `i18n-strategy/_index.md`（消息本地化）、`error-handling.md`（异常处理）、`api-design.md`（HTTP vs 业务码）配套。

---

## 一、设计原则

1. **字符串而非数字**：可读性优先，可作 i18n key 直接复用
2. **按模块分类前缀**：定位失败模块零成本（`USER_*` / `ORDER_*`）
3. **稳定不变**：发布后**禁止**改 code 字面量（前端可能依赖判断）
4. **HTTP 状态码 + 业务码双层**：HTTP 表传输层，业务码表业务语义（详见 `api-design.md` §7）

---

## 二、错误码格式

```
{MODULE}_{CATEGORY}_{SPECIFIC}
```

| 段 | 规则 | 示例 |
|---|---|---|
| `MODULE` | 模块名大写（ORDER / INVENTORY / USER / AUTH / VALID / SYS） | `ORDER` |
| `CATEGORY` | 错误大类（NOT_FOUND / DUPLICATE / FORBIDDEN / INVALID / TIMEOUT） | `NOT_FOUND` |
| `SPECIFIC` | 具体错误（可省，模块单一时） | （无） |

### 通用前缀（系统级）

| 前缀 | 含义 | 示例 |
|---|---|---|
| `COMMON_` | 通用错误 | `COMMON_SUCCESS` / `COMMON_SYSTEM_ERROR` |
| `AUTH_` | 鉴权失败 | `AUTH_UNAUTHORIZED` / `AUTH_TOKEN_EXPIRED` |
| `PERM_` | 权限失败 | `PERM_FORBIDDEN` / `PERM_NO_DATA_PERMISSION` |
| `VALID_` | 参数校验失败 | `VALID_REQUIRED` / `VALID_FORMAT` |
| `SYS_` | 系统级（限流 / 熔断 / 数据库） | `SYS_RATE_LIMIT` / `SYS_DB_ERROR` |

### 业务前缀

| 前缀 | 模块 | 示例 |
|---|---|---|
| `ORDER_` | 订单 | `ORDER_NOT_FOUND` / `ORDER_CANNOT_CANCEL` |
| `INVENTORY_` | 库存 | `INVENTORY_INSUFFICIENT` |
| `USER_` | 用户 | `USER_NOT_FOUND` / `USER_DISABLED` |
| `CUSTOMER_` | 客户 | `CUSTOMER_DUPLICATE` |

---

## 三、组织代码

### 一个模块一个 ErrorCode 类

```java
// {biz}-module/src/main/java/com/{org}/{biz}/constant/OrderErrorCode.java
public final class OrderErrorCode {

    private OrderErrorCode() {}

    public static final String ORDER_NOT_FOUND        = "ORDER_NOT_FOUND";
    public static final String ORDER_CANNOT_CANCEL    = "ORDER_CANNOT_CANCEL";
    public static final String ORDER_DUPLICATE_NO     = "ORDER_DUPLICATE_NO";
    public static final String ORDER_STATUS_INVALID   = "ORDER_STATUS_INVALID";
    public static final String ORDER_AMOUNT_INVALID   = "ORDER_AMOUNT_INVALID";
}
```

### 通用错误码放 common 模块

```java
// {app}-common/src/main/java/com/{org}/common/constant/CommonErrorCode.java
public final class CommonErrorCode {

    private CommonErrorCode() {}

    public static final String COMMON_SUCCESS         = "0";  // 唯一不带前缀
    public static final String COMMON_SYSTEM_ERROR    = "COMMON_SYSTEM_ERROR";
    public static final String COMMON_NOT_FOUND       = "COMMON_NOT_FOUND";

    public static final String AUTH_UNAUTHORIZED      = "AUTH_UNAUTHORIZED";
    public static final String AUTH_TOKEN_EXPIRED     = "AUTH_TOKEN_EXPIRED";
    public static final String PERM_FORBIDDEN         = "PERM_FORBIDDEN";

    public static final String VALID_REQUIRED         = "VALID_REQUIRED";
    public static final String VALID_FORMAT           = "VALID_FORMAT";

    public static final String SYS_RATE_LIMIT         = "SYS_RATE_LIMIT";
    public static final String SYS_DB_ERROR           = "SYS_DB_ERROR";
}
```

---

## 四、与 i18n 集成

### 错误码就是 i18n key

```properties
# messages_zh_CN.properties
ORDER_NOT_FOUND=订单 {0} 不存在
ORDER_CANNOT_CANCEL=订单已发货，无法取消
ORDER_DUPLICATE_NO=订单号 {0} 已存在
USER_DISABLED=用户已被禁用

# messages_en_US.properties
ORDER_NOT_FOUND=Order {0} not found
ORDER_CANNOT_CANCEL=Order already shipped, cannot cancel
ORDER_DUPLICATE_NO=Order number {0} already exists
USER_DISABLED=User has been disabled
```

### 抛出 + 翻译

```java
// 抛出（业务代码）
throw new BusinessException(OrderErrorCode.ORDER_NOT_FOUND, orderId);

// GlobalExceptionHandler 翻译
@ExceptionHandler(BusinessException.class)
public R<?> handle(BusinessException e, Locale locale) {
    String msg = messageSource.getMessage(e.getCode(), e.getArgs(), locale);
    return R.fail(e.getCode(), msg);
}
```

### 响应

```json
{
  "code": "ORDER_NOT_FOUND",
  "msg": "订单 12345 不存在",
  "data": null
}
```

---

## 五、HTTP 状态码与业务码的双层映射

| HTTP | 业务 code 范例 | 触发点 |
|---|---|---|
| 200 | `"0"` | 业务正常 |
| 200 | `ORDER_NOT_FOUND`、`USER_DISABLED` 等业务错 | `R.fail(code)`（业务规则失败） |
| 400 | `VALID_REQUIRED`、`VALID_FORMAT` | `@Valid` 校验失败（Spring 自动） |
| 401 | `AUTH_UNAUTHORIZED`、`AUTH_TOKEN_EXPIRED` | Spring Security 拦截 |
| 403 | `PERM_FORBIDDEN` | Spring Security 权限拦截 |
| 404 | （无业务 code） | Spring 默认（路由不存在） |
| 429 | `SYS_RATE_LIMIT` | 限流组件返回 |
| 500 | `COMMON_SYSTEM_ERROR` | GlobalExceptionHandler 兜底 |

**铁律**：
- 业务规则失败（订单不存在 / 库存不足）→ **HTTP 200 + R.fail(业务 code)**
- 不要把所有错误都映射成 HTTP 4xx —— 前端拦截器要根据 HTTP 状态再分支判断业务码，复杂

---

## 六、特殊错误码

### 成功

```
COMMON_SUCCESS = "0"
```

唯一一个不带前缀的 code（与历史习惯一致；前端判 `code === "0"`）。

### 兜底

```
COMMON_SYSTEM_ERROR = "COMMON_SYSTEM_ERROR"  ← 未捕获异常
COMMON_PARAM_ERROR  = "COMMON_PARAM_ERROR"   ← 未明确分类的参数问题
```

---

## 七、Forbidden 模式

### ❌ 用数字 code

```java
// FORBIDDEN
public static final int ORDER_NOT_FOUND = 10001;
```

数字方案的问题：
- 编号方案稀疏（10001、10002、20001）维护麻烦
- 不能直接当 i18n key
- 阅读 log 时看不出业务含义

### ❌ 在业务代码里硬编码 code 字符串

```java
// FORBIDDEN
throw new BusinessException("ORDER_NOT_FOUND", orderId);  // 字符串字面量

// CORRECT
throw new BusinessException(OrderErrorCode.ORDER_NOT_FOUND, orderId);
```

### ❌ 改了 code 但忘记改 i18n properties

最常见漂移点。Review 时务必检查"code 字面 = properties key"。

### ❌ 一个 code 表示多种含义

```java
// FORBIDDEN
public static final String ORDER_ERROR = "ORDER_ERROR";  // 太宽泛

// CORRECT
public static final String ORDER_NOT_FOUND      = "ORDER_NOT_FOUND";
public static final String ORDER_DUPLICATE_NO   = "ORDER_DUPLICATE_NO";
public static final String ORDER_CANNOT_CANCEL  = "ORDER_CANNOT_CANCEL";
```

### ❌ 跨模块共享业务 code

```java
// FORBIDDEN
OrderErrorCode.NOT_FOUND  // 在 user 模块抛 OrderErrorCode

// CORRECT
UserErrorCode.USER_NOT_FOUND
OrderErrorCode.ORDER_NOT_FOUND
```

---

## 八、Code Review Checklist

- [ ] 抛出 `BusinessException` 时使用常量类引用，无字符串字面量
- [ ] 新增 code 同步在 `messages_zh_CN.properties` + `messages_en_US.properties` 加映射
- [ ] code 命名遵循 `{MODULE}_{CATEGORY}_{SPECIFIC}` 三段格式
- [ ] 单一 code 表达单一业务含义（不重叠）
- [ ] 跨模块时用各自模块的 ErrorCode 类
- [ ] 已发布的 code **未变动**（向后兼容铁律）
- [ ] 通用前缀（`AUTH_` / `PERM_` / `VALID_` / `SYS_` / `COMMON_`）放在 `{app}-common`
- [ ] 业务前缀放在对应模块（`OrderErrorCode` 在 order 模块内）

---

## 九、扩展：错误码 → HTTP 状态码映射（可选）

如果项目对外暴露 API（开放平台 / 移动 App），可加映射表让 GlobalExceptionHandler 根据 code 返不同 HTTP：

```java
private static final Map<String, HttpStatus> CODE_TO_HTTP = Map.of(
    "AUTH_UNAUTHORIZED",  HttpStatus.UNAUTHORIZED,
    "AUTH_TOKEN_EXPIRED", HttpStatus.UNAUTHORIZED,
    "PERM_FORBIDDEN",     HttpStatus.FORBIDDEN,
    "SYS_RATE_LIMIT",     HttpStatus.TOO_MANY_REQUESTS
);
// 业务 code 默认 HTTP 200
```

中后台项目通常**不需要**这层映射—— HTTP 200 + R.code 已够用。
