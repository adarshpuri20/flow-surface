---
description: Plan, execute, review, or commit a development phase.
---

Run the phase conductor for: $ARGUMENTS

Positional: a phase identifier (e.g. `phase-04`). Flags select the stage:

- `--plan`     load `phase-planning`; produce PLAN.md + LANDING-ARCHITECTURE.md v0, then stop for approval
- `--validate` check plan assumptions against the current codebase; write the drift file
- `--lanes`    load `simulation-lanes`; create parallel worktrees and print the per-lane commands
- `--review`   load `surface-review`; run all gates and the smoothness loop
- `--commit`   sync sweep, docs update, landing architecture update, commit
- `--fresh`    delete sub-phase conductor state (the plan survives); with `--plan`, delete both
- (no flag)    read the conductor state and resume from the recorded step

Refuse `--commit` when state is `REVIEW_PENDING` — review is mandatory. Say so plainly.

Read the plan document directly; do not restate its contents in your reasoning.
