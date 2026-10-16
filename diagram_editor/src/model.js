// Application-owned flow document model. React Flow (MIT) renders this model.
// 도형은 PPT처럼 40여 종(shapes.js), 바탕색·테두리색·굵기·선 모양·글자 서식을 도형마다 정한다.
// 연결선은 꺾은선·직선·곡선, 색·굵기·선 모양, 양 끝 화살표 모양을 고른다. 예전 문서(도형 4종·색 이름)도 그대로 연다.
import {FONTS,isFontName,validateTable} from './table.js';
import {SHAPES,LINE_SHAPES,shapePath,textFactor,DASHES,MARKERS,dashArray,markerSvg} from './shapes.js';
import {validateMindmap,mindmapGraph} from './mindmap.js';
export const FORMAT = 'docfit-flow';
export const COLORS = {blue:'#dbeafe',green:'#dcfce7',orange:'#ffedd5',yellow:'#fef9c3',white:'#ffffff'};
// 색 고르기 판(PPT 테마 색처럼 자주 쓰는 색).
export const PALETTE=['#FFFFFF','#F2F2F2','#D9D9D9','#7F7F7F','#262626','#DBEAFE','#BFDBFE','#3B82F6','#1D4ED8','#DCFCE7','#86EFAC','#16A34A',
 '#FEF9C3','#FDE047','#CA8A04','#FFEDD5','#FDBA74','#EA580C','#FEE2E2','#FCA5A5','#DC2626','#EDE9FE','#C4B5FD','#7C3AED','#DFE6F7','#4C4C4C'];
