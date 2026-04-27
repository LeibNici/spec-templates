# 后端测试策略

> 后端测试规范。覆盖测试分层、命名约定、覆盖率门禁、Testcontainers 用法、Mock 边界。
> 与 `quality-guidelines.md` "Mock 策略" 段配套（保留 spring-boot-starter-test 依赖是基础前提）。

---

## 一、测试分层

| 层 | 起 Spring? | 起 DB? | 速度 | 比例 | 工具 |
|---|---|---|---|---|---|
| **单元测试**（Unit） | ❌ | ❌ | 毫秒 | **70%** | JUnit 5 + Mockito |
| **切片测试**（Slice） | 部分（@WebMvcTest / @DataJpaTest） | ❌ 或 H2 | 秒 | **20%** | Spring Test |
| **集成测试**（Integration） | ✅ `@SpringBootTest` | ✅ Testcontainers | 10-30s | **10%** | Testcontainers |
| **E2E**（端到端） | ✅ + 前端 | ✅ 真环境 | 分钟 | **罕见** | Playwright + 真后端 |

**测试金字塔铁律**：单元多、集成少、E2E 极少。倒金字塔（E2E 多）会让 CI 变慢且脆。

---

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

---

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

---

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

---

## 五、集成测试（10%）

### 用 Testcontainers 起真 MySQL / Redis

```java
@SpringBootTest
@Testcontainers
class OrderIntegrationTest {

    @Container
    static MySQLContainer<?> mysql = new MySQLContainer<>("mysql:8.0")
        .withDatabaseName("test")
        .withUsername("test")
        .withPassword("test");

    @Container
    static GenericContainer<?> redis = new GenericContainer<>("redis:7-alpine")
        .withExposedPorts(6379);

    @DynamicPropertySource
    static void registerProps(DynamicPropertyRegistry registry) {
        registry.add("spring.datasource.url", mysql::getJdbcUrl);
        registry.add("spring.datasource.username", mysql::getUsername);
        registry.add("spring.datasource.password", mysql::getPassword);
        registry.add("spring.data.redis.host", redis::getHost);
        registry.add("spring.data.redis.port", () -> redis.getMappedPort(6379));
    }

    @Autowired
    private OrderService orderService;

    @Test
    void should_persistOrder_when_create() {
        OrderCreateDTO dto = OrderCreateDTO.builder()
            .customerId(1L).productId(100L).quantity(5).build();

        OrderVO vo = orderService.create(dto);

        assertThat(vo.getId()).isNotNull();
        assertThat(vo.getOrderNo()).startsWith("ORD-");
    }
}
```

### Singleton Container（共享，提速）

整个 test suite 共享一个容器（不要每个 test class 重起）：

```java
public abstract class AbstractIntegrationTest {

    static final MySQLContainer<?> mysql;
    static final GenericContainer<?> redis;

    static {
        mysql = new MySQLContainer<>("mysql:8.0").withReuse(true);
        redis = new GenericContainer<>("redis:7-alpine").withExposedPorts(6379).withReuse(true);
        mysql.start();
        redis.start();
    }
}

@SpringBootTest
class OrderIntegrationTest extends AbstractIntegrationTest { ... }
```

启用 reuse：在 `~/.testcontainers.properties` 加 `testcontainers.reuse.enable=true`。

### 反模式：H2

```java
// ❌ FORBIDDEN：H2 与 MySQL 行为差异
spring.datasource.url=jdbc:h2:mem:test
```

H2 与 MySQL 在以下行为不同：
- ON CONFLICT / ON DUPLICATE KEY UPDATE 语法
- BIGINT UNSIGNED
- BLOB 处理
- 日期时区
- `utf8mb4_general_ci` 排序规则

测试通过不代表生产能跑。

---

## 六、覆盖率门禁

### 起步阶段（推荐）

- **不强制覆盖率**
- 但要求**核心业务方法**（写操作 / 状态流转 / 计算）必须有测试

### 团队稳定后

| 模块类型 | 行覆盖率门禁 | 工具 |
|---|---|---|
| 核心业务（order / inventory） | **80%** | JaCoCo |
| 工具类（utils / common） | **90%** | 同上 |
| Controller / Mapper | **60%**（间接覆盖即可） | 同上 |
| DTO / VO / Entity | **不强制** | 同上 |

### Maven JaCoCo 集成

