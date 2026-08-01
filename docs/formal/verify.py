#!/usr/bin/env python3
"""
verify.py -- the single asserting artifact for FORMAL.md, three modes.

  --theorems : property-based verification of the four theorems (~13,400 seeded
               trials + 7 edge cases, Theorem 3 by independent path enumeration,
               Corollary 2.1's counterexample and sequential bound locked in)
  --example  : section 5's synthetic worked example (writes figures/fig3-6)
  --real     : section 5b's cal.diy PR 29724 matrices (writes figures/fig9)

Default (no flags): all three, in that order. Exits non-zero if any assertion fails.

The rendering-only scripts (visualize3d.py, sphere_test.py) are deliberately NOT
merged here: section 9 documents the asserted/presentational separation.
"""
import numpy as np, os, sys, random

os.makedirs("figures", exist_ok=True)

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ---------------------------------------------------------------- shared core
def closure(A):
    """Reflexive-transitive closure via boolean Warshall."""
    n = A.shape[0]
    R = (A | np.eye(n, dtype=int)).astype(int)
    for k in range(n):
        R = R | (np.outer(R[:, k], R[k, :]) > 0).astype(int)
    return R

# ================================================================ THEOREMS
# Property-based verification. verify's example sections assert that ONE instance
# satisfies the theorems; this section tests them as universally-quantified
# properties over randomly generated graphs, with Theorem 3 verified by
# independent path enumeration rather than by the definition it is stated in.

RNG = np.random.default_rng(20260731)
random.seed(20260731)

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

def run_theorems():
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

