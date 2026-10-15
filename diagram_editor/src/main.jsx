import React,{useRef,useState,useEffect,createContext,useContext} from 'react';
import {createRoot} from 'react-dom/client';
import {ReactFlow,ReactFlowProvider,Background,Controls,MiniMap,Handle,Position,ConnectionMode,applyNodeChanges,applyEdgeChanges,NodeResizer,BaseEdge,useReactFlow} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import './style.css';
import {FORMAT,PALETTE,templates,template,node,edge,id,decode,validate,svg,layoutGraph,computeNodeAutoFitBox,edgeLabelBox,LINE_HEIGHT,nodeFont,nodePaint,edgePath,EDGE_DEFAULT} from './model.js';
import {SHAPE_GROUPS,SHAPES,LINE_SHAPES,shapePath,DASHES,MARKERS,dashArray} from './shapes.js';
import {sampleMindmap,mindmapGraph,addChild,addSibling,removeNode,updateNode,moveNode,findNode} from './mindmap.js';
import {FONTS,registerFonts,ARROWS,DOWN_ARROWS,FLOW_PRESETS,MAX_FLOW_STEPS,MAX_FLOW_ROWS,MAX_ROWS,MAX_COLS,MAX_ORG,ROLE_NAMES,BORDER_TYPES,BORDER_WIDTHS,BORDER_NAMES,
 flowTable,gridTable,orgTable,barTable,flowDetails,resizeFlow,resizeFlowRows,insertStep,removeStep,resizeGrid,insertRow,removeRow,insertCol,removeCol,resizeOrg,
 setStyle,setBorder,exportSpec,cssOf,cssBorder} from './table.js';

const TITLE='표/다이어그램';
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

