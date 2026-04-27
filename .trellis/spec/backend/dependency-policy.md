# Backend Dependency Policy

> Companion to `quality-guidelines.md` §依赖规则. This file owns the **dependency-level** rules: selection criteria, banned libraries, transitive enforcement, and the exception process.
> 独立成文是为了：①避免 `quality-guidelines.md` 膨胀；②集中维护 ban list 与 enforcer 配置；③让 build/CI 改动有专门 spec 入口。

---

## 选型客观指标（铁律）

新增 / 替换依赖必须按以下硬指标筛选，**与发行国 / 作者无关**：

| 指标 | 阈值 | 否决理由 |
|---|---|---|
| Spring Boot autoconfig 优先 | 有等价 starter / autoconfig 即用 | 减少配置漂移，社区统一 |
| 历史 Critical CVE 数 | 近 5 年 ≥ 2 条直接命中 | 攻击面持续暴露，上游响应慢 |
| 维护活跃度 | 12 个月内必须有 release / commit | 弃坑库会成为 supply chain 死角 |
| Fat-all 包 | 一律禁 | 引入 MB 级无关 class，审计困难 |
| 默认对外暴露的运行时端点 | 一律禁 | 与 Swagger 同理（攻击面） |
| 同类库（JSON / 日志 / 连接池） | 全局唯一一个 | 多实现并存导致语义不一致、依赖膨胀 |

### Why 不按"地理来源"分

发行地不是技术指标。维护活跃、CVE 历史、生态契合度才是 —— 同样的客观指标会保留 MyBatis-Plus（活跃、低 CVE）、淘汰 fastjson（维护节奏滞后、CVE 高）。地缘描述会让 spec 失去客观性，新人接手时无从执行。

---

## 直接禁用清单（带替代方案）

| 禁用 | 替代 | Why |
|---|---|---|
| `org.springdoc:*` / `io.springfox:*` / `io.swagger:*` / `io.swagger.core.v3:*` | 不引（团队内文档走 Javadoc + Checkstyle，前端契约走 TS interface） | 默认 `/swagger-ui.html` `/v3/api-docs` 端点对外暴露，攻击面 |
| `com.alibaba:fastjson` | `com.fasterxml.jackson.core:jackson-databind`（SB 自带） | 多次反序列化 RCE（CVE-2017-18349 / CVE-2022-25845 等）；JSON 库全局唯一铁律 |
| `com.alibaba:fastjson2` | 同上 Jackson | 项目已用 Jackson；新接口禁用，避免双 JSON 库语义分裂 |
| `com.alibaba:druid` / `com.alibaba:druid-spring-boot-starter` | `com.zaxxer:HikariCP`（SB 默认） | druid `/druid/*` 监控页默认对外暴露（同 Swagger 风险）；HikariCP 性能更优且零配置 |
| `cn.hutool:hutool-all` | `cn.hutool:hutool-core` 或具体子包 | fat-all 禁用 |
| `log4j:log4j`（1.x） | `logback-classic`（SB 默认） | EOL，无补丁通道 |
| `org.apache.logging.log4j:log4j-core` 版本 < `2.17.1` | 升级至 ≥ 2.22 或回退 logback | Log4Shell 系列 CVE |
| 任意第二个 JSON 库（`com.google.code.gson:gson` / `com.squareup.moshi:moshi` / `com.jsoniter:jsoniter` 等） | `Jackson` | 全局唯一 JSON 库铁律；新依赖前先核对此条 |

**双轨同步规则**（人读 + 机器拦）：本表格每条新增/移除必须同时反映到下面 `maven-enforcer-plugin` 的 `<excludes>` 列表中。改一处不改另一处即视为违反 spec。

---

## 依赖传递防腐（铁律）

**铁律**：spec 禁用的依赖不仅本模块 `pom.xml` 不能直接写，还必须确认**任何上游依赖未传递引入**。"我没写"≠"jar 里没有"。

### 风险

- `spring-boot-starter-*` 的下游、第三方 starter、内部 BOM 任一处带 banned 依赖，最终 jar 仍会启对应端点 / class
- 攻防扫描器专扫 `/swagger-ui.html`、`/druid/*` 这类端点，配置漂移一次即破防
- CVE 历史库（fastjson / log4j 1.x / log4j-core < 2.17.1）传递引入即等于运行时持有