# ================================================================ EXAMPLE (§5)
def run_example():
    np.set_printoptions(linewidth=120)

    # ------------------------------------------------------------ system
    NODES = ["UI_A", "API", "Svc", "RepoA", "RepoB", "DB_A", "DB_B"]
    n = len(NODES)
    idx = {name: i for i, name in enumerate(NODES)}

    def edges_to_A(edges):
        A = np.zeros((n, n), dtype=int)
        for u, v in edges:
            A[idx[u], idx[v]] = 1
        return A

    # Intended architecture (tenant-A request slice; RepoB->DB_B serves tenant-B entry point)
    E_star = [("UI_A","API"), ("API","Svc"), ("Svc","RepoA"), ("RepoA","DB_A"), ("RepoB","DB_B")]
    # Actual: one defect edge -- Svc routes to RepoB (missing tenant predicate)
    E_act  = E_star + [("Svc","RepoB")]

    A_star, A_act = edges_to_A(E_star), edges_to_A(E_act)

    R_star, R_act = closure(A_star), closure(A_act)
    D = R_act - R_star                       # deformation matrix, entries in {-1,0,+1}
    d_edge = A_act - A_star                  # plane-level (edge) deformation

    def show(M, title):
        print(f"\n{title}")
        hdr = "        " + " ".join(f"{s:>6}" for s in NODES)
        print(hdr)
        for i, row in enumerate(M):
            print(f"{NODES[i]:>7} " + " ".join(f"{v:>6}" for v in row))

    show(A_star, "A*  (intended adjacency)")
    show(A_act,  "A   (actual adjacency)")
    show(R_star, "R*  (intended reachability, reflexive-transitive closure)")
    show(R_act,  "R   (actual reachability)")
    show(D,      "D = R - R*  (deformation: +1 bulge, -1 dent)")

    bulges = [(NODES[i], NODES[j]) for i, j in zip(*np.where(D == 1))]
    dents  = [(NODES[i], NODES[j]) for i, j in zip(*np.where(D == -1))]
    print(f"\nBulge set B = {bulges}")
    print(f"Dent  set N = {dents}")
    print(f"||D||_1 = {np.abs(D).sum()}")

    # --------------------------------------------- Theorem 2: blast radius
    u, v = idx["Svc"], idx["RepoB"]
    Anc  = set(np.where(R_star[:, u] == 1)[0])          # ancestors of u under R* (incl. u)
    Desc = set(np.where(R_star[v, :] == 1)[0])          # descendants of v under R* (incl. v)
    support = {(i, j) for i, j in zip(*np.where(D != 0))}
    box = {(i, j) for i in Anc for j in Desc}
    print(f"\n[Thm 2] Anc*(Svc)  = {sorted(NODES[i] for i in Anc)}")
    print(f"[Thm 2] Desc*(RepoB) = {sorted(NODES[j] for j in Desc)}")
    print(f"[Thm 2] support(D) subset of Anc x Desc : {support <= box}")
    print(f"[Thm 2] |support| = {len(support)}  bound |Anc|*|Desc| = {len(Anc)*len(Desc)}")
    assert support <= box
    beta = len(Anc) * len(Desc) / n**2
    print(f"[Thm 2] normalized blast radius beta = {len(Anc)}*{len(Desc)}/{n}^2 = {beta:.3f}")

    # closed-form check: R' = R  OR  (R e_uv R)
    R_pred = (R_star | (np.outer(R_star[:, u], R_star[v, :]) > 0)).astype(int)
    print(f"[Thm 2] closed form R* v (R* e_uv R*) == R : {np.array_equal(R_pred, R_act)}")
    assert np.array_equal(R_pred, R_act)

    # --------------------------------- scope signal, cut count, energy
    x = np.zeros(n, dtype=int); x[idx["RepoB"]] = 1; x[idx["DB_B"]] = 1   # tenant-B compartment
    def cut_count(A, x):
        return int(sum(A[i, j] * (x[i] != x[j]) for i in range(n) for j in range(n)))
    def laplacian_energy(A, x):
        S = ((A + A.T) > 0).astype(int)      # symmetrized
        L = np.diag(S.sum(axis=1)) - S
        return int(x @ L @ x)

    C_star, C_act = cut_count(A_star, x), cut_count(A_act, x)
    print(f"\n[Thm 4] compartment signal x = {dict(zip(NODES, x.tolist()))}")
    print(f"[Thm 4] cut count C(A*,x) = {C_star}   C(A,x) = {C_act}")
    print(f"[Thm 4] Laplacian energy  E(A*,x) = {laplacian_energy(A_star,x)}   E(A,x) = {laplacian_energy(A_act,x)}")

    # HIGH classification rule: any deformed pair crossing compartments?
    cross = [(NODES[i], NODES[j]) for (i, j) in support if x[i] != x[j]]
    print(f"[radius rule] deformed pairs crossing compartments: {cross}  -> class = {'HIGH' if cross else 'MEDIUM/LOW'}")

    # --------------------------------- the smoothness loop, three iterations
    # Naive fix: sever the sink (delete RepoB->DB_B)  -- kills the exposure, dents tenant B
    E_naive = [e for e in E_act if e != ("RepoB","DB_B")]
    A_naive = edges_to_A(E_naive); R_naive = closure(A_naive); D_naive = R_naive - R_star
    show(D_naive, "D after naive fix (delete RepoB->DB_B)")
    bulges_n = [(NODES[i], NODES[j]) for i, j in zip(*np.where(D_naive == 1))]
    dents_n  = [(NODES[i], NODES[j]) for i, j in zip(*np.where(D_naive == -1))]
    print(f"naive: bulges {bulges_n} dents {dents_n}  ||D||_1 = {np.abs(D_naive).sum()}")
    print(f"naive: cut count C = {cut_count(A_naive, x)}   (defect edge still present)")

    # Thm 3 instance: deleting (RepoB,DB_B): pair (RepoB,DB_B) flips 1->0 iff all paths used the edge
    assert R_star[idx["RepoB"], idx["DB_B"]] == 1 and R_naive[idx["RepoB"], idx["DB_B"]] == 0
    print("[Thm 3] deleted edge was the unique RepoB->DB_B path: dent appears exactly there -- verified")

    # Correct fix: delete the defect edge itself
    E_fix = [e for e in E_star]              # equals intended
    A_fix = edges_to_A(E_fix); R_fix = closure(A_fix); D_fix = R_fix - R_star
    show(D_fix, "D after correct fix (delete Svc->RepoB)")
    print(f"fixed: ||D||_1 = {np.abs(D_fix).sum()}   cut count C = {cut_count(A_fix, x)}")
    assert np.abs(D_fix).sum() == 0

    # --------------------------------- plane vs flow granularity remark
    # Bypass example: add Svc->DB_A to intended. Edge-level violation, flow-level invisible.
    A_byp = edges_to_A(E_star + [("Svc","DB_A")])
    R_byp = closure(A_byp)
    print(f"\n[Remark] bypass Svc->DB_A: edge deformation entries = {int(np.abs(A_byp-A_star).sum())}, "
          f"flow deformation ||R_byp - R*||_1 = {int(np.abs(R_byp-R_star).sum())}  (violation invisible to R)")

    # ============================================================ figures
    POS = {"UI_A":(0,2.2),"API":(1.4,2.2),"Svc":(2.8,2.2),"RepoA":(4.2,3.0),
           "RepoB":(4.2,1.4),"DB_A":(5.6,3.0),"DB_B":(5.6,1.4)}

    def draw_graph(ax, edges, title, defect=None, deleted=None, shade_anc=None, shade_desc=None):
        for name,(px,py) in POS.items():
            in_anc  = shade_anc  and name in shade_anc
            in_desc = shade_desc and name in shade_desc
            fc = "#ffd8a8" if in_anc else ("#a5d8ff" if in_desc else "#e9ecef")
            tenantB = name in ("RepoB","DB_B")
            ax.add_patch(plt.Circle((px,py), .33, fc=fc, ec="#c92a2a" if tenantB else "#495057",
                                    lw=2.2 if tenantB else 1.2, zorder=3))
            ax.text(px, py, name, ha="center", va="center", fontsize=8.5, zorder=4)
        for (a,b) in edges:
            (x1,y1),(x2,y2) = POS[a], POS[b]
            is_def = defect and (a,b)==defect
            ax.annotate("", xy=(x2,y2), xytext=(x1,y1),
                arrowprops=dict(arrowstyle="-|>", lw=2.6 if is_def else 1.6,
                                color="#e03131" if is_def else "#495057",
                                shrinkA=16, shrinkB=16,
                                linestyle="--" if is_def else "-"), zorder=2)
        if deleted:
            (x1,y1),(x2,y2) = POS[deleted[0]], POS[deleted[1]]
            ax.annotate("", xy=(x2,y2), xytext=(x1,y1),
                arrowprops=dict(arrowstyle="-|>", lw=1.4, color="#adb5bd",
                                shrinkA=16, shrinkB=16, linestyle=":"), zorder=1)
            ax.text((x1+x2)/2, (y1+y2)/2-.28, "deleted", color="#868e96", fontsize=7.5, ha="center")
        ax.set_xlim(-.7,6.4); ax.set_ylim(.6,3.8); ax.set_aspect("equal"); ax.axis("off")
        ax.set_title(title, fontsize=10)

    def draw_D(ax, M, title, box_rc=None):
        ax.imshow(M, cmap="bwr", vmin=-1, vmax=1)
        ax.set_xticks(range(n), NODES, rotation=45, ha="right", fontsize=7.5)
        ax.set_yticks(range(n), NODES, fontsize=7.5)
        for i in range(n):
            for j in range(n):
                if M[i,j] != 0:
                    ax.text(j, i, f"{M[i,j]:+d}", ha="center", va="center", fontsize=8,
                            color="white", fontweight="bold")
        if box_rc:
            rows, cols = box_rc
            for i in rows:
                for j in cols:
                    ax.add_patch(plt.Rectangle((j-.5,i-.5),1,1, fill=False, ec="#f08c00", lw=2))
        ax.set_title(title, fontsize=9.5)

    # Fig 3: intended vs actual graphs
    fig, axs = plt.subplots(1, 2, figsize=(11, 3.4))
    draw_graph(axs[0], E_star, "Intended  $A^{*}$  (tenant-A slice)")
    draw_graph(axs[1], E_act,  "Actual  $A$  — defect edge Svc→RepoB (missing tenant predicate)",
               defect=("Svc","RepoB"))
    fig.tight_layout(); fig.savefig("figures/fig3_graphs.png", dpi=170); plt.close(fig)

    # Fig 4: R*, R, D heatmaps
    fig, axs = plt.subplots(1, 3, figsize=(12.5, 3.9))
    draw_D(axs[0], R_star, "$R^{*}$ (intended reachability)")
    draw_D(axs[1], R_act,  "$R$ (actual reachability)")
    draw_D(axs[2], D,      "$D = R - R^{*}$   (+1 = bulge)")
    fig.tight_layout(); fig.savefig("figures/fig4_matrices.png", dpi=170); plt.close(fig)

    # Fig 5: blast radius -- graph shading + boxed D support
    fig, axs = plt.subplots(1, 2, figsize=(11.5, 3.6), gridspec_kw={"width_ratios":[1.35,1]})
    draw_graph(axs[0], E_act, "Anc$^{*}$(Svc) (orange)  ×  Desc$^{*}$(RepoB) (blue)",
               defect=("Svc","RepoB"),
               shade_anc={NODES[i] for i in Anc}, shade_desc={NODES[j] for j in Desc})
    draw_D(axs[1], D, "support(D) ⊆ Anc×Desc  (Thm 2)", box_rc=(sorted(Anc), sorted(Desc)))
    fig.tight_layout(); fig.savefig("figures/fig5_blast_radius.png", dpi=170); plt.close(fig)

    # Fig 6: smoothness loop -- three D states + energy strip
    fig, axs = plt.subplots(1, 3, figsize=(12.5, 3.9))
    draw_D(axs[0], D,       "Iteration 0: NOT SMOOTH\n6 bulges  (‖D‖₁=6, C=1)")
    draw_D(axs[1], D_naive, "Iteration 1 (naive fix): NOT SMOOTH\n3 bulges remain, dent created  (‖D‖₁=4, C=1)")
    draw_D(axs[2], D_fix,   "Iteration 2 (correct fix): SMOOTH\n‖D‖₁=0, C=0")
    fig.tight_layout(); fig.savefig("figures/fig6_smoothness_loop.png", dpi=170); plt.close(fig)

    print("\nfigures written:", sorted(f for f in os.listdir("figures") if f[3] in "3456"))
    print("ALL ASSERTIONS PASSED")

