#!/usr/bin/env python3
"""
verify.py -- Flow Surface Theory, formal companion.
Every number and figure in FORMAL.md is produced by this script.
Run: python3 verify.py   (writes figures/ and prints all matrices + theorem checks)
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import os

os.makedirs("figures", exist_ok=True)
np.set_printoptions(linewidth=120)

# ---------------------------------------------------------------- system
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

def closure(A):
    """Reflexive-transitive closure via boolean Warshall."""
    R = (A | np.eye(n, dtype=int)).astype(int)
    for k in range(n):
        R = R | (np.outer(R[:, k], R[k, :]) > 0).astype(int)
    return R

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

# ------------------------------------------------- Theorem 2: blast radius
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

# ------------------------------------- scope signal, cut count, energy
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

# ------------------------------------- the smoothness loop, three iterations
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

# ------------------------------------- plane vs flow granularity remark
# Bypass example: add Svc->DB_A to intended. Edge-level violation, flow-level invisible.
A_byp = edges_to_A(E_star + [("Svc","DB_A")])
R_byp = closure(A_byp)
print(f"\n[Remark] bypass Svc->DB_A: edge deformation entries = {int(np.abs(A_byp-A_star).sum())}, "
      f"flow deformation ||R_byp - R*||_1 = {int(np.abs(R_byp-R_star).sum())}  (violation invisible to R)")

# ================================================================ figures
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

# Fig 1: intended vs actual graphs
fig, axs = plt.subplots(1, 2, figsize=(11, 3.4))
draw_graph(axs[0], E_star, "Intended  $A^{*}$  (tenant-A slice)")
draw_graph(axs[1], E_act,  "Actual  $A$  — defect edge Svc→RepoB (missing tenant predicate)",
           defect=("Svc","RepoB"))
fig.tight_layout(); fig.savefig("figures/fig1_graphs.png", dpi=170); plt.close(fig)

# Fig 2: R*, R, D heatmaps
fig, axs = plt.subplots(1, 3, figsize=(12.5, 3.9))
draw_D(axs[0], R_star, "$R^{*}$ (intended reachability)")
draw_D(axs[1], R_act,  "$R$ (actual reachability)")
draw_D(axs[2], D,      "$D = R - R^{*}$   (+1 = bulge)")
fig.tight_layout(); fig.savefig("figures/fig2_matrices.png", dpi=170); plt.close(fig)

# Fig 3: blast radius -- graph shading + boxed D support
fig, axs = plt.subplots(1, 2, figsize=(11.5, 3.6), gridspec_kw={"width_ratios":[1.35,1]})
draw_graph(axs[0], E_act, "Anc$^{*}$(Svc) (orange)  ×  Desc$^{*}$(RepoB) (blue)",
           defect=("Svc","RepoB"),
           shade_anc={NODES[i] for i in Anc}, shade_desc={NODES[j] for j in Desc})
draw_D(axs[1], D, "support(D) ⊆ Anc×Desc  (Thm 2)", box_rc=(sorted(Anc), sorted(Desc)))
fig.tight_layout(); fig.savefig("figures/fig3_blast_radius.png", dpi=170); plt.close(fig)

# Fig 4: smoothness loop -- three D states + energy strip
fig, axs = plt.subplots(1, 3, figsize=(12.5, 3.9))
draw_D(axs[0], D,       "Iteration 0: NOT SMOOTH\n6 bulges  (‖D‖₁=6, C=1)")
draw_D(axs[1], D_naive, "Iteration 1 (naive fix): NOT SMOOTH\n3 bulges remain, dent created  (‖D‖₁=4, C=1)")
draw_D(axs[2], D_fix,   "Iteration 2 (correct fix): SMOOTH\n‖D‖₁=0, C=0")
fig.tight_layout(); fig.savefig("figures/fig4_smoothness_loop.png", dpi=170); plt.close(fig)

print("\nfigures written:", sorted(os.listdir("figures")))
print("ALL ASSERTIONS PASSED")
