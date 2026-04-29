## 二、命名约定

### 测试类

```java
// 测试类与被测类同名 + Test 后缀
OrderServiceImpl.java          → OrderServiceImplTest.java
OrderController.java           → OrderControllerTest.java
OrderQueryService.java         → OrderQueryServiceTest.java
```

### 测试方法

**强制格式**：`should_{ExpectedBehavior}_when_{Condition}`

```java
@Test
void should_returnOrder_when_orderExists() { ... }

@Test
void should_throwBusinessException_when_orderNotFound() { ... }

@Test
void should_skipInvalidItems_when_batchCreateContainsErrors() { ... }
```

**禁止**：

```java
@Test
void test1() { ... }                    // ❌ 无信息
@Test
void testCreateOrder() { ... }          // ❌ 没说预期
@Test
void createOrder_success() { ... }      // ❌ 不够明确
@Test
void 创建订单成功() { ... }              // ❌ 中文方法名（部分工具不支持）
```
