"""qtade_quimb -- the Part III / Part IV layer, built on `quimb`.

Parts I and II build everything by hand (`qtade_tn`). From Part III the
problems get big enough that hand-rolled contraction is the bottleneck, so we
switch to a library. `quimb` supplies what is genuinely worth not rewriting:
canonical forms, a good compression implementation, and fast contraction.

It does **not** supply a linear solver for `A x = b` -- almost no tensor-network
library does, because the quantum-physics use case wants ground states instead.
That gap is the honest lesson of this module: you will always end up writing
some of the numerics yourself. Here `solve` delegates to the DMRG solver from
Part II; in production you would reach for AMEn (`ttpy`, `torchtt`) or `xfac`.

Cores are stored exactly as in `qtade_tn`, so moving between the two is a
relabelling and not a conversion:

    MPS core  (left, physical, right)          -> quimb shape "lpr"
    MPO core  (left, out, in, right)           -> quimb shape "ludr"
"""

from __future__ import annotations

import numpy as np
import quimb.tensor as qtn

import qtade_tn as tn

__all__ = [
    "to_mps", "to_mpo", "cores", "mpo_cores",
    "interleave_state", "interleave_operator", "stacked_operator",
    "laplacian_2d", "derivative_2d", "hadamard", "apply", "solve",
    "coarse_grain", "evaluate", "to_grid", "max_bond", "n_params",
]


# ---------------------------------------------------------------------------
# Conversions
# ---------------------------------------------------------------------------

def to_mps(core_list):
    """List of (left, physical, right) arrays -> quimb MPS.

    quimb wants the two boundary tensors without their trivial bond, so the
    length-1 edges are squeezed off here and put back by `cores`.
    """
    arrs = [np.asarray(c) for c in core_list]
    arrs[0] = arrs[0].reshape(arrs[0].shape[1:])
    arrs[-1] = arrs[-1].reshape(arrs[-1].shape[:-1])
    return qtn.MatrixProductState(arrs, shape="lpr")


def to_mpo(core_list):
    """List of (left, out, in, right) arrays -> quimb MPO."""
    arrs = [np.asarray(c) for c in core_list]
    arrs[0] = arrs[0].reshape(arrs[0].shape[1:])
    arrs[-1] = arrs[-1].reshape(arrs[-1].shape[:-1])
    return qtn.MatrixProductOperator(arrs, shape="ludr")


def cores(mps):
    """quimb MPS -> list of (left, physical, right) arrays, boundaries padded."""
    mps = mps.copy()
    mps.permute_arrays("lpr")
    arrs = [np.asarray(a) for a in mps.arrays]
    arrs[0] = arrs[0].reshape(1, *arrs[0].shape)
    arrs[-1] = arrs[-1].reshape(*arrs[-1].shape, 1)
    return arrs


def mpo_cores(mpo):
    """quimb MPO -> list of (left, out, in, right) arrays, boundaries padded."""
    mpo = mpo.copy()
    mpo.permute_arrays("ludr")
    arrs = [np.asarray(a) for a in mpo.arrays]
    arrs[0] = arrs[0].reshape(1, *arrs[0].shape)
    arrs[-1] = arrs[-1].reshape(*arrs[-1].shape, 1)
    return arrs


def max_bond(mps):
    return int(mps.max_bond())


def n_params(mps):
    return int(sum(t.size for t in mps))


# ---------------------------------------------------------------------------
# Bit ordering: the one modelling choice that is not an implementation detail
# ---------------------------------------------------------------------------

def _pass_through_mpo_core(R):
    """An MPO core that does nothing to its site but carries the bond along."""
    c = np.zeros((R, 2, 2, R))
    for p in range(R):
        c[p, 0, 0, p] = 1.0
        c[p, 1, 1, p] = 1.0
    return c


