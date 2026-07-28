# Report format

The report is not a summary — it is an input to planning. Structure it so a planning
session can consume it without re-deriving anything.

## `REPORT.md`

1. **Verdict first.** Which gates open, which stay closed. It must stand alone; nobody
   reads past the verdict for detail.
2. **Delta from the previous run.** New / resolved / persistent / regressed counts, plus
   the notable individual movements.
3. **Findings by severity**, not by feature. The reader is triaging, not browsing.
4. **Gate recommendation table.**
5. **Per-gate planning brief** for every `LOCKED` and `PARTIAL` gate.
6. **Unlock dependency graph** — which gates depend on which work.
7. **Ship scope** — the authoritative list of what ships in this version.

## Gate recommendation table

```markdown
| Gate | Current | Recommended | Blocking findings | Confidence |
| :--- | :--- | :--- | :--- | :--- |
| GATE-03 | LOCKED | UNLOCKED | — | high |
| GATE-07 | LOCKED | LOCKED | F-014, F-021 | — |
| GATE-11 | UNLOCKED | BROKEN | F-030 (REGRESSED) | — |
```

Confidence is lowered by open debt items touching that gate.

## Per-gate planning brief

For each `LOCKED` or `PARTIAL` gate:

```markdown
### GATE-NN — <feature>
- **What's missing:** <specific, not "needs work">
- **Estimated scope:** <sub-phases, or a size class>
- **Depends on:** <other gates or infrastructure>
- **Suggested phase:** <where this belongs in sequence>
```

Briefs are primary output, not an afterthought. The point of an audit is to make the next
plan writable.

## Per-gate report

One file per gate inside the run directory: UI observations (page load, network, console),
backend verification (endpoint inventory, data state, edge cases), sub-gate breakdown when
`PARTIAL`, issues found, prior findings re-checked with lifecycle state, known debt, the
planning brief, and the verdict.
