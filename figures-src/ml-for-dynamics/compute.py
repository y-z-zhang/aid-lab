"""Compute step for the "ML for dynamics" site figure: Lorenz-63 forecast by context parroting.

Follows Algorithm 1 (context parroting) of Zhang & Gilpin, ICLR 2026, with the sampling and the
sMAPE valid-prediction-time metric of that paper. Computes, archives and validates everything
render.py draws; render.py never integrates anything itself.

System      dx/dt = sigma (y - x), dy/dt = x (rho - z) - y, dz/dt = x y - beta z,
            sigma = 10, rho = 28, beta = 8/3.
Steps
  1. Largest Lyapunov exponent lam: batched Benettin (tangent dynamics, fixed-step RK4), 256 initial
     conditions uniform in [-15, 15]^2 x [10, 40] (seed 1), transient 50, average over 300 time
     units, renormalisation every 0.1; run at dt = 2e-3 and dt = 1e-3 (the 1e-3 value is used).
  2. Sampling as in the paper: 30 samples per Lyapunov time, Delta = 1 / (30 lam) = 0.036816.
     One long trajectory, fixed-step RK4 with NSUB = 40 substeps per sample (dt = Delta / 40 =
     9.20e-4), initial condition (1, 1, 20) + U(-1, 1)^3 (seed 7), transient of 100 time units
     discarded, then NSAMP = 40000 samples (about 1470 time units, 1330 Lyapunov times). Every
     coordinate is z-scored over the whole trajectory (as in the paper). Every 4th substep is
     kept as a dense copy (10 points per sample) so the render can draw smooth curves.
  3. Context parroting (Algorithm 1) with the 3-D state as the token: context L = 3000 samples
     (100 Lyapunov times); the last D = 10 samples are the query; every earlier length-D motif
     ending at s <= L - D is compared by Euclidean distance; the samples after the best motif
     are copied (periodically) for H = 300 samples (10 Lyapunov times).
  4. Valid prediction time (VPT): number of leading forecast samples before the prefix sMAPE
     (window [1, t], averaged over x, y, z) first reaches eps = 30, in Lyapunov times (the index
     convention of the authors' benchmark vpt_smape). Statistics over 1000 random context
     windows (start indices from seed 2026), for D = 10 and, as a robustness check, D = 5.
     Deviation from the paper's benchmark protocol: 3-D state tokens and a coordinate-averaged
     sMAPE instead of univariate parroting per coordinate (univariate VPTs of the shown instance
     are also recorded in summary.json).
  5. The shown instance is the first of the 1000 trials whose VPT is closest to the median
     (trial 26, start index 22173). Only its window (L + H samples, plus the dense copy) is
     archived, together with the forecast and all VPT arrays.
Validation (values in data/summary.json from the archived run)
  * Lyapunov exponent 0.9049 +- 0.0005 (dt 2e-3) and 0.9054 +- 0.0006 (dt 1e-3); literature 0.9056.
  * Fixed point (c, c, rho - 1) residual 1.4e-14 (right-hand-side sanity anchor).
  * Per-sample defect of the stored orbit re-integrated at dt/2, 3000 random samples: 1.3e-8.
  * Truth continuation of the instance re-integrated at dt/2 over 10 Lyapunov times: max
    deviation 5.4e-5 (raw units).
  * Independent trajectory at dt/2, same contexts: VPT median 1.50 vs 1.42 Lyapunov times (IQR
    0.37-2.78 vs 0.40-2.83), means 1.86 vs 1.86. KS and Mann-Whitney p-values (0.69, 0.88) are
    recorded but only indicative: the windows overlap and share the initial condition.
  * Shown instance: VPT 1.43 Lyapunov times (median 1.42), copy period 1846 > H, motif distance
    0.123. One-off external checks of the archived npz (not run by compute.py, not in
    summary.json): an independent brute-force Algorithm 1 (1-based indices as in the paper) reproduced
    s_opt, the period and the forecast exactly; an independent dt/2 and dt/4 check of the
    archived window gave per-sample defects of 1.3e-8 and 1.4e-8.
Run         python3 -I compute.py            (from any directory; paths are relative to this file)
Runtime     35 s on an Apple M4 Max (python 3.11.8, numpy 1.26.4, scipy 1.12.0); single core.
            Deterministic: a re-run into a fresh folder reproduced data/lorenz_parroting.npz
            byte for byte and data/summary.json except its wall_s field.
Writes      data/lorenz_parroting.npz  (about 855 KB; read by render.py)
            data/summary.json           (parameters, seeds and the validation numbers above)
"""
import json
import os
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
os.makedirs(DATA, exist_ok=True)

