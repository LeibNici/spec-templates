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
