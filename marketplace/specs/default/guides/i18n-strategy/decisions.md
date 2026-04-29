# Decisions & References

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
