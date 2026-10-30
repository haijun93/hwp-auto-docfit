import React,{useRef,useState,useEffect,createContext,useContext} from 'react';
import {createRoot} from 'react-dom/client';
import {ReactFlow,ReactFlowProvider,Background,Controls,MiniMap,Handle,Position,ConnectionMode,applyNodeChanges,applyEdgeChanges,NodeResizer,BaseEdge,useReactFlow,ViewportPortal,reconnectEdge} from '@xyflow/react';
import {autoRoute,nodeAt,facingSides,smartGuides} from './magnet.js';
import {freehandNode,freehandPath,withBackground,withoutBackground,fitSize,paintStyle,BACKGROUND_ID,isImageSrc} from './paint.js';
import {defaultLayers,addLayer,updateLayer,moveLayer,removeLayer,assignLayer,layeredNodes,layeredEdges,layerOf} from './layers.js';
import '@xyflow/react/dist/style.css';
import './style.css';
import {FORMAT,PALETTE,templates,template,node,edge,id,decode,validate,svg,layoutGraph,computeNodeAutoFitBox,edgeLabelBox,LINE_HEIGHT,nodeFont,nodePaint,edgePath,EDGE_DEFAULT,rotationFromPointer,normalizeRotation} from './model.js';
import {SHAPE_GROUPS,SHAPES,LINE_SHAPES,shapePath,DASHES,MARKERS,dashArray} from './shapes.js';
import {sampleMindmap,mindmapGraph,addChild,addSibling,removeNode,updateNode,moveNode,findNode,positionMindmap,reparentNode,autoLayoutMindmap,restyleNodes,MINDMAP_SHAPES,MINDMAP_SCOPES,MINDMAP_THEME_SHAPES,MINDMAP_PALETTES,MINDMAP_GROUNDS,themeOf,clearBranchStyles} from './mindmap.js';
import {FONTS,registerFonts,ARROWS,DOWN_ARROWS,FLOW_PRESETS,MAX_FLOW_STEPS,MAX_FLOW_ROWS,MAX_ROWS,MAX_COLS,MAX_ORG,ROLE_NAMES,BORDER_TYPES,BORDER_WIDTHS,BORDER_NAMES,
 flowTable,gridTable,orgTable,barTable,flowDetails,resizeFlow,resizeFlowRows,insertStep,removeStep,resizeGrid,insertRow,removeRow,insertCol,removeCol,resizeOrg,
 setStyle,setBorder,exportSpec,cssOf,cssBorder,
 CATALOG_SCOPES,buildCatalogGrid,applyCatalogStructure,setCatalogCellText,setCatalogStyle,setCatalogBorder,buildCatalogEdits,
 isTaskTable,isFixedCalloutCategory,resizeTaskGrid} from './table.js';

const TITLE='다이어그램·마인드맵';
const newName=mode=>'새 '+(mode==='mindmap'?'마인드맵':mode==='paint'?'그림':'다이어그램');
function send(message){
 const host=window.chrome?.webview;
 if(window.parent!==window)window.parent.postMessage(message,window.location.origin);
 else if(host)host.postMessage(JSON.stringify(message));
}
const HistoryContext=createContext(()=>{});
const safeId=v=>String(v).replace(/[^A-Za-z0-9_-]/g,'');

/** 화살표 머리(<marker>)를 React 요소로 그린다(HTML 문자열을 끼워 넣지 않는다). */
function Marker({id:markerId,kind,color}){
 if(!kind||kind==='none')return null;
 const ref=kind==='circle'||kind==='diamond'?5:9;
 return <marker id={markerId} viewBox="0 0 10 10" refX={ref} refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse" markerUnits="userSpaceOnUse">
  {kind==='arrow'&&<path d="M 0 0 L 10 5 L 0 10 z" fill={color}/>}
  {kind==='open'&&<path d="M 1 1 L 9 5 L 1 9" fill="none" stroke={color} strokeWidth="1.6"/>}
  {kind==='stealth'&&<path d="M 0 0 L 10 5 L 0 10 L 3 5 z" fill={color}/>}
  {kind==='diamond'&&<path d="M 0 5 L 5 0 L 10 5 L 5 10 z" fill={color}/>}
  {kind==='circle'&&<circle cx="5" cy="5" r="4" fill={color}/>}
 </marker>;
}

/** 회전 손잡이(PPT처럼 도형 위의 동그라미): 끌면 0~359° 돌리고, Shift를 누르면 15°씩. */
function RotateHandle({nodeId,rotation}){
 const {updateNodeData}=useReactFlow();const checkpoint=useContext(HistoryContext);
 const down=e=>{
  e.stopPropagation();e.preventDefault();
  const box=e.currentTarget.closest('.react-flow__node')?.getBoundingClientRect();if(!box)return;
  const cx=box.left+box.width/2,cy=box.top+box.height/2;checkpoint();
  const move=ev=>updateNodeData(nodeId,{rotation:rotationFromPointer(cx,cy,ev.clientX,ev.clientY,ev.shiftKey)});
  const up=()=>{window.removeEventListener('pointermove',move);window.removeEventListener('pointerup',up);};
  window.addEventListener('pointermove',move);window.addEventListener('pointerup',up);
 };
 return <div className="rotate-handle nodrag" title={`회전 ${rotation??0}° (끌기, Shift: 15°씩)`} aria-label="도형 회전" onPointerDown={down}/>;
}
/** 회전 틀: 도형·연결점·회전 손잡이를 함께 가운데 중심으로 돌린다(연결점 위치도 돈 자리로 잡힌다). */
const Rotated=({data,w,h,children})=><div className="node-rot" style={{width:w,height:h,transform:data.rotation?`rotate(${data.rotation}deg)`:undefined}}>{children}</div>;

/** 도형 노드: PPT 도형 경로를 SVG로 그리고 글을 가운데에 얹는다. 선 도형은 화살표 머리를 붙인다. */
function FlowNode({id:nodeId,data,selected,width,height}){
 const box=computeNodeAutoFitBox({data,width,height}),f=nodeFont(data),p=nodePaint(data);
 const resizeStart=useContext(HistoryContext);
 const w=width??220,h=height??90,inset=Math.max(1,p.width/2+1),line=LINE_SHAPES.has(data.shape);
 const key='n'+safeId(nodeId);
 if(data.shape==='image')return <>{!data.background&&<NodeResizer onResizeStart={resizeStart} isVisible={selected} minWidth={20} minHeight={20} keepAspectRatio/>}
  <Rotated data={data} w={w} h={h}>{selected&&!data.background&&<RotateHandle nodeId={nodeId} rotation={data.rotation}/>}
  <div className="node-body shape-image" style={{width:w,height:h}}><img src={data.src} alt="" draggable={false} style={{width:'100%',height:'100%',display:'block',pointerEvents:'none'}}/></div></Rotated></>;
 if(data.shape==='freehand')return <><NodeResizer onResizeStart={resizeStart} isVisible={selected} minWidth={8} minHeight={8}/>
  <Rotated data={data} w={w} h={h}>{selected&&<RotateHandle nodeId={nodeId} rotation={data.rotation}/>}
  <div className="node-body shape-freehand" style={{width:w,height:h}}><svg className="shape-svg" width={w} height={h} viewBox={`0 0 ${w} ${h}`} aria-hidden="true">
   <path d={freehandPath(data.points,0,0,w,h)} fill="none" stroke={p.stroke==='none'?'#111827':p.stroke} strokeWidth={p.width} strokeDasharray={p.dash||undefined} strokeLinecap="round" strokeLinejoin="round"/></svg></div></Rotated></>;
 const start=data.lineStart??p.startDefault,end=p.end;
 return <><NodeResizer onResizeStart={resizeStart} isVisible={selected} minWidth={line?20:40} minHeight={line?10:30}/>
  <Rotated data={data} w={w} h={h}>
  {Object.entries(Position).map(([k,value])=><Handle key={k} id={value} type="source" position={value}/>)}
  {selected&&<RotateHandle nodeId={nodeId} rotation={data.rotation}/>}
  <div className={'node-body shape-'+data.shape} style={{width:w,height:h}}>
   <svg className="shape-svg" width={w} height={h} viewBox={`0 0 ${w} ${h}`} aria-hidden="true">
    {line&&<defs><Marker id={key+'s'} kind={start} color={p.stroke}/><Marker id={key+'e'} kind={end} color={p.stroke}/></defs>}
    {data.shape!=='text'&&<path d={shapePath(data.shape,inset,inset,Math.max(1,w-2*inset),Math.max(1,h-2*inset))} fill={p.fill} fillRule="evenodd"
     stroke={p.stroke} strokeWidth={p.width} strokeDasharray={p.dash||undefined} strokeLinejoin="round"
     markerStart={line&&start!=='none'?`url(#${key}s)`:undefined} markerEnd={line&&end!=='none'?`url(#${key}e)`:undefined}/>}
   </svg>
   <span className="node-lines" style={{fontFamily:f.family,fontSize:f.px,lineHeight:f.lineHeight+'px',fontWeight:f.weight,color:f.color,marginTop:line?-f.lineHeight*1.4:0}}>
    {box.lines.map((l,i)=><span key={i} style={{display:'block',height:f.lineHeight}}>{l||' '}</span>)}
   </span>
  </div></Rotated></>;
}
/** 연결선: 꺾은선·직선·곡선, 색·굵기·선 모양, 양 끝 화살표 머리. */
function FlowEdge(props){
 const flow=useReactFlow(),nodes=flow.getNodes(),a=nodes.find(n=>n.id===props.source),b=nodes.find(n=>n.id===props.target);
 if(!a||!b)return null;
 const s=props.data??EDGE_DEFAULT,key='e'+safeId(props.id);
 const e={...props,sourceHandle:props.sourcePosition,targetHandle:props.targetPosition};
 const box=edgeLabelBox(e,nodes);
 const path=edgePath(props.sourceX,props.sourceY,props.targetX,props.targetY,props.sourcePosition,props.targetPosition,s.line);
 return <><defs><Marker id={key+'s'} kind={s.start} color={s.color}/><Marker id={key+'e'} kind={s.end} color={s.color}/></defs>
  <BaseEdge id={props.id} path={path} markerStart={s.start!=='none'?`url(#${key}s)`:undefined} markerEnd={s.end!=='none'?`url(#${key}e)`:undefined}
   style={{stroke:s.color,strokeWidth:props.selected?s.width+1.5:s.width,strokeDasharray:dashArray(s.dash)||undefined}}/>
  {props.label&&<g><rect x={box.x-box.width/2} y={box.y-box.height/2} width={box.width} height={box.height} fill="white"/>
  {box.lines.map((line,i)=><text xmlSpace="preserve" key={i} x={box.x} y={box.y+(i-(box.lines.length-1)/2)*LINE_HEIGHT} textAnchor="middle" dominantBaseline="central" style={{fontSize:16,fontFamily:'"Malgun Gothic","Noto Sans KR",sans-serif'}}>{line}</text>)}</g>}</>;
}
const edgeTypes={smoothstep:FlowEdge};
const nodeTypes={flow:FlowNode};

