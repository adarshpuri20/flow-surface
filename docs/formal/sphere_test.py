#!/usr/bin/env python3
"""
sphere_test.py -- radial rendering test.

The original FST image: the system is a closed surface whose radius in each angular
direction is how far the flow travels. Perfect => uniform radius => a sphere.

Reconstruct that from the deformation matrix: r = 1 + eps * D.
  D = 0  -> r = 1        -> unit sphere (smooth topology)
  D = +1 -> r = 1 + eps  -> bulge (outward)
  D = -1 -> r = 1 - eps  -> dent  (inward)

HONESTY NOTE: the assignment of matrix indices to angular coordinates is a chosen
layout, like a map projection -- not derived geometry. The radial deviation is real
data; the placement on the sphere is presentational.
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import os

os.makedirs("figures", exist_ok=True)

NODES = ["UI_A", "API", "Svc", "RepoA", "RepoB", "DB_A", "DB_B"]
n = len(NODES); idx = {s: i for i, s in enumerate(NODES)}

E_star = [("UI_A","API"),("API","Svc"),("Svc","RepoA"),("RepoA","DB_A"),("RepoB","DB_B")]
E_act   = E_star + [("Svc","RepoB")]
E_naive = [e for e in E_act if e != ("RepoB","DB_B")]

def A_of(E):
    A = np.zeros((n,n), int)
    for u,v in E: A[idx[u], idx[v]] = 1
    return A

def closure(A):
    R = (A | np.eye(n,dtype=int)).astype(int)
    for k in range(n):
        R = R | (np.outer(R[:,k], R[k,:]) > 0).astype(int)
    return R

Rs = closure(A_of(E_star))
D0 = closure(A_of(E_act))   - Rs
D1 = closure(A_of(E_naive)) - Rs
D2 = closure(A_of(E_star))  - Rs      # all zeros

def to_sphere_field(D, up=14, passes=40):
    """Upsample D to a smooth (theta, phi) field. Azimuth wraps periodically."""
    U = np.kron(D.astype(float), np.ones((up, up)))
    k = np.array([[1,2,1],[2,4,2],[1,2,1]], float); k /= k.sum()
    P = U.copy()
    for _ in range(passes):
        # wrap azimuth (axis 1), clamp polar (axis 0)
        Pp = np.pad(P, ((1,1),(0,0)), mode="edge")
        Pp = np.pad(Pp, ((0,0),(1,1)), mode="wrap")
        P = sum(k[a,b] * Pp[a:a+P.shape[0], b:b+P.shape[1]]
                for a in range(3) for b in range(3))
    return P

def draw_sphere(ax, D, title, sub, eps=0.34):
    F = to_sphere_field(D)
    rows, cols = F.shape
    phi   = np.linspace(0.001, np.pi-0.001, rows)      # polar   <- source index
    theta = np.linspace(0, 2*np.pi, cols)              # azimuth <- target index
    TH, PH = np.meshgrid(theta, phi)
    # normalise field so peak magnitude maps to eps
    m = np.abs(F).max()
    Fn = F / m if m > 1e-9 else F
    R = 1.0 + eps * Fn
    X = R*np.sin(PH)*np.cos(TH); Y = R*np.sin(PH)*np.sin(TH); Z = R*np.cos(PH)

    norm = plt.Normalize(-1, 1)
    colors = plt.cm.RdBu_r(norm(Fn))
    ax.plot_surface(X, Y, Z, facecolors=colors, rstride=2, cstride=2,
                    linewidth=0, antialiased=True, shade=True)
    lim = 1.0 + eps*1.15
    ax.set_xlim(-lim,lim); ax.set_ylim(-lim,lim); ax.set_zlim(-lim,lim)
    ax.set_box_aspect((1,1,1))
    ax.set_axis_off()
    ax.view_init(elev=18, azim=-52)
    ax.set_title(f"{title}\n{sub}", fontsize=10, pad=2)

fig = plt.figure(figsize=(15, 5.4))
for k,(D,t,s) in enumerate([
    (D0, "Iteration 0 — NOT SMOOTH", "bulge: flows reach past the boundary  ‖D‖₁=6"),
    (D1, "Iteration 1 (naive fix) — NOT SMOOTH", "bulge shrinks, a dent opens  ‖D‖₁=4"),
    (D2, "Iteration 2 — SMOOTH", "uniform radius: the sphere  ‖D‖₁=0")]):
    draw_sphere(fig.add_subplot(1,3,k+1, projection="3d"), D, t, s)
fig.suptitle("The system as a closed surface:  radius = how far the flow travels.  "
             "A perfect system is a sphere.", fontsize=12.5, y=0.97)
fig.text(0.5, 0.035,
         "Radial deviation is computed from D = R − R*. The mapping of matrix indices to "
         "angular position is a chosen layout (like a map projection), not derived geometry.",
         ha="center", fontsize=8.4, color="#868e96", style="italic")
fig.tight_layout(rect=[0,0.06,1,0.93])
fig.savefig("figures/fig8_sphere_topology.png", dpi=165)
plt.close(fig)
print("wrote figures/fig8_sphere_topology.png")
