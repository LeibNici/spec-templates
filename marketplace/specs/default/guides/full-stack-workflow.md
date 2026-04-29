# 全栈开发工作流（不 mock）

> **核心铁律**：每开一个 feature 都是前后端一起做。用"后端先搭空接口"替代"前端 mock"——更快、零联调切换、类型/路径/错误处理全程真实。

---

## 为什么不 mock

mock 是给"前后端时间错开 ≥ 1 周"的团队用的。我们的工作流（前后端同期，AI 协助）下：

| 维度 | mock 派 | 不 mock 派（推荐） |
|---|---|---|
| axios 调用 | mock 截胡，**真接口从未被打通** | 一开始就真接，全程验证 |
| 类型契约对齐 | 凭记忆，易漂移；后期切换时踩雷 | 后端 VO → 前端 TS **直接抄** |
| 接口路径对齐 | 易拼错（mock 不会报错） | 后端先建好，前端 copy URL |
| 错误处理测试 | mock 永远成功，错误路径未走过 | 真 4xx/5xx，路径全覆盖 |
| 联调阶段 | 集中切换"mock→真"，踩雷高峰 | 零切换 |
| AI 协助 | mock 数据 AI 要编一大堆，后期清理麻烦 | AI 直接生成空接口骨架，10 行搞定 |

**根因**：你之前"mock 后无法对齐"的痛——本质是 mock 让真接口的"路径 / 类型 / 错误处理"全程缺席验证，最后联调阶段集中爆雷。

---

## 推荐 5 步流程

### Step 1：DDL 先行（5 min）

```bash
# 1. 写 Flyway V 文件
cat > {app}-admin/src/main/resources/db/migration/V{N}__add_xxx.sql <<'SQL'
CREATE TABLE IF NOT EXISTS `xxx` (
  `id`         BIGINT NOT NULL,
  `xxx_no`    VARCHAR(64) NOT NULL,
  -- 公共字段（继承 BaseEntity）
  `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `create_by`   VARCHAR(64) DEFAULT NULL,
  `update_by`   VARCHAR(64) DEFAULT NULL,
  `deleted`     TINYINT NOT NULL DEFAULT 0,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='xxx 表';
SQL

# 2. admin 启动 → Flyway 自动 migrate（不要手改表）
mvn -f {app}-backend/pom.xml -pl {app}-admin -am clean package -DskipTests
java -jar {app}-admin/target/{app}-backend.jar
```

### Step 2：后端契约层（10 min，**关键步骤**）

**目标**：让 curl 能 200 响应 —— 即便返空数据。

```java
// 1. Entity（继承 BaseEntity）
@Data
@TableName("xxx")
@EqualsAndHashCode(callSuper = true)
public class Xxx extends BaseEntity {
    private String xxxNo;
}

// 2. Mapper（用 BaseMapper 即可）
public interface XxxMapper extends BaseMapper<Xxx> {}

// 3. DTO（入参）/ VO（出参）
@Data
public class XxxCreateDTO {
    @NotBlank(message = "{xxx.no.notblank}")
    private String xxxNo;
}

@Data
public class XxxVO {
    private Long id;
    private String xxxNo;
    private LocalDateTime createTime;
}

// 4. Service 接口 + 空 Impl
public interface XxxService {
    Page<XxxVO> page(XxxQuery query);
    XxxVO create(XxxCreateDTO dto);
}

@Service
@RequiredArgsConstructor
public class XxxServiceImpl implements XxxService {
    private final XxxMapper xxxMapper;

    @Override
    public Page<XxxVO> page(XxxQuery query) {
        // TODO: 暂返空，前端可调通
        return new Page<>();
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public XxxVO create(XxxCreateDTO dto) {
        // TODO: 暂返带 id 的占位，前端可调通
        return XxxVO.builder().id(0L).xxxNo(dto.getXxxNo()).build();
    }
}

// 5. Controller
@RestController
@RequestMapping("/api/xxx")
@RequiredArgsConstructor
public class XxxController {
    private final XxxService xxxService;

    /**
     * 分页查询。
     */
    @GetMapping
    public R<Page<XxxVO>> page(XxxQuery query) {
        return R.ok(xxxService.page(query));
    }

