## 3. 硬编码

### 3.1 状态值常量化

```java
// FORBIDDEN: 裸字符串散落各处
order.setStatus("WAITING_PRODUCTION");
if ("COMPLETED".equals(order.getStatus())) { ... }

// CORRECT: 常量类集中定义
public final class OrderStatus {
    public static final String WAITING = "WAITING_PRODUCTION";
    public static final String COMPLETED = "COMPLETED";
    private OrderStatus() {}
}
order.setStatus(OrderStatus.WAITING);
```

**规则：同一状态字符串出现 ≥2 处，必须提取为常量。**

### 3.2 业务阈值可配

```java
// FORBIDDEN: 硬编码阈值
if (daysUntilPurchase <= 7) { urgency = "URGENT"; }

// CORRECT: 配置表或 @Value
private static final int WARNING_THRESHOLD_DAYS =
    Integer.parseInt(configService.getValue("mrp.warning.days", "7"));
```

### 3.3 日期格式集中

```java
// FORBIDDEN: "yyyy-MM-dd" 散落 N 处
LocalDate.parse(s, DateTimeFormatter.ofPattern("yyyy-MM-dd"));

// CORRECT: 常量定义
public final class DateFormats {
    public static final DateTimeFormatter ISO_DATE = DateTimeFormatter.ofPattern("yyyy-MM-dd");
}
```

### 3.4 数字字面量

除 `0 / 1 / -1` 外，所有数字字面量必须命名为 `private static final` 常量。
