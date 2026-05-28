# Vue Static Gate Boundary

> `vue-tsc` passing does not prove a Vue page can compile or render.

---

## Core Rule

Use multiple gates for frontend changes:

- `vue-tsc` checks TypeScript in script blocks and generated component types.
- ESLint with `eslint-plugin-vue` parses Vue templates.
- Vite dev/build compiles template expressions.
- Playwright verifies the route and user flow in a browser.

Do not report "frontend passed" from `vue-tsc` alone when templates, routes, API calls, or layout changed.

---

## Common Blind Spot

Template expressions can fail at Vite compile time even when type-checking passes.

Wrong:

```vue
<el-empty :description="'Click "Create" to add an item'" />
```

Safer:

```vue
<script setup lang="ts">
const emptyDescription = 'Click "Create" to add an item'
</script>

<template>
  <el-empty :description="emptyDescription" />
</template>
```

Prefer moving complex strings, computed labels, and conditional text into `<script setup>`.

---

## Required Gates by Change Type

| Change | Minimum Gate |
|---|---|
| Type-only change | `vue-tsc --noEmit` |
| Template or SFC change | ESLint plus Vite compile or route open |
| Route/page flow change | Playwright opens the route |
| API client/contract change | Playwright or integration smoke against real backend |
| Build config/plugin change | full production build |

---

## Dev Server Log Check

When using Vite dev server, check the dev log after editing SFC templates:

```bash
tail -80 /tmp/frontend-dev.log
```

Fail on:

- `[vite] Internal server error`
- `Plugin: vite:vue`
- `Error parsing JavaScript expression`
- unresolved import or route chunk errors

---

## Review Checklist

- [ ] Template expressions avoid nested quote tricks and complex inline logic.
- [ ] ESLint uses `eslint-plugin-vue` with `vue-eslint-parser`.
- [ ] Changed routes were compiled by Vite or opened by Playwright.
- [ ] `vue-tsc PASS` is not used as the only evidence for UI changes.
- [ ] Production build runs for config/plugin changes.

---

## Related

- `lint-policy.md`
- `e2e-contract.md`
- `../guides/local-verification.md`