    /**
     * 创建。
     */
    @PostMapping
    public R<XxxVO> create(@RequestBody @Valid XxxCreateDTO dto) {
        return R.ok(xxxService.create(dto));
    }
}
```

**重启后端 → curl 验证**（详见 `dev-server-lifecycle-guide.md`）：

```bash
# 验证 path + 401（未带 token = 路由注册成功）
curl -s -m 2 -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8080/api/xxx
# 期望: 401（路由有了，鉴权挡了）—— 而不是 404
```

✅ 此时前端已经可以接真接口了。

### Step 3：前端类型 + API（5 min）

```ts
// src/types/{biz}/xxx.ts —— 直接抄后端 VO/DTO 字段
export interface XxxVO {
  id: number
  xxxNo: string
  createTime: string
}

export interface XxxCreateDTO {
  xxxNo: string
}

export interface XxxQuery {
  keyword?: string
  page: number
  size: number
}
```

```ts
// src/api/xxx.ts —— 真实 axios 调用，零假数据
import { get, post } from './request'
import type { XxxVO, XxxCreateDTO, XxxQuery } from '@/types/{biz}/xxx'
import type { PageResult } from '@/types/common'

export const pageXxx = (params: XxxQuery) =>
  get<PageResult<XxxVO>>('/api/xxx', { params })

export const createXxx = (data: XxxCreateDTO) =>
  post<XxxVO>('/api/xxx', data)
```

✅ 前端能调通，看到空 records 也是真实的。

### Step 4：前端页面 + 后端实现 并行

**这是主体工作时间**——**前后端两边互不阻塞**：

| 前端 | 后端 |
|---|---|
| 列表页面骨架 + 调 `pageXxx()` | Service Impl 用 `xxxMapper.selectPage()` 填实 |
| 新建表单 + 调 `createXxx()` | `create()` 加业务校验 + insert + 返回 VO |
| 搜索 / 筛选交互 | XxxQuery 加字段 + Mapper XML LIKE 查询 |
| 错误兜底（4xx 提示）| GlobalExceptionHandler 统一异常 |
| Loading / 空态 | （略） |

任意一边进度更快不影响另一边。前端永远看到"真接口的真实响应"——只是数据从空到逐渐填实。

### Step 5：联调（10 min）

```bash
# 1. 验证完整流程
curl -X POST http://localhost:8080/api/xxx \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"xxxNo": "TEST-001"}'

# 2. 前端浏览器实操
# - 列表加载 ✅
# - 新建提交 ✅
# - 编辑 / 删除 ✅
# - 错误提示（如重复 xxxNo）✅
```

零切换 —— 前端代码一行没动，后端从空跳到完整实现。

---

## 反例对照（mock 派会怎么做 + 为什么坑）

### 反例 A：前端 mock 数据写在 api 函数里

```ts
// ❌ 错误
export const pageXxx = (params: XxxQuery) => {
  if (import.meta.env.DEV) {
    return Promise.resolve({
      records: [{ id: 1, xxxNo: 'MOCK-001', createTime: '2026-04-27' }],
      total: 1,
    })
  }
  return get<PageResult<XxxVO>>('/api/xxx', { params })
}
```

**后果**：
1. 后端写好后忘记删 `if DEV`，dev 环境永远显示 mock，prod 环境显示真但本地测不出
2. mock 数据字段拼错（如 `createAt` vs `createTime`），切到真接口报 undefined
3. 错误路径（401 / 500）从未被前端代码处理过

### 反例 B：前端组件里写 const mockList

```vue
<!-- ❌ 错误 -->
<script setup lang="ts">
const mockList = ref([
  { id: 1, xxxNo: 'MOCK-001' },
  { id: 2, xxxNo: 'MOCK-002' },
])
// const list = await pageXxx() // 后端好了再换
</script>
```

**后果**：上线后真接口 200 返空，但页面还在显示 mockList 假数据，运营投诉假数据 demo。

### 反例 C：vite-plugin-mock 装在 mock/ 目录

```ts
// mock/xxx.ts
export default [{ url: '/api/xxx', method: 'get', response: () => mockData }]
```

**后果**：
1. mock 文件不更新，永远落后于后端真 schema
2. dev 用 mock 跑通，切到 prod 接口后字段对不上
3. mock 文件占用 git 体积，重构时还要同步改两份

---

## 例外：仍然可以用 mock 的场景（罕见）

| 场景 | 处理 |
|---|---|
| 第三方 API 无法控制（如银联支付） | 抽 Adapter 接口，dev 软失败 + 真接 prod；不写"假数据 mock" |
| 后端做大重构，老 API 暂时不可用 | 拉 release 分支 + feature 分支并行；不 mock |
| Demo 演示但 DB 没数据 | Flyway V 文件加 seed 数据；不 mock |
| 单元测试 / vitest 测组件 | 仅在 `*.test.ts` 文件里 mock 函数返回值 |

---

## CI 检测（防 mock 残留）

### Pre-commit hook

```bash
#!/bin/sh
# .git/hooks/pre-commit (or husky)

# 前端 mock 残留检测
if grep -rn -E "(mockData|mockList|fakeData|return Promise\.resolve\()" \
   src/ --exclude-dir=test --exclude="*.test.ts" 2>/dev/null; then
  echo "❌ 发现前端 mock 残留，请删除"
  exit 1
fi

# 后端 dev 假数据检测
if grep -rn -E "if \(devMode|@Profile\(\"dev\"\).*return new" \
   {app}-backend/src/main/java/ 2>/dev/null; then
  echo "❌ 发现后端 dev 假数据残留"
  exit 1
fi
```

### CI step

```yaml
# .github/workflows/ci.yml 或 GitLab CI
- name: Check mock residue
  run: |
    ! grep -rn -E "mockData|mockList|fakeData" src/ --exclude-dir=test
```

---

## Review Checklist（PR 必过）

- [ ] api/ 文件无 `Promise.resolve(假数据)` / `if DEV` 分支
- [ ] views/ 业务组件无 `const mockList = [...]`
- [ ] 后端无 `@Profile("dev")` Bean 直接返业务假数据
- [ ] CI mock 检测脚本通过
- [ ] DDL → 后端契约 → 前端真 API 路径连通验证

---

## 与 Trellis 工作流的呼应

本 5 步流程也是 Trellis `parallel-execution-default.md` 的 Wave 分波体现：

- **Wave 1**：DDL（同步）+ 后端 research/implement（并发）
- **Wave 2**：前端类型 + API + 页面（并发，依赖 Wave 1 完成）

AI 协助下整个流程压缩到 2-4 小时（小型 feature）/ 1-2 天（中型 feature）。
