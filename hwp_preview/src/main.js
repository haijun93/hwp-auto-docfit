// 한/글 조판 미리보기: rhwp(@rhwp/core 0.8.7, MIT, Edward Kim)의 Rust→WASM 조판 엔진으로 서식 명세를 실제 HWP
// 문서로 만들고(글자 모양·문단 모양·용지 여백·표), 한/글처럼 줄을 나누고 양쪽 정렬한 첫 쪽을 SVG로 보인다.
// Flutter 설정·서식 요소 화면이 같은 출처 iframe으로 띄우고 postMessage로 명세를 보낸다. 외부 접속 없음.
import init,{HwpDocument} from '@rhwp/core';
import wasmUrl from '@rhwp/core/rhwp_bg.wasm?url';
import {plan,cssFont,normalizeChar} from './spec.js';
import './style.css';

let ctx=null,lastFont='';
const measure=(font,text)=>{
 if(!ctx)ctx=document.createElement('canvas').getContext('2d');
 if(font!==lastFont){ctx.font=font;lastFont=font;}
 return ctx.measureText(text).width;
};
// rhwp는 줄 나눔·정렬 계산에 브라우저 글자 폭을 쓴다(설치된 한/글 글꼴이 있으면 그 폭).
globalThis.measureTextWidth=measure;

const view=document.getElementById('view'),note=document.getElementById('note');
let ready=null;
function post(message){if(window.parent!==window)window.parent.postMessage(message,location.origin);}

function apply(doc,ops){
 const fontIds=new Map();
 const fontId=name=>{if(!fontIds.has(name))fontIds.set(name,doc.findOrCreateFontId(name));return fontIds.get(name);};
 const props=p=>{const {fontName,...rest}=p;const id=fontId(fontName);return JSON.stringify(id>=0?{...rest,fontId:id}:rest);};
 const paras=ops.filter(o=>o.op==='para');
 for(const op of ops){
  if(op.op==='page'){
   const current=JSON.parse(doc.getPageDef(0));
   doc.setPageDef(0,JSON.stringify({...current,...op.def}));
  }
 }
 paras.forEach((op,i)=>{
  if(i>0){const prev=paras[i-1];doc.splitParagraph(0,i-1,prev.text.length);}
  doc.insertText(0,i,0,op.text);
 });
 paras.forEach((op,i)=>{
  for(const run of op.runs)if(run.end>run.start)doc.applyCharFormat(0,i,run.start,run.end,props(run.props));
  doc.applyParaFormat(0,i,JSON.stringify(op.props));
 });
 const table=ops.find(o=>o.op==='table');
 let tablePara=null;
 if(table){
  tablePara=paras.length;
  if(paras.length){doc.splitParagraph(0,paras.length-1,paras[paras.length-1].text.length);}
  const made=JSON.parse(doc.createTable(0,tablePara,0,table.rows.length,table.rows[0].length));
  const pi=made.paraIdx??tablePara,ci=made.controlIdx??0;
  tablePara=pi;
  const cols=table.rows[0].length;
  table.rows.forEach((row,r)=>row.forEach((value,c)=>{
   const cell=r*cols+c;
   if(value)doc.insertTextInCell(0,pi,ci,cell,0,0,value);
   doc.applyCharFormatInCell(0,pi,ci,cell,0,0,Math.max(1,value.length),props(r===0?table.header:table.body));
   doc.applyParaFormatInCell(0,pi,ci,cell,0,JSON.stringify({alignment:'center',koreanBreakUnit:0}));
   if(r===0&&table.fill)doc.setCellProperties(0,pi,ci,cell,JSON.stringify({fillType:'solid',fillColor:table.fill}));
  }));
 }
 return {paras,tablePara,table};
}

