# 国际化（i18n）策略

> 跨层契约文件。覆盖前端 vue-i18n + 后端 Spring MessageSource + 业务字典 + 错误响应。
> 适用于本项目支持的 locale：**`zh-CN`（默认）+ `en-US`**（仅两套）。

---

## 一、决策汇总（一表看清）

| 决策项 | 本项目选择 | 理由 |
|---|---|---|
| 支持的 locale | `zh-CN`（默认）+ `en-US` | BCP 47 标准；不写裸 `zh`/`en` |
| 默认是否启用 i18n | **不启用**，按需开关（项目级决策） | 80% 中后台项目永不需要 |
| 业务字典 i18n | **默认不翻译**（dict_label 仅中文） | 运营难维护双语字典；扩展路径已留 |
| 错误响应翻译 | **后端 msg 已本地化**（主路径）+ 前端 code-based fallback（兜底） | 不维护双轨翻译；防 msg 缺失白屏 |
| 翻译 key 规范 | 嵌套式 `模块.页面.元素` | 与 yudao / 主流 Vue 项目一致 |

---

## 二、是否启用 i18n（决策树）

```
项目要不要开 i18n？
│
├─ 已知有英文/海外用户？
│   └─ ✅ 一开始就开（按本文 §3、§4 落地）
│
├─ 中文用户为主，但客户/PM 提过"将来要支持英文"？
│   └─ ⚠️ 默认不开，但**所有用户可见文案集中在 src/locales/zh-CN/**
│      （为将来扩展留路径，开关时间到了再补 en-US）
│
└─ 纯中文中后台，无国际化需求？
    └─ ❌ 不开，文案直接写在 template 里也可
        （但仍建议集中在 src/locales/zh-CN.ts，便于全局检索/替换）
```

**铁律**：**决定不开**也要把**用户可见文案**集中放置——别散落到 template 里。这样后来想开时迁移成本最低。

---

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

---

## 四、后端实现（Spring MessageSource）

### 4.1 资源文件结构

```
src/main/resources/
└── i18n/
    ├── messages.properties           ← 默认（zh_CN）
    ├── messages_zh_CN.properties
    └── messages_en_US.properties
```

### 4.2 application.yml

```yaml
spring:
  messages:
    basename: i18n/messages
    encoding: UTF-8
    fallback-to-system-locale: false
    default-locale: zh-CN
    cache-duration: PT1H  # 缓存 1h，dev 改为 PT0S
```

### 4.3 properties 内容

```properties
# messages_zh_CN.properties
user.notfound=用户 {0} 不存在
order.cannot.cancel=订单已发货，无法取消
validation.user.name.notblank=用户名不能为空
validation.user.email.format=邮箱格式不正确
common.success=操作成功
common.error.system=系统繁忙，请稍后再试
```

```properties
# messages_en_US.properties
user.notfound=User {0} not found
order.cannot.cancel=Order already shipped, cannot cancel
validation.user.name.notblank=Username cannot be blank
validation.user.email.format=Invalid email format
common.success=Success
common.error.system=System busy, please retry later
```

### 4.4 LocaleResolver 配置

```java
@Configuration
public class WebMvcConfig implements WebMvcConfigurer {

    @Bean
    public LocaleResolver localeResolver() {
        AcceptHeaderLocaleResolver resolver = new AcceptHeaderLocaleResolver();
        resolver.setSupportedLocales(List.of(Locale.SIMPLIFIED_CHINESE, Locale.US));
        resolver.setDefaultLocale(Locale.SIMPLIFIED_CHINESE);
        return resolver;
    }
}
```

### 4.5 业务异常携带 i18n key

```java
// BusinessException.java
@Getter
public class BusinessException extends RuntimeException {
    private final String code;       // i18n key 或错误码
    private final Object[] args;

    public BusinessException(String code, Object... args) {
        super(code);
        this.code = code;
        this.args = args;
    }
}

// 抛出
throw new BusinessException("user.notfound", userId);
```

### 4.6 GlobalExceptionHandler 翻译

```java
@RestControllerAdvice
@RequiredArgsConstructor
public class GlobalExceptionHandler {

    private final MessageSource messageSource;

    @ExceptionHandler(BusinessException.class)
    public R<?> handle(BusinessException e, Locale locale) {
        String msg = messageSource.getMessage(e.getCode(), e.getArgs(), e.getCode(), locale);
        return R.fail(e.getCode(), msg);
    }
}
```

