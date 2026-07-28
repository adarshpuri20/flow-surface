---
description: Plan a multi-sub-phase development phase before any code is written — landing architecture estimate, sub-phase sequence, and blast-radius declaration. Use when starting a phase, when work is large enough to need staging, or on "plan this phase".
---

# Phase Planning

Produce two artifacts before implementation begins.

**Outputs:** `plans/<phase>/PLAN.md` and `plans/<phase>/LANDING-ARCHITECTURE.md` (v0).

## Landing architecture

An *estimate* of the system state after the phase completes, written before it starts.
Its value is the diff: at each sub-phase boundary you update it with measured actuals, and
the gap between v0 and vN is the most honest signal you have about estimation quality.

```markdown
# Landing Architecture — <phase> v0 (estimate)

## Sub-phase execution sequence
| Sub | Title | Depends on | Parallel-safe | Blast radius |
| :-- | :---- | :--------- | :------------ | :----------- |

## Expected schema state
## Expected capabilities        (what the next phase may depend on)
## Expected infrastructure state
## Architecture law updates      (rules this phase adds or changes)
## Parallel execution constraints
## Open questions for the next phase
## Measured actuals              (empty at v0; filled at each boundary)
## Version history
| Version | After sub | Changed | Why |
```

## Planning rules

- **One surface concern per sub-phase.** A sub-phase touching auth *and* the data model
  is two sub-phases.
- **Name the planes each sub-phase crosses.** This list is what the gates are run against
  later. An unnamed plane is an unreviewed plane.
- **Declare blast radius up front.** The author's estimate; the reviewer may revise it.
  Declaring early forces the scope conversation before code exists.
- **State what is explicitly out of scope**, so scope creep can't be rationalised later as
  "it was implied."
- **Mark parallel-safety per sub-phase.** Only sub-phases with disjoint plane sets can run
  in concurrent lanes.
- **Do not restate standing project docs.** Reference them.

## The docs-are-the-prompt rule

Once the plan exists, execution reads it directly. Do not paste plan contents back into
the prompt — duplicated orchestration content drifts from the document and the document
loses authority.

## Gate preview

Before approval, list which review gates each sub-phase will most likely trip, and why.
A sub-phase that trips no gates is either trivial or under-analysed.

Stop after planning and get approval. Planning is a user gate.
