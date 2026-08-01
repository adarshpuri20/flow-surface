---
description: Run the 11-gate Flow Surface review on a set of changed files, then the smoothness convergence loop. Use before merging a branch, before shipping a phase, when asked for a thorough or cross-file code review, or when a fix might have broken something adjacent.
---

# Surface Review — 11 Gates + Smoothness Loop

Review a change against the surface it deformed, not just the lines it touched.

**Input:** a list of changed files (from `git diff --name-only <base>..HEAD`, or supplied).
**Output:** `code-review-<id>.md` and, on convergence, `smoothness-achieved-<id>.md`.

## Configuration

Read `.flow-surface.json` from the repo root if present. It adapts the gates to the
project. See `references/config-schema.md`. Every key is optional — with no config file,
the gates degrade to stack-neutral defaults and still run.

## Tier structure

The gates run in three tiers, each tier consuming the previous tier's findings. Run each
tier's gates **in parallel as subagents** where the harness supports it — each reviewer
gets a clean context window, which matters because the implementing session has usually
consumed most of the main one. Where subagents aren't available, run them sequentially.

| Tier | Question | Gates |
| :--- | :--- | :--- |
| 1 — Point | Is the code correct *here*? | 1–5 |
| 2 — Region | Did this deform anything *adjacent*? | 6–9 |
| 3 — Shape | Is the *whole system* moving toward its ideal? | 10–11 |
| Loop | Did our fixes deform anything? | Smoothness |

Skip rules are per-gate and stated below. A skipped gate is recorded as `SKIPPED` with its
reason — never silently omitted.

Per-gate verdicts come from a fixed vocabulary: `APPROVE`, `APPROVE_WITH_NOTES`,
`CONCERNS` (a substantive worry that does not block on its own — must be backed by at
least one finding), `BLOCK`, or `SKIPPED(reason)`.

---

## Tier 1 — Point quality

**Gate 1 — Architecture.** Does the implementation follow the project's stated
architectural rules? Are patterns consistent with existing conventions? Is separation of
concerns correct? Are new abstractions justified or over-engineered? Do data flows match
the design document? Any circular dependencies or tight coupling?
*Reads:* the architecture-law file from config, the design doc for this change.

**Gate 2 — Security.** Auth enforcement, input validation, injection vectors, secrets
exposure, CORS, role checks, trust-boundary enforcement.
*Skip if:* no endpoint, auth, or input-handling code changed.

**Gate 3 — Performance.** N+1 query patterns, missing indexes, unbounded fetches or loops,
missing pagination, large payload serialization, connection-pool exhaustion, timeout risk
on any execution-limited runtime.

**Gate 4 — Correctness.** Logic errors, off-by-one, null and error handling, async
correctness, type discipline, language-idiomatic review per file type. Run one reviewer
per language present in the diff.

**Gate 5 — Test coverage.** For each changed source file, locate its test file using the
`testPathPatterns` config. Does a test exist? Do the tests cover the *new* paths? Are
there edge cases in the source with no test? Are there tests that import the changed file
but weren't updated?
*Verdict:* `APPROVE` at or above the configured threshold, `BLOCK` if critical paths are
untested.

---

## Tier 2 — Region quality

Tier 2 receives Tier 1's findings to avoid duplicate work.

**Gate 6 — Cross-file dependencies.** Import-chain depth, circular references, missing
re-exports, orphaned imports, dependency-direction violations.

**Gate 7 — Isolation.** Every query, cache key, and file path that should carry the
project's `scopePredicate` actually carries it. Check for leak vectors, shared-state
contamination, missing filter clauses, cross-scope cache pollution. Read the *generated*
query, not the ORM call.
*Skip if:* no data access or endpoints changed. *Never skip* on a multi-tenant project
when either changed.

**Gate 8 — Data freshness.** Stale cache risk, watermark advancement gaps, missing
invalidation, TTL mismatches, eventual-consistency windows that violate the UX contract.

**Gate 9 — Dead paths.** Unreachable code after early returns, unused exports, dead
feature flags, orphaned utilities, commented-out blocks, unused imports.

---

## Tier 3 — Shape quality

**Gate 10 — Interface contract.** Does the response shape match what consumers expect?
Loading, error, and empty states covered? Pagination contract consistent? Field naming
conventional? Backward compatible?

**Gate 11 — Regression risk (neighbour deformation).** For each changed file, identify its
**neighbours**: files that import it, files it imports, files sharing its route namespace,
files sharing its datastore tables. For each neighbour ask: could this change break it? Is
the changed interaction pattern tested? Is there an integration test on the boundary?

This is the gate that operationalises "fixes deform the surface."

---

## The Smoothness Loop

The smoothness loop is not a gate — it is a convergence loop that runs *after* all
eleven gates.

### Surface-aware MEDIUM escalation

> Any `MEDIUM` finding whose proposed fix would itself deform the surface — i.e. the fix
> introduces new regression risk in neighbouring flows — is **escalated to BLOCK**.
> The reasoning must be written down.

This is the rule that makes the whole framework more than a checklist. A checklist asks
whether the finding is severe. This asks whether the *cure* is worse than the disease.

### Iteration protocol (capped at 3)

**Iteration 1.** Collect all `CRITICAL` and `HIGH` findings from the eleven gates. Apply
fixes. Re-trace every affected flow surface.
→ `SMOOTH`: write the smoothness artifact, proceed.
→ `NOT SMOOTH`: iteration 2.

**Iteration 2.** Isolate the fix attempt in a throwaway lane — a git worktree or sandbox —
so the comparison is clean. Apply, test, compare the surface before and after.
→ `SMOOTH`: bring the fix back to the working branch, write the artifact.
→ `NOT SMOOTH`: iteration 3.

**Iteration 3 (final).** Stop attempting. Three failed passes means the plan was wrong,
not the code. Document in the review file:
- which flow surfaces remain non-smooth
- why the fix creates worse deformation than the original finding
- a recommended deferral with a carry-risk rating

Then **stop and present to the human** as an explicit gate. The human decides: accept the
carry risk, or block for manual intervention. Do not loop a fourth time.

### Constrained exit

When the environment denies fix application — a write-permission gate, a read-only
checkout — do not simulate convergence and do not keep looping: record the change as
**NOT CONVERGED** with the constraint stated, specify the fix in the artifact instead
of applying it, and let the stopping rule dispose of the result. A live instance is the
marketplace repo's `examples/cal-diy-pr-29724/` run, which exited exactly this way.

### Stopping rule

| Blast radius | SMOOTH | NOT SMOOTH |
| :--- | :--- | :--- |
| `LOW` | Ship | Ship, record in the debt ledger |
| `MEDIUM` | Ship | **BLOCK** |
| `HIGH` | Ship | **BLOCK** |

A `BLOCK` is not advisory.

---

## Outputs

Two artifacts. Templates in `references/output-templates.md`.

- `code-review-<id>.md` — all gate results, findings by severity, inherited-debt
  disposition, known debt carried forward.
- `smoothness-achieved-<id>.md` — written **only** on convergence. Records iterations
  used, planes traced, and per-plane flow status.

Before writing the artifact, run a **self-consistency check**: the per-gate finding
counts in the gate table must reconcile with the deduplicated findings-by-severity
sections. Annotate every cross-gate convergence explicitly (finding N → Gates X+Y) so
the two views sum consistently; the findings list is authoritative.

**No smoothness artifact means the change has not converged.** Do not merge on the
strength of passing gates alone — the gates find deformations, the loop proves they were
resolved without creating new ones.
