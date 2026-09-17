#!/usr/bin/env node
const fs=require("fs"),path=require("path"),crypto=require("crypto");
const {chromium}=require("playwright");

const argv=process.argv.slice(2);
function flag(name,def){const i=argv.indexOf(`--${name}`);return i>=0?argv[i+1]:def}
const jobsFile=argv.find(x=>!x.startsWith("--"));
if(!jobsFile){console.error("usage: node render_batch.cjs jobs.jsonl --out runs/images --workers 2");process.exit(2)}
const outDir=path.resolve(flag("out","runs/images"));
const workers=Math.max(1,parseInt(flag("workers","2"),10));
const timeoutMs=parseInt(flag("timeout","15000"),10);
fs.mkdirSync(outDir,{recursive:true});
const p5Path=path.resolve(__dirname,"..","external","p5.js","p5.min.js");
const p5Code=fs.readFileSync(p5Path,"utf8");
const jobs=fs.readFileSync(jobsFile,"utf8").split(/\r?\n/).filter(Boolean).map(JSON.parse);

function htmlFor(job,code){
  const W=job.width||400,H=job.height||400,target=job.frame||20;
  const search=(job.mode||"search")==="search";
  const rseed=Number.isFinite(job.random_seed)?job.random_seed:0;
  const nseed=Number.isFinite(job.noise_seed)?job.noise_seed:rseed;
  const seedLine=search?`randomSeed(${rseed});noiseSeed(${nseed});`:"";
  return `<!doctype html><html><head><meta charset="utf-8">
<style>html,body{margin:0;background:#000;overflow:hidden}canvas{display:block}</style></head><body>
<script>${p5Code}</script>
<script>${seedLine}</script>
<script>
window.__ma_done=false;window.__ma_frames=0;window.__ma_error=null;
${code}
const __ma_user_setup=window.setup;
const __ma_user_draw=window.draw;
window.setup=function(){
  try{
    if(__ma_user_setup)__ma_user_setup();else createCanvas(${W},${H});
  }catch(e){window.__ma_error="setup: "+e.message;window.__ma_done=true;}
};
window.draw=function(){
  try{if(__ma_user_draw)__ma_user_draw();}
  catch(e){window.__ma_error="draw: "+e.message;window.__ma_done=true;return;}
  window.__ma_frames++;
  if(window.__ma_frames>=${target})window.__ma_done=true;
};
</script></body></html>`;
}

async function renderJob(browser,job){
  const t0=Date.now();
  const code=typeof job.code==="string"?job.code:fs.readFileSync(job.code_file,"utf8");
  const sourceHash=crypto.createHash("sha256").update(code).digest("hex");
  const page=await browser.newPage({viewport:{width:job.width||400,height:job.height||400}});
  const pageErrors=[];page.on("pageerror",e=>pageErrors.push(e.message));
  try{
    if((job.mode||"search")==="search")await page.clock.install({time:new Date("2020-01-01T00:00:00Z")});
    await page.setContent(htmlFor(job,code),{waitUntil:"load",timeout:timeoutMs});
    if((job.mode||"search")==="search"){
      for(let i=0;i<120;i++){
        if(await page.evaluate(()=>!!window.__ma_done))break;
        await page.clock.runFor(250);
      }
    }else{
      await page.waitForFunction(()=>window.__ma_done,null,{timeout:timeoutMs}).catch(()=>{});
    }
    const state=await page.evaluate(()=>({
      done:!!window.__ma_done,frames:window.__ma_frames||0,error:window.__ma_error||null,
      canvasCount:document.querySelectorAll("canvas").length
    }));
    if(!state.canvasCount)return{id:job.id,ok:false,technical_status:"blank",source_sha256:sourceHash,error:state.error||"no canvas",execution_ms:Date.now()-t0};
    const canvas=page.locator("canvas").first();
    const imagePath=path.join(outDir,`${job.id}.jpg`);
    const image=await canvas.screenshot({type:"jpeg",quality:86,path:imagePath});
    return{id:job.id,ok:!state.error&&state.frames>=(job.frame||20),technical_status:state.error?"crash":"valid",
      source_sha256:sourceHash,render_sha256:crypto.createHash("sha256").update(image).digest("hex"),
      image_path:imagePath,frames:state.frames,error:state.error,page_errors:pageErrors.slice(0,5),
      execution_ms:Date.now()-t0,renderer_mode:job.mode||"search",
      random_seed:job.random_seed??null,noise_seed:job.noise_seed??null};
  }catch(e){
    return{id:job.id,ok:false,technical_status:/Timeout/i.test(e.message)?"timeout":"crash",
      source_sha256:sourceHash,error:e.message,execution_ms:Date.now()-t0};
  }finally{await page.close().catch(()=>{})}
}

(async()=>{
  const browser=await chromium.launch({headless:true});
  let next=0;
  async function worker(){
    while(true){
      const idx=next++;if(idx>=jobs.length)break;
      const out=await renderJob(browser,jobs[idx]);process.stdout.write(JSON.stringify(out)+"\n");
    }
  }
  await Promise.all(Array.from({length:workers},worker));
  await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});
