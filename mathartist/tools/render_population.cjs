#!/usr/bin/env node
/* Deterministic batch renderer for aesthetic audits. Uses the exact browser source renderers.
   With --accumulate N, renders N sub-frames onto one canvas to simulate trail compositing. */
const fs=require('fs'),path=require('path'),{pathToFileURL}=require('url');
let Canvas;try{({Canvas}=require('skia-canvas'))}catch(e){console.error('Missing skia-canvas');process.exit(2)}
const args=process.argv.slice(2);
function flag(name,def){const i=args.indexOf('--'+name);return i>=0?args[i+1]:def}
const rootArg=args.find(a=>!a.startsWith('--')),popFile=args.find((a,i)=>i>0&&!a.startsWith('--')&&args[i-1]===rootArg)||args[1],outDir=args.find((a,i)=>i>0&&!a.startsWith('--')&&args[i-2]===rootArg)||args[2];
const wArg=flag('width','192'),timesArg=flag('times','3,9,17,25'),accStr=flag('accumulate','0');
if(!rootArg||!popFile||!outDir){console.error('usage: render_population.cjs ROOT POP OUTDIR [--width N] [--times 3,9] [--accumulate N]');process.exit(2)}
const ROOT=path.resolve(rootArg),STATIC=path.join(ROOT,'app','static'),W=+wArg,H=W,times=timesArg.split(',').map(Number),accFrames=+accStr;
function resolveAsset(u){let s=String(u);if(/^https?:/.test(s))return null;s=s.replace(/^file:\/\//,'');if(path.isAbsolute(s)&&fs.existsSync(s))return s;s=s.replace(/^\.\//,'').replace(/^\//,'');return path.join(STATIC,s)}
global.fetch=async function(u){const p=resolveAsset(u);if(!p||!fs.existsSync(p))return{ok:false,status:404,json:async()=>{throw Error('404 '+u)},arrayBuffer:async()=>{throw Error('404 '+u)}};const b=fs.readFileSync(p);return{ok:true,status:200,json:async()=>JSON.parse(b.toString('utf8')),arrayBuffer:async()=>b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength),text:async()=>b.toString('utf8')}};
(async()=>{const mod=await import(pathToFileURL(path.join(STATIC,'js','sources','index.js')).href);await mod.initSources();const pop=JSON.parse(fs.readFileSync(popFile,'utf8'));fs.mkdirSync(outDir,{recursive:true});let n=0;
for(const p of pop){const pd=path.join(outDir,p.id);fs.mkdirSync(pd,{recursive:true});
for(let j=0;j<times.length;j++){const cv=new Canvas(W,H);
if(accFrames>0){for(let k=0;k<accFrames;k++)mod.render(cv,p,times[j]+k*0.12)}
else mod.render(cv,p,times[j]);
fs.writeFileSync(path.join(pd,`t${j}.png`),await cv.toBuffer('png'));n++}}
console.log(JSON.stringify({ok:true,phenotypes:pop.length,frames:n,width:W,times,accumulate:accFrames}));})().catch(e=>{console.error(e.stack||String(e));process.exit(1)});
