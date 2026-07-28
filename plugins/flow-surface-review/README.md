# flow-surface-review

An 11-gate cross-file code review that checks what your change **deformed**, not just what
it touched. Zero configuration.

```
/plugin install flow-surface-review@flow-surface
/flow-surface-review:review main
```

A bug is a dent — a flow that breaks before completing. A vulnerability is a bulge — a
flow that reaches past its boundary. Tests catch dents and are blind to bulges, because
tests are written against intended behaviour.

Eleven gates in three tiers (point, region, shape), then a convergence loop that escalates
any `MEDIUM` finding whose *fix* would deform the surface. Optional `.flow-surface.json`
adapts the gates to your stack.

Skills: `flow-surface-theory`, `surface-review`.
