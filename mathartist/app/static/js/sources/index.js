import{initLenia,renderLenia}from'./lenia.js';
import{initNS,renderNS}from'./ns26.js';
import{renderChladni}from'./chladni.js';
import{initBioelectric,renderBioelectric}from'./bioelectric.js';
import{renderArraySeq}from'./arrayseq.js';
import{renderTinyMaps}from'./tiny_maps.js';

/* Source registry.
   Built-ins are optimized renderers. Any additional spec registered with
   scripts/import_array_sequence.py automatically falls back to the generic
   immutable array-sequence renderer, so new paper/model sources do not require
   editing the dashboard core. */
export async function initSources(){await Promise.allSettled([initLenia(),initBioelectric(),initNS()])}
export function render(canvas,p,t){
  if(p.source_id==='LENIA')return renderLenia(canvas,p,t);
  if(p.source_id==='NS26')return renderNS(canvas,p,t);
  if(p.source_id==='CHLADNI')return renderChladni(canvas,p,t);
  if(p.source_id==='BIOELECTRIC')return renderBioelectric(canvas,p,t);
  if(p.source_id==='TINYMAPS')return renderTinyMaps(canvas,p,t);
  return renderArraySeq(canvas,p,t);
}
