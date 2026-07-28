---
description: Run the 11-gate Flow Surface review on the current change.
---

Run a surface review for: $ARGUMENTS

Load the `surface-review` skill and follow it.

Resolve the file list in this order:
1. Explicit paths in $ARGUMENTS
2. A base ref in $ARGUMENTS (e.g. `main`, `HEAD~3`) -> `git diff --name-only <ref>..HEAD`
3. Default -> `git diff --name-only HEAD` plus staged and untracked files

If the diff is empty, say so and stop rather than reviewing the whole repository.

Read `.flow-surface.json` from the repo root if present. If absent, run stack-neutral
defaults — do not ask the user to create one first.

Run all three tiers, then the smoothness loop. Report the verdict and where the artifacts
were written.
