// 표/다이어그램 편집기의 표 모델: 흐름표·기본 표·조직표·장식표. Python docfit_core.table_builder와 같은 규칙.
// 모양은 '표 다이어그램 연습' 폴더를 학습했다(2026-10-15):
//  흐름표(추진일정 흐름표) 위 행 단계 이름(굵게·#DFE6F7)·아래 행 일정, 단계 사이 ➜, 두 행 사이 이중선
//  조직표(조직표) 위 상자에서 세로선 → 가로 버스 → 아래 부서 상자(칸 테두리로 그린 선)
//  장식표(장식표) '2026 추진실적 ……(8. 31. 현재)': 왼쪽 글 상자, 가운데 점선, 오른쪽 날짜
export const FONTS=['한컴돋움','휴먼명조','HY견고딕','HY헤드라인M','함초롬돋움','함초롬바탕','돋움','맑은 고딕','나눔고딕','굴림'];
// 흐름표 화살표: 가로 방향과 세로 방향.
export const ARROWS=['➜','⇨','▶','▷','→','⇒','➡','➤','►','≫'];
export const DOWN_ARROWS=['▼','⇩','↓','▽','⬇','⇓'];
export const MAX_FLOW_STEPS=12,MAX_FLOW_ROWS=5,MAX_ROWS=40,MAX_COLS=12,MAX_TEXT=200,MAX_ORG=8;
export const FLOW_PRESETS=[2,3,4,5,6];
// 한/글 테두리 종류(HWPX 이름)와 화면 미리보기(CSS) 대응. NONE은 투명선(한/글 화면에서는 빨간 점선 안내선).
export const BORDER_TYPES=[
 ['SOLID','실선','solid'],['DASH','파선','dashed'],['LONG_DASH','긴 파선','dashed'],['DOT','점선','dotted'],['CIRCLE','원형 점선','dotted'],
 ['DASH_DOT','일점쇄선','dashed'],['DASH_DOT_DOT','이점쇄선','dashed'],['DOUBLE_SLIM','이중 실선','double'],['SLIM_THICK','얇고 굵은 이중선','double'],
 ['THICK_SLIM','굵고 얇은 이중선','double'],['SLIM_THICK_SLIM','삼중선','double'],['NONE','투명선(선 없음)','none'],
];
export const BORDER_WIDTHS=['0.1 mm','0.12 mm','0.15 mm','0.2 mm','0.25 mm','0.3 mm','0.4 mm','0.5 mm','0.6 mm','0.7 mm','1.0 mm','1.5 mm','2.0 mm','3.0 mm'];
const BORDER_KEYS=new Set(BORDER_TYPES.map(([k])=>k));
export const FLOW_STYLES={
 step:{font:'한컴돋움',size:12,bold:true,color:'#000000',fill:'#DFE6F7'},
 date:{font:'한컴돋움',size:12,bold:false,color:'#000000',fill:'#FFFFFF'},
 arrow:{font:'한컴돋움',size:12,bold:true,color:'#000000',fill:''},
};
export const GRID_STYLES={
 head:{font:'한컴돋움',size:13,bold:true,color:'#000000',fill:'#E7EEF8'},
 body:{font:'휴먼명조',size:12,bold:false,color:'#000000',fill:''},
};
export const ORG_STYLES={
 root:{font:'한컴돋움',size:15,bold:true,color:'#000000',fill:'#DFE6F7'},
 unit:{font:'한컴돋움',size:13,bold:true,color:'#000000',fill:'#FFFFFF'},
 detail:{font:'한컴돋움',size:11,bold:false,color:'#000000',fill:''},
};
export const BAR_STYLES={
 title:{font:'한컴돋움',size:15,bold:true,color:'#000000',fill:''},
 note:{font:'한컴돋움',size:13,bold:true,color:'#000000',fill:''},
};
export const ROLE_NAMES={step:'단계 칸',date:'세부 칸',arrow:'화살표',head:'머리글 칸',body:'본문 칸',root:'윗 상자',unit:'부서 상자',detail:'아래 설명',title:'왼쪽 글',note:'오른쪽 글'};
export const DEFAULT_BORDERS={
 flow:{line:{type:'SOLID',width:'0.4 mm',color:'#4C4C4C'},split:{type:'DOUBLE_SLIM',width:'0.5 mm',color:'#4C4C4C'}},
 grid:{outer:{type:'SOLID',width:'0.4 mm',color:'#000000'},inner:{type:'SOLID',width:'0.12 mm',color:'#000000'}},
 org:{box:{type:'SOLID',width:'0.4 mm',color:'#000000'},link:{type:'SOLID',width:'0.4 mm',color:'#000000'}},
 bar:{box:{type:'SOLID',width:'0.4 mm',color:'#000000'},line:{type:'DASH',width:'0.4 mm',color:'#000000'}},
};
export const BORDER_NAMES={line:'상자 선',split:'단계·세부 사이',outer:'바깥 선',inner:'안쪽 선',box:'상자 선',link:'잇는 선'};
// 학습한 예시의 단계·일정(칸을 늘리면 앞에서부터 쓰고, 모자라면 '단계 N').
const SAMPLE=[['공고 및 접수','9. 14.(월)~10. 6.(화)'],['1차 서류평가','10. 7.(수)~10. 8.(목)'],['서류평가 결과 발표','10. 12.(월)'],['2차 발표평가','10. 28.(수)'],['시상','11월 중'],['결과 보고','12월 중']];

