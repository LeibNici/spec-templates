# Build & Dependency Governance Guide

> **Purpose**: Keep dependency and build configuration hierarchical, predictable, and reusable across projects.

---

## Why This Matters

When each module manages versions independently, projects drift quickly:

- Same library appears in multiple versions
- Upgrade cost grows non-linearly
- Security patching becomes slow and error-prone
- Build behavior differs by module

**Goal**: one source of truth, layered ownership, minimal duplication.

---

## Core Principles (All Projects)

1. **Single Source of Truth for Versions**
   - Library versions must be centrally managed
   - Module-level files should reference coordinates, not define versions

2. **Hierarchical Ownership**
   - Root/parent manages versions and build policies
   - Child modules only declare what they use

3. **Deterministic Structure**
   - Build files should follow a fixed order and layout
   - New contributors should predict where any config lives

4. **No Silent Drift**
   - Any new dependency/version must be added centrally first
   - Child overrides are exceptions, not defaults

---

## Maven Standard (Recommended Baseline)

### Parent POM Responsibilities

- `properties`: central version keys (`xxx.version`)
- `dependencyManagement`: all managed dependency versions
- `pluginManagement`: plugin versions/config baselines
- shared compiler/encoding/java settings

### Child Module POM Responsibilities

- declare only required dependencies
- no explicit `<version>` for centrally managed dependencies
- no independent repository/plugin version policy unless explicitly approved

### POM Section Order (Keep Consistent)

1. `modelVersion`
2. `parent`
3. `groupId/artifactId/version/packaging/name/description`
4. `modules` (aggregator only)
5. `properties`
6. `dependencyManagement`
7. `dependencies`
8. `build` (`pluginManagement` before `plugins` when both exist)
9. `profiles`

---

## Layered Module Convention

For multi-module backends, module order should reflect architecture layers:

1. base/common
2. framework/platform
3. integration/adapters
4. business/domain modules
5. app/startup/assembly

This reduces circular dependency pressure and clarifies ownership.

---

## Allowed Exceptions

A child module may temporarily pin a version only when:

- central upgrade is blocked by compatibility constraints, **and**
- there is an issue/task link plus removal deadline in comment

Without these two conditions, child-level version pinning is **not allowed**.

---

## Anti-Patterns

| Anti-Pattern | Risk |
|---|---|
| 每个模块自己定义依赖版本 | 版本漂移、升级困难 |
| 同一插件版本在多模块重复 | 插件行为不一致 |
| 临时加依赖不更新 parent | 隐藏的传递性冲突 |
| 随机的 POM section 顺序 | 高维护成本 |
| `mvn package -pl xxx-admin` 不带 `-am` | spring-boot repackage 嵌入 .m2 旧依赖 jar，新 Controller / Service 静默 404 无任何启动错误 |
| `mvn install` 写脏 .m2 当解决方案 | 表面缓解，根因仍在；下次别人 clone 又复发；项目规范明令禁用 |
| `mvn spring-boot:run` | 也从 .m2 加载，必有旧 jar 风险 |

---

## Maven 命令铁律（spring-boot 多模块）

**唯一合规命令**（admin 模块为例）：

```bash
mvn clean package -DskipTests -pl {app}-admin -am -f {path-to-backend}/pom.xml
```

| 选项 | 作用 | 省略后果 |
|---|---|---|
| `-pl {app}-admin` | 只打目标模块 | 不带等于 build 整个 reactor，慢 2~3 倍但永远安全 |
| **`-am`** | also-make：把目标模块依赖的所有上游模块也一起 build 进 reactor，并将 `target/*.jar` 同 reactor 嵌入 spring-boot nested jar | **省略后从 `~/.m2/repository` 拉旧 jar 嵌入；新增 class 不在最终 jar 中；启动后请求路径 404；启动日志无任何错误** |
| `-DskipTests` | 跳过测试 | 不影响打包正确性 |
| `-f xxx/pom.xml` | 指定 pom 路径 | 避免 `cd xxx &&` 复合命令 |

**禁用**：`mvn install`（写脏 .m2，CI 与本地不一致）、`mvn spring-boot:run`（同上风险）。

---

## Silent 404 诊断 Checklist

新增 Controller/Service 后路径 404 但启动无错误时，按顺序排查：

1. **先看构建产物，再看代码**（颠倒顺序会浪费数小时）

   ```bash
   # 解压 spring-boot nested jar 看依赖 jar 时间戳
   jar tf target/{app}-admin.jar | grep BOOT-INF/lib/{app}-{biz}
   # 与目标模块的 target/*.jar 时间戳对比
   ls -la {app}-{biz}/target/*.jar
   # 与 .m2 缓存对比
   ls -la ~/.m2/repository/com/{org}/{app}-{biz}/*/*.jar
   ```

   时间戳错位 = 拉了旧依赖 = 立刻 `mvn clean package -pl ... -am`

2. **确认 class 真在 nested jar 内**

   ```bash
   # spring-boot nested jar 不能直接 grep，需要解压
   unzip -p target/{app}-admin.jar BOOT-INF/lib/{app}-{biz}-1.0.0-SNAPSHOT.jar > /tmp/dep.jar
   jar tf /tmp/dep.jar | grep YourNewController
   ```

   缺失 = 上一步 build 没把最新源码打进去

3. **dev profile 暴露 actuator/mappings 加速诊断**（建议长期开启）

   ```yaml
   management:
     endpoints:
       web:
         exposure:
           include: health,info,mappings,beans
   ```

   `curl localhost:8080/actuator/mappings | jq '...'` 直接看注册了哪些路径

4. **401 vs 404 区分**：未带 token → 401（security 拦截）；带 token → 404（DispatcherServlet 找不到 handler）。两者都 401 = 你的路径前缀写错；带 token 401、不带 401 = 同一情况；只有"带 token 404"才是 mapping 真没注册

---

## Review Checklist

- [ ] 所有第三方版本是否集中定义？
- [ ] 子模块是否避免对受管依赖显式声明版本？
- [ ] 插件版本是否集中？
- [ ] 模块顺序是否遵循架构分层？
- [ ] 任何例外是否有过期时间记录？

---

## Gradle Mapping (Cross-Project Reuse)

If the project is Gradle-based, apply the same principles with:

- central version catalog (`libs.versions.toml`)
- convention plugins for shared build logic
- module build scripts without hardcoded versions

Principle stays the same: **centralize versions, decentralize usage**.
