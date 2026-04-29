# Forbidden

## 七、Forbidden（不该 i18n 的内容）

| 类型 | 原因 |
|---|---|
| 订单号 / 编码 / 业务 ID | 是数据，不是文案 |
| 用户输入内容（备注、地址、回复） | 谁输入显示谁的语言 |
| 业务表中的文本字段（产品名、客户名） | 数据本身，需要多语言时单独建表 |
| 日志 / Javadoc / commit message | 给开发者看的，统一英文（或统一中文）即可，不要双轨 |
| 系统枚举 code（`WAITING_PRODUCTION`） | 是 enum 值，前端 `src/constants/` 映射 label |
| 后端 `R<T>.code` 字段 | 是错误码标识，前端 i18n 渲染对应 msg |
