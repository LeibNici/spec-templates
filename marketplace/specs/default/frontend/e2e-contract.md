# Playwright E2E Contract

> Use this when adding or changing page flows, API contracts, write actions, or cross-layer behavior.

---

## Scope

Playwright E2E is the acceptance layer for user-visible Vue flows that depend on backend behavior.

Use it for:

- Page loading and route visibility.
- Create, update, delete, submit, approve, generate, import, export, or other write flows.
- Cross-layer field mapping between backend DTO/VO and frontend types.
- Permission, validation, empty-state, and error-state behavior.
- Regression cases that type-checking and unit tests cannot catch.

Do not replace E2E with screenshots or manual browser inspection when the flow is automatable.

---

## Convention: Seed Strategy

**Priority**: API > DB fixture > UI.

| Layer | Use For | Rule |
|---|---|---|
| API seed | Stable setup endpoints exist | Preferred setup path |
| DB fixture | No API exists for setup-only data | Allowed only in E2E fixtures |
| UI | The action being tested | Do not use UI clicks to create large setup chains |

**Do**:

```typescript
const api = await newApiContext()
await api.post('/api/example/items', { data: itemPayload })

await page.goto('/example/items')
await page.getByRole('button', { name: 'Edit' }).click()
```

**Do Not**: Spend most of a spec clicking unrelated pages only to create preconditions.

---

## Convention: Data Isolation

**Do**:

- Prefix all seeded records with one per-spec unique value.
- Clean up in `afterAll` when practical.
- Fill all fields that the UI displays, not only primary keys.
- Assert key displayed fields are not blank, `null`, `undefined`, `NaN`, or `Invalid Date`.

```typescript
const prefix = `e2e-${Date.now()}`
const itemName = `${prefix}-item`
```

**Do Not**:

- Keep long-lived E2E business data by default.
- Let incomplete fixture rows create false UI blanks.
- Reuse hard-coded codes that collide across repeated runs.

---

## Convention: Wait For Real Writes

Toast messages are not write-completion signals.

**Do**: Register the response wait before clicking the button that triggers the write.

```typescript
const saved = page.waitForResponse((response) =>
  response.url().includes('/api/example/items') &&
  response.request().method() === 'POST',
)
await page.getByRole('button', { name: 'Save' }).click()
expect((await saved).ok()).toBe(true)
```

**Do Not**:

```typescript
await page.getByRole('button', { name: 'Save' }).click()
await expect(page.getByText(/success/i)).toBeVisible()
```

If backend work is asynchronous by contract, wait for the status API or database state, not only the command response.

---

## Convention: Current-Missing Assertions

When a documented future behavior is not implemented yet, do not write a happy-path test and skip it.

**Do**: Assert the current absence in a way that turns red when implementation appears.

```typescript
const response = await api.post('/api/example/future-action', { data: payload })
if (response.status() === 404) {
  return
}
const body = await response.json()
expect(body.success === true, 'Feature appears implemented; upgrade this spec').toBe(false)
```

This keeps the gap visible and prevents silent forgetting.

---

## Convention: API Response Awareness

E2E API clients see the raw backend response. Frontend interceptors may unwrap or transform responses.

**Do**:

- Assert the real wire format returned by backend APIs.
- Keep helper functions for response envelope parsing.
- Fail early on non-2xx transport errors.

**Do Not**: Assume Playwright `APIRequestContext` returns the same shape as your Axios interceptor exposes to components.

---

## Tests Required

For every changed user flow, cover the strongest practical subset:

- Route opens and main page regions are visible.
- Primary action can be executed through the UI.
- Write action waits for request or state completion.
- Result is visible in list/detail or confirmed through API/DB.
- Empty, validation, permission, or business-error state is covered when directly affected.
- Frontend field names, enum values, IDs, and time values match the backend contract.

---

## Related

- `../shared/api-contract.md`
- `../shared/id-time-contract.md`
- `../shared/enum-transport-contract.md`
- `../shared/error-contract.md`
