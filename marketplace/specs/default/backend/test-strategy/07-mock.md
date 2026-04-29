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
