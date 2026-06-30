// Draws the hand-drawn research-theme visuals onto every
//   <svg class="lab-visual" data-lab-visual="attractor|landscape|network" data-seed="N">
// using LabVisuals (lab-visuals.js) + Rough.js. Deterministic per seed.
// Waits for both libraries, then redraws on resize (debounced) so the
// hand-drawn strokes re-fit the element cleanly.
(function () {
  function drawAll() {
    if (!window.rough || !window.LabVisuals) { setTimeout(drawAll, 40); return; }
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

  // The drawings are scale-independent (600x600 viewBox), so a resize doesn't
  // strictly require a redraw — but a debounced redraw keeps stroke density
  // crisp if the element's pixel size changes a lot (e.g. mobile rotation).
  var t = 0;
  window.addEventListener('resize', function () {
    clearTimeout(t);
    t = setTimeout(drawAll, 250);
  });
})();
