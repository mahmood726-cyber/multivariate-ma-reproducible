// Wraps an engine that has only fit() with the same sweep/univariate entry points (measurement only).
const e=require(process.env.K1_ENGINE);
module.exports={fit:e.fit,fitUnivariate:(y,v)=>{const f=e.fit(y.map((a,i)=>({y:[a],S:[[v[i]]]})));return{mu:f.mu[0],se:f.muSE[0],tau2:f.G[0][0],logLik:f.logLik};},
sweepRho:(rows,grid)=>grid.map(rw=>{try{return{rhoW:rw,status:'ok',fit:e.fit(rows.map(r=>{const c=rw*Math.sqrt(r.v[0]*r.v[1]);return{y:r.y,S:[[r.v[0],c],[c,r.v[1]]]};}))};}catch(x){return{rhoW:rw,status:'refused',reason:x.message};}})};
