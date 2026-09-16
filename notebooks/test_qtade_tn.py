import numpy as np, qtade_tn as tn

def chk(name, cond, extra=""):
    print(("PASS " if cond else "FAIL ") + name, extra)
    assert cond, name

rng = np.random.default_rng(1)

# --- TT-SVD round trip ---
n = 8
v = rng.standard_normal([2]*n)
c = tn.tt_svd(v, eps=1e-13)
chk("tt_svd exact", np.allclose(tn.tt_full(c), v, atol=1e-9),
    f"ranks={tn.tt_ranks(c)}")

# --- low-rank recovery ---
x = np.linspace(0,1,2**12, endpoint=False)
f = np.exp(-3*x) + np.sin(4*np.pi*x)
c = tn.qtt_from_vector(f, eps=1e-12)
chk("smooth fn low rank", max(tn.tt_ranks(c)) <= 5, f"ranks={tn.tt_ranks(c)}")
chk("smooth fn accurate", np.allclose(tn.qtt_to_vector(c), f, atol=1e-10))

noise = rng.standard_normal(2**12)
cn = tn.qtt_from_vector(noise, eps=1e-6)
chk("noise high rank", max(tn.tt_ranks(cn)) > 30, f"ranks max={max(tn.tt_ranks(cn))}")

# --- rounding ---
c2 = tn.tt_round(c, eps=1e-8)
chk("round keeps value", np.allclose(tn.qtt_to_vector(c2), f, atol=1e-7),
    f"ranks={tn.tt_ranks(c2)}")

# --- canonical form ---
cc = tn.tt_canonicalise(c, centre=3)
for k in range(3):
    m = cc[k].reshape(-1, cc[k].shape[-1])
    assert np.allclose(m.T@m, np.eye(m.shape[1]), atol=1e-10)
for k in range(4, len(cc)):
    m = cc[k].reshape(cc[k].shape[0], -1)
    assert np.allclose(m@m.T, np.eye(m.shape[0]), atol=1e-10)
chk("mixed canonical", np.allclose(tn.qtt_to_vector(cc), f, atol=1e-10))

# --- arithmetic ---
g = np.cos(2*np.pi*x)
cg = tn.qtt_from_vector(g, eps=1e-12)
chk("add", np.allclose(tn.qtt_to_vector(tn.tt_add(c, cg)), f+g, atol=1e-9))
chk("hadamard", np.allclose(tn.qtt_to_vector(tn.tt_hadamard(c, cg)), f*g, atol=1e-9))
chk("dot", abs(tn.tt_dot(c, cg) - f@g) < 1e-7, f"{tn.tt_dot(c,cg):.6f} vs {f@g:.6f}")
chk("norm", abs(tn.tt_norm(c) - np.linalg.norm(f)) < 1e-8)

# --- shift / Laplacian MPOs ---
for nn in (3,4,5):
    S = tn.qtt_shift(nn, +1)
    N = 2**nn
    dense = np.zeros((N,N))
    for j in range(N-1): dense[j+1, j] = 1.0
    chk(f"shift n={nn}", np.allclose(tn.mpo_full(S), dense), f"rank={max(tn.mpo_ranks(S))}")
    Sm = tn.qtt_shift(nn, -1)
    chk(f"shift- n={nn}", np.allclose(tn.mpo_full(Sm), dense.T))
    L = tn.qtt_laplacian(nn, dx=1.0)
    ref = dense + dense.T - 2*np.eye(N)
    chk(f"laplacian n={nn}", np.allclose(tn.mpo_full(L), ref), f"rank={max(tn.mpo_ranks(L))}")
    D = tn.qtt_first_derivative(nn, dx=1.0)
    chk(f"d/dx n={nn}", np.allclose(tn.mpo_full(D), (dense.T-dense)/2))
    uu = np.arange(N, dtype=float)
    chk(f"d/dx slope n={nn}", np.allclose((tn.mpo_full(D)@uu)[1:-1], 1.0))

