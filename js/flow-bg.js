// Subtle animated background — a slow flow-field of particles tracing
// trajectories of a 2D dynamical system (Duffing-like). Vanilla port of
// the prototype's React component.

(function () {
  const host = document.querySelector('[data-flow-field]');
  if (!host) return;

  // Respect the user's motion preference. If reduced motion is requested,
  // leave the hero with the dark canvas background and skip the animation
  // entirely — no particles, no rAF loop.
  if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    host.style.background = '#070A0D';
    return;
  }

  const canvas = document.createElement('canvas');
  canvas.style.width = '100%';
  canvas.style.height = '100%';
  canvas.style.display = 'block';
  canvas.style.background = '#070A0D';
  host.appendChild(canvas);

  const accent = host.dataset.accent || '#FFB67A';
  const baseDensity = parseFloat(host.dataset.density || '1');
  const speed = parseFloat(host.dataset.speed || '0.45');
  const opacity = parseFloat(host.dataset.opacity || '0.5');

  // Parse hex/named color into RGB triple for alpha blending.
  function parseRgb(c) {
    const tmp = document.createElement('div');
    tmp.style.color = c;
    document.body.appendChild(tmp);
    const cs = getComputedStyle(tmp).color;
    document.body.removeChild(tmp);
    const m = cs.match(/\d+/g);
    return m ? [+m[0], +m[1], +m[2]] : [255, 182, 122];
  }
  const rgb = parseRgb(accent);

  let raf = 0;
  let running = true;
  let last = performance.now();
  let particles = [];
  let width = 0, height = 0, N = 0, scale = 0, cx = 0, cy = 0;
  const ctx = canvas.getContext('2d');

  function setup() {
    const rect = host.getBoundingClientRect();
    width = Math.max(1, Math.round(rect.width));
    height = Math.max(1, Math.round(rect.height));
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    canvas.width = width * dpr;
    canvas.height = height * dpr;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    scale = Math.min(width, height) / 4.5;
    cx = width / 2;
    cy = height / 2;
    const density = baseDensity * (width < 720 ? 0.55 : 1.0);
    N = Math.round(220 * density);
    particles = [];
    for (let i = 0; i < N; i++) {
      const p = {};
      spawn(p);
      p.age = Math.random() * p.life;
      particles.push(p);
    }
    ctx.fillStyle = 'rgba(7,10,13,1)';
    ctx.fillRect(0, 0, width, height);
  }

  function spawn(p) {
    const side = Math.random();
    if (side < 0.5) {
      p.x = Math.random() * width;
      p.y = Math.random() * height;
    } else if (side < 0.75) {
      p.x = -10;
      p.y = Math.random() * height;
    } else {
      p.x = width + 10;
      p.y = Math.random() * height;
    }
    p.age = 0;
    p.life = 220 + Math.random() * 260;
    p.size = 0.5 + Math.random() * 1.2;
  }

  function field(x, y) {
    const sx = (x - cx) / scale;
    const sy = (y - cy) / scale;
    const dx = sy;
    const dy = sx - sx * sx * sx - 0.08 * sy + 0.03 * Math.sin(sx * 1.3);
    return [dx * scale * 0.18, dy * scale * 0.18];
  }

  function frame(now) {
    const dt = Math.min(48, now - last) / 16.67;
    last = now;
    ctx.fillStyle = 'rgba(7,10,13,0.06)';
    ctx.fillRect(0, 0, width, height);
    ctx.fillStyle = `rgba(${rgb[0]}, ${rgb[1]}, ${rgb[2]}, ${(0.35 * opacity).toFixed(3)})`;
    for (let i = 0; i < N; i++) {
      const p = particles[i];
      const [vx, vy] = field(p.x, p.y);
      p.x += vx * speed * dt * 0.06;
      p.y += vy * speed * dt * 0.06;
      p.age += dt;
      if (p.x < -20 || p.x > width + 20 || p.y < -20 || p.y > height + 20 || p.age > p.life) spawn(p);
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
      ctx.fill();
    }
    if (running) raf = requestAnimationFrame(frame);
  }

  function start() {
    running = true;
    last = performance.now();
    raf = requestAnimationFrame(frame);
  }
  function stop() {
    running = false;
    cancelAnimationFrame(raf);
  }

  setup();
  start();

  let resizeT = 0;
  window.addEventListener('resize', () => {
    clearTimeout(resizeT);
    resizeT = setTimeout(() => { stop(); setup(); start(); }, 150);
  });
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) stop();
    else if (!running) start();
  });
})();
