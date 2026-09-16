"""qtade_tn -- a small, readable tensor-train toolkit for the QTADE lecture.

Everything here is NumPy and about 500 lines. It is meant to be *read*, not
just imported: each function is the shortest honest implementation of one idea
from Parts I and II of the course. Nothing is optimised; several things are
deliberately naive so that the cost of the naive version is visible.

Conventions
-----------
A tensor train is a plain Python list of cores::

    cores[k].shape == (r[k], d[k], r[k+1]),   r[0] == r[n] == 1

so ``v[i_0, ..., i_{n-1}] = cores[0][:, i_0, :] @ ... @ cores[n-1][:, i_{n-1}, :]``.

A matrix product operator is a list of cores::

    cores[k].shape == (R[k], d_out[k], d_in[k], R[k+1]),   R[0] == R[n] == 1

Index 0 of a quantics chain is the **most significant** bit, i.e. the coarsest
length scale; index n-1 is the finest. That ordering is what makes "one core =
one length scale" true, and it is assumed throughout.

Part III and Part IV move to `quimb` (see qtade_quimb.py). The cores are the
same arrays in the same order, so moving between the two is a relabelling.
"""

from __future__ import annotations

import numpy as np

__all__ = [
    "tt_full", "tt_ranks", "tt_size", "tt_svd", "tt_round", "tt_add",
    "tt_scale", "tt_hadamard", "tt_dot", "tt_norm", "tt_left_orthogonalise",
    "tt_canonicalise", "mpo_full", "mpo_apply", "mpo_add", "mpo_scale",
    "mpo_identity", "mpo_ranks", "qtt_shift", "qtt_laplacian", "qtt_first_derivative",
    "qtt_grid", "qtt_exp", "qtt_from_vector", "qtt_to_vector",
    "maxvol", "tt_cross", "als_solve", "dmrg_solve", "residual",
]


# ---------------------------------------------------------------------------
# 1. Basics: reconstruct, measure, and pretty-print a train
# ---------------------------------------------------------------------------

def tt_ranks(cores):
    """Bond dimensions [r_0, r_1, ..., r_n]. The list is the whole story."""
    return [cores[0].shape[0]] + [c.shape[-1] for c in cores]


def tt_size(cores):
    """Number of stored floats. Compare against prod(d) to see the compression."""
    return sum(c.size for c in cores)


def tt_full(cores):
    """Contract the whole train into a dense array. Exponential -- small n only.

    This is the function you are trying never to call. It exists so that the
    exercises can check the cheap answer against the expensive one.
    """
    out = cores[0]
    for c in cores[1:]:
        # (..., r) x (r, d, r') -> (..., d, r')
        out = np.tensordot(out, c, axes=([-1], [0]))
    return out.reshape([c.shape[1] for c in cores])


def qtt_to_vector(cores):
    """Quantics train -> length-2^n vector, first core = most significant bit."""
    return tt_full(cores).reshape(-1)


def qtt_from_vector(v, eps=1e-12, chi_max=None):
    """Length-2^n vector -> quantics train, by TT-SVD."""
    n = int(round(np.log2(v.size)))
    assert 2 ** n == v.size, "quantics needs a power-of-two length"
    return tt_svd(v.reshape([2] * n), eps=eps, chi_max=chi_max)


# ---------------------------------------------------------------------------
# 2. TT-SVD: build a train from a dense array
# ---------------------------------------------------------------------------

def _truncation_rank(s, eps_local, chi_max):
    """Largest rank whose discarded tail has 2-norm <= eps_local."""
    if s.size == 0:
        return 1
    tail = np.sqrt(np.cumsum(s[::-1] ** 2))[::-1]      # tail[k] = ||s[k:]||
    keep = int(np.searchsorted(-tail, -eps_local, side="left"))
    keep = max(1, min(keep, s.size))
    if chi_max is not None:
        keep = min(keep, chi_max)
    return keep


