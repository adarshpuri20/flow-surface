---
description: Run sub-phases in parallel isolated lanes (git worktrees or sandboxes) and graduate proven code to the main branch. Use when a phase has parallel-safe sub-phases, when work must not touch main until reviewed, or on "set up the sim lanes".
---

# Simulation Lanes

Parallel isolated implementation lanes, with graduation by cherry-pick.

## The graduated workflow

The lane is the **primary** implementation surface. Main receives only proven code.

```
plan -> ground lane (shared infra) -> parallel landing lanes -> verify -> merge -> review -> cherry-pick to main
```

This is not a safety net bolted onto normal development. It is the development path.
Work done directly on main has skipped the thing that makes graduation mean anything.

## Topology

A **ground** lane holds changes every landing needs — migrations, shared infrastructure,
common types. Landing lanes branch from ground, so they inherit prepared infrastructure
instead of each re-deriving it.

```
main (frozen baseline)
 └── ground              shared infra + migrations
      ├── landing-a      sub-phase A
      ├── landing-b      sub-phase B
      └── landing-c      sub-phase C
```

Cap concurrency at **4 landings**. Beyond that, port and datastore allocation collides and
verification stops being trustworthy. If a phase has more parallel-safe sub-phases than
that, sequence them in waves.

## Resource allocation

Each lane needs its own service port and its own datastore namespace, recorded in the plan.
Claude Code's native worktree support (`claude --worktree`) can replace manual setup.

```bash
git worktree add ../lane-ground -b sim/ground
git worktree add ../lane-a      -b sim/landing-a sim/ground
```

## Verification before merge

Run before merging any lane. This is the step that makes parallel work safe.

1. **Baseline capture** — record main's health, row counts, queue depths, and migration
   revision *before* touching anything.
2. **Per-lane regression check** — start each lane's service, confirm health, run its tests.
3. **Cross-lane contract check** — where two lanes touched the same plane, verify they
   agree. This is where parallel work actually breaks, and no single lane can detect it.
4. **Isolation check** — re-check the baseline. If lane work altered production state, the
   isolation is broken and the whole run is void. Compare every captured value, and confirm
   main's commit hash is unchanged.

## Merge and graduate

Merge ground first, then each landing, into a dedicated merge lane. Run the full
`surface-review` on the **merged** result — not on each lane separately, because
deformations at lane intersections only exist after the merge.

Cherry-pick to main only after the smoothness artifact exists.

## Lane states

`READY` → `EXECUTING` → `SIM_COMPLETED` → `VERIFIED` → `GRADUATED`

Record state per lane. An unrecorded lane is one someone re-runs by accident.
