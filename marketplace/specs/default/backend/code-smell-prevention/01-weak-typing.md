## 1. 弱类型传递（全链路禁止）

**铁律：全链路禁止 `Map<String,Object>` / `JSONObject` / `Object` 作为方法签名的入参或返回值。**

| 层 | 入参 | 返回 |
|---|---|---|
| Controller | DTO + `@Valid` | `R<VO>` |
| Service | DTO / Command / 具体类型 | VO / Entity / 具体类型 |
| Mapper | `@Param` 具体类型 | Entity / VO |

**唯一例外**：`CrossModuleMapper` 返回 `Map` 且调用方在同一方法内立即转为 VO。

### Forbidden

```java
// Service 签名用 Map
void approve(Map<String, Object> params);
Map<String, Object> getDashboard();

// Mapper 返回 List<Map> 且直接透传到 Controller
List<Map<String, Object>> listOrders();

// 用 Object 逃避泛型
R<Object> getOrder(Long id);

// JSONObject 在 Service 间传递
JSONObject data = new JSONObject();
data.put("orderNo", orderNo);
otherService.process(data);
```
