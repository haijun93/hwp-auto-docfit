// 마인드맵: 가운데 주제에서 가지를 뻗는 나무 구조. 가지마다 PPT 도형·색·글자 서식을 고른다.
// 자동 배치를 시작점으로 사용하며 수동 위치·부모 연결·선 모양은 문서에 보존한다.
// 화면·PNG 내보내기는 같은 도형·연결선을 사용한다.
import {SHAPES,DASHES,MARKERS} from './shapes.js';
import {isFontName} from './table.js';
const MAX_NODES=300,MAX_TEXT=200;
// 가지 색(1단계 가지마다 돌아가며).
/** 마인드맵 가지 모양(XMind·MindNode의 주제 모양을 참고해 자주 쓰는 것만 추림). */
export const MINDMAP_SHAPES=[['roundRect','둥근 사각형'],['rectangle','사각형'],['ellipse','타원형'],['terminator','알약형'],
 ['diamond','마름모'],['hexagon','육각형'],['parallelogram','평행사변형'],['cloud','구름'],['underline','밑줄'],['text','테두리 없음']];
/** 모양을 바꿀 범위: 이 가지만·같은 단계 모두·이 가지와 하위 가지·전체. */
export const MINDMAP_SCOPES=[['one','이 가지만'],['level','같은 단계 모두'],['branch','이 가지와 하위 가지'],['all','전체 가지']];
export const BRANCH_COLORS=['#3B82F6','#16A34A','#EA580C','#7C3AED','#DC2626','#CA8A04','#0891B2','#DB2777'];
const rid=()=>crypto.randomUUID();

