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
