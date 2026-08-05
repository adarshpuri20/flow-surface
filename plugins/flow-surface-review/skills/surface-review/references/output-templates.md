# Output templates

## `code-review-<id>.md`

```markdown
# Code Review — <id>

**Reviewed:** <ISO timestamp>
**Files:** <N> changed
**Blast radius:** LOW | MEDIUM | HIGH
**Gate coverage:** <N> cleared (self-reported), <N> skipped by a gate skip rule, <N> not examined (Gates ...)

## Gate results
| Gate | Verdict | Findings | Notes |
| :--- | :--- | :--- | :--- |
| 1 Architecture | APPROVE | 0 | `docs/architecture.md` §3 layering checked against every new import in `src/api/`; a repository imported straight into a route handler would have been a finding — all six route through a service. |
| 2 Security | APPROVE_WITH_NOTES | 2 | Traced all three new query call sites to the driver; a string-interpolated predicate would have been a finding — all three bind parameters. |
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

A row that clears its gate also carries a **falsifier**: the specific thing that, had it been
otherwise, would have made this a finding. Evidence says what was looked at; the falsifier
says what was being looked *for*. Both live in the Notes column, in one sentence — no new
section.

**What this rule does and does not do.** It makes a clearance *legible*: a reader can see what
the gate claims to have looked for and go check it. It provides **no protection against a
review that fabricates its falsifiers**, and it must never be read as providing any. The
artifact contains the sentence, never the work — and every discriminating observation this
rule can ask for has a zero-reading implementation through an index. Under adversarial test,
capable models produced passing falsifiers for seven gates from six `grep` invocations with
no file opened, including one that would have cleared a live SQL-injection vector while
reading exactly like an honest row. So the rule discriminates a *stated* clearance from an
*unstated* one, and nothing finer. It catches the row left blank, and the row filled with the
gate's own title. It does not catch the row filled from an index, which is what a hurried
reviewer and a fabricating one both produce — the adversarial runs above needed no intent,
only the cheapest path that satisfies this requirement. Effort, not honesty, is what the rule
is silent about. Anything downstream that treats a stated falsifier as evidence the gate was
examined has made the mistake this whole section exists to name.

Given that, write falsifiers to be **checkable**, and prefer the shapes an outside reader can
actually attack:

- **Name the search that came back empty, not the one that came back full.** "Traced all
  sixteen call sites of `quoteIdentifier`" says nothing about interpolations that *bypass*
  it, because a search for where a symbol is used cannot find where it is missing. The
  useful form names the enumeration and the subtraction: "enumerated all 19 string
  interpolations into SQL in the three new builders (`rg '\$\{' filter-sql.ts order-sql.ts
  helpers.ts`); 16 pass through `quoteIdentifier`, the other 3 are bound parameters; a raw
  one would have been a finding."
- **State the denominator, not just the numerator.** For any counterfactual that is an
  absence — nothing bypasses, no consumer reads it, nothing was dropped — give the total the
  claim ranges over and how it was derived. A ratio is checkable; a matched-instance count is
  not.
- **Chase reach the way blast-radius discipline demands of findings.** A falsifier resting on
  a call-site count must say how the count was resolved: barrel re-exports, interface
  implementations, and dependency-injection registrations all reach a component without
  containing its name.

Two shapes to avoid, both of which pass a naive reading:

- Boilerplate: "No new N+1 or unbounded loops in the reviewed diff." Negating the gate's own
  title is always boilerplate.
- A declaration wearing an examination's clothes: "`queue_max_size` (`config.py:206`) bounds
  the queue at 1000; an unbounded default would have been a finding." Real path, real symbol,
  real line, real counterfactual, every word from one `grep` — and silent on whether any
  consumer honours the bound, which is the thing that would have been the finding.

Where the clearance rests on the prior state ("nothing was removed", "this did not widen"),
the falsifier names the before-state check, exactly as before-state discipline requires of
findings: "spread-then-literal merge order byte-identical to pre-refactor
(`git show <base>:server.ts`)."

Where the instrument that would have caught it was unavailable, say so inside the falsifier
and name the substitute's own output. "`tsc` not runnable (no `node_modules`); manually traced
`T` from `augment.ts:20` into both consumers, no widening" is a weaker clearance honestly
labelled, and it stays cleared. A substitute asserted without its own locatable result is a
decline to look, and is held to the same bar as a missing capability asserted without the
invocation that proved it missing.

**Every row that clears a gate carries a falsifier**, not only `APPROVE`.
`APPROVE_WITH_NOTES` and `CONCERNS` clear the gate for merge purposes just as `APPROVE` does;
notes or worries riding along do not discharge the obligation to say what was looked for. On
a row that carries findings, the falsifier covers what the gate *cleared*, not what it
reported — an individual finding needs no falsifier of its own.

One falsifier per gate **row**, never per sub-claim. Where two gates rest on the same act of
examination, state it once and cross-reference it, restating the question rather than only
pointing: `falsifier per Gate 2 (same trace; question: does every generated predicate carry
the scope predicate)`. A cross-reference that cannot name a question distinct from the
referenced row's is a duplicate row. If the referenced row later loses its clearance, every
row pointing at it loses it too.

A row that cannot state a falsifier **has not cleared its gate**. Go back and examine it once
more. If a second pass still yields no discriminating observation, the row is
`SKIPPED(no discriminating observation obtainable)` — which counts as *not examined*, carries
a debt entry with a revisit trigger, and caps the overall verdict, exactly as a
missing-capability skip does. A gate whose stated skip rule fires is `SKIPPED` under that
rule and owes no falsifier.

The artifact header carries the resulting **Gate coverage** line (see the template above),
and the bucket mapping is below.

### Per-gate verdict vocabulary

A gate row's verdict is exactly one of:

`APPROVE` | `APPROVE_WITH_NOTES` | `CONCERNS` | `BLOCK` | `SKIPPED(reason)`

`CONCERNS` marks a substantive worry that does not block on its own; every `CONCERNS`
verdict must be backed by at least one finding in the severity sections.

`SKIPPED(reason)` is legal in exactly three cases: the gate's own stated skip rule fires; the
reason names a **missing capability** — no tooling, no credentials, dependencies not
installed, or an environment denying an examination the gate specifically requires — *and*
that missing capability leaves nothing to examine; or a second examination pass yielded no
discriminating observation, per the falsifier rule above. "Nothing looked relevant" is not a
reason. Where a substitute examination was performed, the gate stays cleared and its falsifier
names both the missing instrument and the substitute's own output, as above.

A read-only checkout is **not** by itself a missing capability. Every gate reads. It
constrains fix application, which the constrained-exit rule disposes of separately.

A missing-capability skip must name the command that failed and its error, not the condition
it infers: `SKIPPED(git show <base>:server.ts → "fatal: invalid object name"; shallow clone)`,
not `SKIPPED(no base ref available)`. A capability asserted absent without the invocation
that proved it absent is a decline to look, and is held to the same bar as "nothing looked
relevant."

A `SKIPPED` that is not a skip-rule skip goes in **Known debt carried forward** with a revisit
trigger, and caps the overall verdict at `APPROVE_WITH_NOTES`. A gate the skill marks *never
skip* is the exception: if it was not examined for any reason, the change does not ship, and
that overrides the cap.

**Verdict-to-coverage mapping**, so the header counts are reproducible. The three buckets
partition every row exactly once:

| Verdict | Bucket |
| :--- | :--- |
| `APPROVE`, `APPROVE_WITH_NOTES`, `CONCERNS`, `BLOCK` | cleared (self-reported) |
| `SKIPPED(<gate's own skip rule>)` | skipped by rule |
| `SKIPPED(missing capability)`, `SKIPPED(no discriminating observation obtainable)` | not examined |

No bucket here records *verified* examination. `cleared (self-reported)` counts rows that
assert a clearance; nothing in the artifact distinguishes an asserted clearance from an
examined one.

That tightening is the load-bearing half of the falsifier rule. Without it, a gate that
cannot state a falsifier has a free exit, and the rule selects for reviews that decline to
state rather than reviews that state.

Name the gradient it creates, because the text would otherwise hide it: the tightening buys
statements, not examinations, and the honest exit is the only priced one. A row that cannot
state a falsifier pays a verdict cap and a debt entry; a row that states one from an index
pays nothing and is, as admitted above, indistinguishable here. Do not describe the cap as
buying examination. It buys the absence of blank rows, and it leaves a standing incentive that
only an auditor holding the repository can answer.

A failed falsifier is never a `BLOCK`. It is a defect in the review, not in the code, and
blocking a merge on review prose trains models to write prose that unblocks — the precise
failure this rule exists to prevent. The consequences are to the review's own status:
the row is downgraded, the verdict capped, the gap recorded.

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
