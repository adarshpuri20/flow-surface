# Example: blind review of cal.diy PR #29724

A real-world run of `flow-surface-review` against a stranger codebase, with the
resulting artifact committed verbatim.

## Target

- **Repo:** [calcom/cal.diy](https://github.com/calcom/cal.diy) (MIT community fork of Cal.com)
  at commit `ca90ca2c94536c7fac97e4e829cdfe18624c7f10`
- **Change reviewed:** [PR #29724](https://github.com/calcom/cal.diy/pull/29724) —
  `refactor(app-store): move credential query to repository pattern` (2 files, +46/−21)
- **Plugin:** `flow-surface-review` v0.1.1
- **Run date:** 2026-07-28
- **Configuration:** none — no `.flow-surface.json` in the target; every gate ran on
  stack-neutral defaults.

## Protocol

The review ran **blind**: a fresh headless session (`claude -p`) launched from the clone
root, whose prompt contained nothing but `/flow-surface-review:review ca90ca2^`. The
session had no prior context about the PR, the repo, or any hypothesis about what it
might find. It was scoped read-only with respect to existing files (no `Edit`
permission on the upstream clone).

## Why this PR

Before merging, this PR had already passed CodeRabbit's automated review and a human
"LGTM". Whatever a surface review finds beyond that is a direct answer to the question
"what does this see that checklist review doesn't?"

## Outcome

- **Verdict:** APPROVE_WITH_NOTES — 0 CRITICAL, 1 HIGH, 6 MEDIUM, 7 LOW, with
  per-gate evidence. See [`code-review-ca90ca2c94.md`](./code-review-ca90ca2c94.md).
- The review **independently and unprompted** surfaced a silent behavioral widening
  (delegation-field nulling extended to a branch that previously never received it —
  MEDIUM #2, converged on by Gates 4 and 11 separately) that neither the automated
  reviewer nor the human LGTM had flagged, then verified end-to-end that it is
  unobservable in the current tree and classified it as latent rather than live.
- It also found a HIGH architectural finding — the PR introduces a second, competing
  repository for an entity that already has a canonical, DI-registered one — with a
  fully specified, verified-non-deforming remediation.
- **There is deliberately no `smoothness-achieved` artifact.** The smoothness loop
  specified the HIGH fix, was declined the edit by the session's permission gate, and
  refused to route around it — so the change is recorded as unconverged and the debt
  ledger carries the ready-to-apply fix. Per the skill: no smoothness artifact means
  the change has not converged. The tool does not rubber-stamp its own reviews.

## Known divergences of this run (v0.1.1)

The artifact above is committed verbatim, so where the run drifted from the spec it
demonstrates, the drift is documented here rather than edited away:

- **Gate-verdict vocabulary.** Six of eleven gate rows use `CONCERNS`, which the
  output template never defines (its row vocabulary is `APPROVE` /
  `APPROVE_WITH_NOTES` / `BLOCK`, plus `SKIPPED`), and the split between `APPROVE`
  and `CONCERNS` is not consistent across identical finding profiles. Read
  `CONCERNS` as `APPROVE_WITH_NOTES`. v0.1.2 will either add `CONCERNS` to the
  template enum or normalize the runner to the documented set.
- **Per-gate counts.** The gate table's per-row counts sum higher than the
  deduplicated findings list, because cross-gate convergences are only partially
  annotated (#2 → Gates 4+11, #5 → Gates 4+6). The findings list is authoritative.
- **Loop exit.** The run ended after iteration 1 on a write-permission denial — an
  environment-constrained exit the spec's iteration protocol does not enumerate
  (iterations 2–3 assume a writable lane). "Verified non-deforming" for the HIGH's
  proposed fix therefore means statically traced, not applied.
- **Format pin.** This example reflects the v0.1.1 output format. If the skill has
  moved past v0.1.1, regenerate rather than reading this as current spec.
