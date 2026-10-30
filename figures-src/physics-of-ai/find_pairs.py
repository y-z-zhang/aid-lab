"""Search the basin map for twin releases, and check the pair used by render.py (optional step).

Needs data/basins_N1600.npz, so run compute_basins.py first. render.py does not need this
script; it documents how the pair in params.json was chosen and re-checks it.

Search (seed 3): draw random cells (row i, col j) of the 1600 x 1600 basin map and keep
those whose right neighbour (i, j+1) has a different label and whose release radius
sqrt(x^2 + y^2) lies in (0.55, 1.0); stop after 4000 draws or 60 such cells. For each,
integrate both cell centres from rest with pendulum.trajectory (RK4, dt = 0.0025, settings
from params.json) and keep the pair only if the two trajectory labels differ AND each
equals its basin-map label (a check on the map's orientation and on the classification).
Then keep pairs whose paths stay within |x|, |y| < 1.164 (0.97 x an earlier 1.2-wide
framing; the final window is 1.15) and whose split time (first time the paths are more
than 0.08 apart) is between 2.5 and 7; sort by split time, longest first.
Writes the top 12 to data/candidates.json (git-ignored). With seed 3 all 60 sampled cells
give label-consistent pairs and 44 pass the filters.

The figure uses candidate 7 (chosen by eye from renders of the top 8): cells (560, 1256)
and (560, 1257), release points (0.8559375, 0.44906) and (0.8578125, 0.44906), split time
3.46, basin-map labels 0 and 1, trajectory labels 0 and 1. The check at the end confirms
that params.json holds exactly that candidate, that the basin map gives it labels 0 and 1,
and that the trajectories end over magnets 0 and 1.

Run (from anywhere):
    python3 -I figures-src/physics-of-ai/find_pairs.py
Runtime about 30 s on an Apple M4 Max (single process). Writes data/candidates.json,
identical to the list the figure was originally chosen from.
"""
import json
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pendulum as P  # noqa: E402

SEED = 3
N_DRAWS, N_CAND = 4000, 60
R_BAND = (0.55, 1.0)
SPLIT_DIST = 0.08
SPLIT_T = (2.5, 7.0)
INSIDE = 1.2 * 0.97
N_KEEP = 12


def load_map():
    path = os.path.join(HERE, 'data', 'basins_N1600.npz')
    if not os.path.exists(path):
        sys.exit(f'{os.path.relpath(path)} not found: run compute_basins.py first')
    d = np.load(path)
    lab = d['label'].astype(int); N = int(d['N']); lo, hi = d['domain']
    cell = (hi - lo) / N
    centers = lo + (np.arange(N) + 0.5) * cell      # x of column j; y of row i is centers[N-1-i]
    return lab, N, centers


def search(lab, N, centers, kw):
    rng = np.random.default_rng(SEED)
    cand = []
    for _ in range(N_DRAWS):
        i, j = rng.integers(1, N - 2, 2)
        if lab[i, j] == lab[i, j + 1]:
            continue
        xa, ya = centers[j], centers[N - 1 - i]      # row 0 = top (largest y)
        if R_BAND[0] < np.hypot(xa, ya) < R_BAND[1]:
            cand.append((i, j))
        if len(cand) >= N_CAND:
            break
    results = []
    for (i, j) in cand:
        x0, y0 = centers[j], centers[N - 1 - i]
        x1, y1 = centers[j + 1], centers[N - 1 - i]
        pa, la, _ = P.trajectory(x0, y0, **kw)
        pb, lb, _ = P.trajectory(x1, y1, **kw)
        if la == lb or la != lab[i, j] or lb != lab[i, j + 1]:
            continue                                   # orientation/label consistency check
        n = min(len(pa), len(pb))
        sep = np.hypot(*(pa[:n] - pb[:n]).T)
        t_split = np.argmax(sep > SPLIT_DIST) * kw['dt']
        inside = np.all(np.abs(np.vstack([pa, pb])) < INSIDE)
        results.append(dict(i=int(i), j=int(j), x0=float(x0), y0=float(y0), x1=float(x1), y1=float(y1),
                            la=la, lb=lb, t_split=float(t_split), inside=bool(inside),
                            len_a=len(pa), len_b=len(pb)))
    good = [r for r in results if r['inside'] and SPLIT_T[0] < r['t_split'] < SPLIT_T[1]]
    good.sort(key=lambda r: -r['t_split'])
    print(f'{len(cand)} candidate cells, {len(results)} label-consistent pairs, {len(good)} usable')
    return good[:N_KEEP]


def check_pair(pair, good, lab, N, centers, kw):
    key = ('x0', 'y0', 'x1', 'y1')
    hits = [k for k, g in enumerate(good) if all(g[q] == pair[q] for q in key)]
    print('params.json pair is candidate', hits)
    (i, j), (i2, j2) = pair['provenance']['grid_cells_row_col']
    assert (i2, j2) == (i, j + 1)
    assert (centers[j], centers[N - 1 - i], centers[j + 1], centers[N - 1 - i]) == tuple(pair[q] for q in key)
    map_labels = [int(lab[i, j]), int(lab[i, j + 1])]
    _, la, _ = P.trajectory(pair['x0'], pair['y0'], **kw)
    _, lb, _ = P.trajectory(pair['x1'], pair['y1'], **kw)
    print(f'cells ({i}, {j}) and ({i}, {j + 1}): basin-map labels {map_labels}, '
          f'trajectory labels {[la, lb]}, params.json labels {pair["labels"]}')
    assert map_labels == [la, lb] == pair['labels'] == pair['provenance']['basin_map_labels']
    assert len(hits) == 1, 'params.json pair is not among the search results'
    print('OK: pair checked against the basin map')


def main():
    t0 = time.time()
    with open(os.path.join(HERE, 'params.json')) as f:
        prm = json.load(f)
    itg = prm['integration']
    kw = dict(dt=itg['dt'], T=itg['T_max'], t_min=itg['t_min'], settle=itg['settle'])
    lab, N, centers = load_map()
    good = search(lab, N, centers, kw)
    out = os.path.join(HERE, 'data', 'candidates.json')
    with open(out, 'w') as f:
        json.dump(good, f, indent=1)
    for k, g in enumerate(good):
        print(f'  {k:2d}  cells ({g["i"]}, {g["j"]})  labels {g["la"]},{g["lb"]}  t_split {g["t_split"]:.3f}')
    check_pair(prm['pair'], good, lab, N, centers, kw)
    print(f'wrote {os.path.relpath(out)} in {time.time() - t0:.0f} s')


if __name__ == '__main__':
    main()
