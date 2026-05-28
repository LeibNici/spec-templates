# SpringBoot + Vue Spec Template

This template is a starting point for `.trellis/spec/` in Spring Boot + Vue full-stack repositories.

## Install

```bash
trellis init --registry gh:LeibNici/spec-templates/marketplace --template default
```

Direct mode also works when you want to install this template directory without the marketplace picker:

```bash
trellis init --registry gh:LeibNici/spec-templates/marketplace/specs/default
```

## First Steps After Install

1. Read `PLACEHOLDERS.md`.
2. Replace `{Project Name}`, `{app}`, `{app-name}`, `{biz}`, `{org}`, and `{AppName}`.
3. Read `backend/index.md`, `frontend/index.md`, `shared/index.md`, and `guides/index.md`.
4. Delete or rewrite examples that do not match the target repository.

The target project owns the installed specs. Treat this template as a baseline, not as a live remote policy.

## Directory Map

| Directory | Purpose |
|---|---|
| `backend/` | Java, Spring Boot, MyBatis-Plus, MySQL, Redis, testing, deployment rules |
| `frontend/` | Vue, TypeScript, Vite, Element Plus, Pinia, Axios rules |
| `shared/` | API, enum, ID/time, and error contracts shared by backend and frontend |
| `guides/` | Workflow and thinking guides for cross-layer work, dependency changes, i18n, git, and dev servers |

## Authoring Rules

- Keep each spec focused and small enough to inject into agents.
- Put hard cross-layer contracts in `shared/`, not only in `backend/` or `frontend/`.
- Keep folder `index.md` files current whenever files are added, split, renamed, or deprecated.
- Prefer concrete Good/Bad examples and validation commands over broad principles.
- Do not include `.trellis/tasks/`, `.trellis/workspace/`, platform prompt folders, secrets, internal URLs, or product-only PRDs.
