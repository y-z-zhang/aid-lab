// Generative SVG visuals for research themes.
// Renders into any element matching [data-visual] with attributes:
//   data-visual="loss" | "phase" | "network"
//   data-stroke   – primary stroke color
//   data-accent   – accent color (used by loss & network)
//   data-size     – pixel size (square viewport)

(function () {
  function lossLandscape({ stroke, accent, size }) {
    const lines = [];
    for (let k = 1; k < 12; k++) {
      const v = k / 12;
      let d = '';
      const steps = 90;
      for (let j = 0; j <= steps; j++) {
        const a = (j / steps) * Math.PI * 2;
        const r = 30 + v * 80 + Math.sin(a * 3 + k) * 8 + Math.cos(a * 2 + k * 0.5) * 6;
        const x = 120 + Math.cos(a) * r * 1.0;
        const y = 120 + Math.sin(a) * r * 0.85;
        d += (j ? 'L' : 'M') + x.toFixed(1) + ' ' + y.toFixed(1) + ' ';
      }
      lines.push({ d, op: 0.25 + k * 0.04 });
    }
    let path = '';
    for (let j = 0; j < 90; j++) {
      const t = j / 90;
      const a = t * Math.PI * 6;
      const r = (1 - t) * 100;
      const x = 120 + Math.cos(a) * r;
      const y = 120 + Math.sin(a) * r * 0.85;
      path += (j ? 'L' : 'M') + x.toFixed(1) + ' ' + y.toFixed(1) + ' ';
    }
    const contour = lines.map(l =>
      `<path d="${l.d}" fill="none" stroke="${stroke}" stroke-width="0.6" opacity="${l.op.toFixed(2)}"/>`
    ).join('');
    return `<svg viewBox="0 0 240 240" width="${size}" height="${size}" style="display:block">
      ${contour}
      <path d="${path}" fill="none" stroke="${accent}" stroke-width="1.2" stroke-linecap="round"/>
      <circle cx="120" cy="120" r="3" fill="${accent}"/>
    </svg>`;
  }

  function phasePortrait({ stroke, size }) {
    const N = 1200;
    let d = '';
    for (let i = 0; i < N; i++) {
      const t = (i / N) * Math.PI * 12;
      const r = 0.9 - i / N * 0.6;
      const x = r * Math.cos(t * 1.0);
      const y = r * Math.sin(t * 1.7);
      d += (i ? 'L' : 'M') + (x * 90 + 120).toFixed(1) + ' ' + (y * 90 + 120).toFixed(1) + ' ';
    }
    return `<svg viewBox="0 0 240 240" width="${size}" height="${size}" style="display:block">
      <path d="${d}" fill="none" stroke="${stroke}" stroke-width="0.7" stroke-linecap="round" opacity="0.85"/>
    </svg>`;
  }

  function networkGlyph({ stroke, accent, size }) {
    const nodes = [];
    const N = 12;
    for (let i = 0; i < N; i++) {
      const a = (i / N) * Math.PI * 2 - Math.PI / 2;
      nodes.push([120 + Math.cos(a) * 90, 120 + Math.sin(a) * 90]);
    }
    const edges = [
      [0, 5], [0, 7], [1, 6], [2, 8], [3, 9], [4, 10], [5, 11], [6, 0], [2, 5], [8, 11],
    ];
    const triangle = [[0, 4, 8], [2, 6, 10]];
    const tris = triangle.map(tri =>
      `<polygon points="${tri.map(j => nodes[j].join(',')).join(' ')}" fill="${accent}" opacity="0.10"/>`
    ).join('');
    const ed = edges.map(([a, b]) =>
      `<line x1="${nodes[a][0].toFixed(1)}" y1="${nodes[a][1].toFixed(1)}" x2="${nodes[b][0].toFixed(1)}" y2="${nodes[b][1].toFixed(1)}" stroke="${stroke}" stroke-width="0.7" opacity="0.6"/>`
    ).join('');
    const ns = nodes.map(([x, y], i) =>
      `<circle cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="${i % 4 === 0 ? 4 : 2.6}" fill="${i % 4 === 0 ? accent : stroke}"/>`
    ).join('');
    return `<svg viewBox="0 0 240 240" width="${size}" height="${size}" style="display:block">
      ${tris}${ed}${ns}
    </svg>`;
  }

  function ruggedLoss({ stroke, accent, size }) {
    // Multi-basin scalar field rendered via marching-squares contours, with
    // a 1.6px drop shadow under each contour for depth, plus a gradient-
    // descent training trajectory that snakes from a high corner toward
    // the global minimum.
    const W = 240, H = 240;
    const GRID = 72;
    // [cx, cy, amplitude, sigma] — negative wells are basins, positive are
    // peaks. A gentle bowl background pulls everything inward.
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
    // Sample the field on a regular grid.
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
    // Marching squares: per cell, produce the line segment(s) where the
    // iso-level crosses the cell, with linear interpolation on each edge.
    function contour(level) {
      const segs = [];
      const dx = W / GRID, dy = H / GRID;
      for (let i = 0; i < GRID; i++) {
        for (let j = 0; j < GRID; j++) {
          const tl = grid[i][j];
          const tr = grid[i][j + 1];
          const br = grid[i + 1][j + 1];
          const bl = grid[i + 1][j];
          const code =
            (tl > level ? 8 : 0) |
            (tr > level ? 4 : 0) |
            (br > level ? 2 : 0) |
            (bl > level ? 1 : 0);
          if (code === 0 || code === 15) continue;
          const x = j * dx, y = i * dy;
          const top    = [x + dx * (level - tl) / (tr - tl), y];
          const right  = [x + dx, y + dy * (level - tr) / (br - tr)];
          const bottom = [x + dx * (level - bl) / (br - bl), y + dy];
          const left   = [x, y + dy * (level - tl) / (bl - tl)];
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
    for (let k = 1; k <= LEVELS; k++) {
      const v = zMin + (zMax - zMin) * (k / (LEVELS + 1));
      const segs = contour(v);
      const opacity = 0.20 + (k / LEVELS) * 0.55;
      let path = '', shadow = '';
      for (let s = 0; s < segs.length; s++) {
        const [a, b] = segs[s];
        path   += `M${a[0].toFixed(1)} ${a[1].toFixed(1)}L${b[0].toFixed(1)} ${b[1].toFixed(1)}`;
        shadow += `M${(a[0] + 1.6).toFixed(1)} ${(a[1] + 1.6).toFixed(1)}L${(b[0] + 1.6).toFixed(1)} ${(b[1] + 1.6).toFixed(1)}`;
      }
      parts += `<path d="${shadow}" fill="none" stroke="${stroke}" stroke-width="0.5" opacity="${(opacity * 0.22).toFixed(2)}"/>`;
      parts += `<path d="${path}" fill="none" stroke="${stroke}" stroke-width="0.6" opacity="${opacity.toFixed(2)}"/>`;
    }
    // Training trajectory: noisy gradient descent from a high corner.
    let traj = '';
    let px = 0.86, py = 0.16;
    for (let i = 0; i < 220; i++) {
      const [gx, gy] = grad(px, py);
      px -= 0.012 * gx + Math.sin(i * 0.21) * 0.0009;
      py -= 0.012 * gy + Math.cos(i * 0.27) * 0.0009;
      px = Math.max(0.02, Math.min(0.98, px));
      py = Math.max(0.02, Math.min(0.98, py));
      traj += (i ? 'L' : 'M') + (px * W).toFixed(1) + ' ' + (py * H).toFixed(1) + ' ';
    }
    parts += `<path d="${traj}" fill="none" stroke="${accent}" stroke-width="1.1" opacity="0.95" stroke-linecap="round" stroke-linejoin="round"/>`;
    parts += `<circle cx="${(minJ * W / GRID).toFixed(1)}" cy="${(minI * H / GRID).toFixed(1)}" r="2.6" fill="${accent}"/>`;
    return `<svg viewBox="0 0 240 240" width="${size}" height="${size}" style="display:block">${parts}</svg>`;
  }

  const renderers = { loss: lossLandscape, phase: phasePortrait, network: networkGlyph, rugged: ruggedLoss };

  document.querySelectorAll('[data-visual]').forEach(el => {
    const type = el.dataset.visual;
    const fn = renderers[type];
    if (!fn) return;
    const stroke = el.dataset.stroke || '#EDEEEA';
    const accent = el.dataset.accent || '#FFB67A';
    const size = parseInt(el.dataset.size || '300', 10);
    el.innerHTML = fn({ stroke, accent, size });
  });
})();
