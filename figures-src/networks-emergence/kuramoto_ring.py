"""Model and integrator for the 'Networks and emergence' figure (imported by compute_slice.py and
validate.py; not run on its own, writes nothing).

System (Zhang & Strogatz, "Basins with tentacles", PRL 127, 194101 (2021), Eq. 1): a ring of n
identical phase oscillators with nearest-neighbour Kuramoto coupling, in the rotating frame,
    dtheta_i/dt = sin(theta_{i+1} - theta_i) + sin(theta_{i-1} - theta_i),   theta_{n+1} = theta_1.
It is a gradient flow with potential V = -sum_i cos(theta_{i+1} - theta_i). Its stable equilibria
include the q-twisted states theta_i = 2 pi i q / n (stable for |q| < n/4).

Slice (the paper's Fig. 4 construction): theta = theta0 + a1 * P1 + a2 * P2 with a1, a2 in (-pi, pi],
theta0 the q-twisted state, and P1, P2 binary vectors with floor(n/2) randomly chosen ones, drawn
from numpy.random.default_rng(seed) (slice_directions).

Integrator: classical fixed-step RK4 on the whole batch (rk4_step), vectorised over starting points.

Early classification (integrate_until_absorbed), exact for this model: let
phi_i = wrap(theta_{i+1} - theta_i) in (-pi, pi]. In phi-coordinates
dphi_i/dt = u_{i+1} - 2 u_i + u_{i-1} with u = sin(phi), hence
du_i/dt = cos(phi_i) (u_{i+1} - 2 u_i + u_{i-1}). If max_i |phi_i| < pi/2 then cos(phi_i) > 0 and the
discrete maximum principle gives max u nonincreasing and min u nondecreasing, so the set
{max_i |phi_i| <= c < pi/2} is forward invariant. No phi_i can then cross +-pi, the winding number
q = sum(phi) / (2 pi) is frozen, and the flow converges to the q-twisted state. A trajectory is
therefore labelled and frozen as soon as max |phi| < pi/2 - MARGIN (MARGIN = 0.05 rad), checked every
check_every = 10 steps (and at t = 0). The label is checked against full convergence in validate.py.
"""
import numpy as np

TWO_PI = 2.0 * np.pi
MARGIN = 0.05  # radians below pi/2


def wrap(x):
    """Wrap to (-pi, pi]."""
    return np.pi - np.mod(np.pi - x, TWO_PI)


def rhs(th):
    """th: (B, n). Returns dtheta/dt, shape (B, n)."""
    s = np.sin(np.roll(th, -1, axis=1) - th)      # s_i = sin(theta_{i+1} - theta_i)
    return s - np.roll(s, 1, axis=1)               # + sin(theta_{i-1} - theta_i) = -s_{i-1}


def rk4_step(th, dt):
    k1 = rhs(th)
    k2 = rhs(th + 0.5 * dt * k1)
    k3 = rhs(th + 0.5 * dt * k2)
    k4 = rhs(th + dt * k3)
    return th + (dt / 6.0) * (k1 + 2 * k2 + 2 * k3 + k4)


def neighbour_diffs(th):
    return wrap(np.roll(th, -1, axis=1) - th)


def winding(th):
    return np.rint(neighbour_diffs(th).sum(axis=1) / TWO_PI).astype(np.int64)


def energy(th):
    return -np.cos(np.roll(th, -1, axis=1) - th).sum(axis=1)


def twisted_state(n, q):
    return TWO_PI * np.arange(n) * q / n


def slice_directions(n, seed):
    rng = np.random.default_rng(seed)
    P = np.zeros((2, n))
    for k in range(2):
        idx = rng.choice(n, size=n // 2, replace=False)
        P[k, idx] = 1.0
    return P


def integrate_until_absorbed(th, dt, t_max, check_every=10, margin=MARGIN):
    """Integrate a batch with RK4; freeze each row once max|phi| < pi/2 - margin.

    Returns (q, t_freeze, absorbed, th_final). Rows never absorbed by t_max are
    labelled by their current winding number and flagged absorbed=False.
    """
    th = th.copy()
    B = th.shape[0]
    q = np.zeros(B, dtype=np.int64)
    t_freeze = np.full(B, np.inf)
    absorbed = np.zeros(B, dtype=bool)
    active = np.arange(B)
    cur = th
    thresh = np.pi / 2 - margin
    n_steps = int(round(t_max / dt))
    step = 0
    # check at t=0 as well
    while True:
        if step % check_every == 0 or step == n_steps:
            phi = neighbour_diffs(cur)
            done = np.abs(phi).max(axis=1) < thresh
            if done.any():
                rows = active[done]
                q[rows] = np.rint(phi[done].sum(axis=1) / TWO_PI).astype(np.int64)
                t_freeze[rows] = step * dt
                absorbed[rows] = True
                th[rows] = cur[done]
                active = active[~done]
                cur = cur[~done]
            if active.size == 0 or step >= n_steps:
                break
        cur = rk4_step(cur, dt)
        step += 1
    if active.size:
        q[active] = winding(cur)
        th[active] = cur
    return q, t_freeze, absorbed, th
