# Viewport and Layout

> Use this for full-height Vue layouts, Element Plus scroll containers, and mobile pages with inputs.

---

## Full-Height Layout Rule

A container with `height: 100vh`, `height: 100dvh`, or inherited full height must use flex layout when it has multiple vertical children and one child should take the remaining space.

Wrong:

```vue
<aside class="aside">
  <HeaderBar />
  <el-scrollbar>
    <SideMenu />
  </el-scrollbar>
</aside>
```

```css
.aside {
  height: 100vh;
}
```

Correct:

```css
.aside {
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.aside :deep(.el-scrollbar) {
  flex: 1;
  min-height: 0;
}
```

Rules:

- Vertical remaining space requires `flex: 1` plus `min-height: 0`.
- Horizontal remaining space requires `flex: 1` plus `min-width: 0`.
- Do not expect `height: 100%` inside `display: block` to mean remaining space.
- Keep page-level scrolling and component-level scrolling intentionally separated.

---

## Element Plus Scroll Containers

`el-scrollbar`, `el-table`, `el-menu`, drawer content, and tab panes often need stable parent dimensions.

Checklist:

- [ ] Parent has a fixed or flex-resolved height.
- [ ] The scroll child has `min-height: 0`.
- [ ] Tables inside flex columns have a bounded height or flex parent.
- [ ] Empty states do not resize the surrounding layout.
- [ ] Drawer/dialog body scroll is inside the body region, not the whole page.

---

## Mobile Keyboard Rule

Any H5/mobile page with `input`, `textarea`, or Element Plus inputs must handle soft keyboard viewport changes.

Recommended root behavior:

```ts
const viewportHeight = ref<number | null>(null)
const viewportOffsetTop = ref(0)

function syncViewport() {
  const vv = window.visualViewport
  if (!vv) return
  viewportHeight.value = vv.height
  viewportOffsetTop.value = vv.offsetTop
  if (window.innerHeight - vv.height > 80) {
    window.scrollTo(0, 0)
  }
}
```

```css
.mobile-page {
  position: fixed;
  inset: 0;
  height: 100dvh;
  overflow: hidden;
}
```

Also:

- bind `visualViewport.resize` and `visualViewport.scroll`
- apply `transform: translateY(vv.offsetTop)` when needed
- lock `html` and `body` overflow while the page is mounted
- restore global styles on unmount

---

## Verification

- Desktop: resize the window and confirm no body-level extra scrollbar appears.
- Mobile: focus and blur inputs, confirm no blank gap appears below the page.
- E2E or manual browser check must cover the route when layout code changes.

---

## Related

- `component-guidelines.md`
- `e2e-contract.md`
- `quality-guidelines.md`
