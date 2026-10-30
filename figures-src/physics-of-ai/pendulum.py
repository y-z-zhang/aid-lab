"""Magnetic pendulum model shared by every script in this folder.

System (Zhang et al., Chaos 35, 073102 (2025), Eqs. (5)-(6); Zhang & Cornelius,
PRR 5, 033213 (2023), Eqs. (1)-(3)):
    x'' = -w0^2 x - a x' + sum_i (xi - x)/D_i^3
    y'' = -w0^2 y - a y' + sum_i (yi - y)/D_i^3,   D_i = sqrt((x-xi)^2 + (y-yi)^2 + h^2)
with w0 = 0.5, a = 0.2, h = 0.2 and magnets at
    0: (1/sqrt3, 0)   1: (-1/(2 sqrt3), -1/2)   2: (-1/(2 sqrt3), 1/2).
Potential V(x, y) = w0^2 (x^2 + y^2)/2 - sum_i 1/D_i; energy E = |v|^2/2 + V.

Integrator: classical fixed-step RK4 (rk4_step), vectorised over release points.

Classification (exact for the true flow): E is non-increasing (dE/dt = -a|v|^2). The
lowest non-minimum critical value of V is the index-1 saddle energy
E_C = -4.920805396 (verified by critical_points() below). Once E < E_C - MARGIN the bob
is confined to the sublevel component of one minimum, which lies inside that magnet's
Voronoi cell (mirror-symmetry argument), so the label is the nearest magnet.

Functions
    acc, energy, potential, nearest, rk4_step   model and integrator
    run(x0, y0, dt, T)        batched release-from-rest with energy-trap freeze
                              (used by compute_basins.py for the basin map)
    trajectory(x0, y0, ...)   one full path, run until trapped plus a short settle
                              (used by render.py and find_pairs.py)
    critical_points()         all critical points of V in [-2, 2]^2 (root finding)

Run
    python3 -I pendulum.py
prints the critical points (3 minima at V = -6.932384411, 3 index-1 saddles at
V = -4.920805396, 1 index-2 maximum at the origin at V = -4.909902530) and checks
that E_C matches the saddle energy to 1e-9. Runtime about 2 s on an Apple M4 Max.
Writes nothing.
"""
import numpy as np

W0, A, H = 0.5, 0.2, 0.2
W02, H2 = W0**2, H**2
MX = np.array([1/np.sqrt(3), -1/(2*np.sqrt(3)), -1/(2*np.sqrt(3))])
MY = np.array([0.0, -0.5, 0.5])
E_C = -4.920805396
MARGIN = 1e-3


def acc(x, y, vx, vy):
    ax = -W02*x - A*vx
    ay = -W02*y - A*vy
    for i in range(3):
        dx = MX[i] - x
        dy = MY[i] - y
        r2 = dx*dx + dy*dy + H2
        inv3 = r2**-1.5
        ax += dx*inv3
        ay += dy*inv3
    return ax, ay


def energy(x, y, vx, vy):
    E = 0.5*(vx*vx + vy*vy) + 0.5*W02*(x*x + y*y)
    for i in range(3):
        E -= 1.0/np.sqrt((x-MX[i])**2 + (y-MY[i])**2 + H2)
    return E


def potential(x, y):
    V = 0.5 * W02 * (x * x + y * y)
    for i in range(3):
        V -= 1.0 / np.sqrt((x - MX[i]) ** 2 + (y - MY[i]) ** 2 + H2)
    return V


def nearest(x, y):
    d = np.stack([(x-MX[i])**2 + (y-MY[i])**2 for i in range(3)])
    return np.argmin(d, axis=0).astype(np.int8)


def rk4_step(x, y, vx, vy, dt):
    k1x, k1y, k1vx, k1vy = vx, vy, *acc(x, y, vx, vy)
    h2 = 0.5*dt
    x2, y2, vx2, vy2 = x+h2*k1x, y+h2*k1y, vx+h2*k1vx, vy+h2*k1vy
    k2x, k2y, k2vx, k2vy = vx2, vy2, *acc(x2, y2, vx2, vy2)
    x3, y3, vx3, vy3 = x+h2*k2x, y+h2*k2y, vx+h2*k2vx, vy+h2*k2vy
    k3x, k3y, k3vx, k3vy = vx3, vy3, *acc(x3, y3, vx3, vy3)
    x4, y4, vx4, vy4 = x+dt*k3x, y+dt*k3y, vx+dt*k3vx, vy+dt*k3vy
    k4x, k4y, k4vx, k4vy = vx4, vy4, *acc(x4, y4, vx4, vy4)
    s = dt/6.0
    return (x + s*(k1x+2*k2x+2*k3x+k4x), y + s*(k1y+2*k2y+2*k3y+k4y),
            vx + s*(k1vx+2*k2vx+2*k3vx+k4vx), vy + s*(k1vy+2*k2vy+2*k3vy+k4vy))


