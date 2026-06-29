// Generative SVG visuals for research themes — hand-drawn treatment.
//
// Renders into any element matching [data-visual] with attributes:
//   data-visual="loss" | "rugged" | "network" | "phase"
//   data-stroke   – primary stroke color
//   data-accent   – accent color (used by loss & network)
//   data-size     – pixel size (square viewport)
//
// The hand-drawn feel comes from three things applied to otherwise-precise
// geometry:
//   1. warp()  — a smooth, deterministic 2D displacement field. Because the
//      displacement is a pure function of (x, y), points that coincide (a
//      shared contour vertex, an edge endpoint meeting a node) move together,
//      so lines wobble organically without ever breaking apart.
//   2. smooth() — draws a polyline as flowing quadratic Béziers through
//      segment midpoints, so strokes curve like a pen rather than faceting.
//   3. a faint second pass at a decorrelated warp phase — the classic
//      sketch "drawn twice, not quite the same" doubling.

(function () {
  // Coherent wobble. `ph` decorrelates the second pencil pass.
  function warp(x, y, amp, ph) {
    ph = ph || 0;
    const dx =
      Math.sin(0.045 * y + 0.021 * x + 0.7 + ph) * amp +
      Math.sin(0.110 * y - 0.030 * x + 2.1 + ph) * amp * 0.45;
    const dy =
      Math.cos(0.043 * x - 0.019 * y + 1.3 + ph) * amp +
      Math.cos(0.100 * x + 0.028 * y + 0.4 + ph) * amp * 0.45;
    return [x + dx, y + dy];
  }

  // Warp a list of [x,y] points.
  function warpPts(pts, amp, ph) {
    return pts.map(p => warp(p[0], p[1], amp, ph));
  }

  // Polyline → flowing path via quadratic Béziers through midpoints.
  function smooth(pts, close) {
    if (pts.length < 2) return '';
    const f = n => n.toFixed(2);
    let d = `M${f(pts[0][0])} ${f(pts[0][1])}`;
    for (let i = 1; i < pts.length - 1; i++) {
      const mx = (pts[i][0] + pts[i + 1][0]) / 2;
      const my = (pts[i][1] + pts[i + 1][1]) / 2;
      d += `Q${f(pts[i][0])} ${f(pts[i][1])} ${f(mx)} ${f(my)}`;
    }
    const last = pts[pts.length - 1];
    d += `L${f(last[0])} ${f(last[1])}`;
    if (close) d += 'Z';
    return d;
  }

  // A primary line, drawn twice (two warp phases) for a sketched look.
  function sketch(basePts, { stroke, width, opacity, amp, close }) {
    const a = smooth(warpPts(basePts, amp, 0.0), close);
    const b = smooth(warpPts(basePts, amp * 0.8, 1.9), close);
    return (
      `<path d="${a}" fill="none" stroke="${stroke}" stroke-width="${width}" opacity="${opacity}" stroke-linecap="round" stroke-linejoin="round"/>` +
      `<path d="${b}" fill="none" stroke="${stroke}" stroke-width="${(width * 0.7).toFixed(2)}" opacity="${(opacity * 0.45).toFixed(2)}" stroke-linecap="round" stroke-linejoin="round"/>`
    );
  }

  function svg(size, inner) {
    return `<svg viewBox="0 0 240 240" width="${size}" height="${size}" style="display:block">${inner}</svg>`;
  }

  // ----------------------------------------------------------------
  // LOSS LANDSCAPE — concentric wobbly contours + a descent spiral.
  // ----------------------------------------------------------------
  function lossLandscape({ stroke, accent, size }) {
    let parts = '';
    const steps = 64;
    for (let k = 1; k < 12; k++) {
      const v = k / 12;
      const pts = [];
      for (let j = 0; j <= steps; j++) {
        const a = (j / steps) * Math.PI * 2;
        const r = 30 + v * 80 + Math.sin(a * 3 + k) * 8 + Math.cos(a * 2 + k * 0.5) * 6;
        pts.push([120 + Math.cos(a) * r, 120 + Math.sin(a) * r * 0.85]);
      }
      const op = (0.22 + k * 0.045).toFixed(2);
      parts += `<path d="${smooth(warpPts(pts, 1.7), true)}" fill="none" stroke="${stroke}" stroke-width="0.7" opacity="${op}" stroke-linejoin="round"/>`;
    }
    // Descent spiral inward.
    const spiral = [];
    for (let j = 0; j <= 84; j++) {
      const t = j / 84;
      const a = t * Math.PI * 6;
      const r = (1 - t) * 100;
      spiral.push([120 + Math.cos(a) * r, 120 + Math.sin(a) * r * 0.85]);
    }
    parts += sketch(spiral, { stroke: accent, width: 1.3, opacity: 0.95, amp: 2.2, close: false });
    const c = warp(120, 120, 1.7);
    parts += `<circle cx="${c[0].toFixed(1)}" cy="${c[1].toFixed(1)}" r="3" fill="${accent}"/>`;
    return svg(size, parts);
  }

  // ----------------------------------------------------------------
  // PHASE PORTRAIT — a single long damped Lissajous trajectory.
  // ----------------------------------------------------------------
  function phasePortrait({ stroke, size }) {
    const N = 600;
    const pts = [];
    for (let i = 0; i < N; i++) {
      const t = (i / N) * Math.PI * 12;
      const r = 0.9 - (i / N) * 0.6;
      pts.push([Math.cos(t) * r * 90 + 120, Math.sin(t * 1.7) * r * 90 + 120]);
    }
    return svg(
      size,
      `<path d="${smooth(warpPts(pts, 1.2), false)}" fill="none" stroke="${stroke}" stroke-width="0.8" stroke-linecap="round" stroke-linejoin="round" opacity="0.85"/>`
    );
  }

  // ----------------------------------------------------------------
  // RUGGED LOSS — marching-squares contours of a multi-basin field,
  // with a noisy gradient-descent trajectory. Every contour vertex is
  // warped coherently, so the iso-lines stay closed but ripple by hand.
  // ----------------------------------------------------------------
  function ruggedLoss({ stroke, accent, size }) {
    const W = 240, H = 240, GRID = 72;
    const wells = [
      [0.34, 0.44, -1.10, 0.16],
      [0.66, 0.32, -0.55, 0.12],
      [0.55, 0.72, -0.72, 0.14],
      [0.22, 0.78,  0.42, 0.10],
      [0.82, 0.72,  0.35, 0.10],
      [0.78, 0.55, -0.28, 0.08],
      [0.42, 0.20,  0.30, 0.09],
    ];
    function f(x, y) {
      let z = 0.38 * ((x - 0.5) ** 2 + (y - 0.5) ** 2);
      for (let i = 0; i < wells.length; i++) {
        const [cx, cy, a, s] = wells[i];
        const dx = x - cx, dy = y - cy;
        z += a * Math.exp(-(dx * dx + dy * dy) / (2 * s * s));
      }
      return z;
    }
    function grad(x, y) {
      const h = 0.001;
      return [(f(x + h, y) - f(x - h, y)) / (2 * h), (f(x, y + h) - f(x, y - h)) / (2 * h)];
    }
    const grid = [];
    let zMin = Infinity, zMax = -Infinity, minI = 0, minJ = 0;
    for (let i = 0; i <= GRID; i++) {
      const row = [];
      for (let j = 0; j <= GRID; j++) {
        const z = f(j / GRID, i / GRID);
        row.push(z);
        if (z < zMin) { zMin = z; minI = i; minJ = j; }
        if (z > zMax) zMax = z;
      }
      grid.push(row);
    }
    function contour(level) {
      const segs = [];
      const dx = W / GRID, dy = H / GRID;
      for (let i = 0; i < GRID; i++) {
        for (let j = 0; j < GRID; j++) {
          const tl = grid[i][j], tr = grid[i][j + 1], br = grid[i + 1][j + 1], bl = grid[i + 1][j];
          const code = (tl > level ? 8 : 0) | (tr > level ? 4 : 0) | (br > level ? 2 : 0) | (bl > level ? 1 : 0);
          if (code === 0 || code === 15) continue;
          const x = j * dx, y = i * dy;
          const top = [x + dx * (level - tl) / (tr - tl), y];
          const right = [x + dx, y + dy * (level - tr) / (br - tr)];
          const bottom = [x + dx * (level - bl) / (br - bl), y + dy];
          const left = [x, y + dy * (level - tl) / (bl - tl)];
          switch (code) {
            case 1: case 14: segs.push([left, bottom]); break;
            case 2: case 13: segs.push([bottom, right]); break;
            case 3: case 12: segs.push([left, right]); break;
            case 4: case 11: segs.push([top, right]); break;
            case 6: case 9:  segs.push([top, bottom]); break;
            case 7: case 8:  segs.push([top, left]); break;
            case 5: segs.push([left, top]); segs.push([right, bottom]); break;
            case 10: segs.push([left, bottom]); segs.push([top, right]); break;
          }
        }
      }
      return segs;
    }
    let parts = '';
    const LEVELS = 14;
    const f1 = n => n.toFixed(1);
    for (let k = 1; k <= LEVELS; k++) {
      const v = zMin + (zMax - zMin) * (k / (LEVELS + 1));
      const segs = contour(v);
      const opacity = 0.20 + (k / LEVELS) * 0.55;
      // Warp each segment endpoint coherently; shared vertices stay joined.
      let main = '', sk = '';
      for (let s = 0; s < segs.length; s++) {
        const a0 = warp(segs[s][0][0], segs[s][0][1], 1.4);
        const b0 = warp(segs[s][1][0], segs[s][1][1], 1.4);
        main += `M${f1(a0[0])} ${f1(a0[1])}L${f1(b0[0])} ${f1(b0[1])}`;
        const a1 = warp(segs[s][0][0], segs[s][0][1], 1.2, 1.9);
        const b1 = warp(segs[s][1][0], segs[s][1][1], 1.2, 1.9);
        sk += `M${f1(a1[0])} ${f1(a1[1])}L${f1(b1[0])} ${f1(b1[1])}`;
      }
      parts += `<path d="${sk}" fill="none" stroke="${stroke}" stroke-width="0.5" opacity="${(opacity * 0.3).toFixed(2)}" stroke-linecap="round"/>`;
      parts += `<path d="${main}" fill="none" stroke="${stroke}" stroke-width="0.7" opacity="${opacity.toFixed(2)}" stroke-linecap="round"/>`;
    }
    // Training trajectory: noisy gradient descent from a high corner.
    const traj = [];
    let px = 0.86, py = 0.16;
    for (let i = 0; i < 200; i++) {
      const [gx, gy] = grad(px, py);
      px -= 0.012 * gx + Math.sin(i * 0.21) * 0.0009;
      py -= 0.012 * gy + Math.cos(i * 0.27) * 0.0009;
      px = Math.max(0.02, Math.min(0.98, px));
      py = Math.max(0.02, Math.min(0.98, py));
      traj.push([px * W, py * H]);
    }
    parts += sketch(traj, { stroke: accent, width: 1.2, opacity: 0.95, amp: 1.6, close: false });
    const m = warp((minJ * W) / GRID, (minI * H) / GRID, 1.4);
    parts += `<circle cx="${m[0].toFixed(1)}" cy="${m[1].toFixed(1)}" r="2.6" fill="${accent}"/>`;
    return svg(size, parts);
  }

  // ----------------------------------------------------------------
  // NETWORK GLYPH — ring of nodes, sketched chord edges, two faint
  // triangular faces. Geometry is warped at draw time so nodes and the
  // edges that meet them shift together.
  // ----------------------------------------------------------------
  function networkGlyph({ stroke, accent, size }) {
    const N = 12;
    const base = [];
    for (let i = 0; i < N; i++) {
      const a = (i / N) * Math.PI * 2 - Math.PI / 2;
      base.push([120 + Math.cos(a) * 90, 120 + Math.sin(a) * 90]);
    }
    const edges = [[0, 5], [0, 7], [1, 6], [2, 8], [3, 9], [4, 10], [5, 11], [6, 0], [2, 5], [8, 11]];
    const triangle = [[0, 4, 8], [2, 6, 10]];

    // Sample a base segment into points so the warp can bow it.
    function seg(p, q, n) {
      const out = [];
      for (let i = 0; i <= n; i++) out.push([p[0] + (q[0] - p[0]) * i / n, p[1] + (q[1] - p[1]) * i / n]);
      return out;
    }

    let parts = '';

    // Faint hand-drawn triangular faces (sketched outline + soft fill).
    triangle.forEach(tri => {
      const loop = [];
      for (let e = 0; e < 3; e++) {
        const p = base[tri[e]], q = base[tri[(e + 1) % 3]];
        seg(p, q, 5).slice(0, -1).forEach(pt => loop.push(pt));
      }
      const d = smooth(warpPts(loop, 1.3), true);
      parts += `<path d="${d}" fill="${accent}" fill-opacity="0.07" stroke="${accent}" stroke-width="0.5" opacity="0.4" stroke-linejoin="round"/>`;
    });

    // Sketched chord edges — sampled, warped, bowed.
    edges.forEach(([a, b]) => {
      const pts = seg(base[a], base[b], 7);
      parts += sketch(pts, { stroke, width: 0.7, opacity: 0.55, amp: 2.0, close: false });
    });

    // Nodes — warped centers so they sit where the edges meet.
    base.forEach((p, i) => {
      const w = warp(p[0], p[1], 2.0);
      const hub = i % 4 === 0;
      parts += `<circle cx="${w[0].toFixed(1)}" cy="${w[1].toFixed(1)}" r="${hub ? 4 : 2.6}" fill="${hub ? accent : stroke}"/>`;
    });

    return svg(size, parts);
  }

  const renderers = { loss: lossLandscape, phase: phasePortrait, network: networkGlyph, rugged: ruggedLoss };

  document.querySelectorAll('[data-visual]').forEach(el => {
    const fn = renderers[el.dataset.visual];
    if (!fn) return;
    el.innerHTML = fn({
      stroke: el.dataset.stroke || '#EDEEEA',
      accent: el.dataset.accent || '#FFB67A',
      size: parseInt(el.dataset.size || '300', 10),
    });
  });
})();
