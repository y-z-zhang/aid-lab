# Figure sources

The three research figures on the site (`assets/figures/*.webp`) were computed
for the site from the systems in our papers and drawn in the site palette
(page background `#070A0D`, fine neutral lines, one amber element). This folder
holds everything needed to regenerate or restyle them.

| theme | figure | follows |
|---|---|---|
| `ml-for-dynamics` | context-parroting forecast of the Lorenz system vs the truth | Zhang & Gilpin, ICLR 2026 (Algorithm 1) |
| `physics-of-ai` | two magnetic-pendulum releases 0.002 apart that settle over different magnets | Zhang et al., *Chaos* 35, 073102 (2025) |
| `networks-emergence` | slice of state space around a twisted state of a Kuramoto ring | Zhang & Strogatz, *PRL* 127, 194101 (2021), Fig. 4 |

## Quick start

From the repo root:

```
python3 -I figures-src/ml-for-dynamics/render.py      # uses the committed data, < 1 s
python3 -I figures-src/physics-of-ai/render.py        # integrates two paths, ~1 s
python3 -I figures-src/networks-emergence/render.py   # uses the committed data, < 1 s
python3 -I figures-src/export_webp.py                 # -> assets/figures/*.webp (WebP q90, method 6)
```

Each `render.py` writes `out/<theme>.png` (800×800, git-ignored); `export_webp.py`
converts those to the served WebP files. The optional compute scripts rebuild the
data from scratch; each script's docstring gives the system, parameters,
integrator, seeds, validation and runtime.

Environment used: Python 3.11.8, numpy 1.26.4, scipy 1.12.0, matplotlib 3.8.0,
Pillow 10.2.0. With these versions every `render.py` reproduces its published
image pixel for pixel and `export_webp.py` reproduces the served WebP byte for
byte (checked 2026-10-30). Other matplotlib versions may anti-alias slightly
differently.

---

## ml-for-dynamics: Lorenz forecast by context parroting

**What it shows.** The Lorenz-63 attractor (σ = 10, ρ = 28, β = 8/3) in the x–z
plane, drawn as faint strands of a 100-Lyapunov-time context. On top, in amber, a
context-parroting forecast for 4 Lyapunov times, with the true continuation in
grey; the strip below shows x(t) at the forecast origin. The forecast stays on
the same wing as the truth until 2.83 Lyapunov times.

**Setup.** 30 samples per Lyapunov time (λ = 0.9054 from batched Benettin;
literature 0.9056); fixed-step RK4 with dt = Δ/40; one trajectory of 40,000
samples (seed 7), z-scored; context L = 3000, query D = 10, horizon H = 300.
VPT (prefix-sMAPE crossing of 30, averaged over x, y, z) over 1000 random
contexts (seed 2026): median 1.42 Lyapunov times. The shown instance (trial 26)
has VPT 1.43, at the median. Deviation from the paper's benchmark: 3-D state
tokens rather than univariate parroting per coordinate.

**Files.** `compute.py` (integration, parroting, VPT statistics, validation →
`data/`, ~35 s), `render.py` (draws from `data/lorenz_parroting.npz`, 855 KB),
`data/summary.json` (parameters, seeds, validation numbers).

**Validation.** Fixed-point residual 1.4e-14; per-sample defect of the stored
orbit at dt/2 1.3e-8; independent dt/2 run gives VPT median 1.50 vs 1.42 and
mean 1.86 vs 1.86; an independent brute-force Algorithm 1 reproduced the stored
forecast exactly; a fresh `compute.py` run reproduces the `.npz` byte for byte.

## physics-of-ai: twin releases of a magnetic pendulum

**What it shows.** The magnetic pendulum of Zhang et al., *Chaos* 2025, Eqs.
(5)–(6) (also Zhang & Cornelius, *PRR* 2023), with ω0 = 0.5, a = 0.2, h = 0.2.
The bob is released from rest at two points 0.001875 apart (one cell of a
1600×1600 basin map). The paths travel together, are more than 0.08 apart by
t = 3.46, and settle over different magnets: amber over magnet 0 (right), grey
over magnet 1 (lower left). The background shows contour lines of the potential
(levels `linspace(-4.7, -0.9, 14)`; the 11 from −4.7 to −1.78 fall in view).
Each path is drawn up to its last entry into radius 0.30 of its final magnet.

