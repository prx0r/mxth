/* Derived directly from evoluteur/cymatics js/cymatics.js (MIT, Olivier Giulieri 2026).
   The equations / Bessel implementation are retained; MathArtist adds only observation/render layers. */
const factorial=n=>{let f=1;for(let i=2;i<=n;i++)f*=i;return f};
export const besselJ=(n,x)=>{const half=x/2;let term=Math.pow(half,n)/factorial(n),sum=0;for(let k=0;k<90;k++){sum+=term;term*=-(half*half)/((k+1)*(k+1+n));if(Math.abs(term)<1e-18*(Math.abs(sum)+1e-12))break}return sum};
const Z=[];function zeros(n,count){const out=[],step=.05;let x=n===0?.5:n,prev=besselJ(n,x);while(out.length<count&&x<400){let nx=x+step,v=besselJ(n,nx);if(prev*v<0){let lo=x,hi=nx;for(let i=0;i<60;i++){let m=(lo+hi)/2;if(besselJ(n,lo)*besselJ(n,m)<=0)hi=m;else lo=m}out.push((lo+hi)/2)}x=nx;prev=v}return out}export const zeroOf=(n,s)=>{if(!Z[n])Z[n]=zeros(n,9);return Z[n][s-1]};
export const squareAmplitude=(m,n,mix,x,y)=>{const a=Math.cos(n*Math.PI*x)*Math.cos(m*Math.PI*y);if(m===n)return a;const b=Math.cos(m*Math.PI*x)*Math.cos(n*Math.PI*y);return a+mix*b};
export const circleAmplitude=(n,s,x,y)=>{const dx=x*2-1,dy=y*2-1,r=Math.hypot(dx,dy);if(r>1)return NaN;return besselJ(n,zeroOf(n,s)*r)*Math.cos(n*Math.atan2(dy,dx))};
