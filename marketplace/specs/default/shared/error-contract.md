# Error Contract

> Error handling must be predictable for users, callers, logs, and tests.

---

## Convention: Stable Error Codes

**Do**: Return a stable business error code and a safe message.

**Good**:

```json
{
  "code": "ORDER_NOT_FOUND",
  "message": "订单不存在",
  "data": null
}
```

**Bad**:

```json
{
  "message": "java.lang.NullPointerException at ..."
}
```

**Validation**: Backend tests assert `code`; frontend branches on `code` only when it needs business-specific handling.

---

## Convention: Validation Errors

**Do**: Return field-level validation details when the frontend can show them.

**Good**:

```json
{
  "code": "VALIDATION_FAILED",
  "message": "参数校验失败",
  "errors": [
    { "field": "name", "message": "名称不能为空" }
  ]
}
```

**Do Not**: Collapse all validation details into one generic message when a form can show field feedback.

---

## Convention: Sensitive Data

**Do**: Redact password, token, secret, API key, phone, and identity data in logs and error payloads.

**Do Not**: Return exception stack traces or raw request bodies to the frontend.

**Validation**: Global exception handling tests cover at least one sensitive field when request-body logging changes.
