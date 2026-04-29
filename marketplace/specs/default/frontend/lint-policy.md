# Frontend Lint Policy

> 字面层规范的**意图清单**——告诉 AI / 人 ESLint 该开哪些规则、为什么。
> 本文件不锁定版本号；克隆模板后让 AI 现搜最新版本配 `.eslintrc.cjs`。

---

## 推荐技术栈

| 工具 | 角色 |
|---|---|
| ESLint v9+ (flat config) | 代码规则检查 |
| `eslint-plugin-vue`（Vue 3 preset） | Vue 模板/SFC 规则 |
| `@typescript-eslint/parser` + `eslint-plugin` | TS 类型相关规则 |
| `vue-eslint-parser` | 解析 `.vue` 文件 |
| Prettier + `eslint-config-prettier` | 格式化（与 ESLint 关闭冲突项） |

> Prettier 负责**格式**（引号、分号、行宽、缩进）；ESLint 负责**逻辑**（未用变量、错误模式）。两者分工不重叠。

---

## 必开规则（按优先级）

### 1. JS / TS 通用

| 规则 | 取值 | 理由 |
|---|---|---|
| `prefer-const` | error | 变量未重新赋值就用 const，让"是否会变"在视觉上一目了然 |
| `eqeqeq` | `['error', 'smart']` | 强制 `===`；smart 模式放过 `null == undefined` 这类无害比较 |
| `no-eval` | error | 安全 + 性能 |
| `no-implied-eval` | error | `setTimeout('code', ...)` 字符串求值同等危险 |
| `no-var` | error | `var` 在 ES6 后无理由保留 |
| `no-unused-vars` | error | 死代码警告 |
| `no-console` | `production: error / dev: off` | dev 允许调试，prod 禁打日志（用业务日志层） |
| `no-debugger` | `production: error / dev: off` | 同上 |

### 2. TypeScript 专项

| 规则 | 取值 | 理由 |
|---|---|---|
| `@typescript-eslint/no-explicit-any` | warn | 不强制（兜底场景需要），但持续提醒消除 |
| `@typescript-eslint/no-unused-vars` | error | 替代原生 `no-unused-vars`（更准） |
| `@typescript-eslint/consistent-type-imports` | error | `import type { X }`，避免 runtime 误引 |
| `@typescript-eslint/no-non-null-assertion` | warn | `foo!` 兜底允许，但提醒优先用类型收窄 |

### 3. Vue 3 专项（关键）

| 规则 | 取值 | 理由 |
|---|---|---|
| `vue/component-name-in-template-casing` | `['error', 'PascalCase', { registeredComponentsOnly: true }]` | 模板中 `<UserCard />` 与 import 一致 |
| `vue/attribute-hyphenation` | `['error', 'always']` | 属性 kebab-case，对齐 Vue 官方 + Element Plus 文档 |
| `vue/this-in-template` | `['error', 'never']` | `<script setup>` 不应在模板出现 `this.` |
| `vue/no-mutating-props` | error | 子改父数据是单向数据流反模式 |
| `vue/no-use-v-if-with-v-for` | error | v-for + v-if 同节点：v-for 优先级高，每次都遍历再过滤，性能差 |
| `vue/require-prop-types` | warn | TS 已强制类型，作为兜底（JS 项目时升级为 error） |
| `vue/multi-word-component-names` | warn | 单词组件名（`Item`）易与 HTML 元素冲突 |
| `vue/no-v-html` | warn | `v-html` 未脱敏会 XSS；用到时必须配 DOMPurify |

### 4. 复杂度阈值（与代码硬性上限呼应）

| 规则 | 取值 | 对应 spec |
|---|---|---|
| `complexity` | `['warn', 15]` | 圈复杂度（quality-guidelines.md） |
| `max-lines-per-function` | `['warn', { max: 80, skipBlankLines: true, skipComments: true }]` | 函数 ≤ 80 行 |
| `max-lines` | `['warn', { max: 500, skipBlankLines: true }]` | 文件 ≤ 500 行 |
| `max-depth` | `['warn', 4]` | 嵌套 ≤ 4 层 |
| `max-params` | `['warn', 5]` | 位置参数 ≤ 5 |

> 全部用 `warn` 而非 `error` —— 让旧代码可过 lint，新代码自觉收敛；CI 用 `--max-warnings=0` 控制总量增长。

### 5. Prettier 推荐配置

```json
{
  "semi": false,
  "singleQuote": true,
  "trailingComma": "all",
  "printWidth": 100,
  "endOfLine": "lf",
  "vueIndentScriptAndStyle": false
}
```

| 项 | 选择理由 |
|---|---|
| `semi: false` | 行尾不加分号（Vue 社区主流；与 ASI 一致） |
| `singleQuote: true` | 单引号（与 Vue/Vite 模板示例一致） |
| `trailingComma: 'all'` | 末尾逗号让 git diff 更干净（多加一个参数只动一行） |
| `printWidth: 100` | 80 太挤，120 太宽，100 是 2026 主流 |

---

## 不必开的规则（避免噪声）

| 规则 | 为什么不开 |
|---|---|
| `camelcase` | TS 已有命名约束；Vue prop kebab↔camel 自动转换会被这条误报 |
| `vue/max-attributes-per-line` | Prettier 已管行宽 |
| `import/order` | 必要时再开；新项目初期会刷屏告警 |
| `no-magic-numbers` | 太多正常数字（0/1/-1/200/300ms）会被误报；spec 已有"魔法数字提取常量"的人工 review 项 |

---

## 推荐 `.eslintrc.cjs`（生成时参考，非锁定）

> 克隆模板后，告诉 AI："按 `lint-policy.md` 给我写一份 ESLint flat config + Prettier 配置，用最新稳定版"。AI 通过 context7 拉到最新 plugin 版本号即可。

骨架（仅示意，不直接复用）：

```js
// eslint.config.js
import vue from 'eslint-plugin-vue'
import tseslint from 'typescript-eslint'
import vueParser from 'vue-eslint-parser'
import prettier from 'eslint-config-prettier'

export default [
  ...vue.configs['flat/recommended'],
  ...tseslint.configs.recommended,
  prettier, // 必须放最后，关闭与 Prettier 冲突的格式化规则
  {
    files: ['**/*.{ts,vue}'],
    languageOptions: {
      parser: vueParser,
      parserOptions: { parser: tseslint.parser, sourceType: 'module' },
    },
    rules: {
      // 上文 §1~§4 列的规则
    },
  },
]
```

---

## 落地清单（克隆模板后）

- [ ] `npm i -D eslint @vue/eslint-config-typescript eslint-plugin-vue typescript-eslint vue-eslint-parser prettier eslint-config-prettier`
- [ ] 让 AI 按本 spec 生成 `eslint.config.js` + `.prettierrc` + `.editorconfig`
- [ ] `package.json` 加 `"lint": "eslint . --max-warnings=0"`
- [ ] IDE 装 ESLint 插件（IntelliJ 自带）
- [ ] 配 lint-staged + husky 让 commit 时自动 lint 改动文件
- [ ] CI 流程加 `npm run lint` step

---

## 演化策略

- **新规则上线**：先 `warn` 一周观察，无误报再升 `error`
- **plugin 升大版本**：先 `npm outdated` 看；升级前在分支跑全量 lint，对比新增 warning 量
- **规则争议**：在 PR 描述里写下"为什么这条要关/开"，未来回溯有据