def interleave_state(cx, cy):
    """Interleave two 1-D trains into x1 y1 x2 y2 ... (a separable 2-D field).

    Interleaved ordering keeps each *scale* local along the chain, so a bond
    measures the coupling between scale 2^-k of x and scale 2^-k of y. Stacked
    ordering (all x bits, then all y bits) puts one cut between x_n and y_1 that
    every x-y correlation must cross, at every scale at once.
    """
    assert len(cx) == len(cy)
    out = []
    # A product f(x) g(y) is exact at bond dimension chi_x * chi_y; here the two
    # chains are simply spliced and the bond carries both.
    for a, b in zip(cx, cy):
        out.append(a)
        out.append(b)
    # fix up the bonds: the x core's right bond must meet the y core's left bond
    return _splice(cx, cy)


def _splice(cx, cy):
    """Exact MPS for the product f(x)*g(y) in interleaved bit order."""
    n = len(cx)
    out = []
    for k in range(n):
        ax, ay = cx[k], cy[k]
        rxl, _, rxr = ax.shape
        ryl, _, ryr = ay.shape
        # x site: bond carries (x-bond, y-bond-so-far); y-bond is passed through
        cxx = np.einsum("aib,cd->acibd", ax, np.eye(ryl)).reshape(rxl * ryl, 2, rxr * ryl)
        cyy = np.einsum("ab,cid->acibd", np.eye(rxr), ay).reshape(rxr * ryl, 2, rxr * ryr)
        out.append(cxx)
        out.append(cyy)
    return out


def interleave_operator(op_cores, which, n):
    """Embed a 1-D MPO acting on one coordinate into an interleaved 2-D chain.

    `which` is 0 for x (even sites) or 1 for y (odd sites). Sites belonging to
    the other coordinate get a pass-through core, which is what "identity on
    the other factor" looks like as an MPO.
    """
    assert len(op_cores) == n
    out = []
    for k in range(n):
        R_in = op_cores[k].shape[0]
        R_out = op_cores[k].shape[3]
        if which == 0:
            out.append(op_cores[k])
            out.append(_pass_through_mpo_core(R_out))
        else:
            out.append(_pass_through_mpo_core(R_in))
            out.append(op_cores[k])
    return out


def stacked_operator(op_cores, which, n):
    """The same embedding for stacked ordering x1..xn y1..yn."""
    eye = np.eye(2).reshape(1, 2, 2, 1)
    ident = [eye.copy() for _ in range(n)]
    return op_cores + ident if which == 0 else ident + op_cores


def laplacian_2d(n, h=None, ordering="interleaved"):
    """d^2/dx^2 + d^2/dy^2 on a 2^n x 2^n grid, as an MPO over 2n binary sites."""
    h = 2.0 ** -n if h is None else h
    lx = tn.qtt_laplacian(n, dx=h)
    embed = interleave_operator if ordering == "interleaved" else stacked_operator
    L = tn.mpo_add(embed(lx, 0, n), embed(lx, 1, n))
    return tn.mpo_round(L, eps=1e-13)


def derivative_2d(n, axis, h=None, ordering="interleaved"):
    """Centred first derivative along `axis` (0 = x, 1 = y)."""
    h = 2.0 ** -n if h is None else h
    d = tn.qtt_first_derivative(n, dx=h)
    embed = interleave_operator if ordering == "interleaved" else stacked_operator
    return tn.mpo_round(embed(d, axis, n), eps=1e-13)


# ---------------------------------------------------------------------------
# The two operations every timestep is made of
# ---------------------------------------------------------------------------

def apply(mpo, mps, max_bond=None, cutoff=1e-10):
    """MPO-MPS product followed by compression. Never skip the compression."""
    out = (mpo if isinstance(mpo, qtn.MatrixProductOperator) else to_mpo(mpo)).apply(
        mps if isinstance(mps, qtn.MatrixProductState) else to_mps(mps))
    out.compress(max_bond=max_bond, cutoff=cutoff)
    return out


def _diagonal_mpo(mps):
    """Turn an MPS into the diagonal MPO diag(v). Costs nothing: same cores."""
    ops = []
    for c in cores(mps):
        r, d, r1 = c.shape
        w = np.zeros((r, d, d, r1))
        for i in range(d):
            w[:, i, i, :] = c[:, i, :]
        ops.append(w)
    return to_mpo(ops)


