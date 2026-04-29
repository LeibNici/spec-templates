## 四、切片测试（20%）

仅起 Spring 的某一层，速度比集成测试快。

### Controller 切片（`@WebMvcTest`）

```java
@WebMvcTest(OrderController.class)
class OrderControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockBean   // 替换 Service 层
    private OrderService orderService;

    @Test
    void should_return200_when_getOrderById() throws Exception {
        when(orderService.getById(1L))
            .thenReturn(OrderFixture.aPendingOrder().build());

        mockMvc.perform(get("/api/order/orders/1"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.code").value("0"))
            .andExpect(jsonPath("$.data.id").value(1));
    }
}
```

### Mapper 切片（`@MybatisPlusTest`）

```java
@MybatisPlusTest
class OrderMapperTest {

    @Autowired
    private OrderMapper orderMapper;

    @Sql("/data/order-fixtures.sql")
    @Test
    void should_findOrders_when_filterByStatus() {
        List<Order> orders = orderMapper.selectList(
            Wrappers.<Order>lambdaQuery().eq(Order::getStatus, OrderStatus.PENDING)
        );
        assertThat(orders).hasSize(3);
    }
}
```

> 切片测试默认起 H2 内存库——**仅可用于纯 SQL 语法验证**，业务测试还得用 Testcontainers。
