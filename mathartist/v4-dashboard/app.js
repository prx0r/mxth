const $=s=>document.querySelector(s),$$=s=>[...document.querySelectorAll(s)];
let gen=0,sigma=.35,current=null,specimens=[],history=[],sessionId=crypto.randomUUID().slice(0,8);
let source='TINYMAPS';
const selected=new Set();
const API='';  // same origin

async function api(path,opts={}){const r=await fetch(API+path,{headers:{'Content-Type':'application/json'},...opts});if(!r.ok)throw new Error(await r.text());return r.json()}
async function getJSON(p){return api(p)}
async function postJSON(p,d){return api(p,{method:'POST',body:JSON.stringify(d)})}

// Session persistence
function sessionId(){let s=localStorage.getItem('ma4.session');if(!s){s=crypto.randomUUID().slice(0,8);localStorage.setItem('ma4.session',s)}return s}

// Favorites
function favorites(){return new Set(JSON.parse(localStorage.getItem('ma4.favorites')||'[]'))}
function saveFavorites(set){localStorage.setItem('ma4.favorites',JSON.stringify([...set]))}

// Load specimens from real API
async function loadPopulation(mode='open',count=24){
  const pop=await getJSON(`/api/population?source=${source}&mode=${mode}&count=${count}&session=${sessionId}`);
  return pop.map(p=>({...p,_rendered:false}));
}

// Branch via real API
async function branch(){
  const parents=specimens.filter(s=>selected.has(s.id));
  if(!parents.length)return;
  history.push({specimens:[...specimens],gen});
  gen++;
  try{
    const out=await postJSON('/api/branch',{
      parent_ids:parents.map(p=>p.id),
      sigma,count:24,
      source_id:source,
      lineage_channel:'HUMAN_OPEN_ENDED',
      session_id:sessionId
    });
    specimens=out.map(p=>({...p,_rendered:false}));
  }catch(e){
    // Fallback: use evolve endpoint
    const out=await postJSON('/api/evolve',{
      source_id:source,mode:'frontier',count:24,
      selected_ids:parents.map(p=>p.id),
      session_id:sessionId
    });
    specimens=out.map(p=>({...p,_rendered:false}));
  }
  selected.clear();mount();toast(`G${gen} · ${parents.length} stepping stone${parents.length>1?'s':''}`);
}

// Fresh roots via real API
async function freshRoots(){
  history.push({specimens:[...specimens],gen});
  gen=0;
  const out=await postJSON('/api/root',{source_id:source,count:24});
  specimens=out.map(p=>({...p,_rendered:false}));
  selected.clear();mount();toast('fresh roots');
}

// Render a phenotype using real MathArtist renderer
function renderPheno(cv,p,t){
  const c=cv.getContext('2d'),W=cv.width,H=cv.height;
  c.fillStyle='#010202';c.fillRect(0,0,W,H);
  // Delegate to real renderer based on source_id
  if(typeof window._renderers!=='undefined'&&window._renderers[p.source_id]){
    window._renderers[p.source_id](cv,p,t);
  }else{
    // Fallback: simple point cloud from genome
    renderFallback(cv,p,t);
  }
}

function renderFallback(cv,p,t){
  const c=cv.getContext('2d'),W=cv.width,H=cv.height,g=p.genome||{};
  c.fillStyle='#010202';c.fillRect(0,0,W,H);
  c.globalCompositeOperation='lighter';
  const keys=Object.keys(g);
  if(!keys.length)return;
  for(let i=0;i<2000;i++){
    const u=i/2000*Math.PI*2,k1=keys[0]?g[keys[0]]:1,k2=keys[1]?g[keys[1]]:1;
    const r=(.1+.3*Math.abs(Math.sin(u*k1+t*.1)))*W*.4;
    const warp=Math.sin(u*k2+t*.05)*.5;
    const px=W/2+Math.cos(u+warp)*r;
    const py=H/2+Math.sin(u*.8+warp)*r;
    c.fillStyle=`rgba(200,210,205,${.03+.12*Math.abs(Math.sin(u+t*.07))})`;
    c.fillRect(px,py,1,1);
  }
  c.globalCompositeOperation='source-over';
}

// Card element
function card(s){
  const el=document.createElement('article');
  el.className='cell';el.dataset.id=s.id;
  const cv=document.createElement('canvas');
  cv.width=cv.height=360;
  renderPheno(cv,s,performance.now()/1000);
  const m=document.createElement('div');
  m.className='meta';
  m.innerHTML=`<span>${s.source_variant||s.source_id} · ${s.id.slice(-6)}</span><span>G${s.generation||0}</span>`;
  el.append(cv,m);
  el.onclick=e=>{if(e.detail>1)return;selected.has(s.id)?selected.delete(s.id):selected.add(s.id);update()};
  el.ondblclick=()=>open(s);
  return el;
}

function mount(){
  const g=$("#grid");g.innerHTML='';
  specimens.forEach(s=>g.append(card(s)));
  $("#gen").textContent=`G${gen}`;
  update();
}