SIGMA, RHO, BETA = 10.0, 28.0, 8.0 / 3.0
SEED_LYAP = 1
SEED_TRAJ = 7
SEED_CTX = 2026
NSUB = 40           # RK4 substeps per sample (dt = Delta / 40 ~ 9.2e-4)
DENSE_EVERY = 4     # keep every 4th substep for drawing (10 points per sample)
L = 3000            # context length (samples) = 100 Lyapunov times
D = 10              # embedding dimension / query length
H = 300             # forecast horizon (samples) = 10 Lyapunov times
NTRIAL = 1000       # random contexts for VPT statistics
NSAMP = 40000       # samples in the long trajectory
EPS = 30.0


def rhs(u):
    x, y, z = u[..., 0], u[..., 1], u[..., 2]
    return np.stack([SIGMA * (y - x), x * (RHO - z) - y, x * y - BETA * z], axis=-1)


def rk4(u, dt):
    k1 = rhs(u)
    k2 = rhs(u + 0.5 * dt * k1)
    k3 = rhs(u + 0.5 * dt * k2)
    k4 = rhs(u + dt * k3)
    return u + dt / 6.0 * (k1 + 2 * k2 + 2 * k3 + k4)


def rhs_tan(u, v):
    x, y, z = u[..., 0], u[..., 1], u[..., 2]
    a, b, c = v[..., 0], v[..., 1], v[..., 2]
    du = np.stack([SIGMA * (y - x), x * (RHO - z) - y, x * y - BETA * z], axis=-1)
    dv = np.stack([SIGMA * (b - a), (RHO - z) * a - b - x * c, y * a + x * b - BETA * c], axis=-1)
    return du, dv


def rk4_tan(u, v, dt):
    k1u, k1v = rhs_tan(u, v)
    k2u, k2v = rhs_tan(u + 0.5 * dt * k1u, v + 0.5 * dt * k1v)
    k3u, k3v = rhs_tan(u + 0.5 * dt * k2u, v + 0.5 * dt * k2v)
    k4u, k4v = rhs_tan(u + dt * k3u, v + dt * k3v)
    return (u + dt / 6 * (k1u + 2 * k2u + 2 * k3u + k4u),
            v + dt / 6 * (k1v + 2 * k2v + 2 * k3v + k4v))


def lyapunov(dt, n_ic=256, t_transient=50.0, t_avg=300.0, t_renorm=0.1, seed=SEED_LYAP):
    rng = np.random.default_rng(seed)
    u = rng.uniform(-15, 15, size=(n_ic, 3)) + np.array([0, 0, 25.0])
    for _ in range(int(round(t_transient / dt))):
        u = rk4(u, dt)
    v = rng.standard_normal((n_ic, 3))
    v /= np.linalg.norm(v, axis=1, keepdims=True)
    k = int(round(t_renorm / dt))
    nren = int(round(t_avg / t_renorm))
    acc = np.zeros(n_ic)
    for _ in range(nren):
        for _ in range(k):
            u, v = rk4_tan(u, v, dt)
        nv = np.linalg.norm(v, axis=1)
        acc += np.log(nv)
        v /= nv[:, None]
    lam_i = acc / (nren * k * dt)
    return lam_i.mean(), lam_i.std(ddof=1) / np.sqrt(n_ic)


