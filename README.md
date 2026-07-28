# Flow Surface

Most code review reads the diff. That is the wrong unit.

A change does not just modify the lines it touches — it **deforms the boundaries around
them**. Flow Surface Theory treats every communication boundary in a system as a plane,
and the collection of planes as a closed surface. Then it names the two ways that surface
can deform:

> **A bug is a dent.** A flow breaks before completing — it reaches less far than it should.
>
> **A vulnerability is a bulge.** A flow extends past its boundary — it reaches further than it should.

The asymmetry is the useful part: **a dent fails loudly, a bulge fails silently.** Tests
are written against intended behaviour, so they catch dents and are structurally blind to
bulges. A review that only hunts dents will pass a system full of bulges.

These plugins turn that model into something you can run.

## Three plugins, increasing commitment

| Plugin | What it does | Needs |
| :--- | :--- | :--- |
| **flow-surface-review** | 11-gate cross-file review + smoothness loop | Nothing. Works on any repo today. |
| **phase-conductor** | Plan → execute → review → graduate, with checkpointing | A `plans/` convention |
| **readiness-audit** | Versioned readiness audits, gate ledger, finding lifecycle | A feature registry |

**Start with the first one.** It is zero-config and answers a question every developer has
before merging. The other two are a whole way of working, and they're only worth adopting
if the first one earns your trust.

## Install

```
/plugin marketplace add adarshpuri20/flow-surface
/plugin install flow-surface-review@flow-surface
/reload-plugins

/flow-surface-review:review main
```

## The review

Eleven gates in three tiers, each tier feeding the next:

**Tier 1 — Point.** Is the code correct *here*?
Architecture · Security · Performance · Correctness · Test coverage

**Tier 2 — Region.** Did this deform anything *adjacent*?
Cross-file dependencies · Isolation · Data freshness · Dead paths

**Tier 3 — Shape.** Is the *system* moving toward its ideal?
Interface contract · Regression risk (neighbour deformation)

**Then the smoothness loop**, which is the part that isn't a checklist:

> Any `MEDIUM` finding whose *fix* would itself deform the surface is escalated to `BLOCK`.

A checklist asks whether the finding is severe. This asks whether the cure is worse than
the disease. The loop runs at most three iterations — three failed passes means the plan
was wrong, not the code, and it stops and asks a human rather than grinding.

### Stopping rule

| Blast radius | SMOOTH | NOT SMOOTH |
| :--- | :--- | :--- |
| `LOW` | Ship | Ship, record as debt |
| `MEDIUM` | Ship | **BLOCK** |
| `HIGH` | Ship | **BLOCK** |

Blast radius drives the stopping rule, not the amount of review. Everything gets reviewed.

## Configuration

Optional. Drop a `.flow-surface.json` at your repo root to adapt the gates to your stack —
tenancy predicate, architecture-law file, test path conventions, review agent names,
remote execution, browser adapter. Every key is optional; absent keys degrade to
stack-neutral defaults rather than failing.

Full schema: `plugins/flow-surface-review/skills/surface-review/references/config-schema.md`

## Ideas worth stealing even if you never install this

- **Dents and bulges are different geometries**, and one of them is silent.
- **Fixes deform the surface.** Never assume a fix is isolated — always check what moved.
- **Escalate on the cure, not the disease.** A `MEDIUM` finding with a surface-deforming
  fix is more dangerous than a `HIGH` finding with a clean one.
- **The ideal surface emerges, it isn't designed.** Bugs found late are failures of
  simulation coverage, not of code.
- **`BROKEN` is a distinct state from `LOCKED`.** "Not built" and "built and broken" need
  completely different responses, and most readiness reviews conflate them.
- **`REGRESSED` is a process failure, not a code failure.** The fix didn't hold, so the fix
  wasn't the problem.
- **The tool that assesses readiness must not be the tool that declares it.**

## Provenance

Extracted from a solo-maintained multi-tenant platform run through nineteen development
phases. The failure mode was never "the agent can't write the code" — it was "the agent
wrote code that quietly deformed a boundary nobody was watching." These are the guard
rails that grew around that problem.

## License

MIT