/** 그린 쪽에서 글이 있는 부분만 잘라 보인다(용지 전체는 작아서 읽기 어렵다). */
function crop(svg,pad=14){
 const page=svg.viewBox.baseVal;
 let box=null;
 for(const el of svg.querySelectorAll('text,line,path,polyline,polygon,rect,image')){
  let b;try{b=el.getBBox();}catch{continue;}
  if(!b.width&&!b.height)continue;
  // 용지 바탕·본문 영역 틀처럼 쪽 높이 대부분을 덮는 요소는 글이 아니다.
  if(b.height>=page.height*0.5||(el.tagName==='rect'&&b.width>=page.width*0.95))continue;
  box=box?{x:Math.min(box.x,b.x),y:Math.min(box.y,b.y),r:Math.max(box.r,b.x+b.width),b:Math.max(box.b,b.y+b.height)}:{x:b.x,y:b.y,r:b.x+b.width,b:b.y+b.height};
 }
 if(!box)return;
 const x=Math.max(page.x,box.x-pad),y=Math.max(page.y,box.y-pad);
 const w=Math.min(page.width,box.r+pad)-x,h=Math.min(page.height,box.b+pad)-y;
 svg.setAttribute('viewBox',`${x} ${y} ${w} ${h}`);
 svg.removeAttribute('width');svg.removeAttribute('height');
 svg.style.width='100%';svg.style.height='auto';
 return {x,y,w,h};
}

/** 바뀐 설정이 닿는 문단 뒤에 연한 표시를 깐다. */
function highlight(svg,doc,result,box){
 const ns='http://www.w3.org/2000/svg';
 const marks=[];
 result.paras.forEach((op,i)=>{
  if(!op.focus)return;
  try{
   const a=JSON.parse(doc.getCursorRect(0,i,0)),b=JSON.parse(doc.getCursorRect(0,i,op.text.length));
   if(a.pageIndex!==0)return;
   marks.push({y:a.y,h:b.y+b.height-a.y});
  }catch{/* 위치를 못 구하면 표시하지 않는다 */}
 });
 for(const m of marks){
  const r=document.createElementNS(ns,'rect');
  r.setAttribute('x',box?box.x+4:0);r.setAttribute('y',m.y-2);r.setAttribute('width',box?box.w-8:'100%');r.setAttribute('height',m.h+4);
  r.setAttribute('rx',4);r.setAttribute('class','focus-mark');
  // 용지 바탕 사각형 바로 뒤(글 아래)에 깐다.
  const paper=[...svg.children].find(c=>c.tagName==='rect'&&!c.classList.contains('focus-mark'));
  svg.insertBefore(r,paper?paper.nextSibling:svg.firstChild);
 }
}

function lineCounts(doc,result){
 return result.paras.map((op,i)=>{try{return JSON.parse(doc.getLineInfo(0,i,op.text.length)).lineCount;}catch{return null;}});
}

async function render(spec,requestId){
 await ready;
 const started=performance.now();
 const doc=HwpDocument.createEmpty();
 try{
  doc.createBlankDocument();
  const ops=plan(spec,measure);
  const result=apply(doc,ops);
  view.innerHTML=doc.renderPageSvg(0);
  const svg=view.querySelector('svg');
  const box=svg?crop(svg):null;
  if(svg)highlight(svg,doc,result,box);
  const lines=lineCounts(doc,result);
  const pages=doc.pageCount();
  note.textContent=spec.caption??'';
  post({type:'rendered',requestId,height:Math.ceil(document.body.scrollHeight),lines,pages,ms:Math.round(performance.now()-started)});
 }catch(error){
  view.textContent='';note.textContent='미리보기를 그리지 못했어요: '+(error?.message??error);
  post({type:'preview_error',requestId,message:String(error?.message??error)});
 }finally{doc.free?.();}
}

let pending=null,busy=false;
async function pump(){
 if(busy||!pending)return;
 busy=true;const job=pending;pending=null;
 try{await render(job.spec,job.requestId);}finally{busy=false;pump();}
}
window.addEventListener('message',event=>{
 if(event.source!==window.parent||event.origin!==location.origin)return;
 const data=event.data;
 if(data?.type==='render'&&data.spec){pending={spec:data.spec,requestId:data.requestId??0};pump();}
});
ready=init({module_or_path:wasmUrl}).then(()=>post({type:'ready',engine:'rhwp 0.8.7'})).catch(error=>{
 note.textContent='조판 엔진을 불러오지 못했어요: '+(error?.message??error);
 post({type:'preview_error',message:String(error?.message??error)});
});
// 시험·단독 실행용: 주소 해시에 명세가 있으면 바로 그린다.
if(location.hash.length>1){try{render(JSON.parse(decodeURIComponent(location.hash.slice(1))),0);}catch{/* 무시 */}}
export {render,normalizeChar,cssFont};