def _rk4_scalar(x, y, z, dt):
    """RK4 step on Python floats (fast for one trajectory); same scheme as rk4()."""
    s, r, b = SIGMA, RHO, BETA
    k1x = s * (y - x); k1y = x * (r - z) - y; k1z = x * y - b * z
    h = 0.5 * dt
    x2 = x + h * k1x; y2 = y + h * k1y; z2 = z + h * k1z
    k2x = s * (y2 - x2); k2y = x2 * (r - z2) - y2; k2z = x2 * y2 - b * z2
    x3 = x + h * k2x; y3 = y + h * k2y; z3 = z + h * k2z
    k3x = s * (y3 - x3); k3y = x3 * (r - z3) - y3; k3z = x3 * y3 - b * z3
    x4 = x + dt * k3x; y4 = y + dt * k3y; z4 = z + dt * k3z
    k4x = s * (y4 - x4); k4y = x4 * (r - z4) - y4; k4z = x4 * y4 - b * z4
    c = dt / 6.0
    return (x + c * (k1x + 2 * k2x + 2 * k3x + k4x),
            y + c * (k1y + 2 * k2y + 2 * k3y + k4y),
            z + c * (k1z + 2 * k2z + 2 * k3z + k4z))


def long_trajectory(delta, nsub, nsamp, seed, t_transient=100.0, dense_every=None):
    """Single trajectory sampled every delta; optional dense output for drawing."""
    rng = np.random.default_rng(seed)
    x, y, z = (np.array([1.0, 1.0, 20.0]) + rng.uniform(-1, 1, 3)).tolist()
    dt = delta / nsub
    for _ in range(int(round(t_transient / dt))):
        x, y, z = _rk4_scalar(x, y, z, dt)
    samples = [(x, y, z)]
    dense = [(x, y, z)] if dense_every else None
    for i in range(1, nsamp):
        for j in range(nsub):
            x, y, z = _rk4_scalar(x, y, z, dt)
            if dense is not None and (j + 1) % dense_every == 0:
                dense.append((x, y, z))
        samples.append((x, y, z))
    return np.array(samples), (np.array(dense) if dense is not None else None)


def parrot(ctx, d, h):
    """Algorithm 1. ctx: (L, m). Returns forecast (h, m), s_opt (0-based end index), min distance."""
    n = len(ctx)
    query = ctx[n - d:]                                   # x_{L-D+1:L}
    ends = np.arange(d - 1, n - d)                        # motifs x_{s-D+1:s}, s <= L - D
    win = np.lib.stride_tricks.sliding_window_view(ctx, (d, ctx.shape[1]))[:, 0]  # (n-d+1, d, m)
    cand = win[ends - (d - 1)]
    dist = np.sqrt(((cand - query[None]) ** 2).sum(axis=(1, 2)))
    k = int(np.argmin(dist))
    e = int(ends[k])
    period = n - 1 - e                                    # L - s_opt
    idx = e + 1 + (np.arange(h) % period)
    return ctx[idx], e, float(dist[k]), period


def smape_cum(truth, pred):
    """sMAPE over window [1, t] for every t, averaged over coordinates. (h,)"""
    pt = 200.0 * np.abs(truth - pred) / (np.abs(truth) + np.abs(pred))
    return np.cumsum(pt, axis=0).mean(axis=1) / np.arange(1, len(pt) + 1)


def vpt_steps(truth, pred, eps=EPS):
    s = smape_cum(truth, pred)
    bad = np.nonzero(s >= eps)[0]
    return int(bad[0]) if len(bad) else len(s)


