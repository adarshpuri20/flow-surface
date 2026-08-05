# Rule-shipping discipline

Adopted 2026-08-04, after v0.1.7 shipped a rule whose claimed derivation from the
formalism failed refutation. The rule:

> A rule may ship on operational evidence alone, provided it claims only operational
> grounding. Any rule claiming to derive from the formalism must have the derivation
> checked before it ships, and the check must be run as a refutation attempt.

The distinction matters because the same discipline imposes different obligations according
to the grounding a rule claims, illustrated by the four rules shipped from v0.1.5 through
v0.1.9 and by one refuted before a line of it was written:

| Rule | Grounding claimed | Obligation |
| :--- | :--- | :--- |
| Before-state discipline (v0.1.5) | Operational only | None beyond stating the evidence. Ships as-is. |
| Blast-radius discipline (v0.1.6) | Plausibly derives (Theorem 2 bounds a single edge *addition*'s deformation to `Anc(u) × Desc(v)`; the deletion side is Theorem 3's territory, and its corresponding box, while derivable from Theorem 3's proof, is stated nowhere in the paper) | The derivation must be checked as a refutation attempt before the text may say "derives." Until then it, too, claims operational grounding only. |
| Orthogonality (v0.1.7, renamed double-counting in v0.1.8) | Claimed a formal mechanism (`supp(F)`, disjoint/overlapping support) it never had | The check ran after shipping and refuted it: findings are not graph objects, entries with disjoint support can share a single cause (FORMAL.md §5b Model B — one edge reversal produces both the bulge and the dent), one entry can carry many independent witnesses (the paper's stated quantifier asymmetry: a single dent may be witnessed by the failure of many distinct paths), and ℓ¹ admits no inner product for "orthogonality" to name. v0.1.8 strips the apparatus and keeps what the runs showed firing — the sign test, same-rule collapse, and merged-region pricing now gated by the decision/fix tests — with scope stated as heuristic. |
| Clearance discipline — the findings-only observation (v0.1.9) | Operational, warranted directly | None beyond stating the evidence: two independent blind audits, given a prior run's clearances and its target repository and told nothing about what to look for, each recovered a defect that run had explicitly cleared, and each surfaced a second defect no agent in the same run's twelve-agent verification pass had examined. The clearances supplied the enumeration of where to read, not the defects. Ships as-is. |
| Clearance discipline — the falsifier requirement on clearing rows (v0.1.9) | Operational **for the deficiency only** — shipped runs contain clearing rows citing nothing. **No evidence of any kind for the remedy.** | Must never be cited on the audits warranting the row above; they support a separate instrument re-reading code, not this sentence rule. Three rounds of adversarial hardening failed to close its ceiling: capable models produced passing falsifiers for seven gates from six greps with no file opened, one of which would have cleared a live injection vector. It ships as a legibility rule that discriminates a stated clearance from an unstated one and nothing finer, with that limit stated in the rule itself. Two constraints travel with it: the coverage line must not count falsifier-bearing rows as verified, and no downstream rule may condition on a falsifier's presence as evidence of examination. |
| Dent/bulge inversion on the review surface (proposed 2026-08-05, **never shipped**) | Claimed the formalism's detection asymmetry inverts when the reviewed system is the review itself | Refuted before a line was written, which is the discipline working as intended. Four legs. What the paper *proves* is polarity — Theorem 1: additions create only bulges, deletions only dents. The detection claim glossed onto it, "tests catch dents and are blind to bulges," is proved nowhere; it appears in Theorem 1's Significance note and again in the summary table, derived from monotonicity, and under that grounding it cannot invert. Over-pricing has no image in `D` either: entries are confined to {−1, 0, +1} (Definition 3), recording polarity and never magnitude, and §8 puts pricing outside the matrix explicitly ("nothing in `D` assigns blame for it"), so a correctly located and wrongly valued finding leaves `D` identical in both worlds. The quantifier asymmetry cannot transfer: its force comes from path multiplicity between a fixed pair, and every gate-to-region path is a single hop, leaving ∃ and ∀ coextensive. And `A*`, the intended architecture the whole matrix is relative to, is undeclarable for a review at review time — the intended examination set is exactly the set of regions nobody knew to enumerate, which is the omissions under test, and the only declaration available is the review's own coverage table, the object being audited. §8 gives the consequence: "if the declaration is wrong or absent, `D` measures distance to the wrong target," so no entry is trustworthy, not merely the reading leg 2 already denies it. Diagnosis: the same failure as the orthogonality row, one level up — verdicts are assertions *about* `D` being promoted to entries *of* `D`. What shipped instead is the input-shaped operational statement in the review skill, which claims no grounding and needed none. |

Two companion rules, from the same incident:

- **The check is a refutation attempt, not a confirmation.** The reviewer is told to
  default to "this does not follow" and pointed at the weakest seam.
- **What fired is what ships.** In both blind runs, the observable invocations (sign-test
  merge, same-rule collapse, per-region dedup annotations) were surface-level reads;
  the formal support machinery contributed nothing observable. Text that did no work in
  the evidence does not belong in the rule.

Two tensions in the table above, named rather than hidden. The falsifier requirement fired in
neither blind run either, and unlike the guards below it has no refutation evidence for its
remedy — only for the deficiency it addresses. It is therefore a third exception to "what
fired is what ships," and the weakest thing in the table; it is shipped because a clearance
that cites nothing cannot be argued with at all, and rejected as protection against anything.

And the decision test and fix test shipped in v0.1.8 fired in neither blind run — the runs fired on the sign test, same-rule
collapse, and merged pricing. "What fired is what ships" governs *behaviors*; the two
tests ship as the refutation-demanded *guard* on a behavior that did fire (merged
pricing), replacing the refuted support mechanism as its gate. Guards ship on refutation
evidence; behaviors ship on run evidence.

If a formally grounded grouping rule is ever wanted, it starts from shared edge edits:
Theorem 2 gives the deformation box for a single edge addition, and Theorem 3 — which
characterizes exactly which entries a single edge deletion flips — induces, for that
narrow case, the set of entries one fix clears of bulges (the same deletion can also
*create* dents at intended pairs, which any soundness argument for max-pricing must also
exclude). That induced co-remediation set (the term is ours, not the paper's) applies
only to fixes that are one edge deletion. The generalization to arbitrary edits is
unproven. It lands in the paper before it lands in the plugin.
