#!/usr/bin/env node
const fs=require('fs'),path=require('path'),{pathToFileURL}=require('url');
let Canvas;
try{({Canvas}=require('skia-canvas'))}catch(e){console.error('Missing skia-canvas. Install with: npm install skia-canvas');process.exit(2)}
const [,,rootArg,phenotypeFile,outDir,wArg='512',fpsArg='10',framesArg='300']=process.argv;
if(!rootArg||!phenotypeFile||!outDir){console.error('usage: render_frames.cjs ROOT phenotype.json OUTDIR [width] [fps] [frames]');process.exit(2)}
const ROOT=path.resolve(rootArg),STATIC=path.join(ROOT,'app','static');
function resolveAsset(u){
  let s=String(u); if(s.startsWith('http:')||s.startsWith('https:'))return null;
  s=s.replace(/^file:\/\//,'');
  if(path.isAbsolute(s)&&fs.existsSync(s))return s;
  s=s.replace(/^\.\//,'').replace(/^\//,'');
  return path.join(STATIC,s);
}
global.fetch=async function(u){
  const p=resolveAsset(u);if(!p||!fs.existsSync(p))return{ok:false,status:404,json:async()=>{throw new Error('404 '+u)},arrayBuffer:async()=>{throw new Error('404 '+u)}};
  const b=fs.readFileSync(p);
  return {ok:true,status:200,json:async()=>JSON.parse(b.toString('utf8')),arrayBuffer:async()=>b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength),text:async()=>b.toString('utf8')};
};
(async()=>{
  const mod=await import(pathToFileURL(path.join(STATIC,'js','sources','index.js')).href);
  await mod.initSources();
  const ph=JSON.parse(fs.readFileSync(phenotypeFile,'utf8'));
  const W=+wArg,H=W,fps=+fpsArg,frames=+framesArg;fs.mkdirSync(outDir,{recursive:true});
  const canvas=new Canvas(W,H);
  for(let i=0;i<frames;i++){
    mod.render(canvas,ph,i/fps);
    const buf=await canvas.toBuffer('png');
    fs.writeFileSync(path.join(outDir,`frame-${String(i).padStart(5,'0')}.png`),buf);
  }
  console.log(JSON.stringify({ok:true,frames,width:W,fps,source:ph.source_id,id:ph.id}));
})().catch(e=>{console.error(e.stack||String(e));process.exit(1)});