def hadamard(a, b, max_bond=None, cutoff=1e-10):
    """Elementwise product of two fields.

    Implemented as diag(a) applied to b, which is the cheapest correct way to
    say it: the result has bond dimension chi_a * chi_b before compression.
    Every nonlinear term in Part III costs exactly this.
    """
    return apply(_diagonal_mpo(a), b, max_bond=max_bond, cutoff=cutoff)


def solve(A, b, x0=None, sweeps=3, cutoff=1e-9, max_bond=64, verbose=False):
    """Solve A x = b for an SPD MPO A, using the Part II two-site DMRG solver.

    quimb has no linear solver, so this is the seam where the library stops and
    your own numerics start. The conversion is free -- both sides are the same
    list of cores -- but the solver is ours.
    """
    Ac = mpo_cores(A) if isinstance(A, qtn.MatrixProductOperator) else A
    bc = cores(b) if isinstance(b, qtn.MatrixProductState) else b
    xc = None
    if x0 is not None:
        xc = cores(x0) if isinstance(x0, qtn.MatrixProductState) else x0
    out = tn.dmrg_solve(Ac, bc, x0=xc, sweeps=sweeps, eps=cutoff,
                        chi_max=max_bond, verbose=verbose)
    return to_mps(out)


# ---------------------------------------------------------------------------
# Readout without decompression
# ---------------------------------------------------------------------------

def coarse_grain(mps, keep):
    """Average-pool onto a 2^keep-per-axis grid by contracting the finest bits.

    Contracting a physical leg against (1,1)/2 averages over that bit, i.e.
    coarse-grains by one level. Doing that to the finest 2*(n-keep) sites of an
    interleaved chain gives a viewable picture at cost O(n chi^3) -- the dense
    2^(2n) field is never formed. Without a readout like this the compression
    buys nothing, because you could not look at the answer.
    """
    cs = cores(mps)
    total = len(cs) // 2
    drop = total - keep
    assert drop >= 0
    out = list(cs[: 2 * keep])
    tail = np.ones((1, 1))
    for c in reversed(cs[2 * keep:]):
        v = np.full(c.shape[1], 1.0 / c.shape[1])
        m = np.einsum("aib,i->ab", c, v)
        tail = m @ tail
    if drop:
        out[-1] = np.einsum("aib,bc->aic", out[-1], tail)
    return out


def evaluate(mps, bits):
    """Value at a single grid point, from the binary index. Cost O(n chi^2).

    Accepts either a quimb MPS or a raw list of cores. Pass the cores in a loop:
    converting a quimb object costs more than the evaluation itself.
    """
    cs = mps if isinstance(mps, list) else cores(mps)
    v = np.ones((1, 1))
    for c, i in zip(cs, bits):
        v = v @ c[:, i, :]
    return float(v.reshape(()))


def from_grid(f, eps=1e-10, chi_max=None, ordering="interleaved"):
    """Dense 2^n x 2^n field -> quantics train in the chosen bit order.

    TT-SVD, so this is O(4^n) and only for setting up small examples. A real
    initial condition is built with TT-cross instead (Part II) -- otherwise you
    have already paid the price the method was supposed to avoid.
    """
    n = int(round(np.log2(f.shape[0])))
    a = np.asarray(f).reshape([2] * (2 * n))
    if ordering == "interleaved":
        perm = sum([[i, n + i] for i in range(n)], [])
        a = a.transpose(perm)
    return tn.tt_svd(np.ascontiguousarray(a), eps=eps, chi_max=chi_max)


def to_grid(mps, keep=None):
    """Dense 2-D array for plotting, optionally coarse-grained first."""
    cs = cores(mps) if isinstance(mps, qtn.MatrixProductState) else mps
    total = len(cs) // 2
    if keep is not None and keep < total:
        cs = coarse_grain(to_mps(cs), keep)
        total = keep
    flat = tn.tt_full(cs).reshape(-1)
    # de-interleave: site order is x1 y1 x2 y2 ..., so reshape and transpose
    a = flat.reshape([2] * (2 * total))
    perm = list(range(0, 2 * total, 2)) + list(range(1, 2 * total, 2))
    return a.transpose(perm).reshape(2 ** total, 2 ** total)
