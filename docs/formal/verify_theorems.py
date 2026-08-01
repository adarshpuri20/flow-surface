#!/usr/bin/env python3
"""
verify_theorems.py -- property-based verification of FORMAL.md's four theorems.

WHY THIS EXISTS
  verify.py asserts that ONE seven-node example satisfies the theorems. That checks an
  instance, not a theorem: a subtly wrong statement would pass, because the instance was
  built alongside the claim. This script tests the theorems as universally-quantified
  properties over randomly generated graphs, including adversarial edge cases, and
  verifies Theorem 3 by independent path enumeration rather than by the definition it
  is stated in (which would be circular).

Standalone. Asserts only. Produces no figures and no new claims for the paper.
Run: python3 verify_theorems.py
"""
import numpy as np, itertools, random, sys

RNG = np.random.default_rng(20260731)
random.seed(20260731)

# ---------------------------------------------------------------- core
def closure(A):
    n = A.shape[0]
    R = (A | np.eye(n, dtype=int)).astype(int)
    for k in range(n):
        R = R | (np.outer(R[:, k], R[k, :]) > 0).astype(int)
    return R

def rand_graph(n, p, self_loops=True):
    A = (RNG.random((n, n)) < p).astype(int)
    if not self_loops:
        np.fill_diagonal(A, 0)
    return A

def all_paths_use_edge(A, i, j, u, v, cap=200000):
    """Independent check: does EVERY simple i->j path traverse (u,v)?
    Enumerates simple paths by DFS. Returns (any_path_exists, all_use_edge)."""
    n = A.shape[0]
    found_any, found_avoiding = False, False
    stack = [(i, [i], set([i]))]
    steps = 0
    while stack:
        steps += 1
        if steps > cap:
            return None, None                      # too big; caller skips
        node, path, seen = stack.pop()
        if node == j and len(path) > 0:
            found_any = True
            uses = any(path[k] == u and path[k+1] == v for k in range(len(path)-1))
            if not uses:
                found_avoiding = True
            if found_avoiding:
                return True, False
            continue
        for w in range(n):
            if A[node, w] and w not in seen:
                stack.append((w, path + [w], seen | {w}))
    if i == j:
        found_any = True                            # reflexive
    return found_any, (found_any and not found_avoiding)

# ---------------------------------------------------------------- tests
FAIL = []
def check(name, cond, detail=""):
    if not cond:
        FAIL.append(f"{name}: {detail}")

def t1_polarity(trials=4000):
    """Pure additions create no dents; pure deletions create no bulges; R is monotone."""
    for _ in range(trials):
        n = RNG.integers(2, 11)
        p = RNG.choice([0.05, 0.15, 0.3, 0.5, 0.8])
        Astar = rand_graph(n, p)
        Rstar = closure(Astar)
        # pure addition
        add = Astar.copy()
        for _ in range(RNG.integers(1, 4)):
            add[RNG.integers(n), RNG.integers(n)] = 1
        D = closure(add) - Rstar
        check("T1 add->no dents", (D >= 0).all(), f"n={n} D.min={D.min()}")
        check("T1 monotone(add)", (closure(add) >= Rstar).all())
        # pure deletion
        dele = Astar.copy()
        ones = list(zip(*np.where(Astar == 1)))
        for (a, b) in random.sample(ones, min(len(ones), int(RNG.integers(1, 4)))):
            dele[a, b] = 0
        D2 = closure(dele) - Rstar
        check("T1 del->no bulges", (D2 <= 0).all(), f"n={n} D.max={D2.max()}")
        check("T1 monotone(del)", (closure(dele) <= Rstar).all())

def t2_localization(trials=4000):
    """Single-edge add: closed form holds and support(ΔR) ⊆ Anc(u) × Desc(v)."""
    for _ in range(trials):
        n = RNG.integers(2, 12)
        A = rand_graph(n, RNG.choice([0.05, 0.15, 0.3, 0.6]))
        R = closure(A)
        u, v = int(RNG.integers(n)), int(RNG.integers(n))
        A2 = A.copy(); A2[u, v] = 1
        R2 = closure(A2)
        pred = (R | (np.outer(R[:, u], R[v, :]) > 0)).astype(int)
        check("T2 closed form", np.array_equal(pred, R2), f"n={n} u={u} v={v}")
        anc = set(np.where(R[:, u] == 1)[0]); desc = set(np.where(R[v, :] == 1)[0])
        supp = set(map(tuple, np.argwhere(R2 - R != 0)))
        check("T2 support ⊆ Anc×Desc", supp <= {(i, j) for i in anc for j in desc},
              f"n={n} extra={supp - {(i,j) for i in anc for j in desc}}")
        check("T2 bound", len(supp) <= len(anc)*len(desc))

