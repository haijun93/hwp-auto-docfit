import React,{useRef,useState,useEffect,createContext,useContext} from 'react';
import {createRoot} from 'react-dom/client';
import {ReactFlow,ReactFlowProvider,Background,Controls,MiniMap,Handle,Position,ConnectionMode,applyNodeChanges,applyEdgeChanges,NodeResizer,BaseEdge,useReactFlow} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import './style.css';
import {FORMAT,COLORS,templates,template,node,edge,id,decode,validate,svg,layoutGraph,computeNodeAutoFitBox,edgeLabelBox,LINE_HEIGHT,nodeFont} from './model.js';
import {FONTS,ARROWS,FLOW_PRESETS,MAX_FLOW_STEPS,MAX_ROWS,MAX_COLS,ROLE_NAMES,flowTable,gridTable,resizeFlow,insertStep,removeStep,resizeGrid,insertRow,removeRow,insertCol,removeCol,setStyle,exportSpec,cssOf} from './table.js';

const TITLE='표/다이어그램';
function send(message){
 const host=window.chrome?.webview;
 if(window.parent!==window)window.parent.postMessage(message,window.location.origin);
 else if(host)host.postMessage(JSON.stringify(message));
}
const HistoryContext=createContext(()=>{});
function FlowNode({data,selected,width,height}){
 const box=computeNodeAutoFitBox({data,width,height}),f=nodeFont(data);
 const resizeStart=useContext(HistoryContext);
 return <><NodeResizer onResizeStart={resizeStart} isVisible={selected} minWidth={80} minHeight={50}/>
  {Object.entries(Position).map(([key,value])=><Handle key={key} id={value} type="source" position={value}/>)}
  <div className={'node-body '+data.shape} style={{background:COLORS[data.color]}}>{data.shape==='diamond'&&<svg className="diamond-background" viewBox="0 0 220 90" preserveAspectRatio="none"><polygon points="110,2 218,45 110,88 2,45" fill={COLORS[data.color]} stroke="#475569" strokeWidth="2"/></svg>}<span className="node-lines" style={{fontFamily:f.family,fontSize:f.px,lineHeight:f.lineHeight+'px',fontWeight:f.weight,color:f.color}}>{box.lines.map((line,i)=><span key={i} style={{display:'block',height:f.lineHeight}}>{line||' '}</span>)}</span></div></>;
}
function FlowEdge(props){
 const flow=useReactFlow(),nodes=flow.getNodes(),a=nodes.find(n=>n.id===props.source),b=nodes.find(n=>n.id===props.target);
 if(!a||!b)return null;
 const e={...props,sourceHandle:props.sourcePosition,targetHandle:props.targetPosition};
 const box=edgeLabelBox(e,nodes);
 const horizontal=['left','right'].includes(props.sourcePosition);
 const {sourceX:x1,sourceY:y1,targetX:x2,targetY:y2}=props;
 const path=horizontal?'M '+x1+' '+y1+' H '+((x1+x2)/2)+' V '+y2+' H '+x2:'M '+x1+' '+y1+' V '+((y1+y2)/2)+' H '+x2+' V '+y2;
 return <><BaseEdge id={props.id} path={path} markerEnd={props.markerEnd} style={props.style}/>
 {props.label&&<g><rect x={box.x-box.width/2} y={box.y-box.height/2} width={box.width} height={box.height} fill="white"/>
 {box.lines.map((line,i)=><text xmlSpace="preserve" key={i} x={box.x} y={box.y+(i-(box.lines.length-1)/2)*LINE_HEIGHT} textAnchor="middle" dominantBaseline="central" style={{fontSize:16,fontFamily:'"Malgun Gothic","Noto Sans KR",sans-serif'}}>{line}</text>)}</g>}</>;
}
const edgeTypes={smoothstep:FlowEdge};
const nodeTypes={flow:FlowNode};

/** 글꼴·크기(pt)·굵게·글자색(·바탕색) 고르기. 표 칸과 다이어그램 도형이 같이 쓴다. */
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

function Stepper({label,value,min,max,onChange}){
 return <div className="stepper-row"><span>{label}</span><span className="stepper"><button aria-label={label+' 줄이기'} disabled={value<=min} onClick={()=>onChange(value-1)}>−</button><output aria-live="polite">{value}</output><button aria-label={label+' 늘리기'} disabled={value>=max} onClick={()=>onChange(value+1)}>+</button></span></div>;
}

