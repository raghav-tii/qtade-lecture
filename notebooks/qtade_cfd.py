"""qtade_cfd -- an incompressible flow solver whose state never leaves TT form.

This is the Part III demonstrator: Chorin's projection method (1968) with every
field stored as a quantics tensor train over interleaved x and y bits, and
every operator stored as an MPO. The whole timestep is four primitives:

    MPO application        derivatives and the Laplacian
    Hadamard product       the nonlinear advection term
    linear solve           the pressure Poisson equation
    rounding               after every single one of the above

Scope, stated honestly. Boundary conditions here are homogeneous Dirichlet on
every wall, inherited from the difference operators; there is no ghost-cell
inlet/outlet treatment and no immersed geometry. Those are what turn this into
the solver of Peddinti et al. (2024), and they are the difference between a
teaching demonstrator and a validated code. What this file does reproduce
faithfully is the cost structure: the Poisson solve dominates, and the rank is
the thing to watch.
"""

from __future__ import annotations

import time

import numpy as np

import qtade_quimb as qq
import qtade_tn as tn

__all__ = ["Flow", "divergence", "energy"]


class Flow:
    """Incompressible Navier-Stokes on a 2^n x 2^n box, entirely in TT format."""

    def __init__(self, n, nu=1e-3, dt=None, chi_max=40, cutoff=1e-8,
                 poisson_sweeps=1, ordering="interleaved"):
        self.n = n
        self.N = 2 ** n
        self.h = 1.0 / self.N
        self.nu = nu
        self.dt = dt if dt is not None else 0.2 * self.h
        self.chi_max = chi_max
        self.cutoff = cutoff
        self.poisson_sweeps = poisson_sweeps

        self.Dx = qq.derivative_2d(n, 0, h=self.h, ordering=ordering)
        self.Dy = qq.derivative_2d(n, 1, h=self.h, ordering=ordering)
        self.L = qq.laplacian_2d(n, h=self.h, ordering=ordering)
        # The pressure operator is div(grad) built from the SAME differences as
        # the gradient and divergence above. Using the compact 3-point Laplacian
        # here instead leaves a projection that removes only most of the
        # divergence -- a bug that looks like "the solver is a bit inaccurate".
        self.Lp = tn.mpo_round(
            tn.mpo_add(tn.mpo_compose(self.Dx, self.Dx),
                       tn.mpo_compose(self.Dy, self.Dy)), eps=1e-12)
        self._p = None                      # previous pressure: the warm start
        self.timings = {"predictor": 0.0, "poisson": 0.0, "projection": 0.0}
        self.rank_history = []

    # -- the four primitives, each followed by rounding ---------------------

    def _apply(self, mpo, f):
        return tn.tt_round(tn.mpo_apply(mpo, f), eps=self.cutoff,
                           chi_max=self.chi_max)

    def _mul(self, a, b):
        return tn.tt_round(tn.tt_hadamard(a, b), eps=self.cutoff,
                           chi_max=self.chi_max)

    def _add(self, *fields):
        out = fields[0]
        for f in fields[1:]:
            out = tn.tt_add(out, f)
        return tn.tt_round(out, eps=self.cutoff, chi_max=self.chi_max)

    # -- one Chorin step ----------------------------------------------------

    def step(self, u, v):
        dt, nu = self.dt, self.nu

        # 1. predictor: advection by Hadamard products, diffusion by an MPO.
        t0 = time.perf_counter()
        adv_u = self._add(self._mul(u, self._apply(self.Dx, u)),
                          self._mul(v, self._apply(self.Dy, u)))
        adv_v = self._add(self._mul(u, self._apply(self.Dx, v)),
                          self._mul(v, self._apply(self.Dy, v)))
        us = self._add(u, tn.tt_scale(adv_u, -dt), tn.tt_scale(self._apply(self.L, u), nu * dt))
        vs = self._add(v, tn.tt_scale(adv_v, -dt), tn.tt_scale(self._apply(self.L, v), nu * dt))
        t1 = time.perf_counter()

        # 2. pressure: the only global coupling, and the only linear solve.
        rhs = tn.tt_scale(self._add(self._apply(self.Dx, us),
                                    self._apply(self.Dy, vs)), 1.0 / dt)
        p = tn.dmrg_solve(self.Lp, rhs, x0=self._p, sweeps=self.poisson_sweeps,
                          eps=self.cutoff, chi_max=self.chi_max)
        self._p = p
        t2 = time.perf_counter()

        # 3. projection: subtract the pressure gradient, restore div(v) = 0.
        u_new = self._add(us, tn.tt_scale(self._apply(self.Dx, p), -dt))
        v_new = self._add(vs, tn.tt_scale(self._apply(self.Dy, p), -dt))
        t3 = time.perf_counter()

        self.timings["predictor"] += t1 - t0
        self.timings["poisson"] += t2 - t1
        self.timings["projection"] += t3 - t2
        self.rank_history.append(max(max(tn.tt_ranks(u_new)), max(tn.tt_ranks(v_new))))
        return u_new, v_new, p

    def poisson_share(self):
        total = sum(self.timings.values())
        return self.timings["poisson"] / total if total else float("nan")

    def divergence(self, u, v):
        return divergence(self, u, v)


def divergence(flow, u, v):
    """div(u, v) as a train, for checking what the projection actually did."""
    d = tn.tt_add(tn.mpo_apply(flow.Dx, u), tn.mpo_apply(flow.Dy, v))
    return tn.tt_round(d, eps=1e-12)


def energy(u, v):
    """Kinetic energy, computed without decompressing anything."""
    return 0.5 * (tn.tt_dot(u, u) + tn.tt_dot(v, v))
