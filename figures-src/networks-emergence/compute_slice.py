"""Compute the winding-number map that render.py draws: which twisted state each point of a 2-D slice
of state space ends in, for a ring of identical Kuramoto oscillators.

Provenance: Zhang & Strogatz, "Basins with tentacles", PRL 127, 194101 (2021), Eq. 1 and the slice
construction of Fig. 4 (system, slice and integrator documented in kuramoto_ring.py).

Defaults (= the committed data file used by the site figure)
  n = 83 oscillators (the n used throughout the Letter; Fig. 4 does not state its n), slice centred
  on the q = 15 twisted state, slice directions P1, P2 (41 ones each) from default_rng(7). Seed 7 is
  a single realisation, picked for the picture from seeds 1, 7, 42 and 2021 that were tried.
  Window a1, a2 in [-0.8 pi, 0.8 pi] (--half 0.8 of the paper's (-pi, pi]) on a 1600 x 1600 grid of
  cell centres a_k = half * (-pi + (k + 1/2) * 2 pi / G); row index = a2, column index = a1, row 0 at
  a2 = -half * pi. RK4 with dt = 0.1, horizon t_max = 2000, early freeze once
  max_i |theta_{i+1} - theta_i| < pi/2 - 0.05 (checked every 10 steps; see kuramoto_ring.py). Every
  point is absorbed, by t = 24 at the latest (median 4), so the horizon is never reached.
  Each row of the grid is integrated as one batch; rows are spread over worker processes, which does
  not change the result. No randomness besides the seeded slice directions.

Why the 0.8 pi window is enough: on the full slice (-pi, pi]^2 (same n, q, seed, grid, dt), every
point that ends within 10 windings of the centre (q_final >= 5) lies within |a1| <= 0.634 pi and
|a2| <= 0.627 pi, inside both the window and the 0.72 pi view that render.py draws.

Validation (validate.py; results for these defaults): dt = 0.1 vs dt = 0.05 labels differ on 95 of
2,560,000 grid points (0.0037%), all by one winding; 3000 random points integrated without the early
freeze to max |dtheta/dt| < 1e-9 all end in the twisted state the early freeze predicted; energy
nonincreasing along all of them (max single-step increase 5.7e-14, round-off); the centre is the
stable q = 15 twisted state. A freeze margin of 0.3 instead of 0.05 changes 0 of 40,000 labels
(every 8th point in both directions).

Run     python3 -I compute_slice.py                      (writes the default file below)
        python3 -I compute_slice.py --dt 0.05            (the dt/2 map validate.py compares against)
        python3 -I compute_slice.py --out OTHER.npz      (any other location)
Runtime about 18 s with 14 worker processes on an Apple M4 Max (dt = 0.05: about 35 s).
Writes  data/slice_n{n}_q{q}_s{seed}_g{grid}_h{half}_dt{dt}.npz next to this script unless --out is
        given; the default run writes data/slice_n83_q15_s7_g1600_h0.8_dt0.1.npz (about 0.55 MB),
        holding q (int16, final winding number), t_freeze (float32), absorbed (bool), the parameters,
        P (the slice directions) and wall (seconds; the only field that changes between runs).
"""
import argparse
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np  # noqa: E402
from kuramoto_ring import integrate_until_absorbed, slice_directions, twisted_state  # noqa: E402


def grid_points(G, half):
    return half * (-np.pi + (np.arange(G) + 0.5) * 2 * np.pi / G)


def default_out(n, q, seed, grid, half, dt):
    return os.path.join(HERE, "data", f"slice_n{n}_q{q}_s{seed}_g{grid}_h{half:g}_dt{dt:g}.npz")


def work(args):
    n, qc, seed, G, dt, t_max, rows, half = args
    P = slice_directions(n, seed)
    th0 = twisted_state(n, qc)
    a = grid_points(G, half)
    out_q = np.empty((len(rows), G), dtype=np.int16)
    out_t = np.empty((len(rows), G), dtype=np.float32)
    out_ab = np.empty((len(rows), G), dtype=bool)
    for r_i, r in enumerate(rows):
        IC = th0[None, :] + a[:, None] * P[0][None, :] + a[r] * P[1][None, :]
        q, tf, ab, _ = integrate_until_absorbed(IC, dt, t_max)
        out_q[r_i], out_t[r_i], out_ab[r_i] = q, tf, ab
    return rows, out_q, out_t, out_ab


def compute(n, qc, seed, G, dt, t_max, workers=14, rows_per_task=8, half=1.0):
    q = np.empty((G, G), dtype=np.int16)
    tf = np.empty((G, G), dtype=np.float32)
    ab = np.empty((G, G), dtype=bool)
    tasks = [(n, qc, seed, G, dt, t_max, list(range(s, min(s + rows_per_task, G))), half)
             for s in range(0, G, rows_per_task)]
    with ProcessPoolExecutor(max_workers=workers) as ex:
        for rows, oq, ot, oab in ex.map(work, tasks):
            q[rows], tf[rows], ab[rows] = oq, ot, oab
    return q, tf, ab


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=83)
    ap.add_argument("--q", type=int, default=15)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--grid", type=int, default=1600)
    ap.add_argument("--dt", type=float, default=0.1)
    ap.add_argument("--tmax", type=float, default=2000.0)
    ap.add_argument("--workers", type=int, default=min(14, os.cpu_count() or 1))
    ap.add_argument("--half", type=float, default=0.8)
    ap.add_argument("--out", default=None, help="output .npz (default: data/<name from parameters>)")
    a = ap.parse_args()
    out = a.out or default_out(a.n, a.q, a.seed, a.grid, a.half, a.dt)
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    t0 = time.time()
    q, tf, ab = compute(a.n, a.q, a.seed, a.grid, a.dt, a.tmax, a.workers, half=a.half)
    el = time.time() - t0
    np.savez_compressed(out, q=q, t_freeze=tf, absorbed=ab, n=a.n, q_center=a.q, seed=a.seed,
                        grid=a.grid, half=a.half, dt=a.dt, tmax=a.tmax, P=slice_directions(a.n, a.seed), wall=el)
    vals, cnt = np.unique(q, return_counts=True)
    print(f"wall {el:.1f}s  grid {a.grid}  never-absorbed {int((~ab).sum())}")
    print("t_freeze pct 50/90/99/99.9/max:", np.percentile(tf[ab], [50, 90, 99, 99.9, 100]))
    print("area fractions:", {int(v): round(c / q.size, 4) for v, c in zip(vals, cnt)})
    print("wrote", out)
