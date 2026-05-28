# State Freshness

> Previous tool output is not current truth. Recheck volatile state before making a blocking conclusion.

---

## Core Rule

Files, ports, processes, symlinks, dependency installs, build outputs, and dev servers can change between tool calls. If the conclusion depends on current state, rerun the relevant check.

---

## Recheck Triggers

| Trigger | Recheck |
|---|---|
| User asks to retry or says the state changed | rerun the exact command or direct state check |
| More than a few seconds passed during install/build/startup | recheck files, ports, or logs |
| A command was interrupted | recheck partial outputs before diagnosing |
| You are about to say "missing", "still running", "port occupied", or "not started" | verify with `ls`, `lsof`, `ps`, `curl`, or log tail |
| You changed source code and then tested a server | rebuild/restart or prove hot reload applied |

---

## Patterns

Current file state:

```bash
ls -la /path/to/critical/file
```

Current port owner:

```bash
lsof -nP -iTCP:8080 -sTCP:LISTEN
```

Current endpoint state:

```bash
curl -s -m 2 -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8080/api/health
```

Current dev log:

```bash
tail -80 /tmp/frontend-dev.log
```

---

## Forbidden Conclusions

- "The file is missing" based only on an old `ls` after an install continued.
- "The dev server cannot start" without retrying after dependencies changed.
- "The endpoint is 404" after changing code but before rebuilding/restarting.
- "The process is still running" without a fresh `lsof` or `ps`.

---

## Review Checklist

- [ ] Volatile state was checked close to the conclusion.
- [ ] User corrections triggered a fresh check, not a debate from stale output.
- [ ] Startup and route conclusions use endpoint probes or fresh logs.
- [ ] Build artifact conclusions inspect the current artifact.

---

## Related

- `dev-server-lifecycle-guide.md`
- `local-verification.md`
