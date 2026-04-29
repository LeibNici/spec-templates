## 三、单元测试（70%）

### 特征

- **不起 Spring 上下文**（不 `@SpringBootTest`）
- 用 `@Mock` mock 所有外部依赖（Mapper / 其他 Service / RestTemplate）
- 关注**业务逻辑分支**

### 模板

```java
@ExtendWith(MockitoExtension.class)
class OrderServiceImplTest {

    @Mock
    private OrderMapper orderMapper;

    @Mock
    private InventoryService inventoryService;

    @InjectMocks
    private OrderServiceImpl orderService;

    @Test
    void should_throwBusinessException_when_orderNotFound() {
        // given
        when(orderMapper.selectById(1L)).thenReturn(null);

        // when & then
        assertThatThrownBy(() -> orderService.getById(1L))
            .isInstanceOf(BusinessException.class)
            .hasFieldOrPropertyWithValue("code", OrderErrorCode.ORDER_NOT_FOUND);
    }

    @Test
    void should_freezeInventory_when_orderConfirmed() {
        // given
        Order order = OrderFixture.aPendingOrder().withId(1L).build();
        when(orderMapper.selectById(1L)).thenReturn(order);

        // when
        orderService.confirm(1L);

        // then
        verify(inventoryService).freeze(eq(order.getProductId()), eq(order.getQuantity()));
    }
}
```

### 测试 Fixture（推荐用 Builder）

```java
public class OrderFixture {

    public static OrderBuilder aPendingOrder() {
        return Order.builder()
            .id(1L)
            .orderNo("TEST-001")
            .status(OrderStatus.PENDING)
            .productId(100L)
            .quantity(5)
            .createTime(LocalDateTime.now());
    }

    public static OrderBuilder aShippedOrder() {
        return aPendingOrder().status(OrderStatus.SHIPPED);
    }
}
```

测试中：

```java
Order order = OrderFixture.aPendingOrder().withId(2L).build();
```
