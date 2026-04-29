# Frontend Directory Structure

> 适用：Vue 3 + Vite 5 + TypeScript

## Layout

```
src/
  main.ts                # 应用入口 + errorHandler + onunhandledrejection
  App.vue
  api/
    request.ts           # Axios: JWT 注入 + res.data 拆包 + 401 跳登录
    {biz}.ts             # 按模块分文件（带泛型类型）
  router/index.ts        # 路由 + 导航守卫
  stores/
    user.ts              # 用户状态（Pinia）
    app.ts               # 应用级状态
    dict.ts              # 业务字典缓存
  views/{biz}/           # 按模块组织页面组件
  components/            # 共享组件（StatusTag, ...）
  constants/             # 系统枚举常量集中
  composables/           # 共享 composable（useDict, useLoading, ...）
  layouts/MainLayout.vue
  utils/format.ts        # 格式化工具
  types/                 # 共享 TS 类型 / VO interface
    {biz}/               # 对应后端业务模块
    common.ts
  styles/                # 全局样式
  assets/                # 静态资源
```

> `{biz}` 是业务模块占位符，与后端 `{biz}` 模块一一对应。

---

## 关键约定

- **API 文件按模块**：`api/order.ts`, `api/inventory.ts`
- **Views 按模块**：`views/order/`, `views/inventory/`
- **常量集中**：所有系统枚举在 `src/constants/`，不散落在页面
- **Composables 共享逻辑**：`useDict`, `useLoading`, `usePagination` 等
- **Types 描述 API 契约**：VO/DTO interface 在 `src/types/`

---

## Forbidden

- API 函数无泛型类型声明
- 常量/枚举散落在页面组件
- 工具函数在多页面重复（抽到 `utils/` 或 `composables/`）
- 跨模块直接 `import` 他人的 store / composable（应通过 props / emits 或公共层）

---

## 新建模块 Checklist

每个业务模块（前端 view 维度）必须产出：

- [ ] `src/api/{biz}.ts` — API 函数（带泛型）
- [ ] `src/types/{biz}/` — VO/DTO interface
- [ ] `src/views/{biz}/` — 页面组件
- [ ] `src/composables/{biz}/`（可选）— 模块特有 composable
- [ ] `src/router/` 内补充路由