def tt_svd(array, eps=1e-10, chi_max=None):
    """Sequential SVD down the chain (Oseledets 2011, Algorithm 1).

    `eps` is a *relative* Frobenius tolerance for the whole train. It is split
    across the n-1 cuts as eps/sqrt(n-1), which is what makes the result
    quasi-optimal: within sqrt(n-1) of the best rank-chi approximation.
    """
    array = np.asarray(array, dtype=float)
    dims = list(array.shape)
    n = len(dims)
    delta = eps * np.linalg.norm(array) / np.sqrt(max(n - 1, 1))

    cores, rank, rest = [], 1, array.reshape(dims[0], -1)
    for k in range(n - 1):
        rest = rest.reshape(rank * dims[k], -1)
        u, s, vt = np.linalg.svd(rest, full_matrices=False)
        keep = _truncation_rank(s, delta, chi_max)
        cores.append(u[:, :keep].reshape(rank, dims[k], keep))
        rest = (s[:keep, None] * vt[:keep])
        rank = keep
    cores.append(rest.reshape(rank, dims[-1], 1))
    return cores


# ---------------------------------------------------------------------------
# 3. Gauge: orthogonalisation, canonical form, rounding
# ---------------------------------------------------------------------------

def tt_left_orthogonalise(cores, upto=None):
    """QR sweep from the left. Cores [0, upto) become left-orthogonal.

    Left-orthogonal means: reshape the core to (r*d, r') and its columns are
    orthonormal. The environment to the left of the orthogonality centre is
    then the identity, which is what makes truncation at the centre optimal.
    """
    cores = [c.copy() for c in cores]
    n = len(cores)
    upto = n - 1 if upto is None else upto
    for k in range(upto):
        r, d, r1 = cores[k].shape
        q, rr = np.linalg.qr(cores[k].reshape(r * d, r1))
        cores[k] = q.reshape(r, d, -1)
        cores[k + 1] = np.tensordot(rr, cores[k + 1], axes=([1], [0]))
    return cores


def tt_canonicalise(cores, centre=0):
    """Mixed canonical form with the orthogonality centre at `centre`."""
    cores = tt_left_orthogonalise(cores, upto=centre)
    n = len(cores)
    for k in range(n - 1, centre, -1):
        r, d, r1 = cores[k].shape
        q, rr = np.linalg.qr(cores[k].reshape(r, d * r1).T)
        cores[k] = q.T.reshape(-1, d, r1)
        cores[k - 1] = np.tensordot(cores[k - 1], rr.T, axes=([2], [0]))
    return cores


def tt_round(cores, eps=1e-10, chi_max=None):
    """Recompress a train to tolerance `eps` (or to `chi_max`).

    The workhorse of the whole subject. Every product inflates ranks -- an MPO
    application multiplies chi by chi_MPO, a sum adds ranks, a Hadamard product
    multiplies them -- so this runs after *every* operation. Cost O(n chi^3).
    """
    n = len(cores)
    if n == 1:
        return [c.copy() for c in cores]
    cores = tt_left_orthogonalise(cores)                 # centre now at n-1
    nrm = np.linalg.norm(cores[-1])
    delta = eps * nrm / np.sqrt(n - 1)

    for k in range(n - 1, 0, -1):
        r, d, r1 = cores[k].shape
        u, s, vt = np.linalg.svd(cores[k].reshape(r, d * r1), full_matrices=False)
        keep = _truncation_rank(s, delta, chi_max)
        cores[k] = vt[:keep].reshape(keep, d, r1)
        cores[k - 1] = np.tensordot(cores[k - 1], u[:, :keep] * s[:keep], axes=([2], [0]))
    return cores


# ---------------------------------------------------------------------------
# 4. Arithmetic. Every one of these grows the rank; every one needs rounding.
# ---------------------------------------------------------------------------

def tt_scale(cores, alpha):
    out = [c.copy() for c in cores]
    out[0] = out[0] * alpha
    return out


def tt_add(a, b):
    """Sum of two trains: ranks ADD. Block-diagonal stacking of the cores."""
    n = len(a)
    assert len(b) == n
    out = []
    for k in range(n):
        ra, d, ra1 = a[k].shape
        rb, _, rb1 = b[k].shape
        if k == 0:
            core = np.concatenate([a[k], b[k]], axis=2)
        elif k == n - 1:
            core = np.concatenate([a[k], b[k]], axis=0)
        else:
            core = np.zeros((ra + rb, d, ra1 + rb1))
            core[:ra, :, :ra1] = a[k]
            core[ra:, :, ra1:] = b[k]
        out.append(core)
    return out


