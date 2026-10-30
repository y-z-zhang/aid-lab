"""Validate the winding-number map written by compute_slice.py (nothing here feeds the figure).

Checks
 1. dt vs dt/2: label agreement over the full grid between two independently computed maps.
 2. Early freeze vs full convergence: a random subsample of grid points (default 3000, from
    default_rng(12345)) integrated with RK4 at the coarse dt WITHOUT the early freeze until
    max |dtheta/dt| < 1e-9 (a gradient flow, so a vanishing velocity means an equilibrium), horizon
    30000; then final winding number and distance to the twisted state.
 3. Energy V = -sum cos(theta_{i+1} - theta_i) nonincreasing along those trajectories.
 4. Centre point: residual of the twisted state, its winding number, linear stability, and the
    labels of the four grid points around the centre.
 5. Freeze margin: labels with margin 0.3 rad instead of 0.05 on every 8th grid point in each
    direction (200 x 200 points), compared with the coarse map.

Result for the committed data (dt = 0.1 vs 0.05, --nsub 3000), on an Apple M4 Max:
 [1] 95 of 2,560,000 labels differ (0.0037%), all by one winding; never absorbed: 0 and 0.
 [2] 3000 of 3000 converged (median/max time 3030/5550); final label == early-freeze label for all
     3000; max_i |phi_i - 2 pi q/n| at the end 3.1e-08.
 [3] max single-step energy increase 5.7e-14 (round-off).
 [4] max |rhs| 1.2e-14, winding 15, largest nonzero Jacobian eigenvalue -2.4153e-03 (stable);
     centre labels [15, 15, 15, 15].
 [5] 0 of 40000 labels differ; never absorbed 0.

Run     python3 -I compute_slice.py --dt 0.05     (once, about 35 s; writes the dt/2 map to data/,
                                                  not committed)
        python3 -I validate.py --nsub 3000         (defaults: the two data/ files for the site figure)
        python3 -I validate.py COARSE.npz FINE.npz  (any other pair from compute_slice.py)
Runtime about 20 s with 14 worker processes on an Apple M4 Max. Prints to stdout; writes nothing.
"""
import argparse
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np  # noqa: E402
from kuramoto_ring import (TWO_PI, energy, integrate_until_absorbed, neighbour_diffs,  # noqa: E402
                           rhs, rk4_step, slice_directions, twisted_state, winding)

COARSE = os.path.join(HERE, "data", "slice_n83_q15_s7_g1600_h0.8_dt0.1.npz")
FINE = os.path.join(HERE, "data", "slice_n83_q15_s7_g1600_h0.8_dt0.05.npz")


