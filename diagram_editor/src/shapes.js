// 표/다이어그램 도형 목록과 SVG 경로(PPT 도형처럼 분류). 화면 노드·PNG 내보내기·마인드맵이 같이 쓴다.
// 모든 경로는 (x,y)에서 시작하는 w×h 상자 안에 그린다.

export const SHAPE_GROUPS=[
 ['사각형',[['rectangle','사각형'],['roundRect','둥근 사각형'],['snipRect','모서리 잘린 사각형'],['frame','액자']]],
 ['기본 도형',[['ellipse','타원'],['triangle','삼각형'],['rightTriangle','직각 삼각형'],['parallelogram','평행 사변형'],['trapezoid','사다리꼴'],
  ['diamond','마름모'],['pentagon','오각형'],['hexagon','육각형'],['octagon','팔각형'],['plus','십자형'],['cylinder','원통'],['cloud','구름'],['heart','하트']]],
 ['블록 화살표',[['arrowRight','오른쪽 화살표'],['arrowLeft','왼쪽 화살표'],['arrowUp','위쪽 화살표'],['arrowDown','아래쪽 화살표'],
  ['arrowLeftRight','좌우 화살표'],['chevron','갈매기형'],['homePlate','오각형 화살표']]],
 ['순서도',[['process','처리'],['decision','판단'],['terminator','단말(시작·끝)'],['data','데이터'],['document','문서'],
  ['predefined','미리 정의된 처리'],['manualInput','수동 입력']]],
 ['별·현수막',[['star5','별 5'],['star8','별 8'],['banner','현수막']]],
 ['설명선',[['calloutRect','사각 설명선'],['calloutRound','둥근 설명선']]],
 ['선',[['line','직선'],['arrowLine','화살표 선'],['doubleArrowLine','양쪽 화살표 선'],['vline','세로선'],['diagonal','대각선']]],
 ['글',[['text','텍스트 상자']]],
];
export const SHAPES=new Map(SHAPE_GROUPS.flatMap(([,items])=>items));
export const LINE_SHAPES=new Set(['line','arrowLine','doubleArrowLine','vline','diagonal']);
// 예전 문서의 도형 이름(rectangle·diamond·ellipse·text)은 그대로 쓴다.

const poly=points=>'M '+points.map(([x,y])=>x.toFixed(2)+' '+y.toFixed(2)).join(' L ')+' Z';
function regular(x,y,w,h,n,rotation=-Math.PI/2){
 return poly(Array.from({length:n},(_,i)=>{const a=rotation+i*2*Math.PI/n;return [x+w/2+w/2*Math.cos(a),y+h/2+h/2*Math.sin(a)];}));
}
function star(x,y,w,h,n,inner){
 return poly(Array.from({length:n*2},(_,i)=>{const a=-Math.PI/2+i*Math.PI/n,r=i%2?inner:1;return [x+w/2+w/2*r*Math.cos(a),y+h/2+h/2*r*Math.sin(a)];}));
}