def tt_hadamard(a, b):
    """Elementwise product: ranks MULTIPLY. This is the expensive primitive.

    chi_a * chi_b before rounding, which is why nonlinear terms are where
    tensor-train solvers hurt. Smarter schemes exist (Michailidis et al. 2025).
    """
    out = []
    for ca, cb in zip(a, b):
        ra, d, ra1 = ca.shape
        rb, _, rb1 = cb.shape
        core = np.einsum("aib,cid->acibd", ca, cb).reshape(ra * rb, d, ra1 * rb1)
        out.append(core)
    return out


def tt_dot(a, b):
    """Inner product by sweeping a 1 x r_a x r_b environment along the chain."""
    env = np.ones((1, 1))
    for ca, cb in zip(a, b):
        env = np.einsum("ac,aib->cib", env, ca)
        env = np.einsum("cib,cid->bd", env, cb)
    return float(env.reshape(()))


def tt_norm(cores):
    return np.sqrt(max(tt_dot(cores, cores), 0.0))


# ---------------------------------------------------------------------------
# 5. MPOs
# ---------------------------------------------------------------------------

def mpo_ranks(cores):
    return [cores[0].shape[0]] + [c.shape[-1] for c in cores]


def mpo_full(cores):
    """Dense 2^n x 2^n matrix. Diagnostic only -- this is the thing we avoid."""
    out = cores[0]
    for c in cores[1:]:
        out = np.tensordot(out, c, axes=([-1], [0]))
    n = len(cores)
    out = out.reshape([1] + [s for c in cores for s in c.shape[1:3]] + [1])
    perm = [0] + [1 + 2 * k for k in range(n)] + [1 + 2 * k + 1 for k in range(n)] + [2 * n + 1]
    out = out.transpose(perm)
    dout = int(np.prod([c.shape[1] for c in cores]))
    din = int(np.prod([c.shape[2] for c in cores]))
    return out.reshape(dout, din)


def mpo_identity(n, d=2):
    eye = np.eye(d).reshape(1, d, d, 1)
    return [eye.copy() for _ in range(n)]


def mpo_scale(cores, alpha):
    out = [c.copy() for c in cores]
    out[0] = out[0] * alpha
    return out


def mpo_add(a, b):
    n = len(a)
    out = []
    for k in range(n):
        ra, do, di, ra1 = a[k].shape
        rb, _, _, rb1 = b[k].shape
        if k == 0:
            core = np.concatenate([a[k], b[k]], axis=3)
        elif k == n - 1:
            core = np.concatenate([a[k], b[k]], axis=0)
        else:
            core = np.zeros((ra + rb, do, di, ra1 + rb1))
            core[:ra, :, :, :ra1] = a[k]
            core[ra:, :, :, ra1:] = b[k]
        out.append(core)
    return out


def mpo_compose(a, b):
    """Operator product (a b): MPO ranks multiply, exactly as for states.

    Needed more often than you would expect. The pressure Poisson operator, for
    instance, must be div(grad) built from the *same* difference operators used
    for the gradient and the divergence -- not the compact 3-point Laplacian.
    Mixing the two leaves a projection that does not actually project.
    """
    out = []
    for wa, wb in zip(a, b):
        pa, do, mid, qa = wa.shape
        pb, mid2, di, qb = wb.shape
        assert mid == mid2
        core = np.einsum("pikq,rkjs->prijqs", wa, wb)
        out.append(core.reshape(pa * pb, do, di, qa * qb))
    return out


def mpo_apply(mpo, tt):
    """Apply an MPO to a train. Result has bond dimension chi * chi_MPO.

    Always follow with tt_round. Skipping that is the classic first mistake:
    the rank is multiplied by chi_MPO on every step, so it grows like 3^k.
    """
    out = []
    for w, c in zip(mpo, tt):
        R, do, di, R1 = w.shape
        r, _, r1 = c.shape
        core = np.einsum("aijb,cjd->acibd", w, c).reshape(R * r, do, R1 * r1)
        out.append(core)
    return out


def mpo_round(cores, eps=1e-12, chi_max=None):
    """Round an MPO by treating (d_out, d_in) as one fat physical index."""
    shapes = [(c.shape[1], c.shape[2]) for c in cores]
    flat = [c.reshape(c.shape[0], -1, c.shape[3]) for c in cores]
    flat = tt_round(flat, eps=eps, chi_max=chi_max)
    return [f.reshape(f.shape[0], do, di, f.shape[2])
            for f, (do, di) in zip(flat, shapes)]


# ---------------------------------------------------------------------------
# 6. Quantics operators, built as finite automata on the binary digits
# ---------------------------------------------------------------------------

