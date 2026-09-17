export function sessionId(){let s=localStorage.getItem("mathartist.session");if(!s){s=(crypto.randomUUID?.()||Math.random().toString(36).slice(2));localStorage.setItem("mathartist.session",s)}return s}
export function favorites(){return new Set(JSON.parse(localStorage.getItem("mathartist.favorites")||"[]"))}
export function saveFavorites(set){localStorage.setItem("mathartist.favorites",JSON.stringify([...set]))}
