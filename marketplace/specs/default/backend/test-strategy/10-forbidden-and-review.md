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

- 测试基础设施（spring-boot-starter-test 必须保留）：`backend/quality-guidelines.md` §测试与 Mock
- 不写业务 mock：`backend/quality-guidelines.md` §测试与 Mock + `guides/full-stack-workflow.md`
- 错误码（测试断言时引用）：`backend/error-code.md`
- Maven 配置（jacoco-plugin / failsafe-plugin）：`guides/build-dependency-governance-guide.md`