def qtt_shift(n, step=+1):
    """Shift matrix S with S[i, j] = 1 iff i == j + step, as a rank-2 MPO.

    The construction is a carry automaton. Write j in binary with core 0
    carrying the most significant bit. Adding one to j propagates a carry from
    the least significant end, so sweep the bond from RIGHT to LEFT and let the
    bond index c carry exactly one bit of information: "the digits to my right
    produced a carry". Then

        i_k = (j_k + c_in) mod 2,     c_out = j_k AND c_in

    with c fixed to 1 at the right edge (we are adding 1) and to 0 at the left
    edge (no overflow off the top -- that is what makes this the non-periodic
    shift). Two states, hence chi_MPO = 2. Nothing is fitted or truncated.
    """
    assert step in (+1, -1)
    core = np.zeros((2, 2, 2, 2))          # [c_out(left), i, j, c_in(right)]
    for c_in in (0, 1):
        for j in (0, 1):
            i = (j + c_in) % 2
            c_out = 1 if (j == 1 and c_in == 1) else 0
            core[c_out, i, j, c_in] = 1.0

    cores = [core.copy() for _ in range(n)]
    cores[0] = cores[0][0:1]               # left edge: no outgoing carry
    cores[-1] = cores[-1][:, :, :, 1:2]    # right edge: carry in = 1
    if step == -1:                         # i = j - 1 is the transpose
        cores = [c.transpose(0, 2, 1, 3).copy() for c in cores]
    return cores


def qtt_laplacian(n, dx=None, bc="dirichlet"):
    """Second-difference operator (S + S^T - 2 I)/dx^2 on 2^n points.

    Built by adding three MPOs and rounding: ranks 2 + 2 + 1 = 5 in, rank 3
    out. The rounding is doing real work, and you can watch it.
    """
    if bc != "dirichlet":
        raise NotImplementedError("only homogeneous Dirichlet here; see the exercise")
    dx = 2.0 ** -n if dx is None else dx
    L = mpo_add(qtt_shift(n, +1), qtt_shift(n, -1))
    L = mpo_add(L, mpo_scale(mpo_identity(n), -2.0))
    L = mpo_round(L, eps=1e-13)
    return mpo_scale(L, 1.0 / dx ** 2)


def qtt_first_derivative(n, dx=None, bc="dirichlet"):
    """Centred first difference, (u[i+1] - u[i-1]) / (2 dx).

    Note the order: S maps u[i] to u[i-1], so the forward neighbour comes from
    S^T and the operator is (S^T - S)/(2 dx), not the other way round. Getting
    this backwards costs you a sign and, in an advection term, the direction
    the flow travels.
    """
    if bc != "dirichlet":
        raise NotImplementedError("only homogeneous Dirichlet here")
    dx = 2.0 ** -n if dx is None else dx
    D = mpo_add(qtt_shift(n, -1), mpo_scale(qtt_shift(n, +1), -1.0))
    D = mpo_round(D, eps=1e-13)
    return mpo_scale(D, 1.0 / (2 * dx))


# ---------------------------------------------------------------------------
# 7. Analytic quantics cores -- the "free" route of the three in Part II
# ---------------------------------------------------------------------------

def qtt_grid(n, a=0.0, b=1.0):
    """x_i = a + (b - a) * i / 2^n as a rank-2 train.

    Rank 2 because x is affine in the digits: one bond slot carries the
    accumulated value, one carries the constant 1.
    """
    h = (b - a) / 2 ** n
    cores = []
    for k in range(n):
        w = h * 2 ** (n - 1 - k)
        c = np.zeros((2, 2, 2))
        c[0, :, 0] = 1.0                    # still accumulating
        c[1, :, 1] = 1.0                    # already finished
        c[0, 1, 1] = w                      # this digit contributes w
        c[0, 0, 1] = 0.0
        cores.append(c)
    # close the chain: enter in state 0, leave in state 1, and add the offset a
    first = np.zeros((1, 2, 2))
    first[0] = cores[0][0]
    first[0, :, 1] += a                     # constant term rides the finished slot
    cores[0] = first
    last = cores[-1][:, :, 1:2].copy()
    cores[-1] = last
    return cores


