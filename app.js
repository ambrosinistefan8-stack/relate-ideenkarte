const svg = document.querySelector('#graph');
const status = document.querySelector('#status');
const message = document.querySelector('#loading');
const details = document.querySelector('#details');
const search = document.querySelector('#search');
const count = document.querySelector('#count');
const NS = 'http://www.w3.org/2000/svg';
let nodes = [], edges = [], selected = null;
const types = {idea:'Idee', theme:'Thema', document:'Dokument', task:'Aufgabe', agent:'Agent'};
function el(tag, attrs = {}) { const n = document.createElementNS(NS,tag); for (const [k,v] of Object.entries(attrs)) n.setAttribute(k,v); return n; }
function plain(tag, text, className) { const n = document.createElement(tag); n.textContent = text; if(className) n.className = className; return n; }
function normalize(g) {
  if (!Array.isArray(g.ideas) || !Array.isArray(g.themes) || !Array.isArray(g.links)) throw Error('Die Antwort enthält keine gültige Karte.');
  nodes = [];
  for (const [field,kind] of [['ideas','idea'],['themes','theme'],['documents','document'],['tasks','task'],['agents','agent']]) {
    for (const x of (g[field] || [])) {
      const id = kind === 'theme' ? `theme:${x.name}` : x.id;
      const title = kind === 'theme' ? x.name : (x.title || x.name);
      if (typeof id !== 'string' || typeof title !== 'string' || nodes.some(n => n.id === id)) throw Error('Ungültige oder doppelte Knoten-ID.');
      nodes.push({id,title,kind,description:x.description || ''});
    }
  }
  edges = g.links.map(x => ({source:x.idea_id,target:`theme:${x.theme}`,type:'HAS_THEME'})).concat((g.relations || []).map(x => ({source:x.source,target:x.target,type:x.type})));
  if(edges.some(e => !nodes.some(n=>n.id===e.source) || !nodes.some(n=>n.id===e.target))) throw Error('Eine Verbindung verweist auf einen fehlenden Knoten.');
}
function position() {
  const center = nodes.filter(n=>n.kind==='idea');
  const outer = nodes.filter(n=>n.kind!=='idea');
  center.forEach((n,i)=>{const a=2*Math.PI*i/Math.max(center.length,1)-Math.PI/2;n.x=400+125*Math.cos(a);n.y=270+100*Math.sin(a)});
  outer.forEach((n,i)=>{const a=2*Math.PI*i/Math.max(outer.length,1)-Math.PI/2;n.x=400+300*Math.cos(a);n.y=270+205*Math.sin(a)});
}
function titleLines(text) { let words=text.split(/\s+/), lines=['']; for(const word of words){let last=lines.length-1;if((lines[last]+' '+word).trim().length>17 && lines[last]) lines.push(word); else lines[last]=(lines[last]+' '+word).trim();} return lines.slice(0,2); }
function draw() {
  svg.replaceChildren(); position();
  let term = search.value.trim().toLocaleLowerCase('de');
  let matches = new Set(nodes.filter(n=>!term || `${n.title} ${types[n.kind]} ${n.description}`.toLocaleLowerCase('de').includes(term)).map(n=>n.id));
  for (const e of edges) {
    const a=nodes.find(n=>n.id===e.source), b=nodes.find(n=>n.id===e.target);
    let line=el('line',{x1:a.x,y1:a.y,x2:b.x,y2:b.y,class:`edge${selected && (e.source===selected || e.target===selected)?' selected':''}${term && !matches.has(e.source) && !matches.has(e.target)?' dim':''}`}); svg.append(line);
  }
  for (const n of nodes) {
    const group=el('g',{class:`node${n.id===selected?' active':''}${!matches.has(n.id)?' dim':''}`,transform:`translate(${n.x} ${n.y})`,tabindex:'0',role:'button','aria-label':`${types[n.kind]}: ${n.title}`});
    const color=n.kind==='theme'?'#f7e9cf':n.kind==='idea'?'#e3f0e4':'#e9eeeb';
    group.append(el('circle',{r:n.kind==='idea'?43:36,fill:color,stroke:'#fff','stroke-width':'2'}));
    let kind=el('text',{class:'kind',y:'-10'});kind.textContent=types[n.kind].toUpperCase();group.append(kind);
    titleLines(n.title).forEach((line,i)=>{let t=el('text',{class:'label',y:6+i*15});t.textContent=line;group.append(t)});
    const choose=()=>select(n.id);group.addEventListener('click',choose);group.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();choose()}});svg.append(group);
  }
}
function select(id) {
  selected=id; let n=nodes.find(n=>n.id===id); if(!n)return;
  details.replaceChildren(plain('span','DEINE AUSWAHL','section-label'),plain('div',types[n.kind].toUpperCase(),`badge ${n.kind}`),plain('h3',n.title));
  if(n.description)details.append(plain('p',n.description));
  let connected=edges.filter(e=>e.source===id||e.target===id);
  details.append(plain('div',`VERBINDUNGEN · ${connected.length}`,'small-label'));
  let list=plain('ul','','detail-list');
  connected.forEach(e=>{let other=nodes.find(x=>x.id===(e.source===id?e.target:e.source));let li=document.createElement('li');let b=plain('button',`${types[other.kind]} · ${other.title}`);b.type='button';b.addEventListener('click',()=>select(other.id));li.append(b,plain('div',e.type.replaceAll('_',' '),'relation'));list.append(li)});
  if(!connected.length) list.append(plain('li','Keine Verbindungen gefunden.'));details.append(list);draw();
}
async function load(){
  status.textContent='Verbinde mit Relate …';message.className='message';message.textContent='Daten werden geladen …';message.hidden=false;svg.hidden=true;
  try{const response=await fetch('/api/graph',{cache:'no-store'});const data=await response.json();if(!response.ok)throw Error(data.error+(data.detail?'\n'+data.detail:''));normalize(data);selected=null;count.textContent=`${nodes.length} Knoten · ${edges.length} Verbindungen`;draw();svg.hidden=false;message.hidden=true;status.textContent='Relate · lokal verbunden';}
  catch(e){nodes=[];edges=[];selected=null;svg.replaceChildren();details.replaceChildren(plain('span','DEINE AUSWAHL','section-label'),plain('p','Keine Daten verfügbar. Bitte Verbindung prüfen und erneut laden.'));count.textContent='';status.textContent='Relate · nicht erreichbar';message.className='message error';message.textContent=e.message;}
}
search.addEventListener('input',draw);document.querySelector('#reload').addEventListener('click',load);load();
