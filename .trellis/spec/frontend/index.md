# Frontend Development Guidelines

> 适用于 **Vue 3 + TypeScript 5 + Vite 5 + Element Plus 2 + Pinia + Axios**
> 阈值采用"实战宽松档"，见 `quality-guidelines.md`

---

## Guidelines Index

| Guide | Scope |
|-------|-------|
| [Directory Structure](./directory-structure.md) | `src/` 目录布局、模块组织、关键约定 |
| [Quality Guidelines](./quality-guidelines.md) | 代码硬性上限、HTTP 错误归因、健壮性兜底、Forbidden patterns |
| [Component Guidelines](./component-guidelines.md) | 组件大小、大列表优化、StatusTag、el-drawer、Dialog 写操作刷新契约 |
| [Hook Guidelines](./hook-guidelines.md) | Composables（Vue 3 Composition API）、useDict、数据获取 |
| [State Management](./state-management.md) | Pinia stores、reactive 选择、shallowRef vs ref |
| [Type Safety](./type-safety.md) | API 函数泛型、VO/DTO 类型、前后端契约对齐 |
| [Template Style](./template-style.md) | `<template>` / `<script setup>` 写法约定 |
| [Lint Policy](./lint-policy.md) | ESLint / Prettier 规则意图清单（字面层防腐） |

---

## Pre-Development Checklist

Before writing any frontend code, read these files based on your task:

- **All tasks**: `quality-guidelines.md` + `type-safety.md`（mandatory）
- **New page / component**: `component-guidelines.md` + `directory-structure.md` + `template-style.md`
- **Data fetching / dict**: `hook-guidelines.md`
- **State management**: `state-management.md`
- **Cross-layer feature**: Also read `../guides/`

---

**Language**: 中英混排（术语英文，铁律中文）。
