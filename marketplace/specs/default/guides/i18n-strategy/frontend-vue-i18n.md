# Frontend (vue-i18n)

## 三、前端实现（vue-i18n）

### 3.1 包

```
vue-i18n (v10+)
@intlify/unplugin-vue-i18n  ← Vite 插件，编译期优化
```

### 3.2 文件结构

```
src/locales/
├── index.ts             ← 创建 i18n 实例，导出 i18n
├── zh-CN/
│   ├── index.ts         ← 聚合 + 整合 Element Plus locale
│   ├── common.ts        ← 通用：按钮、操作、状态、确认、表单
│   ├── error.ts         ← 错误消息（HTTP / 业务 code → msg）
│   └── pages/
│       ├── order.ts
│       ├── customer.ts
│       └── ...
└── en-US/               ← 同结构镜像
    ├── index.ts
    ├── common.ts
    ├── error.ts
    └── pages/...
```

### 3.3 Key 规范（嵌套式）

```ts
// src/locales/zh-CN/pages/order.ts
export default {
  list: {
    title: '订单列表',
    btnCreate: '新建订单',
    colCustomer: '客户',
    colAmount: '金额',
    msgCreateSuccess: '订单创建成功',
  },
  detail: {
    title: '订单详情 - {orderNo}',  // 占位符
    btnEdit: '编辑',
  },
}
```

```vue
<!-- 模板 -->
<el-button>{{ $t('order.list.btnCreate') }}</el-button>
<h1>{{ $t('order.detail.title', { orderNo }) }}</h1>
```

```ts
// composable / TS 代码
const { t } = useI18n()
ElMessage.success(t('order.list.msgCreateSuccess'))
```

### 3.4 Key 命名约定

| 类型 | 前缀 | 示例 |
|---|---|---|
| 按钮 | `btn` | `order.list.btnCreate` |
| 列名 / 字段标签 | `col` 或 `lbl` | `order.list.colCustomer` |
| 标题 | `title` | `order.list.title` |
| 占位符 | `placeholder` | `customer.list.placeholderSearch` |
| 提示消息 | `msg` | `order.list.msgCreateSuccess` |
| 确认对话框 | `confirm` | `common.confirmDelete` |

### 3.5 切换 locale + 持久化

```ts
// src/composables/useLocale.ts
import { useI18n } from 'vue-i18n'

const STORAGE_KEY = 'app:locale'

export function useLocale() {
  const { locale } = useI18n()

  function setLocale(value: 'zh-CN' | 'en-US') {
    locale.value = value
    localStorage.setItem(STORAGE_KEY, value)
    // 通知 dayjs / Element Plus 切换（见 §3.7）
    syncDayjs(value)
  }

  return { locale, setLocale }
}
```

### 3.6 Element Plus locale 同步

```vue
<!-- App.vue -->
<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElConfigProvider } from 'element-plus'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'
import en from 'element-plus/dist/locale/en.mjs'

const { locale } = useI18n()
const elementLocale = computed(() => (locale.value === 'zh-CN' ? zhCn : en))
</script>

<template>
  <el-config-provider :locale="elementLocale">
    <router-view />
  </el-config-provider>
</template>
```

### 3.7 dayjs locale 同步

```ts
// src/utils/dayjs.ts
import dayjs from 'dayjs'
import 'dayjs/locale/zh-cn'
import 'dayjs/locale/en'

export function syncDayjs(locale: 'zh-CN' | 'en-US') {
  dayjs.locale(locale === 'zh-CN' ? 'zh-cn' : 'en')
}
```

### 3.8 缺失 key 兜底（防 `???key???` 露给用户）

```ts
// src/locales/index.ts
import { createI18n } from 'vue-i18n'

export const i18n = createI18n({
  legacy: false,
  locale: localStorage.getItem('app:locale') || 'zh-CN',
  fallbackLocale: 'zh-CN',
  missingWarn: import.meta.env.DEV,    // 开发时报警
  fallbackWarn: import.meta.env.DEV,
  silentTranslationWarn: import.meta.env.PROD,  // 生产静默
  messages: {
    'zh-CN': zhCN,
    'en-US': enUS,
  },
  missing: (locale, key) => {
    if (import.meta.env.DEV) console.warn(`[i18n] missing key: ${key} (${locale})`)
    return key  // 兜底：显示 key 本身，不是 `???`
  },
})
```
