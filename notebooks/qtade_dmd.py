"""qtade_dmd -- dynamic mode decomposition, dense and inside a space-time MPS.

Part IV inverts the problem of Part III: the snapshots are given and the
operator is wanted. The bottleneck of standard DMD is the SVD of an
N_x x N_t snapshot matrix. The observation that makes MPS-DMD work is that a
space-time tensor train *already contains* that SVD: gauge it to mixed
canonical form at the bond separating the space sites from the time sites, and
the Schmidt decomposition across that bond IS U Sigma V^dagger.

Everything below therefore costs O((n_x + n_t) chi^3) -- logarithmic in both
N_x and N_t -- and never forms a snapshot matrix.

Reference: Peddinti et al., arXiv:2510.21767.
"""

from __future__ import annotations

import numpy as np

import qtade_tn as tn

__all__ = ["exact_dmd", "space_time_qtt", "mps_dmd", "predict", "predict_dense"]


# ---------------------------------------------------------------------------
# The textbook version, for comparison
# ---------------------------------------------------------------------------

def exact_dmd(X, rank=None):
    """Standard exact DMD on a dense N_x x N_t snapshot matrix (Tu et al. 2014)."""
    X1, X2 = X[:, :-1], X[:, 1:]
    U, s, Vt = np.linalg.svd(X1, full_matrices=False)
    r = rank or np.sum(s > 1e-12 * s[0])
    U, s, Vt = U[:, :r], s[:r], Vt[:r]
    At = U.conj().T @ X2 @ Vt.conj().T @ np.diag(1.0 / s)
    lam, W = np.linalg.eig(At)
    Phi = U @ W
    b = np.linalg.lstsq(Phi, X[:, 0], rcond=None)[0]
    return {"eigenvalues": lam, "modes": Phi, "amplitudes": b, "rank": r}


# ---------------------------------------------------------------------------
# Building the space-time train
# ---------------------------------------------------------------------------

def space_time_qtt(X, eps=1e-10, chi_max=None, order="space-time"):
    """Dense 2^n_x x 2^n_t snapshot matrix -> one quantics train over both.

    Time stops being a loop and becomes more legs on the same chain. The bond
    at the space/time interface then measures temporal complexity directly: a
    travelling wave and a standing wave are told apart by one integer.

    `order` is "space-time" or "time-space". Space-then-time is the usual
    choice; the ordering matters for the same reason bit interleaving does.
    """
    nx = int(round(np.log2(X.shape[0])))
    nt = int(round(np.log2(X.shape[1])))
    assert 2 ** nx == X.shape[0] and 2 ** nt == X.shape[1]
    A = X.reshape([2] * (nx + nt))
    if order == "time-space":
        perm = list(range(nx, nx + nt)) + list(range(nx))
        A = A.transpose(perm)
    return tn.tt_svd(A, eps=eps, chi_max=chi_max)


# ---------------------------------------------------------------------------
# MPS-DMD
# ---------------------------------------------------------------------------

def _overlap_matrix(a_cores, b_cores):
    """M[p, q] = sum_t a[p, t] b[q, t], for two trains with an open left bond."""
    env = np.ones((1, 1))
    for ca, cb in zip(reversed(a_cores), reversed(b_cores)):
        env = np.einsum("pib,qid,bd->pq", ca, cb, env)
    return env


def mps_dmd(cores, n_space, rank=None, shift_eps=1e-12):
    """DMD carried out inside a space-time tensor train.

    Three steps, no snapshot matrix anywhere:

    1. gauge to mixed canonical form at the space/time bond, so the left block
       is an isometry U and the Schmidt values are Sigma;
    2. shift the time index with a rank-2 MPO and project,
       A~ = Sigma (V^dagger T V) Sigma^{-1}, a chi x chi matrix;
    3. eigendecompose A~. Modes are Phi = U W, still in train form.

    Returns a dict; pass it to `predict`.

    The one subtlety is the last snapshot. The non-periodic shift sends it to
    zero, so the raw projection is Q P^T rather than the least-squares
    Q P^+ that DMD actually wants. Writing V^dagger's final column as v,

        P P^T = I - v v^T,

    so one Sherman-Morrison rank-one correction recovers exact DMD. Skipping it
    damps every eigenvalue by roughly 1/N_t per step -- invisible in the
    spectrum, ruinous after a few hundred steps of prediction. The exercises
    make you look at both.
    """
    n = len(cores)
    n_time = n - n_space
    assert n_time >= 1

    # --- 1. gauge: left block left-orthogonal, right block right-orthogonal ---
    g = tn.tt_canonicalise(cores, centre=n_space - 1)
    c = g[n_space - 1]
    r, d, r1 = c.shape
    u, s, vt = np.linalg.svd(c.reshape(r * d, r1), full_matrices=False)
    k = len(s) if rank is None else min(rank, len(s))
    k = max(1, min(k, int(np.sum(s > 1e-14 * s[0]))))
    u, s, vt = u[:, :k], s[:k], vt[:k]

    left = g[:n_space - 1] + [u.reshape(r, d, k)]        # isometry U, as a train
    right = [np.tensordot(vt, g[n_space], axes=([1], [0]))] + g[n_space + 1:]

    # --- 2. shift time by one and project ---
    S = tn.qtt_shift(n_time, -1)                          # (Su)[t] = u[t+1]
    shifted = tn.tt_round(tn.mpo_apply(S, right), eps=shift_eps)
    M = _overlap_matrix(shifted, right)                   # = Q P^T

    # v = V^dagger[:, last]: the time train evaluated at all-ones time bits.
    v = np.eye(right[0].shape[0])
    for core in right:
        v = v @ core[:, -1, :]
    v = v.reshape(-1)
    denom = 1.0 - float(v @ v)
    if abs(denom) < 1e-12:                                # degenerate, skip it
        Minv = M
    else:
        Minv = M + np.outer(M @ v, v) / denom             # M (I - v v^T)^{-1}
    At = (s[:, None] * Minv) / s[None, :]

    lam, W = np.linalg.eig(At)

    # --- 3. amplitudes from the first snapshot: b = W^{-1} Sigma V^dagger[:, 0] ---
    # V^dagger[:, 0] is the time train evaluated at all-zero time bits: one
    # matrix chain of length n_time, never a column of a 2^n_t-wide matrix.
    acc = np.eye(right[0].shape[0])
    for core in right:
        acc = acc @ core[:, 0, :]
    b = np.linalg.solve(W, s * acc.reshape(-1))

    return {"eigenvalues": lam, "W": W, "U": left, "sigma": s,
            "amplitudes": b, "rank": k, "n_space": n_space, "At": At}


def mode(result, j):
    """Spatial mode j as a tensor train (contract U's open bond with W[:, j])."""
    left = [c.copy() for c in result["U"]]
    left[-1] = np.tensordot(left[-1], result["W"][:, j].astype(complex),
                            axes=([2], [0]))[:, :, None]
    return left


def predict(result, steps):
    """Predicted field after `steps` timesteps, as a tensor train.

    x(T + k) = U W Lambda^k b: one chi x chi diagonal multiply, then a single
    contraction of the open bond. Cost O(n_x chi^3), independent of how far
    ahead you predict.
    """
    coef = result["W"] @ (result["eigenvalues"] ** steps * result["amplitudes"])
    left = [c.astype(complex) for c in result["U"]]
    left[-1] = np.tensordot(left[-1], coef, axes=([2], [0]))[:, :, None]
    return left


def predict_dense(result, steps):
    """Same, reconstructed to a dense vector. Diagnostic only."""
    return np.real(tn.tt_full(predict(result, steps)).reshape(-1))
