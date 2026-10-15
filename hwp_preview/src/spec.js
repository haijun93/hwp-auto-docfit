// 서식 미리보기 명세 → rhwp(@rhwp/core, MIT) 편집 명령 계획. 순수 함수라 node 시험이 가능하다.
//
// 명세(Flutter가 보냄):
// { page:{left,right,top,bottom}(mm),
//   paragraphs:[{ text, marker, indent(앞 칸 수), hanging(bool), label(굵게 할 앞부분 글),
//                 char:{font,size(pt),bold,spacing(%),ratio(%),color}, markerChar:{font,size,bold},
//                 para:{line(%),before(pt),align}, focus(bool) }],
//   table:{ rows:[[글]], header:{font,size,bold,fill}, body:{font,size,bold}, focus } }
// 단위(rhwp 실측, 한/글 HWP5와 같음): 글자 크기·문단 위 간격 = pt×100, 내어쓰기 = pt×200, 여백 = HWPUNIT(1mm≈283.46).
export const FONTS=['한컴돋움','휴먼명조','HY견고딕','HY헤드라인M','함초롬돋움','함초롬바탕','돋움','바탕','굴림','맑은 고딕','나눔고딕'];
export const LIMITS={paragraphs:30,text:400,rows:8,cols:6};
const ALIGN={left:'left',center:'center',right:'right',justify:'justify','왼쪽':'left','가운데':'center','오른쪽':'right','양쪽':'justify','배분':'distribute'};
const mm=v=>Math.round(v*7200/25.4);
const clamp=(v,lo,hi,fallback)=>Number.isFinite(v)?Math.min(hi,Math.max(lo,v)):fallback;
const str=(v,max)=>typeof v==='string'?v.slice(0,max).replace(/[\u0000-\u0008\u000b-\u001f]/g,''):'';
const font=v=>FONTS.includes(v)?v:null;

export function normalizeChar(c={},base={}){
 return {font:font(c.font)??base.font??'한컴돋움',size:clamp(+c.size,6,40,base.size??13),bold:typeof c.bold==='boolean'?c.bold:(base.bold??false),
  spacing:clamp(+c.spacing,-50,50,base.spacing??0),ratio:clamp(+c.ratio,50,200,base.ratio??100),
  color:/^#[0-9a-fA-F]{6}$/.test(c.color??'')?c.color:(base.color??'#000000')};
}

/** 명세를 검증해 rhwp 명령 목록으로 바꾼다. measure(fontCss, text) → px는 내어쓰기 폭 계산에 쓴다. */
export function plan(spec,measure){
 if(!spec||typeof spec!=='object')throw new Error('미리보기 명세가 없습니다.');
 const ops=[];
 const page=spec.page??{};
 ops.push({op:'page',def:{marginLeft:mm(clamp(+page.left,0,60,20)),marginRight:mm(clamp(+page.right,0,60,20)),
  marginTop:mm(clamp(+page.top,0,60,12.7)),marginBottom:mm(clamp(+page.bottom,0,60,12.7))}});
 const paragraphs=(Array.isArray(spec.paragraphs)?spec.paragraphs:[]).slice(0,LIMITS.paragraphs);
 paragraphs.forEach((p,index)=>{
  const ch=normalizeChar(p.char);
  const mk=normalizeChar(p.markerChar,ch);
  const marker=str(p.marker,4);
  const lead=' '.repeat(clamp(+p.indent,0,8,0));
  const prefix=marker?lead+marker+' ':lead;
  const body=str(p.text,LIMITS.text);
  const label=str(p.label,60);
  const text=prefix+body;
  const runs=[];
  if(prefix)runs.push({start:0,end:prefix.length,props:charProps(mk)});
  if(label&&body.startsWith(label)){
   runs.push({start:prefix.length,end:prefix.length+label.length,props:charProps({...ch,bold:true})});
   runs.push({start:prefix.length+label.length,end:text.length,props:charProps(ch)});
  }else runs.push({start:prefix.length,end:text.length,props:charProps(ch)});
  const para=p.para??{};
  const props={alignment:ALIGN[para.align]??'justify',lineSpacing:clamp(+para.line,50,500,160),lineSpacingType:'Percent',
   spacingBefore:Math.round(clamp(+para.before,0,100,0)*100),spacingAfter:0,koreanBreakUnit:0,marginLeft:0,indent:0};
  // 한/글 내어쓰기: 둘째 줄부터 항목기호 뒤 첫 글자 자리에서 시작(앞 칸 + 기호 + 빈칸 폭).
  if(p.hanging!==false&&prefix&&measure){
   const px=measure(cssFont(mk),prefix);
   props.indent=-Math.round(px*0.75*200);
  }
  ops.push({op:'para',index,text,runs,props,focus:!!p.focus});
 });
 const t=spec.table;
 if(t&&Array.isArray(t.rows)&&t.rows.length){
  const rows=t.rows.slice(0,LIMITS.rows).map(r=>(Array.isArray(r)?r:[]).slice(0,LIMITS.cols).map(v=>str(v,40)));
  const cols=Math.max(1,...rows.map(r=>r.length));
  ops.push({op:'table',rows:rows.map(r=>Array.from({length:cols},(_,i)=>r[i]??'')),
   header:charProps(normalizeChar(t.header,{font:'한컴돋움',size:13,bold:true})),
   body:charProps(normalizeChar(t.body,{font:'휴먼명조',size:12})),
   fill:/^#[0-9a-fA-F]{6}$/.test(t.header?.fill??'')?t.header.fill:null,focus:!!t.focus});
 }
 return ops;
}

/** rhwp applyCharFormat 속성(fontId는 실행할 때 글꼴 이름으로 찾는다). */
export function charProps(c){
 const seven=v=>Array(7).fill(Math.round(v));
 return {fontName:c.font,fontSize:Math.round(c.size*100),bold:!!c.bold,textColor:c.color,spacings:seven(c.spacing),ratios:seven(c.ratio)};
}
export function cssFont(c){return (c.bold?'bold ':'')+Math.round(c.size*4/3)+'px "'+c.font+'"';}
