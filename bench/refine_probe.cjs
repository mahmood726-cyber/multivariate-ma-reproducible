// Diagnostic only: examine rank-one boundary gradient using shipped profile.
const fs=require('fs'),vm=require('vm');
let src=fs.readFileSync('app-patched/shared/multivariate-ma.js','utf8').replace('var api = { fit: fit };','var api = { fit: fit, profile: _profile };');
let ctx=vm.createContext({});vm.runInContext(src,ctx);const api=ctx.AlmMultivariate;
const c=JSON.parse(fs.readFileSync('corpus.json','utf8'))[14],ss=c.accepted.map(i=>c.studies[i-1]);
const f=api.fit(ss);console.log(f);
function gr(x){let G=x.map(a=>x.map(b=>a*b)),p=api.profile(ss,G),sc=[[0,0],[0,0]];
 ss.forEach((s,i)=>{let w=p.Ws[i],d=s.y.map((v,j)=>v-p.mu[j]),r=w.map(row=>row.reduce((a,v,j)=>a+v*d[j],0));
 for(let a=0;a<2;a++)for(let b=0;b<2;b++){let t=0;for(let u=0;u<2;u++)for(let v=0;v<2;v++)t+=w[a][u]*p.sumWinv[u][v]*w[v][b];sc[a][b]+=w[a][b]-t-r[a]*r[b];}});
 return sc.map(row=>row[0]*x[0]+row[1]*x[1]);}
let x=[Math.sqrt(f.G[0][0]),f.G[0][1]/Math.sqrt(f.G[0][0])];
for(let it=0;it<10;it++){let g=gr(x),h=[[],[]];for(let j=0;j<2;j++){let l=x.slice(),r=x.slice();l[j]-=1e-4;r[j]+=1e-4;let gl=gr(l),gg=gr(r);for(let i=0;i<2;i++)h[i][j]=(gg[i]-gl[i])/2e-4;}
let det=h[0][0]*h[1][1]-h[0][1]*h[1][0],dx=[(h[1][1]*g[0]-h[0][1]*g[1])/det,(-h[1][0]*g[0]+h[0][0]*g[1])/det];console.log(it,x,g,dx);x=x.map((v,j)=>v-dx[j]);}
let G=x.map(a=>x.map(b=>a*b));console.log('FINAL',G,api.profile(ss,G));