def trials(z, seed, d=D):
    rng = np.random.default_rng(seed)
    starts = rng.integers(0, len(z) - L - H, size=NTRIAL)
    out = []
    for i0 in starts:
        ctx = z[i0:i0 + L]
        tru = z[i0 + L:i0 + L + H]
        pred, e, dmin, per = parrot(ctx, d, H)
        out.append(vpt_steps(tru, pred))
    return starts, np.array(out)


def main():
    t0 = time.time()
    summary = {}

    # 1. Lyapunov exponent, dt check
    lam1, se1 = lyapunov(2e-3)
    lam2, se2 = lyapunov(1e-3)
    summary["lyapunov"] = {"dt_2e-3": [lam1, se1], "dt_1e-3": [lam2, se2],
                           "n_ic": 256, "t_avg": 300.0, "literature": 0.9056}
    lam = lam2
    tau = 1.0 / lam
    delta = tau / 30.0
    print(f"lambda = {lam1:.4f}+-{se1:.4f} (dt 2e-3), {lam2:.4f}+-{se2:.4f} (dt 1e-3); "
          f"Delta = {delta:.5f}  [{time.time()-t0:.0f}s]")

    # 2. Long trajectory at dt and (independent run) at dt/2
    raw, dense = long_trajectory(delta, NSUB, NSAMP, SEED_TRAJ, dense_every=DENSE_EVERY)
    mu, sd = raw.mean(axis=0), raw.std(axis=0)
    z = (raw - mu) / sd
    print(f"trajectory done [{time.time()-t0:.0f}s]  mean {mu.round(3)}, std {sd.round(3)}")

    # fixed-point anchor
    c = np.sqrt(BETA * (RHO - 1))
    fp_res = float(np.abs(rhs(np.array([c, c, RHO - 1]))).max())

    # per-sample defect at dt/2 on 3000 random samples
    rng = np.random.default_rng(11)
    pick = rng.integers(0, NSAMP - 1, 3000)
    u = raw[pick].copy()
    for _ in range(2 * NSUB):
        u = rk4(u, delta / (2 * NSUB))
    defect = float(np.abs(u - raw[pick + 1]).max())
    print(f"per-sample defect at dt/2: {defect:.2e}; fixed-point residual {fp_res:.1e}")

    # 3-4. VPT statistics over random contexts (D = 10 main, D = 5 robustness)
    starts, vpts = trials(z, SEED_CTX)
    _, vpts5 = trials(z, SEED_CTX, d=5)
    v_tau = vpts / 30.0
    print(f"VPT (D=10) median {np.median(v_tau):.2f} tau, IQR {np.percentile(v_tau,25):.2f}-"
          f"{np.percentile(v_tau,75):.2f}; D=5 median {np.median(vpts5)/30:.2f}  [{time.time()-t0:.0f}s]")

    # independent run at dt/2 for distributional agreement
    raw_h, _ = long_trajectory(delta, 2 * NSUB, NSAMP, SEED_TRAJ)
    z_h = (raw_h - raw_h.mean(0)) / raw_h.std(0)
    _, vpts_h = trials(z_h, SEED_CTX)
    from scipy.stats import ks_2samp, mannwhitneyu
    ks_p = float(ks_2samp(vpts, vpts_h).pvalue)
    mw_p = float(mannwhitneyu(vpts, vpts_h).pvalue)
    print(f"dt/2 run: VPT median {np.median(vpts_h)/30:.2f} tau; KS p={ks_p:.3f}, MW p={mw_p:.3f}"
          f"  [{time.time()-t0:.0f}s]")

    # chosen instance: the trial whose VPT is closest to the median (first such)
    med = np.median(vpts)
    k = int(np.argmin(np.abs(vpts - med)))
    i0 = int(starts[k])
    ctx = z[i0:i0 + L]
    tru = z[i0 + L:i0 + L + H]
    pred, e_opt, dmin, period = parrot(ctx, D, H)
    vpt_k = vpt_steps(tru, pred)
    vpt_x = vpt_steps(tru[:, :1], pred[:, :1])
    # univariate per-coordinate parroting (paper's benchmark protocol) for the same context
    uni = {}
    for j, name in enumerate("xyz"):
        pj, ej, _, _ = parrot(ctx[:, j:j + 1], D, H)
        uni[name] = vpt_steps(tru[:, j:j + 1], pj) / 30.0
    err = np.linalg.norm(pred - tru, axis=1)
    nrmse = np.sqrt(((pred - tru) ** 2).mean(axis=1))
    bad = np.nonzero(nrmse >= 0.5)[0]
    t_nrmse = (int(bad[0]) if len(bad) else H) / 30.0
    # truth continuation re-integrated at dt/2 from the context's last state
    u = raw[i0 + L - 1].copy()
    cont = []
    for _ in range(H):
        for _ in range(2 * NSUB):
            u = rk4(u, delta / (2 * NSUB))
        cont.append(u.copy())
    cont = np.array(cont)
    cont_dev = float(np.abs(cont - raw[i0 + L:i0 + L + H]).max())
    print(f"instance trial {k}: start {i0}, s_opt(end) {e_opt}, period {period}, "
          f"dmin {dmin:.4f}, VPT {vpt_k/30:.2f} tau (x only {vpt_x/30:.2f}); "
          f"univariate {uni}; truth cont. dev at dt/2 {cont_dev:.2e}")

    per = NSUB // DENSE_EVERY
    a, b = i0 * per, (i0 + L + H - 1) * per + 1
    dense_win = (dense[a:b] - mu) / sd

    np.savez_compressed(
        os.path.join(DATA, "lorenz_parroting.npz"),
        z_window=z[i0:i0 + L + H], dense_window=dense_win, dense_per_sample=per,
        forecast=pred, s_opt_end=e_opt, period=period, L=L, D=D, H=H,
        mu=mu, sd=sd, lam=lam, delta=delta, vpts=vpts, vpts_dt2=vpts_h, vpts_D5=vpts5,
        smape_cum=smape_cum(tru, pred), err=err, vpt_instance=vpt_k, i0=i0)

    summary.update({
        "delta": delta, "nsub": NSUB, "dt": delta / NSUB, "nsamp": NSAMP, "L": L, "D": D, "H": H,
        "seeds": {"lyap": SEED_LYAP, "traj": SEED_TRAJ, "contexts": SEED_CTX},
        "mean": mu.tolist(), "std": sd.tolist(),
        "fixed_point_residual": fp_res, "per_sample_defect_dt2": defect,
        "vpt_tau": {"median": float(np.median(v_tau)), "q25": float(np.percentile(v_tau, 25)),
                    "q75": float(np.percentile(v_tau, 75)), "n": NTRIAL,
                    "median_dt2": float(np.median(vpts_h) / 30),
                    "q25_dt2": float(np.percentile(vpts_h, 25) / 30),
                    "q75_dt2": float(np.percentile(vpts_h, 75) / 30),
                    "median_D5": float(np.median(vpts5) / 30),
                    "mean": float(v_tau.mean()), "mean_dt2": float(np.mean(vpts_h) / 30),
                    "ks_p_dt_vs_dt2": ks_p, "mannwhitney_p_dt_vs_dt2": mw_p},
        "instance": {"trial": k, "start": i0, "s_opt_end_0based": e_opt, "period": period,
                     "dmin": dmin, "vpt_tau": vpt_k / 30, "vpt_tau_x_only": vpt_x / 30,
                     "univariate_vpt_tau": uni, "truth_continuation_dev_dt2": cont_dev,
                     "t_nrmse_0p5_tau": t_nrmse},
        "wall_s": time.time() - t0,
    })
    with open(os.path.join(DATA, "summary.json"), "w") as f:
        json.dump(summary, f, indent=2)
    print(f"done [{time.time()-t0:.0f}s]")


if __name__ == "__main__":
    main()