// 예시 서식: 가로 1종·세로 1종(여러 도형과 분기·되돌아가는 선을 함께 보인다).
export const templates = {
 horizontal:{name:'가로 흐름도'},
 vertical:{name:'세로 흐름도'},
};
export const id = () => crypto.randomUUID();
export function node(label, x, y, shape='rectangle',color='blue',identity=id(),style={}) {
 return {id:identity,type:'flow',position:{x,y},data:{label,shape,color,...style},width:220,height:90};
}
export const EDGE_DEFAULT={line:'step',color:'#334155',width:2,dash:'solid',start:'none',end:'arrow'};
export function edge(source,target,label='',identity=id(),sourceHandle='bottom',targetHandle='top',style=null) {
 const s=style?{...EDGE_DEFAULT,...style}:EDGE_DEFAULT;
 return {id:identity,source,target,sourceHandle,targetHandle,type:'smoothstep',label,
  markerEnd:{type:'arrowclosed',color:s.color},style:{stroke:s.color,strokeWidth:s.width},...(style?{data:{...s}}:{})};
}
export function template(key) {
 const vertical=key==='vertical';
 if(!templates[key])throw new Error('예시 서식을 확인해 주세요.');
 const at=(i,branch=0)=>vertical?{x:100+branch*300,y:40+i*150}:{x:40+i*270,y:120+branch*190};
 const steps=[['시작','terminator','green'],['신청 접수','process','blue'],['요건 검토','process','blue'],['적합한가?','decision','yellow'],
  ['결재','predefined','blue'],['결과 통보','document','blue'],['끝','terminator','green']];
 const nodes=steps.map(([label,shape,color],i)=>{const p=at(i);return node(label,p.x,p.y,shape,color);});
 const back=at(3,1);nodes.push(node('보완 요청',back.x,back.y,'manualInput','orange'));
 const out=vertical?['bottom','top']:['right','left'];
 const edges=nodes.slice(0,6).map((n,i)=>edge(n.id,nodes[i+1].id,i===3?'예':'',id(),out[0],out[1]));
 edges.push(edge(nodes[3].id,nodes[7].id,'아니오',id(),vertical?'right':'bottom',vertical?'left':'top',{dash:'dash'}));
 edges.push(edge(nodes[7].id,nodes[2].id,'다시 검토',id(),vertical?'top':'left',vertical?'right':'bottom',{line:'curve',dash:'dash'}));
 return {nodes,edges,name:templates[key].name};
}
const finite = v => typeof v==='number' && Number.isFinite(v) && Math.abs(v)<=1e6;
const text = (v,max=2000) => typeof v==='string'&&v.length<=max;
const hex = v => typeof v==='string'&&/^#[0-9A-Fa-f]{6}$/.test(v);
const MARKER_KEYS=new Set(MARKERS.map(([k])=>k)),DASH_KEYS=new Set(DASHES.map(([k])=>k));
export function validate(snapshot) {
 if(snapshot?.format!==FORMAT||snapshot.version!==1||!Array.isArray(snapshot.nodes)||!Array.isArray(snapshot.edges))throw new Error('지원하지 않는 흐름도 형식입니다.');
 if(snapshot.nodes.length>1000||snapshot.edges.length>2000)throw new Error('도형 또는 연결선 수가 제한을 넘습니다.');
 const ids=new Set();
 const nodes=snapshot.nodes.map(n=>{
  if(!text(n.id,100)||!n.id||ids.has(n.id)||!finite(n.position?.x)||!finite(n.position?.y)||!text(n.data?.label)||!SHAPES.has(n.data.shape)||!Object.hasOwn(COLORS,n.data.color))throw new Error('도형 데이터가 올바르지 않습니다.');
  ids.add(n.id);
  const style={...nodeTextStyle(n.data),...nodeShapeStyle(n.data)};
  const w=n.width??220,h=n.height??90;
  if(!finite(w)||!finite(h)||w<20||h<10||w>100000||h>100000)throw new Error('도형 크기가 올바르지 않습니다.');
  const made=node(n.data.label,n.position.x,n.position.y,n.data.shape,n.data.color,n.id);
  return {...made,data:{...made.data,...style},width:w,height:h};
 });
 const nodeIds=new Set(ids);
 const edges=snapshot.edges.map(e=>{
  if(!text(e.id,100)||!e.id||ids.has(e.id)||!nodeIds.has(e.source)||!nodeIds.has(e.target)||!text(e.label??'',300))throw new Error('연결선 데이터가 올바르지 않습니다.');
  ids.add(e.id);
  const handles=['top','bottom','left','right'];
  if(!handles.includes(e.sourceHandle)||!handles.includes(e.targetHandle))throw new Error('연결 위치를 확인해 주세요.');
  return edge(e.source,e.target,e.label??'',e.id,e.sourceHandle,e.targetHandle,e.data==null?null:edgeStyle(e.data));
 });
 const table=snapshot.table==null?undefined:validateTable(snapshot.table);
 const mindmap=snapshot.mindmap==null?undefined:validateMindmap(snapshot.mindmap);
 return {format:FORMAT,version:1,nodes,edges,...(table?{table}:{}),...(mindmap?{mindmap}:{})};
}
/** 연결선 모양: line(step 꺾은선·straight 직선·curve 곡선), color, width(0.5~10), dash, start·end(화살표 머리). */
export function edgeStyle(data){
 const s={...EDGE_DEFAULT,...data};
 if(!['step','straight','curve'].includes(s.line)||!hex(s.color)||typeof s.width!=='number'||!(s.width>=0.5&&s.width<=10)||!DASH_KEYS.has(s.dash)||!MARKER_KEYS.has(s.start)||!MARKER_KEYS.has(s.end))
  throw new Error('연결선 모양을 확인해 주세요.');
 return {line:s.line,color:s.color,width:s.width,dash:s.dash,start:s.start,end:s.end};
}
/** 도형 글자 서식(선택): font(글꼴), size(pt), bold, textColor. 값이 없으면 예전 기본(맑은 고딕 12pt). */
export const TEXT_FONTS=FONTS;
export function nodeTextStyle(data){
 const style={};
 if(data.font!==undefined){if(!isFontName(data.font))throw new Error('도형 글꼴을 확인해 주세요.');style.font=data.font;}
 if(data.size!==undefined){if(typeof data.size!=='number'||!(data.size>=6&&data.size<=40))throw new Error('도형 글꼴 크기를 확인해 주세요.');style.size=data.size;}
 if(data.bold!==undefined){if(typeof data.bold!=='boolean')throw new Error('도형 굵게 값을 확인해 주세요.');style.bold=data.bold;}
 if(data.textColor!==undefined){if(!hex(data.textColor))throw new Error('도형 글자색을 확인해 주세요.');style.textColor=data.textColor;}
 return style;
}
/** 도형 모양 서식(선택): fill(바탕색·'none'), stroke(테두리색·'none'), strokeWidth(0~10), dash, lineStart·lineEnd(선 도형 화살표). */
export function nodeShapeStyle(data){
 const style={};
 const color=v=>v==='none'||hex(v);
 if(data.fill!==undefined){if(!color(data.fill))throw new Error('도형 바탕색을 확인해 주세요.');style.fill=data.fill;}
 if(data.stroke!==undefined){if(!color(data.stroke))throw new Error('도형 테두리색을 확인해 주세요.');style.stroke=data.stroke;}
 if(data.strokeWidth!==undefined){if(typeof data.strokeWidth!=='number'||!(data.strokeWidth>=0&&data.strokeWidth<=10))throw new Error('도형 테두리 굵기를 확인해 주세요.');style.strokeWidth=data.strokeWidth;}
 if(data.dash!==undefined){if(!DASH_KEYS.has(data.dash))throw new Error('도형 테두리 모양을 확인해 주세요.');style.dash=data.dash;}
 for(const key of ['lineStart','lineEnd'])if(data[key]!==undefined){if(!MARKER_KEYS.has(data[key]))throw new Error('선 화살표 모양을 확인해 주세요.');style[key]=data[key];}
 return style;
}
/** 도형을 그릴 실제 값(예전 문서의 색 이름 color도 바탕색으로 쓴다). */
export function nodePaint(data){
 const line=LINE_SHAPES.has(data.shape),textOnly=data.shape==='text';
 return {fill:line||textOnly?'none':(data.fill??COLORS[data.color]??'#ffffff'),
  stroke:textOnly?(data.stroke??'none'):(data.stroke??(line?'#334155':'#475569')),
  width:data.strokeWidth??2,dash:dashArray(data.dash),
  start:data.lineStart??'none',end:data.lineEnd??(data.shape==='arrowLine'||data.shape==='doubleArrowLine'?'arrow':'none'),
  startDefault:data.shape==='doubleArrowLine'?'arrow':'none'};
}
export function nodeFont(data={}){
 const px=Math.round((data.size??12)*4/3);
 return {px,lineHeight:Math.round(px*1.5),weight:data.bold?700:400,family:'"'+(data.font??'맑은 고딕')+'", "Malgun Gothic", "Noto Sans KR", sans-serif',color:data.textColor??'#172b4d',
  css:(data.bold?'700 ':'')+px+'px "'+(data.font??'맑은 고딕')+'", "Malgun Gothic", "Noto Sans KR", sans-serif'};
}
function rich(value) {
 if(typeof value?.text==='string')return value.text;
 return (value?.content??[]).map(rich).join(value?.type==='doc'?'\n':'');
}
export function decode(snapshot) {
 if(snapshot?.format===FORMAT)return {...validate(snapshot),converted:false};
 const store=snapshot?.document?.store;
 if(!store||typeof store!=='object')throw new Error('지원하지 않는 문서입니다.');
 const values=Object.values(store),pages=values.filter(v=>v.typeName==='page');
 if(pages.length>1)throw new Error('여러 페이지의 tldraw 문서는 자동 변환하지 않습니다. 원본을 보존했습니다.');
 const shapes=values.filter(v=>v.typeName==='shape');
 if(shapes.some(v=>!['geo','text','arrow'].includes(v.type)||v.rotation))throw new Error('자유선·회전 등 자동 변환할 수 없는 도형이 있습니다. 원본을 보존했습니다.');
 const nodes=shapes.filter(v=>v.type!=='arrow').map(v=>{
  if(v.parentId&&!v.parentId.startsWith('page:'))throw new Error('그룹 도형은 자동 변환하지 않습니다.');
  const p=v.props??{},shape=v.type==='text'?'text':({'rectangle':'rectangle','diamond':'diamond','ellipse':'ellipse'}[p.geo]);
  if(!shape)throw new Error('자동 변환할 수 없는 도형 종류입니다.');
  if(v.type==='text'&&!text(p.text??rich(p.richText)))throw new Error('문자 도형을 확인해 주세요.');
  return {...node(p.text??rich(p.richText),v.x,v.y,shape,Object.hasOwn(COLORS,p.color)?p.color:'blue',v.id),width:p.w??220,height:p.h??90};
 });
 const nodeMap=new Map(nodes.map(n=>[n.id,n]));
 const bindings=values.filter(v=>v.typeName==='binding'&&v.type==='arrow');
 const edges=shapes.filter(v=>v.type==='arrow').map(v=>{
  const p=v.props??{},start=bindings.find(b=>b.fromId===v.id&&b.props?.terminal==='start'),end=bindings.find(b=>b.fromId===v.id&&b.props?.terminal==='end');
  const find=(point)=>{
   if(!point||!finite(point.x)||!finite(point.y))return null;
   const x=v.x+point.x,y=v.y+point.y;
   const distances=nodes.flatMap(n=>['top','bottom','left','right'].map(side=>{
    const [px,py]=anchor(n,side);return {id:n.id,side,d:Math.hypot(px-x,py-y)};
   })).sort((a,b)=>a.d-b.d);
   const near=distances[0];
   if(!near||near.d>40||distances[1]&&distances[1].id!==near.id&&Math.abs(distances[1].d-near.d)<1)return null;
   return near;
  };
  const a=start&&nodeMap.has(start.toId)?{id:start.toId,side:'bottom'}:find(p.start);
  const b=end&&nodeMap.has(end.toId)?{id:end.toId,side:'top'}:find(p.end);
  if(!a||!b||p.bend)throw new Error('연결 위치가 모호하거나 곡선인 화살표는 자동 변환하지 않습니다.');
  return edge(a.id,b.id,p.text??rich(p.richText),v.id,a.side,b.side);
 });
 return {...validate({format:FORMAT,version:1,nodes,edges}),converted:true};
}
export function anchor(n,side) {
 const {x,y}=n.position,w=n.width??220,h=n.height??90;
 return side==='top'?[x+w/2,y]:side==='bottom'?[x+w/2,y+h]:side==='left'?[x,y+h/2]:[x+w,y+h/2];
}
/** 연결선 경로(화면·PNG 공통): 꺾은선은 가운데에서 꺾고, 곡선은 나가는 방향으로 휘게 한다. */
export function edgePath(x1,y1,x2,y2,sourceSide,targetSide,line='step'){
 if(line==='straight')return `M ${x1} ${y1} L ${x2} ${y2}`;
 if(line==='curve'){
  const d=Math.max(40,Math.hypot(x2-x1,y2-y1)/2.5);
  const off=side=>({left:[-d,0],right:[d,0],top:[0,-d],bottom:[0,d]}[side]??[0,0]);
  const [ax,ay]=off(sourceSide),[bx,by]=off(targetSide);
  return `M ${x1} ${y1} C ${x1+ax} ${y1+ay} ${x2+bx} ${y2+by} ${x2} ${y2}`;
 }
 const horizontal=['left','right'].includes(sourceSide);
 return horizontal?'M '+x1+' '+y1+' H '+((x1+x2)/2)+' V '+y2+' H '+x2:'M '+x1+' '+y1+' V '+((y1+y2)/2)+' H '+x2+' V '+y2;
}
const esc = s => String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&apos;'}[c]));
export const FONT_SIZE=16, LINE_HEIGHT=24, PADDING_X=16, PADDING_Y=12, BLEED=20;
export const FONT='16px "Malgun Gothic", "Noto Sans KR", sans-serif';
let measuringContext;
export function textWidth(value,font=FONT,px=FONT_SIZE) {
 if(typeof document!=='undefined'){
  measuringContext??=document.createElement('canvas').getContext('2d');
  if(measuringContext){measuringContext.font=font;return measuringContext.measureText(value).width;}
 }
 // Conservative non-browser fallback for model validation/tests.
 return Array.from(value).reduce((sum,c)=>sum+(/\p{Mark}/u.test(c)?0:/\p{Extended_Pictographic}/u.test(c)?px*2:px),0);
}
export function wrapKoreanAwareText(value,maxWidth,font=FONT,px=FONT_SIZE) {
 const textWidth=line=>measure(line,font,px);
 const result=[];
 for(const paragraph of String(value).split('\n')){
  if(!paragraph){result.push('');continue;}
  let line='';
  // Keep words when they fit; split long Korean/Latin tokens by Unicode code point.
  for(const token of paragraph.match(/\S+\s*|\s+/gu)??[]){
   if(line&&textWidth(line+token)>maxWidth){result.push(line.trimEnd());line='';}
   for(const character of token){
    if(line&&textWidth(line+character)>maxWidth){result.push(line.trimEnd());line='';}
    line+=character;
   }
  }
  result.push(line.trimEnd());
 }
 return result.length?result:[''];
}
const measure=(value,font,px)=>textWidth(value,font,px);
export function computeNodeAutoFitBox(n) {
 const f=nodeFont(n.data);
 if(LINE_SHAPES.has(n.data.shape)){
  // 선 도형은 글이 있으면 선 위에 한 줄로 쓰고, 상자 크기는 사용자가 끈 그대로 둔다.
  const lines=n.data.label?wrapKoreanAwareText(n.data.label,Math.max(32,(n.width??220)-8),f.css,f.px):[];
  return {width:n.width??220,height:n.height??40,lines,lineHeight:f.lineHeight,factor:1,textWidth:0,textHeight:lines.length*f.lineHeight,font:f};
 }
 const factor=textFactor(n.data.shape);
 const minWidth=Math.max(60,n.width??220),maxWidth=Math.max(360,minWidth);
 const lines=wrapKoreanAwareText(n.data.label,Math.max(32,Math.floor(maxWidth*factor-2*PADDING_X)),f.css,f.px);
 const longest=Math.max(0,...lines.map(line=>textWidth(line,f.css,f.px)));
 const width=Math.max(minWidth,Math.ceil((longest+2*PADDING_X)/factor));
 const height=Math.max(n.height??90,Math.ceil((lines.length*f.lineHeight+2*PADDING_Y)/factor));
 return {width,height,lines,lineHeight:f.lineHeight,factor,textWidth:longest,textHeight:lines.length*f.lineHeight,font:f};
}
export function layoutGraph(graph) {
 return {...graph,nodes:graph.nodes.map(n=>{const box=computeNodeAutoFitBox(n);return {...n,width:box.width,height:box.height};})};
}
export function edgeLabelBox(e,nodes) {
 const a=nodes.find(n=>n.id===e.source),b=nodes.find(n=>n.id===e.target);
 const [x1,y1]=anchor(a,e.sourceHandle),[x2,y2]=anchor(b,e.targetHandle);
 const lines=wrapKoreanAwareText(e.label??'',240);
 const width=Math.max(...lines.map(l=>textWidth(l)),0)+16,height=lines.length*LINE_HEIGHT+12;
 return {x:(x1+x2)/2,y:(y1+y2)/2,width,height,lines};
}
export function getDiagramBounds(graph) {
 const {nodes,edges}=layoutGraph(graph);
 if(!nodes.length)throw new Error('내보낼 도형이 없습니다.');
 const boxes=nodes.map(n=>({x:n.position.x,y:n.position.y,width:n.width,height:n.height}));
 for(const e of edges)if(e.label){const b=edgeLabelBox(e,nodes);boxes.push({...b,x:b.x-b.width/2,y:b.y-b.height/2});}
 const x=Math.min(...boxes.map(b=>b.x))-BLEED,y=Math.min(...boxes.map(b=>b.y))-BLEED;
 const width=Math.max(...boxes.map(b=>b.x+b.width))-x+BLEED,height=Math.max(...boxes.map(b=>b.y+b.height))-y+BLEED;
 if(width*height>12_000_000||width>8000||height>8000)throw new Error('이미지가 너무 큽니다. 도형 배치를 줄여 주세요.');
 return {x,y,width,height};
}
function svgLines(lines,x,y,f=nodeFont()) {
 return lines.map((line,i)=>'<text xml:space="preserve" x="'+x+'" y="'+(y+(i-(lines.length-1)/2)*f.lineHeight)+'" text-anchor="middle" dominant-baseline="central" font-size="'+f.px+'" font-weight="'+f.weight+'" font-family="'+esc(f.family.replaceAll('"',''))+'" fill="'+f.color+'">'+esc(line)+'</text>').join('');
}
/** 도형 한 개의 SVG(화면 노드와 PNG가 같은 모양을 쓴다). 화살표 머리는 defs로 따로 모은다. */
export function nodeSvg(n,x,y,w,h,defs){
 const p=nodePaint(n.data),d=shapePath(n.data.shape,x,y,w,h);
 let markers='';
 if(LINE_SHAPES.has(n.data.shape)){
  const start=n.data.lineStart??p.startDefault,end=p.end,key='m'+String(n.id).replace(/[^A-Za-z0-9_-]/g,'');
  if(start!=='none'){defs.push(markerSvg(key+'s',start,p.stroke));markers+=' marker-start="url(#'+key+'s)"';}
  if(end!=='none'){defs.push(markerSvg(key+'e',end,p.stroke));markers+=' marker-end="url(#'+key+'e)"';}
 }
 return (d?'<path d="'+d+'" fill="'+(p.fill==='none'?'none':p.fill)+'" fill-rule="evenodd" stroke="'+(p.stroke==='none'?'none':p.stroke)+'" stroke-width="'+p.width+'"'+(p.dash?' stroke-dasharray="'+p.dash+'"':'')+' stroke-linejoin="round"'+markers+'/>':'');
}
export function svg(snapshot) {
 const checked=validate(snapshot);
 const graph=layoutGraph(checked.mindmap&&!checked.nodes.length?mindmapGraph(checked.mindmap):checked),{nodes,edges}=graph,bounds=getDiagramBounds(graph);
 const defs=[];
 const drawnEdges=edges.map(e=>{
  const s=e.data??EDGE_DEFAULT,key='e'+String(e.id).replace(/[^A-Za-z0-9_-]/g,'');
  const a=nodes.find(n=>n.id===e.source),b=nodes.find(n=>n.id===e.target),[x1,y1]=anchor(a,e.sourceHandle),[x2,y2]=anchor(b,e.targetHandle);
  const d=edgePath(x1,y1,x2,y2,e.sourceHandle,e.targetHandle,s.line);
  let markers='';
  if(s.start!=='none'){defs.push(markerSvg(key+'s',s.start,s.color));markers+=' marker-start="url(#'+key+'s)"';}
  if(s.end!=='none'){defs.push(markerSvg(key+'e',s.end,s.color));markers+=' marker-end="url(#'+key+'e)"';}
  const label=edgeLabelBox(e,nodes);
  return '<path d="'+d+'" fill="none" stroke="'+s.color+'" stroke-width="'+s.width+'"'+(dashArray(s.dash)?' stroke-dasharray="'+dashArray(s.dash)+'"':'')+markers+'/>'+(e.label?'<rect x="'+(label.x-label.width/2)+'" y="'+(label.y-label.height/2)+'" width="'+label.width+'" height="'+label.height+'" fill="white"/>'+svgLines(label.lines,label.x,label.y):'');
 }).join('');
 const drawnNodes=nodes.map(n=>{
  const {x,y}=n.position,w=n.width,h=n.height,box=computeNodeAutoFitBox(n);
  const ty=LINE_SHAPES.has(n.data.shape)?y+h/2-box.lineHeight*0.7:y+h/2;
  return nodeSvg(n,x,y,w,h,defs)+svgLines(box.lines,x+w/2,ty,nodeFont(n.data));
 }).join('');
 return {width:bounds.width,height:bounds.height,source:'<svg xmlns="http://www.w3.org/2000/svg" width="'+bounds.width+'" height="'+bounds.height+'" viewBox="'+bounds.x+' '+bounds.y+' '+bounds.width+' '+bounds.height+'"><defs>'+defs.join('')+'</defs><rect x="'+bounds.x+'" y="'+bounds.y+'" width="'+bounds.width+'" height="'+bounds.height+'" fill="white"/>'+drawnEdges+drawnNodes+'</svg>'};
}
