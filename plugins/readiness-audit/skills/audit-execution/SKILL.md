---
description: Run a versioned production-readiness audit — classify features into gates, verify them against live behaviour, and produce a plannable report. Use when asked whether a system is ready to ship, what actually works, or to audit features against their backend support.
---

# Readiness Audit

Classify every feature into a permanent gate, verify it, and report. **Observe and
classify — do not modify code.**

**Output:** `research/audits/audit-NNN/`

## Gates as the unit of planning

Every auditable feature gets a **permanent gate ID** that persists for the product's life.
Future work targets gate IDs, not feature names — names change, IDs don't.

| State | Meaning |
| :--- | :--- |
| `UNLOCKED` | Production-ready, ships in the current version |
| `LOCKED` | Deliberately gated; needs future work to unlock |
| `PARTIAL` | Some sub-capabilities work, others locked; has a sub-gate breakdown |
| `BROKEN` | Backend exists, integration is broken. Must fix before launch |

`BROKEN` is the state most audits lack, and the most useful one. "Not built" and "built and
broken" need completely different responses.

## The feature registry

The handler **never hardcodes a feature list.** It reads `research/feature-registry.md`,
a human-maintained table. If it's missing, error and say so — do not improvise a list, or
the audit silently scopes itself to whatever the agent happened to notice.

| Column | Purpose |
| :--- | :--- |
| Gate ID | Permanent identifier |
| Feature | Human-readable name |
| Nav Route | UI route, or `—` for none |
| Backend Module | Module for endpoint discovery, or `—` |
| Context Doc | Optional domain documentation |
| Built By | Which phases built it, for cross-referencing reviews |
| Batch | Grouping for execution |
| Notes | Context for the auditor |

### Route classification drives verification

**`Nav Route: —` means backend-only.** Verify through shell, datastore, and logs. Do not
attempt UI verification — that mistake wastes an entire audit cycle.

**A real route means full-stack.** Verify through the browser adapter *and* the backend.

## Discovery before verification

For each gate, run two discovery passes in parallel, in isolated contexts:

1. **Backend discovery** — read the *deployed* module, service files, schema, and tests.
   Return an endpoint inventory, dependencies, and health.
2. **Codebase discovery** — read prior review files, the debt ledger, previous audit
   reports, and UI components. Return verdicts, open debt, prior findings, and structure.

Merge both into a prioritised test plan, then execute it. Running discovery in subagents
keeps raw file contents out of the main context; the main context gets condensed reports.

**Prior findings and open debt are high-priority re-verification targets.** They are the
most likely things to still be broken.

## Finding lifecycle

Classify each finding by comparing against the previous audit run:

| State | Meaning |
| :--- | :--- |
| `NEW` | Not in the previous audit |
| `PERSISTENT` | Present before, still unresolved |
| `RESOLVED` | Present before, verified fixed |
| `REGRESSED` | Previously resolved, present again |

`REGRESSED` is the highest-signal state in the system. A regression means the fix did not
hold — that is a process failure, not a code failure, and it escalates differently.

## Versioned, immutable runs

Each run creates `research/audits/audit-NNN/`. **Never edit a previous run.** The diff
between runs is the signal; editing history destroys it.

Resume an `ACTIVE` run rather than starting a new one. Only an explicit `--fresh` starts
over. State accumulates across invocations and is never cleared mid-run.

## Evidence discipline

A finding needs an artifact: a query result, a response body, a log line, a console error.
"The code appears to handle this" is a reading of the code, not a finding. If it could not
be verified, record it as `UNVERIFIED` with the reason — that is honest and still useful.

See `references/report-format.md` for the report and planning-brief structure.