/** 흐름표 미리보기: 단계 카드 + 화살표. 칸 글을 바로 고치고, 칸 사이에 단계를 끼우거나 뺄 수 있다. */
function FlowTableView({table,onChange}){
 const s=table.styles;
 const update=(i,patch)=>onChange({...table,steps:table.steps.map((step,j)=>j===i?{...step,...patch}:step)});
 return <div className="table-canvas"><div className="flow-strip" style={{gridTemplateColumns:table.steps.map((_,i)=>i?'34px 1fr':'1fr').join(' ')}}>
  {table.steps.map((step,i)=><React.Fragment key={i}>
   {i>0&&<div className="flow-arrow" style={cssOf(s.arrow)}>{table.arrow}<button className="insert" title="여기에 단계 끼우기" aria-label={i+'번째 단계 뒤에 단계 끼우기'} disabled={table.steps.length>=MAX_FLOW_STEPS} onClick={()=>onChange(insertStep(table,i))}>+</button></div>}
   <div className="flow-step">
    <textarea className="cell step" rows={2} aria-label={(i+1)+'번째 단계 이름'} maxLength={200} value={step.title} style={cssOf(s.step)} onChange={e=>update(i,{title:e.target.value})}/>
    <textarea className="cell date" rows={2} aria-label={(i+1)+'번째 단계 일정'} maxLength={200} value={step.date} placeholder="일정" style={cssOf(s.date)} onChange={e=>update(i,{date:e.target.value})}/>
    <button className="remove" title="이 단계 빼기" aria-label={(i+1)+'번째 단계 빼기'} disabled={table.steps.length<=2} onClick={()=>onChange(removeStep(table,i))}>×</button>
   </div>
  </React.Fragment>)}
 </div><p className="hint">칸 글을 바로 고치세요. 칸 사이 +로 단계를 끼우고, ×로 뺍니다. 한/글에서는 위 행과 아래 행 사이가 이중선입니다.</p></div>;
}

/** 기본 표 미리보기: 칸 글을 바로 고치고, 행·열 머리의 +/×로 그 자리에 행·열을 끼우거나 뺀다. */
function GridTableView({table,onChange}){
 const cols=table.rows[0].length,s=table.styles;
 const update=(r,c,value)=>onChange({...table,rows:table.rows.map((row,i)=>i===r?row.map((v,j)=>j===c?value:v):row)});
 return <div className="table-canvas"><table className="grid-preview"><thead><tr><th/>{Array.from({length:cols},(_,c)=><th key={c}><span className="col-tools">
  <button title="왼쪽에 열 끼우기" aria-label={(c+1)+'열 앞에 열 끼우기'} disabled={cols>=MAX_COLS} onClick={()=>onChange(insertCol(table,c))}>+</button>
  <button title="이 열 빼기" aria-label={(c+1)+'열 빼기'} disabled={cols<=1} onClick={()=>onChange(removeCol(table,c))}>×</button></span></th>)}</tr></thead>
  <tbody>{table.rows.map((row,r)=><tr key={r}><th><span className="row-tools">
   <button title="위에 행 끼우기" aria-label={(r+1)+'행 위에 행 끼우기'} disabled={table.rows.length>=MAX_ROWS} onClick={()=>onChange(insertRow(table,r))}>+</button>
   <button title="이 행 빼기" aria-label={(r+1)+'행 빼기'} disabled={table.rows.length<=1} onClick={()=>onChange(removeRow(table,r))}>×</button></span></th>
   {row.map((value,c)=>{const role=r<table.header_rows?'head':'body';return <td key={c} style={{background:(table.custom[role]||role==='head')?s[role].fill||'white':'white'}}>
    <input className="cell" aria-label={(r+1)+'행 '+(c+1)+'열'} maxLength={200} value={value} style={{...cssOf(s[role]),background:'transparent'}} onChange={e=>update(r,c,e.target.value)}/></td>;})}
  </tr>)}</tbody></table>
  <p className="hint">{table.use_basic_style?'한/글로 저장하면 앱의 기본 표 서식(준말 ‘표’)을 입히고, 직접 고른 글자 서식만 덧입힙니다.':'기본 표 서식 없이 고른 글자 서식과 얇은 실선으로 만듭니다.'}</p></div>;
}

