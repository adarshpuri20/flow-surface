#!/usr/bin/env python3
"""
visualize3d.py -- Flow Surface Theory, 3D rendering of the deformation matrix.

The deformation matrix D is a scalar field over the (source, target) index space.
That makes it a *surface* in the one place the word is literal rather than metaphorical:
z = D[i][j], bulges are peaks (+1), dents are valleys (-1), smooth is the flat plane z=0.

Standalone by design: verify.py is the asserted artifact and is not imported or modified.
Run: python3 visualize3d.py   (writes figures/fig2_*.png, fig7_*.png, fig8_*.png)
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401
import os

os.makedirs("figures", exist_ok=True)

NODES = ["UI_A", "API", "Svc", "RepoA", "RepoB", "DB_A", "DB_B"]
n = len(NODES)
idx = {s: i for i, s in enumerate(NODES)}

E_star = [("UI_A","API"),("API","Svc"),("Svc","RepoA"),("RepoA","DB_A"),("RepoB","DB_B")]
E_act   = E_star + [("Svc","RepoB")]                       # defect edge
E_naive = [e for e in E_act if e != ("RepoB","DB_B")]      # naive fix: sever the sink
E_fix   = list(E_star)                                     # correct fix

def A_of(edges):
    A = np.zeros((n, n), dtype=int)
    for u, v in edges:
        A[idx[u], idx[v]] = 1
    return A

def closure(A):
    R = (A | np.eye(n, dtype=int)).astype(int)
    for k in range(n):
        R = R | (np.outer(R[:, k], R[k, :]) > 0).astype(int)
    return R

R_star = closure(A_of(E_star))
D0 = closure(A_of(E_act))   - R_star     # 6 bulges
D1 = closure(A_of(E_naive)) - R_star     # 3 bulges + 1 dent  (discontinuity moved)
D2 = closure(A_of(E_fix))   - R_star     # smooth

BULGE, DENT, FLAT = "#e03131", "#1971c2", "#ced4da"

def bars3d(ax, D, title, subtitle):
    """Discrete truth: one bar per matrix entry. No interpolation."""
    xs, ys, zs, dz, cols = [], [], [], [], []
    for i in range(n):
        for j in range(n):
            v = D[i, j]
            xs.append(j); ys.append(i)
            if v == 0:
                zs.append(-0.02); dz.append(0.04); cols.append(FLAT)
            else:
                zs.append(0.0); dz.append(v); cols.append(BULGE if v > 0 else DENT)
    ax.bar3d(np.array(xs) - .38, np.array(ys) - .38, zs, .76, .76, dz,
             color=cols, edgecolor="#343a40", linewidth=.35, shade=True)
    ax.set_zlim(-1.15, 1.15)
    ax.set_xticks(range(n)); ax.set_xticklabels(NODES, fontsize=6.5, rotation=48, ha="right")
    ax.set_yticks(range(n)); ax.set_yticklabels(NODES, fontsize=6.5)
    ax.set_zticks([-1, 0, 1]); ax.set_zticklabels(["dent −1", "0", "bulge +1"], fontsize=7)
    ax.set_xlabel("target j", fontsize=8, labelpad=6)
    ax.set_ylabel("source i", fontsize=8, labelpad=6)
    ax.view_init(elev=26, azim=-58)
    ax.set_title(f"{title}\n{subtitle}", fontsize=9.5, pad=8)
    ax.xaxis.pane.set_alpha(.04); ax.yaxis.pane.set_alpha(.04); ax.zaxis.pane.set_alpha(.04)

# ---- Fig 7: the smoothness loop as three surfaces -------------------------
fig = plt.figure(figsize=(15, 4.9))
for k, (D, t, s) in enumerate([
        (D0, "Iteration 0 — NOT SMOOTH", "6 bulges  ‖D‖₁=6   tenant-A reaches tenant-B data"),
        (D1, "Iteration 1 (naive fix) — NOT SMOOTH", "3 bulges + 1 dent  ‖D‖₁=4   the number fell, a valley opened"),
        (D2, "Iteration 2 (correct fix) — SMOOTH", "‖D‖₁=0   the flat plane")]):
    bars3d(fig.add_subplot(1, 3, k + 1, projection="3d"), D, t, s)
fig.suptitle("The deformation matrix as a surface:  z = D[i][j]   —   peaks are bulges, valleys are dents, flat is smooth",
             fontsize=11.5, y=.99)
fig.tight_layout(rect=[0, 0, 1, .93])
fig.savefig("figures/fig7_surface_3d_loop.png", dpi=165)
plt.close(fig)

# ---- Fig 8: the moved discontinuity, single large view --------------------
fig = plt.figure(figsize=(8.4, 6.4))
ax = fig.add_subplot(111, projection="3d")
bars3d(ax, D1, "The moved discontinuity",
       "naive fix: ‖D‖₁ 6→4 (strict descent) — yet three bulges survive\n"
       "and a new dent opens at (RepoB, DB_B): tenant B's own flow, broken")
ax.text2D(.02, .04,
          "The aggregate improved. The system got worse in kind.\n"
          "This is why the loop inspects entry polarity, not the norm.",
          transform=ax.transAxes, fontsize=8.6, color="#495057", style="italic")
fig.tight_layout()
fig.savefig("figures/fig8_moved_discontinuity_3d.png", dpi=165)
plt.close(fig)

# ---- Fig 2: interpolated view, explicitly labelled as illustrative --------
def blur(M, passes=28):
    """Gaussian-ish smoothing by repeated 3x3 averaging, on an upsampled grid."""
    U = np.kron(M.astype(float), np.ones((6, 6)))
    k = np.array([[1, 2, 1], [2, 4, 2], [1, 2, 1]], float); k /= k.sum()
    P = np.pad(U, 1, mode="edge")
    for _ in range(passes):
        P = np.pad(sum(k[a, b] * P[a:a + U.shape[0], b:b + U.shape[1]]
                       for a in range(3) for b in range(3)), 1, mode="edge")
    return P[1:-1, 1:-1]

fig = plt.figure(figsize=(13.5, 4.6))
for k, (D, t) in enumerate([(D0, "Iteration 0"), (D1, "Iteration 1 (naive)"), (D2, "Iteration 2 (correct)")]):
    ax = fig.add_subplot(1, 3, k + 1, projection="3d")
    Z = blur(D)
    X, Y = np.meshgrid(np.linspace(0, n - 1, Z.shape[1]), np.linspace(0, n - 1, Z.shape[0]))
    ax.plot_surface(X, Y, Z, cmap="RdBu_r", vmin=-.45, vmax=.45,
                    rstride=2, cstride=2, linewidth=0, antialiased=True)
    ax.set_zlim(-.5, .5); ax.view_init(elev=30, azim=-58)
    ax.set_xticks([]); ax.set_yticks([]); ax.set_zticks([])
    ax.set_title(t, fontsize=10)
    for pane in (ax.xaxis.pane, ax.yaxis.pane, ax.zaxis.pane):
        pane.set_alpha(.03)
fig.suptitle("Illustrative only — interpolated for intuition. The rigorous object is discrete (Fig 7);\n"
             "no manifold is claimed, and the interpolation has no formal content.",
             fontsize=10, y=.99, color="#868e96")
fig.tight_layout(rect=[0, 0, 1, .88])
fig.savefig("figures/fig2_illustrative_interpolation.png", dpi=165)
plt.close(fig)

print("wrote figures/fig7_surface_3d_loop.png")
print("wrote figures/fig8_moved_discontinuity_3d.png")
print("wrote figures/fig2_illustrative_interpolation.png")
print("\nnote: verify.py untouched; this script asserts nothing and computes no new claims.")