// ---- 지도 테마(이음오피스·XMind의 테마 방식 참고: 모양 × 색 묶음 × 바탕을 지도 전체에 한 번에) ----
export const MINDMAP_THEME_SHAPES=[['classic','기본'],['pill','알약'],['capsule','캡슐'],['line','선'],['block','블록']];
/** 색 묶음: 이름, 가지 색 6개, 가운데 주제 색. 값은 이 앱에서 정했다. */
export const MINDMAP_PALETTES=[
 ['office','사무',['#3B82F6','#16A34A','#EA580C','#7C3AED','#DC2626','#CA8A04','#0891B2','#DB2777'],'#1D4ED8'],
 ['public','공공',['#1E40AF','#0F766E','#B45309','#6D28D9','#BE123C','#4D7C0F'],'#172554'],
 ['ocean','바다',['#0369A1','#0E7490','#2563EB','#0D9488','#4F46E5','#0284C7'],'#0C4A6E'],
 ['forest','숲',['#15803D','#65A30D','#A16207','#0F766E','#4D7C0F','#B45309'],'#14532D'],
 ['sunset','노을',['#EA580C','#DB2777','#D97706','#DC2626','#C026D3','#F59E0B'],'#9A3412'],
 ['berry','보라',['#7C3AED','#C026D3','#4F46E5','#DB2777','#9333EA','#2563EB'],'#4C1D95'],
 ['pastel','파스텔',['#60A5FA','#4ADE80','#FB923C','#C084FC','#F87171','#FACC15'],'#3B82F6'],
 ['mono','흑백',['#334155','#475569','#1F2937','#64748B','#374151','#52525B'],'#0F172A'],
];
export const MINDMAP_GROUNDS=[['light','밝게'],['dark','어둡게'],['tint','옅은 색']];
export function themeOf(map){
 const t=map?.theme??{};
 return {shape:MINDMAP_THEME_SHAPES.some(([k])=>k===t.shape)?t.shape:'classic',
  palette:MINDMAP_PALETTES.some(([k])=>k===t.palette)?t.palette:'office',
  ground:MINDMAP_GROUNDS.some(([k])=>k===t.ground)?t.ground:'light'};
}
const mix=(a,b,share)=>{
 const p=h=>[1,3,5].map(i=>parseInt(h.slice(i,i+2),16));
 const [x,y]=[p(a),p(b)];
 return '#'+x.map((v,i)=>Math.round(v*share+y[i]*(1-share)).toString(16).padStart(2,'0')).join('').toUpperCase();
};
/** 테마가 정한 바탕·글자색·가지 색. */
export function themeColors(map){
 const t=themeOf(map),[, ,branches,central]=MINDMAP_PALETTES.find(([k])=>k===t.palette);
 const background=t.ground==='dark'?'#1E2430':t.ground==='tint'?mix(central,'#FFFFFF',.07):'#FFFFFF';
 const text=t.ground==='dark'?'#F1F5F9':'#172B4D';
 return {...t,branches,central:t.ground==='dark'?mix(central,'#FFFFFF',.55):central,background,text};
}
/** 단계(0 가운데·1 큰 가지·2 이하)와 가지 색에 따른 테마 기본 모양. */
function themeBase(c,depth,color){
 const soft=mix(color,c.background,c.ground==='dark'?.35:.18);
 switch(c.shape){
  case 'pill':return depth===0?{shape:'terminator',fill:c.central,stroke:c.central,textColor:'#FFFFFF',bold:true,size:16}
   :depth===1?{shape:'terminator',fill:soft,stroke:soft,textColor:c.text,bold:true,size:13}
   :{shape:'text',fill:'none',stroke:color,textColor:c.text,size:12};
  case 'capsule':return depth===0?{shape:'terminator',fill:c.central,stroke:c.central,textColor:'#FFFFFF',bold:true,size:16}
   :depth===1?{shape:'terminator',fill:c.background,stroke:color,textColor:c.text,bold:true,size:13}
   :{shape:'text',fill:'none',stroke:color,textColor:c.text,size:12};
  case 'line':return depth===0?{shape:'roundRect',fill:c.background,stroke:c.central,textColor:c.text,bold:true,size:16}
   :{shape:'underline',fill:'none',stroke:color,textColor:c.text,bold:depth===1,size:depth===1?13:12};
  case 'block':return depth===0?{shape:'roundRect',fill:c.central,stroke:c.central,textColor:'#FFFFFF',bold:true,size:16}
   :depth===1?{shape:'roundRect',fill:color,stroke:color,textColor:'#FFFFFF',bold:true,size:13}
   :{shape:'roundRect',fill:soft,stroke:soft,textColor:c.text,size:12};
  default:return depth===0?{shape:'ellipse',fill:c.central,stroke:c.central,textColor:'#FFFFFF',bold:true,size:16}
   :depth===1?{shape:'roundRect',fill:color,stroke:color,textColor:'#FFFFFF',bold:true,size:13}
   :{shape:'roundRect',fill:c.background,stroke:color,textColor:c.text,size:12};
 }
}
/** 가지마다 따로 고친 서식을 지워 지도 전체를 테마 하나로 맞춘다(위치·크기·연결선은 그대로). */
export function clearBranchStyles(map){
 const next=structuredClone(map);
 (function w(n){n.style={};n.children.forEach(w);})(next.root);
 return next;
}
export function mindmapNode(text='새 가지',style={}){return {id:rid(),text,style:{...style},children:[]};}
export function sampleMindmap(){
 const root=mindmapNode('2026 업무 계획');
 const add=(parent,text,kids=[])=>{const n=mindmapNode(text);n.children=kids.map(k=>mindmapNode(k));parent.children.push(n);return n;};
 add(root,'관광 활성화',['축제 개최','관광 안내 개선']);
 add(root,'지역 경제',['전통시장 지원','소상공인 컨설팅']);
 add(root,'문화 예술',['공연장 운영','생활 문화 교실']);
 add(root,'청년 정책',['일자리 연계','주거 지원']);
 return {root,layout:'both'};
}
function walk(node,fn,parent=null,depth=0){fn(node,parent,depth);node.children.forEach(c=>walk(c,fn,node,depth+1));}
export function findNode(map,id){let found=null;walk(map.root,(n,p)=>{if(n.id===id)found={node:n,parent:p};});return found;}
const clone=map=>structuredClone(map);
export function addChild(map,parentId,text='새 가지'){
 const next=clone(map),hit=findNode(next,parentId);if(!hit)return {map,id:null};
 const n=mindmapNode(text);
 if(hit.node.position){
  n.position={x:hit.node.position.x+270,y:hit.node.position.y+90*hit.node.children.length};
  const used=[];walk(next.root,v=>{if(v.position)used.push(v.position);});
  while(used.some(p=>Math.abs(p.x-n.position.x)<210&&Math.abs(p.y-n.position.y)<80))n.position.y+=90;
 }
 hit.node.children.push(n);return {map:next,id:n.id};
}
export function addSibling(map,id,text='새 가지'){
 const next=clone(map),hit=findNode(next,id);if(!hit?.parent)return addChild(map,id,text);
 const n=mindmapNode(text);const i=hit.parent.children.findIndex(c=>c.id===id);
 if(hit.node.position)n.position={x:hit.node.position.x,y:hit.node.position.y+100};
 hit.parent.children.splice(i+1,0,n);return {map:next,id:n.id};
}
export function removeNode(map,id){
 const next=clone(map),hit=findNode(next,id);if(!hit?.parent)return map;
 hit.parent.children=hit.parent.children.filter(c=>c.id!==id);return next;
}
export function updateNode(map,id,patch){
 const next=clone(map),hit=findNode(next,id);if(!hit)return map;
 if(patch.text!==undefined)hit.node.text=patch.text;
 if(patch.style)hit.node.style={...hit.node.style,...patch.style};
 if(patch.position)hit.node.position={...patch.position};
 if(patch.size)hit.node.size={...patch.size};
 if(patch.edge)hit.node.edge={...hit.node.edge,...patch.edge};
 return next;
}
/** 여러 가지의 서식을 한 번에 바꾼다(scope는 MINDMAP_SCOPES 키). 원형으로 바꾸면 손으로 바꾼 크기도 정사각형으로 맞춘다. */
export function restyleNodes(map,id,scope,patch){
 const next=clone(map);let targetDepth=-1,target=null;
 walk(next.root,(n,p,d)=>{if(n.id===id){targetDepth=d;target=n;}});
 if(!target)return map;
 const inBranch=new Set();walk(target,n=>inBranch.add(n.id));
 walk(next.root,(n,p,d)=>{
  const hit=scope==='all'||(scope==='level'&&d===targetDepth)||(scope==='branch'&&inBranch.has(n.id))||n.id===id;
  if(!hit)return;
  n.style={...n.style,...patch};
  if(patch.shape==='circle'&&n.size){const s=Math.max(n.size.width,n.size.height);n.size={width:s,height:s};}
 });
 return next;
}
/** 가지 순서 옮기기(같은 부모 안에서 위·아래). */
export function moveNode(map,id,delta){
 const next=clone(map),hit=findNode(next,id);if(!hit?.parent)return map;
 const list=hit.parent.children,i=list.findIndex(c=>c.id===id),j=i+delta;
 if(j<0||j>=list.length)return map;
 [list[i],list[j]]=[list[j],list[i]];return next;
}
const hex=v=>typeof v==='string'&&/^#[0-9A-Fa-f]{6}$/.test(v);
export function validateMindmap(map){
 if(!map||typeof map!=='object'||!map.root)throw new Error('마인드맵 형식을 확인해 주세요.');
 let count=0;const ids=new Set();
 const check=n=>{
  if(++count>MAX_NODES)throw new Error('마인드맵 가지는 '+MAX_NODES+'개까지입니다.');
  if(typeof n?.id!=='string'||!n.id||n.id.length>100||ids.has(n.id)||typeof n.text!=='string'||n.text.length>MAX_TEXT||!Array.isArray(n.children))throw new Error('마인드맵 가지를 확인해 주세요.');
  ids.add(n.id);
  const s=n.style??{},style={};
  if(s.shape!==undefined){if(!SHAPES.has(s.shape))throw new Error('가지 도형을 확인해 주세요.');style.shape=s.shape;}
  for(const k of ['fill','stroke','textColor'])if(s[k]!==undefined){if(!(hex(s[k])||(k!=='textColor'&&s[k]==='none')))throw new Error('가지 색을 확인해 주세요.');style[k]=s[k];}
  if(s.size!==undefined){if(typeof s.size!=='number'||!(s.size>=6&&s.size<=40))throw new Error('가지 글자 크기를 확인해 주세요.');style.size=s.size;}
  if(s.bold!==undefined){if(typeof s.bold!=='boolean')throw new Error('가지 굵게 값을 확인해 주세요.');style.bold=s.bold;}
  if(s.font!==undefined){if(!isFontName(s.font))throw new Error('가지 글꼴을 확인해 주세요.');style.font=s.font;}
  const extra={};
  if(n.size!==undefined){
   if(!Number.isFinite(n.size?.width)||!Number.isFinite(n.size?.height)||n.size.width<40||n.size.height<30||n.size.width>4000||n.size.height>4000)throw new Error('가지 크기를 확인해 주세요.');
   extra.size={width:n.size.width,height:n.size.height};
  }
  if(n.position!==undefined){
   if(!Number.isFinite(n.position?.x)||!Number.isFinite(n.position?.y)||Math.abs(n.position.x)>1000000||Math.abs(n.position.y)>1000000)throw new Error('가지 위치를 확인해 주세요.');
   extra.position={x:n.position.x,y:n.position.y};
  }
  if(n.edge!==undefined){
   const e=n.edge;if(!e||typeof e!=='object')throw new Error('가지 연결선을 확인해 주세요.');
   extra.edge={hidden:e.hidden===true};
   if(e.label!==undefined){if(typeof e.label!=='string'||e.label.length>300)throw new Error('연결선 설명을 확인해 주세요.');extra.edge.label=e.label;}
   for(const k of ['sourceHandle','targetHandle'])if(e[k]!==undefined){if(!['left','right','top','bottom'].includes(e[k]))throw new Error('연결점을 확인해 주세요.');extra.edge[k]=e[k];}
   if(e.style!==undefined){
    const st=e.style;
    if(!st||!['step','straight','curve'].includes(st.line)||!hex(st.color)||!Number.isFinite(st.width)||st.width<0.5||st.width>10||!DASHES.some(([k])=>k===st.dash)||!MARKERS.some(([k])=>k===st.start)||!MARKERS.some(([k])=>k===st.end))throw new Error('연결선 모양을 확인해 주세요.');
    extra.edge.style={line:st.line,color:st.color,width:st.width,dash:st.dash,start:st.start,end:st.end};
   }
  }
  return {id:n.id,text:n.text,style,...extra,children:n.children.map(check)};
 };
 const layout=['both','right','down'].includes(map.layout)?map.layout:'both';
 let theme;
 if(map.theme!==undefined){
  const t=map.theme;
  if(!t||typeof t!=='object'||!MINDMAP_THEME_SHAPES.some(([k])=>k===t.shape)||!MINDMAP_PALETTES.some(([k])=>k===t.palette)||!MINDMAP_GROUNDS.some(([k])=>k===t.ground))
   throw new Error('지도 테마를 확인해 주세요.');
  theme={shape:t.shape,palette:t.palette,ground:t.ground};
 }
 return {root:check(map.root),layout,...(theme?{theme}:{})};
}
const W=200,H=64,GAP_X=70,GAP_Y=22;
function leaves(n){return n.children.length?n.children.reduce((s,c)=>s+leaves(c),0):1;}
/**
 * 자동 배치 → 도형·연결선. layout: both(좌우로 나눔)·right(오른쪽으로)·down(아래로 내려가는 조직도형).
 * 1단계 가지마다 색을 돌려 쓰고, 그 아래 가지는 같은 색의 연한 바탕을 쓴다(사용자가 고른 색이 있으면 그 색).
 */
