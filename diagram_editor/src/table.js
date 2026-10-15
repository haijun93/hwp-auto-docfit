// 표/다이어그램 편집기의 표 모델: 흐름표(가로 단계)와 기본 표(행·열). Python docfit_core.table_builder와 같은 규칙.
// 흐름표 모양은 '추진일정 흐름표.hwpx'를 학습했다(2026-10-15): 위 행 단계 이름(굵게·#DFE6F7), 아래 행 일정, 단계 사이 ➜.
export const FONTS=['한컴돋움','휴먼명조','HY견고딕','HY헤드라인M','함초롬돋움','함초롬바탕','돋움','맑은 고딕','나눔고딕','굴림'];
export const ARROWS=['➜','⇨','▶','→','➡'];
export const MAX_FLOW_STEPS=12,MAX_ROWS=40,MAX_COLS=12,MAX_TEXT=200;
export const FLOW_PRESETS=[2,3,4,5,6];
export const FLOW_STYLES={
 step:{font:'한컴돋움',size:12,bold:true,color:'#000000',fill:'#DFE6F7'},
 date:{font:'한컴돋움',size:12,bold:false,color:'#000000',fill:'#FFFFFF'},
 arrow:{font:'한컴돋움',size:12,bold:true,color:'#000000',fill:''},
};
export const GRID_STYLES={
 head:{font:'한컴돋움',size:13,bold:true,color:'#000000',fill:'#E7EEF8'},
 body:{font:'휴먼명조',size:12,bold:false,color:'#000000',fill:''},
};
export const ROLE_NAMES={step:'단계 칸',date:'일정 칸',arrow:'화살표',head:'머리글 칸',body:'본문 칸'};
// 학습한 예시의 단계·일정(칸을 늘리면 앞에서부터 쓰고, 모자라면 '단계 N').
const SAMPLE=[['공고 및 접수','9. 14.(월)~10. 6.(화)'],['1차 서류평가','10. 7.(수)~10. 8.(목)'],['서류평가 결과 발표','10. 12.(월)'],['2차 발표평가','10. 28.(수)'],['시상','11월 중'],['결과 보고','12월 중']];

const copy=value=>structuredClone(value);
export function flowTable(count=5){
 const n=Math.max(2,Math.min(MAX_FLOW_STEPS,count));
 return {kind:'flow',arrow:ARROWS[0],steps:Array.from({length:n},(_,i)=>({title:SAMPLE[i]?.[0]??'단계 '+(i+1),date:SAMPLE[i]?.[1]??''})),styles:copy(FLOW_STYLES)};
}
/** 단계 수를 바꾼다. 있던 단계 글은 그대로 두고, 늘린 칸은 '단계 N'으로 채운다. */
export function resizeFlow(table,count){
 const n=Math.max(2,Math.min(MAX_FLOW_STEPS,count));
 const steps=table.steps.slice(0,n);
 while(steps.length<n)steps.push({title:'단계 '+(steps.length+1),date:''});
 return {...table,steps};
}
export function insertStep(table,index){
 if(table.steps.length>=MAX_FLOW_STEPS)return table;
 const steps=[...table.steps];steps.splice(index,0,{title:'새 단계',date:''});return {...table,steps};
}
export function removeStep(table,index){
 if(table.steps.length<=2)return table;
 return {...table,steps:table.steps.filter((_,i)=>i!==index)};
}
export function gridTable(rows=4,cols=4){
 const r=Math.max(1,Math.min(MAX_ROWS,rows)),c=Math.max(1,Math.min(MAX_COLS,cols));
 const head=['구 분','항목 1','항목 2','항목 3','항목 4','항목 5','항목 6','항목 7','항목 8','항목 9','항목 10','항목 11'];
 return {kind:'grid',header_rows:1,use_basic_style:true,
  rows:Array.from({length:r},(_,i)=>Array.from({length:c},(_,j)=>i===0?head[j]:'')),styles:copy(GRID_STYLES),custom:{head:false,body:false}};
}
/** 행·열 수를 바꾼다. 있던 칸 글은 그대로 두고 늘린 칸은 비운다. */
export function resizeGrid(table,rows,cols){
 const r=Math.max(1,Math.min(MAX_ROWS,rows)),c=Math.max(1,Math.min(MAX_COLS,cols));
 const next=Array.from({length:r},(_,i)=>Array.from({length:c},(_,j)=>table.rows[i]?.[j]??''));
 return {...table,rows:next,header_rows:Math.min(table.header_rows,r)};
}
export function insertRow(table,index){
 if(table.rows.length>=MAX_ROWS)return table;
 const rows=[...table.rows];rows.splice(index,0,Array(rows[0].length).fill(''));return {...table,rows};
}
export function removeRow(table,index){
 if(table.rows.length<=1)return table;
 const rows=table.rows.filter((_,i)=>i!==index);return {...table,rows,header_rows:Math.min(table.header_rows,rows.length)};
}
export function insertCol(table,index){
 if(table.rows[0].length>=MAX_COLS)return table;
 return {...table,rows:table.rows.map(row=>{const next=[...row];next.splice(index,0,'');return next;})};
}
export function removeCol(table,index){
 if(table.rows[0].length<=1)return table;
 return {...table,rows:table.rows.map(row=>row.filter((_,j)=>j!==index))};
}
export function setStyle(table,role,patch){
 const styles={...table.styles,[role]:{...table.styles[role],...patch}};
 return table.kind==='grid'?{...table,styles,custom:{...table.custom,[role]:true}}:{...table,styles};
}

