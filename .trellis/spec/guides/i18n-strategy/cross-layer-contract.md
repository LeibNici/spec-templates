# Cross-Layer Contract

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
