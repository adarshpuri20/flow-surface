# phase-conductor

Plan → execute → review → graduate, with checkpoint state that survives context
compaction and parallel isolated lanes.

```
/plugin install phase-conductor@flow-surface
/phase-conductor:phase phase-01 --plan
```

- **Landing architecture** — an estimate of the post-phase system written *before* the
  phase, then corrected with measured actuals at each boundary. The estimate-vs-actual
  delta is the honest signal.
- **Conductor state** — written after every step, so a fresh context resumes mid-phase
  instead of re-deriving where it was.
- **Simulation lanes** — parallel worktrees branching from a shared ground lane; main
  receives only cherry-picked proven code.
- **Review is mandatory** — `REVIEW_PENDING` cannot transition to `COMPLETED`.

Pairs with `flow-surface-review`, which supplies the gates. Skills: `phase-planning`,
`phase-execution`, `simulation-lanes`.
