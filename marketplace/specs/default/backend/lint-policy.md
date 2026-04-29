# Backend Lint Policy

> Java 字面层规范的**意图清单**——告诉 AI / 人 静态检查工具该开哪些规则、为什么。
> 与 frontend 的 lint-policy 对称。

---

## 推荐技术栈

| 工具 | 角色 | 配置位置 |
|---|---|---|
| **Checkstyle** | 编码风格、命名、行长等 | `checkstyle.xml`（项目根） |
| **SpotBugs** | 字节码层面 bug 模式（NPE、同步、序列化等） | `spotbugs.xml` 或仅 Maven plugin 配置 |
| **PMD** | 代码气味、复杂度、未用代码 | `pmd-ruleset.xml` |
| **SonarLint**（IDE 插件） | 实时反馈，与 SonarQube 规则一致 | IDEA 插件，无需配置文件 |

> 工具分工：Checkstyle = 字符（缩进、import 顺序）；PMD = 模式（圈复杂度、空 catch）；SpotBugs = 字节码 bug。三者搭配覆盖 Java 字面层。

---

## 推荐 baseline

### A. 起步路径（推荐）

直接用 **Sun Checks**（Checkstyle 自带）+ **Sonar Java way**（PMD 等同集）作为起步规则集。这两个是社区共识，覆盖率高、误报少。

- Checkstyle: 基于 `sun_checks.xml` 微调
- PMD: 基于 `category/java/bestpractices.xml` + `category/java/codestyle.xml`
- SpotBugs: 默认 ruleset 即可

### B. 高阶路径（有专人维护）

引入 **Alibaba P3C**（`p3c-pmd`）—— 阿里 Java 开发手册落地版本，更激进，包含国内常见踩坑模式（线程池、日期类、SimpleDateFormat 线程安全等）。

> 选 A 还是 B：刚起步选 A；团队 ≥ 5 人 + 有 code champion 选 B。

---

## 必开规则（与代码硬性上限呼应）

### 1. 复杂度阈值（呼应 quality-guidelines.md）

| 规则 (PMD/Checkstyle) | 取值 | 对应 spec |
|---|---|---|
| `MethodLength` (Checkstyle) | 80 | 函数 ≤ 80 行 |
| `FileLength` (Checkstyle) | 500 | 文件 ≤ 500 行 |
| `CyclomaticComplexity` (PMD) | 15 | 圈复杂度 ≤ 15 |
| `NPathComplexity` (Checkstyle) | 200 | NPath（与 cyclomatic 互补） |
| `ParameterNumber` (Checkstyle) | 5 | 位置参数 ≤ 5 |
| `MaxNestingLevel` (Checkstyle) | 4 | 嵌套 ≤ 4 |

### 2. 命名规范（与 naming-conventions.md 对齐）

| 规则 | 取值 |
|---|---|
| `TypeName` | `*Controller`/`*Service`/`*ServiceImpl`/`*Mapper`/`*Enum`/`*Constants` 后缀正则 |
| `ConstantName` | `^[A-Z][A-Z0-9]*(_[A-Z0-9]+)*$`（UPPER_SNAKE_CASE） |
| `MemberName` / `LocalVariableName` | `^[a-z][a-zA-Z0-9]*$`（lowerCamelCase） |
| `PackageName` | `^[a-z]+(\.[a-z][a-z0-9]*)*$`（全小写） |

### 3. 异常处理铁律（呼应 error-handling.md / code-smell-prevention/_index.md）

| 规则 | 取值 | 理由 |
|---|---|---|
| `EmptyCatchBlock` (Checkstyle) | error，禁止 `catch{}` | 至少 `log.warn` 或 rethrow |
| `EmptyControlStatement` (Checkstyle) | error | 空 if/while 几乎都是漏写 |
| `AvoidCatchingGenericException` (PMD) | warn | `catch(Exception)` 兜底允许，但提醒优先抓具体类型 |
| `EmptyStatementBlock` (PMD) | error | 空 method body |

### 4. 集合 / Optional / 流（防真实 bug）

| 规则 | 取值 |
|---|---|
| `AvoidUsingHardCodedIP` (PMD) | warn |
| `UseUtilityClass` (PMD) | warn — 全 static 方法的类必须 final + 私有构造 |
| `LooseCoupling` (PMD) | error — 用 `List<T>`/`Map<K,V>` 而非 `ArrayList<T>`/`HashMap<K,V>` 作字段类型 |
| `AvoidThrowingNullPointerException` (PMD) | error |
| `AvoidPrintStackTrace` (PMD) | error — 必须走 logger |
| `SystemPrintln` (PMD) | error — 禁 `System.out.println` |

### 5. 并发 / 资源（SpotBugs 主战场）

SpotBugs 默认 ruleset 包含：

- `RV_RETURN_VALUE_IGNORED_BAD_PRACTICE` — 忽略返回值（如 `String.replace` 不接结果）
- `NP_NULL_PARAM_DEREF` — 可能 NPE 的参数解引用
- `IS2_INCONSISTENT_SYNC` — 不一致的同步访问
- `DM_DEFAULT_ENCODING` — 用了 platform-dependent 编码（必须显式 `UTF-8`）

