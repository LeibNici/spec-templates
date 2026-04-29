# Placeholder 字典 — 克隆模板后必读

> 本仓库是 SpringBoot+Vue 项目脚手架。`git clone` 给新项目后，先按本字典做一次全局替换，再开始开发。

---

## 占位符字典

| 占位符 | 含义 | 示例值 | 出现位置 |
|---|---|---|---|
| `{Project Name}` | 项目展示名（中文/英文） | `信川数字化系统` / `Acme Inventory` | `CLAUDE.md` 第 1 行 |
| `{app}` / `{app-name}` | 应用代号（小写，连字符） | `xinchuan` / `acme-inv` | 后端模块前缀、前端目录、jar 名 |
| `{biz}` | 业务模块代号 | `order` / `inventory` / `mes` | Maven 子模块、Java 包、前端 `views/{biz}/` |
| `{org}` | 组织包名（点分） | `com.xinchuan` / `com.acme` | Java `package com.{org}.{biz}.*` |
| `{path-to-backend}` | 后端项目绝对路径 | `/Users/me/IdeaProjects/acme/acme-backend` | `mvn -f`、启动脚本 |
| `{AppName}Application` | Spring Boot 启动类名 | `XinchuanApplication` | `dev-server-lifecycle-guide.md` 日志 grep |

---

## 一键替换（Bash）

```bash
# 在新项目根目录执行（已 clone 本模板）
PROJECT_NAME="信川数字化系统"
APP="xinchuan"
BIZ_DEFAULT="order"           # 首个业务模块名（其他模块按需新增）
ORG="com.xinchuan"
APP_NAME_CLASS="Xinchuan"     # 启动类前缀（PascalCase）

# 仅替换 .trellis/spec/ + CLAUDE.md
find .trellis/spec CLAUDE.md -type f -name "*.md" | while read f; do
  sed -i '' \
    -e "s|{Project Name}|${PROJECT_NAME}|g" \
    -e "s|{app-name}|${APP}|g" \
    -e "s|{app}|${APP}|g" \
    -e "s|{biz}|${BIZ_DEFAULT}|g" \
    -e "s|{org}|${ORG}|g" \
    -e "s|{AppName}|${APP_NAME_CLASS}|g" \
    "$f"
done

# `{path-to-backend}` 留着不替换（按本机绝对路径，由开发者本地运行时填）
```

> macOS 用 `sed -i ''`，Linux 用 `sed -i`（无引号）。

---

## 替换前自查

- [ ] 已 fork / clone 到新项目目录
- [ ] 已删除 `.trellis/tasks/` 下原项目残留任务（保留 `00-bootstrap-guidelines/` 模板可作首任务）
- [ ] 已检查 `.git/` 是否为新仓库（`rm -rf .git && git init` 如需独立 history）
- [ ] 已确认 `{path-to-backend}` 占位符仍保留（这是本机路径，不是项目内容）

---

## 替换后验证

```bash
# 应输出 0 行（除 PLACEHOLDERS.md 自己）
grep -rn -E '\{(app|biz|org|Project Name|AppName)' .trellis/spec CLAUDE.md \
  | grep -v "PLACEHOLDERS.md"
```

输出非空 → 还有占位符没替换，按行号补改。

`{path-to-backend}` 是**主动保留**的占位符（本机路径），不计入此校验。

---

## 不要手改的占位符

下面这些**保留**为占位符，由开发者**当场**填写本机路径，不要在模板里硬编码：

- `{path-to-backend}` — 后端绝对路径（不同开发者机器路径不同）
- `~/tools/amazon-corretto-17.jdk/...` — Java 路径（按本机实际安装位置）
- `192.168.x.x` / `<host>` — DB / Redis 主机（按部署环境）
- `<encrypted-payload>` — 登录密文（按 dev profile 实际加密结果捕获）

这些在 `dev-server-lifecycle-guide.md` 中以注释标注。
