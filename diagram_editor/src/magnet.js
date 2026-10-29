// 다이어그램 자석: 연결선이 도형에 붙고(가까운 연결점·마주 보는 면), 도형을 옮길 때 다른 도형에 맞춰 붙는다.
// PowerPoint의 연결선·스마트 가이드, draw.io의 floating 연결선을 참고했다. 화면과 무관한 순수 함수다.
const SIDES=['top','right','bottom','left'];

/** 도형 상자: 위치와 크기(화면에서 잰 크기가 있으면 그것). */
export function box(n){
 const w=n.measured?.width??n.width??220,h=n.measured?.height??n.height??90;
 return {x:n.position.x,y:n.position.y,w,h,cx:n.position.x+w/2,cy:n.position.y+h/2};
}

/** 한 면의 연결점 좌표. */
export function sidePoint(n,side){
 const b=box(n);
 return side==='top'?{x:b.cx,y:b.y}:side==='bottom'?{x:b.cx,y:b.y+b.h}:side==='left'?{x:b.x,y:b.cy}:{x:b.x+b.w,y:b.cy};
}

/** 점에서 가장 가까운 연결점의 면. */
export function nearestSide(n,point){
 let best='top',dist=Infinity;
 for(const side of SIDES){const p=sidePoint(n,side),d=Math.hypot(p.x-point.x,p.y-point.y);if(d<dist){dist=d;best=side;}}
 return best;
}

/** 두 도형이 서로 마주 보는 면(가로로 더 떨어져 있으면 좌우, 아니면 위아래). */
export function facingSides(a,b){
 const A=box(a),B=box(b),dx=B.cx-A.cx,dy=B.cy-A.cy;
 // 도형 크기를 고려해 겹친 방향을 덜 친다(넓은 도형끼리 위아래로 놓였을 때 좌우로 붙지 않게).
 const gx=Math.abs(dx)-(A.w+B.w)/2,gy=Math.abs(dy)-(A.h+B.h)/2;
 if(gx>gy)return dx>=0?['right','left']:['left','right'];
 return dy>=0?['bottom','top']:['top','bottom'];
}

/** 자동 연결점(data.autoSide)이 켜진 연결선을 도형 위치에 맞춰 마주 보는 면으로 다시 붙인다. 바뀐 것이 없으면 같은 배열. */
export function autoRoute(nodes,edges){
 const byId=new Map(nodes.map(n=>[n.id,n]));let changed=false;
 const next=edges.map(e=>{
  if(!e.data?.autoSide)return e;
  const a=byId.get(e.source),b=byId.get(e.target);if(!a||!b)return e;
  const [s,t]=facingSides(a,b);
  if(e.sourceHandle===s&&e.targetHandle===t)return e;
  changed=true;return {...e,sourceHandle:s,targetHandle:t};
 });
 return changed?next:edges;
}

/** 놓은 곳(흐름 좌표) 아래의 도형. 선 도형은 붙일 대상이 아니다. */
export function nodeAt(nodes,point,skip=new Set(),isLine=()=>false){
 for(let i=nodes.length-1;i>=0;i--){
  const n=nodes[i];if(skip.has(n.id)||isLine(n))continue;
  const b=box(n);
  if(point.x>=b.x&&point.x<=b.x+b.w&&point.y>=b.y&&point.y<=b.y+b.h)return n;
 }
 return null;
}

/**
 * 스마트 가이드: 옮기는 도형의 왼쪽·가운데·오른쪽(위·가운데·아래)이 다른 도형과 threshold 안이면 맞춘다.
 * 돌려주는 값: 맞춘 위치 {x,y}와 화면에 그릴 안내선 [{x1,y1,x2,y2}].
 */
export function smartGuides(moving,others,threshold=6){
 const m=box(moving);
 let bestX=null,bestY=null;
 const xs=[[m.x,0],[m.cx,m.w/2],[m.x+m.w,m.w]],ys=[[m.y,0],[m.cy,m.h/2],[m.y+m.h,m.h]];
 for(const o of others){
  if(o.id===moving.id)continue;
  const b=box(o);
  for(const [value,offset] of xs)for(const target of [b.x,b.cx,b.x+b.w]){
   const d=Math.abs(value-target);
   if(d<=threshold&&(!bestX||d<bestX.d))bestX={d,x:target-offset,line:target,other:b};
  }
  for(const [value,offset] of ys)for(const target of [b.y,b.cy,b.y+b.h]){
   const d=Math.abs(value-target);
   if(d<=threshold&&(!bestY||d<bestY.d))bestY={d,y:target-offset,line:target,other:b};
  }
 }
 const x=bestX?bestX.x:m.x,y=bestY?bestY.y:m.y,lines=[];
 if(bestX){const o=bestX.other;lines.push({x1:bestX.line,y1:Math.min(o.y,y)-10,x2:bestX.line,y2:Math.max(o.y+o.h,y+m.h)+10});}
 if(bestY){const o=bestY.other;lines.push({x1:Math.min(o.x,x)-10,y1:bestY.line,x2:Math.max(o.x+o.w,x+m.w)+10,y2:bestY.line});}
 return {x,y,lines};
}
