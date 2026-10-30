"""Render step for the "ML for dynamics" site figure, drawn from archived data only (no integration).

Figure (800 x 800 px PNG, background #070A0D, no text, no axes):
  top    Lorenz-63 context (L = 3000 samples = 100 Lyapunov times), x-z projection, as 0.9 px
         #5A6268 strands at alpha 0.40 in 1-tau pieces; true continuation (2.4 px, #8A938F -> #5A6268)
         and the context-parroting forecast (3.0 px, #FFB67A -> #B8794D) for 4 Lyapunov times;
         9 px amber dot at the last context sample.
  bottom x(t): last 2.5 Lyapunov times of context (2.4 px #5A6268), #343C42 hairline at the forecast
         start, then truth (2.4 px) and forecast (3.0 px) for 4 Lyapunov times.
The forecast is Algorithm 1 (context parroting) of Zhang & Gilpin, ICLR 2026; see compute.py for the
system, integrator, seeds (1 / 7 / 2026) and validation.

Run      python3 -I render.py        (from any directory; paths are relative to this file)
Runtime  0.3 s on an Apple M4 Max (matplotlib 3.8.0 Agg, numpy 1.26.4, Pillow 10.2.0)
Reads    data/lorenz_parroting.npz   (written by compute.py; archived, so no recomputation needed)
Writes   out/ml-for-dynamics.png     (opaque RGB, 800 x 800)
Site     python3 -I figures-src/export_webp.py ml-for-dynamics   (from the repo root)
         converts out/ml-for-dynamics.png to assets/figures/ml-for-dynamics.webp (quality 90, method 6)
Check    out/ml-for-dynamics.png is byte-identical (max abs pixel difference 0) to the PNG the
         site's WebP was converted from, and re-encoding it as export_webp.py does gives a file
         byte-identical to assets/figures/ml-for-dynamics.webp (with these library versions).

Design history: this is the "two-part" layout (phase plane above, x(t) strip below) chosen over a
plain attractor and a phase-plane-only forecast. An art-director pass then raised the truth line
2.2 -> 2.4 px (phase plane and strip) and the strip context tail 2.0 -> 2.4 px, to share a line
system with the networks-emergence contours.

Provenance notes (corrected after the numerics check):
  * VPT = number of leading samples before the prefix sMAPE (window [1, t], averaged over x, y, z)
    first reaches 30 (>= 30), the index convention of the authors' benchmark/metrics.py (vpt_smape).
    Deviation from the paper's protocol: 3-D state tokens and a coordinate-averaged sMAPE instead of
    univariate parroting per coordinate.
  * Shown instance (trial 26): 3-D VPT 1.43 tau, x-only VPT 2.83 tau. Forecast and truth go to
    opposite wings at 2.83 tau and stay there for the rest of the 4-tau window, except 3.49-3.54 tau.
    x zero crossings on the drawn dense curves, time from the last context sample: forecast 0.76,
    1.45, 2.83, 3.54 tau; truth 0.77, 1.47, 3.49 tau.
  * Representativeness: the instance is at the median of the 3-D VPT distribution (1.42 tau over 1000
    contexts), at the median of wing-agreement time (2.83 vs 2.87 tau; wing-agreement time = first 0-based
    sample k where sign(x) of forecast and truth differ for >= 3 consecutive samples, k/30) and at
    the 67th percentile of x-only VPT (median 1.97 tau), so the x(t) strip is mildly favourable but
    not cherry-picked. One-off check over the same 1000 contexts (seed 2026), not recorded in
    summary.json; to recompute (about 10 s), rerun compute.long_trajectory and compute.parrot over
    those starts.
  * Early forecast error: RMS normalised error about 0.1 (median over the first 2 tau), up to 0.6 in
    one spike near 1.2 tau; the dt/2 deviation of the truth (5.4e-5 raw units) is negligible.
  * dt vs dt/2 VPT distributions: medians 1.42 vs 1.50 tau, means 1.86 vs 1.86 tau. The KS (0.69)
    and Mann-Whitney (0.88) p-values are indicative only: the 1000 windows overlap heavily and both
    pipelines share the initial condition and start indices.
  * Copy period 1846 > H = 300, so the repeat convention (Algorithm 1 vs parrot.py) is irrelevant.
  * Pixel check: all chromatic pixels are amber or amber/neutral antialiasing blends; no foreign hues.
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.collections import LineCollection
from matplotlib.colors import to_rgba
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data", "lorenz_parroting.npz")
OUT_DIR = os.path.join(HERE, "out")
OUT_PNG = os.path.join(OUT_DIR, "ml-for-dynamics.png")

BG = "#070A0D"
AMBER = ["#FFB67A", "#E09A63", "#B8794D", "#84573A", "#4F3727", "#2A1F18"]
NEUTRAL = ["#EDEEEA", "#B8BCB6", "#8A938F", "#5A6268", "#343C42", "#1B232B"]
PX = 72.0 / 100.0   # linewidth in points for 1 px at dpi 100

# line system (px at 800 x 800)
LW_CTX = 0.9        # context strands in the phase plane
A_CTX = 0.40
LW_TRUTH = 2.4      # true continuation (phase plane and strip)
LW_TAIL = 2.4       # strip: context tail
LW_FC = 3.0         # parroting forecast
LW_HAIR = 2.0       # strip: forecast-origin hairline
DOT = 9             # amber dot at the last context sample

d = np.load(DATA)
mu, sd = d["mu"], d["sd"]
L, H, per = int(d["L"]), int(d["H"]), int(d["dense_per_sample"])
e_opt = int(d["s_opt_end"])
dense = d["dense_window"] * sd + mu            # raw units, 10 points per sample
ctx_dense = dense[: (L - 1) * per + 1]


def truth_dense(nshow):
    return dense[(L - 1) * per: (L - 1 + nshow) * per + 1]


def forecast_dense(nshow):
    # Algorithm 1 copies the context after the matched motif (ends at e_opt); period > H, so
    # the forecast is one contiguous context segment. Drawn from the motif end (the copy's "now").
    assert int(d["period"]) >= nshow
    return dense[e_opt * per: (e_opt + nshow) * per + 1]


def proj(p, plane):
    i, j = {"xz": (0, 2), "xy": (0, 1)}[plane]
    return np.column_stack([p[:, i], p[:, j]])


def phase_axes(fig, rect, plane, pts, pad=0.06):
    ax = fig.add_axes(rect)
    ax.set_facecolor(BG)
    ax.set_axis_off()
    xy = proj(pts, plane)
    lo, hi = xy.min(0), xy.max(0)
    c, half = (lo + hi) / 2, (hi - lo).max() / 2 * (1 + pad)
    # equal data aspect inside the axes rectangle
    fw, fh = rect[2] * 8, rect[3] * 8
    if fw / fh >= 1:
        ax.set_xlim(c[0] - half * fw / fh, c[0] + half * fw / fh)
        ax.set_ylim(c[1] - half, c[1] + half)
    else:
        ax.set_xlim(c[0] - half, c[0] + half)
        ax.set_ylim(c[1] - half * fh / fw, c[1] + half * fh / fw)
    return ax


def strands(ax, p, plane, color, lw_px, alpha, z, chunk):
    """Path split into pieces of `chunk` dense points, so translucent strands accumulate where
    the orbit revisits (a single matplotlib path never blends with itself)."""
    xy = proj(p, plane)
    pieces = [xy[i:i + chunk + 1] for i in range(0, len(xy) - 1, chunk)]
    lc = LineCollection(pieces, colors=[to_rgba(color, alpha)], linewidths=lw_px * PX,
                        zorder=z, capstyle="butt", joinstyle="round", antialiased=True)
    ax.add_collection(lc)


def hex2rgb(h):
    return np.array(to_rgba(h)[:3])


def ramp(stops, t):
    """Piecewise-linear interpolation between palette stops, t in [0, 1]."""
    cols = np.array([hex2rgb(c) for c in stops])
    x = np.linspace(0, 1, len(stops))
    return np.column_stack([np.interp(t, x, cols[:, k]) for k in range(3)])


def faded_line(ax, xy, stops, lw_px, z=2):
    """Opaque polyline whose colour runs through `stops` along its length (time)."""
    segs = np.stack([xy[:-1], xy[1:]], axis=1)
    t = np.linspace(0, 1, len(segs))
    lc = LineCollection(segs, colors=ramp(stops, t), linewidths=lw_px * PX, zorder=z,
                        capstyle="round", joinstyle="round", antialiased=True)
    ax.add_collection(lc)


CHUNK = 300   # dense points per context piece (= 30 samples = 1 Lyapunov time)
NSHOW = 120   # forecast / truth samples drawn (= 4 Lyapunov times)
NTAIL = 75    # context samples in the x(t) strip (= 2.5 Lyapunov times)

# colour runs along lead time: bright at the forecast origin, darker at 4 Lyapunov times
FC_STOPS = [AMBER[0], AMBER[0], AMBER[1], AMBER[2]]
TR_STOPS = [NEUTRAL[2], NEUTRAL[2], NEUTRAL[2], NEUTRAL[3]]


def main(plane="xz", nshow=NSHOW, ntail=NTAIL, split=0.27):
    fig = plt.figure(figsize=(8, 8), dpi=100, facecolor=BG)
    m = 0.045
    ax = phase_axes(fig, [m, split + 0.01, 1 - 2 * m, 1 - split - 0.01 - m], plane, ctx_dense,
                    pad=0.02)
    strands(ax, ctx_dense, plane, NEUTRAL[3], LW_CTX, A_CTX, z=1, chunk=CHUNK)
    faded_line(ax, proj(truth_dense(nshow), plane), TR_STOPS, LW_TRUTH, z=2)
    faded_line(ax, proj(forecast_dense(nshow), plane), FC_STOPS, LW_FC, z=3)
    p0 = proj(dense[(L - 1) * per][None], plane)[0]       # last context sample
    ax.plot(*p0, "o", ms=DOT * PX, color=AMBER[0], mew=0, zorder=4)

    # x(t) strip: last context samples, then truth and forecast; time in Lyapunov times
    bx = fig.add_axes([0.06, 0.045, 0.88, split - 0.075])
    bx.set_facecolor(BG)
    bx.set_axis_off()
    tail = dense[(L - 1 - ntail) * per: (L - 1) * per + 1]
    tt = (np.arange(len(tail)) - (len(tail) - 1)) / (per * 30.0)
    bx.plot(tt, tail[:, 0], color=NEUTRAL[3], lw=LW_TAIL * PX, solid_capstyle="round", zorder=1)
    tr = truth_dense(nshow)
    fc = forecast_dense(nshow)
    t1 = np.arange(len(tr)) / (per * 30.0)
    faded_line(bx, np.column_stack([t1, tr[:, 0]]), TR_STOPS, LW_TRUTH, z=2)
    faded_line(bx, np.column_stack([t1, fc[:, 0]]), FC_STOPS, LW_FC, z=3)
    bx.axvline(0, color=NEUTRAL[4], lw=LW_HAIR * PX, zorder=0)   # forecast origin
    bx.set_xlim(tt[0], t1[-1])
    lim = np.abs(dense[:, 0]).max() * 1.04
    bx.set_ylim(-lim, lim)

    os.makedirs(OUT_DIR, exist_ok=True)
    fig.savefig(OUT_PNG, dpi=100, facecolor=BG)
    plt.close(fig)
    Image.open(OUT_PNG).convert("RGB").save(OUT_PNG)   # opaque 800 x 800, no alpha channel
    print(OUT_PNG)


if __name__ == "__main__":
    main()
