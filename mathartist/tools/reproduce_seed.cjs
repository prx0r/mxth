#!/usr/bin/env node
/**
 * reproduce_seed.cjs — Exact p5.js reproduction via Playwright (real browser).
 * Sketch code runs BEFORE p5 init so global setup/draw register properly.
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
const timeoutMs = parseInt(flag('timeout', '15000'));

if (!codeFile) { console.error('usage: reproduce_seed.cjs <code.js> [--frame N]'); process.exit(1); }
const code = fs.readFileSync(codeFile, 'utf-8');
const codeHash = crypto.createHash('sha256').update(code).digest('hex');
const p5Path = path.resolve(__dirname, '..', 'external', 'p5.js', 'p5.min.js');
if (!fs.existsSync(p5Path)) { console.error(JSON.stringify({ok:false,error:'p5.js not found'})); process.exit(1); }
const p5Code = fs.readFileSync(p5Path, 'utf-8');

const html = `<!DOCTYPE html><html><head><meta charset='utf-8'></head><body>
<script>
window.setup=undefined;window.draw=undefined;
${code}
const _ud=window.draw,_us=window.setup;
window.draw=function(){try{if(_ud)_ud();}catch(e){window.__drawErr=e.message;}
  window.__fc=(window.__fc||0)+1;if(window.__fc>=${targetFrame})window.__done=true;};
window.setup=function(){try{if(_us&&_us!==window.setup)_us();else createCanvas(${W},${H});}
  catch(e){window.__setupErr=e.message;}};
</script>
<script>${p5Code}</script></body></html>`;

(async()=>{
  const{chromium}=require('playwright');
  const browser=await chromium.launch({headless:true});
  const page=await browser.newPage({viewport:{width:W,height:H}});
  const errs=[];
  page.on('pageerror',e=>errs.push(e.message));
  const t0=Date.now();
  const tmpH=path.join('/tmp',`repro_${codeHash.slice(0,12)}.html`);
  fs.writeFileSync(tmpH,html);
  await page.goto(`file://${tmpH}`,{waitUntil:'load'});
  for(let i=0;i<Math.ceil(timeoutMs/100);i++){
    if(await page.evaluate(()=>window.__done))break;
    await page.waitForTimeout(100);
  }
  const r=await page.evaluate(()=>({fc:window.__fc||0,done:window.__done||false,
    drawErr:window.__drawErr||null,setupErr:window.__setupErr||null,
    cW:document.querySelector('canvas')?.width||0,cH:document.querySelector('canvas')?.height||0}));
  await page.waitForTimeout(100);
  const ss=await page.screenshot({type:'png'});
  await browser.close();
  const rh=crypto.createHash('sha256').update(ss).digest('hex');
  const out={code_file:path.resolve(codeFile),code_hash:codeHash,frame_captured:r.fc,
    frame_target:targetFrame,canvas_width:r.cW||W,canvas_height:r.cH||H,render_hash:rh,
    ok:!r.drawErr&&!r.setupErr&&r.fc>=targetFrame,error:r.drawErr||r.setupErr||null,
    console_errors:errs.slice(0,5),p5_version:'1.11.3',browser:'chromium-headless',
    execution_ms:Date.now()-t0};
  if(outPath){fs.writeFileSync(outPath,ss);out.screenshot=outPath;}
  console.log(JSON.stringify(out,null,2));
  try{fs.unlinkSync(tmpH)}catch(e){}
  process.exit(out.ok?0:1);
})().catch(e=>{console.error(JSON.stringify({ok:false,error:e.message}));process.exit(1)});