```xml
<plugin>
    <groupId>org.jacoco</groupId>
    <artifactId>jacoco-maven-plugin</artifactId>
    <version>${jacoco.version}</version>
    <executions>
        <execution>
            <goals><goal>prepare-agent</goal></goals>
        </execution>
        <execution>
            <id>report</id>
            <phase>verify</phase>
            <goals><goal>report</goal></goals>
        </execution>
        <execution>
            <id>check</id>
            <goals><goal>check</goal></goals>
            <configuration>
                <rules>
                    <rule>
                        <element>BUNDLE</element>
                        <limits>
                            <limit>
                                <counter>LINE</counter>
                                <minimum>0.70</minimum>
                            </limit>
                        </limits>
                    </rule>
                </rules>
            </configuration>
        </execution>
    </executions>
</plugin>
```

---

## 七、Mock 策略（与 quality-guidelines.md 呼应）

### Mock 边界（再次强调）

| 测试层 | Mock 谁 | 用什么 |
|---|---|---|
| 单元测试 | mock 所有外部（Mapper / 其他 Service / RestTemplate） | `@Mock` |
| 切片测试 Controller | mock Service | `@MockBean` |
| 切片测试 Mapper | 不 mock，用 H2 或 Testcontainers | — |
| 集成测试 | 仅 mock 外部三方 API | `@MockBean` 或 WireMock |
| 集成测试 DB / Redis | **不 mock**，Testcontainers | Testcontainers |

### 反模式

```java
// ❌ 集成测试 mock 了 Mapper —— 失去集成测试的意义
@MockBean
private OrderMapper orderMapper;
```

集成测试的价值就是验证"业务逻辑 + DB + Redis"的真实交互；mock Mapper 等于变成单元测试还更慢。

---

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

---

## 九、测试执行策略

### 本地

```bash
# 跑单元测试 + 切片测试（快）
mvn test

# 跑集成测试（含 Testcontainers）
mvn verify

# 跑特定测试类
mvn test -Dtest=OrderServiceImplTest

# 跑特定测试方法
mvn test -Dtest=OrderServiceImplTest#should_returnOrder_when_orderExists
```

### CI

```yaml
# .github/workflows/ci.yml
- name: Unit + Slice tests
  run: mvn test           # PR 必跑

- name: Integration tests
  run: mvn verify -DskipUnitTests=true     # 夜间或 main merge 后跑
```

**理由**：单元 + 切片测试要快（< 2 min），保 PR 反馈速度；集成测试慢（10-30 min），分阶段跑。

---

## 十、Forbidden Patterns

| 模式 | 反例 | 正例 |
|---|---|---|
| 测试间共享状态 | `static List<Order> data;` 在多 test 间累积 | 每个 @Test 自己 setup |
| 顺序依赖 | `test1` 必须在 `test2` 前跑 | 用 `@TestMethodOrder` 显式声明，或解耦 |
| 真接外部 API | 直接调微信支付 sandbox | mock 外部 API（WireMock） |
| H2 替代 MySQL 集成测试 | `jdbc:h2:mem:test` | Testcontainers |
| 测试无断言 | 只 `service.create(...)` 不 `assertThat(...)` | 显式断言结果 |
| 测试方法 > 100 行 | 一个测试覆盖 10 种场景 | 拆分成 N 个 @Test |
| 测试 catch + 吃异常 | `try { ... } catch (Exception e) {}` | `assertThatThrownBy(...).isInstanceOf(...)` |

---

## 十一、Code Review Checklist（测试专项）

- [ ] 新增业务方法配套有测试
- [ ] 测试方法名 `should_xxx_when_xxx` 格式
- [ ] 单元测试无 `@SpringBootTest`
- [ ] 集成测试用 Testcontainers，不用 H2
- [ ] 集成测试不 mock Mapper
- [ ] 测试间状态隔离（@Transactional 或 truncate）
- [ ] 测试无 `Thread.sleep`（用 Awaitility 或事件等待）
- [ ] 断言明确（`assertThat(...).isEqualTo(...)`）
- [ ] 异常路径有覆盖（`assertThatThrownBy(...)`）

---

## 十二、相关 spec

- 测试基础设施（spring-boot-starter-test 必须保留）：`backend/quality-guidelines.md`
- 不写业务 mock：`backend/quality-guidelines.md` "Mock 策略" + `guides/full-stack-workflow.md`
- 错误码（测试断言时引用）：`backend/error-code.md`
- Maven 配置（jacoco-plugin / failsafe-plugin）：`guides/build-dependency-governance-guide.md`
