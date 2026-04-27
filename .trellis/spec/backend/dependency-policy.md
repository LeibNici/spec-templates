# Backend Dependency Policy

> Companion to `quality-guidelines.md` §依赖规则. This file owns the **dependency-level** rules (banned libraries, transitive enforcement, exception process).
> 独立成文是为了：①避免 `quality-guidelines.md` 膨胀；②给后续依赖选型表预留空间；③让 build/CI 配置改动有专门的 spec 入口。

---

## 直接禁用清单（继承自 `quality-guidelines.md` §依赖规则）

- `xxx-all` 包（如 `hutool-all` → 用 `hutool-core` 或具体子包）
- Swagger / SpringDoc / Springfox 依赖

---

## 依赖传递防腐（铁律）

**铁律**：spec 禁用的依赖不仅本模块 `pom.xml` 不能直接写，还必须确认**任何上游依赖未传递引入**。"我没写"≠"jar 里没有"。

### 风险

- `spring-boot-starter-*` 的下游、第三方 starter、内部 BOM 任一处带 `springdoc-openapi-*` / `io.springfox` / `io.swagger.*`，最终 jar 仍会启 `/swagger-ui.html` + `/v3/api-docs` 端点
- 攻防扫描器专扫这两个端点，配置漂移一次即破防
- 同样适用所有 banned 依赖（fat-all、deprecated、有历史 CVE 的库）

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
              <exclude>org.springdoc:*</exclude>
              <exclude>io.springfox:*</exclude>
              <exclude>io.swagger:*</exclude>
              <exclude>io.swagger.core.v3:*</exclude>
              <exclude>cn.hutool:hutool-all</exclude>
            </excludes>
            <message>本依赖被 spec 禁用，详见 .trellis/spec/backend/dependency-policy.md</message>
          </bannedDependencies>
        </rules>
        <fail>true</fail>
      </configuration>
    </execution>
  </executions>
</plugin>
```

`searchTransitive=true` 是关键 —— 直接 + 传递两层都拦。

### 命中后处理

1. 定位依赖链：

   ```bash
   mvn dependency:tree -Dincludes=org.springdoc:*,io.springfox:*,io.swagger.*:* -pl {module}
   ```

2. 在引入它的 `<dependency>` 上加 `<exclusion>`：

   ```xml
   <dependency>
     <groupId>com.example</groupId>
     <artifactId>some-starter</artifactId>
     <exclusions>
       <exclusion>
         <groupId>org.springdoc</groupId>
         <artifactId>*</artifactId>
       </exclusion>
     </exclusions>
   </dependency>
   ```

3. 重新 `mvn clean package -DskipTests` 验证 enforcer 通过

### 例行检查清单（升级父 pom 或新增 starter 必跑）

- [ ] `mvn dependency:tree | grep -E "swagger|springdoc|springfox|hutool-all"` 无命中
- [ ] enforcer 任务在 CI 跑通（`mvn -DskipTests verify` 已包含 enforcer goal）
- [ ] 新增 ban 项必须同时进 enforcer `<excludes>` 与本文件直接禁用清单（双轨：人读 + 机器拦）

### Why grep pom.xml 不够

- 直接 grep 只看一手依赖，过不了二手
- enforcer 解析的是 effective dependency graph，与最终 jar 一致
- CI 失败比 review 可靠：review 会漏，build 不会

---

## 例外报备

如业务确需引入禁用列表里的库（如对接的三方 SDK 强依赖某禁用项）：

1. PR 描述写明"此依赖被 spec 禁，例外引入原因 + 风险评估 + 退出计划"
2. 父 pom enforcer `<excludes>` 加上对应豁免行 + 注释 issue 链接
3. 例外不得跨模块扩散，仅限该 PR 涉及模块

---

## See Also

- `quality-guidelines.md` §依赖规则 — parent pom / dependencyManagement / pluginManagement 治理原则
- `../guides/build-dependency-governance-guide.md` — Maven 命令铁律、模块分层、跨工程通用治理
