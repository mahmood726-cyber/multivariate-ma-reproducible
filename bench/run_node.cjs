// Execute all shipped scripts, including complete inline page, in Node/linkedom.
const fs=require('fs'),vm=require('vm'),path=require('path');
const {parseHTML}=require('linkedom');
const variant=process.argv[2]||'original', root=`app-${variant}`;
const html=fs.readFileSync(`${root}/multivariate-ma/index.html`,'utf8');
const {window,document}=parseHTML(html);
window.matchMedia=()=>({matches:false});document.readyState='complete';
const context=vm.createContext({window,document,matchMedia:window.matchMedia,console});
for(const script of document.querySelectorAll('script')) {
 const src=script.getAttribute('src');
 vm.runInContext(src?fs.readFileSync(path.join(root,'multivariate-ma',src),'utf8'):script.textContent,context,{filename:src||'index.html:inline'});
}
const defaultUninstrumented=JSON.parse(JSON.stringify(window._almLastMultivariate()));
let capture=null;const fit=window.AlmMultivariate.fit;
window.AlmMultivariate.fit=function(studies,opts){capture={studies};const result=fit.apply(this,arguments);capture.result=result;return result;};
function run(text,names=['Outcome 1','Outcome 2']) {
 capture=null;document.getElementById('f-data').value=text;
 document.getElementById('f-o1').value=names[0];document.getElementById('f-o2').value=names[1];
 let error=null;
 try{document.getElementById('f-data').dispatchEvent(new window.Event('input'));}catch(e){error=e.message;}
 return {error,output:window._almLastMultivariate(),capture,headline:document.getElementById('headline').textContent,
 cards:Array.from(document.querySelectorAll('#stats .stat'),el=>({label:el.querySelector('.k').textContent,value:el.querySelector('.v').textContent})),svg:document.getElementById('plot-host').innerHTML};
}
const corpus=JSON.parse(fs.readFileSync('corpus.json','utf8')),out=[];
const num=x=>x===null?'NA':String(x);
for(const c of corpus){const text=c.studies.map(s=>[s.label,...[s.y[0],s.S[0][0],s.y[1],s.S[1][1],s.S[0][1]].map(num)].join(', ')).join('\n');out.push({id:c.id,input:text,...run(text,c.outcomes)});}
fs.writeFileSync(`app-${variant}.json`,JSON.stringify(out));
const valid='a, .1, .2, .3, .4, .1\nb, .5, .3, .6, .5, .2\nc, -.1, .2, .4, .4, .1';
const cases=[
 {id:'empty',text:'',status:'refused'},
 {id:'singleton',text:'a, .1, .2, .3, .4, .1',status:'refused'},
 {id:'indefinite',text:'a, .1, .2, .3, .4, 1\nb, .5, .3, .6, .5, 1',status:'refused'},
 {id:'singular',text:'a, 0, 1, 0, 1, 1\nb, 1, 1, 1, 1, 1',status:'refused'},
 {id:'negative-variance',text:'a, .1, -.2, .3, .4, .1\n'+valid,status:'ok',k:3},
 {id:'partial-outcome',text:'missing, NA, .2, .3, .4, .1\n'+valid,status:'ok',k:3},
 {id:'numeric-junk',text:'bad, .1oops, .2, .3, .4, .1\n'+valid,status:'ok',k:3},
 {id:'nonfinite',text:'bad, Infinity, .2, .3, .4, .1\n'+valid,status:'ok',k:3},
 {id:'blank-number',text:'bad, , .2, .3, .4, .1\n'+valid,status:'ok',k:3},
 {id:'comments',text:'# comment\n\nshort\n'+valid,status:'ok',k:3},
 {id:'escaped-outcomes',text:valid,names:['A&B <C>','D & E'],status:'ok',k:3},
 {id:'constant-effects',text:'a, 1, 1, 2, 1, 0\nb, 1, 1, 2, 1, 0',status:'ok',k:2},
 {id:'two-studies',text:'a, 0, 1, 0, 1, 0\nb, 3, 1, 2, 1, 0',status:'ok',k:2},
 {id:'no-study-cap',text:Array.from({length:2001},(_,i)=>`${i}, ${i%3}, 1, ${i%5}, 1, .2`).join('\n'),status:'ok',k:2001}
];
const probes=[];for(const c of cases){run(valid);probes.push({...c,...run(c.text,c.names)});}
const apiCases=[{id:'api-singleton',studies:[{y:[0,0],S:[[1,0],[0,1]]}]},{id:'api-indefinite',studies:[{y:[0,0],S:[[1,2],[2,1]]},{y:[1,1],S:[[1,2],[2,1]]}]},{id:'api-asymmetric',studies:[{y:[0,0],S:[[1,.2],[.3,1]]},{y:[1,1],S:[[1,0],[0,1]]}]},{id:'api-nan',studies:[{y:[NaN,0],S:[[1,0],[0,1]]},{y:[1,1],S:[[1,0],[0,1]]}]}];
for(const c of apiCases){let output=null,error=null;try{output=fit(c.studies);}catch(e){error=e.message;}probes.push({id:c.id,status:'refused',api:true,error,output});}
fs.writeFileSync(`focused-${variant}.json`,JSON.stringify(probes));
fs.writeFileSync(`runtime-${variant}.json`,JSON.stringify({node:process.version,linkedom:require('linkedom/package.json').version,mode:'Node VM with linkedom; all shipped page scripts executed',defaultUninstrumented,notVerified:['browser layout','native rendering','accessibility interactions']},null,2));
console.log(`APP ${variant}: ${out.length} configurations; ${probes.length} focused cases; no download controls exist`);