def qtt_exp(n, rate=1.0, a=0.0, b=1.0):
    """exp(rate * x) on the same grid as qtt_grid: exactly rank 1.

    exp(rate * sum_k i_k w_k) = prod_k exp(rate * i_k w_k): the exponential
    factorises over the digits, which is the cleanest example of why rank
    tracks structure rather than resolution.
    """
    h = (b - a) / 2 ** n
    cores = []
    for k in range(n):
        w = h * 2 ** (n - 1 - k)
        c = np.zeros((1, 2, 1))
        c[0, 0, 0] = 1.0
        c[0, 1, 0] = np.exp(rate * w)
        cores.append(c)
    cores[0] = cores[0] * np.exp(rate * a)
    return cores


# ---------------------------------------------------------------------------
# 8. Cross interpolation: build a train from samples, never from the array
# ---------------------------------------------------------------------------

def maxvol(A, tol=1.05, max_iter=100):
    """Row indices of a near-maximal-volume r x r submatrix of a tall A.

    Greedy row swapping (Goreinov et al. 2010). Returns `rows` such that
    A @ inv(A[rows]) has entries bounded by roughly `tol`. That bound is the
    whole reason cross interpolation is numerically stable.
    """
    m, r = A.shape
    if m <= r:
        return np.arange(m)
    # Start from column-pivoted QR of A^T: a cheap, already-decent guess at
    # r linearly independent rows. The swapping loop then improves it.
    from scipy.linalg import qr as _qr
    _, _, piv = _qr(A.T, pivoting=True, mode="economic")
    rows = np.asarray(piv[:r], dtype=int).copy()
    for _ in range(max_iter):
        B = A @ np.linalg.inv(A[rows])
        i, j = np.unravel_index(np.argmax(np.abs(B)), B.shape)
        if abs(B[i, j]) <= tol:
            break
        rows[j] = i
    return rows


def _index_rows(left, i, right, n, k):
    """Assemble full multi-indices from left pivots, the free digit, and right pivots."""
    out = np.empty((len(left) * len(i) * len(right), n), dtype=int)
    p = 0
    for l in left:
        for ii in i:
            for r in right:
                out[p, :k] = l
                out[p, k] = ii
                out[p, k + 1:] = r
                p += 1
    return out


def tt_cross(f, dims, rank=8, sweeps=3, seed=0, return_stats=False):
    """Fixed-rank TT-cross for a black-box f(multi_index_array) -> values.

    The point of the algorithm is the cost: O(n * d * rank^2) evaluations of f,
    with no dense array anywhere. `f` receives an (m, n) integer array and must
    return m values, so it can be a simulation, a lookup, or anything callable.

    This is the plain fixed-rank version (Oseledets & Tyrtyshnikov 2010). The
    rank-adaptive variants used in practice -- TCI, xfac -- add pivots where the
    local error is largest instead of fixing `rank` up front.
    """
    rng = np.random.default_rng(seed)
    n = len(dims)

    def digits(v, ds):
        out = []
        for d in reversed(ds):
            out.append(int(v % d))
            v //= d
        return tuple(reversed(out))

    # Right pivot sets. J[k] holds index tails covering digits k .. n-1.
    # These must be DISTINCT: drawing them independently at random and then
    # deduplicating silently collapses the rank when the tail space is small,
    # which is a genuinely annoying bug to find. Spread them instead.
    J = [None] * (n + 1)
    J[n] = [()]
    for k in range(n - 1, 0, -1):
        space = int(np.prod(dims[k:]))
        m = min(rank, space)
        if space <= 4 * m:
            picks = np.linspace(0, space - 1, m).round().astype(int)
        else:
            picks = rng.choice(space, size=m, replace=False)
        J[k] = [digits(v, dims[k:]) for v in sorted(set(int(v) for v in picks))]
    I = [None] * (n + 1)
    I[0] = [()]
    n_evals = 0

    for _ in range(sweeps):
        # ---- left to right: fix row pivots I[k+1] ----
        for k in range(n - 1):
            left, right = I[k], J[k + 1]
            idx = _index_rows(left, range(dims[k]), right, n, k)
            vals = np.asarray(f(idx), dtype=float)
            n_evals += len(idx)
            C = vals.reshape(len(left) * dims[k], len(right))
            Q, _ = np.linalg.qr(C)
            rows = maxvol(Q)
            # a row of Q is a (left-pivot, digit) pair; idx is ordered
            # left-major, then digit, then right-pivot, so stride by len(right)
            I[k + 1] = [tuple(idx[row * len(right), :k + 1]) for row in rows]
        # ---- right to left: fix column pivots J[k], and build the cores ----
        cores = [None] * n
        for k in range(n - 1, 0, -1):
            left, right = I[k], J[k + 1]
            idx = _index_rows(left, range(dims[k]), right, n, k)
            vals = np.asarray(f(idx), dtype=float)
            n_evals += len(idx)
            C = vals.reshape(len(left), dims[k] * len(right))
            Q, _ = np.linalg.qr(C.T)
            rows = maxvol(Q)
            core = (Q @ np.linalg.inv(Q[rows])).T
            cores[k] = core.reshape(-1, dims[k], len(right))
            J[k] = [tuple(idx[row, k:]) for row in rows]
        idx = _index_rows(I[0], range(dims[0]), J[1], n, 0)
        vals = np.asarray(f(idx), dtype=float)
        n_evals += len(idx)
        cores[0] = vals.reshape(1, dims[0], len(J[1]))

    return (cores, {"evaluations": n_evals}) if return_stats else cores