# --- analytic cores ---
nn = 10
gx = tn.qtt_to_vector(tn.qtt_grid(nn, 0.0, 1.0))
chk("qtt_grid", np.allclose(gx, np.linspace(0,1,2**nn,endpoint=False)),
    f"rank={max(tn.tt_ranks(tn.qtt_grid(nn)))}")
ge = tn.qtt_to_vector(tn.qtt_exp(nn, rate=-2.0))
chk("qtt_exp", np.allclose(ge, np.exp(-2*np.linspace(0,1,2**nn,endpoint=False))),
    f"rank={max(tn.tt_ranks(tn.qtt_exp(nn)))}")

# --- MPO apply ---
nn = 10
xs = np.linspace(0,1,2**nn,endpoint=False)
u = np.sin(2*np.pi*xs)
cu = tn.qtt_from_vector(u, eps=1e-13)
L = tn.qtt_laplacian(nn, dx=xs[1]-xs[0])
Lu = tn.qtt_to_vector(tn.tt_round(tn.mpo_apply(L, cu), 1e-10))
ref = np.zeros_like(u); h = xs[1]-xs[0]
ref[1:-1] = (u[2:] - 2*u[1:-1] + u[:-2])/h**2
ref[0] = (u[1]-2*u[0])/h**2; ref[-1] = (u[-2]-2*u[-1])/h**2
chk("mpo_apply laplacian", np.allclose(Lu, ref, atol=1e-6), f"maxerr={np.abs(Lu-ref).max():.2e}")

# --- solvers: implicit Euler step ---
nn = 10
alpha, dt = 1.0, 1e-4
h = 2.0**-nn
L = tn.qtt_laplacian(nn, dx=h)
A = tn.mpo_add(tn.mpo_identity(nn), tn.mpo_scale(L, -alpha*dt))
A = tn.mpo_round(A, eps=1e-13)
u0 = tn.qtt_from_vector(np.exp(-200*(xs-0.5)**2), eps=1e-12)
xsol = tn.dmrg_solve(A, u0, sweeps=3, eps=1e-10, chi_max=40)
res = tn.residual(A, xsol, u0)
chk("dmrg_solve", res < 1e-7, f"residual={res:.2e}, chi={max(tn.tt_ranks(xsol))}")
Adense = tn.mpo_full(A)
ref = np.linalg.solve(Adense, tn.qtt_to_vector(u0))
chk("dmrg vs dense", np.allclose(tn.qtt_to_vector(xsol), ref, atol=1e-7),
    f"err={np.abs(tn.qtt_to_vector(xsol)-ref).max():.2e}")

xals = tn.als_solve(A, u0, x0=[c.copy() for c in u0], sweeps=4)
chk("als_solve", tn.residual(A, xals, u0) < 1e-6, f"residual={tn.residual(A,xals,u0):.2e}")

# --- maxvol ---
Q,_ = np.linalg.qr(rng.standard_normal((200, 6)))
rows = tn.maxvol(Q)
B = Q @ np.linalg.inv(Q[rows])
chk("maxvol bounded", np.abs(B).max() < 1.2, f"max|B|={np.abs(B).max():.3f}")

# --- tt_cross ---
nn = 14
def f_idx(idx):
    # idx: (m, n) bits, core 0 = most significant
    w = 2.0**(-(np.arange(nn)+1))
    xx = idx @ w
    return np.exp(-2*xx) + np.sin(6*np.pi*xx)
cores, stats = tn.tt_cross(f_idx, [2]*nn, rank=6, sweeps=3, return_stats=True)
xx = np.linspace(0,1,2**nn,endpoint=False)
exact = np.exp(-2*xx) + np.sin(6*np.pi*xx)
got = tn.qtt_to_vector(cores)
err = np.linalg.norm(got-exact)/np.linalg.norm(exact)
chk("tt_cross", err < 1e-8, f"rel err={err:.2e}, evals={stats['evaluations']} vs 2^{nn}={2**nn}")
print("\nALL TESTS PASSED")