/** 지도 테마 모양 단추의 작은 그림(가운데 주제 + 큰 가지 + 작은 가지). */
function ThemeShapeIcon({kind}){
 const c='#2563eb',soft='#dbeafe';
 const main=kind==='pill'?<rect x="22" y="4" width="20" height="8" rx="4" fill={soft}/>
  :kind==='capsule'?<rect x="22" y="4" width="20" height="8" rx="4" fill="white" stroke={c}/>
  :kind==='line'?<path d="M22 12 H42" stroke={c} strokeWidth="1.6"/>
  :kind==='block'?<rect x="22" y="4" width="20" height="8" rx="2" fill={c}/>
  :<rect x="22" y="4" width="20" height="8" rx="2" fill={c}/>;
 const sub=kind==='block'?<rect x="22" y="15" width="16" height="6" rx="1.5" fill={soft}/>
  :kind==='line'?<path d="M22 21 H38" stroke={c} strokeWidth="1"/>
  :kind==='classic'?<rect x="22" y="15" width="16" height="6" rx="1.5" fill="white" stroke={c}/>
  :<path d="M23 18 H36" stroke="#334155" strokeWidth="1.4"/>;
 return <svg width="44" height="24" viewBox="0 0 44 24" aria-hidden="true">
  {kind==='classic'?<ellipse cx="9" cy="12" rx="8" ry="6" fill="#1d4ed8"/>:kind==='line'?<rect x="1" y="6" width="16" height="12" rx="2" fill="white" stroke="#1d4ed8"/>
   :<rect x="1" y="6" width="16" height="12" rx={kind==='block'?2:6} fill="#1d4ed8"/>}
  <path d={kind==='block'?'M17 12 H20 V8 H22 M20 12 V18 H22':'M17 12 C20 12 19 8 22 8 M17 12 C20 12 19 18 22 18'} fill="none" stroke={c} strokeWidth="1"/>
  {main}{sub}</svg>;
}
/** 도형 갤러리 단추의 작은 그림. */
function ShapeIcon({shape}){
 const line=LINE_SHAPES.has(shape),key='i'+shape;
 const end=shape==='arrowLine'||shape==='doubleArrowLine'?'arrow':'none',start=shape==='doubleArrowLine'?'arrow':'none';
 return <svg width="26" height="20" viewBox="0 0 26 20" aria-hidden="true">
  {line&&<defs><Marker id={key+'s'} kind={start} color="#334155"/><Marker id={key+'e'} kind={end} color="#334155"/></defs>}
  {shape==='text'?<text x="13" y="15" textAnchor="middle" fontSize="13" fill="#334155">가</text>
   :<path d={shapePath(shape,2,2,22,16)} fill={line?'none':'#dbeafe'} fillRule="evenodd" stroke="#334155" strokeWidth="1.3"
     markerStart={start!=='none'?`url(#${key}s)`:undefined} markerEnd={end!=='none'?`url(#${key}e)`:undefined}/>}
 </svg>;
}
function ColorRow({label,value,onChange,allowNone=true}){
 return <div className="color-row"><span>{label}</span><div className="swatches">
  {allowNone&&<button className={'swatch none'+(value==='none'?' on':'')} title="없음" aria-label={label+' 없음'} onClick={()=>onChange('none')}/>}
  {PALETTE.map(c=><button key={c} className={'swatch'+(value?.toUpperCase()===c?' on':'')} style={{background:c}} title={c} aria-label={label+' '+c} onClick={()=>onChange(c)}/>)}
  <input type="color" aria-label={label+' 직접 고르기'} value={value&&value!=='none'?value:'#ffffff'} onChange={e=>onChange(e.target.value.toUpperCase())}/>
 </div></div>;
}
function Select({label,value,options,onChange}){
 return <label>{label}<select aria-label={label} value={value} onChange={e=>onChange(e.target.value)}>{options.map(([k,name])=><option key={k} value={k}>{name}</option>)}</select></label>;
}
function Stepper({label,value,min,max,onChange,step=1}){
 return <div className="stepper-row"><span>{label}</span><span className="stepper"><button aria-label={label+' 줄이기'} disabled={value<=min} onClick={()=>onChange(Math.max(min,+(value-step).toFixed(2)))}>−</button><output aria-live="polite">{value}</output><button aria-label={label+' 늘리기'} disabled={value>=max} onClick={()=>onChange(Math.min(max,+(value+step).toFixed(2)))}>+</button></span></div>;
}
/** 글꼴·크기(pt)·굵게·글자색(·바탕색) 고르기. 표 칸·다이어그램 도형·마인드맵 가지가 같이 쓴다. */
function TextStyleControls({value,onChange,fill=false,label}){
 const size=value.size??12;
 return <fieldset className="text-style"><legend>{label}</legend>
  <label>글꼴<select aria-label={label+' 글꼴'} value={value.font??'맑은 고딕'} onChange={e=>onChange({font:e.target.value})}>{FONTS.map(f=><option key={f} value={f} style={{fontFamily:'"'+f+'"'}}>{f}</option>)}</select></label>
  <div className="style-row">
   <label className="size">크기<span className="stepper"><button aria-label="글자 작게" onClick={()=>onChange({size:Math.max(6,size-1)})}>−</button><input aria-label={label+' 글꼴 크기'} type="number" min="6" max="40" step="0.5" value={size} onChange={e=>{const v=Number(e.target.value);if(v>=6&&v<=40)onChange({size:v});}}/><button aria-label="글자 크게" onClick={()=>onChange({size:Math.min(40,size+1)})}>+</button></span>pt</label>
   <button className={'toggle'+(value.bold?' on':'')} aria-pressed={!!value.bold} onClick={()=>onChange({bold:!value.bold})}><b>가</b> 굵게</button>
  </div>
  <div className="style-row">
   <label className="color">글자색<input aria-label={label+' 글자색'} type="color" value={value.color??value.textColor??'#000000'} onChange={e=>onChange(fill?{color:e.target.value.toUpperCase()}:{textColor:e.target.value.toUpperCase()})}/></label>
   {fill&&<label className="color">바탕색<input aria-label={label+' 바탕색'} type="color" value={value.fill||'#FFFFFF'} onChange={e=>onChange({fill:e.target.value.toUpperCase()})}/><button className="mini" onClick={()=>onChange({fill:''})}>없음</button></label>}
  </div>
 </fieldset>;
}
/** 도형 모양 고르기: 바탕색·테두리색·굵기·선 모양(+선 도형의 화살표 머리). */
function ShapeStyleControls({data,onChange}){
 const p=nodePaint(data),line=LINE_SHAPES.has(data.shape);
 return <fieldset className="text-style"><legend>도형 모양</legend>
  <Select label="도형 바꾸기" value={data.shape} options={[...SHAPES.entries()]} onChange={shape=>onChange({shape})}/>
  {!line&&<ColorRow label="바탕색" value={p.fill} onChange={fill=>onChange({fill})}/>}
  <ColorRow label={line?'선 색':'테두리색'} value={p.stroke} onChange={stroke=>onChange({stroke})}/>
  <Stepper label={line?'선 굵기':'테두리 굵기'} value={p.width} min={0} max={10} step={0.5} onChange={strokeWidth=>onChange({strokeWidth})}/>
  <Select label="선 모양" value={data.dash??'solid'} options={DASHES.map(([k,n])=>[k,n])} onChange={dash=>onChange({dash})}/>
  <div className="rotate-row"><span>회전</span><input type="range" min="0" max="359" step="1" aria-label="회전 각도" value={data.rotation??0} onChange={e=>onChange({rotation:normalizeRotation(e.target.value)})}/>
   <input type="number" min="0" max="359" aria-label="회전 각도(도)" value={data.rotation??0} onChange={e=>{const v=Number(e.target.value);if(v>=0&&v<=360)onChange({rotation:normalizeRotation(v)});}}/>°
   <button className="mini" title="왼쪽으로 90°" onClick={()=>onChange({rotation:normalizeRotation((data.rotation??0)-90)})}>⟲</button>
   <button className="mini" title="오른쪽으로 90°" onClick={()=>onChange({rotation:normalizeRotation((data.rotation??0)+90)})}>⟳</button></div>
  {line&&<><Select label="시작 화살표" value={data.lineStart??p.startDefault} options={MARKERS} onChange={lineStart=>onChange({lineStart})}/>
   <Select label="끝 화살표" value={p.end} options={MARKERS} onChange={lineEnd=>onChange({lineEnd})}/></>}
 </fieldset>;
}
function EdgeStyleControls({value,onChange}){
 const s={...EDGE_DEFAULT,...(value??{})};
 return <fieldset className="text-style"><legend>연결선 모양</legend>
  <div className="role-tabs">{[['step','꺾은선'],['straight','직선'],['curve','곡선']].map(([k,n])=><button key={k} className={s.line===k?'active':''} onClick={()=>onChange({...s,line:k})}>{n}</button>)}</div>
  <ColorRow label="선 색" value={s.color} allowNone={false} onChange={color=>onChange({...s,color})}/>
  <Stepper label="굵기" value={s.width} min={0.5} max={10} step={0.5} onChange={width=>onChange({...s,width})}/>
  <Select label="선 모양" value={s.dash} options={DASHES.map(([k,n])=>[k,n])} onChange={dash=>onChange({...s,dash})}/>
  <Select label="시작 화살표" value={s.start} options={MARKERS} onChange={start=>onChange({...s,start})}/>
  <Select label="끝 화살표" value={s.end} options={MARKERS} onChange={end=>onChange({...s,end})}/>
 </fieldset>;
}
/** 표 테두리 고르기(한/글과 같은 12종·굵기·색). */
function BorderControls({table,onChange,parts}){
 return <fieldset className="text-style"><legend>테두리</legend>
  {parts.map(part=>{const b=table.borders[part];return <div key={part} className="border-part"><b>{BORDER_NAMES[part]}</b>
   <Select label={BORDER_NAMES[part]+' 종류'} value={b.type} options={BORDER_TYPES.map(([k,n])=>[k,n])} onChange={type=>onChange(setBorder(table,part,{type}))}/>
   <div className="style-row"><Select label="굵기" value={b.width} options={BORDER_WIDTHS.map(w=>[w,w])} onChange={width=>onChange(setBorder(table,part,{width}))}/>
    <label className="color">색<input type="color" aria-label={BORDER_NAMES[part]+' 색'} value={b.color} onChange={e=>onChange(setBorder(table,part,{color:e.target.value.toUpperCase()}))}/></label></div>
   <div className="border-sample" style={{borderTop:cssBorder(b)}}/></div>;})}
 </fieldset>;
}

