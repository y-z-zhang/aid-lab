"""Basin map of the magnetic pendulum and its numerical validation (optional step).

render.py does NOT need this. The basin map is only used by find_pairs.py, to pick two
neighbouring release points that end over different magnets, and to check that the pair
in params.json has basin-map labels 0 and 1.

System: magnetic pendulum of Zhang et al., Chaos 35, 073102 (2025), Eqs. (5)-(6), and
Zhang & Cornelius, PRR 5, 033213 (2023), Eqs. (1)-(3); w0 = 0.5, a = 0.2, h = 0.2
(pendulum.py). Released from rest on an N x N grid over [-1.5, 1.5]^2, N = 1600.
Grid: pixel centres x_j = -1.5 + (j+0.5)*3/N (left->right), y_i = 1.5 - (i+0.5)*3/N
(top->bottom, so row 0 is y = +1.5 and the array is in the usual image orientation).
Integrator: fixed-step RK4 (pendulum.run), dt = 0.0025, horizon T = 100 (the papers' T),
energy-trapping classification checked every 20 steps (label = nearest magnet once
E < E_C - 1e-3; see pendulum.py). Parallel over 96 fixed chunks; results do not depend on
the number of worker processes.

Validation (subsample seed 20261030), as recorded in data/validation.json:
  - all 2,560,000 points trapped by T = 100; energy decreased between every pair of checks;
    basin fractions 0.3347 / 0.3327 / 0.3327; latest trap time 12.9;
  - 2% random subsample (51,200 points) re-run at dt/2: 0 label changes; at 2 dt: 2 changes;
    with T = 200: 0 changes;
  - 1000 of those points against scipy DOP853 (rtol = atol = 1e-10, the papers' tolerance)
    with the same trapping rule as a terminal event: 0 mismatches;
  - 5000 points with the papers' rule (nearest magnet at T = 100, no freezing): 0 mismatches,
    max speed at T = 100 is 3e-4;
  - y -> -y mirror symmetry (magnets 1 <-> 2): 0 violations.

Run (from anywhere):
    python3 -I figures-src/physics-of-ai/compute_basins.py
Runtime about 2 min on an Apple M4 Max with 12 worker processes (115 s wall clock: main
map 67 s, validation 48 s). Re-running it reproduced label, ttrap and fallback bit for bit
(identical .npz file) and every validation number above.
Writes data/basins_N1600.npz (2.6 MB, git-ignored: label int8 with -1 = untrapped,
ttrap float32, fallback int8, N, dt, T, domain) and data/validation.json.
"""
import json, os, sys, time
import numpy as np
from multiprocessing import Pool

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pendulum as P

N = 1600
DT = 0.0025
T = 100.0
SEED = 20261030
OUT = os.path.join(HERE, "data")


def grid(N):
    c = -1.5 + (np.arange(N) + 0.5) * 3.0 / N
    X, Y = np.meshgrid(c, c[::-1])
    return X, Y


def _work(args):
    x0, y0, dt, T = args
    return P.run(x0, y0, dt, T)


def prun(x0, y0, dt, T, nproc=min(12, os.cpu_count() or 1), nchunks=96):
    xs, ys = np.array_split(x0, nchunks), np.array_split(y0, nchunks)
    with Pool(nproc) as pool:
        res = pool.map(_work, [(a, b, dt, T) for a, b in zip(xs, ys)])
    lab = np.concatenate([r[0] for r in res])
    tt = np.concatenate([r[1] for r in res])
    fb = np.concatenate([r[2] for r in res])
    mdE = max(r[3] for r in res)
    return lab, tt, fb, mdE


def ref_dop853(x0, y0):
    from scipy.integrate import solve_ivp
    def f(t, s):
        ax, ay = P.acc(s[0], s[1], s[2], s[3])
        return [s[2], s[3], ax, ay]
    def ev(t, s):
        return P.energy(s[0], s[1], s[2], s[3]) - (P.E_C - P.MARGIN)
    ev.terminal = True
    ev.direction = -1
    out = np.full(x0.size, -1, np.int8)
    for k in range(x0.size):
        if P.energy(x0[k], y0[k], 0.0, 0.0) < P.E_C - P.MARGIN:   # released already trapped
            out[k] = P.nearest(np.array([x0[k]]), np.array([y0[k]]))[0]
            continue
        sol = solve_ivp(f, (0, T), [x0[k], y0[k], 0.0, 0.0], method="DOP853",
                        rtol=1e-10, atol=1e-10, events=ev)
        if sol.t_events[0].size:
            s = sol.y_events[0][0]
            out[k] = P.nearest(np.array([s[0]]), np.array([s[1]]))[0]
    return out


