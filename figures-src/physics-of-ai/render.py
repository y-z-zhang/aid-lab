"""Render the Physics of AI figure: two nearly identical releases of a magnetic pendulum.

What it draws (800 x 800 px, dark page #070A0D, view window [-1.15, 1.15]^2):
  - contour lines of the potential V(x, y) = w0^2 (x^2 + y^2)/2 - sum_i 1/D_i at
    levels linspace(-4.7, -0.9, 14) (only the 11 levels from -4.7 to -1.78 fall inside the
    window; the largest V in view is -1.52), on a 900 x 900 grid, colour #343C42, 1.2 px;
  - two trajectories of the magnetic pendulum of Zhang et al., Chaos 35, 073102 (2025),
    Eqs. (5)-(6) (w0 = 0.5, a = 0.2, h = 0.2; model in pendulum.py), released from rest
    at points 0.001875 apart (one cell of the 1600 x 1600 basin map). Amber (#FFB67A, 3 px)
    from (x0, y0), grey (#8A938F, 2.4 px) from (x1, y1). They travel together, separate
    by more than 0.08 at t = 3.46, and are captured by different magnets (labels 0 and 1);
  - the release point as an amber dot, the three magnets as hollow circles.

Integration: pendulum.trajectory, fixed-step RK4, dt = 0.0025, energy checked every step,
stopped 3 time units after the energy falls below the saddle level E_C - 1e-3 (the same
trapping rule as the validated basin map; see compute_basins.py). Each path is drawn only
up to its last entry into radius 0.30 of its final magnet; after that it only rings down.

Provenance and validation: the pair is candidate 7 of the search in find_pairs.py, which
compares neighbouring cells of the validated basin map (data/basins_N1600.npz). Its two
cells, (row, col) = (560, 1256) and (560, 1257), have basin-map labels 0 and 1, and
trajectories integrated here end over magnets 0 and 1 (checked again by find_pairs.py).
This script needs neither the basin map nor any other data: everything is read from
params.json and recomputed. It asserts that both paths are trapped and end over the
labels recorded there.

Run (from anywhere):
    python3 -I figures-src/physics-of-ai/render.py
Runtime about 1 s on an Apple M4 Max. Writes out/physics-of-ai.png (RGBA, 800 x 800),
pixel-identical to the PNG behind assets/figures/physics-of-ai.webp. To update the site:
    python3 -I figures-src/export_webp.py physics-of-ai
"""
import json
import os
import sys
import time

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
from PIL import Image  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pendulum as P  # noqa: E402

THEME = 'physics-of-ai'


def clip_at_capture(p, label, cut):
    """Stop the path at its last entry into radius `cut` of the magnet it is finally trapped
    over (after which it only rings down), so the drawing ends at the magnet, not in a tangle."""
    d = np.hypot(p[:, 0] - P.MX[label], p[:, 1] - P.MY[label])
    far = np.where(d > cut)[0]
    last_far = far[-1] if far.size else 0           # after this it never leaves the disk again
    return p[: last_far + 2]


def main():
    t0 = time.time()
    with open(os.path.join(HERE, 'params.json')) as f:
        prm = json.load(f)
    pair, itg, st = prm['pair'], prm['integration'], prm['style']
    BG, OUT, W = st['background'], st['size_px'], st['window_half_width']
    PT = 72 / st['dpi']                              # points per pixel

    kw = dict(dt=itg['dt'], T=itg['T_max'], t_min=itg['t_min'], settle=itg['settle'])
    pa, la, ta = P.trajectory(pair['x0'], pair['y0'], **kw)
    pb, lb, tb = P.trajectory(pair['x1'], pair['y1'], **kw)
    assert ta is not None and tb is not None, 'a path was not trapped by T_max'
    assert [la, lb] == pair['labels'], ([la, lb], pair['labels'])
    print(f'amber: {len(pa)} points, trapped at t = {ta:.4f}, magnet {la}')
    print(f'grey:  {len(pb)} points, trapped at t = {tb:.4f}, magnet {lb}')
    print('path lengths match params.json:', [len(pa), len(pb)] == pair['path_points'])
    pa, pb = clip_at_capture(pa, la, st['capture_cut']), clip_at_capture(pb, lb, st['capture_cut'])

    g = np.linspace(-W, W, st['contour_grid'])
    X, Y = np.meshgrid(g, g)
    V = P.potential(X, Y)
    lv = st['contour_levels']
    levels = np.linspace(lv['start'], lv['stop'], lv['num'])

    fig = plt.figure(figsize=(OUT / st['dpi'], OUT / st['dpi']), dpi=st['dpi'], facecolor=BG)
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_axis_off(); ax.set_facecolor(BG)
    ax.set_xlim(-W, W); ax.set_ylim(-W, W); ax.set_aspect('equal')
    ax.contour(X, Y, V, levels=levels, colors=[st['contour_color']], linewidths=st['contour_lw_px'] * PT,
               linestyles='solid', antialiased=True, zorder=1)
    ax.plot(pb[:, 0], pb[:, 1], color=st['grey'], lw=st['grey_lw_px'] * PT, solid_capstyle='round',
            solid_joinstyle='round', zorder=2)
    ax.plot(pa[:, 0], pa[:, 1], color=st['amber'], lw=st['amber_lw_px'] * PT, solid_capstyle='round',
            solid_joinstyle='round', zorder=3)
    ax.scatter([pair['x0']], [pair['y0']], s=(st['start_dot_px'] * PT) ** 2, c=st['amber'], linewidths=0, zorder=5)
    ax.scatter(P.MX, P.MY, s=(st['magnet_px'] * PT) ** 2, facecolors=BG, edgecolors=st['magnet_edge'],
               linewidths=st['magnet_edge_lw_px'] * PT, zorder=4)

    os.makedirs(os.path.join(HERE, 'out'), exist_ok=True)
    out = os.path.join(HERE, 'out', f'{THEME}.png')
    fig.savefig(out, dpi=st['dpi'], facecolor=BG)
    plt.close(fig)
    im = Image.open(out)
    assert im.size == (OUT, OUT), im.size
    print(f'wrote {os.path.relpath(out)} {im.size} {im.mode} in {time.time() - t0:.1f} s')


if __name__ == '__main__':
    main()