### 4.7 Bean Validation 消息

```java
public class UserCreateDTO {
    @NotBlank(message = "{validation.user.name.notblank}")
    private String name;

    @Email(message = "{validation.user.email.format}")
    private String email;
}
```

需要在 application.yml 让 Hibernate Validator 用 Spring MessageSource：

```java
@Bean
public LocalValidatorFactoryBean validator(MessageSource messageSource) {
    LocalValidatorFactoryBean factory = new LocalValidatorFactoryBean();
    factory.setValidationMessageSource(messageSource);
    return factory;
}
```

---

## 五、跨层契约（铁律）

```
前端 store.locale ('zh-CN')
   │
   │ Axios 拦截器自动注入 Accept-Language
   ↓
HTTP Request
  Accept-Language: zh-CN
   │
   ↓
后端 AcceptHeaderLocaleResolver
   │  解析 Locale = SIMPLIFIED_CHINESE
   ↓
业务抛 BusinessException("user.notfound", userId)
   │
   ↓
GlobalExceptionHandler 翻译
   │  msg = messageSource.getMessage("user.notfound", [42], zh_CN)
   ↓
HTTP Response
  { code: "user.notfound", msg: "用户 42 不存在", data: null }
   │
   ↓
前端 axios 拦截器 → ElMessage.error(response.msg)
```

### Axios 拦截器（前端）

```ts
// src/api/request.ts
axios.interceptors.request.use((config) => {
  const locale = localStorage.getItem('app:locale') || 'zh-CN'
  config.headers['Accept-Language'] = locale
  return config
})
```

### 错误响应处理（前端）

```ts
// 主路径：信任后端 msg
ElMessage.error(response.msg)

// 兜底：msg 缺失时用 code 通过前端 i18n 渲染
function showError(response: { code: string; msg?: string }) {
  const { t } = useI18n()
  const msg = response.msg
    || t(`error.${response.code}`, response.code)  // 前端 i18n 兜底
    || t('common.error.system')                    // 通用兜底
  ElMessage.error(msg)
}
```

**前端 `error.ts` 只放兜底**（高频错误码 + 通用文案），**不重复维护**所有业务错误：

```ts
// src/locales/zh-CN/error.ts
export default {
  network: '网络异常，请检查网络连接',
  timeout: '请求超时',
  unauthorized: '登录已过期',
  forbidden: '没有权限',
  notFound: '资源不存在',
  serverError: '服务器异常',
}
```

---

## 六、业务字典 i18n（默认不开）

### 6.1 默认策略

`sys_dict_data.dict_label` 仅维护**中文**。前端切到英文时：
- 业务字典值（如客户类型 `VIP` → `大客户`）保持中文显示
- 用户可在 dict 管理界面同时维护"英文 label"作为附属字段（可选）

**理由**：
- 字典是运营维护资产，强制双语会显著增加运营负担
- 多数业务场景下，dict_label 中文显示对英文用户也能理解（特别是行业术语）
- 真要英文版 → 启用 §6.2 扩展方案

### 6.2 扩展方案（按需启用）

新建关联表 `sys_dict_data_i18n`：

