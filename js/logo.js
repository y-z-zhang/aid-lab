// AI & Dynamics Group logo + wordmark.
// All styles are intentionally inline and self-contained — styles.css has
// no wordmark rules, so this file is the single source of truth.
// Injects markup into elements marked with:
//   data-logo-mark         – the circular phase-space mark (data-size, data-accent)
//   data-wordmark          – "AI & Dynamics" + GROUP tag (data-size: 0..1)
// The mark is a Möbius-ribbon infinity (single-edged, hence one edge color).

(function () {
  // Möbius-ribbon infinity: a band with a half-twist, drawn by its edges.
  // The accent's intensity varies continuously along the band's SINGLE
  // boundary edge over its full double circuit — down one visible track,
  // through the twist, back along the other — so the two drawn curves carry
  // complementary gradients that hand off across the twist. That handoff is
  // the topology: a Möbius band has one edge. Points precomputed in a
  // 100x100 viewBox (centerline is a 1:2 Lissajous tilted -14°; the band
  // tapers edge-on where it dives under the crossing).
  const _trackL = [[40.7,59.8],[38.9,62.1],[37.2,64.1],[35.6,65.7],[34.1,66.8],[32.8,67.4],[31.9,67.6],[31.3,67.6],[30.9,67.4],[30.4,67.0],[29.8,66.4],[29.1,65.5],[28.2,64.2],[27.4,62.5],[26.7,60.6],[26.0,58.5],[25.5,56.3],[25.1,54.1],[24.9,51.9],[24.9,49.9],[25.1,48.1],[25.4,46.7],[25.8,45.7],[26.1,45.2],[26.3,45.1],[26.2,45.2],[26.2,45.3],[26.5,45.3],[27.3,45.4],[28.6,45.8],[30.4,46.4],[32.5,47.4],[34.9,48.7],[37.5,50.2],[40.2,51.9],[43.1,53.8],[46.1,55.8],[49.2,57.8],[52.2,59.8],[55.3,61.7],[58.4,63.5],[61.5,65.0],[64.5,66.4],[67.6,67.4],[70.7,68.0],[73.9,68.1],[77.2,67.6],[80.3,66.3],[82.9,64.2],[84.9,61.6],[86.1,58.8],[86.9,55.8],[87.2,52.9],[87.2,49.9],[86.9,46.9],[86.3,43.8],[85.5,40.8],[84.5,37.9],[83.3,35.1],[81.9,32.5],[80.3,30.1],[78.5,27.9],[76.4,26.0],[74.0,24.6],[71.3,23.7],[68.5,23.6],[65.7,24.2],[63.3,25.4],[61.1,27.0],[59.1,29.0],[57.3,31.3],[55.5,33.9],[53.8,36.7]];
  const _trackR = [[46.2,63.3],[44.5,66.1],[42.7,68.7],[40.9,71.0],[38.9,73.0],[36.7,74.6],[34.3,75.8],[31.5,76.4],[28.7,76.3],[26.0,75.4],[23.6,74.0],[21.5,72.1],[19.7,69.9],[18.1,67.5],[16.7,64.9],[15.5,62.1],[14.5,59.2],[13.7,56.2],[13.1,53.1],[12.8,50.1],[12.8,47.1],[13.1,44.2],[13.9,41.2],[15.1,38.4],[17.1,35.8],[19.7,33.7],[22.8,32.4],[26.1,31.9],[29.3,32.0],[32.4,32.6],[35.5,33.6],[38.5,35.0],[41.6,36.5],[44.7,38.3],[47.8,40.2],[50.8,42.2],[53.9,44.2],[56.9,46.2],[59.8,48.1],[62.5,49.8],[65.1,51.3],[67.5,52.6],[69.6,53.6],[71.4,54.2],[72.7,54.6],[73.5,54.7],[73.8,54.7],[73.8,54.8],[73.7,54.9],[73.9,54.8],[74.2,54.3],[74.6,53.3],[74.9,51.9],[75.1,50.1],[75.1,48.1],[74.9,45.9],[74.5,43.7],[74.0,41.5],[73.3,39.4],[72.6,37.5],[71.8,35.8],[70.9,34.5],[70.2,33.6],[69.6,33.0],[69.1,32.6],[68.7,32.4],[68.1,32.4],[67.2,32.6],[65.9,33.2],[64.4,34.3],[62.8,35.9],[61.1,37.9],[59.3,40.2]];
  const _amber = [255, 182, 122];
  const _bg = [7, 10, 13];   // matches --bg; the gradient fades toward it

  function _edgeSegments(ew) {
    let out = '';
    [_trackL, _trackR].forEach((pts, k) => {
      const n = pts.length - 1;
      for (let i = 0; i < n; i++) {
        const s = k * 0.5 + 0.5 * (i + 0.5) / n;          // position along the one edge
        const f = 0.30 + 0.70 * (1 + Math.cos(2 * Math.PI * s)) / 2;
        const c = _amber.map((a, j) => Math.round(_bg[j] + (a - _bg[j]) * f));
        out += `<path d="M ${pts[i][0]} ${pts[i][1]} L ${pts[i + 1][0]} ${pts[i + 1][1]}" stroke="rgb(${c[0]},${c[1]},${c[2]})" stroke-width="${ew}" stroke-linecap="round" fill="none"/>`;
      }
    });
    return out;
  }

  function mark({ size, stroke, strokeWidth = 3 }) {
    const ew = (strokeWidth * 0.8).toFixed(2);
    return `<svg width="${size}" height="${size}" viewBox="0 0 100 100" style="display:block" aria-hidden="true">
      <circle cx="50" cy="50" r="45" fill="none" stroke="${stroke}" stroke-width="${strokeWidth}"/>
      ${_edgeSegments(ew)}
    </svg>`;
  }

  function wordmark({ size = 1, color = '#EDEEEA', accent = '#FFB67A' }) {
    const fs = 20 * size;
    return `<span class="wordmark-host" style="display:inline-flex;align-items:baseline;gap:${(8 * size).toFixed(2)}px;font-family:'Geist',system-ui,sans-serif;color:${color};line-height:1">
      <span style="font-weight:600;font-size:${fs}px;letter-spacing:-0.02em;white-space:nowrap">AI <span style="color:${accent}">&amp;</span> Dynamics</span>
      <span style="font-family:'Geist Mono',ui-monospace,monospace;font-size:${(fs * 0.42).toFixed(2)}px;letter-spacing:0.14em;opacity:0.55;text-transform:uppercase;padding-bottom:${(fs * 0.06).toFixed(2)}px">Group</span>
    </span>`;
  }

  document.querySelectorAll('[data-logo-mark]').forEach(el => {
    el.innerHTML = mark({
      size: parseInt(el.dataset.size || '36', 10),
      stroke: el.dataset.stroke || '#EDEEEA',
      accent: el.dataset.accent || '#FFB67A',
    });
  });

  document.querySelectorAll('[data-wordmark]').forEach(el => {
    el.innerHTML = wordmark({
      size: parseFloat(el.dataset.size || '1'),
      color: el.dataset.color || '#EDEEEA',
      accent: el.dataset.accent || '#FFB67A',
    });
  });
})();
