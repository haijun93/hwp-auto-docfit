// Application-owned flow document model. React Flow (MIT) renders this model.
import {FONTS,validateTable} from './table.js';
export const FORMAT = 'docfit-flow';
export const COLORS = {blue:'#dbeafe',green:'#dcfce7',orange:'#ffedd5',yellow:'#fef9c3',white:'#ffffff'};
export const templates = {
 general:{name:'일반 행정업무 처리',steps:['접수','검토','결재','시행','완료']},
 contract:{name:'계약 및 발주',steps:['수요 발생','발주 검토','계약 방법 결정','계약 체결','검사·검수']},
 direct_contract:{name:'수의계약 검토',steps:['계약 대상 확인','금액·사유 검토','적정성 판단','계약 진행']},
 budget:{name:'예산 집행',steps:['집행 계획','예산 확인','품의','지출 원인행위','대금 지급']},
 subsidy:{name:'지방보조금 관리',steps:['공모·신청','심사','교부 결정','사업 수행','정산','사후관리']},
 construction:{name:'공사 관리',steps:['사업 계획','설계','발주','착공','준공 검사','대금 지급']},
 permit:{name:'인허가 처리',steps:['신청 접수','요건 검토','보완 여부 판단','승인·반려 결정','결과 통보']},
 approval:{name:'보고 및 결재',steps:['자료 작성','담당 검토','팀장 검토','부서장 결재','시행']},
 incident:{name:'사고·민원 대응',steps:['상황 접수','긴급성 판단','초기 조치','보고','사후관리']},
 complaint:{name:'민원 처리',steps:['민원 접수','담당자 배정','내용 검토','보완 요청','보완 내용 재검토','처리 결과 통보']},
};
export const id = () => crypto.randomUUID();
export function node(label, x, y, shape='rectangle',color='blue',identity=id()) {
 return {id:identity,type:'flow',position:{x,y},data:{label,shape,color},width:220,height:90};
}
export function edge(source,target,label='',identity=id(),sourceHandle='bottom',targetHandle='top') {
 return {id:identity,source,target,sourceHandle,targetHandle,type:'smoothstep',label,
 markerEnd:{type:'arrowclosed',color:'#334155'},style:{stroke:'#334155',strokeWidth:2}};
}
export function template(key) {
 const t=templates[key];if(!t)throw new Error('예시 서식을 확인해 주세요.');
 const nodes=t.steps.map((s,i)=>node(s,100,60+i*160,i===2&&key==='complaint'?'diamond':'rectangle',i===t.steps.length-1?'green':'blue'));
 const links=key==='complaint'?[[0,1],[1,2],[2,3,'예'],[3,4],[4,2,'재검토'],[2,5,'아니오']]:nodes.slice(1).map((_,i)=>[i,i+1]);
 if(key==='complaint'){nodes[3].position={x:-250,y:540};nodes[4].position={x:-250,y:700};nodes[5].position={x:450,y:540};}
 const edges=links.map(([a,b,label])=>edge(nodes[a].id,nodes[b].id,label||'',id(),a===4?'right':a===2&&b===3?'left':a===2&&b===5?'right':'bottom',a===4?'left':'top'));
 return {nodes,edges,name:t.name};
}
const finite = v => typeof v==='number' && Number.isFinite(v) && Math.abs(v)<=1e6;
const text = (v,max=2000) => typeof v==='string'&&v.length<=max;
export function validate(snapshot) {
 if(snapshot?.format!==FORMAT||snapshot.version!==1||!Array.isArray(snapshot.nodes)||!Array.isArray(snapshot.edges))throw new Error('지원하지 않는 흐름도 형식입니다.');
 if(snapshot.nodes.length>1000||snapshot.edges.length>2000)throw new Error('도형 또는 연결선 수가 제한을 넘습니다.');
 const ids=new Set();
 const nodes=snapshot.nodes.map(n=>{
  if(!text(n.id,100)||!n.id||ids.has(n.id)||!finite(n.position?.x)||!finite(n.position?.y)||!text(n.data?.label)||!['rectangle','diamond','ellipse','text'].includes(n.data.shape)||!Object.hasOwn(COLORS,n.data.color))throw new Error('도형 데이터가 올바르지 않습니다.');
  ids.add(n.id);
  const style=nodeTextStyle(n.data);
  const w=n.width??220,h=n.height??90;
  if(!finite(w)||!finite(h)||w<30||h<30||w>100000||h>100000)throw new Error('도형 크기가 올바르지 않습니다.');
  const made=node(n.data.label,n.position.x,n.position.y,n.data.shape,n.data.color,n.id);
  return {...made,data:{...made.data,...style},width:w,height:h};
 });
 const nodeIds=new Set(ids);
 const edges=snapshot.edges.map(e=>{
  if(!text(e.id,100)||!e.id||ids.has(e.id)||!nodeIds.has(e.source)||!nodeIds.has(e.target)||!text(e.label??'',300))throw new Error('연결선 데이터가 올바르지 않습니다.');
  ids.add(e.id);
  const handles=['top','bottom','left','right'];
  if(!handles.includes(e.sourceHandle)||!handles.includes(e.targetHandle))throw new Error('연결 위치를 확인해 주세요.');
  return edge(e.source,e.target,e.label??'',e.id,e.sourceHandle,e.targetHandle);
 });
 const table=snapshot.table==null?undefined:validateTable(snapshot.table);
 return table?{format:FORMAT,version:1,nodes,edges,table}:{format:FORMAT,version:1,nodes,edges};
}
/** 도형 글자 서식(선택): font(글꼴), size(pt), bold, textColor. 값이 없으면 예전 기본(맑은 고딕 12pt). */
export const TEXT_FONTS=FONTS;
export function nodeTextStyle(data){
 const style={};
 if(data.font!==undefined){if(!FONTS.includes(data.font))throw new Error('도형 글꼴을 확인해 주세요.');style.font=data.font;}
 if(data.size!==undefined){if(typeof data.size!=='number'||!(data.size>=6&&data.size<=40))throw new Error('도형 글꼴 크기를 확인해 주세요.');style.size=data.size;}
 if(data.bold!==undefined){if(typeof data.bold!=='boolean')throw new Error('도형 굵게 값을 확인해 주세요.');style.bold=data.bold;}
 if(data.textColor!==undefined){if(typeof data.textColor!=='string'||!/^#[0-9A-Fa-f]{6}$/.test(data.textColor))throw new Error('도형 글자색을 확인해 주세요.');style.textColor=data.textColor;}
 return style;
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
  const find=(point,terminal)=>{
   if(!point||!finite(point.x)||!finite(point.y))return null;
   const x=v.x+point.x,y=v.y+point.y;
   const distances=nodes.flatMap(n=>['top','bottom','left','right'].map(side=>{
    const [px,py]=anchor(n,side);return {id:n.id,side,d:Math.hypot(px-x,py-y)};
   })).sort((a,b)=>a.d-b.d);
   const near=distances[0];
   if(!near||near.d>40||distances[1]&&distances[1].id!==near.id&&Math.abs(distances[1].d-near.d)<1)return null;
   return near;
  };
  const a=start&&nodeMap.has(start.toId)?{id:start.toId,side:'bottom'}:find(p.start,'start');
  const b=end&&nodeMap.has(end.toId)?{id:end.toId,side:'top'}:find(p.end,'end');
  if(!a||!b||p.bend)throw new Error('연결 위치가 모호하거나 곡선인 화살표는 자동 변환하지 않습니다.');
  return edge(a.id,b.id,p.text??rich(p.richText),v.id,a.side,b.side);
 });
 return {...validate({format:FORMAT,version:1,nodes,edges}),converted:true};
}
export function anchor(n,side) {
 const {x,y}=n.position,w=n.width??220,h=n.height??90;
 return side==='top'?[x+w/2,y]:side==='bottom'?[x+w/2,y+h]:side==='left'?[x,y+h/2]:[x+w,y+h/2];
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
 const factor=n.data.shape==='diamond'?.5:n.data.shape==='ellipse'?.7:1;
 const minWidth=Math.max(120,n.width??220),maxWidth=Math.max(360,minWidth);
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
 const width=Math.max(...lines.map(textWidth),0)+16,height=lines.length*LINE_HEIGHT+12;
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
export function svg(snapshot) {
 const graph=layoutGraph(validate(snapshot)),{nodes,edges}=graph,bounds=getDiagramBounds(graph);
 const drawnEdges=edges.map(e=>{
  const a=nodes.find(n=>n.id===e.source),b=nodes.find(n=>n.id===e.target),[x1,y1]=anchor(a,e.sourceHandle),[x2,y2]=anchor(b,e.targetHandle);
  const horizontal=['left','right'].includes(e.sourceHandle);
  const d=horizontal?'M '+x1+' '+y1+' H '+((x1+x2)/2)+' V '+y2+' H '+x2:'M '+x1+' '+y1+' V '+((y1+y2)/2)+' H '+x2+' V '+y2;
  const label=edgeLabelBox(e,nodes);
  return '<path d="'+d+'" fill="none" stroke="#334155" stroke-width="2" marker-end="url(#arrow)"/>'+(e.label?'<rect x="'+(label.x-label.width/2)+'" y="'+(label.y-label.height/2)+'" width="'+label.width+'" height="'+label.height+'" fill="white"/>'+svgLines(label.lines,label.x,label.y):'');
 }).join('');
 const drawnNodes=nodes.map(n=>{
  const {x,y}=n.position,w=n.width,h=n.height,c=COLORS[n.data.color];
  const shape=n.data.shape==='text'?'':n.data.shape==='diamond'?'<polygon points="'+(x+w/2)+','+y+' '+(x+w)+','+(y+h/2)+' '+(x+w/2)+','+(y+h)+' '+x+','+(y+h/2)+'"':n.data.shape==='ellipse'?'<ellipse cx="'+(x+w/2)+'" cy="'+(y+h/2)+'" rx="'+w/2+'" ry="'+h/2+'"':'<rect x="'+x+'" y="'+y+'" width="'+w+'" height="'+h+'" rx="8"';
  return (shape?shape+' fill="'+c+'" stroke="#475569" stroke-width="2"/>':'')+svgLines(computeNodeAutoFitBox(n).lines,x+w/2,y+h/2,nodeFont(n.data));
 }).join('');
 return {width:bounds.width,height:bounds.height,source:'<svg xmlns="http://www.w3.org/2000/svg" width="'+bounds.width+'" height="'+bounds.height+'" viewBox="'+bounds.x+' '+bounds.y+' '+bounds.width+' '+bounds.height+'"><defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="#334155"/></marker></defs><rect x="'+bounds.x+'" y="'+bounds.y+'" width="'+bounds.width+'" height="'+bounds.height+'" fill="white"/>'+drawnEdges+drawnNodes+'</svg>'};
}
