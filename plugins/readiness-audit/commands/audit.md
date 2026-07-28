---
description: Run a production readiness audit, generate its report, or check ledger status.
---

Run the readiness audit for: $ARGUMENTS

- `--audit [GATE-NN ...]`  load `audit-execution`; run (or resume) the audit. With gate IDs, audit only those
- `--batch <N>`            with --audit, run one batch only
- `--report`               compile REPORT.md, gate recommendations, and planning briefs
- `--status`               load `gate-ledger`; print current gate states and open debt. Read-only
- `--commit`               finalize the run and mark it COMPLETED
- `--fresh`                start a new run instead of resuming the active one

Default with no flag: `--status`.

Requires `research/feature-registry.md`. If missing, error with what columns it needs —
do not improvise a feature list.

Never open a gate. Recommend only; opening is the human's edit to the ledger.