function update(){
  const n=selected.size;
  $("#hint").textContent=n?`${n} stepping stone${n>1?'s':''} marked · choose pressure then branch`:'Choose anything with potential. Beauty is not required.';
  $("#evolve").disabled=!n;
  $("#dock").classList.toggle('hidden',!n);
  $("#count").textContent=n;
  $$(".cell").forEach(e=>e.classList.toggle('selected',selected.has(e.dataset.id)));
}

function open(s){
  current=s;
  $("#detail").classList.remove('hidden');
  $("#title").textContent=s.id;
  $("#eyebrow").textContent=`${s.source_id} · ${(s.source_variant||'').toUpperCase()}`;
  $("#dg").textContent=s.generation||0;
  $("#dp").textContent=s.parent_ids?.length?s.parent_ids[0].slice(-8):'ROOT';
  $("#params").textContent=JSON.stringify(s.genome||s.g,null,2);
  $("#potential").classList.toggle('on',selected.has(s.id));
  renderPheno($("#hero"),s,performance.now()/1000);
}

function toast(t){
  const e=$("#toast");e.textContent=t;e.classList.add('show');
  clearTimeout(toast.t);toast.t=setTimeout(()=>e.classList.remove('show'),1100);
}

// Event recording
async function recordEvent(p,type,value=null,metadata={}){
  try{await postJSON('/api/event',{phenotype_id:p.id,session_id:sessionId,event_type:type,value,metadata:{dashboard:'v4',...metadata}})}catch{}
}

// Wire controls
$("#evolve").onclick=$("#branch").onclick=branch;
$("#root").onclick=freshRoots;
$("#undo").onclick=()=>{
  if(!history.length)return;
  const h=history.pop();specimens=h.specimens;gen=h.gen;
  selected.clear();mount();toast('undone');
};
$("#shuffle").onclick=()=>{specimens.sort(()=>Math.random()-.5);mount()};
$("#close").onclick=()=>{$("#detail").classList.add('hidden');current=null};
$("#potential").onclick=()=>{
  if(!current)return;
  selected.add(current.id);$("#potential").classList.add('on');
  recordEvent(current,'potential',1);toast('POTENTIAL recorded');
};
$("#save").onclick=()=>{
  if(!current)return;
  const fav=favorites();
  if(fav.has(current.id)){fav.delete(current.id);toast('unsaved')}
  else{fav.add(current.id);recordEvent(current,'save',1);toast('saved')}
  saveFavorites(fav);
};
$("#branchOne").onclick=()=>{
  if(!current)return;
  selected.clear();selected.add(current.id);
  $("#detail").classList.add('hidden');branch();
};

$$(".responses button").forEach(b=>b.onclick=()=>b.classList.toggle('active'));
$("#reflect").onclick=()=>$("#reflection").classList.toggle('hidden');

$$(".sub nav button").forEach(b=>b.onclick=()=>{
  $$(".sub nav button").forEach(x=>x.classList.remove('active'));
  b.classList.add('active');
  const tab=b.textContent.trim();
  if(tab==='POTENTIAL')loadTab('potential');
  else if(tab==='LINEAGE')loadTab('lineage');
  else if(tab==='SAVED')loadTab('saved');
  else if(tab==='STUDY')loadTab('study');
  else loadTab('open');
});

$$("#temps button").forEach(b=>b.onclick=()=>{
  $$("#temps button").forEach(x=>x.classList.remove('on'));
  b.classList.add('on');sigma=+b.dataset.s;
});

addEventListener('keydown',e=>{
  if(e.key==='Escape'){$("#detail").classList.add('hidden');current=null}
  if(e.code==='Space'&&selected.size){e.preventDefault();branch()}
});

async function loadTab(tab){
  try{
    if(tab==='potential'){
      specimens=await loadPopulation('potential',24);
    }else if(tab==='saved'){
      const fav=[...favorites()];
      if(fav.length)specimens=await getJSON(`/api/byids?ids=${encodeURIComponent(fav.join(','))}`);
      else specimens=[];
    }else{
      specimens=await loadPopulation('open',24);
    }
  }catch(e){specimens=[];toast('load failed: '+e.message)}
  selected.clear();gen=0;mount();
}

function loop(t){
  if(current)renderPheno($("#hero"),current,t/1000);
  requestAnimationFrame(loop);
}

// Init: load real specimens from API
(async()=>{
  try{
    specimens=await loadPopulation('open',24);
    mount();
  }catch(e){
    toast('API not available: '+e.message);
    // Fallback: generate synthetic
    specimens=Array.from({length:24},(_,i)=>({id:'mx-'+crypto.randomUUID().slice(0,8),source_id:'TINYMAPS',source_variant:'radial-warp',generation:0,parent_ids:[],genome:{},mode:'frontier'}));
    mount();
  }
  requestAnimationFrame(loop);
})();
