# Frontend Development Guidelines

> 适用于 **Vue 3 + TypeScript 5 + Vite 5 + Element Plus 2 + Pinia + Axios**
> 阈值采用"实战宽松档"，见 `quality-guidelines.md`

---

## Applies To

- `{app}-frontend/**`
- Vue SFCs, TypeScript API clients, Pinia stores, routing, UI components, and frontend tests.

---

## Pre-Development Checklist

Before writing any frontend code, read these files based on your task:

- **All tasks**: `quality-guidelines.md` + `type-safety.md`（mandatory）
- **New page / component**: `component-guidelines.md` + `directory-structure.md` + `template-style.md`
- **Full-height layout / mobile input / Element Plus scroll area**: `viewport-layout.md`
- **Data fetching / dict**: `hook-guidelines.md`
- **State management**: `state-management.md`
- **Vue template / route compile / frontend gate evidence**: `static-gate-boundary.md` + `lint-policy.md`
- **Cross-layer feature**: also read `../shared/index.md` + `../guides/full-stack-workflow.md`
- **Page flow / write action / contract regression**: `e2e-contract.md`

---

## Quality Checklist

- [ ] API functions and frontend types match the backend response/request contract.
- [ ] ID, time, enum, and error handling rules match `../shared/`.
- [ ] Components follow size, state, loading, and error-state rules.
- [ ] Full-height and mobile-input layouts have stable viewport behavior.
- [ ] Reused constants, composables, and stores are searched before adding new ones.
- [ ] Template/SFC changes are checked by ESLint/Vite/route verification, not `vue-tsc` alone.
- [ ] Write flows and cross-layer regressions have Playwright coverage or a documented reason they cannot.
- [ ] Targeted UI/API verification covers the changed flow.

---

## Spec Map

| Guide | Scope | Status |
|-------|-------|---|
| [Directory Structure](./directory-structure.md) | `src/` 目录布局、模块组织、关键约定 | Filled |
| [Quality Guidelines](./quality-guidelines.md) | 代码硬性上限、HTTP 错误归因、健壮性兜底、Forbidden patterns | Filled |
| [Component Guidelines](./component-guidelines.md) | 组件大小、大列表优化、StatusTag、el-drawer、Dialog 写操作刷新契约 | Filled |
| [Hook Guidelines](./hook-guidelines.md) | Composables（Vue 3 Composition API）、useDict、数据获取 | Filled |
| [State Management](./state-management.md) | Pinia stores、reactive 选择、shallowRef vs ref | Filled |
| [Type Safety](./type-safety.md) | API 函数泛型、VO/DTO 类型、前后端契约对齐 | Filled |
| [Template Style](./template-style.md) | `<template>` / `<script setup>` 写法约定 | Filled |
| [Playwright E2E Contract](./e2e-contract.md) | API/DB/UI seed 策略、数据隔离、写操作等待真实请求、跨层验收 | Filled |
| [Viewport and Layout](./viewport-layout.md) | 100vh/flex/min-height、Element Plus 滚动容器、移动端软键盘视口 | Filled |
| [Vue Static Gate Boundary](./static-gate-boundary.md) | vue-tsc / ESLint / Vite / Playwright 的能力边界与验收口径 | Filled |
| [Lint Policy](./lint-policy.md) | ESLint / Prettier 规则意图清单（字面层防腐） | Filled |

---

**Language**: 中英混排（术语英文，铁律中文）。
