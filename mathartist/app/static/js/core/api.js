export async function api(path,opts={}){const r=await fetch(path,{headers:{"Content-Type":"application/json"},...opts});if(!r.ok)throw new Error(await r.text());return r.json()}
export const getJSON=p=>api(p);export const postJSON=(p,x)=>api(p,{method:"POST",body:JSON.stringify(x)});