# ---------------------------------------------------------------------------
# 9. Solving A x = b on the tensor-train manifold
# ---------------------------------------------------------------------------
#
# Index conventions for the environments, once, so the einsums below read:
#
#   x core     x[k][a, i, b]        a, b  = train bonds,      i = physical
#   A core     A[k][p, i, j, q]     p, q  = operator bonds,   i = out, j = in
#   LA[k][a, p, c]   everything strictly left of site k, with a on the bra
#                    copy of x, c on the ket copy, p on the operator
#   RA[k][b, q, d]   everything from site k to the end
#   Lb[k][a, e] / Rb[k][b, f]   the same for <x|b>, e/f on the right-hand side
#
# "Environment" is just a name for a partial contraction you cache instead of
# recomputing. Building them is O(n chi^3); not building them is O(n^2 chi^3).


def _contract_left_A(LA, xc, Ac):
    t = np.einsum("apc,aib->pcib", LA, xc)
    t = np.einsum("pcib,pijq->cjbq", t, Ac)
    return np.einsum("cjbq,cjd->bqd", t, xc)


def _contract_right_A(RA, xc, Ac):
    t = np.einsum("bqd,aib->aiqd", RA, xc)
    t = np.einsum("aiqd,pijq->apjd", t, Ac)
    return np.einsum("apjd,cjd->apc", t, xc)


def _contract_left_b(Lb, xc, bc):
    t = np.einsum("ae,aib->eib", Lb, xc)
    return np.einsum("eib,eif->bf", t, bc)


def _contract_right_b(Rb, xc, bc):
    t = np.einsum("bf,aib->aif", Rb, xc)
    return np.einsum("aif,eif->ae", t, bc)


def _sweep_envs(A, b, x):
    """All right environments, so a left-to-right sweep can start at site 0."""
    n = len(x)
    RA = [None] * (n + 1)
    Rb = [None] * (n + 1)
    RA[n] = np.ones((1, 1, 1))
    Rb[n] = np.ones((1, 1))
    for k in range(n - 1, -1, -1):
        RA[k] = _contract_right_A(RA[k + 1], x[k], A[k])
        Rb[k] = _contract_right_b(Rb[k + 1], x[k], b[k])
    return RA, Rb


# The local problem can be solved two ways, and the choice is not cosmetic.
# Forming the effective matrix explicitly costs O(chi^4 d^4) memory -- at
# chi = 40 that is already a 6400 x 6400 dense matrix per site. Applying it
# without ever forming it costs O(chi^3 d^2) per matvec, so above a small size
# we switch to conjugate gradients on the implicit operator. This is exactly
# the O(chi^6) worst case versus the O(chi^4) you actually observe.

DENSE_LOCAL_LIMIT = 512


def _apply_local(x, LA, Ac, RA):
    t = np.einsum("cjd,apc->apjd", x, LA)
    t = np.einsum("apjd,pijq->aiqd", t, Ac)
    return np.einsum("aiqd,bqd->aib", t, RA)


def _apply_local_pair(x, LA, A1, A2, RA):
    t = np.einsum("cjld,apc->apjld", x, LA)
    t = np.einsum("apjld,pijq->aiqld", t, A1)
    t = np.einsum("aiqld,qkls->aikds", t, A2)
    return np.einsum("aikds,bsd->aikb", t, RA)


