// Application-owned flow document model. React Flow (MIT) renders this model.
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
  const w=n.width??220,h=n.height??90;
  if(!finite(w)||!finite(h)||w<30||h<30||w>2000||h>2000)throw new Error('도형 크기가 올바르지 않습니다.');
  return {...node(n.data.label,n.position.x,n.position.y,n.data.shape,n.data.color,n.id),width:w,height:h};
 });
 const nodeIds=new Set(ids);
 const edges=snapshot.edges.map(e=>{
  if(!text(e.id,100)||!e.id||ids.has(e.id)||!nodeIds.has(e.source)||!nodeIds.has(e.target)||!text(e.label??'',300))throw new Error('연결선 데이터가 올바르지 않습니다.');
  ids.add(e.id);
  const handles=['top','bottom','left','right'];
  if(!handles.includes(e.sourceHandle)||!handles.includes(e.targetHandle))throw new Error('연결 위치를 확인해 주세요.');
  return edge(e.source,e.target,e.label??'',e.id,e.sourceHandle,e.targetHandle);
 });
 return {format:FORMAT,version:1,nodes,edges};
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
export function svg(snapshot) {
 const {nodes,edges}=validate(snapshot);
 if(!nodes.length)throw new Error('내보낼 도형이 없습니다.');
 const minX=Math.min(...nodes.map(n=>n.position.x))-40,minY=Math.min(...nodes.map(n=>n.position.y))-40;
 const width=Math.max(...nodes.map(n=>n.position.x+n.width))-minX+40,height=Math.max(...nodes.map(n=>n.position.y+n.height))-minY+40;
 if(width*height>12_000_000||width>8000||height>8000)throw new Error('이미지가 너무 큽니다. 도형 배치를 줄여 주세요.');
 const label=(str,x,y)=>String(str).split('\n').flatMap(line=>Array.from(line).reduce((a,c,i)=>(i%20===0?a.push(c):a[a.length-1]+=c,a),[])).map((line,i,all)=>'<text x="'+x+'" y="'+(y+(i-(all.length-1)/2)*22)+'" text-anchor="middle" dominant-baseline="central" font-size="16" font-family="Malgun Gothic, Noto Sans KR, sans-serif" fill="#172b4d">'+esc(line)+'</text>').join('');
 const drawnEdges=edges.map(e=>{
  const a=nodes.find(n=>n.id===e.source),b=nodes.find(n=>n.id===e.target),[x1,y1]=anchor(a,e.sourceHandle),[x2,y2]=anchor(b,e.targetHandle);
  const horizontal=['left','right'].includes(e.sourceHandle);
  const d=horizontal?'M '+x1+' '+y1+' H '+((x1+x2)/2)+' V '+y2+' H '+x2:'M '+x1+' '+y1+' V '+((y1+y2)/2)+' H '+x2+' V '+y2;
  return '<path d="'+d+'" fill="none" stroke="#334155" stroke-width="2" marker-end="url(#arrow)"/>'+label(e.label,(x1+x2)/2+12,(y1+y2)/2-14);
 }).join('');
 const drawnNodes=nodes.map(n=>{
  const {x,y}=n.position,w=n.width,h=n.height,c=COLORS[n.data.color];
  const shape=n.data.shape==='text'?'':n.data.shape==='diamond'?'<polygon points="'+(x+w/2)+','+y+' '+(x+w)+','+(y+h/2)+' '+(x+w/2)+','+(y+h)+' '+x+','+(y+h/2)+'"':n.data.shape==='ellipse'?'<ellipse cx="'+(x+w/2)+'" cy="'+(y+h/2)+'" rx="'+w/2+'" ry="'+h/2+'"':'<rect x="'+x+'" y="'+y+'" width="'+w+'" height="'+h+'" rx="8"';
  return (shape?shape+' fill="'+c+'" stroke="#475569" stroke-width="2"/>':'')+label(n.data.label,x+w/2,y+h/2);
 }).join('');
 return {width,height,source:'<svg xmlns="http://www.w3.org/2000/svg" width="'+width+'" height="'+height+'" viewBox="'+minX+' '+minY+' '+width+' '+height+'"><defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="#334155"/></marker></defs><rect x="'+minX+'" y="'+minY+'" width="'+width+'" height="'+height+'" fill="white"/>'+drawnEdges+drawnNodes+'</svg>'};
}
