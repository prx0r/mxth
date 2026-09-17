const cache=new Map();
export async function loadBinary(url,TypedArray){
  if(cache.has(url))return cache.get(url);
  const p=fetch(url).then(r=>{if(!r.ok)throw new Error(`${url}: ${r.status}`);return r.arrayBuffer()}).then(b=>new TypedArray(b));
  cache.set(url,p);return p;
}
export async function loadJSON(url){
  if(cache.has(url))return cache.get(url);
  const p=fetch(url).then(r=>{if(!r.ok)throw new Error(`${url}: ${r.status}`);return r.json()});
  cache.set(url,p);return p;
}
export function frameIndex(t,rate,count,fps=8){return ((Math.floor(t*fps*Math.max(.001,rate))%count)+count)%count}