def _solve_local(apply_fn, rhs, shape, x0=None):
    """Dense solve for small blocks, conjugate gradients for large ones."""
    m = int(np.prod(shape))
    if m <= DENSE_LOCAL_LIMIT:
        cols = np.empty((m, m))
        basis = np.zeros(m)
        for j in range(m):
            basis[j] = 1.0
            cols[:, j] = apply_fn(basis.reshape(shape)).reshape(-1)
            basis[j] = 0.0
        cols = 0.5 * (cols + cols.T)
        reg = 1e-13 * max(np.trace(cols) / m, 1e-300)
        return np.linalg.solve(cols + reg * np.eye(m), rhs.reshape(-1)).reshape(shape)

    from scipy.sparse.linalg import LinearOperator, cg
    op = LinearOperator((m, m), matvec=lambda v: apply_fn(v.reshape(shape)).reshape(-1),
                        dtype=float)
    guess = None if x0 is None else np.asarray(x0).reshape(-1)
    sol, _ = cg(op, rhs.reshape(-1), x0=guess, rtol=1e-10, maxiter=400)
    return sol.reshape(shape)


def _local_solve(LA, Ac, RA, Lb, bc, Rb, x0=None):
    """The frozen-environment problem for a single core."""
    rhs = np.einsum("ae,eif->aif", Lb, bc)
    rhs = np.einsum("aif,bf->aib", rhs, Rb)
    shape = (LA.shape[0], Ac.shape[1], RA.shape[0])
    return _solve_local(lambda v: _apply_local(v, LA, Ac, RA), rhs, shape, x0)


def _local_solve_pair(LA, A1, A2, RA, Lb, b1, b2, Rb, x0=None):
    """Same, for two neighbouring cores contracted into one block."""
    rhs = np.einsum("ae,eif->aif", Lb, b1)
    rhs = np.einsum("aif,fkg->aikg", rhs, b2)
    rhs = np.einsum("aikg,bg->aikb", rhs, Rb)
    shape = (LA.shape[0], A1.shape[1], A2.shape[1], RA.shape[0])
    return _solve_local(lambda v: _apply_local_pair(v, LA, A1, A2, RA), rhs, shape, x0)


def _random_tt(dims, chi, seed=0):
    rng = np.random.default_rng(seed)
    n = len(dims)
    ranks = [1]
    for k in range(n - 1):
        left = int(np.prod(dims[:k + 1]))
        right = int(np.prod(dims[k + 1:]))
        ranks.append(int(min(chi, left, right)))
    ranks.append(1)
    return [rng.standard_normal((ranks[k], dims[k], ranks[k + 1])) for k in range(n)]


def als_solve(A, b, x0=None, sweeps=4, chi=8, verbose=False):
    """One-site ALS for A x = b, A symmetric positive definite.

    Freeze every core but one. With the train in mixed canonical form the local
    problem is a dense system of size r*d*r', solved exactly; sweep left, sweep
    right, repeat. The objective decreases monotonically -- but chi is whatever
    x0 had and never adapts. That single limitation is why dmrg_solve and AMEn
    (Dolgov & Savostyanov 2014) exist.

    A must be SPD. For a general A, apply this to the normal equations
    A^T A x = A^T b, and accept the squared condition number.
    """
    n = len(b)
    dims = [c.shape[1] for c in b]
    x = tt_canonicalise(x0 if x0 is not None else _random_tt(dims, chi), centre=0)

    for sweep in range(sweeps):
        RA, Rb = _sweep_envs(A, b, x)
        LA = [np.ones((1, 1, 1))] + [None] * n
        Lb = [np.ones((1, 1))] + [None] * n

        for k in range(n):                                    # left to right
            x[k] = _local_solve(LA[k], A[k], RA[k + 1], Lb[k], b[k], Rb[k + 1], x0=x[k])
            if k < n - 1:
                r, d, r1 = x[k].shape
                q, rr = np.linalg.qr(x[k].reshape(r * d, r1))
                x[k] = q.reshape(r, d, -1)
                x[k + 1] = np.tensordot(rr, x[k + 1], axes=([1], [0]))
                LA[k + 1] = _contract_left_A(LA[k], x[k], A[k])
                Lb[k + 1] = _contract_left_b(Lb[k], x[k], b[k])

        RA[n], Rb[n] = np.ones((1, 1, 1)), np.ones((1, 1))
        for k in range(n - 1, -1, -1):                        # right to left
            x[k] = _local_solve(LA[k], A[k], RA[k + 1], Lb[k], b[k], Rb[k + 1], x0=x[k])
            if k > 0:
                r, d, r1 = x[k].shape
                q, rr = np.linalg.qr(x[k].reshape(r, d * r1).T)
                x[k] = q.T.reshape(-1, d, r1)
                x[k - 1] = np.tensordot(x[k - 1], rr.T, axes=([2], [0]))
                RA[k] = _contract_right_A(RA[k + 1], x[k], A[k])
                Rb[k] = _contract_right_b(Rb[k + 1], x[k], b[k])
        if verbose:
            print(f"  ALS sweep {sweep + 1}: relative residual "
                  f"{residual(A, x, b):.3e}")
    return x