const copy=value=>structuredClone(value);
export function flowTable(count=5){
 const n=Math.max(2,Math.min(MAX_FLOW_STEPS,count));
 return {kind:'flow',direction:'horizontal',arrow:ARROWS[0],rows:1,steps:Array.from({length:n},(_,i)=>({title:SAMPLE[i]?.[0]??'단계 '+(i+1),details:[SAMPLE[i]?.[1]??'']})),
  styles:copy(FLOW_STYLES),borders:copy(DEFAULT_BORDERS.flow)};
}
/** 예전 흐름표(date 하나)도 details로 읽는다. */
export function flowDetails(step,rows){
 const list=Array.isArray(step.details)?step.details:[step.date??''];
 return Array.from({length:rows},(_,i)=>list[i]??'');
}
/** 단계 수를 바꾼다. 있던 단계 글은 그대로 두고, 늘린 칸은 '단계 N'으로 채운다. */
export function resizeFlow(table,count){
 const n=Math.max(2,Math.min(MAX_FLOW_STEPS,count));
 const rows=table.rows??1;
 const steps=table.steps.slice(0,n).map(s=>({title:s.title,details:flowDetails(s,rows)}));
 while(steps.length<n)steps.push({title:'단계 '+(steps.length+1),details:Array(rows).fill('')});
 return {...table,steps};
}
/** 세로(행) 방향 칸 수: 단계 이름 아래 세부 칸(일정·담당·내용…)을 1~5줄로. */
export function resizeFlowRows(table,rows){
 const r=Math.max(1,Math.min(MAX_FLOW_ROWS,rows));
 return {...table,rows:r,steps:table.steps.map(s=>({title:s.title,details:flowDetails(s,r)}))};
}
export function insertStep(table,index){
 if(table.steps.length>=MAX_FLOW_STEPS)return table;
 const steps=[...table.steps];steps.splice(index,0,{title:'새 단계',details:Array(table.rows??1).fill('')});return {...table,steps};
}
export function removeStep(table,index){
 if(table.steps.length<=2)return table;
 return {...table,steps:table.steps.filter((_,i)=>i!==index)};
}
export function gridTable(rows=4,cols=4){
 const r=Math.max(1,Math.min(MAX_ROWS,rows)),c=Math.max(1,Math.min(MAX_COLS,cols));
 const head=['구 분','항목 1','항목 2','항목 3','항목 4','항목 5','항목 6','항목 7','항목 8','항목 9','항목 10','항목 11'];
 return {kind:'grid',header_rows:1,use_basic_style:true,
  rows:Array.from({length:r},(_,i)=>Array.from({length:c},(_,j)=>i===0?head[j]:'')),styles:copy(GRID_STYLES),custom:{head:false,body:false},
  borders:copy(DEFAULT_BORDERS.grid),custom_border:false};
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
// 조직표(학습: 조직표.hwpx — 문화경제국 → 관광정책과·지역경제과…).
export function orgTable(count=4){
 const names=['관광정책과','지역경제과','문화예술과','고용협력과','청년정책과','체육진흥과','기획예산과','총무과'];
 const n=Math.max(1,Math.min(MAX_ORG,count));
 return {kind:'org',root:'문화경제국',units:Array.from({length:n},(_,i)=>({title:names[i],detail:''})),styles:copy(ORG_STYLES),borders:copy(DEFAULT_BORDERS.org)};
}
export function resizeOrg(table,count){
 const n=Math.max(1,Math.min(MAX_ORG,count));
 const units=table.units.slice(0,n);
 while(units.length<n)units.push({title:'부서 '+(units.length+1),detail:''});
 return {...table,units};
}
// 장식표(학습: 장식표.hwpx '2026 추진실적 ……(8. 31. 현재)').
export function barTable(){
 return {kind:'bar',title:'2026 추진실적',note:'( 8. 31. 현재 )',styles:copy(BAR_STYLES),borders:copy(DEFAULT_BORDERS.bar)};
}
export function setStyle(table,role,patch){
 const styles={...table.styles,[role]:{...table.styles[role],...patch}};
 return table.kind==='grid'?{...table,styles,custom:{...table.custom,[role]:true}}:{...table,styles};
}
export function setBorder(table,part,patch){
 const borders={...table.borders,[part]:{...table.borders[part],...patch}};
 return table.kind==='grid'?{...table,borders,custom_border:true}:{...table,borders};
}

const text=v=>typeof v==='string'&&v.length<=MAX_TEXT&&!/[\u0000-\u0008\u000b\u000c\u000e-\u001f]/.test(v);
const hex=v=>typeof v==='string'&&/^#[0-9A-Fa-f]{6}$/.test(v);
function style(value,fallback){
 const s={...fallback,...(value??{})};
 if(!FONTS.includes(s.font)||typeof s.size!=='number'||!(s.size>=6&&s.size<=40)||typeof s.bold!=='boolean'||!hex(s.color)||(s.fill&&!hex(s.fill)))
  throw new Error('글자 서식(글꼴·크기·색)을 확인해 주세요.');
 return {font:s.font,size:s.size,bold:s.bold,color:s.color,fill:s.fill||''};
}
function borders(value,kind){
 const base=DEFAULT_BORDERS[kind];
 return Object.fromEntries(Object.entries(base).map(([part,fallback])=>{
  const b={...fallback,...(value?.[part]??{})};
  if(!BORDER_KEYS.has(b.type)||!BORDER_WIDTHS.includes(b.width)||!hex(b.color))throw new Error('테두리(종류·굵기·색)를 확인해 주세요.');
  return [part,{type:b.type,width:b.width,color:b.color}];
 }));
}
const styles=(value,defaults)=>Object.fromEntries(Object.entries(defaults).map(([k,v])=>[k,style(value?.[k],v)]));
/** 저장·내보내기 전에 표 정보를 검증해 정리한다(Python normalize와 같은 한도). */
export function validateTable(table){
 if(table==null)return null;
 if(table.kind==='flow'){
  if(!Array.isArray(table.steps)||table.steps.length<2||table.steps.length>MAX_FLOW_STEPS)throw new Error('흐름표 단계는 2~'+MAX_FLOW_STEPS+'칸입니다.');
  const direction=table.direction==='vertical'?'vertical':'horizontal';
  const arrows=direction==='vertical'?DOWN_ARROWS:ARROWS;
  if(!arrows.includes(table.arrow))throw new Error('화살표 모양을 확인해 주세요.');
  const rows=table.rows??1;
  if(!Number.isInteger(rows)||rows<1||rows>MAX_FLOW_ROWS)throw new Error('세부 칸은 1~'+MAX_FLOW_ROWS+'줄입니다.');
  const steps=table.steps.map(s=>{const details=flowDetails(s??{},rows);if(!text(s?.title??'')||!details.every(text))throw new Error('칸 글을 확인해 주세요.');return {title:s.title??'',details};});
  return {kind:'flow',direction,arrow:table.arrow,rows,steps,styles:styles(table.styles,FLOW_STYLES),borders:borders(table.borders,'flow')};
 }
 if(table.kind==='grid'){
  const rows=table.rows;
  if(!Array.isArray(rows)||rows.length<1||rows.length>MAX_ROWS||!rows.every(Array.isArray))throw new Error('표는 1~'+MAX_ROWS+'행입니다.');
  const cols=rows[0].length;
  if(cols<1||cols>MAX_COLS||rows.some(r=>r.length!==cols||!r.every(text)))throw new Error('표는 1~'+MAX_COLS+'열이고 칸 글은 '+MAX_TEXT+'자까지입니다.');
  if(!Number.isInteger(table.header_rows)||table.header_rows<0||table.header_rows>Math.min(2,rows.length))throw new Error('머리글 행 수를 확인해 주세요.');
  return {kind:'grid',header_rows:table.header_rows,use_basic_style:table.use_basic_style!==false,rows:rows.map(r=>[...r]),
   styles:styles(table.styles,GRID_STYLES),custom:{head:!!table.custom?.head,body:!!table.custom?.body},
   borders:borders(table.borders,'grid'),custom_border:!!table.custom_border};
 }
 if(table.kind==='org'){
  if(!text(table.root??'')||!Array.isArray(table.units)||table.units.length<1||table.units.length>MAX_ORG)throw new Error('조직표 부서는 1~'+MAX_ORG+'개입니다.');
  const units=table.units.map(u=>{if(!text(u?.title??'')||!text(u?.detail??''))throw new Error('칸 글을 확인해 주세요.');return {title:u.title??'',detail:u.detail??''};});
  return {kind:'org',root:table.root,units,styles:styles(table.styles,ORG_STYLES),borders:borders(table.borders,'org')};
 }
 if(table.kind==='bar'){
  if(!text(table.title??'')||!text(table.note??''))throw new Error('칸 글을 확인해 주세요.');
  return {kind:'bar',title:table.title,note:table.note,styles:styles(table.styles,BAR_STYLES),borders:borders(table.borders,'bar')};
 }
 throw new Error('표 종류를 확인해 주세요.');
}
/** Python으로 보낼 내보내기 정보: 기본 표에서 사용자가 고르지 않은 서식·테두리는 빼서 기본 표 서식을 따르게 한다. */
export function exportSpec(table){
 const t=validateTable(table);
 if(t.kind!=='grid')return t;
 const picked=Object.fromEntries(Object.entries(t.styles).filter(([role])=>t.custom[role]));
 return {kind:'grid',header_rows:t.header_rows,use_basic_style:t.use_basic_style,rows:t.rows,styles:picked,...(t.custom_border?{borders:t.borders}:{})};
}
/** 화면 미리보기용 CSS 글자 서식(pt를 화면 px로 1.33배). */
export function cssOf(s){
 return {fontFamily:'"'+s.font+'","Malgun Gothic","Noto Sans KR",sans-serif',fontSize:Math.round(s.size*1.33)+'px',fontWeight:s.bold?700:400,color:s.color,background:s.fill||'transparent'};
}
/** 화면 미리보기용 CSS 테두리(투명선은 한/글처럼 연한 안내선으로). */
export function cssBorder(b){
 if(!b||b.type==='NONE')return '1px dotted #f87171';
 const css=(BORDER_TYPES.find(([k])=>k===b.type)??BORDER_TYPES[0])[2];
 const px=Math.max(1,Math.round(parseFloat(b.width)*3.78*(css==='double'?2.2:1)));
 return `${Math.max(css==='double'?3:1,px)}px ${css} ${b.color}`;
}
