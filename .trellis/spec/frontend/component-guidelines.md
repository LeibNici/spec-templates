# Frontend Component Guidelines

## Size Limits

- Vue 文件 ≤ 500 行；超出 → 抽 composable + 拆子组件
- Template 嵌套 ≤ 4 层

---

## 大列表优化

- `shallowRef` 替代 `ref`（大数组）
- `el-pagination` 前端分页
- `el-tree`：禁用 `default-expand-all`；> 1000 节点 → `el-tree-v2`
- 编辑弹窗：`reactive` 仅用于表单字段，不用于整份数据

---

## 高并发（> 200 用户）

| 场景 | 解决方案 |
|---|---|
| 搜索输入 | `debounce 300ms` |
| 提交按钮 | `:disabled` / `:loading` 直到响应 |
| 列表刷新 | `throttle 1s` |
| 下拉 > 200 项 | `remote-method` |
| 表格 > 200 行 | `el-table-v2`（虚拟滚动） |
| 树 > 500 节点 | 懒加载 |

---

## 性能

- 路由懒加载（`() => import(...)`）
- 公共库走 CDN externals
- 图片 > 200KB → 压缩 / WebP
- 长超时 API：单独传 `{ timeout: 180000 }`，永远不要改全局

---

## StatusTag 组件（建议）

为状态标签 + 颜色渲染建立统一组件。

### Forbidden

```vue
<!-- WRONG: 每页自己写状态映射 -->
<el-tag :type="row.status === 'APPROVED' ? 'success' : 'warning'">
  {{ row.status === 'APPROVED' ? '已审批' : '待审批' }}
</el-tag>
```

### Correct

```vue
<StatusTag :value="row.status" dict-type="approval_status" />
```

---

## el-drawer 用法（主从列表）

「主列表 + 明细抽屉」场景统一用 `el-drawer` 而非 `el-dialog`（抽屉更适合宽表格 / 长字段 / 多列筛选）。

### 推荐配置

```vue
<el-drawer
  v-model="drawerVisible"
  :title="drawerTitle"
  direction="rtl"
  size="800px"
  destroy-on-close
>
  <!-- header 区：当前主行标识 + 明细筛选 -->
  <!-- body 区：明细表格 -->
</el-drawer>
```

| 字段 | 值 | 原因 |
|---|---|---|
| `direction` | `rtl`（右侧划出） | 主流后台管理习惯 |
| `size` | `800px`（宽表格）/ `600px`（窄） | 避免表格横向滚动 |
| `destroy-on-close` | `true` | 防止上一条详情残留污染下一条 |

### 交互边界（铁律）

1. **Drawer 内部职责单一**：只做"展示 + 筛选"，**禁止**写操作按钮（采购 / 审批 / 删除等统一在主列表维度进行）
2. **筛选下拉候选派生方式**：若候选集是当前主行衍生的维度，优先从**首次加载的明细数据 `distinct` 派生**，不要另开 API；只有候选集跨主行的情况才新增 `options` 接口
3. **状态隔离**：Drawer state 放在 composable（`useXxxDrawer` 或合并进 `useXxxGrouped`），不放组件 `setup` 顶层
4. **打开时机**：点行操作列按钮触发 `openDetail(row)`，在 composable 内部串行 `setCurrentRow → setVisible(true) → loadDetails()`，禁止异步 race

---

## 异步批量操作

API 可能超时的场景（批量导入 > 500、导出 > 10K、批量审批 > 50）：

- 显示"处理中"loading
- 提交按钮禁用直到完成
- 长操作显示"还在处理，请稍后刷新"
- 防重复提交

---

## Dialog 写操作后列表刷新契约

**铁律**：Dialog 内调用的 API 只要会**改变服务端持久化状态**，Dialog 关闭时父列表必须 `fetchData()` 刷新。**即使 API 名字看起来像查询**（`check` / `preview` / `validate`），只要落库就视为写操作。

### Why

