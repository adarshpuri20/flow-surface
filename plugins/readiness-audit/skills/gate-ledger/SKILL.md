---
description: Read and maintain the persistent gate ledger and debt ledger that span audit runs and build phases. Use when checking which gates are open, recording accepted debt, or asking what the current readiness state is.
---

# Ledgers

The durable state that outlives any single run.

## Two ledgers, two owners

**`research/GATE-LEDGER.md`** — feature gate status across audit runs. Written by the
audit workflow.

```markdown
| Gate | Feature | State | Since | Evidence | Report |
| :--- | :--- | :--- | :--- | :--- | :--- |
| GATE-01 | Dashboard | UNLOCKED | audit-002 | — | audits/audit-002/GATE-01.md |
| GATE-07 | Exports | LOCKED | — | F-014, F-021 | audits/audit-004/GATE-07.md |
```

**`plans/DEBT-LEDGER.md`** — technical debt across build phases. Written by the phase
workflow.

```markdown
| ID | Item | Accepted at | Radius | Revisit trigger |
| :--- | :--- | :--- | :--- | :--- |
| D-007 | No pagination on export | phase-18 | LOW | >10k rows |
```

They cross-reference: **open debt lowers a gate's confidence score.** A gate that is
technically `UNLOCKED` but sits on three `MEDIUM` debt items is not the same as a clean one.

## Lifecycle

1. **Read on startup.** Load prior states so previously audited gates aren't re-derived.
2. **Live-update during the run.** Update each gate's row as it completes, so a status
   check shows real progress rather than a stale snapshot.
3. **Full merge at report time.** Authoritative merge that preserves gates written by
   other runs.
4. **Per-run snapshot.** A read-only copy inside the run directory, so each run is
   self-contained.

## Rules

- **A gate never opens without evidence.** Cite the run.
- **Debt requires a revisit trigger, not a date.** Dates get ignored; triggers fire.
- **Gates can close again.** A `REGRESSED` finding against an open gate closes it.
- **Append-preserving.** Never drop rows written by another run.

## The handoff boundary

The audit workflow **recommends** gate states. It does not open gates.

Opening a gate is a human edit to the ledger and to whatever feature-flag configuration
the application reads. That manual step is the **only** connection between the audit
workflow and the phase workflow. They share no state and never invoke each other.

This is deliberate: the tool that assesses readiness must not be the tool that declares
it, or the assessment becomes self-ratifying.