export function mindmapGraph(map){
 const nodes=[],edges=[],colors=themeColors(map);
 const BRANCH_COLORS=colors.branches,edgeLine=colors.shape==='block'?'step':'curve';
 const place=(n,x,y,depth,color,dir)=>{
  const s=n.style??{};
  const base=themeBase(colors,depth,color);
  const st={...base,...s};
  let w=n.size?.width??(depth===0?W+40:W),h=n.size?.height??(depth===0?H+16:H);
  if(st.shape==='circle'&&!n.size){
   // 원형은 정사각형 상자. 자동 배치 자리의 가운데(왼쪽 가지는 오른쪽 끝)에 맞춘다.
   const d=depth===0?120:76;
   if(dir==='left')x+=w-d;else if(dir==='down')x+=(w-d)/2;
   y+=(h-d)/2;w=d;h=d;
  }
  nodes.push({id:n.id,type:'flow',position:n.position?{...n.position}:{x,y},width:w,height:h,
   data:{label:n.text,shape:st.shape,color:'white',fill:st.fill,stroke:st.stroke,strokeWidth:2,textColor:st.textColor,size:st.size,bold:!!st.bold,...(st.font?{font:st.font}:{})}});
 };
 const rec=(n,x,top,depth,color,dir,parent)=>{
  const span=leaves(n)*(H+GAP_Y);
  const y=dir==='down'?top:top+span/2-H/2;
  const xx=x;
  place(n,xx,y,depth,color,dir);
  if(parent){
   const sides=dir==='left'?['left','right']:dir==='down'?['bottom','top']:['right','left'];
   edges.push({id:'mm-'+parent+'-'+n.id,source:parent,target:n.id,sourceHandle:sides[0],targetHandle:sides[1],type:'smoothstep',label:'',
    markerEnd:{type:'arrowclosed',color},style:{stroke:color,strokeWidth:depth===1?3:2},data:{line:edgeLine,color,width:depth===1?3:2,dash:'solid',start:'none',end:'none'}});
  }
  let cursor=top;
  n.children.forEach((c,i)=>{
   const childColor=depth===0?BRANCH_COLORS[i%BRANCH_COLORS.length]:color;
   const step=leaves(c)*(dir==='down'?W+GAP_X/2:H+GAP_Y);
   if(dir==='down')rec(c,cursor,y+H+GAP_X,depth+1,childColor,dir,n.id);
   else rec(c,dir==='left'?xx-W-GAP_X:xx+(depth===0?W+40:W)+GAP_X,cursor,depth+1,childColor,dir,n.id);
   cursor+=step;
  });
 };
 const root=map.root,layout=map.layout??'both';
 if(layout==='down'){
  // 조직도처럼 위에서 아래로: 자식 폭만큼 가로로 펼친다.
  const widthOf=n=>Math.max(W,n.children.reduce((s,c)=>s+widthOf(c)+GAP_X/2,-GAP_X/2));
  const recDown=(n,left,y,depth,color,parent)=>{
   const w=widthOf(n);place(n,left+w/2-W/2,y,depth,color,'down');
   if(parent)edges.push({id:'mm-'+parent+'-'+n.id,source:parent,target:n.id,sourceHandle:'bottom',targetHandle:'top',type:'smoothstep',label:'',
    markerEnd:{type:'arrowclosed',color},style:{stroke:color,strokeWidth:2},data:{line:'step',color,width:2,dash:'solid',start:'none',end:'none'}});
   let cursor=left;
   n.children.forEach((c,i)=>{const cc=depth===0?BRANCH_COLORS[i%BRANCH_COLORS.length]:color;recDown(c,cursor,y+H+GAP_X,depth+1,cc,n.id);cursor+=widthOf(c)+GAP_X/2;});
  };
  recDown(root,0,0,0,colors.central,null);
  return finishGraph(map,nodes,edges);
 }
 const rootSpan=Math.max(leaves(root),1)*(H+GAP_Y);
 place(root,0,rootSpan/2-H/2,0,colors.central,'right');
 const kids=root.children.map((c,i)=>({c,color:BRANCH_COLORS[i%BRANCH_COLORS.length]}));
 const right=layout==='right'?kids:kids.filter((_,i)=>i%2===0),left=layout==='right'?[]:kids.filter((_,i)=>i%2===1);
 const side=(list,dir)=>{
  const total=list.reduce((s,{c})=>s+leaves(c)*(H+GAP_Y),0);
  let cursor=rootSpan/2-total/2;
  for(const {c,color} of list){
   rec(c,dir==='left'?-W-GAP_X:W+40+GAP_X,cursor,1,color,dir,root.id);
   cursor+=leaves(c)*(H+GAP_Y);
  }
 };
 side(right,'right');side(left,'left');
 return finishGraph(map,nodes,edges);
}