**Files.**

| file | role |
|---|---|
| `pendulum.py` | model, fixed-step RK4, energy-trap classifier, `trajectory()`, critical points |
| `params.json` | the chosen pair (release points, labels, provenance), integration settings, style values |
| `render.py` | **the figure**: integrates the two paths and draws them; needs no data files |
| `compute_basins.py` | optional: validated basin map → `data/basins_N1600.npz` (2.6 MB, git-ignored) and `data/validation.json` |
| `find_pairs.py` | optional: searches the basin map for neighbouring cells with different labels, then re-checks the chosen pair |

To restyle, edit `style` in `params.json`. To use a different pair, run
`compute_basins.py` and `find_pairs.py` (about 2.5 min together), take an entry
of `data/candidates.json`, and set in `params.json`: `pair.x0, y0, x1, y1` from
it; `pair.labels` and `pair.provenance.basin_map_labels` to `[la, lb]`;
`pair.path_points` to `[len_a, len_b]`; `pair.provenance.grid_cells_row_col` to
`[[i, j], [i, j+1]]`; and `pair.provenance.t_split` and `found_by` (candidate
index). Then re-run `find_pairs.py` to check it.

**Numerics.** RK4 with dt = 0.0025. A point counts as trapped once its energy
falls below E_C − 1e-3 (E_C = −4.920805396, the index-1 saddle energy); after
that it cannot leave its magnet's well. Basin-map validation: all 2.56M points
trapped by T = 100; 0/51,200 label changes at dt/2 and 0 with T = 200; 0/1000
mismatches against scipy DOP853 at rtol = atol = 1e-10; 0 mirror-symmetry
violations. The chosen pair (candidate 7, cells (560, 1256) and (560, 1257)) has
basin-map labels 0 and 1, and its directly integrated paths end over magnets 0
and 1.

## networks-emergence: basins with tentacles

**What it shows.** A 2-D slice through the state space of a ring of n = 83
identical Kuramoto oscillators, dθᵢ/dt = sin(θᵢ₊₁ − θᵢ) + sin(θᵢ₋₁ − θᵢ):
θ = θ0 + a1·P1 + a2·P2, centred on the stable q = 15 twisted state, with each
point labelled by the winding number of the twisted state it ends in. The
central basin is filled `#2A1F18` and outlined in amber; grey outlines mark the
nested sets {dq ≤ k} for k = 3, 6, 9 (dq = 15 − q_final). View
a1, a2 ∈ [−0.72π, 0.72π].

**Provenance.** Follows Eq. 1 and the slice construction of Fig. 4 of Zhang &
Strogatz, *PRL* 2021. The Letter does not give n for Fig. 4; n = 83 is the n used
throughout. The binary slice directions P1, P2 (41 ones each) come from
`numpy.random.default_rng(7)`, a single realisation chosen for the picture.

**Files.** `kuramoto_ring.py` (model, integrator), `compute_slice.py` (map →
`data/slice_n83_q15_s7_g1600_h0.8_dt0.1.npz`, 0.55 MB, committed; ~18 s),
`render.py` (the figure), `validate.py` (optional checks; needs the dt/2 map
from `compute_slice.py --dt 0.05`, which is git-ignored). Re-running
`compute_slice.py` at its defaults overwrites the committed data file; only its
wall-clock field changes.

**Numerics.** RK4 with dt = 0.1, horizon 2000, on a 1600² grid over
[−0.8π, 0.8π]². A trajectory is labelled once max |θᵢ₊₁ − θᵢ| < π/2 − 0.05, a
forward-invariant set, so its winding number is frozen. dt = 0.1 vs 0.05: 95 of
2,560,000 labels differ, each by one winding; 3000 random points run to full
convergence all end in the predicted twisted state; on the full slice every
point within 10 windings of the centre lies inside |aᵢ| ≤ 0.634π, so the 0.8π
window loses nothing that is drawn.