/** 도형의 SVG path d. 선 도형은 열린 경로다. */
export function shapePath(shape,x,y,w,h){
 const r=x+w,b=y+h,cx=x+w/2,cy=y+h/2,m=Math.min(w,h);
 switch(shape){
  case 'roundRect':case 'terminator':{const k=shape==='terminator'?h/2:m*0.18;return `M ${x+k} ${y} H ${r-k} A ${k} ${k} 0 0 1 ${r} ${y+k} V ${b-k} A ${k} ${k} 0 0 1 ${r-k} ${b} H ${x+k} A ${k} ${k} 0 0 1 ${x} ${b-k} V ${y+k} A ${k} ${k} 0 0 1 ${x+k} ${y} Z`;}
  case 'snipRect':{const k=m*0.2;return poly([[x,y],[r-k,y],[r,y+k],[r,b],[x,b]]);}
  case 'frame':{const k=m*0.12;return poly([[x,y],[r,y],[r,b],[x,b]])+' '+poly([[x+k,y+k],[x+k,b-k],[r-k,b-k],[r-k,y+k]]);}
  case 'ellipse':return `M ${x} ${cy} A ${w/2} ${h/2} 0 1 0 ${r} ${cy} A ${w/2} ${h/2} 0 1 0 ${x} ${cy} Z`;
  case 'triangle':return poly([[cx,y],[r,b],[x,b]]);
  case 'rightTriangle':return poly([[x,y],[r,b],[x,b]]);
  case 'parallelogram':case 'data':{const k=w*0.2;return poly([[x+k,y],[r,y],[r-k,b],[x,b]]);}
  case 'trapezoid':case 'manualInputBottom':{const k=w*0.2;return poly([[x+k,y],[r-k,y],[r,b],[x,b]]);}
  case 'diamond':case 'decision':return poly([[cx,y],[r,cy],[cx,b],[x,cy]]);
  case 'pentagon':return regular(x,y,w,h,5);
  case 'hexagon':{const k=w*0.22;return poly([[x+k,y],[r-k,y],[r,cy],[r-k,b],[x+k,b],[x,cy]]);}
  case 'octagon':{const k=m*0.29;return poly([[x+k,y],[r-k,y],[r,y+k],[r,b-k],[r-k,b],[x+k,b],[x,b-k],[x,y+k]]);}
  case 'plus':{const a=w*0.3,c=h*0.3;return poly([[x+a,y],[r-a,y],[r-a,y+c],[r,y+c],[r,b-c],[r-a,b-c],[r-a,b],[x+a,b],[x+a,b-c],[x,b-c],[x,y+c],[x+a,y+c]]);}
  case 'cylinder':{const e=Math.min(h*0.15,w*0.25);return `M ${x} ${y+e} A ${w/2} ${e} 0 0 1 ${r} ${y+e} V ${b-e} A ${w/2} ${e} 0 0 1 ${x} ${b-e} Z M ${x} ${y+e} A ${w/2} ${e} 0 0 0 ${r} ${y+e}`;}
  case 'cloud':return `M ${x+w*.25} ${b-h*.12} C ${x-w*.05} ${b-h*.12} ${x-w*.02} ${y+h*.45} ${x+w*.18} ${y+h*.42} C ${x+w*.12} ${y+h*.12} ${x+w*.42} ${y+h*.02} ${x+w*.5} ${y+h*.22} C ${x+w*.6} ${y} ${x+w*.88} ${y+h*.08} ${x+w*.82} ${y+h*.36} C ${r+w*.04} ${y+h*.4} ${r+w*.02} ${b-h*.1} ${x+w*.78} ${b-h*.12} Z`;
  case 'heart':return `M ${cx} ${b} C ${x-w*.1} ${y+h*.55} ${x+w*.05} ${y-h*.05} ${cx} ${y+h*.28} C ${r-w*.05} ${y-h*.05} ${r+w*.1} ${y+h*.55} ${cx} ${b} Z`;
  case 'arrowRight':{const s=w*0.65;return poly([[x,y+h*.25],[x+s,y+h*.25],[x+s,y],[r,cy],[x+s,b],[x+s,b-h*.25],[x,b-h*.25]]);}
  case 'arrowLeft':{const s=w*0.35;return poly([[r,y+h*.25],[x+s,y+h*.25],[x+s,y],[x,cy],[x+s,b],[x+s,b-h*.25],[r,b-h*.25]]);}
  case 'arrowUp':{const s=h*0.35;return poly([[x+w*.25,b],[x+w*.25,y+s],[x,y+s],[cx,y],[r,y+s],[r-w*.25,y+s],[r-w*.25,b]]);}
  case 'arrowDown':{const s=h*0.65;return poly([[x+w*.25,y],[x+w*.25,y+s],[x,y+s],[cx,b],[r,y+s],[r-w*.25,y+s],[r-w*.25,y]]);}
  case 'arrowLeftRight':{const s=w*0.22;return poly([[x,cy],[x+s,y],[x+s,y+h*.25],[r-s,y+h*.25],[r-s,y],[r,cy],[r-s,b],[r-s,b-h*.25],[x+s,b-h*.25],[x+s,b]]);}
  case 'chevron':{const k=w*0.25;return poly([[x,y],[r-k,y],[r,cy],[r-k,b],[x,b],[x+k,cy]]);}
  case 'homePlate':{const k=w*0.25;return poly([[x,y],[r-k,y],[r,cy],[r-k,b],[x,b]]);}
  case 'document':return `M ${x} ${y} H ${r} V ${b-h*.12} C ${r-w*.25} ${b-h*.3} ${x+w*.3} ${b+h*.1} ${x} ${b-h*.1} Z`;
  case 'predefined':{const k=w*0.1;return poly([[x,y],[r,y],[r,b],[x,b]])+` M ${x+k} ${y} V ${b} M ${r-k} ${y} V ${b}`;}
  case 'manualInput':return poly([[x,y+h*.25],[r,y],[r,b],[x,b]]);
  case 'star5':return star(x,y,w,h,5,0.4);
  case 'star8':return star(x,y,w,h,8,0.62);
  case 'banner':{const k=h*0.18;return `M ${x} ${y+k} Q ${x+w/4} ${y-k} ${cx} ${y+k} T ${r} ${y+k} V ${b-k} Q ${r-w/4} ${b+k} ${cx} ${b-k} T ${x} ${b-k} Z`;}
  case 'calloutRect':{const t=h*0.75;return poly([[x,y],[r,y],[r,y+t],[x+w*.42,y+t],[x+w*.2,b],[x+w*.26,y+t],[x,y+t]]);}
  case 'calloutRound':{const t=h*0.75;return `M ${x+w*.3} ${y+t*.97} L ${x+w*.18} ${b} L ${x+w*.42} ${y+t} A ${w/2} ${t/2} 0 1 0 ${x+w*.3} ${y+t*.97} Z`;}
  case 'line':case 'arrowLine':case 'doubleArrowLine':return `M ${x} ${cy} L ${r} ${cy}`;
  case 'vline':return `M ${cx} ${y} L ${cx} ${b}`;
  case 'diagonal':return `M ${x} ${y} L ${r} ${b}`;
  case 'text':return '';
  default:return poly([[x,y],[r,y],[r,b],[x,b]]);
 }
}

