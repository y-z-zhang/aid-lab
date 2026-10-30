"""Render the 'Networks and emergence' site figure: the basin of a twisted state, with tentacles.

What it shows
  A 2-D slice through the 83-dimensional state space of a ring of identical Kuramoto oscillators,
  centred on the stable q = 15 twisted state, with every starting point labelled by the winding
  number q_final of the twisted state it ends in. Following Zhang & Strogatz, "Basins with
  tentacles", PRL 127, 194101 (2021), Fig. 4 construction (see compute_slice.py for the system, the
  slice and the numerics). dq = 15 - q_final >= 0 everywhere in the slice.

What is drawn (8 x 8 in at 100 dpi -> 800 x 800 px, axes fill the figure, no axis, page #070A0D)
  view    a1 (left to right) and a2 (bottom to top) in [-0.72 pi, 0.72 pi], centred on the twisted
          state. The data window is [-0.8 pi, 0.8 pi] on a 1600^2 grid of cell centres
          a_k = 0.8 * (-pi + (k + 1/2) * 2 pi / 1600); the view is its central 1440^2 cells.
  core    the central basin {dq = 0} (q_final = 15): contourf at levels [-0.5, 0.5], fill #2A1F18,
          outlined by the contour dq = 0.5 in #FFB67A, 2.8 px wide (2.8 * 0.72 pt), drawn last.
  lines   outlines of the nested sets {dq <= k} for k = 3, 6, 9: contour of the integer field dq
          at level k + 0.5 (so every line runs along cell boundaries of the data), 2.0 px wide,
          k = 3 #8A938F, k = 6 #5A6268, k = 9 #343C42, drawn outer first (k = 9, 6, 3).
  rest    everything else is the page colour; starting points ending in q_final <= 5 (dq >= 10) lie
          outside the outermost line. The sets are nested, so the outlines never cross; where two
          layers pinch to a few cells the strokes touch.
  Drawing order: core fill, k = 9, 6, 3 outlines, core outline.

Reads   data/slice_n83_q15_s7_g1600_h0.8_dt0.1.npz   (written by compute_slice.py; nothing is
        recomputed here)
Writes  out/networks-emergence.png   (800 x 800 RGBA PNG straight from matplotlib savefig; alpha
        is 255 everywhere). figures-src/export_webp.py turns it into
        assets/figures/networks-emergence.webp.

Run     python3 -I render.py          (from any directory; paths are relative to this file)
Runtime under 1 s on an Apple M4 Max (python 3.11.8, numpy 1.26.4, matplotlib 3.8.0, Pillow 10.2.0).
Check   With matplotlib 3.8.0 the output is pixel-identical (max abs difference 0 over all four
        channels) to the PNG the site's WebP was converted from. Other matplotlib versions may
        differ by antialiasing at the line edges.
"""
import os
import sys

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data", "slice_n83_q15_s7_g1600_h0.8_dt0.1.npz")
OUT_DIR = os.path.join(HERE, "out")
OUT_PNG = os.path.join(OUT_DIR, "networks-emergence.png")

DPI = 100
SIZE_IN = 8.0                    # 8 in at 100 dpi = 800 px
PT_PER_PX = 72.0 / DPI           # line widths below are given in px at 800 px
BG = "#070A0D"                   # page colour
CORE_FILL = "#2A1F18"
CORE_LINE = ("#FFB67A", 2.8)     # (colour, width in px)
LINES = [(3, "#8A938F"),         # (k, colour): outline of {dq <= k}
         (6, "#5A6268"),
         (9, "#343C42")]
LINE_PX = 2.0
VIEW_HALF = 0.72                 # half-width of the view, in units of pi


def load(path=DATA):
    """Return (npz, dq, half): dq = q_center - q_final on the grid (row index = a2, column = a1)."""
    d = np.load(path)
    qc = int(d["q_center"])
    q = d["q"].astype(int)
    assert q.max() == qc, "dq = q_center - q_final assumes q_final <= q_center everywhere"
    return d, qc - q, float(d["half"])


def grid_points(G, half):
    """Cell centres used by compute_slice.py, the same for a1 and a2."""
    return half * (-np.pi + (np.arange(G) + 0.5) * 2 * np.pi / G)


def render(dq, half, out_png=OUT_PNG):
    a = grid_points(dq.shape[0], half)
    W = VIEW_HALF * np.pi
    fig = plt.figure(figsize=(SIZE_IN, SIZE_IN), dpi=DPI, facecolor=BG)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_axis_off()
    ax.set_facecolor(BG)
    ax.set_xlim(-W, W)
    ax.set_ylim(-W, W)
    ax.contourf(a, a, dq, levels=[-0.5, 0.5], colors=[CORE_FILL])
    for k, col in sorted(LINES, reverse=True):                     # outer first, inner on top
        ax.contour(a, a, dq, levels=[k + 0.5], colors=[col], linewidths=LINE_PX * PT_PER_PX,
                   linestyles="solid")
    col, px = CORE_LINE
    ax.contour(a, a, dq, levels=[0.5], colors=[col], linewidths=px * PT_PER_PX, linestyles="solid")
    fig.savefig(out_png, dpi=DPI, facecolor=BG)
    plt.close(fig)


def main():
    d, dq, half = load()
    os.makedirs(OUT_DIR, exist_ok=True)
    render(dq, half)
    G = dq.shape[0]
    m = int(round(G * (1 - VIEW_HALF / half) / 2))                  # cells cropped per side
    crop = dq[m:G - m, m:G - m]
    qc = int(d["q_center"])
    print("data:", os.path.relpath(DATA, HERE), "| n", int(d["n"]), "q_center", qc,
          "seed", int(d["seed"]), "grid", G, "half", half, "dt", float(d["dt"]))
    print(f"view +/-{VIEW_HALF} pi = central {G - 2 * m}^2 cells; q_final in view "
          f"{qc - crop.max()}..{qc - crop.min()}; central basin {(crop == 0).mean():.4f} of the view")
    print("wrote", os.path.relpath(OUT_PNG, HERE))


if __name__ == "__main__":
    sys.exit(main())
