import React,{useRef,useState,useEffect,createContext,useContext} from 'react';
import {createRoot} from 'react-dom/client';
import {ReactFlow,ReactFlowProvider,Background,Controls,MiniMap,Handle,Position,ConnectionMode,applyNodeChanges,applyEdgeChanges,NodeResizer,BaseEdge,useReactFlow} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import './style.css';
import {FORMAT,COLORS,templates,template,node,edge,id,decode,validate,svg,layoutGraph,computeNodeAutoFitBox,edgeLabelBox,LINE_HEIGHT} from './model.js';

function send(message){
 const host=window.chrome?.webview;
 if(window.parent!==window)window.parent.postMessage(message,window.location.origin);
 else if(host)host.postMessage(JSON.stringify(message));
}
const HistoryContext=createContext(()=>{});
function FlowNode({data,selected,width,height}){
 const box=computeNodeAutoFitBox({data,width,height});
 const resizeStart=useContext(HistoryContext);
 return <><NodeResizer onResizeStart={resizeStart} isVisible={selected} minWidth={80} minHeight={50}/>
  {Object.entries(Position).map(([key,value])=><Handle key={key} id={value} type="source" position={value}/>)}
  <div className={'node-body '+data.shape} style={{background:COLORS[data.color]}}>{data.shape==='diamond'&&<svg className="diamond-background" viewBox="0 0 220 90" preserveAspectRatio="none"><polygon points="110,2 218,45 110,88 2,45" fill={COLORS[data.color]} stroke="#475569" strokeWidth="2"/></svg>}<span className="node-lines">{box.lines.map((line,i)=><span key={i} style={{display:'block',height:LINE_HEIGHT}}>{line||'\u00a0'}</span>)}</span></div></>;
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
function App(){
 const [graph,setGraph]=useState({nodes:[],edges:[]}),[name,setName]=useState('새 업무 흐름도'),[busy,setBusy]=useState(false),[status,setStatus]=useState('도형을 추가하고 연결점을 끌어 연결하세요.');
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
 };
 const snapshot=()=>validate({format:FORMAT,version:1,...current.current});
 const handle=useRef(null);
 handle.current=async message=>{
  if(!message||typeof message!=='object')return;
  try{
   switch(message.type){
    case 'new':replace({nodes:[],edges:[]},'새 업무 흐름도',false);send({type:'document_new'});break;
    case 'mark_saved':
     if(Number.isInteger(message.generation))savedGeneration.current=Math.max(savedGeneration.current,message.generation);
     send({type:'dirty',value:generation.current>savedGeneration.current,generation:generation.current});
     setStatus(generation.current>savedGeneration.current?'추가 변경사항을 저장해 주세요.':'저장했습니다.');break;
    case 'load':{
     const loaded=decode(message.snapshot);
     replace({nodes:loaded.nodes,edges:loaded.edges},message.name,loaded.converted);
     send({type:'document_loaded',converted:loaded.converted});break;
    }
    case 'apply_template':{
     const value=template(message.template);commit({nodes:value.nodes,edges:value.edges});setName(value.name);fit();
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
 return <HistoryContext.Provider value={checkpoint}><div className="editor-shell">
  <header><strong>업무 흐름도</strong><span className="document-name">{name}</span><nav>
   <button onClick={()=>send({type:'request_new'})}>새 문서</button>
   <button onClick={()=>send({type:'request_list'})}>열기·삭제</button>
   <button onClick={()=>send({type:'request_save'})}>저장</button>
   <button disabled={busy} onClick={()=>send({type:'request_png'})}>{busy?'PNG 변환 중…':'PNG 내보내기'}</button>
   <select aria-label="예시 서식" value="" onChange={e=>send({type:'request_template',template:e.target.value})}><option value="">예시 서식 10종</option>{Object.entries(templates).map(([key,t])=><option key={key} value={key}>{t.name}</option>)}</select>
  </nav></header>
  <div className="workspace">
   <aside><h2>도형</h2>{[['rectangle','처리'],['diamond','판단'],['ellipse','시작·종료'],['text','텍스트']].map(([shape,label])=><button key={shape} onClick={()=>add(shape)}>{label} 추가</button>)}
    <button onClick={()=>undo()}>실행 취소 (Ctrl+Z)</button><button onClick={()=>undo(true)}>다시 실행 (Ctrl+Y)</button>
    <button onClick={()=>{
     const items=graph.nodes.filter(n=>n.selected);if(items.length<2)return;const x=Math.min(...items.map(n=>n.position.x));commit({...graph,nodes:graph.nodes.map(n=>n.selected?{...n,position:{...n.position,x}}:n)});
    }}>선택 도형 왼쪽 정렬</button>
    {selected&&<><h2>선택 도형</h2><label>내용<textarea aria-label="도형 내용" maxLength={2000} value={selected.data.label} onChange={e=>edit({label:e.target.value})}/></label><label>배경<select aria-label="도형 배경" value={selected.data.color} onChange={e=>edit({color:e.target.value})}>{Object.keys(COLORS).map(c=><option key={c} value={c}>{{blue:'파랑',green:'초록',orange:'주황',yellow:'노랑',white:'흰색'}[c]}</option>)}</select></label></>}
    {selectedEdge&&<label>연결선 설명<input aria-label="연결선 설명" maxLength={300} value={selectedEdge.label??''} onChange={e=>commit({...graph,edges:graph.edges.map(v=>v.id===selectedEdge.id?{...v,label:e.target.value}:v)})}/></label>}
    <p>연결점을 끌어 도형 연결<br/>Shift+선택: 여러 도형<br/>Delete: 선택 삭제<br/>Ctrl+휠: 확대·축소</p>
   </aside>
   <main><ReactFlow nodes={graph.nodes} edges={graph.edges} nodeTypes={nodeTypes} edgeTypes={edgeTypes} connectionMode={ConnectionMode.Loose} snapToGrid snapGrid={[10,10]}
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
    fitView deleteKeyCode={['Backspace','Delete']}><Background gap={20}/><Controls/><MiniMap/></ReactFlow></main>
  </div><footer role="status">{status} · 로컬 저장</footer>
 </div></HistoryContext.Provider>;
}
createRoot(document.getElementById('root')).render(<ReactFlowProvider><App/></ReactFlowProvider>);
