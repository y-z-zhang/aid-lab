// AID Lab logo + wordmark.
// Injects markup into elements marked with:
//   data-logo-mark         – the circular phase-space mark (data-size, data-accent)
//   data-wordmark          – "AıD Lab" with phase-arc dot (data-size: 0..1)
// The mark uses a 3:2 Lissajous closed loop as the trajectory.

(function () {
  function lissajousPath(N = 320) {
    let d = '';
    for (let i = 0; i <= N; i++) {
      const t = (i / N) * Math.PI * 2;
      const x = 0.78 * Math.sin(3 * t + Math.PI / 2);
      const y = 0.62 * Math.sin(2 * t);
      const sx = 50 + x * 38;
      const sy = 50 + y * 38;
      d += (i ? 'L' : 'M') + sx.toFixed(2) + ' ' + sy.toFixed(2) + ' ';
    }
    return d;
  }
  const _path = lissajousPath();

  function mark({ size, stroke, accent, strokeWidth = 1.4 }) {
    return `<svg width="${size}" height="${size}" viewBox="0 0 100 100" style="display:block" aria-hidden="true">
      <circle cx="50" cy="50" r="46" fill="none" stroke="${stroke}" stroke-width="${strokeWidth}"/>
      <path d="${_path}" fill="none" stroke="${stroke}" stroke-width="${(strokeWidth * 0.85).toFixed(2)}" opacity="0.65" stroke-linecap="round"/>
      <circle cx="50" cy="50" r="2.2" fill="${stroke}"/>
      <circle cx="88" cy="50" r="2.6" fill="${accent}"/>
      <circle cx="12" cy="50" r="2.6" fill="${accent}"/>
    </svg>`;
  }

  function wordmark({ size = 1, color = '#EDEEEA', accent = '#FFB67A' }) {
    const fs = 22 * size;
    return `<span class="wordmark-host" style="display:inline-flex;align-items:baseline;gap:${(8 * size).toFixed(2)}px;font-family:'Geist',system-ui,sans-serif;color:${color};line-height:1">
      <span style="font-weight:600;font-size:${fs}px;letter-spacing:-0.03em;position:relative">A<span style="position:relative;display:inline-block;margin:0 -0.02em"><span style="font-weight:600">ı</span><svg width="${(fs * 0.5).toFixed(2)}" height="${(fs * 0.45).toFixed(2)}" viewBox="0 0 20 18" style="position:absolute;left:50%;top:-0.45em;transform:translateX(-50%)" aria-hidden="true"><path d="M2 14 Q 10 -2 18 14" fill="none" stroke="${accent}" stroke-width="1.6" stroke-linecap="round"/><circle cx="10" cy="4" r="2.4" fill="${accent}"/></svg></span>D</span>
      <span style="font-family:'Geist Mono',ui-monospace,monospace;font-size:${(fs * 0.42).toFixed(2)}px;letter-spacing:0.14em;opacity:0.55;text-transform:uppercase;padding-bottom:${(fs * 0.06).toFixed(2)}px">Lab</span>
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
