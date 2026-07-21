// Draws the hand-drawn research-theme visuals onto every
//   <svg class="lab-visual" data-lab-visual="attractor|landscape|network" data-seed="N">
// using LabVisuals (lab-visuals.js) + Rough.js. Deterministic per seed.
(function () {
  var tries = 0;

  function drawAll() {
    if (!window.rough || !window.LabVisuals) {
      // Script order in the HTML already guarantees both are loaded; this
      // only covers a slow/failed fetch, so give up rather than poll forever.
      if (tries++ > 50) return;
      setTimeout(drawAll, 40);
      return;
    }
    document.querySelectorAll('svg.lab-visual[data-lab-visual]').forEach(function (svg) {
      var kind = svg.getAttribute('data-lab-visual');
      var seed = parseInt(svg.getAttribute('data-seed') || '7', 10);
      var nodes = parseInt(svg.getAttribute('data-nodes') || '34', 10);
      if (kind === 'attractor') window.LabVisuals.drawAttractor(svg, { seed: seed });
      else if (kind === 'landscape') window.LabVisuals.drawLandscape(svg, { seed: seed });
      else if (kind === 'network') window.LabVisuals.drawNetwork(svg, { seed: seed, nodes: nodes });
    });
  }

  drawAll();

  // No resize listener: the drawings are deterministic per seed and live in a
  // fixed 600x600 viewBox, so a redraw is byte-identical — pure wasted work
  // (mobile URL-bar show/hide fires resize constantly during scroll).
})();
