/* Generic immutable array-sequence renderer.
   Used for exported simulation/experimental fields (bioelectricity, PDE states, etc.).
   Source bytes are never mutated; genomes alter observation only. */
const cache=new Map();
function start(id){
  if(cache.has(id))return;
  const state={ready:false,data:null,meta:null,error:null};cache.set(id,state);
  fetch(`./data/imported/${encodeURIComponent(id)}.json`).then(r=>{if(!r.ok)throw new Error(`array sequence ${id}: ${r.status}`);return r.json()}).then(meta=>{
    const raw=atob(meta.data_b64);const u=new Uint8Array(raw.length);for(let i=0;i<raw.length;i++)u[i]=raw.charCodeAt(i);
    state.meta=meta;state.data=u;state.ready=true;
  }).catch(e=>state.error=String(e));
}
function valueAt(st,frame,y,x,ch=0){
  const m=st.meta,C=m.channels||1,H=m.height,W=m.width;
  return st.data[((frame*H+y)*W+x)*C+Math.min(C-1,ch)]/255;
}
export function renderArraySeq(canvas,p,t){
  start(p.source_id);const st=cache.get(p.source_id),c=canvas.getContext('2d'),Wc=canvas.width,Hc=canvas.height,g=p.genome;
  c.fillStyle=`rgba(2,3,3,${Math.max(.04,1-(g.trail??0))})`;c.fillRect(0,0,Wc,Hc);
  if(!st?.ready){c.fillStyle='#343837';c.font='8px monospace';c.fillText(st?.error?'SOURCE ERROR':'LOADING SOURCE',8,14);return}
  const m=st.meta,H=m.height,W=m.width,F=m.frames,C=m.channels||1;
  const frame=Math.floor((t*(g.time_rate??1)*(m.fps||10)))%F,ch=Math.round(g.channel??0)%C;
  let mass=0,cx=0,cy=0;for(let y=0;y<H;y++)for(let x=0;x<W;x++){const v=valueAt(st,frame,y,x,ch);mass+=v;cx+=x*v;cy+=y*v}cx=mass?cx/mass:(W-1)/2;cy=mass?cy/mass:(H-1)/2;
  const rot=g.rotation??0,co=Math.cos(rot),si=Math.sin(rot),zoom=g.zoom??1,scale=Math.min(Wc/W,Hc/H)*zoom,sample=Math.max(.15,g.sample??1),step=Math.max(1,Math.round(1/sample));
  c.globalCompositeOperation='lighter';
  for(let y=0;y<H;y+=step)for(let x=0;x<W;x+=step){
    let v=valueAt(st,frame,y,x,ch),q=v,obs=g.observable||'field';
    if(obs==='edge'){const vr=valueAt(st,frame,y,(x+1)%W,ch),vd=valueAt(st,frame,(y+1)%H,x,ch);q=Math.min(1,Math.hypot(vr-v,vd-v)*(g.contours??5))}
    else if(obs==='contour'){if(v<.002)continue;q=.5+.5*Math.cos((v*(g.contours??5))*Math.PI*2)}
    if(q<(g.threshold??0))continue;
    const dx=x-cx,dy=y-cy,xx=(dx*co-dy*si)*scale+Wc/2,yy=(dx*si+dy*co)*scale+Hc/2;
    q=Math.pow(Math.max(0,Math.min(1,q)),g.gamma??1);const lum=Math.floor(90+165*q),a=(.025+.22*q)*(g.exposure??.8),sz=Math.max(.65,(g.point_size??1)*(.45+q));
    c.fillStyle=`rgba(${lum},${lum},${lum},${a})`;c.fillRect(xx,yy,sz,sz);
  }
  c.globalCompositeOperation='source-over';
}
