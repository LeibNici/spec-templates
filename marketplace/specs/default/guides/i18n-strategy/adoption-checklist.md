# Adoption Checklist

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
