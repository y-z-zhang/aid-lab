/*
 * lab-visuals.js — hand-drawn research-card illustrations for AID Lab
 * ------------------------------------------------------------------
 * Framework-agnostic. Depends on Rough.js (https://roughjs.com) loaded
 * first as `window.rough`. Exposes `window.LabVisuals` with three pure
 * render functions, each taking an <svg> element + options:
 *
 *   LabVisuals.drawAttractor(svgEl, opts)   // card 1 — "Learning of dynamics"
 *   LabVisuals.drawLandscape(svgEl, opts)   // card 2 — "Dynamics of learning"
 *   LabVisuals.drawNetwork(svgEl, opts)     // card 3 — "Rule of emergence"
 *
 * Shared opts: { roughness, seed }. drawNetwork also takes { nodes }.
 * Deterministic for a given seed, so output is stable across re-renders.
 * Palette is the AID Lab site palette (amber / green / cyan).
 */
(function () {
  'use strict';

  // ---- palette (matches the AID Lab site accents) ------------------------
  var PALETTE = {
    attractor: '#FFB67A',          // amber
    landscape: '#85FFC7',          // mint green
    landscapeTrail: '#D6FFEC',     // lighter mint for the descent trail
    network: '#7ED6E0',            // cyan
    networkWhite: '#EDEEEA',       // site ink
    networkEdge: '#5E86A6'         // muted connector
  };

  // ---- tiny seeded RNG (mulberry32) so layouts are reproducible ----------
  function makeRng(seed) {
    var t = seed >>> 0;
    return function () {
      t += 0x6d2b79f5;
      var r = Math.imul(t ^ (t >>> 15), 1 | t);
      r ^= r + Math.imul(r ^ (r >>> 7), 61 | r);
      return ((r ^ (r >>> 14)) >>> 0) / 4294967296;
    };
  }
  function clamp(v, lo, hi) { return v < lo ? lo : v > hi ? hi : v; }
  function dist(a, b) { var dx = a.x - b.x, dy = a.y - b.y; return Math.sqrt(dx * dx + dy * dy); }

  // ---- reset an <svg> to a clean 600x600 drawing surface -----------------
  function prep(svg, size) {
    while (svg.firstChild) svg.removeChild(svg.firstChild);
    svg.setAttribute('viewBox', '0 0 ' + size + ' ' + size);
    svg.setAttribute('preserveAspectRatio', 'xMidYMid meet');
  }

  // ---- small hand-drawn arrowhead pointing along (dx,dy) -----------------
  function arrow(svg, rc, x, y, dx, dy, color, roughness, seed) {
    var len = Math.hypot(dx, dy) || 1;
    var ux = dx / len, uy = dy / len;
    var ax = -uy, ay = ux;            // perpendicular
    var s = 9;                         // arrow size
    var p1 = [x - ux * s + ax * s * 0.55, y - uy * s + ay * s * 0.55];
    var p2 = [x - ux * s - ax * s * 0.55, y - uy * s - ay * s * 0.55];
    [p1, p2].forEach(function (p, i) {
      var g = rc.line(x, y, p[0], p[1], { stroke: color, strokeWidth: 1.3, roughness: roughness, bowing: 1, seed: seed + i });
      g.setAttribute('opacity', '0.9');
      svg.appendChild(g);
    });
  }

  // =======================================================================
  // CARD 1 — phase-portrait of a nonlinear system spiralling to a fixed pt
  // =======================================================================
  function drawAttractor(svg, opts) {
    var o = Object.assign({ color: PALETTE.attractor, roughness: 1.7, seed: 7, turns: 3.6, passes: 2 }, opts || {});
    prep(svg, 600);
    var rc = window.rough.svg(svg);
    var cx = 300, cy = 296, maxR = 215, steps = 260;

    var pts = [];
    for (var i = 0; i <= steps; i++) {
      var t = i / steps;
      var ang = t * o.turns * 2 * Math.PI;
      var r = maxR * Math.pow(t, 0.82);
      r += Math.sin(ang * 1.7 + 1.0) * 12 * t + Math.cos(ang * 0.8 + 0.4) * 7 * t;
      var x = cx + r * Math.cos(ang);
      var y = cy + r * Math.sin(ang) * 0.9;
      pts.push([x, y]);
    }

    for (var p = 0; p < o.passes; p++) {
      var g = rc.curve(pts, { stroke: o.color, strokeWidth: 1.5, roughness: o.roughness, bowing: 1.6, seed: o.seed + p * 13 });
      g.setAttribute('opacity', p === 0 ? '0.95' : '0.38');
      svg.appendChild(g);
    }

    [0.30, 0.62].forEach(function (f, k) {
      var idx = Math.floor(f * steps);
      var a = pts[idx], b = pts[idx - 6] || pts[idx];
      arrow(svg, rc, a[0], a[1], b[0] - a[0], b[1] - a[1], o.color, o.roughness, o.seed + 50 + k * 4);
    });

    var dot = rc.circle(cx, cy, 13, { fill: o.color, fillStyle: 'solid', fillWeight: 2, stroke: o.color, strokeWidth: 1.2, roughness: 1, seed: o.seed });
    svg.appendChild(dot);
  }

  // =======================================================================
  // CARD 2 — hand-sketched loss landscape (contours) + descent trajectory
  // =======================================================================
  function drawLandscape(svg, opts) {
    var o = Object.assign({ color: PALETTE.landscape, trail: PALETTE.landscapeTrail, roughness: 1.5, seed: 21, levels: 9 }, opts || {});
    prep(svg, 600);
    var rc = window.rough.svg(svg);
    var bx = 262, by = 312;

    for (var L = o.levels; L >= 1; L--) {
      var tt = L / o.levels;
      var baseR = 26 + tt * 232;
      var ring = [];
      var segs = 70;
      for (var i = 0; i <= segs; i++) {
        var ang = (i / segs) * 2 * Math.PI;
        var rr = baseR * (1 + 0.17 * Math.sin(ang * 2 + L * 0.55) + 0.10 * Math.sin(ang * 3 + 1.3) + 0.05 * Math.sin(ang * 5 + L));
        var pull = 1 - 0.16 * tt * Math.max(0, Math.cos(ang - 0.6));
        ring.push([bx + rr * Math.cos(ang) * pull, by + rr * Math.sin(ang) * 0.82 * pull]);
      }
      var g = rc.curve(ring, { stroke: o.color, strokeWidth: 1.15, roughness: o.roughness, bowing: 1.2, seed: o.seed + L * 7 });
      g.setAttribute('opacity', (0.28 + 0.5 * (1 - tt)).toFixed(3));
      svg.appendChild(g);
    }

    var rng = makeRng(o.seed * 97 + 5);
    var path = [];
    var x = 470, y = 96;
    for (var s = 0; s < 11; s++) {
      path.push([x, y]);
      var dx = (bx - x), dy = (by - y);
      var step = 0.34 - s * 0.012;
      x += dx * step + (rng() - 0.5) * 30 * (1 - s / 12);
      y += dy * step + (rng() - 0.5) * 22 * (1 - s / 12);
    }
    path.push([bx + 4, by - 2]);

    var line = rc.curve(path, { stroke: o.trail, strokeWidth: 1.8, roughness: o.roughness * 0.9, bowing: 1, seed: o.seed + 3 });
    line.setAttribute('opacity', '0.95');
    svg.appendChild(line);

    path.forEach(function (pt, idx) {
      var last = idx === path.length - 1;
      var c = rc.circle(pt[0], pt[1], last ? 12 : 5.5, {
        fill: last ? o.trail : o.color, fillStyle: 'solid', fillWeight: 2,
        stroke: last ? o.trail : o.color, strokeWidth: 1, roughness: 1.1, seed: o.seed + idx * 4
      });
      c.setAttribute('opacity', last ? '1' : '0.85');
      svg.appendChild(c);
    });
  }

  // =======================================================================
  // CARD 3 — complex modular network with higher-order (simplicial) faces
  // =======================================================================
  function drawNetwork(svg, opts) {
    var o = Object.assign({
      color: PALETTE.network, white: PALETTE.networkWhite, edge: PALETTE.networkEdge,
      roughness: 1.4, seed: 31, nodes: 34
    }, opts || {});
    prep(svg, 600);
    var rc = window.rough.svg(svg);
    var rng = makeRng((o.seed * 2654435761) >>> 0);
    var N = Math.max(6, o.nodes | 0);
    var W = 600, cx = 300, cy = 300;

    var nClusters = N <= 16 ? 2 : N <= 30 ? 3 : 4;
    var clusters = [];
    for (var c = 0; c < nClusters; c++) {
      var a = (c / nClusters) * 2 * Math.PI - Math.PI / 2 + (rng() - 0.5) * 0.5;
      var rr = 126 * (0.72 + 0.46 * rng());
      clusters.push({ x: cx + rr * Math.cos(a), y: cy + rr * Math.sin(a) * 0.92, nodes: [] });
    }
    var nodes = [];
    for (var i = 0; i < N; i++) {
      var cl = clusters[i % nClusters];
      var spread = 56 + 30 * rng();
      var gx = (rng() + rng() + rng() - 1.5) / 1.5;
      var gy = (rng() + rng() + rng() - 1.5) / 1.5;
      var node = {
        x: clamp(cl.x + gx * spread, 58, W - 58),
        y: clamp(cl.y + gy * spread, 58, W - 58),
        c: i % nClusters, deg: 0, i: i
      };
      nodes.push(node); cl.nodes.push(node);
    }

    var edges = [], edgeSet = new Set();
    function addEdge(a, b) {
      if (a === b) return;
      var key = a < b ? a + '-' + b : b + '-' + a;
      if (edgeSet.has(key)) return;
      edgeSet.add(key); edges.push([a, b]); nodes[a].deg++; nodes[b].deg++;
    }
    clusters.forEach(function (cl) {
      cl.nodes.forEach(function (n) {
        var near = cl.nodes.filter(function (m) { return m !== n; })
          .map(function (m) { return { m: m, d: dist(n, m) }; })
          .sort(function (p, q) { return p.d - q.d; });
        var k = 2 + (rng() < 0.45 ? 1 : 0);
        for (var j = 0; j < Math.min(k, near.length); j++) addEdge(n.i, near[j].m.i);
      });
    });
    for (var cc = 0; cc < nClusters; cc++) {
      var A = clusters[cc].nodes, B = clusters[(cc + 1) % nClusters].nodes, best = null;
      A.forEach(function (na) { B.forEach(function (nb) { var d = dist(na, nb); if (!best || d < best.d) best = { a: na, b: nb, d: d }; }); });
      if (best) addEdge(best.a.i, best.b.i);
      if (rng() < 0.6) { var ra = A[(rng() * A.length) | 0], rb = B[(rng() * B.length) | 0]; if (ra && rb) addEdge(ra.i, rb.i); }
    }
    var extra = Math.round(N * 0.2);
    for (var e = 0; e < extra; e++) addEdge((rng() * N) | 0, (rng() * N) | 0);

    var adj = []; for (var z = 0; z < N; z++) adj.push(new Set());
    edges.forEach(function (ed) { adj[ed[0]].add(ed[1]); adj[ed[1]].add(ed[0]); });
    var tris = [];
    for (var a1 = 0; a1 < N && tris.length < 24; a1++) {
      adj[a1].forEach(function (b1) {
        if (b1 > a1) adj[b1].forEach(function (c1) {
          if (c1 > b1 && adj[a1].has(c1)) tris.push([a1, b1, c1]);
        });
      });
    }
    function triPerim(t) { return dist(nodes[t[0]], nodes[t[1]]) + dist(nodes[t[1]], nodes[t[2]]) + dist(nodes[t[2]], nodes[t[0]]); }
    tris.sort(function (p, q) { return triPerim(p) - triPerim(q); });
    var chosen = tris.slice(0, Math.min(6, tris.length));

    chosen.forEach(function (t, idx) {
      var g = rc.polygon(
        [[nodes[t[0]].x, nodes[t[0]].y], [nodes[t[1]].x, nodes[t[1]].y], [nodes[t[2]].x, nodes[t[2]].y]],
        { fill: o.color, fillStyle: 'hachure', hachureGap: 5.5, fillWeight: 0.6, stroke: 'none', roughness: o.roughness, seed: o.seed + idx * 5 }
      );
      g.setAttribute('opacity', '0.17');
      svg.appendChild(g);
    });
    edges.forEach(function (ed, idx) {
      var na = nodes[ed[0]], nb = nodes[ed[1]];
      var g = rc.line(na.x, na.y, nb.x, nb.y, { stroke: o.edge, strokeWidth: 1, roughness: o.roughness, bowing: 1.7, seed: o.seed + idx * 3 });
      g.setAttribute('opacity', '0.5');
      svg.appendChild(g);
    });
    var maxDeg = nodes.reduce(function (m, n) { return Math.max(m, n.deg); }, 1);
    nodes.forEach(function (n, idx) {
      var t = n.deg / maxDeg;
      var rad = 4.5 + t * 7;
      var isHub = n.deg >= maxDeg * 0.7;
      var isWhite = !isHub && rng() < 0.38;
      var stroke = isWhite ? o.white : o.color;
      var cfg = { stroke: stroke, strokeWidth: 1.3, roughness: Math.min(o.roughness * 0.5, 0.7), disableMultiStroke: true, seed: o.seed + idx * 7 };
      if (isHub) { cfg.fill = o.color; cfg.fillStyle = 'solid'; cfg.fillWeight = 2.4; }
      else if (isWhite) { cfg.fill = o.white; cfg.fillStyle = 'solid'; cfg.fillWeight = 2.4; }
      var g = rc.circle(n.x, n.y, rad * 2, cfg);
      svg.appendChild(g);
    });
  }

  window.LabVisuals = {
    PALETTE: PALETTE,
    makeRng: makeRng,
    drawAttractor: drawAttractor,
    drawLandscape: drawLandscape,
    drawNetwork: drawNetwork
  };
})();