def t2_multiedge_counterexample():
    """MINIMAL counterexample to the naive multi-edge union bound (locked in).
    n=3, A* empty, add (0,1) and (1,2). Pair (0,2) is deformed but lies in neither
    Anc(0)xDesc(1) = {(0,1)} nor Anc(1)xDesc(2) = {(1,2)}, because the witnessing path
    chains through BOTH new edges. The cross term is structurally absent."""
    A = np.zeros((3, 3), int); R = closure(A)
    A2 = A.copy(); A2[0, 1] = 1; A2[1, 2] = 1; R2 = closure(A2)
    supp = set(map(tuple, np.argwhere(R2 - R != 0)))
    box = set()
    for (u, v) in [(0, 1), (1, 2)]:
        box |= {(i, j) for i in np.where(R[:, u] == 1)[0] for j in np.where(R[v, :] == 1)[0]}
    check("T2-CE deformed pair exists outside naive box", (0, 2) in supp - box,
          f"supp={supp} box={box}")

    # The CORRECTED bound: apply Theorem 2 sequentially, recomputing the closure
    # between steps, so each step is genuinely a single-edge addition.
    Rk = R.copy(); Ak = A.copy(); seq_box = set()
    for (u, v) in [(0, 1), (1, 2)]:
        seq_box |= {(i, j) for i in np.where(Rk[:, u] == 1)[0] for j in np.where(Rk[v, :] == 1)[0]}
        Ak[u, v] = 1; Rk = closure(Ak)
    check("T2-CE sequential bound covers support", supp <= seq_box,
          f"missing={supp - seq_box}")

def t2_sequential_bound(trials=1500):
    """The corrected multi-edge rule: union of per-step boxes, each computed in the
    closure AFTER the previous steps. Should hold universally."""
    viol = 0
    for _ in range(trials):
        n = RNG.integers(3, 10)
        A = rand_graph(n, RNG.choice([0.08, 0.2, 0.4]))
        R0 = closure(A)
        adds = [(int(RNG.integers(n)), int(RNG.integers(n))) for _ in range(int(RNG.integers(2, 5)))]
        Ak, Rk, box = A.copy(), R0.copy(), set()
        for (u, v) in adds:
            box |= {(i, j) for i in np.where(Rk[:, u] == 1)[0] for j in np.where(Rk[v, :] == 1)[0]}
            Ak[u, v] = 1; Rk = closure(Ak)
        supp = set(map(tuple, np.argwhere(Rk - R0 != 0)))
        if not supp <= box:
            viol += 1
    return viol

def t2_multiedge(trials=1500):
    """Does the localization bound generalize to multi-edge changes as a UNION?
    (FORMAL.md states Thm 2 for a single edge; §5 and §5b involve several.)"""
    viol = 0
    for _ in range(trials):
        n = RNG.integers(3, 10)
        A = rand_graph(n, RNG.choice([0.08, 0.2, 0.4]))
        R = closure(A)
        adds = [(int(RNG.integers(n)), int(RNG.integers(n))) for _ in range(int(RNG.integers(2, 5)))]
        A2 = A.copy()
        for (u, v) in adds: A2[u, v] = 1
        R2 = closure(A2)
        box = set()
        for (u, v) in adds:
            anc = np.where(R[:, u] == 1)[0]; desc = np.where(R[v, :] == 1)[0]
            box |= {(i, j) for i in anc for j in desc}
        supp = set(map(tuple, np.argwhere(R2 - R != 0)))
        if not supp <= box:
            viol += 1
    return viol

def t3_fix_deformation(trials=900):
    """Single-edge delete: (i,j) flips 1->0 IFF every i->j path used that edge.
    'Every path' verified by INDEPENDENT enumeration, not by recomputing closure."""
    tested = 0
    for _ in range(trials):
        n = RNG.integers(2, 7)                       # small: enumeration is exponential
        A = rand_graph(n, RNG.choice([0.2, 0.35, 0.5]), self_loops=False)
        ones = list(zip(*np.where(A == 1)))
        if not ones: continue
        u, v = random.choice(ones)
        R = closure(A)
        A2 = A.copy(); A2[u, v] = 0
        R2 = closure(A2)
        for i in range(n):
            for j in range(n):
                if i == j: continue
                flipped = (R[i, j] == 1 and R2[i, j] == 0)
                exists, all_use = all_paths_use_edge(A, i, j, u, v)
                if exists is None: continue
                tested += 1
                check("T3 iff", flipped == (R[i, j] == 1 and all_use),
                      f"n={n} ({i},{j}) edge=({u},{v}) flipped={flipped} all_use={all_use}")
    return tested