function App(){
 const [graph,setGraph]=useState({nodes:[],edges:[]}),[name,setName]=useState('새 '+TITLE),[busy,setBusy]=useState(false),[status,setStatus]=useState('도형을 추가하고 연결점을 끌어 연결하세요.');
 const [mode,setMode]=useState('diagram'),[flowRole,setFlowRole]=useState('step'),[gridRole,setGridRole]=useState('head');
 const flow=useRef(null),current=useRef(graph),history=useRef([]),future=useRef([]),nameRef=useRef(name);
 current.current=graph;nameRef.current=name;
 const generation=useRef(0),savedGeneration=useRef(0);
 const mark=()=>{generation.current++;send({type:'dirty',value:true,generation:generation.current});};
 const checkpoint=()=>{history.current.push(structuredClone(current.current));if(history.current.length>80)history.current.shift();future.current=[];};
 const commit=(next,record=true)=>{if(record)checkpoint();next=layoutGraph(next);current.current=next;setGraph(next);mark();};
 const undo=(redo=false)=>{
  const stack=redo?future:history,other=redo?history:future;if(!stack.current.length)return;
  other.current.push(structuredClone(current.current));const next=stack.current.pop();current.current=next;setGraph(next);mark();
 };
 const fit=()=>setTimeout(()=>flow.current?.fitView({padding:.18}),30);
 const replace=(next,title,dirty)=>{
  next=layoutGraph(next);current.current=next;setGraph(next);setName(title);history.current=[];future.current=[];
  generation.current++;if(!dirty)savedGeneration.current=generation.current;
  send({type:'dirty',value:dirty,generation:generation.current});fit();
  if(next.table)setMode(next.table.kind);
 };
 const snapshot=()=>validate({format:FORMAT,version:1,...current.current});
 // 표 탭: 흐름표·기본 표는 따로 기억하고, 저장할 때는 지금(또는 마지막) 표를 문서에 함께 넣는다.
 const tables=useRef({flow:flowTable(5),grid:gridTable(4,4)});
 const table=mode==='diagram'?null:(graph.table?.kind===mode?graph.table:tables.current[mode]);
 const changeTable=next=>{tables.current[next.kind]=next;commit({...current.current,table:next});};
 const switchMode=next=>{
  setMode(next);
  if(next!=='diagram'&&current.current.table?.kind!==next){const value=tables.current[next];current.current={...current.current,table:value};setGraph(current.current);}
  setStatus(next==='flow'?'칸 수를 고르고 칸 글을 바로 고치세요. 다 되면 ‘한/글 문서로 저장’을 누르세요.':next==='grid'?'행·열을 늘리거나 줄이고 칸 글을 고치세요.':'도형을 추가하고 연결점을 끌어 연결하세요.');
  if(next==='diagram')fit();
 };
 const handle=useRef(null);
 handle.current=async message=>{
  if(!message||typeof message!=='object')return;
  try{
   switch(message.type){
    case 'new':tables.current={flow:flowTable(5),grid:gridTable(4,4)};replace({nodes:[],edges:[]},'새 '+TITLE,false);send({type:'document_new'});break;
    case 'mark_saved':
     if(Number.isInteger(message.generation))savedGeneration.current=Math.max(savedGeneration.current,message.generation);
     send({type:'dirty',value:generation.current>savedGeneration.current,generation:generation.current});
     setStatus(generation.current>savedGeneration.current?'추가 변경사항을 저장해 주세요.':'저장했습니다.');break;
    case 'load':{
     const loaded=decode(message.snapshot);
     if(loaded.table)tables.current[loaded.table.kind]=loaded.table;
     replace({nodes:loaded.nodes,edges:loaded.edges,...(loaded.table?{table:loaded.table}:{})},message.name,loaded.converted);
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
     const image=svg(snapshot()),url=URL.createObjectURL(new Blob([image.source],{type:'image/svg+xml'}));
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
 useEffect(()=>{
  const keys=e=>{
   if(['INPUT','TEXTAREA','SELECT'].includes(e.target.tagName)||e.target.isContentEditable)return;
   if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==='s'){e.preventDefault();send({type:'request_save'});}
   if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==='z'){e.preventDefault();undo(e.shiftKey);}
   if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==='y'){e.preventDefault();undo(true);}
  };window.addEventListener('keydown',keys);return()=>window.removeEventListener('keydown',keys);
 });
 const selected=graph.nodes.find(n=>n.selected),selectedEdge=graph.edges.find(e=>e.selected);
 const edit=(data)=>{
  commit({...graph,nodes:graph.nodes.map(n=>n.id===selected.id?{...n,data:{...n.data,...data}}:n)});
 };
 const add=shape=>{
  const position=flow.current?.screenToFlowPosition({x:window.innerWidth/2,y:window.innerHeight/2})??{x:100,y:100};
  commit({...graph,nodes:[...graph.nodes.map(n=>({...n,selected:false})),{...node(shape==='diamond'?'조건 판단':'내용 입력',position.x,position.y,shape),selected:true}]});
 };
 const exportHwpx=()=>{
  try{send({type:'export_hwpx',name:nameRef.current,spec:exportSpec(table)});}
  catch(error){setStatus(error.message);}
 };
 const tabs=[['diagram','다이어그램'],['flow','흐름표'],['grid','기본 표']];
 return <HistoryContext.Provider value={checkpoint}><div className="editor-shell">
  <header><strong>{TITLE}</strong><span className="document-name">{name}</span>
   <div className="mode-tabs" role="tablist" aria-label="만들 것">{tabs.map(([key,label])=><button key={key} role="tab" aria-selected={mode===key} className={mode===key?'active':''} onClick={()=>switchMode(key)}>{label}</button>)}</div>
   <nav>
   <button onClick={()=>send({type:'request_new'})}>새 문서</button>
   <button onClick={()=>send({type:'request_list'})}>열기·삭제</button>
   <button onClick={()=>send({type:'request_save'})}>저장</button>
   {mode==='diagram'?<>
    <button disabled={busy} onClick={()=>send({type:'request_png'})}>{busy?'PNG 변환 중…':'PNG 내보내기'}</button>
    <select aria-label="예시 서식" value="" onChange={e=>send({type:'request_template',template:e.target.value})}><option value="">예시 서식 10종</option>{Object.entries(templates).map(([key,t])=><option key={key} value={key}>{t.name}</option>)}</select>
   </>:<button className="primary" onClick={exportHwpx}>한/글 문서로 저장</button>}
  </nav></header>
  <div className="workspace">
   {mode==='diagram'&&<aside><h2>도형</h2>{[['rectangle','처리'],['diamond','판단'],['ellipse','시작·종료'],['text','텍스트']].map(([shape,label])=><button key={shape} onClick={()=>add(shape)}>{label} 추가</button>)}
    <button onClick={()=>undo()}>실행 취소 (Ctrl+Z)</button><button onClick={()=>undo(true)}>다시 실행 (Ctrl+Y)</button>
    <button onClick={()=>{
     const items=graph.nodes.filter(n=>n.selected);if(items.length<2)return;const x=Math.min(...items.map(n=>n.position.x));commit({...graph,nodes:graph.nodes.map(n=>n.selected?{...n,position:{...n.position,x}}:n)});
    }}>선택 도형 왼쪽 정렬</button>
    {selected&&<><h2>선택 도형</h2><label>내용<textarea aria-label="도형 내용" maxLength={2000} value={selected.data.label} onChange={e=>edit({label:e.target.value})}/></label><label>배경<select aria-label="도형 배경" value={selected.data.color} onChange={e=>edit({color:e.target.value})}>{Object.keys(COLORS).map(c=><option key={c} value={c}>{{blue:'파랑',green:'초록',orange:'주황',yellow:'노랑',white:'흰색'}[c]}</option>)}</select></label>
     <TextStyleControls label="도형 글자" value={{font:selected.data.font,size:selected.data.size,bold:selected.data.bold,textColor:selected.data.textColor}} onChange={edit}/></>}
    {selectedEdge&&<label>연결선 설명<input aria-label="연결선 설명" maxLength={300} value={selectedEdge.label??''} onChange={e=>commit({...graph,edges:graph.edges.map(v=>v.id===selectedEdge.id?{...v,label:e.target.value}:v)})}/></label>}
    <p>연결점을 끌어 도형 연결<br/>Shift+선택: 여러 도형<br/>Delete: 선택 삭제<br/>Ctrl+휠: 확대·축소</p>
   </aside>}
   {mode==='flow'&&table&&<aside><h2>칸 수(가로)</h2>
    <div className="presets">{FLOW_PRESETS.map(n=><button key={n} className={table.steps.length===n?'active':''} aria-pressed={table.steps.length===n} onClick={()=>changeTable(resizeFlow(table,n))}>{n}칸</button>)}</div>
    <Stepper label="단계" value={table.steps.length} min={2} max={MAX_FLOW_STEPS} onChange={n=>changeTable(resizeFlow(table,n))}/>
    <label>화살표<select aria-label="화살표 모양" value={table.arrow} onChange={e=>changeTable({...table,arrow:e.target.value})}>{ARROWS.map(a=><option key={a} value={a}>{a}</option>)}</select></label>
    <h2>글자 서식</h2>
    <div className="role-tabs">{['step','date','arrow'].map(role=><button key={role} className={flowRole===role?'active':''} onClick={()=>setFlowRole(role)}>{ROLE_NAMES[role]}</button>)}</div>
    <TextStyleControls fill label={ROLE_NAMES[flowRole]} value={table.styles[flowRole]} onChange={patch=>changeTable(setStyle(table,flowRole,patch))}/>
    <button onClick={()=>undo()}>실행 취소 (Ctrl+Z)</button>
   </aside>}
   {mode==='grid'&&table&&<aside><h2>표 크기</h2>
    <Stepper label="행(가로줄)" value={table.rows.length} min={1} max={MAX_ROWS} onChange={n=>changeTable(resizeGrid(table,n,table.rows[0].length))}/>
    <Stepper label="열(세로줄)" value={table.rows[0].length} min={1} max={MAX_COLS} onChange={n=>changeTable(resizeGrid(table,table.rows.length,n))}/>
    <Stepper label="머리글 행" value={table.header_rows} min={0} max={Math.min(2,table.rows.length)} onChange={n=>changeTable({...table,header_rows:n})}/>
    <label className="check"><input type="checkbox" checked={table.use_basic_style} onChange={e=>changeTable({...table,use_basic_style:e.target.checked})}/>기본 표 서식 입히기</label>
    <h2>글자 서식</h2>
    <div className="role-tabs">{['head','body'].map(role=><button key={role} className={gridRole===role?'active':''} onClick={()=>setGridRole(role)}>{ROLE_NAMES[role]}</button>)}</div>
    <TextStyleControls fill label={ROLE_NAMES[gridRole]} value={table.styles[gridRole]} onChange={patch=>changeTable(setStyle(table,gridRole,patch))}/>
    {table.custom[gridRole]&&<button onClick={()=>changeTable({...table,custom:{...table.custom,[gridRole]:false},styles:{...table.styles,[gridRole]:gridTable().styles[gridRole]}})}>{ROLE_NAMES[gridRole]} 기본 서식으로</button>}
    <button onClick={()=>undo()}>실행 취소 (Ctrl+Z)</button>
   </aside>}
   <main><div className="flow-layer" style={{display:mode==='diagram'?'block':'none'}}><ReactFlow nodes={graph.nodes} edges={graph.edges} nodeTypes={nodeTypes} edgeTypes={edgeTypes} connectionMode={ConnectionMode.Loose} snapToGrid snapGrid={[10,10]}
    onInit={instance=>{flow.current=instance;send({type:'ready',protocol_version:1,editor:FORMAT});}}
    onNodesChange={changes=>{
     const edits=changes.filter(c=>c.type!=='select'&&!(c.type==='dimensions'&&!c.resizing));
     let next={...current.current,nodes:applyNodeChanges(changes,current.current.nodes)};
     if(changes.some(c=>c.type==='dimensions'&&(c.resizing!==undefined||c.setAttributes)))next=layoutGraph(next);
     current.current=next;setGraph(next);if(edits.length)mark();
    }}
    onEdgesChange={changes=>{const next={...current.current,edges:applyEdgeChanges(changes,current.current.edges)};current.current=next;setGraph(next);if(changes.some(c=>c.type!=='select'))mark();}}
    onNodeDragStart={()=>checkpoint()} onBeforeDelete={async()=>{checkpoint();return true;}}
    onConnect={connection=>commit({...current.current,edges:[...current.current.edges,edge(connection.source,connection.target,'',id(),connection.sourceHandle,connection.targetHandle)]})}
    onSelectionDragStart={()=>checkpoint()} onNodeDoubleClick={(_,n)=>{setStatus('왼쪽 내용 입력에서 수정하세요.');}}
    fitView deleteKeyCode={mode==='diagram'?['Backspace','Delete']:null}><Background gap={20}/><Controls/><MiniMap/></ReactFlow></div>
    {mode==='flow'&&table&&<FlowTableView table={table} onChange={changeTable}/>}
    {mode==='grid'&&table&&<GridTableView table={table} onChange={changeTable}/>}</main>
  </div><footer role="status">{status} · 로컬 저장</footer>
 </div></HistoryContext.Provider>;
}
createRoot(document.getElementById('root')).render(<ReactFlowProvider><App/></ReactFlowProvider>);