Element Plus 的 `el-dialog` 只负责自身 modelValue；它不知道父组件有列表需要同步。Dialog 内展示的"最新值"只存在于 Dialog 局部，关闭后父组件 `tableData` 仍是打开前的旧快照。

**最易漏的一类 API**：名字是 `check` / `preview` / `calc` 但后端顺手落库——典型的"看起来只读、实际写库"。

### 反例

**现象**：列表点"齐套检查"→ 弹窗显示齐套率 `95.5%` → 关闭弹窗 → 列表"齐套率"列仍是 `0%`。

**根因**：`kitCheck(id)` 后端把 `kit_readiness_rate` 写入表，前端只把返回值塞给 Dialog 的局部 `kitData`，**没写 `fetchData()`**。

### 推荐写法

**方案 A（推荐）**：watch Dialog 的 v-model，由 true→false 时刷新

```ts
const kitDialog = ref(false)
watch(kitDialog, (open, prev) => {
  if (prev && !open) fetchData()
})
```

优点：任意关闭路径（X / ESC / 遮罩 / 代码置 false）都命中。

**方案 B**：Dialog 组件 emit `closed` 事件，父组件监听

```vue
<MyDialog v-model="dialog" @closed="fetchData" />
```

仅在 Dialog 组件已暴露 `closed` 事件时使用。

### Review Checklist

新增 Dialog 时 PR 必过：

- [ ] Dialog 调用的 API 是否有副作用（落库 / 改状态 / 锁定 / 生成下游数据）？
- [ ] 是 → 父列表是否展示了该 API 会改的字段？
- [ ] 是 → 是否有 `watch(dialog)` 或 `@closed` 关闭时 `fetchData()`？
- [ ] API 名字是否误导（`check` / `preview` / `calc` 其实写库）？→ **最该加刷新的就是这类**

---

## 层级主数据选择 UI 契约

> 替换硬编码 `string[]` 为主数据 API 时，**先看主数据 schema 有没有 parent / group 字段**——有则上树，不要扁平多选。

### 决策树

```
主数据有 parent_xxx_code / group_xxx_code / 自引用 parentId？
├─ 否 → el-select multiple filterable（保留扁平多选）
└─ 是 → el-tree show-checkbox
        ├─ 节点数 ≤ 1000：el-tree
        ├─ 节点数 > 1000：el-tree-v2
        └─ 单选场景：tree + radio 替代 cascader
```

**铁律**：同一份层级主数据在系统内**必须用同一种渲染范式**。比如某档案在 A 页面是树，那在 B 页面也必须是树（用户的 mental model 是连续的）。

### el-tree show-checkbox 模板

```vue
<el-tree
  ref="treeRef"
  :data="treeData"
  node-key="key"
  show-checkbox
  :props="{ label: 'label', children: 'children' }"
/>
```

回填已选值（编辑场景）：

```ts
function syncTreeFromValues() {
  nextTick(() => {
    const targetSet = new Set(form.skillTags.split(','))
    const leafKeys = collectLeafKeysByPayload(targetSet)
    treeRef.value?.setCheckedKeys(leafKeys, false)
  })
}
```

收集已选叶子（写回 form）：

```ts
function onCheck() {
  const leaves = treeRef.value?.getCheckedNodes(true) ?? []  // leafOnly=true
  form.skillTags = leaves.map(n => n.payload).join(',')
}
```

### 关键陷阱

1. **`getCheckedNodes(false)` 把父组节点也算进来**：父组当 value 写库会污染逗号字符串。永远 `getCheckedNodes(true)`（leafOnly）
2. **`v-if` 分支切换 tree 不同步**：tree 实例被卸载重建时，需要 `watch(...)` + `nextTick(syncTreeFromValues)`
3. **dialogVisible 异步渲染**：设 `dialogVisible=true` 时 tree ref 可能尚未挂载，必须 `nextTick`
4. **数据来源单一性**：树结构和叶子集合**只调一个 API**，不要"先拉树再单独拉叶子"——两次请求时序不一致会造成"勾选时孤儿叶子"
