# Output templates

## `code-review-<id>.md`

```markdown
# Code Review — <id>

**Reviewed:** <ISO timestamp>
**Files:** <N> changed
**Blast radius:** LOW | MEDIUM | HIGH

## Gate results
| Gate | Verdict | Findings | Notes |
| :--- | :--- | :--- | :--- |
| 1 Architecture | APPROVE | 0 | |
| 2 Security | APPROVE_WITH_NOTES | 2 | |
| ... | | | |
| 11 Regression risk | BLOCK | 1 | |

## Surface smoothness
SMOOTH | NOT SMOOTH (with accepted carry risk)

## Overall verdict
APPROVE | APPROVE_WITH_NOTES | BLOCK

## Findings by severity
### CRITICAL
### HIGH
### MEDIUM
### LOW

## Inherited debt disposition
| Item | From | Status |
| :--- | :--- | :--- |

## Known debt carried forward
| Item | Reason deferred | Revisit trigger |
| :--- | :--- | :--- |
```

Every gate row needs evidence — a file and line, a query result, a log excerpt. A gate
marked `APPROVE` with no evidence is an unreviewed gate.

## `smoothness-achieved-<id>.md`

Written **only** on convergence.

```markdown
# Smoothness Achieved — <id>

**Timestamp:** <ISO>
**Iterations:** 1 | 2 | 3
**Findings analyzed:** N
**Smooth on first pass:** N
**Required iteration:** N
**Unresolvable:** N   (0 = clean pass)

## Flow surface analysis
| Finding | Intersecting planes | Flow status | Verdict |
| :--- | :--- | :--- | :--- |
| <desc> | A<->B, B<->C | A->B SMOOTH; B->C DENT (handler swallows exception) | fix moved the discontinuity |

## Lane used
<worktree / sandbox / none>

## Accepted carry risk
| Deformation | Radius | Rating | Rationale |
| :--- | :--- | :--- | :--- |
```

Per-finding flow status uses exactly three values: `SMOOTH`, `DENT` (flow shorter than
expected), `BULGE` (flow longer than expected).
