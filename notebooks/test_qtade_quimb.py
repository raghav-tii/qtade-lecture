"""Sanity checks for the Part III/IV layer. Run: python3 test_qtade_quimb.py"""
import numpy as np
import qtade_tn as tn
import qtade_quimb as qq


def chk(name, cond, extra=""):
    print(("PASS " if cond else "FAIL ") + name, extra)
    assert cond, name


n = 5
x = np.linspace(0, 1, 2 ** n, endpoint=False)
h = x[1] - x[0]
fx = tn.qtt_from_vector(np.sin(2 * np.pi * x), eps=1e-13)
gy = tn.qtt_from_vector(np.exp(-x), eps=1e-13)
prod = qq._splice(fx, gy)
ref = np.outer(np.sin(2 * np.pi * x), np.exp(-x))

chk("separable 2-D field", np.allclose(qq.to_grid(prod), ref))
chk("quimb round trip", np.allclose(qq.to_grid(qq.cores(qq.to_mps(prod))), ref))

mps = qq.to_mps(prod)
L = qq.laplacian_2d(n, h=h)
got = qq.to_grid(qq.cores(qq.apply(L, mps, cutoff=1e-12)))
r2 = np.zeros_like(ref)
r2[1:-1, :] += (ref[2:, :] - 2 * ref[1:-1, :] + ref[:-2, :]) / h ** 2
r2[0, :] += (ref[1, :] - 2 * ref[0, :]) / h ** 2
r2[-1, :] += (ref[-2, :] - 2 * ref[-1, :]) / h ** 2
r2[:, 1:-1] += (ref[:, 2:] - 2 * ref[:, 1:-1] + ref[:, :-2]) / h ** 2
r2[:, 0] += (ref[:, 1] - 2 * ref[:, 0]) / h ** 2
r2[:, -1] += (ref[:, -2] - 2 * ref[:, -1]) / h ** 2
chk("2-D Laplacian", np.allclose(got, r2, atol=1e-6),
    f"MPO rank {max(tn.mpo_ranks(L))}")

D = qq.derivative_2d(n, 0, h=h)
gd = qq.to_grid(qq.cores(qq.apply(D, mps, cutoff=1e-12)))
rd = np.zeros_like(ref)
rd[1:-1, :] = (ref[2:, :] - ref[:-2, :]) / (2 * h)
rd[0, :] = ref[1, :] / (2 * h)
rd[-1, :] = -ref[-2, :] / (2 * h)
chk("2-D d/dx", np.allclose(gd, rd, atol=1e-8))

chk("Hadamard", np.allclose(qq.to_grid(qq.cores(qq.hadamard(mps, mps, cutoff=1e-12))),
                            ref * ref, atol=1e-9))
chk("coarse-grained readout",
    np.allclose(qq.to_grid(qq.coarse_grain(mps, 3)),
                ref.reshape(8, 4, 8, 4).mean(axis=(1, 3)), atol=1e-10))

bits = [0, 1, 1, 0, 0, 1, 1, 1, 0, 0]
ix = int("".join(map(str, bits[0::2])), 2)
iy = int("".join(map(str, bits[1::2])), 2)
chk("pointwise evaluate", abs(qq.evaluate(mps, bits) - ref[ix, iy]) < 1e-12)

A = tn.mpo_round(tn.mpo_add(tn.mpo_identity(2 * n), tn.mpo_scale(L, -1e-5)), 1e-13)
xs = qq.solve(A, mps, sweeps=3, cutoff=1e-10, max_bond=32)
res = tn.residual(A, qq.cores(xs), prod)
chk("2-D implicit solve", res < 1e-9, f"residual {res:.2e}")

chk("stacked vs interleaved MPO rank",
    max(tn.mpo_ranks(qq.laplacian_2d(n, h=h, ordering="stacked"))) <= 5,
    f"stacked {max(tn.mpo_ranks(qq.laplacian_2d(n, h=h, ordering='stacked')))}, "
    f"interleaved {max(tn.mpo_ranks(L))}")

print("\nALL TESTS PASSED")