def run(x0, y0, dt, T, check_every=20):
    """Integrate from rest at (x0, y0). Returns label (-1 = not trapped by T),
    trap time, nearest-magnet label at T (fallback), max energy increase between checks."""
    n = x0.size
    x, y = x0.astype(np.float64).copy(), y0.astype(np.float64).copy()
    vx, vy = np.zeros(n), np.zeros(n)
    idx = np.arange(n)
    label = np.full(n, -1, np.int8)
    ttrap = np.full(n, np.nan)
    fallback = np.full(n, -1, np.int8)
    E_prev = energy(x, y, vx, vy)
    max_dE = -np.inf
    nsteps = int(round(T/dt))
    step = 0
    while step < nsteps and idx.size:
        m = min(check_every, nsteps - step)
        for _ in range(m):
            x, y, vx, vy = rk4_step(x, y, vx, vy, dt)
        step += m
        E = energy(x, y, vx, vy)
        if E.size:
            max_dE = max(max_dE, float(np.max(E - E_prev)))
        done = E < E_C - MARGIN
        if np.any(done):
            label[idx[done]] = nearest(x[done], y[done])
            ttrap[idx[done]] = step*dt
            keep = ~done
            idx, x, y, vx, vy, E = idx[keep], x[keep], y[keep], vx[keep], vy[keep], E[keep]
        E_prev = E
    fallback[:] = label
    if idx.size:
        fallback[idx] = nearest(x, y)
    return label, ttrap, fallback, max_dE


def trajectory(x0, y0, dt=0.0025, T=40.0, t_min=1.0, settle=3.0):
    """One path released from rest at (x0, y0), RK4 with step dt, energy checked every step.
    Once E < E_C - MARGIN (and t > t_min) it continues for `settle` time units so the
    capture spiral is visible, then stops. Returns (path (n, 2), final nearest-magnet label,
    trap time or None if not trapped by T)."""
    x, y, vx, vy = np.array([x0]), np.array([y0]), np.zeros(1), np.zeros(1)
    pts = [(x0, y0)]
    E_trap = E_C - MARGIN
    t_trap = None
    for k in range(int(T / dt)):
        x, y, vx, vy = rk4_step(x, y, vx, vy, dt)
        pts.append((x[0], y[0]))
        if energy(x, y, vx, vy)[0] < E_trap and k * dt > t_min:
            t_trap = (k + 1) * dt
            for _ in range(int(settle / dt)):
                x, y, vx, vy = rk4_step(x, y, vx, vy, dt)
                pts.append((x[0], y[0]))
            break
    return np.array(pts), int(nearest(x, y)[0]), t_trap


def _grad(p):
    x, y = p
    gx, gy = W02*x, W02*y
    for i in range(3):
        D3 = ((x-MX[i])**2 + (y-MY[i])**2 + H2)**1.5
        gx += (x-MX[i])/D3
        gy += (y-MY[i])/D3
    return np.array([gx, gy])


def critical_points():
    """Critical points of V in [-2, 2]^2: hybr root finding from every 7th node of a
    401 x 401 grid, deduplicated at 1e-6. Returns [(x, y, V, Hessian index)] sorted by V."""
    from scipy.optimize import root
    g = np.linspace(-2, 2, 401)
    X, Y = np.meshgrid(g, g)
    found = []
    for x0, y0 in zip(X.ravel()[::7], Y.ravel()[::7]):
        s = root(_grad, [x0, y0], method='hybr', tol=1e-14)
        if s.success and np.max(np.abs(_grad(s.x))) < 1e-10 and np.all(np.abs(s.x) < 3):
            if not any(np.hypot(*(s.x - f)) < 1e-6 for f in found):
                found.append(s.x)
    out = []
    e = 1e-6
    for p in sorted(found, key=lambda p: potential(*p)):
        hess = np.array([(_grad(p + [e, 0]) - _grad(p - [e, 0])) / (2*e),
                         (_grad(p + [0, e]) - _grad(p - [0, e])) / (2*e)]).T
        out.append((float(p[0]), float(p[1]), float(potential(*p)),
                    int(np.sum(np.linalg.eigvalsh(hess) < 0))))
    return out


if __name__ == '__main__':
    cps = critical_points()
    for x, y, v, idx in cps:
        print(f'x={x: .9f} y={y: .9f}  V={v: .9f}  index={idx}')
    saddles = [v for *_, v, idx in cps if idx == 1]
    assert len(saddles) == 3 and max(abs(v - E_C) for v in saddles) < 1e-9, saddles
    assert min(v for *_, v, idx in cps if idx > 0) == min(saddles), 'E_C is not the lowest non-minimum level'
    print(f'E_C = {E_C} matches the index-1 saddle energy (|diff| < 1e-9)')