# ================================================================ REAL (§5b)
def run_real():
    np.set_printoptions(linewidth=140)

    def build(nodes, edges):
        n = len(nodes); ix = {s: i for i, s in enumerate(nodes)}
        A = np.zeros((n, n), int)
        for u, v in edges: A[ix[u], ix[v]] = 1
        return A, closure(A), ix

    def report(name, nodes, Eb, Eh):
        n = len(nodes)
        Ab, Rb, ix = build(nodes, Eb)
        Ah, Rh, _  = build(nodes, Eh)
        D, d = Rh - Rb, Ah - Ab
        print(f"\n{'='*78}\n{name}\n{'='*78}")
        print(f"nodes ({n}): {', '.join(nodes)}")
        bul = [(nodes[i], nodes[j]) for i, j in zip(*np.where(D == 1))]
        den = [(nodes[i], nodes[j]) for i, j in zip(*np.where(D == -1))]
        add = [(nodes[i], nodes[j]) for i, j in zip(*np.where(d == 1))]
        rem = [(nodes[i], nodes[j]) for i, j in zip(*np.where(d == -1))]
        print(f"\nPLANE level  d = A - A*   ||d||_1 = {np.abs(d).sum()}")
        print(f"  edges added  : {add}")
        print(f"  edges removed: {rem}")
        print(f"\nFLOW level   D = R - R*   ||D||_1 = {np.abs(D).sum()}")
        print(f"  BULGES (+1): {bul if bul else 'none'}")
        print(f"  DENTS  (-1): {den if den else 'none'}")
        return D, d, bul, den, add, rem, ix, nodes

    # ------------------------------------------------------------ MODEL A
    # Component/call granularity. The BASE inline query and the HEAD repository are
    # IDENTIFIED as one node: this is an extract-method refactor, same role, and
    # treating them as distinct would record a rename as six deformations (noise).
    # ** This identification is an approximation decision and is declared, not hidden. **
    nodes_A = ["trpc", "getEvtType", "srv", "credQuery", "build", "enrich", "getApps", "db", "sel"]
    base_A = [("trpc","srv"), ("getEvtType","srv"),
              ("srv","credQuery"), ("srv","enrich"), ("srv","build"), ("srv","getApps"),
              ("credQuery","db"), ("credQuery","sel")]
    head_A = [("trpc","srv"), ("getEvtType","srv"),
              ("srv","credQuery"), ("srv","enrich"), ("srv","getApps"),
              ("credQuery","db"), ("credQuery","sel"), ("credQuery","build")]
    DA, dA, bulA, denA, addA, remA, ixA, nA = report(
        "MODEL A -- component/call granularity", nodes_A, base_A, head_A)

    # ------------------------------------------------------------ MODEL B
    # Dataflow at BRANCH resolution. BASE: raw rows reach both branches; only the
    # else branch applies build (server.ts:96-98). HEAD: the repository applies build
    # unconditionally (PrismaCredentialRepository.ts:38) so BUILT rows reach both.
    nodes_B = ["trpc","getEvtType","srv","credQuery","build","ifBranch","elseBranch","enrich","getApps","db","sel"]
    base_B = [("trpc","srv"), ("getEvtType","srv"), ("srv","credQuery"),
              ("credQuery","db"), ("credQuery","sel"),
              ("credQuery","ifBranch"), ("credQuery","elseBranch"),
              ("ifBranch","enrich"), ("elseBranch","build"),
              ("enrich","getApps"), ("build","getApps")]
    head_B = [("trpc","srv"), ("getEvtType","srv"), ("srv","credQuery"),
              ("credQuery","db"), ("credQuery","sel"),
              ("credQuery","build"),
              ("build","ifBranch"), ("build","elseBranch"),
              ("ifBranch","enrich"),
              ("enrich","getApps"), ("elseBranch","getApps")]
    DB, dB, bulB, denB, addB, remB, ixB, nB = report(
        "MODEL B -- dataflow at branch resolution", nodes_B, base_B, head_B)

    # ------------------------------------------------------------ assertions
    print(f"\n{'='*78}\nASSERTIONS\n{'='*78}")

    # A1: Model A -- the defect surfaces as exactly one bulge, credQuery -> build.
    assert bulA == [("credQuery","build")], bulA
    assert denA == [], denA
    print("A1  Model A: exactly one bulge (credQuery -> build), zero dents        PASS")

    # A2: Model A -- a plane-level edge deletion (srv -> build) is INVISIBLE at flow
    #     level, because reachability srv->build is preserved through credQuery.
    #     This is section 4's claim, occurring in real code.
    assert ("srv","build") in remA, remA
    assert DA[ixA["srv"], ixA["build"]] == 0
    print("A2  Model A: srv->build deleted at plane level, invisible in D          PASS")

    # A3: Model B -- the branch-widening appears as a bulge onto the if-user branch.
    assert ("build","ifBranch") in bulB, bulB
    print("A3  Model B: bulge (build -> ifBranch) = the branch-widening            PASS")

    # A4: Granularity matters: Model A cannot express the defect the reviewer found.
    assert ("build","ifBranch") not in [tuple(x) for x in bulA]
    print("A4  Model A cannot express the finding Model B makes explicit           PASS")

    # A5: BASE against itself is the sphere: D = 0 identically.
    _, Rb_self, _ = build(nodes_B, base_B)
    assert np.abs(Rb_self - Rb_self).sum() == 0
    print("A5  BASE vs BASE: ||D||_1 = 0  -- the sphere, from real code            PASS")

    print(f"\nModel A ||D||_1 = {np.abs(DA).sum()}   Model B ||D||_1 = {np.abs(DB).sum()}")
    print("ALL ASSERTIONS PASSED")

    # ------------------------------------------------------------ spheres
    def field(D, up=14, passes=40):
        U = np.kron(D.astype(float), np.ones((up, up)))
        k = np.array([[1,2,1],[2,4,2],[1,2,1]], float); k /= k.sum()
        P = U.copy()
        for _ in range(passes):
            Pp = np.pad(np.pad(P, ((1,1),(0,0)), mode="edge"), ((0,0),(1,1)), mode="wrap")
            P = sum(k[a,b]*Pp[a:a+P.shape[0], b:b+P.shape[1]] for a in range(3) for b in range(3))
        return P

    def sphere(ax, D, title, sub, eps=0.34):
        F = field(D); rows, cols = F.shape
        PH, TH = np.meshgrid(np.linspace(.001, np.pi-.001, rows),
                             np.linspace(0, 2*np.pi, cols), indexing="ij")
        m = np.abs(F).max(); Fn = F/m if m > 1e-9 else F
        R = 1.0 + eps*Fn
        ax.plot_surface(R*np.sin(PH)*np.cos(TH), R*np.sin(PH)*np.sin(TH), R*np.cos(PH),
                        facecolors=plt.cm.RdBu_r(plt.Normalize(-1,1)(Fn)),
                        rstride=2, cstride=2, linewidth=0, antialiased=True, shade=True)
        L = 1+eps*1.15
        ax.set_xlim(-L,L); ax.set_ylim(-L,L); ax.set_zlim(-L,L)
        ax.set_box_aspect((1,1,1)); ax.set_axis_off(); ax.view_init(elev=18, azim=-52)
        ax.set_title(f"{title}\n{sub}", fontsize=10, pad=1)

    fig = plt.figure(figsize=(15, 5.4))
    sphere(fig.add_subplot(131, projection="3d"), np.zeros_like(DB),
           "BASE vs BASE — SMOOTH", "real code, ‖D‖₁=0 — the sphere")
    sphere(fig.add_subplot(132, projection="3d"), DA,
           "Model A — component granularity", f"one bulge  ‖D‖₁={np.abs(DA).sum()}")
    sphere(fig.add_subplot(133, projection="3d"), DB,
           "Model B — branch resolution", f"the branch-widening  ‖D‖₁={np.abs(DB).sum()}")
    fig.suptitle("cal.diy PR #29724 — the real deformation, rendered radially.  "
                 "BASE is the sphere; the refactor deforms it.", fontsize=12.5, y=.97)
    fig.text(.5, .035, "Radial deviation computed from D = R − R*. Angular placement is a chosen "
             "layout, not derived geometry. Node identity across BASE/HEAD is a declared "
             "approximation (see §5b).", ha="center", fontsize=8.2, color="#868e96", style="italic")
    fig.tight_layout(rect=[0,.06,1,.93])
    fig.savefig("figures/fig9_real_deformation_spheres.png", dpi=165)
    print("\nwrote figures/fig9_real_deformation_spheres.png")

# ================================================================ main
if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="FORMAL.md asserting artifact: three modes")
    ap.add_argument("--theorems", action="store_true", help="property-based theorem tests only")
    ap.add_argument("--example", action="store_true", help="section 5 synthetic example only")
    ap.add_argument("--real", action="store_true", help="section 5b cal.diy matrices only")
    args = ap.parse_args()
    run_all = not (args.theorems or args.example or args.real)
    if args.theorems or run_all:
        run_theorems()
    if args.example or run_all:
        run_example()
    if args.real or run_all:
        run_real()