def dmrg_solve(A, b, x0=None, sweeps=4, eps=1e-8, chi_max=64, verbose=False):
    """Two-site (DMRG-style) solver: optimise a pair, split by SVD, chi adapts.

    One line of algorithm separates this from als_solve, and the behaviour is
    very different. Because the pair is split by a *truncated* SVD, the bond
    dimension is chosen by a tolerance instead of fixed in advance, and the
    extra variational freedom escapes local minima that trap one-site sweeps.
    The price is a local problem of size (r d) x (d r'), hence up to O(chi^6).
    """
    n = len(b)
    x = tt_canonicalise([c.copy() for c in (x0 if x0 is not None else b)], centre=0)

    for sweep in range(sweeps):
        RA, Rb = _sweep_envs(A, b, x)
        LA = [np.ones((1, 1, 1))] + [None] * n
        Lb = [np.ones((1, 1))] + [None] * n

        for k in range(n - 1):                                # left to right
            guess = np.tensordot(x[k], x[k + 1], axes=([2], [0]))
            pair = _local_solve_pair(LA[k], A[k], A[k + 1], RA[k + 2],
                                     Lb[k], b[k], b[k + 1], Rb[k + 2], x0=guess)
            rl, d1, d2, rr = pair.shape
            u, s, vt = np.linalg.svd(pair.reshape(rl * d1, d2 * rr),
                                     full_matrices=False)
            keep = _truncation_rank(s, eps * np.linalg.norm(s), chi_max)
            x[k] = u[:, :keep].reshape(rl, d1, keep)
            x[k + 1] = (s[:keep, None] * vt[:keep]).reshape(keep, d2, rr)
            LA[k + 1] = _contract_left_A(LA[k], x[k], A[k])
            Lb[k + 1] = _contract_left_b(Lb[k], x[k], b[k])

        RA[n], Rb[n] = np.ones((1, 1, 1)), np.ones((1, 1))
        RA[n - 1] = _contract_right_A(RA[n], x[n - 1], A[n - 1])
        Rb[n - 1] = _contract_right_b(Rb[n], x[n - 1], b[n - 1])
        for k in range(n - 2, -1, -1):                        # right to left
            guess = np.tensordot(x[k], x[k + 1], axes=([2], [0]))
            pair = _local_solve_pair(LA[k], A[k], A[k + 1], RA[k + 2],
                                     Lb[k], b[k], b[k + 1], Rb[k + 2], x0=guess)
            rl, d1, d2, rr = pair.shape
            u, s, vt = np.linalg.svd(pair.reshape(rl * d1, d2 * rr),
                                     full_matrices=False)
            keep = _truncation_rank(s, eps * np.linalg.norm(s), chi_max)
            x[k] = (u[:, :keep] * s[:keep]).reshape(rl, d1, keep)
            x[k + 1] = vt[:keep].reshape(keep, d2, rr)
            RA[k + 1] = _contract_right_A(RA[k + 2], x[k + 1], A[k + 1])
            Rb[k + 1] = _contract_right_b(Rb[k + 2], x[k + 1], b[k + 1])
        if verbose:
            print(f"  DMRG sweep {sweep + 1}: relative residual "
                  f"{residual(A, x, b):.3e},  chi = {max(tt_ranks(x))}")
    return x


def residual(A, x, b):
    """||A x - b|| / ||b||, computed entirely in tensor-train format."""
    r = tt_add(mpo_apply(A, x), tt_scale(b, -1.0))
    r = tt_round(r, eps=1e-12)
    return tt_norm(r) / tt_norm(b)
