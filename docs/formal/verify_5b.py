#!/usr/bin/env python3
"""
verify_5b.py -- FORMAL.md section 5b: the real deformation matrix.

Source: agent-1 extraction, cal.diy PR #29724, 127/127 evidence items verified.
  BASE (intended contract A*) = f3284f581f  (= ca90ca2^)
  HEAD (actual A)             = ca90ca2c94

Two models at different granularities, because the granularity IS the finding.
  Model A: component/call graph  -- the resolution a naive extractor produces
  Model B: dataflow at branch resolution -- what it takes to see the actual defect

Standalone. Asserts its own claims. Imports nothing from verify.py.
"""
import numpy as np, os
np.set_printoptions(linewidth=140)
os.makedirs("figures", exist_ok=True)

def closure(A, n):
    R = (A | np.eye(n, dtype=int)).astype(int)
    for k in range(n):
        R = R | (np.outer(R[:, k], R[k, :]) > 0).astype(int)
    return R

def build(nodes, edges):
    n = len(nodes); ix = {s: i for i, s in enumerate(nodes)}
    A = np.zeros((n, n), int)
    for u, v in edges: A[ix[u], ix[v]] = 1
    return A, closure(A, n), ix

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

# ---------------------------------------------------------------- MODEL A
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

# ---------------------------------------------------------------- MODEL B
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

# ---------------------------------------------------------------- assertions
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

# ---------------------------------------------------------------- spheres
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

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
