---
description: The geometric model behind surface review — communication planes, dents as bugs, bulges as vulnerabilities, and smoothness as the invariant. Load when classifying a defect, when judging whether a fix deformed something adjacent, or when reasoning about a case the gates do not cover.
---

# Flow Surface Theory

A geometric framework for reasoning about bugs, fixes, security, and system quality.

## 1. The core model

### Communication planes

Every pair of components that communicate defines a **plane**. The plane contains all
possible flows between them — call sequences, data exchanges, state transitions.

```
UI component    <-> API client        -> Plane A
API client      <-> service layer     -> Plane B
service layer   <-> domain logic      -> Plane C
domain logic    <-> datastore         -> Plane D
```

All planes pass through the **origin** — the system at rest, no flows active.

### The flow figure

The collection of all planes, with flows propagating outward from the origin, forms a
**closed 3D surface**. The radius at any angular position equals the length of the flow
in that direction — measured in time, or in completion.

The shape is unique to the architecture. The shape is *not* a sphere; it reflects the
density and criticality of flows in each direction.

**The shape does not matter. Smoothness matters.**

### The smoothness invariant

A perfect system has a smooth surface: continuously differentiable everywhere. No edges,
no vertices, no discontinuities. Every flow completes at exactly its expected length.

> Smoothness is the invariant. Shape is architecture-dependent.

## 2. Defects as surface deformations

### Bugs are dents

A **dent** is a surface region where flows break before completing — the traversal
terminates early, the radius at that position is shorter than ideal, and the surface
shows a local concavity. The flow is the motion; the dent is the standing feature of
the surface it reveals. Many distinct flows can reveal the same dent.

```
Expected: component -> client -> service -> domain -> response
Actual:   component -> client -> service -> ERROR (flow stopped)
                                            ^ radius short -> DENT
```

### Vulnerabilities are bulges

A **bulge** is a surface region where flows extend beyond their intended boundary —
data reaches further than it should, the radius is longer than ideal, and the surface
shows a local convexity. One over-reaching traversal is enough to raise a bulge; the
region stands whether or not any flow is currently crossing it.

```
Expected: request -> scoped read -> response
Actual:   request -> UNSCOPED read -> response containing another tenant's data
                     ^ radius long -> BULGE
```

The asymmetry is the point: **a dent fails loudly, a bulge fails silently.** A review that
only hunts dents will pass a system full of bulges, because bulges are invisible to tests
written against intended behaviour.

### Magnitude

The distance between the actual surface point and the ideal surface at the same angular
position is the defect's magnitude. Greater distance, more severe.

## 3. Fixes deform the surface

**A fix is not a patch.** It does not merely fill a dent or shave a bulge — it deforms the
surrounding surface. Pushing one point toward ideal shifts its neighbours. A fix may:

- Restore smoothness at the target point — good
- Create a new dent at an adjacent point — a new bug
- Create a new bulge at an adjacent point — a new vulnerability
- Move a discontinuity rather than remove it — the worst outcome, because it looks fixed

### The review question

> Does this fix restore **local smoothness** across all flows passing through this region?
> Or does it just move the discontinuity to an adjacent point?

This is why reviewing only the changed lines is insufficient. You must check the
**neighbouring flows** — the other planes intersecting at the fix point.

## 4. Flow packets

Each flow through a plane is a **packet** — a discrete unit of simulation with an entry
point, an expected path, an expected terminus, and an actual terminus.

If actual differs from expected, the surface is not smooth at that point.

Packets propagate like inputs through a network: input, through each layer, to output.
The "loss" at each packet is the distance between actual and ideal. Global loss is the
aggregate across all packets.

### Scoring

```
Per packet:
  intention = 1 if the flow did what it was designed to do, else 0
  stability = 1 if no neighbouring flow broke, else 0
  usability = 1 if the user-facing result is correct and comprehensible, else 0

Per region:
  region_score = mean(intention, stability, usability) over packets in region

Global:
  surface_score = weighted mean of region scores, weighted by flow criticality
```

A score of 1.0 is perfectly smooth. Anything below means dents or bulges exist somewhere.

### Parallel simulation

Each parallel agent — worktree, sandbox, or subagent — simulates a different region of
the surface. An integration step then checks that the global surface is smooth *across*
regions, which is where most cross-region defects live.

## 5. Blast radius

Blast radius classifies how much surface a change can deform:

| Radius | Meaning |
| :--- | :--- |
| `LOW` | Touches one plane. Deformation cannot propagate. |
| `MEDIUM` | Touches multiple planes, or one plane with multiple consumers. |
| `HIGH` | Touches a plane everything else depends on — auth, tenancy, persistence, identity. |

Blast radius drives the **stopping rule**, not the amount of review. Everything gets
reviewed; only `MEDIUM` and above blocks on a rough result.

## 6. The ideal surface emerges

The ideal surface is not defined upfront — it emerges from running enough flow
simulations. Each simulation is a sample. As samples accumulate, the measured surface
converges on the true one.

This means:

- Early in development the surface is rough and poorly defined. That is expected.
- Bugs found late are bugs in regions that were not simulated enough — a failure of
  simulation coverage, not of the code.
- The goal is not zero bugs. It is maximum surface coverage at minimum simulation cost.

## 7. Principles

1. **Smoothness over correctness.** A locally correct fix that breaks neighbouring flows
   is worse than a slightly imperfect fix that preserves smoothness.
2. **Simulate neighbours, not just the point.** Validate against every flow intersecting
   the fix, not only the flow that broke.
3. **Dents are bugs, bulges are vulnerabilities.** Flows that fall short reveal dents
   that break functionality; flows that overreach reveal bulges that expose data. Both
   break smoothness.
4. **Parallel simulation is how you scale.** Each agent simulates a region; integration
   validates the global surface.
5. **The ideal surface emerges — it isn't designed.** Design toward smoothness, not toward
   a predetermined shape.
6. **Fixes deform the surface.** Never assume a fix is isolated. Always check what moved.
7. **The review is a loss function.** The gates compute the loss. The smoothness loop
   checks the gradient. The goal is monotonic convergence toward smooth.

---

Operational counterpart: the `surface-review` skill turns this model into eleven concrete
gates plus a convergence loop.
