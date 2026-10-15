// 마인드맵: 가운데 주제에서 가지를 뻗는 나무 구조. 가지마다 PPT 도형·색·글자 서식을 고른다.
// 배치는 자동(가운데 주제 좌우로 가지를 나눠 펼침)이고, 그린 결과는 일반 도형·연결선(model.js)으로 바꿔
// 화면·PNG 내보내기를 같이 쓴다.
import {SHAPES} from './shapes.js';
import {FONTS} from './table.js';
const MAX_NODES=300,MAX_TEXT=200;
// 가지 색(1단계 가지마다 돌아가며).
export const BRANCH_COLORS=['#3B82F6','#16A34A','#EA580C','#7C3AED','#DC2626','#CA8A04','#0891B2','#DB2777'];
const rid=()=>crypto.randomUUID();
export function mindmapNode(text='새 가지',style={}){return {id:rid(),text,style:{...style},children:[]};}
export function sampleMindmap(){
 const root=mindmapNode('2026 업무 계획',{shape:'ellipse',fill:'#1D4ED8',textColor:'#FFFFFF',bold:true,size:16});
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
 const n=mindmapNode(text);hit.node.children.push(n);return {map:next,id:n.id};
}
export function addSibling(map,id,text='새 가지'){
 const next=clone(map),hit=findNode(next,id);if(!hit?.parent)return addChild(map,id,text);
 const n=mindmapNode(text);const i=hit.parent.children.findIndex(c=>c.id===id);hit.parent.children.splice(i+1,0,n);return {map:next,id:n.id};
}
export function removeNode(map,id){
 const next=clone(map),hit=findNode(next,id);if(!hit?.parent)return map;
 hit.parent.children=hit.parent.children.filter(c=>c.id!==id);return next;
}
export function updateNode(map,id,patch){
 const next=clone(map),hit=findNode(next,id);if(!hit)return map;
 if(patch.text!==undefined)hit.node.text=patch.text;
 if(patch.style)hit.node.style={...hit.node.style,...patch.style};
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
  if(s.font!==undefined){if(!FONTS.includes(s.font))throw new Error('가지 글꼴을 확인해 주세요.');style.font=s.font;}
  return {id:n.id,text:n.text,style,children:n.children.map(check)};
 };
 const layout=['both','right','down'].includes(map.layout)?map.layout:'both';
 return {root:check(map.root),layout};
}
const W=200,H=64,GAP_X=70,GAP_Y=22;
function leaves(n){return n.children.length?n.children.reduce((s,c)=>s+leaves(c),0):1;}
/**
 * 자동 배치 → 도형·연결선. layout: both(좌우로 나눔)·right(오른쪽으로)·down(아래로 내려가는 조직도형).
 * 1단계 가지마다 색을 돌려 쓰고, 그 아래 가지는 같은 색의 연한 바탕을 쓴다(사용자가 고른 색이 있으면 그 색).
 */
export function mindmapGraph(map){
 const nodes=[],edges=[];
 const place=(n,x,y,depth,color,dir)=>{
  const s=n.style??{};
  const base=depth===0?{shape:'ellipse',fill:'#1D4ED8',stroke:'#1D4ED8',textColor:'#FFFFFF',bold:true,size:16}
   :depth===1?{shape:'roundRect',fill:color,stroke:color,textColor:'#FFFFFF',bold:true,size:13}
   :{shape:'roundRect',fill:'#FFFFFF',stroke:color,textColor:'#172b4d',size:12};
  const st={...base,...s};
  nodes.push({id:n.id,type:'flow',position:{x,y},width:depth===0?W+40:W,height:depth===0?H+16:H,
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
    markerEnd:{type:'arrowclosed',color},style:{stroke:color,strokeWidth:depth===1?3:2},data:{line:'curve',color,width:depth===1?3:2,dash:'solid',start:'none',end:'none'}});
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
  recDown(root,0,0,0,'#1D4ED8',null);
  return {nodes,edges};
 }
 const rootSpan=Math.max(leaves(root),1)*(H+GAP_Y);
 place(root,0,rootSpan/2-H/2,0,'#1D4ED8','right');
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
 return {nodes,edges};
}