const text=v=>typeof v==='string'&&v.length<=MAX_TEXT&&!/[\u0000-\u0008\u000b\u000c\u000e-\u001f]/.test(v);
const hex=v=>typeof v==='string'&&/^#[0-9A-Fa-f]{6}$/.test(v);
function style(value,fallback){
 const s={...fallback,...(value??{})};
 if(!FONTS.includes(s.font)||typeof s.size!=='number'||!(s.size>=6&&s.size<=40)||typeof s.bold!=='boolean'||!hex(s.color)||(s.fill&&!hex(s.fill)))
  throw new Error('글자 서식(글꼴·크기·색)을 확인해 주세요.');
 return {font:s.font,size:s.size,bold:s.bold,color:s.color,fill:s.fill||''};
}
/** 저장·내보내기 전에 표 정보를 검증해 정리한다(Python normalize와 같은 한도). */
export function validateTable(table){
 if(table==null)return null;
 if(table.kind==='flow'){
  if(!Array.isArray(table.steps)||table.steps.length<2||table.steps.length>MAX_FLOW_STEPS)throw new Error('흐름표 단계는 2~'+MAX_FLOW_STEPS+'칸입니다.');
  if(!ARROWS.includes(table.arrow))throw new Error('화살표 모양을 확인해 주세요.');
  const steps=table.steps.map(s=>{if(!text(s?.title??'')||!text(s?.date??''))throw new Error('칸 글을 확인해 주세요.');return {title:s.title??'',date:s.date??''};});
  return {kind:'flow',arrow:table.arrow,steps,styles:Object.fromEntries(Object.entries(FLOW_STYLES).map(([k,v])=>[k,style(table.styles?.[k],v)]))};
 }
 if(table.kind==='grid'){
  const rows=table.rows;
  if(!Array.isArray(rows)||rows.length<1||rows.length>MAX_ROWS||!rows.every(Array.isArray))throw new Error('표는 1~'+MAX_ROWS+'행입니다.');
  const cols=rows[0].length;
  if(cols<1||cols>MAX_COLS||rows.some(r=>r.length!==cols||!r.every(text)))throw new Error('표는 1~'+MAX_COLS+'열이고 칸 글은 '+MAX_TEXT+'자까지입니다.');
  if(!Number.isInteger(table.header_rows)||table.header_rows<0||table.header_rows>Math.min(2,rows.length))throw new Error('머리글 행 수를 확인해 주세요.');
  return {kind:'grid',header_rows:table.header_rows,use_basic_style:table.use_basic_style!==false,rows:rows.map(r=>[...r]),
   styles:Object.fromEntries(Object.entries(GRID_STYLES).map(([k,v])=>[k,style(table.styles?.[k],v)])),
   custom:{head:!!table.custom?.head,body:!!table.custom?.body}};
 }
 throw new Error('표 종류는 흐름표 또는 기본 표입니다.');
}
/** Python으로 보낼 내보내기 정보: 기본 표에서 사용자가 고르지 않은 역할의 서식은 빼서 기본 표 서식을 따르게 한다. */
export function exportSpec(table){
 const t=validateTable(table);
 if(t.kind==='flow')return t;
 const styles=Object.fromEntries(Object.entries(t.styles).filter(([role])=>t.custom[role]));
 return {kind:'grid',header_rows:t.header_rows,use_basic_style:t.use_basic_style,rows:t.rows,styles};
}
/** 화면 미리보기용 CSS 글자 서식(pt를 화면 px로 1.33배). */
export function cssOf(s){
 return {fontFamily:'"'+s.font+'","Malgun Gothic","Noto Sans KR",sans-serif',fontSize:Math.round(s.size*1.33)+'px',fontWeight:s.bold?700:400,color:s.color,background:s.fill||'transparent'};
}