### Required：父 pom 用 maven-enforcer-plugin build 期机器拦截

```xml
<plugin>
  <groupId>org.apache.maven.plugins</groupId>
  <artifactId>maven-enforcer-plugin</artifactId>
  <executions>
    <execution>
      <id>ban-banned-dependencies</id>
      <goals><goal>enforce</goal></goals>
      <configuration>
        <rules>
          <bannedDependencies>
            <searchTransitive>true</searchTransitive>
            <excludes>
              <!-- API doc endpoints (attack surface) -->
              <exclude>org.springdoc:*</exclude>
              <exclude>io.springfox:*</exclude>
              <exclude>io.swagger:*</exclude>
              <exclude>io.swagger.core.v3:*</exclude>
              <!-- JSON: keep Jackson as the only library -->
              <exclude>com.alibaba:fastjson</exclude>
              <exclude>com.alibaba:fastjson2</exclude>
              <exclude>com.google.code.gson:gson</exclude>
              <!-- Connection pool: druid monitor endpoint is default-exposed -->
              <exclude>com.alibaba:druid</exclude>
              <exclude>com.alibaba:druid-spring-boot-starter</exclude>
              <!-- Logging: ban log4j 1.x and Log4Shell-vulnerable log4j-core -->
              <exclude>log4j:log4j</exclude>
              <exclude>org.apache.logging.log4j:log4j-core:(,2.17.1)</exclude>
              <!-- Fat-all packages -->
              <exclude>cn.hutool:hutool-all</exclude>
            </excludes>
            <message>本依赖被 spec 禁用，详见 .trellis/spec/backend/dependency-policy.md §直接禁用清单</message>
          </bannedDependencies>
        </rules>
        <fail>true</fail>
      </configuration>
    </execution>
  </executions>
</plugin>
```

`searchTransitive=true` 是关键 —— 直接 + 传递两层都拦。版本范围语法 `(,2.17.1)` = "凡 < 2.17.1 一律禁"。

### 命中后处理

1. 定位依赖链：

   ```bash
   mvn dependency:tree -Dincludes=com.alibaba:fastjson,com.alibaba:druid,org.springdoc:* -pl {module}
   ```

2. 在引入它的 `<dependency>` 上加 `<exclusion>`：

   ```xml
   <dependency>
     <groupId>com.example</groupId>
     <artifactId>some-starter</artifactId>
     <exclusions>
       <exclusion>
         <groupId>com.alibaba</groupId>
         <artifactId>fastjson</artifactId>
       </exclusion>
     </exclusions>
   </dependency>
   ```

3. 重新 `mvn clean package -DskipTests` 验证 enforcer 通过

### 例行检查清单（升级父 pom 或新增 starter 必跑）

- [ ] `mvn dependency:tree | grep -E "fastjson|druid|swagger|springdoc|springfox|hutool-all|log4j-core"` 无非预期命中
- [ ] enforcer 任务在 CI 跑通（`mvn -DskipTests verify` 已包含 enforcer goal）
- [ ] 新增 ban 项必须同时进本文 §直接禁用清单 表格 + enforcer `<excludes>`（双轨）

### Why grep pom.xml 不够

- 直接 grep 只看一手依赖，过不了二手
- enforcer 解析的是 effective dependency graph，与最终 jar 一致
- CI 失败比 review 可靠：review 会漏，build 不会

---

## 例外报备

如业务确需引入禁用列表里的库（如对接的三方 SDK 强依赖某禁用项）：

1. PR 描述写明：**例外原因 + 风险评估 + 退出计划**（含目标日期或目标版本）
2. 父 pom enforcer `<excludes>` 删除对应行（或注释豁免）+ 行尾注释 issue / ticket 链接
3. 例外**不得跨模块扩散** —— 仅限该 PR 涉及模块；同一例外被第二个模块复用必须重新走例外流程
4. 例外审批者不应是 PR 作者本人（避免自我背书）

---

## See Also

- `quality-guidelines.md` §依赖规则 — parent pom / dependencyManagement / pluginManagement 治理原则
- `../guides/build-dependency-governance-guide.md` — Maven 命令铁律、模块分层、跨工程通用治理
- `../guides/index.md` §Enforcement — spec 自身的 size/H2 机器拦截（同思路：双轨）
