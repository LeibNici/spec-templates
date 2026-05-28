# Local Verification

> Compile success is not integration success. Before pushing or deploying behavior changes, run the relevant app locally and verify the changed path.

---

## Core Rule

Any backend, frontend, SQL, API contract, or integration behavior change must be validated locally unless the change is documentation/spec only or the repository explicitly has no runnable app.

Use the strongest practical check for the changed path:

- backend: package, start jar, call the changed endpoint
- frontend: typecheck/lint/build as applicable, start dev server, open the changed route
- full-stack: local frontend talks to local backend
- database: migrate and inspect schema/indexes
- E2E: Playwright covers user-visible flows

---

## Backend Checklist

- [ ] Build the target app with the repository-standard command.
- [ ] Start the packaged jar, not a stale classpath runner.
- [ ] Probe a changed endpoint until it returns `200`, `400`, `401`, or `403`; `404` means route registration is not proven.
- [ ] Call the normal path and at least one affected edge path.
- [ ] Inspect logs for startup, migration, and request errors.

For Spring Boot multi-module projects, follow `build-dependency-governance-guide.md` and use `-pl <app> -am` when building a target app.

---

## Frontend Checklist

- [ ] Run typecheck for TypeScript changes.
- [ ] Run lint for template/SFC changes.
- [ ] Start Vite and check the dev log for template compile errors.
- [ ] Open the changed route through Playwright or browser verification.
- [ ] Verify console and network have no unexpected errors.
- [ ] For write flows, wait for the real network request or final state.

---

## Full-Stack Checklist

- [ ] Backend is local and freshly built.
- [ ] Frontend is local and points to the local backend.
- [ ] API request/response fields match shared contracts.
- [ ] Empty, validation, permission, and success states affected by the change are checked.
- [ ] Playwright E2E exists or the reason for not adding it is recorded.

---

## Allowed Skips

Local verification may be skipped for:

- Markdown/spec-only changes
- comments or typo-only changes
- deleting code that is proven unused by repository search
- configuration text that does not affect runtime

When skipping, state why the change has no runtime path.

---

## Related

- `dev-server-lifecycle-guide.md`
- `build-dependency-governance-guide.md`
- `full-stack-workflow.md`
- `../frontend/e2e-contract.md`
- `../frontend/static-gate-boundary.md`
