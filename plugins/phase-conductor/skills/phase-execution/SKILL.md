---
description: Execute a planned phase with checkpoint-based state that survives context compaction, then hand off to review and commit. Use after a plan exists, to resume interrupted phase work, or on "continue the phase".
---

# Phase Execution

Drive a planned phase from implementation to commit, resuming cleanly after interruption.

## Why checkpoints exist

Long agentic sessions get compacted. The conductor state is what lets a fresh context pick
up mid-phase without re-deriving where it was. It is written **after every step**, not at
the end — a state file that only exists at completion has no value.

`plans/<phase>/.conductor-state.json`:

```json
{
  "phase": "phase-04",
  "sub_phase": "04B",
  "state": "EXECUTING",
  "current_step": 3,
  "total_steps": 7,
  "steps": [
    { "n": 1, "title": "...", "status": "done", "files_modified": ["..."] }
  ],
  "user_gates_passed": ["plan-approval"],
  "notes": "..."
}
```

## State machine

| State | Meaning | Next |
| :--- | :--- | :--- |
| `PLANNED` | Plan approved, no sub-phase started | `VALIDATED` or `EXECUTING` |
| `VALIDATED` | Design checked against the real codebase; drift recorded | `EXECUTING` |
| `EXECUTING` | Implementation in progress; resumable at `current_step` | `REVIEW_PENDING` |
| `REVIEW_PENDING` | Built; review not yet run | `REVIEWED` |
| `REVIEWED` | Gates passed and smoothness converged | `COMPLETED` |
| `COMPLETED` | Committed | next sub-phase, or `PHASE_COMPLETE` |

**Review is mandatory.** `REVIEW_PENDING` cannot transition directly to `COMPLETED`.
Refuse the commit and say why.

## Validation before execution

Check the plan's assumptions against the codebase as it exists now, and write a drift file
recording what is aligned, what drifted, what is missing, and what decisions that forces.
Plans age. A plan written three sub-phases ago has assumptions that are quietly false.

## Execution loop

Per step: implement, verify, record `files_modified`, write state, continue. Stop only at
declared user gates. Between gates, execute continuously — the value of a conductor is
that it does not stop to ask permission for work already approved in the plan.

If the plan turns out to be wrong, **stop and revise the plan**. Do not improvise past it:
improvised work has no declared blast radius and cannot be reviewed against anything.

## Sub-phase boundary

On `COMPLETED`, before starting the next sub-phase:

1. Update the landing architecture from v(n-1) to v(n) with measured actuals.
2. Record the estimate-vs-actual delta and what caused it.
3. Carry forward known debt to the next sub-phase's review as inherited debt.
4. Advance to the next sub-phase in the sequence, or mark `PHASE_COMPLETE`.

Skipping the landing update is the single most common way this workflow decays: the
estimate stops being corrected, and the next phase inherits a fiction.

## Handoff to review

At `REVIEW_PENDING`, invoke the `surface-review` skill with the accumulated file list from
`steps[].files_modified`. See `references/deployment-sync.md` if the project builds
somewhere other than where it commits.
