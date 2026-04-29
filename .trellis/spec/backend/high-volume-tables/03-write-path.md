# 3. 写入路径

> AOP 注解驱动 + 事务隔离 + 独立线程池。业务代码零侵入。

---

## 3.1 `@OperationLog` 注解

```java
@Target(ElementType.METHOD)
@Retention(RetentionPolicy.RUNTIME)
public @interface OperationLog {
    String action();                       // CREATE / UPDATE / DELETE / ...
    String bizType();                      // ORDER / USER / ROLE / ...
    String bizIdSpEL()  default "";        // SpEL 取业务主键，如 "#result.id"
    String bizNoSpEL()  default "";        // SpEL 取业务编号，如 "#result.orderNo"
    boolean recordPayload() default true;  // 是否记录入参快照
}
```

业务代码：

```java
@Service
public class OrderServiceImpl implements OrderService {

    @OperationLog(action = "CREATE", bizType = "ORDER",
                  bizIdSpEL = "#result.id", bizNoSpEL = "#result.orderNo")
    @Transactional(rollbackFor = Exception.class)
    public OrderVO create(@Valid OrderCreateDTO dto) {
        Order order = ...;
        return convert(order);
    }
}
```

---

## 3.2 切面铁律

```java
@Aspect
@Component
@RequiredArgsConstructor
public class OperationLogAspect {

    private final ApplicationEventPublisher publisher;

    @AfterReturning(pointcut = "@annotation(operationLog)", returning = "result")
    public void afterSuccess(JoinPoint jp, OperationLog operationLog, Object result) {
        OperationLogEvent evt = build(jp, operationLog, result, "SUCCESS", null);
        publisher.publishEvent(evt);   // 发事件，由独立监听器异步入库
    }

    @AfterThrowing(pointcut = "@annotation(operationLog)", throwing = "ex")
    public void afterFail(JoinPoint jp, OperationLog operationLog, Throwable ex) {
        OperationLogEvent evt = build(jp, operationLog, null, "FAIL", ex.getMessage());
        publisher.publishEvent(evt);
    }
}
```

切面行为铁律：

| 项 | 要求 |
|---|---|
| 异常隔离 | 切面自身**绝不抛异常**给业务方法（try-catch 兜底，失败仅 `log.warn`） |
| 事务隔离 | **不参与业务事务**——切面发 `ApplicationEvent`，监听器用 `@TransactionalEventListener(AFTER_COMMIT)` 接，业务回滚则日志不写 |
| 异步写入 | 监听器用独立线程池（见 3.3） |
| SpEL 求值 | 必须 try-catch；解析失败时 `bizId/bizNo` 设 NULL，不阻塞日志写入 |
| 失败降级 | 写入失败 → `log.warn` + Micrometer counter；**绝不重试 retry-loop**（防雪崩） |

---

## 3.3 独立线程池

```java
@Bean("operationLogExecutor")
public ThreadPoolTaskExecutor operationLogExecutor() {
    ThreadPoolTaskExecutor pool = new ThreadPoolTaskExecutor();
    pool.setCorePoolSize(2);
    pool.setMaxPoolSize(8);
    pool.setQueueCapacity(2000);
    pool.setThreadNamePrefix("op-log-");
    pool.setRejectedExecutionHandler(
        new ThreadPoolExecutor.CallerRunsPolicy()    // 队列满时退化为同步写
    );
    pool.setWaitForTasksToCompleteOnShutdown(true);
    pool.setAwaitTerminationSeconds(10);
    return pool;
}
```

约定：
- **不复用** `@Async` 默认线程池（与业务异步任务隔离）
- 队列满 `CallerRunsPolicy` 降级——宁可短暂卡业务也不丢日志（合规要求下）
- Graceful shutdown 等队列清空，最长 10 秒

---

## 3.4 监听器实现

```java
@Component
@RequiredArgsConstructor
public class OperationLogListener {

    private final OperationLogMapper mapper;

    @Async("operationLogExecutor")
    @TransactionalEventListener(phase = TransactionPhase.AFTER_COMMIT)
    public void onEvent(OperationLogEvent evt) {
        try {
            mapper.insert(evt.toEntity());
        } catch (Exception e) {
            log.warn("operation log insert failed: {}", evt.getRequestId(), e);
            Metrics.counter("operation_log.insert.fail").increment();
        }
    }
}
```

---

→ 下一步：[04-query-rules.md](./04-query-rules.md)