**全部启用**，无需挑选。

### 6. import 顺序（Checkstyle）

```
java.* / javax.*
（空行）
其他第三方库
（空行）
com.{org}.* （本项目）
```

规则：`CustomImportOrder` + `RedundantImport` + `UnusedImports`。

---

## 项目已有的 checkstyle.xml

**位置**：项目根 `checkstyle.xml`（与本 spec 配套，已就位）。

**起点**：基于 Checkstyle 自带 `sun_checks.xml`，针对 Spring Boot 3 + Lombok + 本项目 spec 演化而来。

**已对齐 spec 的关键值**：

| 规则 | 阈值 | 对应 spec |
|---|---|---|
| `MethodLength` | 80 | 函数 ≤ 80 行 |
| `ParameterNumber` | 5 | 位置参数 ≤ 5 |
| `FileLength` | 500 | 文件 ≤ 500 行 |
| `CyclomaticComplexity` | 15 | 圈复杂度 ≤ 15 |
| `BooleanExpressionComplexity` | 5 | 布尔条件分支限制 |
| `LineLength` | 150 | 适配 MyBatis 注解 / SQL |
| `MagicNumber` 白名单 | -1/0/1/2/8/10/16/100/200/500 | spec "0/1/-1 例外" |

**已禁用的规则**（与项目实际不符）：

- `DesignForExtension` — Spring `@Service` / `@Controller` 方法不要求 final
- `FinalParameters` — Lombok `@AllArgsConstructor` 生成的构造器有冲突，强制 final 治标不治本

**Javadoc 全系列保留**（与 quality-guidelines.md "注释策略"对齐）：
- `JavadocPackage` / `JavadocType` / `JavadocMethod` / `MissingJavadocMethod` 全开
- `JavadocVariable` 仅 protected 及以上强制
- `MissingJavadocMethod` 仅 public 强制
- private 方法和实现类内部细节不强制注释

---

## 不必开的规则（避免噪声）

| 规则 | 为什么不开 |
|---|---|
| `FinalLocalVariable` (Checkstyle) | 强制所有局部变量 final，与 Lombok / Stream 风格冲突 |
| `RegexpSingleline` 强制行长 ≤ 100 | 已用 `LineLength` max=150 |

---

## Maven 集成（pom.xml 片段）

放在父 pom 的 `<pluginManagement>`：

```xml
<plugin>
  <groupId>org.apache.maven.plugins</groupId>
  <artifactId>maven-checkstyle-plugin</artifactId>
  <version>${checkstyle.plugin.version}</version>
  <configuration>
    <configLocation>checkstyle.xml</configLocation>
    <consoleOutput>true</consoleOutput>
    <failsOnError>false</failsOnError>  <!-- 起步阶段 false，团队稳定后改 true -->
    <linkXRef>false</linkXRef>
  </configuration>
</plugin>

<plugin>
  <groupId>com.github.spotbugs</groupId>
  <artifactId>spotbugs-maven-plugin</artifactId>
  <version>${spotbugs.plugin.version}</version>
</plugin>

<plugin>
  <groupId>org.apache.maven.plugins</groupId>
  <artifactId>maven-pmd-plugin</artifactId>
  <version>${pmd.plugin.version}</version>
  <configuration>
    <rulesets>
      <ruleset>category/java/bestpractices.xml</ruleset>
      <ruleset>category/java/codestyle.xml</ruleset>
      <ruleset>category/java/errorprone.xml</ruleset>
    </rulesets>
  </configuration>
</plugin>
```

具体版本号克隆时让 AI 现查最新稳定版。

---

## CI 集成

```bash
# 单步跑全部静态检查
mvn -B verify checkstyle:check spotbugs:check pmd:check
```

起步阶段：`failsOnError=false`，仅产报告。
团队稳定后：`failsOnError=true`，违规直接挂 CI。

---

## 落地清单（克隆模板后）

- [ ] 父 pom 加上面三个 plugin（管理在 `<pluginManagement>`）
- [ ] 让 AI 按本 spec 生成 `checkstyle.xml`（基于 sun_checks.xml 调整阈值）
- [ ] 让 AI 按本 spec 生成 `pmd-ruleset.xml`（picking bestpractices + codestyle + errorprone）
- [ ] IDEA 装 SonarLint / CheckStyle-IDEA / SpotBugs 三件套
- [ ] CI pipeline 加 `mvn verify` step

---

## 与 spec 的关系

本文件不替代任何架构 spec，**只覆盖字面层**：

| 范畴 | 谁管 |
|---|---|
| Controller 不能注入 Mapper | `quality-guidelines.md` + AI review |
| Service 单一职责 | `code-smell-prevention/02-srp.md` + AI review |
| 命名 PascalCase / camelCase | **本文件 + Checkstyle** |
| 圈复杂度上限 | **本文件 + PMD** + AI review 兜底 |
| 空 catch 块 | **本文件 + Checkstyle** + spec 双重 |
| 跨模块直连他人 Mapper | `code-smell-prevention/04-isolation.md` + AI review（PMD 无法识别业务模块边界） |

**90% 架构问题 PMD/Checkstyle 抓不到**，所以本文件仅作辅助防线，主力仍是 spec + AI agent。