def full_converge(args):
    th, dt, tol, t_max = args
    B = th.shape[0]
    th = th.copy()
    E_prev = energy(th)
    max_dE = -np.inf
    t_conv = np.full(B, np.nan)
    active = np.arange(B)
    cur = th
    step = 0
    n_steps = int(t_max / dt)
    while active.size and step < n_steps:
        cur = rk4_step(cur, dt)
        step += 1
        E = energy(cur)
        max_dE = max(max_dE, float((E - E_prev[active]).max()))
        E_prev[active] = E
        if step % 50 == 0:
            v = np.abs(rhs(cur)).max(axis=1)
            done = v < tol
            if done.any():
                th[active[done]] = cur[done]
                t_conv[active[done]] = step * dt
                active, cur = active[~done], cur[~done]
    if active.size:
        th[active] = cur
    return th, t_conv, max_dE


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("coarse", nargs="?", default=COARSE)
    ap.add_argument("fine", nargs="?", default=FINE)
    ap.add_argument("--nsub", type=int, default=3000)
    ap.add_argument("--sub_seed", type=int, default=12345)
    ap.add_argument("--workers", type=int, default=min(14, os.cpu_count() or 1))
    a = ap.parse_args()

    c, f = np.load(a.coarse), np.load(a.fine)
    n, qc, seed, G = int(c["n"]), int(c["q_center"]), int(c["seed"]), int(c["grid"])
    assert int(f["seed"]) == seed and int(f["grid"]) == G
    qa, qb = c["q"], f["q"]
    diff = qa != qb
    print(f"[1] dt={float(c['dt'])} vs dt={float(f['dt'])}: {int(diff.sum())} of {G*G} pixels differ "
          f"({100*diff.mean():.4f}%); never-absorbed coarse={int((~c['absorbed']).sum())}, "
          f"fine={int((~f['absorbed']).sum())}")
    if diff.any():
        print("    differing pixels |dq| values:", np.unique(np.abs(qa[diff] - qb[diff]), return_counts=True))

    # 2-3 full convergence on a subsample
    rng = np.random.default_rng(a.sub_seed)
    idx = rng.choice(G * G, size=a.nsub, replace=False)
    r, col = np.divmod(idx, G)
    half = float(c["half"]) if "half" in c.files else 1.0
    assert half == (float(f["half"]) if "half" in f.files else 1.0)
    grid = half * (-np.pi + (np.arange(G) + 0.5) * 2 * np.pi / G)
    P = slice_directions(n, seed)
    th0 = twisted_state(n, qc)
    IC = th0[None] + grid[col][:, None] * P[0][None] + grid[r][:, None] * P[1][None]
    chunks = np.array_split(np.arange(a.nsub), a.workers)
    t0 = time.time()
    with ProcessPoolExecutor(max_workers=a.workers) as ex:
        res = list(ex.map(full_converge, [(IC[ch], float(c["dt"]), 1e-9, 30000.0) for ch in chunks]))
    thf = np.concatenate([x[0] for x in res])
    tconv = np.concatenate([x[1] for x in res])
    max_dE = max(x[2] for x in res)
    qf = winding(thf)
    phi = neighbour_diffs(thf)
    dev = np.abs(phi - (TWO_PI * qf / n)[:, None]).max(axis=1)
    agree = (qf == qa[r, col])
    print(f"[2] full convergence ({time.time()-t0:.0f}s, dt={float(c['dt'])}, tol 1e-9): "
          f"{int(np.isnan(tconv).sum())} of {a.nsub} not converged by T=30000; "
          f"median/max convergence time {np.nanmedian(tconv):.0f}/{np.nanmax(tconv):.0f}")
    print(f"    final label == early-freeze label: {int(agree.sum())}/{a.nsub}; "
          f"max_i |phi_i - 2 pi q/n| at end: {dev.max():.2e}")
    print(f"[3] max single-step energy increase along {a.nsub} trajectories: {max_dE:.2e}")

    # 4 centre point
    res0 = np.abs(rhs(th0[None])).max()
    lam = -2 * np.cos(TWO_PI * qc / n) * (1 - np.cos(TWO_PI * np.arange(n) / n))
    m = G // 2
    print(f"[4] twisted state q={qc}: max|rhs|={res0:.1e}, winding={int(winding(th0[None])[0])}, "
          f"largest nonzero Jacobian eigenvalue={np.sort(lam)[-2]:.4e} (stable if <0); "
          f"labels of the 4 centre pixels: {qa[m-1:m+1, m-1:m+1].ravel().tolist()}")

    # 5 freeze-margin sensitivity on every 8th grid point
    sub = np.arange(0, G, 8)
    A1, A2 = np.meshgrid(grid[sub], grid[sub])
    ICm = th0[None] + A1.reshape(-1, 1) * P[0][None] + A2.reshape(-1, 1) * P[1][None]
    q30, _, ab30, _ = integrate_until_absorbed(ICm, float(c["dt"]), float(c["tmax"]), margin=0.3)
    ref = qa[np.ix_(sub, sub)].ravel()
    print(f"[5] margin 0.3 vs 0.05: {int((q30 != ref).sum())} of {ref.size} labels differ; "
          f"never absorbed {int((~ab30).sum())}")