/** Move a branch and descendants; a root move or cycle is invalid. */
export function reparentNode(map,id,parentId,handles={}){
 const next=clone(map),hit=findNode(next,id),parent=findNode(next,parentId);
 if(!hit?.parent||!parent||findNode({root:hit.node},parentId))throw new Error('자기 자신이나 하위 가지에 연결할 수 없습니다.');
 hit.parent.children=hit.parent.children.filter(n=>n.id!==id);
 parent.node.children.push(hit.node);
 hit.node.edge={...hit.node.edge,...handles,hidden:false};return next;
}
/** Freeze visible placement before dragging so other branches stay in place. */
export function positionMindmap(map,positions){
 const next=clone(map),display=mindmapGraph(map),byId=new Map(display.nodes.map(n=>[n.id,n.position]));
 walk(next.root,n=>{n.position={...(positions[n.id]??byId.get(n.id))};});return next;
}
export function autoLayoutMindmap(map,layout=map.layout){
 const next=clone(map);next.layout=layout;walk(next.root,n=>{delete n.position;});return next;
}
function finishGraph(map,nodes,edges){
 const byId=new Map();walk(map.root,n=>byId.set(n.id,n));
 return {background:themeColors(map).background,nodes,edges:edges.filter(e=>!byId.get(e.target)?.edge?.hidden).map(e=>{
  const saved=byId.get(e.target)?.edge??{};
  const a=nodes.find(n=>n.id===e.source),b=nodes.find(n=>n.id===e.target);
  const horizontal=Math.abs(b.position.x-a.position.x)>=Math.abs(b.position.y-a.position.y);
  const sides=horizontal?(b.position.x>=a.position.x?['right','left']:['left','right']):(b.position.y>=a.position.y?['bottom','top']:['top','bottom']);
  const styled=saved.style?{data:{...saved.style},style:{stroke:saved.style.color,strokeWidth:saved.style.width},markerEnd:{type:'arrowclosed',color:saved.style.color}}:{};
  return {...e,...styled,label:saved.label??'',sourceHandle:saved.sourceHandle??sides[0],targetHandle:saved.targetHandle??sides[1]};
 })};
}
