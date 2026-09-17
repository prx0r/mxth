/* MathArtist V3.1 compact mathematical maps.
   These are parameterized mathematical programs distilled from compact Processing
   sketches supplied by the user in the 2026-09-17 design session. The observer is
   intentionally dumb: evaluate points, robustly auto-fit, plot white points on black. */

const TAU=Math.PI*2;
const clamp=(x,a,b)=>Math.max(a,Math.min(b,x));

function robustFit(points,W,H){
  if(!points.length)return {cx:0,cy:0,s:1};
  // Robust extent: histogram-free quantile estimate via sorted coordinates. This is an
  // observation normalization only; it never feeds back into the mathematical program.
  const xs=points.map(p=>p[0]).filter(Number.isFinite).sort((a,b)=>a-b);
  const ys=points.map(p=>p[1]).filter(Number.isFinite).sort((a,b)=>a-b);
  if(xs.length<8)return {cx:0,cy:0,s:1};
  const q=(a,f)=>a[Math.max(0,Math.min(a.length-1,Math.floor((a.length-1)*f)))];
  const x0=q(xs,.01),x1=q(xs,.99),y0=q(ys,.01),y1=q(ys,.99);
  const cx=(x0+x1)/2,cy=(y0+y1)/2,ex=Math.max(1e-9,x1-x0),ey=Math.max(1e-9,y1-y0);
  return {cx,cy,s:.86*Math.min(W/ex,H/ey)};
}

function drawPoints(canvas,points){
  const c=canvas.getContext('2d'),W=canvas.width,H=canvas.height;
  c.globalCompositeOperation='source-over';c.fillStyle='#030303';c.fillRect(0,0,W,H);
  const f=robustFit(points,W,H);c.fillStyle='rgba(240,240,240,.34)';
  for(const p of points){
    const x=(p[0]-f.cx)*f.s+W/2,y=(p[1]-f.cy)*f.s+H/2;
    if(x>=1&&x<W-1&&y>=1&&y<H-1)c.fillRect(x,y,1,1);
  }
}

function radialWarp(g,t){
  const P=[],N=10000,tt=t*(g.time_rate??.45);
  for(let i=N;i--;){
    const y=i/(g.i_div??100);
    const k=(g.k_base??8)+Math.sin(i/(g.k_freq??19)+tt)*Math.cos(i/(g.k_freq2??49));
    const e=y/(g.e_div??8)-(g.e_bias??12);
    const mag=Math.hypot(k,e);
    const d=Math.pow(mag,g.d_power??2)/(g.d_div??79)+(g.d_bias??1);
    const phase=d*d-tt+Math.cos(tt/(g.phase_slow??3))+(g.e_phase??.3)*Math.sin(e);
    const q=k/d*(g.k_over_d??4)-e*Math.sin(k)+k/(d*d)*((g.inner_bias??12)+d*(g.inner_scale??6)*Math.sin(phase));
    const x=q+(g.x_offset??0);
    const yy=(g.y_wave??12)*Math.sin(d*(g.y_freq??2.6)-tt)+d*(g.y_scale??66)+(g.e_y??0)*e;
    if(Number.isFinite(x)&&Number.isFinite(yy))P.push([x,yy]);
  }
  return P;
}


function polarWarp(g,t){
  const P=[],N=12000,tt=t*(g.time_rate??.5),parity=Math.max(1,Math.round(g.parity??2));
  for(let i=N;i--;){
    const y=i/(g.i_div??110);
    const k=(g.k_amp??8)*Math.cos(y<(g.switch_y??59)?i%(g.k_mod??9):i*(g.k_mult??4));
    const e=y/(g.e_div??6)-(g.e_bias??16);
    const d=Math.pow(Math.hypot(k,e),g.d_power??2)/(g.d_div??79)+(g.d_bias??1.1);
    if(Math.abs(d)<1e-6)continue;
    const q=k/d*(g.k_over_d??3)-e*Math.sin(k)+k/(d*d)*((g.inner_bias??9)-d*(g.inner_scale??4)*Math.sin(d*d-tt+Math.sin(e)*(g.e_phase??.5)))+(g.q_bias??70);
    const c=d/(g.c_div??2)-tt/(g.t_div??12)+(i%parity)*(g.parity_phase??4);
    const x=q*Math.sin(c);
    const yy=q*Math.cos(c)+e*(g.e_y??1);
    if(Number.isFinite(x)&&Number.isFinite(yy)&&Math.abs(x)<1e6&&Math.abs(yy)<1e6)P.push([x,yy]);
  }
  return P;
}

function latentNineteen(g,t){
  const P=[],N=10000,tt=t*(g.time_rate??.62),mMax=Math.max(2,Math.round(g.m_mod??19));
  for(let i=N;i--;){
    const m=i%mMax;
    const k=(g.k_amp??9)*Math.cos(i*(g.k_f1??5))*Math.sin(i*(g.k_f2??1));
    const e=(g.e_amp??9)*Math.cos(i*(g.e_f1??7))*Math.cos(i*(g.e_f2??1));
    if(e<=g.e_gate)continue;
    const mag=Math.hypot(k,e);
    const d=Math.pow(mag,g.d_power??3)/(g.d_div??999)+(g.d_bias??4.6)-Math.pow(Math.cos(tt/(g.slow??4)+m),3)*(g.phase_depth??.333);
    if(Math.abs(d)<1e-6)continue;
    const o=Math.sin(d*d-tt+m);
    const c=d/(g.c_div??8)-tt/(g.t_div??32)+m;
    const x=(g.radius??99)*Math.sin(c)+k/(g.k_div??3)*Math.exp(clamp(o,-1,1));
    const y=(g.radius??99)*Math.cos(c/(g.c_y_div??3))+d*(g.d_y??39)+Math.pow(Math.max(.001,e),clamp(o,-.8,.8));
    if(Number.isFinite(x)&&Number.isFinite(y)&&Math.abs(x)<1e6&&Math.abs(y)<1e6)P.push([x,y]);
  }
  return P;
}

function torusLattice(g,t){
  const P=[],ny=Math.round(g.rows??40),nx=Math.round(g.cols??80),tt=t*(g.time_rate??.22);
  const ax=.5,ay=-.5,ca=Math.cos(ax),sa=Math.sin(ax),cb=Math.cos(ay),sb=Math.sin(ay);
  for(let y=0;y<ny;y++)for(let x=0;x<nx;x++){
    const v=(y+tt)*(Math.PI/(g.p_div??40))*2*(g.v_freq??1);
    const u=(x+tt)*(Math.PI/(g.p_div??40))*(g.u_freq??1);
    const R=(g.major??2)+(g.minor??1)*Math.sin(v);
    let X=R*Math.cos(u),Y=R*Math.sin(u),Z=(g.z_amp??1)*Math.cos(v);
    // Fixed camera, not an evolvable parameter.
    let y1=Y*ca-Z*sa,z1=Y*sa+Z*ca,x1=X;
    let x2=x1*cb-z1*sb,z2=x1*sb+z1*cb;
    const per=1/(1+.12*(z2+3));
    P.push([x2*per,y1*per]);
  }
  return P;
}

export function renderTinyMaps(canvas,p,t){
  const g=p.genome||{};let pts=[];
  if(p.source_variant==='radial-warp')pts=radialWarp(g,t);
  else if(p.source_variant==='polar-warp')pts=polarWarp(g,t);
  else if(p.source_variant==='latent-19')pts=latentNineteen(g,t);
  else pts=torusLattice(g,t);
  drawPoints(canvas,pts);
}