/** 흐름표 미리보기(가로·세로). 칸 글을 바로 고치고, 칸 사이 +로 단계를 끼우고 ×로 뺀다. */
function FlowTableView({table,onChange}){
 const s=table.styles,b=table.borders,rows=table.rows??1,vertical=table.direction==='vertical';
 const update=(i,patch)=>onChange({...table,steps:table.steps.map((step,j)=>j===i?{...step,...patch}:step)});
 const setDetail=(i,r,v)=>update(i,{details:flowDetails(table.steps[i],rows).map((d,k)=>k===r?v:d)});
 const step=(st,i)=><div className="flow-step" style={{border:cssBorder(b.line),flexDirection:vertical?'row':'column'}}>
  <textarea className="cell step" rows={2} aria-label={(i+1)+'번째 단계 이름'} maxLength={200} value={st.title} style={{...cssOf(s.step),[vertical?'borderRight':'borderBottom']:cssBorder(b.split)}} onChange={e=>update(i,{title:e.target.value})}/>
  {flowDetails(st,rows).map((d,r)=><textarea key={r} className="cell date" rows={2} aria-label={(i+1)+'번째 단계 세부 '+(r+1)} maxLength={200} value={d} placeholder={r===0?'일정':'세부 내용'}
   style={{...cssOf(s.date),...(r>0?{[vertical?'borderLeft':'borderTop']:cssBorder(b.line)}:{})}} onChange={e=>setDetail(i,r,e.target.value)}/>)}
  <button className="remove" title="이 단계 빼기" aria-label={(i+1)+'번째 단계 빼기'} disabled={table.steps.length<=2} onClick={()=>onChange(removeStep(table,i))}>×</button>
 </div>;
 return <div className="table-canvas"><div className={'flow-strip'+(vertical?' vertical':'')} style={vertical?{}:{gridTemplateColumns:table.steps.map((_,i)=>i?'34px 1fr':'1fr').join(' ')}}>
  {table.steps.map((st,i)=><React.Fragment key={i}>
   {i>0&&<div className="flow-arrow" style={cssOf(s.arrow)}>{table.arrow}<button className="insert" title="여기에 단계 끼우기" aria-label={i+'번째 단계 뒤에 단계 끼우기'} disabled={table.steps.length>=MAX_FLOW_STEPS} onClick={()=>onChange(insertStep(table,i))}>+</button></div>}
   {step(st,i)}
  </React.Fragment>)}
 </div><p className="hint">칸 글을 바로 고치세요. 칸 사이 +로 단계를 끼우고, ×로 뺍니다. 투명선은 한/글 화면처럼 빨간 점선으로 보여요.</p></div>;
}
/** 기본 표 미리보기: 칸 글을 바로 고치고, 행·열 머리의 +/×로 그 자리에 행·열을 끼우거나 뺀다. */
function GridTableView({table,onChange}){
 const cols=table.rows[0].length,s=table.styles,b=table.borders;
 const update=(r,c,value)=>onChange({...table,rows:table.rows.map((row,i)=>i===r?row.map((v,j)=>j===c?value:v):row)});
 const edgeCss=(r,c,side)=>{
  if(!table.custom_border)return '1px solid #334155';
  const outer=side==='top'?r===0:side==='bottom'?r===table.rows.length-1:side==='left'?c===0:c===cols-1;
  return cssBorder(outer?b.outer:b.inner);
 };
 return <div className="table-canvas"><table className="grid-preview"><thead><tr><th/>{Array.from({length:cols},(_,c)=><th key={c}><span className="col-tools">
  <button title="왼쪽에 열 끼우기" aria-label={(c+1)+'열 앞에 열 끼우기'} disabled={cols>=MAX_COLS} onClick={()=>onChange(insertCol(table,c))}>+</button>
  <button title="이 열 빼기" aria-label={(c+1)+'열 빼기'} disabled={cols<=1} onClick={()=>onChange(removeCol(table,c))}>×</button></span></th>)}</tr></thead>
  <tbody>{table.rows.map((row,r)=><tr key={r}><th><span className="row-tools">
   <button title="위에 행 끼우기" aria-label={(r+1)+'행 위에 행 끼우기'} disabled={table.rows.length>=MAX_ROWS} onClick={()=>onChange(insertRow(table,r))}>+</button>
   <button title="이 행 빼기" aria-label={(r+1)+'행 빼기'} disabled={table.rows.length<=1} onClick={()=>onChange(removeRow(table,r))}>×</button></span></th>
   {row.map((value,c)=>{const role=r<table.header_rows?'head':'body';return <td key={c} style={{background:(table.custom[role]||role==='head')?s[role].fill||'white':'white',
    borderTop:edgeCss(r,c,'top'),borderBottom:edgeCss(r,c,'bottom'),borderLeft:edgeCss(r,c,'left'),borderRight:edgeCss(r,c,'right')}}>
    <input className="cell" aria-label={(r+1)+'행 '+(c+1)+'열'} maxLength={200} value={value} style={{...cssOf(s[role]),background:'transparent'}} onChange={e=>update(r,c,e.target.value)}/></td>;})}
  </tr>)}</tbody></table>
  <p className="hint">{table.use_basic_style?'한/글로 저장하면 앱의 기본 표 서식(준말 ‘표’)을 입히고, 직접 고른 글자 서식·테두리만 덧입힙니다.':'기본 표 서식 없이 고른 글자 서식과 테두리로 만듭니다.'}</p></div>;
}
/** 조직표 미리보기: 윗 상자 → 세로선 → 가로 버스 → 부서 상자 → 아래 설명. */
function OrgTableView({table,onChange}){
 const s=table.styles,b=table.borders,link=cssBorder(b.link),box=cssBorder(b.box);
 const update=(i,patch)=>onChange({...table,units:table.units.map((u,j)=>j===i?{...u,...patch}:u)});
 return <div className="table-canvas"><div className="org">
  <div className="org-root"><input aria-label="윗 상자" value={table.root} maxLength={200} style={{...cssOf(s.root),border:box}} onChange={e=>onChange({...table,root:e.target.value})}/></div>
  <div className="org-stem" style={{borderLeft:link}}/>
  <div className="org-units" style={{gridTemplateColumns:`repeat(${table.units.length},1fr)`}}>
   {table.units.map((u,i)=><div key={i} className="org-unit">
    <div className="org-bus" style={{borderTop:table.units.length>1?link:'none',marginLeft:i===0?'50%':0,marginRight:i===table.units.length-1?'50%':0}}/>
    <div className="org-drop" style={{borderLeft:link}}/>
    <input aria-label={(i+1)+'번째 부서'} value={u.title} maxLength={200} style={{...cssOf(s.unit),border:box}} onChange={e=>update(i,{title:e.target.value})}/>
    <textarea aria-label={(i+1)+'번째 부서 아래 설명'} rows={3} value={u.detail} maxLength={200} placeholder="팀·인원(선택)" style={cssOf(s.detail)} onChange={e=>update(i,{detail:e.target.value})}/>
   </div>)}
  </div></div><p className="hint">한/글 표의 칸 테두리로 선을 그려, 한/글에서 글을 고쳐도 모양이 유지돼요.</p></div>;
}
/** 장식표 미리보기: '2026 추진실적 ……(8. 31. 현재)'. */
function BarTableView({table,onChange}){
 const s=table.styles,b=table.borders;
 return <div className="table-canvas"><div className="bar">
  <input aria-label="왼쪽 글" value={table.title} maxLength={200} style={{...cssOf(s.title),border:cssBorder(b.box)}} onChange={e=>onChange({...table,title:e.target.value})}/>
  <div className="bar-line" style={{borderTop:cssBorder(b.line)}}/>
  <input aria-label="오른쪽 글" value={table.note} maxLength={200} style={cssOf(s.note)} onChange={e=>onChange({...table,note:e.target.value})}/>
 </div><p className="hint">보고서 소제목 옆 실적 기준일 표시처럼 쓰는 장식 막대예요(학습: 장식표.hwpx).</p></div>;
}

function LayerPanel({layers,active,counts,selectedCount,onActive,onChange,onAdd,onRemove,onMove,onAssign}){
 const [renaming,setRenaming]=useState(null);
 return <section className="layer-panel" aria-label="레이어">
  <h2>레이어</h2>
  <ul className="layer-list">{[...layers].reverse().map((l,i)=><li key={l.id} className={l.id===active?'active':''} onClick={()=>onActive(l.id)}>
   <button className="layer-eye" aria-label={(l.visible?'숨기기: ':'보이기: ')+l.name} aria-pressed={!l.visible} title={l.visible?'숨기기':'보이기'} onClick={e=>{e.stopPropagation();onChange(l.id,{visible:!l.visible});}}>{l.visible?'👁':'◌'}</button>
   <button className="layer-lock" aria-label={(l.locked?'잠금 풀기: ':'잠그기: ')+l.name} aria-pressed={l.locked} title={l.locked?'잠금 풀기':'잠그기'} onClick={e=>{e.stopPropagation();onChange(l.id,{locked:!l.locked});}}>{l.locked?'🔒':'🔓'}</button>
   {renaming===l.id?<input autoFocus aria-label="레이어 이름" maxLength={60} defaultValue={l.name} onClick={e=>e.stopPropagation()}
     onBlur={e=>{onChange(l.id,{name:e.target.value.trim()||l.name});setRenaming(null);}} onKeyDown={e=>{if(e.key==='Enter')e.currentTarget.blur();if(e.key==='Escape')setRenaming(null);}}/>
    :<span className="layer-name" title="두 번 눌러 이름 바꾸기" onDoubleClick={()=>setRenaming(l.id)}>{l.name}</span>}
   <small>{counts[l.id]??0}</small>
  </li>)}</ul>
  <div className="tool-row">
   <button onClick={onAdd} title="새 레이어(맨 위)">＋ 새 레이어</button>
   <button onClick={()=>onMove(1)} title="한 칸 위로" aria-label="레이어 위로">▲</button>
   <button onClick={()=>onMove(-1)} title="한 칸 아래로" aria-label="레이어 아래로">▼</button>
   <button disabled={layers.length<=1} onClick={onRemove} title="레이어와 안의 개체 지우기" aria-label="레이어 지우기">🗑</button>
  </div>
  {selectedCount>0&&<button className="layer-assign" onClick={onAssign}>고른 개체 {selectedCount}개를 이 레이어로</button>}
 </section>;
}

const TABLE_KINDS=['flow','grid'];
const AVAILABLE_MODES=new Set(['diagram','mindmap','paint']);
const ROLE_SETS={flow:['step','date','arrow'],grid:['head','body']};
const BORDER_PARTS={flow:['line','split'],grid:['outer','inner']};
const newTables=()=>({flow:flowTable(5),grid:gridTable(4,4)});

/** 앱(상위 창 docfitCall)에서 이 PC의 글꼴 목록을 받아 글꼴 고르기에 더한다(한국어 이름·한/글 글꼴 먼저). */
function useInstalledFonts(){
 const [,setCount]=useState(FONTS.length);
 useEffect(()=>{
  const call=window.parent!==window?window.parent.docfitCall:null;
  if(typeof call!=='function')return;
  call('hangul_fonts',JSON.stringify(['list'])).then(text=>{
   const fonts=JSON.parse(text)?.fonts??[];
   const korean=n=>/[가-힣]/.test(n);
   const ordered=[...fonts.filter(f=>korean(f.name)),...fonts.filter(f=>!korean(f.name))].map(f=>f.name);
   setCount(registerFonts(ordered).length);
  }).catch(()=>{});
 },[]);
}

