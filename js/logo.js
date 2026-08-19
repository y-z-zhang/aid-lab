// AI & Dynamics Group logo + wordmark.
// All styles are intentionally inline and self-contained — styles.css has
// no wordmark rules, so this file is the single source of truth.
// Injects markup into elements marked with:
//   data-logo-mark         – the circular phase-space mark (data-size, data-accent)
//   data-wordmark          – "AI & Dynamics" + GROUP tag (data-size: 0..1)
// The mark is a Möbius-ribbon infinity (single-edged, hence one edge color).

(function () {
  // Möbius-ribbon infinity: a band with a half-twist, drawn by its edges.
  // Both visible edge curves are accent-colored because a Möbius band has
  // only one edge — trace it through the twist and you come back along the
  // other side. Paths precomputed in a 100x100 viewBox (centerline is a 1:2
  // Lissajous tilted -14°; the band tapers edge-on where it dives under).
  const _edgeL = 'M 40.7 59.8 L 39.8 61.0 L 38.9 62.2 L 38.0 63.3 L 37.1 64.2 L 36.2 65.1 L 35.4 65.8 L 34.6 66.4 L 33.9 66.9 L 33.3 67.2 L 32.7 67.5 L 32.2 67.6 L 31.8 67.6 L 31.5 67.6 L 31.2 67.5 L 31.0 67.4 L 30.8 67.3 L 30.6 67.1 L 30.3 66.9 L 30.0 66.6 L 29.6 66.2 L 29.2 65.7 L 28.8 65.1 L 28.4 64.4 L 28.0 63.6 L 27.5 62.8 L 27.1 61.9 L 26.8 60.9 L 26.4 59.8 L 26.1 58.7 L 25.8 57.6 L 25.5 56.5 L 25.3 55.3 L 25.1 54.2 L 25.0 53.0 L 24.9 51.9 L 24.9 50.9 L 24.9 49.9 L 25.0 48.9 L 25.1 48.0 L 25.2 47.3 L 25.4 46.6 L 25.6 46.0 L 25.8 45.6 L 26.0 45.3 L 26.1 45.1 L 26.2 45.1 L 26.3 45.1 L 26.3 45.1 L 26.2 45.2 L 26.2 45.3 L 26.3 45.3 L 26.4 45.3 L 26.7 45.3 L 27.1 45.4 L 27.7 45.5 L 28.3 45.7 L 29.2 45.9 L 30.1 46.3 L 31.1 46.7 L 32.2 47.2 L 33.3 47.8 L 34.6 48.5 L 35.9 49.3 L 37.2 50.1 L 38.6 50.9 L 40.1 51.8 L 41.5 52.8 L 43.0 53.8 L 44.6 54.8 L 46.1 55.8 L 47.7 56.9 L 49.3 57.9 L 50.8 58.9 L 52.4 59.9 L 54.0 60.9 L 55.6 61.9 L 57.2 62.8 L 58.8 63.7 L 60.3 64.5 L 61.9 65.2 L 63.5 65.9 L 65.0 66.6 L 66.6 67.1 L 68.2 67.5 L 69.8 67.9 L 71.4 68.1 L 73.1 68.2 L 74.7 68.1 L 76.4 67.8 L 78.1 67.3 L 79.7 66.6 L 81.2 65.7 L 82.5 64.6 L 83.7 63.3 L 84.6 62.0 L 85.4 60.5 L 86.0 59.1 L 86.5 57.6 L 86.8 56.1 L 87.0 54.6 L 87.2 53.1 L 87.2 51.5 L 87.2 50.0 L 87.0 48.4 L 86.9 46.9 L 86.6 45.3 L 86.3 43.7 L 85.9 42.2 L 85.5 40.7 L 85.0 39.1 L 84.4 37.7 L 83.8 36.2 L 83.2 34.8 L 82.5 33.4 L 81.7 32.1 L 80.9 30.9 L 80.0 29.7 L 79.1 28.5 L 78.1 27.5 L 77.0 26.5 L 75.9 25.7 L 74.6 24.9 L 73.3 24.3 L 71.9 23.9 L 70.5 23.6 L 69.0 23.6 L 67.6 23.7 L 66.2 24.0 L 64.8 24.5 L 63.6 25.2 L 62.4 25.9 L 61.3 26.8 L 60.3 27.8 L 59.3 28.8 L 58.3 30.0 L 57.4 31.2 L 56.4 32.5 L 55.6 33.8 L 54.7 35.2 L 53.8 36.7';
  const _edgeR = 'M 46.2 63.3 L 45.3 64.8 L 44.4 66.2 L 43.6 67.5 L 42.6 68.8 L 41.7 70.0 L 40.7 71.2 L 39.7 72.2 L 38.7 73.2 L 37.6 74.1 L 36.4 74.8 L 35.2 75.5 L 33.8 76.0 L 32.4 76.3 L 31.0 76.4 L 29.5 76.4 L 28.1 76.1 L 26.7 75.7 L 25.4 75.1 L 24.1 74.3 L 23.0 73.5 L 21.9 72.5 L 20.9 71.5 L 20.0 70.3 L 19.1 69.1 L 18.3 67.9 L 17.5 66.6 L 16.8 65.2 L 16.2 63.8 L 15.6 62.3 L 15.0 60.9 L 14.5 59.3 L 14.1 57.8 L 13.7 56.3 L 13.4 54.7 L 13.1 53.1 L 13.0 51.6 L 12.8 50.0 L 12.8 48.5 L 12.8 46.9 L 13.0 45.4 L 13.2 43.9 L 13.5 42.4 L 14.0 40.9 L 14.6 39.5 L 15.4 38.0 L 16.3 36.7 L 17.5 35.4 L 18.8 34.3 L 20.3 33.4 L 21.9 32.7 L 23.6 32.2 L 25.3 31.9 L 26.9 31.8 L 28.6 31.9 L 30.2 32.1 L 31.8 32.5 L 33.4 32.9 L 35.0 33.4 L 36.5 34.1 L 38.1 34.8 L 39.7 35.5 L 41.2 36.3 L 42.8 37.2 L 44.4 38.1 L 46.0 39.1 L 47.6 40.1 L 49.2 41.1 L 50.7 42.1 L 52.3 43.1 L 53.9 44.2 L 55.4 45.2 L 57.0 46.2 L 58.5 47.2 L 59.9 48.2 L 61.4 49.1 L 62.8 49.9 L 64.1 50.7 L 65.4 51.5 L 66.7 52.2 L 67.8 52.8 L 68.9 53.3 L 69.9 53.7 L 70.8 54.1 L 71.7 54.3 L 72.3 54.5 L 72.9 54.6 L 73.3 54.7 L 73.6 54.7 L 73.7 54.7 L 73.8 54.7 L 73.8 54.8 L 73.7 54.9 L 73.7 54.9 L 73.8 54.9 L 73.9 54.9 L 74.0 54.7 L 74.2 54.4 L 74.4 54.0 L 74.6 53.4 L 74.8 52.7 L 74.9 52.0 L 75.0 51.1 L 75.1 50.1 L 75.1 49.1 L 75.1 48.1 L 75.0 47.0 L 74.9 45.8 L 74.7 44.7 L 74.5 43.5 L 74.2 42.4 L 73.9 41.3 L 73.6 40.2 L 73.2 39.1 L 72.9 38.1 L 72.5 37.2 L 72.0 36.4 L 71.6 35.6 L 71.2 34.9 L 70.8 34.3 L 70.4 33.8 L 70.0 33.4 L 69.7 33.1 L 69.4 32.9 L 69.2 32.7 L 69.0 32.6 L 68.8 32.5 L 68.5 32.4 L 68.2 32.4 L 67.8 32.4 L 67.3 32.5 L 66.7 32.8 L 66.1 33.1 L 65.4 33.6 L 64.6 34.2 L 63.8 34.9 L 62.9 35.8 L 62.0 36.7 L 61.1 37.8 L 60.2 39.0 L 59.3 40.2';

  function mark({ size, stroke, accent, strokeWidth = 3 }) {
    const ew = (strokeWidth * 0.8).toFixed(2);
    return `<svg width="${size}" height="${size}" viewBox="0 0 100 100" style="display:block" aria-hidden="true">
      <circle cx="50" cy="50" r="45" fill="none" stroke="${stroke}" stroke-width="${strokeWidth}"/>
      <path d="${_edgeL}" fill="none" stroke="${accent}" stroke-width="${ew}" stroke-linecap="round"/>
      <path d="${_edgeR}" fill="none" stroke="${accent}" stroke-width="${ew}" stroke-linecap="round"/>
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
