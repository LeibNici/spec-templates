## 一、测试分层

| 层 | 起 Spring? | 起 DB? | 速度 | 比例 | 工具 |
|---|---|---|---|---|---|
| **单元测试**（Unit） | ❌ | ❌ | 毫秒 | **70%** | JUnit 5 + Mockito |
| **切片测试**（Slice） | 部分（@WebMvcTest / @DataJpaTest） | ❌ 或 H2 | 秒 | **20%** | Spring Test |
| **集成测试**（Integration） | ✅ `@SpringBootTest` | ✅ Testcontainers | 10-30s | **10%** | Testcontainers |
| **E2E**（端到端） | ✅ + 前端 | ✅ 真环境 | 分钟 | **罕见** | Playwright + 真后端 |

**测试金字塔铁律**：单元多、集成少、E2E 极少。倒金字塔（E2E 多）会让 CI 变慢且脆。
