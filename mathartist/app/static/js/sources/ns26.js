/* NS26 — Navier-Stokes similarity-scale renderer.

   The similarity relations are immutable:
     radial ~ tau^(1/2)
     axial ~ tau^(1/2-h)
     velocity ~ tau^(-1/2-h)

   The genome controls h, tau, twist, etaFreq (real scientific/observation parameters)
   plus density, trail, exposure (visual). This is the v1 math with proper provenance. */

export function initNS() {}  // no async init needed

export function renderNS(canvas, p, t) {
  const c = canvas.getContext('2d'), W = canvas.width, H = canvas.height, g = p.genome;
  c.fillStyle = `rgba(2,3,3,${Math.max(0.02, 1 - (g.trail || 0.16))})`;
  c.fillRect(0, 0, W, H);
  c.globalCompositeOperation = 'lighter';

  const h = g.h || 0.006;
  const etaFreq = g.etaFreq || 3.0;
  const twist = g.twist || 1.2;
  const density = g.density || 1.0;
  const exposure = g.exposure || 0.62;

  // Core similarity scaling: tau drives everything
  const tau = Math.max(0.0005, (g.tau || 0.12) * (0.72 + 0.28 * Math.sin(t * 0.22 + etaFreq)));
  const rScale = Math.pow(tau, 0.5);
  const zScale = Math.pow(tau, 0.5 - h);
  const vel = Math.pow(tau, -0.5 - h);

  const N = Math.floor(3300 * density);
  for (let i = 0; i < N; i++) {
    const u = i / N;
    const eta = 2 * ((i * 0.61803398875) % 1) - 1;
    const X = 0.05 + 3.4 * ((i * 0.754877666) % 1);

    // Similarity-scale radial distance
    const r = Math.sqrt(2 * tau * X) * rScale * 4.4;

    // Pulse pattern from eta-frequency
    const pulse = Math.sin(etaFreq * eta * Math.PI + X * 5 - t * vel * 0.018);

    // Azimuthal angle with twist
    const theta = Math.PI * 2 * u * 34 + twist * vel * 0.016 * t + 0.55 * pulse;

    // Axial position from similarity scaling
    const z = zScale * eta * 5.2 + 0.12 * Math.sin(X * 9 - t);

    // Project to 2D — v1 used r * W * 0.15 * zoom for projection
    const zoom = g.zoom || 1.0;
    const px = W / 2 + Math.cos(theta) * r * W * 0.15 * zoom;
    const py = H / 2 + z * H * 0.15 * zoom;

    // Point brightness from pulse
    const q = 0.35 + 0.65 * Math.abs(pulse);
    const alpha = (0.02 + 0.18 * q) * exposure;

    c.fillStyle = `rgba(200,210,205,${alpha})`;
    c.fillRect(px, py, 1, 1);
  }
  c.globalCompositeOperation = 'source-over';
}