```sql
CREATE TABLE IF NOT EXISTS `sys_dict_data_i18n` (
  `id`           BIGINT      NOT NULL                COMMENT '主键ID（雪花）',
  `dict_data_id` BIGINT      NOT NULL                COMMENT '关联 sys_dict_data.id',
  `locale`       VARCHAR(10) NOT NULL                COMMENT 'BCP 47，如 zh-CN / en-US',
  `dict_label`   VARCHAR(64) NOT NULL                COMMENT '本地化标签',
  `create_time`  DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `update_time`  DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_dict_data_locale` (`dict_data_id`, `locale`),
  KEY `idx_dict_data_id` (`dict_data_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='字典数据多语言表';
```

**dict API 返回时按 Accept-Language 选 label**：

```java
List<DictDataVO> getDictData(String dictType, Locale locale) {
    List<SysDictData> dataList = dictDataMapper.selectByType(dictType);
    Map<Long, String> i18nLabels = dataList.isEmpty()
        ? Map.of()
        : i18nMapper.selectLabels(
            dataList.stream().map(SysDictData::getId).toList(),
            locale.toLanguageTag()
        );

    return dataList.stream().map(d -> DictDataVO.builder()
        .code(d.getDictCode())
        // 优先 i18n label，无 fallback 中文 dict_label
        .label(i18nLabels.getOrDefault(d.getId(), d.getDictLabel()))
        .build()).toList();
}
```

### 6.3 何时该启用扩展方案

满足任一项：
- ≥30% 用户使用英文界面
- 业务方明确要求字典英文化（如外贸订单系统）
- 已有外文用户反馈"看不懂中文标签"

否则**不启用**——保持默认。

---

## 七、Forbidden（不该 i18n 的内容）

| 类型 | 原因 |
|---|---|
| 订单号 / 编码 / 业务 ID | 是数据，不是文案 |
| 用户输入内容（备注、地址、回复） | 谁输入显示谁的语言 |
| 业务表中的文本字段（产品名、客户名） | 数据本身，需要多语言时单独建表 |
| 日志 / Javadoc / commit message | 给开发者看的，统一英文（或统一中文）即可，不要双轨 |
| 系统枚举 code（`WAITING_PRODUCTION`） | 是 enum 值，前端 `src/constants/` 映射 label |
| 后端 `R<T>.code` 字段 | 是错误码标识，前端 i18n 渲染对应 msg |

---

## 八、落地清单（克隆模板后启用 i18n）

- [ ] 决定本项目是否启用 i18n（按 §2 决策树）
- [ ] **不启用**：把用户可见文案集中到 `src/locales/zh-CN/`，便于将来扩展
- [ ] **启用**：执行下面所有步骤

### 前端

- [ ] `npm i vue-i18n@10 @intlify/unplugin-vue-i18n`
- [ ] 创建 `src/locales/{zh-CN,en-US}/` 目录结构
- [ ] `main.ts` 注册 i18n 实例
- [ ] Axios 拦截器注入 `Accept-Language` header
- [ ] `App.vue` 包 `<el-config-provider :locale="...">`
- [ ] dayjs locale 同步函数
- [ ] localStorage 持久化用户选择

### 后端

- [ ] `src/main/resources/i18n/messages_{zh_CN,en_US}.properties` 三件套
- [ ] `application.yml` 加 `spring.messages.*`
- [ ] `WebMvcConfig` 注册 `AcceptHeaderLocaleResolver`
- [ ] `BusinessException` 改为携带 `code + args` 模式
- [ ] `GlobalExceptionHandler` 用 `MessageSource.getMessage(code, args, locale)`
- [ ] `LocalValidatorFactoryBean` 让 Bean Validation 走 Spring MessageSource

### 验证

- [ ] 切换 locale 整个 UI（含 Element Plus 控件）正确响应
- [ ] 后端业务异常返回的 `msg` 已本地化
- [ ] 缺失 key 不会显示 `???key???`（前端兜底 + 后端 fallback）
- [ ] dayjs 日期显示正确
- [ ] 业务字典默认中文显示（除非启用 §6.2）

---

## 九、决策记录（防后续误改）

- ✅ 仅 `zh-CN` + `en-US`，未来要加 `ja-JP` / `ko-KR` 通过新增 properties + 前端 locale 文件即可
- ✅ 业务字典默认**不翻译**，扩展方案见 §6.2
- ✅ 错误响应**信任后端 msg**，前端 code-based 仅做 fallback
- ❌ **禁止**前后端各自维护一套完整翻译（双轨制必漂移）
- ❌ **禁止**业务表里存中文 dict_label（应存 dict_code，由前端/后端按 locale 渲染）

---

## 十、参考实现（可读性优先）

- yudao（ruoyi-vue-pro）的 i18n 实现是国内 Vue 3 + Spring Boot 项目里相对完整的范本
- vue-i18n 官方文档：https://vue-i18n.intlify.dev/
- Spring MessageSource 文档：https://docs.spring.io/spring-framework/reference/core/beans/context-introduction.html#context-functionality-messagesource

> 本 spec 在 yudao i18n 设计基础上简化了 locale 数（仅 zh-CN/en-US）+ 字典默认不翻译，更贴近中小项目实际。
