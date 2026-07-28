# `.flow-surface.json` — adapter configuration

Place at the repository root. **Every key is optional.** With no config file the review
runs on stack-neutral defaults. The file exists so one review framework can serve a Python
queue-consumer service and a TypeScript SPA without either being a special case.

```json
{
  "architectureLaw": "ARCHITECTURE.md",
  "contextDocs": ["docs/glossary.md"],
  "scopePredicate": "tenant_id",
  "persistenceInvariant": "All writes flow through the queue consumer; services never write directly.",
  "trustBoundaries": ["HTTP handlers", "queue consumers", "webhook receivers"],
  "testPathPatterns": [
    "src/(.*)\\.ts -> src/__tests__/$1.test.ts",
    "app/(.*)\\.py -> tests/test_$1.py"
  ],
  "coverageThreshold": 0.8,
  "reviewOutputDir": "reviews/",
  "agents": {
    "architecture": "architect",
    "security": "security-reviewer",
    "correctness": { "py": "python-reviewer", "ts,tsx": "code-reviewer" },
    "default": "Explore"
  },
  "remote": {
    "mode": "local",
    "exec": null
  },
  "verification": {
    "ui": "none",
    "db": null,
    "serviceHealth": null
  }
}
```

## Keys

| Key | Effect when absent |
| :--- | :--- |
| `architectureLaw` | Gate 1 falls back to inferring conventions from the codebase |
| `contextDocs` | Reviewers read only the diff and its imports |
| `scopePredicate` | Gate 7 degrades to a generic data-leak check |
| `persistenceInvariant` | Gate 1 checks general transactional consistency instead |
| `trustBoundaries` | Gate 2 infers boundaries from route and handler definitions |
| `testPathPatterns` | Gate 5 guesses conventional test locations per language |
| `coverageThreshold` | Defaults to `0.8` |
| `reviewOutputDir` | Defaults to `reviews/` |
| `agents` | All gates run with the general-purpose agent |
| `remote.mode` | `local` — no remote execution attempted |
| `verification.ui` | `none` — gates run as static analysis only |

## Remote execution

```json
"remote": { "mode": "ssh", "exec": "ssh <host> \"{cmd}\"" }
```

`{cmd}` is substituted. `mode` may be `local`, `ssh`, or `container`. When `local`,
commands run directly and every remote-only step is skipped rather than failed.

## Verification adapters

```json
"verification": {
  "ui": "chrome-devtools",
  "db": "<db-client> \"{sql}\"",
  "serviceHealth": "curl -sf localhost:8000/health"
}
```

`ui` may be `none`, `chrome-devtools`, `playwright`, or any MCP browser tool name. When a
feature has no UI route, the UI adapter is skipped regardless of this setting — see the
`readiness-audit` plugin's route classification.
