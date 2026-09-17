#!/usr/bin/env node
/**
 * reproduce_seed.cjs — Exact p5.js seed reproduction harness using Playwright.
 *
 * Runs a p5.js sketch in a real Chromium browser with pinned p5 version,
 * captures a screenshot at a fixed frame, and returns the render hash.
 *
 * Usage:
 *   node tools/reproduce_seed.cjs <code_file> [--frame 30] [--width 400] [--height 400] [--out screenshot.png] [--timeout 15000]
 *
 * Key: sketch code runs BEFORE p5 initializes so global setup/draw are registered.
 */
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const args = process.argv.slice(2);
function flag(name, def) { const i = args.indexOf('--' + name); return i >= 0 ? args[i + 1] : def; }

const codeFile = args.find(a => !a.startsWith('--'));
const targetFrame = parseInt(flag('frame', '30'));
const W = parseInt(flag('width', '400'));
const H = parseInt(flag('height', '400'));
const outPath = flag('out', null);
const timeout = parseInt(flag('timeout', '15000'));

if (!codeFile) {
  console.error('usage: reproduce_seed.cjs <code.js> [--frame N] [--width N] [--height N] [--out file.png]');
  process.exit(1);
}

const code = fs.readFileSync(codeFile, 'utf-8');
const codeHash = crypto.createHash('sha256').update(code).digest('hex');

const p5Path = path.resolve(__dirname, '..', 'external', 'p5.js', 'p5.min.js');
if (!fs.existsSync(p5Path)) {
  console.error(JSON.stringify({ ok: false, error: 'p5.js not found', path: p5Path }));
  process.exit(1);
}
const p5Code = fs.readFileSync(p5Path, 'utf-8');

function buildHTML(sketchCode, p5Src, w, h, targetF) {
  return `<!DOCTYPE html><html><head><meta charset='utf-8'></head><body>
<script>
window.setup = undefined;
window.draw = undefined;

${sketchCode}

const _userDraw = window.draw;
const _userSetup = window.setup;
window.draw = function() {
  try { if (_userDraw) _userDraw(); } catch(e) { window.__drawError = e.message; }
  window.__frameCount = (window.__frameCount || 0) + 1;
  if (window.__frameCount >= ${targetF}) window.__done = true;
};
window.setup = function() {
  try {
    if (_userSetup && _userSetup !== undefined) _userSetup();
    else createCanvas(${w}, ${h});
  } catch(e) { window.__setupError = e.message; }
};
</script>
<script>${p5Src}</script>
</body></html>`;
}

async function main() {
  let chromium;
  try {
    ({ chromium } = require('playwright'));
  } catch(e) {
    console.error(JSON.stringify({ ok: false, error: 'playwright not installed', code_hash: codeHash }));
    process.exit(1);
  }

  const html = buildHTML(code, p5Code, W, H, targetFrame);
  const tmpHtml = path.join('/tmp', `repro_${codeHash.slice(0, 12)}.html`);
  fs.writeFileSync(tmpHtml, html);

  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: W, height: H } });

  const errors = [];
  page.on('pageerror', e => errors.push(e.message));

  const startTime = Date.now();
  await page.goto(`file://${tmpHtml}`, { waitUntil: 'load' });

  // Wait for target frame or timeout
  for (let i = 0; i < Math.ceil(timeout / 100); i++) {
    const done = await page.evaluate(() => window.__done);
    if (done) break;
    await page.waitForTimeout(100);
  }

  const result = await page.evaluate(() => ({
    frame: window.__frameCount || 0,
    done: window.__done || false,
    drawError: window.__drawError || null,
    setupError: window.__setupError || null,
    canvasW: document.querySelector('canvas')?.width || 0,
    canvasH: document.querySelector('canvas')?.height || 0,
  }));

  await page.waitForTimeout(100);
  const screenshot = await page.screenshot({ type: 'png' });
  await browser.close();

  const renderHash = crypto.createHash('sha256').update(screenshot).digest('hex');
  const output = {
    code_file: path.resolve(codeFile),
    code_hash: codeHash,
    frame_captured: result.frame,
    frame_target: targetFrame,
    canvas_width: result.canvasW || W,
    canvas_height: result.canvasH || H,
    render_hash: renderHash,
    execution_time_ms: Date.now() - startTime,
    ok: !result.drawError && !result.setupError && result.frame >= targetFrame,
    error: result.drawError || result.setupError || null,
    console_errors: errors.slice(0, 5),
    p5_version: '1.11.3',
    browser: 'chromium-headless',
  };

  if (outPath) {
    fs.writeFileSync(outPath, screenshot);
    output.screenshot = outPath;
  }

  console.log(JSON.stringify(output, null, 2));
  try { fs.unlinkSync(tmpHtml); } catch(e) {}
  process.exit(output.ok ? 0 : 1);
}

main().catch(e => {
  console.error(JSON.stringify({ ok: false, error: e.message }));
  process.exit(1);
});
