## 八、测试数据隔离

### 推荐：每个 @Test 方法 @Transactional + rollback

```java
@SpringBootTest
@Transactional   // 测试结束自动回滚
class OrderIntegrationTest {

    @Test
    void should_createOrder() {
        orderService.create(...);
        // 测试结束后 Spring 自动回滚，不污染 DB
    }
}
```

### 备选：truncate-before-each（慢但更彻底）

```java
@BeforeEach
void cleanup() {
    jdbcTemplate.execute("TRUNCATE TABLE oms_order");
    jdbcTemplate.execute("TRUNCATE TABLE oms_order_item");
}
```

适合：测试涉及多事务（无法 rollback）/ 测试 trigger 行为。

### 用 @Sql 注入 fixture

```java
@Test
@Sql({"/sql/init-customer.sql", "/sql/init-products.sql"})
void should_findOrdersByCustomer() { ... }
```
