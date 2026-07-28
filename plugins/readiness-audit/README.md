# readiness-audit

Versioned production-readiness audits with a permanent gate ledger and finding lifecycle.

```
/plugin install readiness-audit@flow-surface
/readiness-audit:audit --status
```

- **Permanent gate IDs** — future work targets IDs, not feature names.
- **Four states** — `UNLOCKED`, `LOCKED`, `PARTIAL`, `BROKEN`. The last one matters:
  "not built" and "built and broken" need different responses.
- **Finding lifecycle** — `NEW` / `PERSISTENT` / `RESOLVED` / `REGRESSED`. A regression is
  a process failure, not a code failure.
- **Immutable runs** — the diff between runs is the signal.

Requires `research/feature-registry.md`. This plugin recommends gate states; it never
opens one. Skills: `audit-execution`, `gate-ledger`.