function App(){
 useInstalledFonts();
 const [graph,setGraph]=useState({nodes:[],edges:[]}),[name,setName]=useState('새 '+TITLE),[busy,setBusy]=useState(false),[status,setStatus]=useState('도형을 추가하고 연결점을 끌어 연결하세요.');
 const [mode,setMode]=useState('diagram'),[role,setRole]=useState({flow:'step',grid:'head'});
 const [catalog,setCatalog]=useState(null),[catalogCategory,setCatalogCategory]=useState(''),[catalogTemplate,setCatalogTemplate]=useState(''),[catalogStates,setCatalogStates]=useState({});
 const [catalogCellSel,setCatalogCellSel]=useState({r:0,c:0}),[catalogScope,setCatalogScope]=useState('cell'),[catalogCustomBorder,setCatalogCustomBorder]=useState(false);
 const [mmSelected,setMmSelected]=useState(null);
 const [activeLayer,setActiveLayer]=useState(null);
 // 도형 묶음 펼침 상태(도형을 넣어도 펼친 묶음이 접히지 않게 기억한다).
 const [openGroups,setOpenGroups]=useState(()=>new Set(['사각형','기본 도형','선']));
 const flow=useRef(null),current=useRef(graph),history=useRef([]),future=useRef([]),nameRef=useRef(name),clipboard=useRef(null);
 current.current=graph;nameRef.current=name;
 const generation=useRef(0),savedGeneration=useRef(0);
 const mark=()=>{generation.current++;send({type:'dirty',value:true,generation:generation.current});};
 const checkpoint=()=>{history.current.push(structuredClone(current.current));if(history.current.length>80)history.current.shift();future.current=[];};
 const commit=(next,record=true)=>{
  if(record)checkpoint();
  const before=new Set(current.current.nodes.map(n=>n.id)),fresh=next.nodes.filter(n=>!before.has(n.id)&&!n.data?.background&&!n.data?.layer);
  if(fresh.length&&next.nodes!==current.current.nodes){
   const layers=next.layers??defaultLayers(),target=layers.some(l=>l.id===activeLayer)?activeLayer:layers[layers.length-1].id;
   const layer=layers.find(l=>l.id===target);
   next={...next,nodes:assignLayer(next.nodes,fresh.map(n=>n.id),target)};
   if(next.layers&&(!layer.visible||layer.locked)){next={...next,layers:updateLayer(next.layers,target,{visible:true,locked:false})};setStatus('‘'+layer.name+'’ 레이어에 넣으려고 보이기·잠금 풀기를 했어요.');}
  }
  next=layoutGraph(next);current.current=next;setGraph(next);mark();
 };
 const undo=(redo=false)=>{
  const stack=redo?future:history,other=redo?history:future;if(!stack.current.length)return;
  other.current.push(structuredClone(current.current));const next=stack.current.pop();current.current=next;setGraph(next);mark();
 };
 const fit=()=>setTimeout(()=>flow.current?.fitView({padding:.18}),40);
 const tables=useRef(newTables());
 const replace=(next,title,dirty)=>{
  next=layoutGraph(next);current.current=next;setGraph(next);setName(title);history.current=[];future.current=[];
  generation.current++;if(!dirty)savedGeneration.current=generation.current;
  send({type:'dirty',value:dirty,generation:generation.current});fit();
  if(next.table&&TABLE_KINDS.includes(next.table.kind)){setMode('diagram');setStatus('흐름표·기본 표는 더 이상 지원하지 않아요. 표 템플릿을 써 주세요.');}
  else if(next.table)setMode('diagram');
  else if(next.mindmap&&!next.nodes.length)setMode('mindmap');
 };
 const snapshot=()=>validate({format:FORMAT,version:1,...current.current});
 const table=TABLE_KINDS.includes(mode)?(graph.table?.kind===mode?graph.table:tables.current[mode]):null;
 const changeTable=next=>{tables.current[next.kind]=next;commit({...current.current,table:next});};
 const mindmap=graph.mindmap??null;
 const changeMindmap=(next,select)=>{commit({...current.current,mindmap:next});if(select!==undefined)setMmSelected(select);};
 const [mmScope,setMmScope]=useState('one');
 // 그림판: 도구(선택·펜), 펜·도형 색과 굵기, 그리는 중인 펜 선(화면 좌표)
 const drawable=mode==='diagram'||mode==='paint';
 const [paintTool,setPaintTool]=useState('select'),[penColor,setPenColor]=useState('#DC2626'),[penWidth,setPenWidth]=useState(3);
 const [penLive,setPenLive]=useState(null);const penPoints=useRef([]);
 const setBackgroundFromFile=file=>{
  if(!file||!/^image\//.test(file.type)){setStatus('그림 파일(PNG·JPG 등)을 놓아 주세요.');return;}
  if(file.size>40*1024*1024){setStatus('40MB보다 큰 그림은 넣을 수 없습니다.');return;}
  const reader=new FileReader();
  reader.onload=()=>{const image=new Image();image.onload=()=>{
   const {width,height}=fitSize(image.naturalWidth,image.naturalHeight,2000);
   const c=document.createElement('canvas');c.width=width;c.height=height;c.getContext('2d').drawImage(image,0,0,width,height);
   const src=file.type==='image/png'?c.toDataURL('image/png'):c.toDataURL('image/jpeg',.9);
   commit({...current.current,nodes:withBackground(current.current.nodes,src,width,height)});
   setStatus('배경 사진을 넣었어요. 펜·도형·글상자를 올려 보세요.');setTimeout(()=>flow.current?.fitView({padding:.05}),50);
  };image.onerror=()=>setStatus('그림을 읽지 못했습니다.');image.src=reader.result;};
  reader.readAsDataURL(file);
 };
 useEffect(()=>{
  if(mode!=='paint')return;
  // 사진을 창에 끌어 놓거나 Ctrl+V로 붙여 넣으면 배경으로(그림판 탭에서만).
  const over=e=>{if([...(e.dataTransfer?.types??[])].includes('Files')){e.preventDefault();e.dataTransfer.dropEffect='copy';}};
  const drop=e=>{const file=e.dataTransfer?.files?.[0];if(file){e.preventDefault();setBackgroundFromFile(file);}};
  const paste=e=>{const item=[...(e.clipboardData?.items??[])].find(i=>i.type.startsWith('image/'));if(item){e.preventDefault();setBackgroundFromFile(item.getAsFile());}};
  window.addEventListener('dragover',over);window.addEventListener('drop',drop);window.addEventListener('paste',paste);
  return()=>{window.removeEventListener('dragover',over);window.removeEventListener('drop',drop);window.removeEventListener('paste',paste);};
 });
 const addPaint=shape=>{
  const center=flow.current?.screenToFlowPosition({x:window.innerWidth/2,y:window.innerHeight/2})??{x:100,y:100};
  let position={...center},tries=0;
  // 이미 놓인 개체와 겹치지 않게 오른쪽 아래로 비켜 놓는다.
  while(tries<30&&graph.nodes.some(n=>!n.data?.background&&position.x<n.position.x+n.width&&n.position.x<position.x+60&&position.y<n.position.y+n.height&&n.position.y<position.y+40)){position={x:position.x+50,y:position.y+60};tries++;}
  const made=node(shape==='text'?'글 입력':'',position.x,position.y,shape,'blue',id(),paintStyle(shape,penColor,penWidth));
  if(LINE_SHAPES.has(shape))Object.assign(made,shape==='vline'?{width:40,height:160}:shape==='diagonal'?{width:160,height:120}:{width:200,height:40});
  if(shape==='text')Object.assign(made,{width:160,height:50});
  commit({...graph,nodes:[...graph.nodes.map(n=>({...n,selected:false})),{...made,selected:true}]});
  setPaintTool('select');
 };
 const penEvent=e=>{const r=e.currentTarget.getBoundingClientRect();return {screen:[e.clientX-r.left,e.clientY-r.top],flow:flow.current?.screenToFlowPosition({x:e.clientX,y:e.clientY})};};
 const penDown=e=>{e.preventDefault();e.currentTarget.setPointerCapture?.(e.pointerId);const p=penEvent(e);penPoints.current=[p.flow];setPenLive([p.screen]);};
 const penMove=e=>{if(!penLive)return;const p=penEvent(e);penPoints.current.push(p.flow);setPenLive(v=>[...(v??[]),p.screen]);};
 const penUp=()=>{
  const made=penPoints.current.length>1?freehandNode(penPoints.current,{stroke:penColor,strokeWidth:penWidth}):null;
  penPoints.current=[];setPenLive(null);
  if(made)commit({...current.current,nodes:[...current.current.nodes.map(n=>({...n,selected:false})),made]});
 };
 const [guides,setGuides]=useState([]);
 // 자석: 놓은 곳 아래 도형(선 도형 제외)을 찾는다.
 const dropTarget=(event,skip)=>{
  const p=event.changedTouches?.[0]??event;
  if(!flow.current||p?.clientX==null)return null;
  const point=flow.current.screenToFlowPosition({x:p.clientX,y:p.clientY});
  return nodeAt(current.current.nodes,point,new Set(skip),n=>LINE_SHAPES.has(n.data?.shape));
 };
 const magnetEdge=(source,target,extra={})=>{
  const [s,t]=facingSides(source,target);
  const made=edge(source.id,target.id,'',id(),s,t,{...EDGE_DEFAULT,autoSide:true});
  return {...made,...extra};
 };
 const restyle=patch=>changeMindmap(restyleNodes(current.current.mindmap??mindmap,mmSelected,mmScope,patch));
 const switchMode=next=>{
  if(!AVAILABLE_MODES.has(next)){
   setStatus(next==='catalog'?'표 서식 모음은 현재 알파 버전에서 비활성화되어 있습니다.':'조직표와 장식표는 현재 알파 버전에서 사용할 수 없습니다.');
   return;
  }
  setMode(next);
  if(TABLE_KINDS.includes(next)&&current.current.table?.kind!==next){current.current={...current.current,table:tables.current[next]};setGraph(current.current);}
  if(next==='mindmap'&&!current.current.mindmap){current.current={...current.current,mindmap:sampleMindmap()};setGraph(current.current);}
  setStatus({flow:'칸 수를 고르고 칸 글을 바로 고치세요. 다 되면 ‘한/글 문서로 저장’을 누르세요.',grid:'행·열을 늘리거나 줄이고 칸 글을 고치세요.',
   mindmap:'가지를 고르고 Tab=하위 가지, Enter=같은 단계 가지, Delete=지우기.',
   }[next]??'도형을 추가하고 연결점을 끌어 연결하세요.');
  if(next==='diagram'||next==='mindmap')fit();
 };
 const handle=useRef(null);
 handle.current=async message=>{
  if(!message||typeof message!=='object')return;
  try{
   switch(message.type){case 'set_mode':{if(message.mode==='diagram'||message.mode==='mindmap'||message.mode==='paint'){switchMode(message.mode);if(nameRef.current==='새 '+TITLE)setName(newName(message.mode));}break;}
    case 'new':tables.current=newTables();setMmSelected(null);replace({nodes:[],edges:[]},newName(mode),false);send({type:'document_new'});break;
    case 'set_background':{
     // 앱 창에 끌어 놓은 사진(앱이 받아 알맞은 크기로 바꿔 넘김)을 그림판 배경으로.
     if(mode!=='paint'||!isImageSrc(message.src))break;
     const size=fitSize(Number(message.width)||1,Number(message.height)||1,2000);
     commit({...current.current,nodes:withBackground(current.current.nodes,message.src,size.width,size.height)});
     setStatus('배경 사진을 넣었어요. 펜·도형·글상자를 올려 보세요.');setTimeout(()=>flow.current?.fitView({padding:.05}),50);break;}
    case 'mark_saved':
     if(Number.isInteger(message.generation))savedGeneration.current=Math.max(savedGeneration.current,message.generation);
     send({type:'dirty',value:generation.current>savedGeneration.current,generation:generation.current});
     setStatus(generation.current>savedGeneration.current?'추가 변경사항을 저장해 주세요.':'저장했습니다.');break;
    case 'load':{
     const loaded=decode(message.snapshot);
     if(loaded.table)tables.current[loaded.table.kind]=loaded.table;
     setActiveLayer(null);replace({nodes:loaded.nodes,edges:loaded.edges,...(loaded.table?{table:loaded.table}:{}),...(loaded.mindmap?{mindmap:loaded.mindmap}:{}),...(loaded.layers?{layers:loaded.layers}:{})},message.name,loaded.converted);
     send({type:'document_loaded',converted:loaded.converted});break;
    }
    case 'apply_template':{
     const value=template(message.template);commit({...current.current,nodes:value.nodes,edges:value.edges});setName(value.name);setMode('diagram');fit();
     send({type:'template_applied',template:message.template,name:value.name});break;
    }
    case 'catalog_data':{
     setStatus('표 서식 모음은 현재 알파 버전에서 비활성화되어 있습니다.');
     send({type:'editor_error',message:'표 서식 모음은 현재 알파 버전에서 비활성화되어 있습니다.'});break;
    }
    case 'save':{
     const nextName=message.name??nameRef.current;setName(nextName);
     send({type:'save_document',id:message.id??null,name:nextName,generation:generation.current,snapshot:snapshot()});break;
    }
    case 'copy_png':
    case 'export_png':{
     setBusy(true);
     const doc=snapshot();
     const image=svg(mode==='mindmap'&&doc.mindmap?{...doc,nodes:[],edges:[]}:doc),url=URL.createObjectURL(new Blob([image.source],{type:'image/svg+xml'}));
     try{
      const bitmap=new Image();await new Promise((resolve,reject)=>{bitmap.onload=resolve;bitmap.onerror=()=>reject(new Error('이미지 변환에 실패했습니다.'));bitmap.src=url;});
      const canvas=document.createElement('canvas');canvas.width=Math.ceil(image.width*1.5);canvas.height=Math.ceil(image.height*1.5);
      const context=canvas.getContext('2d');context.scale(1.5,1.5);context.drawImage(bitmap,0,0);
      const base64=canvas.toDataURL('image/png').split(',')[1];
      if(base64.length>28*1024*1024)throw new Error('PNG 크기가 제한을 넘습니다.');
      send({type:message.type==='copy_png'?'copy_result':'export_png',kind:'png',name:nameRef.current,base64});
     }finally{URL.revokeObjectURL(url);setBusy(false);}
     break;
    }
    default:break;
   }
  }catch(error){setBusy(false);setStatus(error.message);send({type:'editor_error',message:error.message});}
 };
 useEffect(()=>{
  const receive=event=>{
   if(window.parent===window&&window.chrome?.webview){let data=event.data;try{if(typeof data==='string')data=JSON.parse(data);}catch{return;}handle.current(data);}
   else if(event.source===window.parent&&event.origin===location.origin)handle.current(event.data);
  };
  const host=window.parent===window?(window.chrome?.webview??window):window;host.addEventListener('message',receive);
  return ()=>host.removeEventListener('message',receive);
 },[]);
 const selectedNodes=graph.nodes.filter(n=>n.selected),selected=selectedNodes[0],selectedEdge=graph.edges.find(e=>e.selected);
 const layers=graph.layers??defaultLayers();
 const currentLayer=layers.some(l=>l.id===activeLayer)?activeLayer:layers[layers.length-1].id;
 const layerCounts={};for(const n of graph.nodes)if(!n.data?.background){const k=layerOf(n,layers);layerCounts[k]=(layerCounts[k]??0)+1;}
 const changeLayers=next=>commit({...current.current,layers:next,nodes:current.current.nodes.map(n=>({...n,selected:false}))});
 const layerPanel=<LayerPanel layers={layers} active={currentLayer} counts={layerCounts} selectedCount={selectedNodes.filter(n=>!n.data?.background).length}
  onActive={setActiveLayer}
  onChange={(layerId,patch)=>changeLayers(updateLayer(layers,layerId,patch))}
  onAdd={()=>{try{const next=addLayer(layers);changeLayers(next);setActiveLayer(next[next.length-1].id);}catch(error){setStatus(error.message);}}}
  onMove={step=>changeLayers(moveLayer(layers,currentLayer,step))}
  onRemove={()=>{const count=layerCounts[currentLayer]??0;if(count&&!window.confirm('이 레이어와 안의 개체 '+count+'개를 지울까요? (Ctrl+Z로 되돌릴 수 있어요)'))return;
   commit(removeLayer({...current.current,layers},currentLayer));setActiveLayer(null);}}
  onAssign={()=>commit({...current.current,layers,nodes:assignLayer(current.current.nodes,selectedNodes.map(n=>n.id),currentLayer)})}/>;
 const duplicate=()=>{
  const items=current.current.nodes.filter(n=>n.selected);if(!items.length)return;
  const copies=items.map(n=>({...structuredClone(n),id:id(),position:{x:n.position.x+30,y:n.position.y+30},selected:true}));
  commit({...current.current,nodes:[...current.current.nodes.map(n=>({...n,selected:false})),...copies]});
 };
 const selectedCatalogCategory=catalog?.categories?.find(item=>item.id===catalogCategory);
 const selectedCatalogTemplate=selectedCatalogCategory?.templates?.find(item=>item.id===catalogTemplate);
 const currentCatalogEntry=selectedCatalogTemplate?(catalogStates[selectedCatalogTemplate.id]??{grid:buildCatalogGrid(selectedCatalogTemplate),ops:[],history:[],future:[]}):{grid:[],ops:[],history:[],future:[]};
 const catalogGrid=currentCatalogEntry.grid;
 const selectedCatalogStructure=currentCatalogEntry.ops;
 const catalogColCount=catalogGrid.length?Math.max(1,...catalogGrid.map(r=>r.reduce((s,cell)=>s+(cell.colSpan??1),0))):0;
 const safeSelR=Math.min(catalogCellSel.r,Math.max(0,catalogGrid.length-1));
 const safeSelC=Math.min(catalogCellSel.c,Math.max(0,(catalogGrid[safeSelR]?.length??1)-1));
 const activeCatalogCell=catalogGrid[safeSelR]?.[safeSelC]??catalogGrid[0]?.[0]??null;
 const isStepTemplate=selectedCatalogTemplate?isTaskTable(selectedCatalogTemplate.id,selectedCatalogCategory?.name):false;
 const isFixedCategory=selectedCatalogCategory?isFixedCalloutCategory(selectedCatalogCategory.name,selectedCatalogTemplate?.id):false;
 const currentCatalogSteps=isStepTemplate&&catalogGrid[0]?Math.max(2,Math.min(6,Math.round(catalogGrid[0].length/4))):3;
 const changeCatalogSteps=targetSteps=>{
  if(!selectedCatalogTemplate)return;
  try{
   const res=resizeTaskGrid(catalogGrid,targetSteps);
   updateCatalogEntry(res.grid,res.ops,true);
  }catch(error){setStatus(error.message);}
 };
 const updateCatalogEntry=(nextGrid,nextOps=selectedCatalogStructure,record=true)=>{
  if(!selectedCatalogTemplate)return;
  const prevHistory=record?[...currentCatalogEntry.history.slice(-49),{grid:structuredClone(catalogGrid),ops:structuredClone(selectedCatalogStructure)}]:currentCatalogEntry.history;
  setCatalogStates({...catalogStates,[selectedCatalogTemplate.id]:{grid:nextGrid,ops:nextOps,history:prevHistory,future:record?[]:currentCatalogEntry.future}});
  mark();
 };
 const undoCatalog=(redo=false)=>{
  if(!selectedCatalogTemplate)return;
  const stack=redo?currentCatalogEntry.future:currentCatalogEntry.history;
  if(!stack.length)return;
  const popped=stack[stack.length-1];
  const nextHistory=redo?[...currentCatalogEntry.history,{grid:structuredClone(catalogGrid),ops:structuredClone(selectedCatalogStructure)}]:currentCatalogEntry.history.slice(0,-1);
  const nextFuture=redo?currentCatalogEntry.future.slice(0,-1):[...currentCatalogEntry.future,{grid:structuredClone(catalogGrid),ops:structuredClone(selectedCatalogStructure)}];
  setCatalogStates({...catalogStates,[selectedCatalogTemplate.id]:{grid:popped.grid,ops:popped.ops,history:nextHistory,future:nextFuture}});
  mark();
 };
 useEffect(()=>{
  const keys=e=>{
   if(['INPUT','TEXTAREA','SELECT'].includes(e.target.tagName)||e.target.isContentEditable)return;
   const ctrl=e.ctrlKey||e.metaKey,k=e.key.toLowerCase();
   if(ctrl&&k==='s'){e.preventDefault();send({type:'request_save'});}
   if(ctrl&&k==='z'){e.preventDefault();mode==='catalog'?undoCatalog(e.shiftKey):undo(e.shiftKey);}
   if(ctrl&&k==='y'){e.preventDefault();mode==='catalog'?undoCatalog(true):undo(true);}
   if(drawable&&ctrl&&k==='d'){e.preventDefault();duplicate();}
   if(drawable&&ctrl&&k==='c'){clipboard.current=structuredClone(current.current.nodes.filter(n=>n.selected&&!n.data?.background));}
   if(drawable&&ctrl&&k==='v'&&clipboard.current?.length){e.preventDefault();
    const copies=clipboard.current.map(n=>({...n,id:id(),position:{x:n.position.x+40,y:n.position.y+40},selected:true}));
    commit({...current.current,nodes:[...current.current.nodes.map(n=>({...n,selected:false})),...copies]});}
   if(mode==='mindmap'&&mindmap&&mmSelected){
    if(['Tab','Enter'].includes(e.key)&&mmGraphCount(current.current.mindmap)>=300){e.preventDefault();setStatus('가지는 문서당 300개까지입니다.');return;}
    if(e.key==='Tab'){e.preventDefault();const r=addChild(mindmap,mmSelected);changeMindmap(r.map,r.id);}
    else if(e.key==='Enter'){e.preventDefault();const r=addSibling(mindmap,mmSelected);changeMindmap(r.map,r.id);}
    else if(e.key==='Delete'||e.key==='Backspace'){e.preventDefault();if(mmSelected!==mindmap.root.id)changeMindmap(removeNode(mindmap,mmSelected),mindmap.root.id);}
   }
  };window.addEventListener('keydown',keys);return()=>window.removeEventListener('keydown',keys);
 });
 const edit=(data)=>commit({...graph,nodes:graph.nodes.map(n=>n.selected?{...n,data:{...n.data,...data}}:n)});
 const editEdge=(data)=>commit({...graph,edges:graph.edges.map(e=>e.id===selectedEdge.id?{...e,data,style:{stroke:data.color,strokeWidth:data.width},markerEnd:{type:'arrowclosed',color:data.color}}:e)});
 const add=shape=>{
  const center=flow.current?.screenToFlowPosition({x:window.innerWidth/2,y:window.innerHeight/2})??{x:100,y:100};
  // 같은 자리에 겹치지 않게, 이미 도형이 있으면 오른쪽 아래로 조금씩 비켜 놓는다.
  let position={...center},tries=0;
  while(tries<30&&graph.nodes.some(n=>Math.abs(n.position.x-position.x)<20&&Math.abs(n.position.y-position.y)<20)){position={x:position.x+40,y:position.y+40};tries++;}
  const line=LINE_SHAPES.has(shape);
  const made=node(shape==='diamond'||shape==='decision'?'조건 판단':line?'':shape==='text'?'글 입력':'내용 입력',position.x,position.y,shape);
  if(line)Object.assign(made,shape==='vline'?{width:40,height:160}:shape==='diagonal'?{width:160,height:120}:{width:200,height:40});
  commit({...graph,nodes:[...graph.nodes.map(n=>({...n,selected:false})),{...made,selected:true}]});
 };
 const align=kind=>{
  const items=graph.nodes.filter(n=>n.selected);if(items.length<2)return;
  const L=Math.min(...items.map(n=>n.position.x)),R=Math.max(...items.map(n=>n.position.x+n.width)),T=Math.min(...items.map(n=>n.position.y)),B=Math.max(...items.map(n=>n.position.y+n.height));
  const pos=n=>({left:{x:L},center:{x:(L+R)/2-n.width/2},right:{x:R-n.width},top:{y:T},middle:{y:(T+B)/2-n.height/2},bottom:{y:B-n.height}}[kind]);
  commit({...graph,nodes:graph.nodes.map(n=>n.selected?{...n,position:{...n.position,...pos(n)}}:n)});
 };
 const order=front=>{
  const sel=graph.nodes.filter(n=>n.selected),rest=graph.nodes.filter(n=>!n.selected);
  if(sel.length)commit({...graph,nodes:front?[...rest,...sel]:[...sel,...rest]});
 };
 const exportHwpx=()=>{
  try{send({type:'export_hwpx',name:nameRef.current,spec:exportSpec(table)});}
  catch(error){setStatus(error.message);}
 };
 const setCatalogCell=(row,col,value)=>{
  if(!selectedCatalogTemplate)return;
  updateCatalogEntry(setCatalogCellText(catalogGrid,row,col,value),selectedCatalogStructure,false);
 };
 const changeCatalogStructure=operation=>{
  if(!selectedCatalogTemplate)return;
  try{
   const res=applyCatalogStructure(catalogGrid,selectedCatalogStructure,operation);
   updateCatalogEntry(res.grid,res.ops,true);
  }catch(error){setStatus(error.message);}
 };
 const resizeCatalogRows=targetRows=>{
  if(targetRows>catalogGrid.length)changeCatalogStructure('add_row');
  else if(targetRows<catalogGrid.length)changeCatalogStructure('delete_row');
 };
 const resizeCatalogCols=targetCols=>{
  if(targetCols>catalogColCount)changeCatalogStructure('add_column');
  else if(targetCols<catalogColCount)changeCatalogStructure('delete_column');
 };
 const changeCatalogStyle=patch=>{
  if(!selectedCatalogTemplate)return;
  try{updateCatalogEntry(setCatalogStyle(catalogGrid,catalogScope,{r:safeSelR,c:safeSelC},patch),selectedCatalogStructure,true);}
  catch(error){setStatus(error.message);}
 };
 const changeCatalogBorderTable=nextBorderTable=>{
  if(!selectedCatalogTemplate||!activeCatalogCell)return;
  try{
   const curOuter=activeCatalogCell.borders.top,curInner=activeCatalogCell.borders.bottom;
   const nextOuter=nextBorderTable.borders.outer,nextInner=nextBorderTable.borders.inner;
   let nextGrid=catalogGrid;
   if(JSON.stringify(curOuter)!==JSON.stringify(nextOuter))nextGrid=setCatalogBorder(nextGrid,catalogScope,{r:safeSelR,c:safeSelC},'outer',nextOuter);
   if(JSON.stringify(curInner)!==JSON.stringify(nextInner))nextGrid=setCatalogBorder(nextGrid,catalogScope,{r:safeSelR,c:safeSelC},'inner',nextInner);
   updateCatalogEntry(nextGrid,selectedCatalogStructure,true);
  }catch(error){setStatus(error.message);}
 };
 const resetCatalogTemplate=()=>{
  if(!selectedCatalogTemplate)return;
  updateCatalogEntry(buildCatalogGrid(selectedCatalogTemplate),[],true);
  setStatus('선택한 표 모양을 원래 서식으로 되돌렸습니다.');
 };
 const exportCatalog=()=>{
  if(!selectedCatalogTemplate){setStatus('먼저 저장할 표 모양을 선택하세요.');return;}
  const {cell_edits,style_edits}=buildCatalogEdits(catalogGrid);
  send({type:'export_catalog',id:selectedCatalogTemplate.id,name:selectedCatalogTemplate.name,cell_edits,structure_edits:selectedCatalogStructure,style_edits});
 };
 const copyCatalog=()=>{
  if(!selectedCatalogTemplate){setStatus('먼저 복사할 표 모양을 선택하세요.');return;}
  const {cell_edits,style_edits}=buildCatalogEdits(catalogGrid);
  send({type:'copy_catalog',id:selectedCatalogTemplate.id,cell_edits,structure_edits:selectedCatalogStructure,style_edits});
 };
 // 마인드맵: 수동 위치와 계층 연결을 화면·내보내기에 함께 반영한다.
 const mmGraph=mode==='mindmap'&&mindmap?layoutGraph(mindmapGraph(mindmap)):null;
 const mmNode=mindmap&&mmSelected?findNode(mindmap,mmSelected)?.node:null;
 const shownNodes=mmGraph?mmGraph.nodes.map(n=>({...n,selected:n.id===mmSelected,draggable:true,connectable:true})):layeredNodes(graph.nodes,graph.layers);
 const shownEdges=mmGraph?mmGraph.edges:layeredEdges(graph.edges,graph.nodes,graph.layers);
 const canvas=mode==='diagram'||mode==='mindmap'||mode==='paint';
 const hasBackground=graph.nodes.some(n=>n.id===BACKGROUND_ID);
 const scopeLabel=CATALOG_SCOPES.find(([k])=>k===catalogScope)?.[1]??'선택 칸';
 return <HistoryContext.Provider value={checkpoint}><div className="editor-shell">
  <header>
   <nav>
   <button onClick={()=>send({type:'request_new'})}>새 문서</button>
   <button onClick={()=>send({type:'request_list'})}>열기·삭제</button>
   <button onClick={()=>send({type:'request_save'})}>저장</button>
   <button onClick={()=>send({type:'request_save_copy'})}>사본 저장</button>
   {mode==='catalog'?<><button onClick={()=>send({type:'request_catalog'})}>목록 새로고침</button><button className="primary" disabled={!selectedCatalogTemplate||busy} onClick={copyCatalog}>선택한 표 한/글에 복사</button><button disabled={!selectedCatalogTemplate||busy} onClick={exportCatalog}>수정 표 HWPX 저장</button></>:canvas?<>
    <button disabled={busy} onClick={()=>handle.current({type:'copy_png'})}>그림 복사 (한/글 붙여넣기)</button>
    <button disabled={busy} onClick={()=>send({type:'request_png'})}>{busy?'PNG 변환 중…':'PNG 내보내기'}</button>
    {mode==='diagram'&&<select aria-label="예시 서식" value="" onChange={e=>send({type:'request_template',template:e.target.value})}><option value="">예시 서식</option>{Object.entries(templates).map(([key,t])=><option key={key} value={key}>{t.name}</option>)}</select>}
   </>:null}
  </nav></header>
  <div className="workspace">
   {mode==='diagram'&&<aside>
    <h2>도형</h2>
    {SHAPE_GROUPS.map(([group,items])=><details key={group} open={openGroups.has(group)} onToggle={e=>{const o=e.currentTarget.open;setOpenGroups(s=>{const next=new Set(s);o?next.add(group):next.delete(group);return next;});}} className="shape-group"><summary>{group}</summary>
     <div className="shape-grid">{items.map(([shape,label])=><button key={shape} title={label} aria-label={label+' 추가'} onClick={()=>add(shape)}><ShapeIcon shape={shape}/></button>)}</div></details>)}
    <div className="tool-row"><button onClick={()=>undo()} title="실행 취소 (Ctrl+Z)">↶ 취소</button><button onClick={()=>undo(true)} title="다시 실행 (Ctrl+Y)">↷ 다시</button><button onClick={duplicate} title="복제 (Ctrl+D)">⧉ 복제</button></div>
    {selectedNodes.length>1&&<><h2>정렬 ({selectedNodes.length}개)</h2><div className="tool-row">
     {[['left','왼쪽'],['center','가운데'],['right','오른쪽'],['top','위'],['middle','중간'],['bottom','아래']].map(([k,n])=><button key={k} onClick={()=>align(k)}>{n}</button>)}</div></>}
    {selected&&<><h2>선택 도형</h2>
     <label>내용<textarea aria-label="도형 내용" maxLength={2000} value={selected.data.label} onChange={e=>edit({label:e.target.value})}/></label>
     <div className="tool-row"><button onClick={()=>order(true)}>맨 앞으로</button><button onClick={()=>order(false)}>맨 뒤로</button></div>
     <ShapeStyleControls data={selected.data} onChange={edit}/>
     <TextStyleControls label="도형 글자" value={{font:selected.data.font,size:selected.data.size,bold:selected.data.bold,textColor:selected.data.textColor}} onChange={edit}/></>}
    {selectedEdge&&!selected&&<><h2>선택 연결선</h2><label>연결선 설명<input aria-label="연결선 설명" maxLength={300} value={selectedEdge.label??''} onChange={e=>commit({...graph,edges:graph.edges.map(v=>v.id===selectedEdge.id?{...v,label:e.target.value}:v)})}/></label>
     <EdgeStyleControls value={selectedEdge.data} onChange={editEdge}/>
     <label className="check"><input type="checkbox" checked={!!selectedEdge.data?.autoSide} onChange={e=>{
      const data={...(selectedEdge.data??EDGE_DEFAULT),autoSide:e.target.checked};let next={...graph,edges:graph.edges.map(v=>v.id===selectedEdge.id?{...v,data}:v)};
      next={...next,edges:autoRoute(next.nodes,next.edges)};commit(next);}}/> 자석 연결(도형을 옮기면 마주 보는 면으로 붙음)</label></>}
    {layerPanel}
    <p>연결점을 끌어 도형 연결<br/>Shift+선택: 여러 도형<br/>Ctrl+C/V 복사·붙여넣기, Ctrl+D 복제<br/>Delete: 선택 삭제 · Ctrl+휠: 확대·축소</p>
   </aside>}
   {mode==='paint'&&<aside className="paint-aside">
    <h2>그림판</h2>
    <div className="tool-row" role="radiogroup" aria-label="그림판 도구">
     <button role="radio" aria-checked={paintTool==='select'} className={paintTool==='select'?'active':''} onClick={()=>setPaintTool('select')}>↖ 선택·이동</button>
     <button role="radio" aria-checked={paintTool==='pen'} className={paintTool==='pen'?'active':''} onClick={()=>setPaintTool('pen')}>✎ 펜</button></div>
    <ColorRow label="펜·도형 색" value={penColor} onChange={c=>setPenColor(c==='none'?'#111827':c)}/>
    <Select label="굵기" value={String(penWidth)} options={[['2','가늘게'],['3','보통'],['5','굵게'],['8','아주 굵게']]} onChange={v=>setPenWidth(Number(v))}/>
    <h2>배경 사진</h2>
    <div className="paint-drop-zone" aria-label="배경 사진 놓는 곳"><b>📷 사진을 끌어 놓으세요</b><span>그림판 아무 곳에 놓아도 배경이 돼요. Ctrl+V로 붙여 넣어도 돼요.</span>
     <label className="file-link">파일에서 고르기<input type="file" accept="image/*" aria-label="배경 사진 열기" onChange={e=>{setBackgroundFromFile(e.target.files?.[0]);e.target.value='';}}/></label></div>
    <button disabled={!hasBackground} onClick={()=>commit({...current.current,nodes:withoutBackground(current.current.nodes)})}>배경 지우기</button>
    <p>배경은 맨 뒤에 고정돼요.</p>
    <h2>넣기</h2>
    <div className="shape-grid">{[['text','글상자'],['rectangle','사각형'],['roundRect','둥근 사각형'],['ellipse','타원'],['circle','원'],['arrowLine','화살표'],['line','직선'],['arrowRight','블록 화살표'],['star5','별'],['calloutRound','말풍선'],['triangle','삼각형'],['heart','하트']].map(([shape,label])=>
     <button key={shape} title={label} aria-label={label+' 넣기'} onClick={()=>addPaint(shape)}><ShapeIcon shape={shape}/></button>)}</div>
    <div className="tool-row"><button onClick={()=>undo()} title="실행 취소 (Ctrl+Z)">↶ 취소</button><button onClick={()=>undo(true)} title="다시 실행 (Ctrl+Y)">↷ 다시</button><button onClick={duplicate} title="복제 (Ctrl+D)">⧉ 복제</button></div>
    {selected&&<><h2>선택 개체</h2>
     {selected.data.shape!=='freehand'&&<label>글<textarea aria-label="개체 글" maxLength={2000} value={selected.data.label} onChange={e=>edit({label:e.target.value})}/></label>}
     <div className="tool-row"><button onClick={()=>order(true)}>맨 앞으로</button><button onClick={()=>order(false)}>맨 뒤로</button></div>
     <ShapeStyleControls data={selected.data} onChange={edit}/>
     {selected.data.shape!=='freehand'&&<TextStyleControls label="글자" value={{font:selected.data.font,size:selected.data.size,bold:selected.data.bold,textColor:selected.data.textColor}} onChange={edit}/>}</>}
    {layerPanel}
    <p>모든 펜 선·도형·글상자는 따로 옮기고 크기·색을 바꿀 수 있어요.<br/>Delete: 지우기 · Ctrl+C/V 복사 · Ctrl+D 복제</p>
   </aside>}
   {mode==='mindmap'&&mindmap&&<aside><h2>마인드맵</h2>
    <Select label="배치" value={mindmap.layout} options={[['both','가운데에서 좌우로'],['right','오른쪽으로'],['down','위에서 아래로(조직도형)']]} onChange={layout=>{changeMindmap(autoLayoutMindmap(mindmap,layout));fit();}}/>
    {(()=>{const th=themeOf(mindmap),setTheme=patch=>{const m=current.current.mindmap??mindmap;changeMindmap({...m,theme:{...themeOf(m),...patch}});};return <fieldset className="text-style mm-theme" aria-label="지도 테마"><legend>지도 테마</legend>
     <small>지도 전체에 한 번에 적용해요(가지마다 따로 고친 서식은 그대로).</small>
     <div className="mm-theme-row" role="radiogroup" aria-label="테마 모양">{MINDMAP_THEME_SHAPES.map(([key,label])=>
      <button key={key} role="radio" aria-checked={th.shape===key} className={th.shape===key?'active':''} onClick={()=>setTheme({shape:key})}>
       <ThemeShapeIcon kind={key}/><small>{label}</small></button>)}</div>
     <div className="mm-theme-row" role="radiogroup" aria-label="테마 색">{MINDMAP_PALETTES.map(([key,label,colors])=>
      <button key={key} role="radio" aria-checked={th.palette===key} className={th.palette===key?'active':''} title={label} onClick={()=>setTheme({palette:key})}>
       <span className="mm-swatch">{colors.slice(0,5).map(c=><i key={c} style={{background:c}}/>)}</span><small>{label}</small></button>)}</div>
     <div className="mm-theme-row" role="radiogroup" aria-label="테마 바탕">{MINDMAP_GROUNDS.map(([key,label])=>
      <button key={key} role="radio" aria-checked={th.ground===key} className={th.ground===key?'active':''} onClick={()=>setTheme({ground:key})}>{label}</button>)}</div>
     <button onClick={()=>changeMindmap(clearBranchStyles(mindmap))}>가지별 서식 지우기 (테마로 통일)</button>
    </fieldset>;})()}
    <button onClick={()=>{changeMindmap(autoLayoutMindmap(mindmap));fit();}}>자동 정렬 (수동 위치 초기화)</button>
    <p>도형을 끌어 이동 · 연결점을 끌어 부모 변경<br/>하위 가지는 단계 제한 없이 추가 (문서당 300개)</p>
    {mmNode?<><h2>선택 가지</h2>
     <label>내용<textarea aria-label="가지 내용" maxLength={200} value={mmNode.text} onChange={e=>changeMindmap(updateNode(mindmap,mmSelected,{text:e.target.value}))}/></label>
     <div className="tool-row"><button disabled={mmGraph.nodes.length>=300} onClick={()=>{const r=addChild(mindmap,mmSelected);changeMindmap(r.map,r.id);}}>＋ 하위 가지 (Tab)</button>
      <button disabled={mmGraph.nodes.length>=300} onClick={()=>{const r=addSibling(mindmap,mmSelected);changeMindmap(r.map,r.id);}}>＋ 같은 단계 (Enter)</button></div>
     <div className="tool-row"><button disabled={mmSelected===mindmap.root.id} onClick={()=>changeMindmap(moveNode(mindmap,mmSelected,-1))}>▲ 위로</button>
      <button disabled={mmSelected===mindmap.root.id} onClick={()=>changeMindmap(moveNode(mindmap,mmSelected,1))}>▼ 아래로</button>
      <button disabled={mmSelected===mindmap.root.id} onClick={()=>changeMindmap(removeNode(mindmap,mmSelected),mindmap.root.id)}>지우기</button></div>
     {mmSelected!==mindmap.root.id&&<><label>연결선 설명<input aria-label="가지 연결선 설명" maxLength={300} value={mmNode.edge?.label??''} onChange={e=>changeMindmap(updateNode(mindmap,mmSelected,{edge:{label:e.target.value}}))}/></label><button onClick={()=>changeMindmap(updateNode(mindmap,mmSelected,{edge:{hidden:!mmNode.edge?.hidden}}))}>{mmNode.edge?.hidden?'부모 연결선 표시':'부모 연결선 삭제 (가지 유지)'}</button></>}
     {mmSelected!==mindmap.root.id&&<EdgeStyleControls value={mmNode.edge?.style??mmGraph.edges.find(e=>e.target===mmSelected)?.data??EDGE_DEFAULT} onChange={style=>changeMindmap(updateNode(mindmap,mmSelected,{edge:{style}}))}/>}
     {(()=>{const shown=mmGraph?.nodes.find(n=>n.id===mmSelected)?.data??{};return <>
      <fieldset className="text-style"><legend>가지 모양</legend>
       <Select label="적용 범위" value={mmScope} options={MINDMAP_SCOPES} onChange={setMmScope}/>
       <div className="mm-shape-grid" role="radiogroup" aria-label="가지 모양">{MINDMAP_SHAPES.map(([key,label])=>
        <button key={key} role="radio" aria-checked={(shown.shape??'roundRect')===key} className={(shown.shape??'roundRect')===key?'active':''} title={label} onClick={()=>restyle({shape:key})}>
         <ShapeIcon shape={key==='text'?'rectangle':key}/><small>{label}</small></button>)}</div>
       <details className="shape-group"><summary>다른 도형</summary>
        <Select label="도형" value={shown.shape??'roundRect'} options={[...SHAPES.entries()].filter(([k])=>!LINE_SHAPES.has(k))} onChange={shape=>restyle({shape})}/></details>
       <ColorRow label="바탕색" value={shown.fill} onChange={fill=>restyle({fill})}/>
       <ColorRow label="테두리색" value={shown.stroke} onChange={stroke=>restyle({stroke})}/>
      </fieldset>
      <TextStyleControls label="가지 글자" value={{font:shown.font,size:shown.size,bold:shown.bold,textColor:shown.textColor}} onChange={patch=>restyle(patch)}/></>;})()}
    </>:<p>가지를 눌러 고르세요.</p>}
    <button onClick={()=>undo()}>실행 취소 (Ctrl+Z)</button>
   </aside>}
   {mode==='catalog'&&<aside>
    <div className="catalog-menu">
     <h2>서식 이름</h2>
     {!catalog&&<p>표 서식 목록을 불러오는 중…</p>}
     {catalog?.categories?.map(category=><button key={category.id} className={catalogCategory===category.id?'active':''} aria-pressed={catalogCategory===category.id} onClick={()=>{setCatalogCategory(category.id);setCatalogTemplate(category.templates[0]?.id??'');setCatalogCellSel({r:0,c:0});}}>{category.name}<small>{category.templates.length}개 모양</small></button>)}
     {selectedCatalogCategory&&<><h2>표 모양</h2>{selectedCatalogCategory.templates.map(template=><button key={template.id} className={catalogTemplate===template.id?'active':''} aria-pressed={catalogTemplate===template.id} onClick={()=>{setCatalogTemplate(template.id);setCatalogCellSel({r:0,c:0});}}>{template.name}<small>{template.rows}행 × {template.cols}열</small></button>)}</>}
    </div>
    {selectedCatalogTemplate&&activeCatalogCell&&<>
     {isStepTemplate ? <>
      <h2>단계(과제) 수</h2>
      <div className="presets">{FLOW_PRESETS.map(n=><button key={n} className={currentCatalogSteps===n?'active':''} aria-pressed={currentCatalogSteps===n} onClick={()=>changeCatalogSteps(n)}>{n}칸</button>)}</div>
      <Stepper label="단계(과제) 수" value={currentCatalogSteps} min={2} max={6} onChange={changeCatalogSteps}/>
     </> : (!isFixedCategory && <>
      <h2>표 크기</h2>
      <Stepper label="행(가로줄)" value={catalogGrid.length} min={1} max={100} onChange={resizeCatalogRows}/>
      <Stepper label="열(세로줄)" value={catalogColCount} min={1} max={50} onChange={resizeCatalogCols}/>
     </>)}
     <label className="check"><input type="checkbox" checked={catalogCustomBorder} onChange={e=>setCatalogCustomBorder(e.target.checked)}/>테두리 직접 고르기</label>
     <h2>편집 범위 ({ safeSelR+1 }행 { safeSelC+1 }칸)</h2>
     <div className="role-tabs">{CATALOG_SCOPES.map(([k,n])=><button key={k} className={catalogScope===k?'active':''} onClick={()=>setCatalogScope(k)}>{n}</button>)}</div>
     <TextStyleControls fill label={scopeLabel+' 서식'} value={activeCatalogCell.style} onChange={changeCatalogStyle}/>
     {catalogCustomBorder&&<BorderControls table={{kind:'grid',borders:{outer:activeCatalogCell.borders.top,inner:activeCatalogCell.borders.bottom}}} parts={['outer','inner']} onChange={changeCatalogBorderTable}/>}
     <div className="tool-row"><button onClick={resetCatalogTemplate}>원래 서식으로</button><button onClick={()=>undoCatalog()}>실행 취소 (Ctrl+Z)</button></div>
    </>}
    {catalog&&<p>{catalog.template_count}개 표 모양을 기본 표처럼 자유 편집해 HWPX로 저장하거나 복사합니다.</p>}
   </aside>}
   {TABLE_KINDS.includes(mode)&&table&&<aside>
    {mode==='flow'&&<><h2>방향</h2>
     <div className="role-tabs">{[['horizontal','가로 (→)'],['vertical','세로 (↓)']].map(([k,n])=><button key={k} className={(table.direction??'horizontal')===k?'active':''} onClick={()=>changeTable({...table,direction:k,arrow:k==='vertical'?DOWN_ARROWS[0]:ARROWS[0]})}>{n}</button>)}</div>
     <h2>단계 수</h2>
     <div className="presets">{FLOW_PRESETS.map(n=><button key={n} className={table.steps.length===n?'active':''} aria-pressed={table.steps.length===n} onClick={()=>changeTable(resizeFlow(table,n))}>{n}칸</button>)}</div>
     <Stepper label="단계" value={table.steps.length} min={2} max={MAX_FLOW_STEPS} onChange={n=>changeTable(resizeFlow(table,n))}/>
     <Stepper label={(table.direction==='vertical'?'옆으로':'아래로')+' 세부 칸'} value={table.rows??1} min={1} max={MAX_FLOW_ROWS} onChange={n=>changeTable(resizeFlowRows(table,n))}/>
     <Select label="화살표" value={table.arrow} options={(table.direction==='vertical'?DOWN_ARROWS:ARROWS).map(a=>[a,a])} onChange={arrow=>changeTable({...table,arrow})}/></>}
    {mode==='grid'&&<><h2>표 크기</h2>
     <Stepper label="행(가로줄)" value={table.rows.length} min={1} max={MAX_ROWS} onChange={n=>changeTable(resizeGrid(table,n,table.rows[0].length))}/>
     <Stepper label="열(세로줄)" value={table.rows[0].length} min={1} max={MAX_COLS} onChange={n=>changeTable(resizeGrid(table,table.rows.length,n))}/>
     <Stepper label="머리글 행" value={table.header_rows} min={0} max={Math.min(2,table.rows.length)} onChange={n=>changeTable({...table,header_rows:n})}/>
     <label className="check"><input type="checkbox" checked={table.use_basic_style} onChange={e=>changeTable({...table,use_basic_style:e.target.checked})}/>기본 표 서식 입히기</label>
     <label className="check"><input type="checkbox" checked={!!table.custom_border} onChange={e=>changeTable({...table,custom_border:e.target.checked})}/>테두리 직접 고르기</label></>}
    {mode==='org'&&<><h2>부서 수</h2><Stepper label="부서" value={table.units.length} min={1} max={MAX_ORG} onChange={n=>changeTable(resizeOrg(table,n))}/></>}
    <h2>글자 서식</h2>
    <div className="role-tabs">{ROLE_SETS[mode].map(r=><button key={r} className={role[mode]===r?'active':''} onClick={()=>setRole({...role,[mode]:r})}>{ROLE_NAMES[r]}</button>)}</div>
    <TextStyleControls fill label={ROLE_NAMES[role[mode]]} value={table.styles[role[mode]]} onChange={patch=>changeTable(setStyle(table,role[mode],patch))}/>
    {mode==='grid'&&table.custom[role.grid]&&<button onClick={()=>changeTable({...table,custom:{...table.custom,[role.grid]:false},styles:{...table.styles,[role.grid]:gridTable().styles[role.grid]}})}>{ROLE_NAMES[role.grid]} 기본 서식으로</button>}
    {(mode!=='grid'||table.custom_border)&&<BorderControls table={table} parts={BORDER_PARTS[mode]} onChange={changeTable}/>}
    <button onClick={()=>undo()}>실행 취소 (Ctrl+Z)</button>
   </aside>}
   <main><div className="flow-layer" style={{display:canvas?'block':'none'}}>{mode==='paint'&&!hasBackground&&<div className="paint-empty" aria-hidden="true"><b>📷 배경 사진을 여기에 끌어 놓으세요</b><span>탐색기에서 사진을 끌어 오면 바로 배경이 돼요(Ctrl+V도 돼요)</span></div>}<ReactFlow style={mmGraph?.background?{background:mmGraph.background}:undefined} nodes={shownNodes} edges={shownEdges} nodeTypes={nodeTypes} edgeTypes={edgeTypes} connectionMode={ConnectionMode.Loose} snapToGrid snapGrid={[10,10]}
    nodesDraggable={canvas} nodesConnectable={canvas} elementsSelectable
    onInit={instance=>{flow.current=instance;send({type:'ready',protocol_version:1,editor:FORMAT});}}
    onNodeClick={(_,n)=>{if(mode==='mindmap')setMmSelected(n.id);}}
    onPaneClick={()=>{if(mode==='mindmap')setMmSelected(null);}}
    onNodesChange={changes=>{
     if(mode==='mindmap'){
      const positions=Object.fromEntries(changes.filter(c=>c.type==='position'&&c.position).map(c=>[c.id,c.position]));
      const dimensions=changes.filter(c=>c.type==='dimensions'&&c.dimensions&&(c.resizing!==undefined||c.setAttributes));
      if(Object.keys(positions).length||dimensions.length){
       let map=positionMindmap(current.current.mindmap,positions);
       for(const c of dimensions)map=updateNode(map,c.id,{size:c.dimensions});
       const next={...current.current,mindmap:map};current.current=next;setGraph(next);mark();
      }return;
     }
     if(!drawable)return;
     // 스마트 가이드: 도형 하나를 끌 때 다른 도형의 가장자리·가운데에 맞춰 붙이고 빨간 점선을 보인다(PPT처럼).
     const moves=changes.filter(c=>c.type==='position'&&c.position);
     if(moves.length===1&&(moves[0].dragging||guides.length)){
      const moving=current.current.nodes.find(n=>n.id===moves[0].id);
      if(moving){
       const others=current.current.nodes.filter(n=>!n.selected&&n.id!==moving.id);
       const g=smartGuides({...moving,position:moves[0].position},others,8/(flow.current?.getZoom?.()||1)); // 화면 기준 8px
       changes=changes.map(c=>c===moves[0]?{...c,position:{x:g.x,y:g.y}}:c);
       setGuides(moves[0].dragging?g.lines:[]);
      }
     }else if(moves.some(c=>!c.dragging)||!moves.length&&guides.length)setGuides([]);
     const edits=changes.filter(c=>c.type!=='select'&&!(c.type==='dimensions'&&!c.resizing));
     let next={...current.current,nodes:applyNodeChanges(changes,current.current.nodes)};
     if(changes.some(c=>c.type==='dimensions'&&(c.resizing!==undefined||c.setAttributes)))next=layoutGraph(next);
     // 자석 연결선: 도형을 옮기면 마주 보는 면으로 다시 붙는다.
     const routed=autoRoute(next.nodes,next.edges);if(routed!==next.edges)next={...next,edges:routed};
     current.current=next;setGraph(next);if(edits.length)mark();
    }}
    onEdgesChange={changes=>{if(!drawable)return;const next={...current.current,edges:applyEdgeChanges(changes,current.current.edges)};current.current=next;setGraph(next);if(changes.some(c=>c.type!=='select'))mark();}}
    onNodeDragStart={()=>checkpoint()} onBeforeDelete={async({nodes,edges})=>{if(!drawable)return false;checkpoint();return {nodes:nodes.filter(n=>!n.data?.background),edges};}}
    onConnect={connection=>{
     if(mode==='mindmap'){try{changeMindmap(reparentNode(positionMindmap(current.current.mindmap,{}),connection.target,connection.source,{sourceHandle:connection.sourceHandle,targetHandle:connection.targetHandle}));}catch(error){setStatus(error.message);}return;}
     // 새 연결선은 자석 연결: 두 도형이 마주 보는 면에 붙고, 도형을 옮기면 따라간다(연결선 설정에서 끌 수 있음).
     const a=current.current.nodes.find(n=>n.id===connection.source),b=current.current.nodes.find(n=>n.id===connection.target);
     if(a&&b&&a.id!==b.id&&!LINE_SHAPES.has(a.data?.shape)&&!LINE_SHAPES.has(b.data?.shape)){commit({...current.current,edges:[...current.current.edges,magnetEdge(a,b)]});return;}
     commit({...current.current,edges:[...current.current.edges,edge(connection.source,connection.target,'',id(),connection.sourceHandle,connection.targetHandle,{...EDGE_DEFAULT})]});
    }}
    connectionRadius={40}
    onConnectEnd={(event,state)=>{
     // 연결점이 아니라 도형 몸체에 놓아도 붙인다(draw.io처럼). 이후 도형을 옮기면 마주 보는 면으로 따라간다.
     if(!drawable||state?.isValid||!state?.fromNode)return;
     const target=dropTarget(event,[state.fromNode.id]);
     const source=current.current.nodes.find(n=>n.id===state.fromNode.id);
     if(!target||!source)return;
     commit({...current.current,edges:[...current.current.edges,magnetEdge(source,target)]});
    }}
    edgesReconnectable={drawable}
    onReconnect={(old,connection)=>{if(!drawable)return;
     const edges=reconnectEdge(old,connection,current.current.edges,{shouldReplaceId:false}).map(e=>e.id===old.id?{...e,data:{...(e.data??EDGE_DEFAULT),autoSide:false}}:e);
     commit({...current.current,edges});}}
    onReconnectEnd={(event,old,handleType,state)=>{
     if(!drawable||state?.isValid)return;
     const fixed=handleType==='source'?old.target:old.source;
     const target=dropTarget(event,[fixed]);if(!target)return;
     const other=current.current.nodes.find(n=>n.id===fixed);if(!other)return;
     const [a,b]=handleType==='source'?[target,other]:[other,target];
     const [s,t]=facingSides(a,b);
     commit({...current.current,edges:current.current.edges.map(e=>e.id===old.id?{...e,source:a.id,target:b.id,sourceHandle:s,targetHandle:t,data:{...(e.data??EDGE_DEFAULT),autoSide:true}}:e)});
    }}
    onNodeDragStop={()=>setGuides([])}
    onSelectionDragStart={()=>checkpoint()} onNodeDoubleClick={()=>{setStatus('왼쪽 내용 입력에서 수정하세요.');}}
    fitView deleteKeyCode={drawable?['Backspace','Delete']:null}><Background gap={20}/><Controls/><MiniMap/>
    {guides.length>0&&<ViewportPortal><svg className="smart-guides" style={{position:'absolute',left:0,top:0,overflow:'visible',pointerEvents:'none'}}>
     {guides.map((l,i)=><line key={i} x1={l.x1} y1={l.y1} x2={l.x2} y2={l.y2} stroke="#EF4444" strokeWidth="1" strokeDasharray="4 3"/>)}</svg></ViewportPortal>}</ReactFlow>
    {mode==='paint'&&paintTool==='pen'&&<div className="pen-layer" aria-label="펜으로 그리기" onPointerDown={penDown} onPointerMove={penMove} onPointerUp={penUp} onPointerCancel={penUp}>
     {penLive&&<svg width="100%" height="100%"><polyline points={penLive.map(p=>p.join(',')).join(' ')} fill="none" stroke={penColor} strokeWidth={penWidth*(flow.current?.getZoom?.()??1)} strokeLinecap="round" strokeLinejoin="round"/></svg>}</div>}</div>
    {mode==='catalog'&&<div className="catalog-preview"><div className="catalog-preview-card">
     <h2>{selectedCatalogTemplate?.name??'표 서식을 선택하세요'}</h2>
     {selectedCatalogTemplate?<><p>{catalogGrid.length}행 × {catalogColCount}열 · {isStepTemplate?'단계별 정보단위+연결단위 연동 편집':isFixedCategory?'고정 서식 요소 편집 및 복사':'기본 표 자유 편집 (행·열 끼우기, 글자·바탕·테두리 서식, 병합 미리보기)'}</p>
      <div className="catalog-structure-tools">
       {isStepTemplate ? <>
        <span style={{marginRight:6,fontWeight:600}}>과제 수:</span>
        {FLOW_PRESETS.map(n=><button key={n} className={currentCatalogSteps===n?'active':''} onClick={()=>changeCatalogSteps(n)}>{n}단계</button>)}
        <span>현재 {currentCatalogSteps}단계 ({catalogGrid.length}행 × {catalogColCount}열) · 선택: {safeSelR+1}행 {safeSelC+1}칸</span>
       </> : (!isFixedCategory ? <>
        <button onClick={()=>changeCatalogStructure('add_row')}>＋ 행 추가</button>
        <button onClick={()=>changeCatalogStructure('delete_row')}>− 마지막 행 삭제</button>
        <button onClick={()=>changeCatalogStructure('add_column')}>＋ 열 추가</button>
        <button onClick={()=>changeCatalogStructure('delete_column')}>− 마지막 열 삭제</button>
        <span>현재 {catalogGrid.length}행 × {catalogColCount}열 · 선택: {safeSelR+1}행 {safeSelC+1}칸</span>
       </> : <>
        <span>고정 서식 ({catalogGrid.length}행 × {catalogColCount}열) · 원하는 칸을 눌러 글자·서식을 편집하거나 복사·저장하세요.</span>
       </>)}
      </div>
      <div className="catalog-table-scroll"><table className="grid-preview catalog-grid-preview">
       {(!isStepTemplate && !isFixedCategory) && <thead><tr><th/>{Array.from({length:catalogColCount},(_,c)=><th key={c}><span className="col-tools">
        <button title="왼쪽에 열 끼우기" aria-label={(c+1)+'열 앞에 열 끼우기'} disabled={catalogColCount>=50} onClick={()=>changeCatalogStructure({op:'insert_column',index:c})}>+</button>
        <button title="이 열 빼기" aria-label={(c+1)+'열 빼기'} disabled={catalogColCount<=1} onClick={()=>changeCatalogStructure({op:'delete_column',index:c})}>×</button></span></th>)}</tr></thead>}
       <tbody>{catalogGrid.map((row,r)=><tr key={r}>
        {(!isStepTemplate && !isFixedCategory) && <th><span className="row-tools">
         <button title="위에 행 끼우기" aria-label={(r+1)+'행 위에 행 끼우기'} disabled={catalogGrid.length>=100} onClick={()=>changeCatalogStructure({op:'insert_row',index:r})}>+</button>
         <button title="이 행 빼기" aria-label={(r+1)+'행 빼기'} disabled={catalogGrid.length<=1} onClick={()=>changeCatalogStructure({op:'delete_row',index:r})}>×</button></span></th>}
        {row.map((cell,c)=><td key={c} rowSpan={cell.rowSpan} colSpan={cell.colSpan} className={safeSelR===r&&safeSelC===c?'selected-cell':''}
         style={{background:cell.style.fill||'white',borderTop:cssBorder(cell.borders.top),borderBottom:cssBorder(cell.borders.bottom),borderLeft:cssBorder(cell.borders.left),borderRight:cssBorder(cell.borders.right)}}
         onClick={()=>setCatalogCellSel({r,c})}>
         <input className="catalog-cell" aria-label={`${r+1}행 ${c+1}번째 칸`} maxLength={2000} value={cell.text}
          onFocus={()=>setCatalogCellSel({r,c})}
          style={{...cssOf(cell.style),background:'transparent',textAlign:cell.align==='LEFT'?'left':cell.align==='RIGHT'?'right':'center'}}
          onChange={e=>setCatalogCell(r,c,e.target.value)}/></td>)}</tr>)}</tbody></table></div>
      <p className="hint">칸을 눌러 글을 바로 고치고, 행·열 머리의 +/×로 원하는 자리에 행·열을 끼우거나 뺍니다. 왼쪽에서 선택 칸·행·열·표 전체의 글꼴·크기·굵게·글자색·바탕색과 테두리(한/글 12종)도 자유롭게 바꿀 수 있어요. 투명선은 한/글 화면처럼 빨간 점선으로 보입니다.</p>
      <button className="primary" onClick={exportCatalog}>이 표 모양을 HWPX로 저장</button></>:<p>{catalog?'왼쪽에서 서식 이름과 표 모양을 선택하세요.':'표 서식 목록을 불러오는 중…'}</p>}
    </div></div>}
    {mode==='flow'&&table&&<FlowTableView table={table} onChange={changeTable}/>}
    {mode==='grid'&&table&&<GridTableView table={table} onChange={changeTable}/>}
    {mode==='org'&&table&&<OrgTableView table={table} onChange={changeTable}/>}
    {mode==='bar'&&table&&<BarTableView table={table} onChange={changeTable}/>}</main>
  </div><footer role="status">{status} · 로컬 저장</footer>
 </div></HistoryContext.Provider>;
}
function mmGraphCount(map){let count=0,stack=[map.root];while(stack.length){const node=stack.pop();count++;stack.push(...node.children);}return count;}
createRoot(document.getElementById('root')).render(<ReactFlowProvider><App/></ReactFlowProvider>);
