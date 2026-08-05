# Rule-shipping discipline

Adopted 2026-08-04, after v0.1.7 shipped a rule whose claimed derivation from the
formalism failed refutation. The rule:

> A rule may ship on operational evidence alone, provided it claims only operational
> grounding. Any rule claiming to derive from the formalism must have the derivation
> checked before it ships, and the check must be run as a refutation attempt.

The distinction matters because the same discipline imposes three different obligations,
illustrated by the three rules shipped in v0.1.5 through v0.1.7:

| Rule | Grounding claimed | Obligation |
| :--- | :--- | :--- |
| Before-state discipline (v0.1.5) | Operational only | None beyond stating the evidence. Ships as-is. |
| Blast-radius discipline (v0.1.6) | Plausibly derives (Theorem 2 bounds a single edge *addition*'s deformation to `Anc(u) × Desc(v)`; the deletion side is Theorem 3's territory, and its corresponding box, while derivable from Theorem 3's proof, is stated nowhere in the paper) | The derivation must be checked as a refutation attempt before the text may say "derives." Until then it, too, claims operational grounding only. |
| Orthogonality (v0.1.7, renamed double-counting in v0.1.8) | Claimed a formal mechanism (`supp(F)`, disjoint/overlapping support) it never had | The check ran after shipping and refuted it: findings are not graph objects, entries with disjoint support can share a single cause (FORMAL.md §5b Model B — one edge reversal produces both the bulge and the dent), one entry can carry many independent witnesses (the paper's stated quantifier asymmetry: a single dent may be witnessed by the failure of many distinct paths), and ℓ¹ admits no inner product for "orthogonality" to name. v0.1.8 strips the apparatus and keeps what the runs showed firing — the sign test, same-rule collapse, and merged-region pricing now gated by the decision/fix tests — with scope stated as heuristic. |

Two companion rules, from the same incident:

- **The check is a refutation attempt, not a confirmation.** The reviewer is told to
  default to "this does not follow" and pointed at the weakest seam.
- **What fired is what ships.** In both blind runs, the observable invocations (sign-test
  merge, same-rule collapse, per-region dedup annotations) were surface-level reads;
  the formal support machinery contributed nothing observable. Text that did no work in
  the evidence does not belong in the rule.

One tension in the table above, named rather than hidden: the decision test and fix test
shipped in v0.1.8 fired in neither blind run — the runs fired on the sign test, same-rule
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
