/* FROZEN SOURCE CORE — NS26 similarity scaffold (DERIVED).

   Selected similarity-scale relations from the 2026 forced Navier-Stokes blow-up
   construction: radial tau^(1/2), axial tau^(1/2-h), velocity tau^(-1/2-h), h=0.006.
   This is NOT the full proof object. The scaffold math below is immutable: the
   dashboard observer (ns26.js) may choose camera/tone/sampling/playback controls
   declared in specs/NS26.json, but it must not alter these relations. Any change
   to this file changes the source-bundle hash and must ship as a new source id.

   Source bytes: app/static/data/ns26/base.f32.bin (frozen particle scaffold) and
   app/static/data/ns26/schedule.json (frozen tau/rs/zs/vel schedule).
   Generator: tools/generate_trajectories.py::generate_ns26 (byte-reproducible).
*/

export const NS26_H = 0.006;
export const NS26_TAU = Math.PI * 2;

/* Pure frozen mechanism: scaffold-space point from base coords + schedule entry.
   u in [0,1), eta in [-1,1], X streamwise coordinate; S = {tau, rs, zs, vel};
   phase = frozen frame phase + observation-time drift (passed in);
   extraPhase = observation azimuthal wind (passed in, e.g. swirl control).
   Returns [x, y, z, q] with q = |pulse|, the native rendered scalar. */
export function scaffoldPoint(u, eta, X, S, phase, extraPhase) {
  const r = Math.sqrt(2 * S.tau * X) * S.rs * 7;
  const pulse = Math.sin(eta * 11 + X * 8 - phase);
  const a = NS26_TAU * u * 31 + extraPhase + 0.5 * pulse;
  const x = r * Math.cos(a);
  const y = S.zs * eta * 8 + 0.16 * pulse;
  const z = r * Math.sin(a);
  return [x, y, z, Math.abs(pulse)];
}

/* Frozen variant framing (camera only, not genome): pulse-view is a fixed
   close-up on the pulse ridge; similarity-core shows the full scaffold. */
export const NS26_FRAMING = {
  'similarity-core': { zoom: 1.0, yOff: 0.0 },
  'pulse-view': { zoom: 2.3, yOff: -0.35 },
};