/** 도형 안에서 글이 들어갈 가로 비율(마름모·타원처럼 안쪽이 좁은 도형은 줄여 넣는다). */
export function textFactor(shape){
 if(['diamond','decision','star5','star8'].includes(shape))return .5;
 if(['ellipse','triangle','heart','cloud','hexagon','octagon','pentagon','calloutRound'].includes(shape))return .7;
 if(['arrowRight','arrowLeft','arrowLeftRight','chevron','homePlate','parallelogram','data','trapezoid'].includes(shape))return .75;
 return 1;
}

// ---- 선 모양(도형 테두리·연결선 공통) -------------------------------------------------------------
export const DASHES=[['solid','실선',''],['dash','파선','8 5'],['dot','점선','2 4'],['dashDot','일점쇄선','10 4 2 4'],['longDash','긴 파선','16 6']];
export const dashArray=kind=>(DASHES.find(([k])=>k===kind)??DASHES[0])[2];

// ---- 화살표 머리(연결선 양 끝·선 도형) ----------------------------------------------------------
export const MARKERS=[['none','없음'],['arrow','화살표(채움)'],['open','열린 화살표'],['stealth','뾰족 화살표'],['diamond','마름모'],['circle','원']];
/** 화살표 머리 SVG(<marker>). color는 #RRGGBB, kind는 MARKERS 키. */
export function markerSvg(id,kind,color){
 if(!kind||kind==='none')return '';
 const shape={
  arrow:`<path d="M 0 0 L 10 5 L 0 10 z" fill="${color}"/>`,
  open:`<path d="M 1 1 L 9 5 L 1 9" fill="none" stroke="${color}" stroke-width="1.6"/>`,
  stealth:`<path d="M 0 0 L 10 5 L 0 10 L 3 5 z" fill="${color}"/>`,
  diamond:`<path d="M 0 5 L 5 0 L 10 5 L 5 10 z" fill="${color}"/>`,
  circle:`<circle cx="5" cy="5" r="4" fill="${color}"/>`,
 }[kind];
 return shape?`<marker id="${id}" viewBox="0 0 10 10" refX="${kind==='circle'||kind==='diamond'?5:9}" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse" markerUnits="userSpaceOnUse">${shape}</marker>`:'';
}