/** 도형 노드: PPT 도형 경로를 SVG로 그리고 글을 가운데에 얹는다. 선 도형은 화살표 머리를 붙인다. */
function FlowNode({id:nodeId,data,selected,width,height}){
 const box=computeNodeAutoFitBox({data,width,height}),f=nodeFont(data),p=nodePaint(data);
 const resizeStart=useContext(HistoryContext);
 const w=width??220,h=height??90,inset=Math.max(1,p.width/2+1),line=LINE_SHAPES.has(data.shape);
 const key='n'+safeId(nodeId);
 const start=data.lineStart??p.startDefault,end=p.end;
 return <><NodeResizer onResizeStart={resizeStart} isVisible={selected} minWidth={line?20:40} minHeight={line?10:30}/>
  {Object.entries(Position).map(([k,value])=><Handle key={k} id={value} type="source" position={value}/>)}
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
  </div></>;
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

const TABLE_KINDS=['flow','grid','org','bar'];
const ROLE_SETS={flow:['step','date','arrow'],grid:['head','body'],org:['root','unit','detail'],bar:['title','note']};
const BORDER_PARTS={flow:['line','split'],grid:['outer','inner'],org:['box','link'],bar:['box','line']};
const newTables=()=>({flow:flowTable(5),grid:gridTable(4,4),org:orgTable(4),bar:barTable()});

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
 const [mode,setMode]=useState('diagram'),[role,setRole]=useState({flow:'step',grid:'head',org:'root',bar:'title'});
 const [mmSelected,setMmSelected]=useState(null);
 // 도형 묶음 펼침 상태(도형을 넣어도 펼친 묶음이 접히지 않게 기억한다).
 const [openGroups,setOpenGroups]=useState(()=>new Set(['사각형','기본 도형','선']));
 const flow=useRef(null),current=useRef(graph),history=useRef([]),future=useRef([]),nameRef=useRef(name),clipboard=useRef(null);
 current.current=graph;nameRef.current=name;
 const generation=useRef(0),savedGeneration=useRef(0);
 const mark=()=>{generation.current++;send({type:'dirty',value:true,generation:generation.current});};
 const checkpoint=()=>{history.current.push(structuredClone(current.current));if(history.current.length>80)history.current.shift();future.current=[];};
 const commit=(next,record=true)=>{if(record)checkpoint();next=layoutGraph(next);current.current=next;setGraph(next);mark();};
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
  if(next.table)setMode(next.table.kind);else if(next.mindmap&&!next.nodes.length)setMode('mindmap');
 };
 const snapshot=()=>validate({format:FORMAT,version:1,...current.current});
 const table=TABLE_KINDS.includes(mode)?(graph.table?.kind===mode?graph.table:tables.current[mode]):null;
 const changeTable=next=>{tables.current[next.kind]=next;commit({...current.current,table:next});};
 const mindmap=graph.mindmap??null;
 const changeMindmap=(next,select)=>{commit({...current.current,mindmap:next});if(select!==undefined)setMmSelected(select);};
 const switchMode=next=>{
  setMode(next);
  if(TABLE_KINDS.includes(next)&&current.current.table?.kind!==next){current.current={...current.current,table:tables.current[next]};setGraph(current.current);}
  if(next==='mindmap'&&!current.current.mindmap){current.current={...current.current,mindmap:sampleMindmap()};setGraph(current.current);}
  setStatus({flow:'칸 수를 고르고 칸 글을 바로 고치세요. 다 되면 ‘한/글 문서로 저장’을 누르세요.',grid:'행·열을 늘리거나 줄이고 칸 글을 고치세요.',
   org:'윗 상자와 부서 이름을 고치고 부서 수를 정하세요.',bar:'왼쪽 글과 오른쪽 날짜를 고치세요.',
   mindmap:'가지를 고르고 Tab=하위 가지, Enter=같은 단계 가지, Delete=지우기.'}[next]??'도형을 추가하고 연결점을 끌어 연결하세요.');
  if(next==='diagram'||next==='mindmap')fit();
 };
 const handle=useRef(null);
 handle.current=async message=>{
  if(!message||typeof message!=='object')return;
  try{
   switch(message.type){
    case 'new':tables.current=newTables();setMmSelected(null);replace({nodes:[],edges:[]},'새 '+TITLE,false);setMode('diagram');send({type:'document_new'});break;
    case 'mark_saved':
     if(Number.isInteger(message.generation))savedGeneration.current=Math.max(savedGeneration.current,message.generation);
     send({type:'dirty',value:generation.current>savedGeneration.current,generation:generation.current});
     setStatus(generation.current>savedGeneration.current?'추가 변경사항을 저장해 주세요.':'저장했습니다.');break;
    case 'load':{
     const loaded=decode(message.snapshot);
     if(loaded.table)tables.current[loaded.table.kind]=loaded.table;
     replace({nodes:loaded.nodes,edges:loaded.edges,...(loaded.table?{table:loaded.table}:{}),...(loaded.mindmap?{mindmap:loaded.mindmap}:{})},message.name,loaded.converted);
     send({type:'document_loaded',converted:loaded.converted});break;
    }
    case 'apply_template':{
     const value=template(message.template);commit({...current.current,nodes:value.nodes,edges:value.edges});setName(value.name);setMode('diagram');fit();
     send({type:'template_applied',template:message.template,name:value.name});break;
    }
    case 'save':{
     const nextName=message.name??nameRef.current;setName(nextName);
     send({type:'save_document',id:message.id??null,name:nextName,generation:generation.current,snapshot:snapshot()});break;
    }
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
      send({type:'export_png',name:nameRef.current,base64});
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
 const duplicate=()=>{
  const items=current.current.nodes.filter(n=>n.selected);if(!items.length)return;
  const copies=items.map(n=>({...structuredClone(n),id:id(),position:{x:n.position.x+30,y:n.position.y+30},selected:true}));
  commit({...current.current,nodes:[...current.current.nodes.map(n=>({...n,selected:false})),...copies]});
 };
 useEffect(()=>{
  const keys=e=>{
   if(['INPUT','TEXTAREA','SELECT'].includes(e.target.tagName)||e.target.isContentEditable)return;
   const ctrl=e.ctrlKey||e.metaKey,k=e.key.toLowerCase();
   if(ctrl&&k==='s'){e.preventDefault();send({type:'request_save'});}
   if(ctrl&&k==='z'){e.preventDefault();undo(e.shiftKey);}
   if(ctrl&&k==='y'){e.preventDefault();undo(true);}
   if(mode==='diagram'&&ctrl&&k==='d'){e.preventDefault();duplicate();}
   if(mode==='diagram'&&ctrl&&k==='c'){clipboard.current=structuredClone(current.current.nodes.filter(n=>n.selected));}
   if(mode==='diagram'&&ctrl&&k==='v'&&clipboard.current?.length){e.preventDefault();
    const copies=clipboard.current.map(n=>({...n,id:id(),position:{x:n.position.x+40,y:n.position.y+40},selected:true}));
    commit({...current.current,nodes:[...current.current.nodes.map(n=>({...n,selected:false})),...copies]});}
   if(mode==='mindmap'&&mindmap&&mmSelected){
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
 // 마인드맵: 자동 배치한 도형·연결선을 같은 화면에 그린다(끌어 옮기기 대신 가지 순서·배치로 정리).
 const mmGraph=mode==='mindmap'&&mindmap?layoutGraph(mindmapGraph(mindmap)):null;
 const mmNode=mindmap&&mmSelected?findNode(mindmap,mmSelected)?.node:null;
 const shownNodes=mmGraph?mmGraph.nodes.map(n=>({...n,selected:n.id===mmSelected,draggable:false,connectable:false})):graph.nodes;
 const shownEdges=mmGraph?mmGraph.edges:graph.edges;
 const tabs=[['diagram','다이어그램'],['mindmap','마인드맵'],['flow','흐름표'],['grid','기본 표'],['org','조직표'],['bar','장식표']];
 const canvas=mode==='diagram'||mode==='mindmap';
 return <HistoryContext.Provider value={checkpoint}><div className="editor-shell">
  <header><strong>{TITLE}</strong><span className="document-name">{name}</span>
   <div className="mode-tabs" role="tablist" aria-label="만들 것">{tabs.map(([key,label])=><button key={key} role="tab" aria-selected={mode===key} className={mode===key?'active':''} onClick={()=>switchMode(key)}>{label}</button>)}</div>
   <nav>
   <button onClick={()=>send({type:'request_new'})}>새 문서</button>
   <button onClick={()=>send({type:'request_list'})}>열기·삭제</button>
   <button onClick={()=>send({type:'request_save'})}>저장</button>
   {canvas?<>
    <button disabled={busy} onClick={()=>send({type:'request_png'})}>{busy?'PNG 변환 중…':'PNG 내보내기'}</button>
    {mode==='diagram'&&<select aria-label="예시 서식" value="" onChange={e=>send({type:'request_template',template:e.target.value})}><option value="">예시 서식</option>{Object.entries(templates).map(([key,t])=><option key={key} value={key}>{t.name}</option>)}</select>}
   </>:<button className="primary" onClick={exportHwpx}>한/글 문서로 저장</button>}
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
     <EdgeStyleControls value={selectedEdge.data} onChange={editEdge}/></>}
    <p>연결점을 끌어 도형 연결<br/>Shift+선택: 여러 도형<br/>Ctrl+C/V 복사·붙여넣기, Ctrl+D 복제<br/>Delete: 선택 삭제 · Ctrl+휠: 확대·축소</p>
   </aside>}
   {mode==='mindmap'&&mindmap&&<aside><h2>마인드맵</h2>
    <Select label="배치" value={mindmap.layout} options={[['both','가운데에서 좌우로'],['right','오른쪽으로'],['down','위에서 아래로(조직도형)']]} onChange={layout=>{changeMindmap({...mindmap,layout});fit();}}/>
    {mmNode?<><h2>선택 가지</h2>
     <label>내용<textarea aria-label="가지 내용" maxLength={200} value={mmNode.text} onChange={e=>changeMindmap(updateNode(mindmap,mmSelected,{text:e.target.value}))}/></label>
     <div className="tool-row"><button onClick={()=>{const r=addChild(mindmap,mmSelected);changeMindmap(r.map,r.id);}}>＋ 하위 가지 (Tab)</button>
      <button onClick={()=>{const r=addSibling(mindmap,mmSelected);changeMindmap(r.map,r.id);}}>＋ 같은 단계 (Enter)</button></div>
     <div className="tool-row"><button disabled={mmSelected===mindmap.root.id} onClick={()=>changeMindmap(moveNode(mindmap,mmSelected,-1))}>▲ 위로</button>
      <button disabled={mmSelected===mindmap.root.id} onClick={()=>changeMindmap(moveNode(mindmap,mmSelected,1))}>▼ 아래로</button>
      <button disabled={mmSelected===mindmap.root.id} onClick={()=>changeMindmap(removeNode(mindmap,mmSelected),mindmap.root.id)}>지우기</button></div>
     {(()=>{const shown=mmGraph?.nodes.find(n=>n.id===mmSelected)?.data??{};return <>
      <fieldset className="text-style"><legend>가지 모양</legend>
       <Select label="도형" value={shown.shape??'roundRect'} options={[...SHAPES.entries()].filter(([k])=>!LINE_SHAPES.has(k))} onChange={shape=>changeMindmap(updateNode(mindmap,mmSelected,{style:{shape}}))}/>
       <ColorRow label="바탕색" value={shown.fill} onChange={fill=>changeMindmap(updateNode(mindmap,mmSelected,{style:{fill}}))}/>
       <ColorRow label="테두리색" value={shown.stroke} onChange={stroke=>changeMindmap(updateNode(mindmap,mmSelected,{style:{stroke}}))}/>
      </fieldset>
      <TextStyleControls label="가지 글자" value={{font:shown.font,size:shown.size,bold:shown.bold,textColor:shown.textColor}} onChange={patch=>changeMindmap(updateNode(mindmap,mmSelected,{style:patch}))}/></>;})()}
    </>:<p>가지를 눌러 고르세요.</p>}
    <button onClick={()=>undo()}>실행 취소 (Ctrl+Z)</button>
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
   <main><div className="flow-layer" style={{display:canvas?'block':'none'}}><ReactFlow nodes={shownNodes} edges={shownEdges} nodeTypes={nodeTypes} edgeTypes={edgeTypes} connectionMode={ConnectionMode.Loose} snapToGrid snapGrid={[10,10]}
    nodesDraggable={mode==='diagram'} nodesConnectable={mode==='diagram'} elementsSelectable
    onInit={instance=>{flow.current=instance;send({type:'ready',protocol_version:1,editor:FORMAT});}}
    onNodeClick={(_,n)=>{if(mode==='mindmap')setMmSelected(n.id);}}
    onPaneClick={()=>{if(mode==='mindmap')setMmSelected(null);}}
    onNodesChange={changes=>{
     if(mode!=='diagram')return;
     const edits=changes.filter(c=>c.type!=='select'&&!(c.type==='dimensions'&&!c.resizing));
     let next={...current.current,nodes:applyNodeChanges(changes,current.current.nodes)};
     if(changes.some(c=>c.type==='dimensions'&&(c.resizing!==undefined||c.setAttributes)))next=layoutGraph(next);
     current.current=next;setGraph(next);if(edits.length)mark();
    }}
    onEdgesChange={changes=>{if(mode!=='diagram')return;const next={...current.current,edges:applyEdgeChanges(changes,current.current.edges)};current.current=next;setGraph(next);if(changes.some(c=>c.type!=='select'))mark();}}
    onNodeDragStart={()=>checkpoint()} onBeforeDelete={async()=>{if(mode!=='diagram')return false;checkpoint();return true;}}
    onConnect={connection=>commit({...current.current,edges:[...current.current.edges,edge(connection.source,connection.target,'',id(),connection.sourceHandle,connection.targetHandle,{...EDGE_DEFAULT})]})}
    onSelectionDragStart={()=>checkpoint()} onNodeDoubleClick={()=>{setStatus('왼쪽 내용 입력에서 수정하세요.');}}
    fitView deleteKeyCode={mode==='diagram'?['Backspace','Delete']:null}><Background gap={20}/><Controls/><MiniMap/></ReactFlow></div>
    {mode==='flow'&&table&&<FlowTableView table={table} onChange={changeTable}/>}
    {mode==='grid'&&table&&<GridTableView table={table} onChange={changeTable}/>}
    {mode==='org'&&table&&<OrgTableView table={table} onChange={changeTable}/>}
    {mode==='bar'&&table&&<BarTableView table={table} onChange={changeTable}/>}</main>
  </div><footer role="status">{status} · 로컬 저장</footer>
 </div></HistoryContext.Provider>;
}
createRoot(document.getElementById('root')).render(<ReactFlowProvider><App/></ReactFlowProvider>);
