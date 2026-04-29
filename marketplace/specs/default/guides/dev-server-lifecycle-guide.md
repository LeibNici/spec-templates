# 开发服生命周期契约（Dev Server Lifecycle）

> **铁律**：前后端启动、停止、重启、健康检查必须走此 SOP；违反任一条视为"未启动"。

---

## 1. 工具路径（锁定绝对路径，禁用系统 PATH）

| 工具 | 推荐路径 |
|---|---|
| Java 17 (Corretto) | `~/tools/amazon-corretto-17.jdk/Contents/Home/bin/java` |
| Maven | `/opt/homebrew/bin/mvn`（macOS arm64）或 `$(which mvn)` |
| MySQL CLI | `~/tools/mysql-8.0.40-macos14-arm64/bin/mysql` |
| npm | `$(which npm)`（通过 nvm 管理，不锁版本） |

> 实际路径按本机环境调整；目的是避免依赖系统 PATH 导致版本错配。

**禁用**：系统自带 `java`（版本可能不是 17）、版本不可控的 brew alias。

---

## 2. 端口与日志

| 服务 | 端口 | 日志输出 |
|---|---|---|
| Admin Backend | 8080 | `/tmp/admin-boot.log` |
| Frontend Dev (vite) | 3000 | `/tmp/frontend-dev.log` |

前端 `vite.config.ts` 配置把 `/api/**` 代理到后端 `:8080`，curl 既可打 `:3000`（经代理）也可直打 `:8080`（绕代理测后端）。

---

## 3. 启动 SOP

### 3.1 后端 Admin

```bash
# Step 1：杀旧进程（强制，禁止跳过）
lsof -ti:8080 | xargs -r kill -9

# Step 2：mvn clean package（禁用 spring-boot:run）
export JAVA_HOME=~/tools/amazon-corretto-17.jdk/Contents/Home
/opt/homebrew/bin/mvn -q -f /path/to/{app}-backend/pom.xml \
  -pl {app}-admin -am clean package -DskipTests

# Step 3：java -jar 启动（run_in_background=true，禁加 & / nohup）
$JAVA_HOME/bin/java -Dspring.profiles.active=dev \
  -jar /path/to/{app}-backend/{app}-admin/target/{app}-backend.jar \
  > /tmp/admin-boot.log 2>&1
# ↑ 在 Bash 工具调用时设 run_in_background: true
```

**禁止**：

- ❌ `spring-boot:run`（会从 `~/.m2` 加载旧 jar，不是 target/ 下最新产物）
- ❌ `cd {app}-admin && mvn ...`（用 `-f pom路径` 代替）
- ❌ `nohup ... &` 或命令末尾加 `&`（双重后台化会丢失 pid，AI agent 背景任务无法管理）
- ❌ 跳过 Step 1 直接启动（8080 残留 pid 会导致端口占用）

### 3.2 前端 Dev Server

```bash
# Step 1：杀旧进程
lsof -ti:3000 | xargs -r kill -9
lsof -ti:5173 | xargs -r kill -9   # vite 默认端口兜底

# Step 2：npm dev（用 --prefix，禁用 cd &&）
npm --prefix /path/to/{app}-frontend run dev > /tmp/frontend-dev.log 2>&1
# ↑ run_in_background: true
```

**禁止**：

- ❌ `cd {app}-frontend && npm run dev`（用 `--prefix` 代替）
- ❌ 任何形式的 `&` 或 `nohup`

---

## 4. 健康检查（强制等待就绪）

### 4.1 后端 — 端点级探活（首选，改完代码刚重启时用）

```bash
# 探一个真实接口，401/403/200/400 任一返回即视为就绪
# - 401 = SecurityFilterChain + DispatcherServlet 都加载完
# - 200/400 = 业务逻辑也通了
# - 000 / 连接拒绝 = 服务未起（curl -m 2 快速失败，不阻塞）
until curl -s -m 2 -o /dev/null -w "%{http_code}\n" \
        -X POST http://127.0.0.1:8080/api/{your/endpoint} \
        2>/dev/null | grep -E '^(200|400|401|403)$' >/dev/null; do
  sleep 3
done
echo "ready"
```

**为什么端点级优于 grep 日志**：

1. 同时验证两件事 — Spring 启完 + **新接口路由注册成功**（grep `Started` 只能验证前者）
2. 拼写错的 `@PostMapping`、忘加包扫描会立刻 404 暴露，不会让你以为"启动成功"
3. 改完代码 → 重打 jar → 重启 → 探目标接口 = 一条链路，<10s 收敛

> **强烈推荐**：探**刚改过**的接口而非通用 `/api/health`。改 controller 不重启 / repackage 漏依赖 jar 的事故全靠这一步发现。

### 4.2 后端 — 日志级（兜底，纯起停时用）

```bash
# 没改代码、只是重启时用日志关键字即可
until grep -q "Started {AppName}Application" /tmp/admin-boot.log 2>/dev/null \
   || grep -qE "APPLICATION FAILED|Error starting" /tmp/admin-boot.log 2>/dev/null; do
  sleep 2
done
grep -E "Started|port 8080" /tmp/admin-boot.log | tail -3
```

### 4.3 前端

```bash
until grep -qE "ready in|Local:" /tmp/frontend-dev.log 2>/dev/null; do sleep 2; done
```

**禁止**：

- ❌ 固定 `sleep 30`（项目启动时间不固定，冷启有时 ~10s，有时 ~30s）
- ❌ 等 60s 后再做检查（等就绪是确定性条件，不是时间问题，浪费 cache + 延迟）
- ❌ `sleep 2 && curl ...`（少打一次循环就可能踩到"路由还没注册完"窗口）

