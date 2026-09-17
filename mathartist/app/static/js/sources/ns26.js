/* NS26 observer — renders the FROZEN similarity scaffold (see ns26_core.js).
   Velocity-aligned streak renderer with glow. Source bytes are immutable;
   all controls are observation-only. */
import { loadBinary, loadJSON, frameIndex } from '../core/trajectory.js';
import { scaffoldPoint, NS26_FRAMING, NS26_TAU } from './ns26_core.js';

let base = null, sched = null, ready = false;

export async function initNS() {
  if (ready) return;
  [sched, base] = await Promise.all([
    loadJSON('./data/ns26/schedule.json'),
    loadBinary('./data/ns26/base.f32.bin', Float32Array),
  ]);
  ready = true;
}

function project(x, y, z, cy, sy, cp, sp, zoom, W, H) {
  const x1 = x * cy - z * sy, z1 = x * sy + z * cy;
  const y1 = y * cp - z1 * sp, z2 = y * sp + z1 * cp;
  const per = 1 / (1 + Math.max(-0.7, z2 * 0.13));
  return [W / 2 + x1 * W * 0.15 * zoom * per, H / 2 + y1 * H * 0.15 * zoom * per, z2, per];
}

export function renderNS(canvas, p, t) {
  if (!ready) return;
  const c = canvas.getContext('2d'), W = canvas.width, H = canvas.height, g = p.genome;
  c.fillStyle = `rgba(2,3,3,${Math.max(0.035, 1 - g.trail)})`;
  c.fillRect(0, 0, W, H);
  c.globalCompositeOperation = 'lighter';
  const F = NS26_FRAMING[p.source_variant] || NS26_FRAMING['similarity-core'];
  const frames = sched.frames, fps = sched.fps || 8;
  const fi = frameIndex(t, g.time_rate, frames, fps);
  const fi2 = (fi + 1) % frames;
  const tt = t * (g.time_rate || 0.8);
  const S  = { tau: sched.tau[fi],  rs: sched.rs[fi],  zs: sched.zs[fi],  vel: sched.vel[fi] };
  const S2 = { tau: sched.tau[fi2], rs: sched.rs[fi2], zs: sched.zs[fi2], vel: sched.vel[fi2] };
  const framePhase  = (NS26_TAU * fi) / frames;
  const framePhase2 = (NS26_TAU * fi2) / frames;
  const phase  = framePhase  + tt * S.vel  * 0.025;
  const phase2 = framePhase2 + tt * S2.vel * 0.025;
  const extra  = (g.swirl || 0) * S.vel  * 0.015 * tt;
  const extra2 = (g.swirl || 0) * S2.vel * 0.015 * tt;
  const yaw = (g.rotation || 0) + 0.04 * tt;
  const cy = Math.cos(yaw), sy = Math.sin(yaw);
  const pitch = 0.55 * (g.pitch || 0), cp = Math.cos(pitch), sp = Math.sin(pitch);
  const N = base.length / 3;
  const Ndraw = Math.max(64, Math.min(N, Math.floor(N * (g.sample || 0.85))));
  const zoom = (g.zoom || 1) * F.zoom;
  const threshold = g.threshold || 0;
  const gamma = g.gamma || 0.8;
  const exposure = g.exposure || 1;
  const psize = g.point_size || 0.8;

  /* Collect visible particles with velocity streak endpoints */
  const visible = [];
  for (let i = 0; i < Ndraw; i++) {
    const u = base[3 * i], eta = base[3 * i + 1], X = base[3 * i + 2];
    const pt  = scaffoldPoint(u, eta, X, S,  phase,  extra);
    const pt2 = scaffoldPoint(u, eta, X, S2, phase2, extra2);
    const q = pt[3];
    if (q < threshold) continue;
    const [xx, yy, z2, per] = project(pt[0], pt[1] + F.yOff, pt[2], cy, sy, cp, sp, zoom, W, H);
    const [xx2, yy2] = project(pt2[0], pt2[1] + F.yOff, pt2[2], cy, sy, cp, sp, zoom, W, H);
    if (xx < -30 || xx > W + 30 || yy < -30 || yy > H + 30) continue;
    visible.push({ xx, yy, xx2, yy2, z2, q, eta });
  }
  visible.sort((a, b) => a.z2 - b.z2);

  /* Render streaks + glow */
  for (const v of visible) {
    const depthFade = 0.3 + 0.7 * (1 / (1 + Math.max(-0.5, v.z2 * 0.08)));
    const qg = Math.pow(Math.max(0, Math.min(1, v.q)), gamma);
    const alpha = (0.08 + 0.55 * qg * exposure * depthFade);
    const lum = Math.floor((65 + 190 * qg) * depthFade);
    const warm = v.z2 < 0 ? Math.min(1, -v.z2 * 0.12) : 0;
    const r = Math.min(255, lum + Math.floor(warm * 50));
    const gr = Math.min(255, lum + Math.floor(warm * 20));
    const b = Math.min(255, lum + Math.floor((1 - warm) * 30));
    const s = psize * (0.6 + qg * 1.0) * depthFade;
    /* velocity streak: line from current to next position */
    const dx = v.xx2 - v.xx, dy = v.yy2 - v.yy;
    const len = Math.sqrt(dx * dx + dy * dy);
    const streakLen = Math.min(8, Math.max(1, len * 2)) * psize * depthFade;
    const nx = len > 0.01 ? dx / len : 0, ny = len > 0.01 ? dy / len : 0;
    c.strokeStyle = `rgba(${r},${gr},${b},${alpha * 0.7})`;
    c.lineWidth = s * 0.7;
    c.beginPath();
    c.moveTo(v.xx - nx * streakLen * 0.4, v.yy - ny * streakLen * 0.4);
    c.lineTo(v.xx + nx * streakLen * 0.6, v.yy + ny * streakLen * 0.6);
    c.stroke();
    /* core dot */
    c.fillStyle = `rgba(${r},${gr},${b},${alpha})`;
    c.fillRect(v.xx - s * 0.5, v.yy - s * 0.5, s, s);
    /* outer glow for bright particles */
    if (qg > 0.5 && s > 0.8) {
      const gs = s * 3;
      c.fillStyle = `rgba(${r},${gr},${b},${alpha * 0.12})`;
      c.fillRect(v.xx - gs * 0.5, v.yy - gs * 0.5, gs, gs);
    }
  }
  c.globalCompositeOperation = 'source-over';
}
