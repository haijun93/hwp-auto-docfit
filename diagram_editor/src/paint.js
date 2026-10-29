// 그림판: 사진을 배경으로 깔고 그 위에 펜(자유 곡선)·도형·선·글상자를 독립 개체로 올린다(PPT처럼 각각 옮기고 고친다).
// 배경 사진은 맨 뒤에 잠긴 그림 개체(shape 'image', data.background)이고, 펜 선은 shape 'freehand'(0~1로 맞춘 점 목록)다.
export const BACKGROUND_ID='paint-background';
export const MAX_POINTS=1500;
export const MAX_IMAGE_CHARS=16*1024*1024;
const DATA_URL=/^data:image\/(png|jpeg);base64,[A-Za-z0-9+/=]+$/;

export const isImageSrc=src=>typeof src==='string'&&src.length<=MAX_IMAGE_CHARS&&DATA_URL.test(src);
export function validPoints(points){
 return Array.isArray(points)&&points.length>=2&&points.length<=MAX_POINTS&&points.every(p=>Array.isArray(p)&&p.length===2&&p.every(v=>Number.isFinite(v)&&v>=0&&v<=1));
}

/** 펜으로 그린 점(흐름 좌표)을 개체 하나로: 상자에 맞춰 0~1로 바꾸고, 가까운 점은 줄인다. */
export function freehandNode(points,style={},identity=crypto.randomUUID()){
 const kept=[];
 for(const p of points){const last=kept[kept.length-1];if(!last||Math.hypot(p.x-last.x,p.y-last.y)>=1.5)kept.push(p);}
 while(kept.length>MAX_POINTS)for(let i=kept.length-2;i>0&&kept.length>MAX_POINTS;i-=2)kept.splice(i,1);
 if(kept.length<2)return null;
 const pad=Math.max(2,(style.strokeWidth??3)/2+1);
 const minX=Math.min(...kept.map(p=>p.x))-pad,minY=Math.min(...kept.map(p=>p.y))-pad;
 const w=Math.max(8,Math.max(...kept.map(p=>p.x))+pad-minX),h=Math.max(8,Math.max(...kept.map(p=>p.y))+pad-minY);
 const round=v=>Math.round(v*10000)/10000;
 return {id:identity,type:'flow',position:{x:minX,y:minY},width:w,height:h,
  data:{label:'',shape:'freehand',color:'blue',fill:'none',stroke:style.stroke??'#DC2626',strokeWidth:style.strokeWidth??3,
   points:kept.map(p=>[round((p.x-minX)/w),round((p.y-minY)/h)])}};
}

/** 0~1 점 목록을 (x,y,w,h) 상자의 SVG 경로로(부드러운 이차 곡선). */
export function freehandPath(points,x,y,w,h){
 const P=points.map(([u,v])=>[x+u*w,y+v*h]);
 if(P.length<3)return 'M '+P.map(p=>p.map(n=>n.toFixed(1)).join(' ')).join(' L ');
 let d='M '+P[0][0].toFixed(1)+' '+P[0][1].toFixed(1);
 for(let i=1;i<P.length-1;i++){const mx=(P[i][0]+P[i+1][0])/2,my=(P[i][1]+P[i+1][1])/2;d+=' Q '+P[i][0].toFixed(1)+' '+P[i][1].toFixed(1)+' '+mx.toFixed(1)+' '+my.toFixed(1);}
 const last=P[P.length-1];return d+' L '+last[0].toFixed(1)+' '+last[1].toFixed(1);
}

/** 배경 사진 개체: 맨 뒤, 끌거나 고를 수 없고 지워지지 않는다(배경 지우기 단추로만). */
export function backgroundNode(src,width,height){
 return {id:BACKGROUND_ID,type:'flow',position:{x:0,y:0},width,height,zIndex:-1,draggable:false,selectable:false,deletable:false,
  data:{label:'',shape:'image',color:'blue',src,background:true,fill:'none',stroke:'none',strokeWidth:0}};
}
/** 배경을 바꾸거나 넣는다(다른 개체는 그대로). */
export function withBackground(nodes,src,width,height){
 return [backgroundNode(src,width,height),...nodes.filter(n=>n.id!==BACKGROUND_ID)];
}
export const withoutBackground=nodes=>nodes.filter(n=>n.id!==BACKGROUND_ID);

/** 긴 변이 max를 넘지 않게 줄인 크기. */
export function fitSize(width,height,max=2000){
 const s=Math.min(1,max/Math.max(width,height));
 return {width:Math.max(1,Math.round(width*s)),height:Math.max(1,Math.round(height*s))};
}

/** 그림판 기본 서식: 사진 위에 그리므로 도형은 속이 비고 빨간 테두리, 글은 굵은 검정 16pt. */
export function paintStyle(shape,color='#DC2626',width=3){
 if(shape==='text')return {fill:'none',stroke:'none',textColor:'#111827',size:16,bold:true};
 return {fill:'none',stroke:color,strokeWidth:width};
}