def t4_laplacian(trials=3000):
    """x^T L x equals the number of boundary-crossing undirected edges."""
    for _ in range(trials):
        n = RNG.integers(2, 12)
        A = rand_graph(n, RNG.choice([0.1, 0.25, 0.5]), self_loops=False)
        x = RNG.integers(0, 2, n)
        S = ((A + A.T) > 0).astype(int); np.fill_diagonal(S, 0)
        L = np.diag(S.sum(axis=1)) - S
        energy = int(x @ L @ x)
        cut = int(sum(S[i, j] * (x[i] != x[j]) for i in range(n) for j in range(n)) / 2)
        check("T4 energy==cut", energy == cut, f"n={n} E={energy} cut={cut}")
        check("T4 zero iff no crossing", (energy == 0) == (cut == 0))

def edge_cases():
    """Degenerate inputs the random sampler is unlikely to hit."""
    # single node
    A = np.zeros((1, 1), int); check("EC single node", closure(A)[0, 0] == 1)
    # empty graph: closure is identity
    A = np.zeros((5, 5), int); check("EC empty", np.array_equal(closure(A), np.eye(5, dtype=int)))
    # complete graph incl. self-loops: closure is all ones
    A = np.ones((5, 5), int); check("EC complete", (closure(A) == 1).all())
    # self-loop only
    A = np.zeros((3, 3), int); A[1, 1] = 1
    check("EC self-loop", np.array_equal(closure(A), np.eye(3, dtype=int)))
    # adding an existing edge is a no-op on R
    A = rand_graph(6, .3); R = closure(A)
    ones = list(zip(*np.where(A == 1)))
    if ones:
        u, v = ones[0]; A2 = A.copy(); A2[u, v] = 1
        check("EC add existing = no-op", np.array_equal(closure(A2), R))
    # cycle: deleting one edge of a 3-cycle does NOT dent pairs reachable the long way
    A = np.zeros((3, 3), int); A[0,1]=A[1,2]=A[2,0]=1
    R = closure(A); A2 = A.copy(); A2[0,1]=0; R2 = closure(A2)
    check("EC cycle delete", R[0,2] == 1 and R2[0,2] == 0)   # 0->2 only via 0->1->2
    check("EC cycle keeps 1->0", R[1,0] == 1 and R2[1,0] == 1)  # 1->2->0 survives

# ---------------------------------------------------------------- run
print("Property-based verification of FORMAL.md theorems")
print("=" * 66)
t1_polarity();       print(f"  T1 polarity / monotonicity      4000 random graphs   {'FAIL' if FAIL else 'PASS'}")
n0 = len(FAIL)
t2_localization();   print(f"  T2 localization + closed form   4000 random graphs   {'FAIL' if len(FAIL)>n0 else 'PASS'}")
n0 = len(FAIL)
tested3 = t3_fix_deformation()
print(f"  T3 fix deformation (iff)        {tested3} pairs, paths enumerated   {'FAIL' if len(FAIL)>n0 else 'PASS'}")
n0 = len(FAIL)
t4_laplacian();      print(f"  T4 Laplacian energy == cut      3000 random graphs   {'FAIL' if len(FAIL)>n0 else 'PASS'}")
n0 = len(FAIL)
edge_cases();        print(f"  edge cases (7 degenerate inputs)                     {'FAIL' if len(FAIL)>n0 else 'PASS'}")

n0 = len(FAIL)
t2_multiedge_counterexample()
print(f"  T2 minimal counterexample (locked)                   {'FAIL' if len(FAIL)>n0 else 'PASS'}")

viol  = t2_multiedge()
viol2 = t2_sequential_bound()
print(f"\n  T2 NAIVE multi-edge union bound   1500 trials, {viol} violations   "
      f"{'HOLDS' if viol == 0 else '*** DOES NOT HOLD ***'}")
print(f"  T2 SEQUENTIAL bound (corrected)   1500 trials, {viol2} violations   "
      f"{'HOLDS' if viol2 == 0 else 'DOES NOT HOLD'}")

print("=" * 66)
if FAIL:
    print(f"{len(FAIL)} FAILURES:")
    for f in FAIL[:12]: print("   ", f)
    sys.exit(1)
print("ALL PROPERTIES HOLD across ~13,400 randomized trials + 7 edge cases.")
print("\nScope note: this verifies the theorems as stated over finite directed graphs.")
print("It does not verify that R extracted from real source code is sound — that is")
print("the static-analysis approximation named in FORMAL.md §8, and no amount of")
print("graph-level testing can close it.")