def nearest_at_T(x0, y0, dt, T):
    x, y = x0.copy(), y0.copy()
    vx, vy = np.zeros_like(x), np.zeros_like(x)
    for _ in range(int(round(T / dt))):
        x, y, vx, vy = P.rk4_step(x, y, vx, vy, dt)
    return P.nearest(x, y), np.hypot(vx, vy)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    X, Y = grid(N)
    t0 = time.time()
    lab, tt, fb, mdE = prun(X.ravel(), Y.ravel(), DT, T)
    t_main = time.time() - t0
    lab = lab.reshape(N, N); tt = tt.reshape(N, N); fb = fb.reshape(N, N)
    np.savez_compressed(os.path.join(OUT, f"basins_N{N}.npz"), label=lab, ttrap=tt.astype(np.float32),
                        fallback=fb, N=N, dt=DT, T=T, domain=np.array([-1.5, 1.5]))
    print(f"main run {t_main:.1f}s untrapped={np.sum(lab < 0)} maxdE={mdE:.2e} counts={np.bincount(fb.ravel())}")

    rng = np.random.default_rng(SEED)
    flat = rng.choice(N * N, size=int(0.02 * N * N), replace=False)
    xs, ys, l0 = X.ravel()[flat], Y.ravel()[flat], lab.ravel()[flat]
    l_half, _, _, mdE_half = prun(xs, ys, DT / 2, T)
    l_dbl, _, _, mdE_dbl = prun(xs, ys, DT * 2, T)
    l_long, _, _, _ = prun(xs, ys, DT, 2 * T)
    sub = rng.choice(flat.size, size=1000, replace=False)
    t1 = time.time()
    l_ref = ref_dop853(xs[sub], ys[sub])
    t_ref = time.time() - t1
    sub2 = rng.choice(flat.size, size=5000, replace=False)
    l_nT, vT = nearest_at_T(xs[sub2], ys[sub2], DT, T)

    v = dict(
        N=N, dt=DT, T=T, seed=SEED, n_points=int(N * N), main_runtime_s=round(t_main, 1),
        untrapped_at_T=int(np.sum(lab < 0)),
        max_energy_increase_between_checks=mdE,
        basin_fractions=[float(np.mean(fb == k)) for k in range(3)],
        ttrap_percentiles_50_90_99_max=[float(q) for q in np.nanpercentile(tt, [50, 90, 99, 100])],
        subsample_size=int(flat.size),
        mismatch_dt_half=float(np.mean(l_half != l0)), n_mismatch_dt_half=int(np.sum(l_half != l0)),
        mismatch_dt_double=float(np.mean(l_dbl != l0)), n_mismatch_dt_double=int(np.sum(l_dbl != l0)),
        max_energy_increase_dt_half=mdE_half, max_energy_increase_dt_double=mdE_dbl,
        mismatch_T_200=float(np.mean(l_long != l0)),
        ref_dop853_n=1000, ref_dop853_mismatch=float(np.mean(l_ref != l0[sub])),
        ref_dop853_n_mismatch=int(np.sum(l_ref != l0[sub])), ref_dop853_untrapped=int(np.sum(l_ref < 0)),
        ref_runtime_s=round(t_ref, 1),
        nearest_at_T100_n=5000, nearest_at_T100_mismatch=float(np.mean(l_nT != l0[sub2])),
        max_speed_at_T100=float(vT.max()),
        # y -> -y mirror maps magnet 1 <-> 2 (indices 1, 2) and fixes magnet 0
        mirror_violations=int(np.sum(np.where(lab[::-1] == 0, 0, 3 - lab[::-1]) != lab)),
    )
    with open(os.path.join(OUT, "validation.json"), "w") as f:
        json.dump(v, f, indent=2)
    print(json.dumps(v, indent=2))