---

## 5. 停止 SOP

```bash
lsof -ti:8080 | xargs -r kill -9  # admin
lsof -ti:3000 | xargs -r kill -9  # frontend
```

---

## 6. 登录与接口自测

### 6.1 登录密码加密（按项目实际情况）

**重要**：若项目登录走 AES/RSA 加密传输（前端加密 → 后端解密），AI 在终端无法在没有密钥的情况下加密，必须**预捕获**密文或由用户从浏览器 DevTools 提供。

| 途径 | 适用 | 做法 |
|---|---|---|
| 前端登录 | 浏览器/Playwright | 直接走 UI |
| curl 登录 | 终端自测 | 复用预捕获的加密 payload |
| 开发者直连 | 不推荐 | DB 直接改 `sys_user.password`（BCrypt） |

> dev profile 下 clientId/key 固定 → 同账号同明文密文恒定。生产环境密钥不同，密文不可跨环境复用。

### 6.2 带 token curl

```bash
TOKEN=$(curl -sS -X POST http://localhost:8080/api/auth/login \
  -H "Content-Type: application/json" \
  --data-raw '{"username":"<user>","password":"<encrypted-payload>"}' \
  | python3 -c "import sys,json;print(json.load(sys.stdin)['data']['token'])")

curl -sS http://localhost:8080/api/admin/{your/endpoint} \
  -H "Authorization: Bearer $TOKEN"
```

### 6.3 500 响应的调试路径

后端全局异常常把 403/404/业务异常统一包 500，debug 时**必须**看日志而非仅看 HTTP code：

```bash
grep -E "ERROR.*GlobalExceptionHandler|AccessDeniedException|Caused by:" \
     /tmp/admin-boot.log | tail -20
```

常见掩盖场景：

- `Access Denied` → 权限码对不上
- `Field 'id' doesn't have a default value` → MP 主键占位被击穿（前端 form `id: 0` / `id: ''` 触发）
- 解密失败 → 登录密码未加密

---

## 7. Flyway 与数据库连接

- `application-dev.yml` 启用的 URL 决定连哪个库；启动日志会打印实际 URL：

  ```
  Database: jdbc:mysql://<host>:3306/<db> (MySQL 8.0)
  ```

- 新 DDL 走 `V{N}__{domain}_{desc}.sql`，启动时 Flyway 自动 migrate；**禁止**手改业务表或修改已部署的 V 文件
- 启动后验证字段：

  ```bash
  ~/tools/mysql-8.0.40-macos14-arm64/bin/mysql -h <host> -uroot -proot -D <db> \
    -e "SHOW COLUMNS FROM <table>;"
  ```

---

## 8. Quick Checklist（每次启动前自查）

- [ ] 已 `lsof -ti:<port> | xargs -r kill -9` 清端口
- [ ] Maven 用 `-f pom路径` 而非 `cd xxx &&`
- [ ] `run_in_background: true`，命令中**没有** `&` 或 `nohup`
- [ ] 启动日志重定向到 `/tmp/admin-boot.log` 或 `/tmp/frontend-dev.log`
- [ ] 启动后用 §4.1 端点级探活（改过 controller）或 §4.2 日志级（纯起停）轮询，不盲 sleep
- [ ] curl 返回 500 先 grep 后端日志，不先改代码
- [ ] 连接的 DB URL 与预期一致（看启动日志）

---

## 9. 改完后端代码 → 重启 SOP（端到端 <30s）

```bash
# 1. 重打 jar（必须 -pl ... -am；省 -am 会从 .m2 拉旧依赖 jar 静默 404）
JAVA_HOME=~/tools/amazon-corretto-17.jdk/Contents/Home \
/opt/homebrew/bin/mvn -f /path/to/{app}-backend/pom.xml \
  -pl {app}-admin -am clean package -DskipTests 2>&1 | tail -8
# ↑ 期望 BUILD SUCCESS；出错时 | tail -30 看完整 trace

# 2. 杀旧（同一条 Bash 命令，确保串行）
lsof -ti:8080 | xargs -r kill -9; sleep 2

# 3. 后台启动（run_in_background: true）
~/tools/amazon-corretto-17.jdk/Contents/Home/bin/java \
  -jar /path/to/{app}-backend/{app}-admin/target/{app}-backend.jar \
  > /tmp/admin-boot.log 2>&1

# 4. 端点级探活（探刚改的接口 — 同时验证服务+路由）
until curl -s -m 2 -o /dev/null -w "%{http_code}\n" \
        -X POST http://127.0.0.1:8080/api/<刚改的接口> \
        2>/dev/null | grep -E '^(200|400|401|403)$' >/dev/null; do
  sleep 3
done; echo "ready"
```

**关键原则**：

- 改完后端**必探目标接口**，404 立刻暴露 controller 路由没注册（@PostMapping 拼写、Component 扫描遗漏、包路径错位）
- 401 = JWT 过滤器装好且路由匹配，**不需要**真登录就能确认就绪
- 不要用 sleep 等 60s 后回来——这是有确定性条件的轮询，应该原地 `until ... do sleep 3`
- 整套 4 步耗时 ≤ 30s（含编译 ~7s、启动 ~15s、探活 ~3s × 1~2 轮）

---

## 触发关键词

启动、`run_in_background`、`lsof`、`nohup`、`spring-boot:run`、`mvn -f`、`npm --prefix`、`/tmp/admin-boot.log`、`/tmp/frontend-dev.log`、Flyway 迁移确认、`Access Denied`、端口占用、dev profile
