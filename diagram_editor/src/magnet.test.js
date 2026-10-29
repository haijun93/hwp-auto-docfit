import test from 'node:test';
import assert from 'node:assert/strict';
import {nearestSide,facingSides,autoRoute,nodeAt,smartGuides} from './magnet.js';

const n=(id,x,y,w=100,h=50)=>({id,position:{x,y},width:w,height:h});

test('nearest connection point on a shape',()=>{
 const a=n('a',0,0);
 assert.equal(nearestSide(a,{x:50,y:-5}),'top');
 assert.equal(nearestSide(a,{x:104,y:20}),'right');
 assert.equal(nearestSide(a,{x:40,y:49}),'bottom');
 assert.equal(nearestSide(a,{x:-3,y:30}),'left');
});

test('facing sides follow relative position, preferring the wider gap',()=>{
 assert.deepEqual(facingSides(n('a',0,0),n('b',300,10)),['right','left']);
 assert.deepEqual(facingSides(n('a',0,0),n('b',-300,0)),['left','right']);
 assert.deepEqual(facingSides(n('a',0,0),n('b',20,200)),['bottom','top']);
 assert.deepEqual(facingSides(n('a',0,200),n('b',30,0)),['top','bottom']);
 // 넓은 도형이 위아래로 조금 비켜 있으면 위아래로 붙는다.
 assert.deepEqual(facingSides(n('a',0,0,400,40),n('b',150,120,400,40)),['bottom','top']);
});

test('autoRoute only touches auto-side edges and keeps identity when nothing changes',()=>{
 const nodes=[n('a',0,0),n('b',300,0)];
 const edges=[{id:'e1',source:'a',target:'b',sourceHandle:'bottom',targetHandle:'top',data:{autoSide:true}},
  {id:'e2',source:'a',target:'b',sourceHandle:'bottom',targetHandle:'top',data:{}}];
 const routed=autoRoute(nodes,edges);
 assert.equal(routed[0].sourceHandle,'right');assert.equal(routed[0].targetHandle,'left');
 assert.equal(routed[1],edges[1]);
 assert.equal(autoRoute(nodes,routed),routed);
 nodes[1].position={x:0,y:300};
 assert.deepEqual([autoRoute(nodes,routed)[0].sourceHandle,autoRoute(nodes,routed)[0].targetHandle],['bottom','top']);
});

test('nodeAt finds the top-most shape and skips lines and the source',()=>{
 const nodes=[n('a',0,0),n('b',50,20),n('line',60,30)];
 const isLine=x=>x.id==='line';
 assert.equal(nodeAt(nodes,{x:70,y:40},new Set(),isLine).id,'b');
 assert.equal(nodeAt(nodes,{x:70,y:40},new Set(['b']),isLine).id,'a');
 assert.equal(nodeAt(nodes,{x:500,y:500}),null);
});

test('smart guides snap edges and centers within the threshold and draw a guide',()=>{
 const target=n('t',200,100,100,50);
 // 왼쪽 끝이 4px 어긋남 → 맞춤, 세로는 멀어서 그대로
 let g=smartGuides(n('m',204,300),[target]);
 assert.equal(g.x,200);assert.equal(g.y,300);
 assert.equal(g.lines.length,1);assert.equal(g.lines[0].x1,200);
 // 가운데끼리(가로 중심 250)
 g=smartGuides(n('m',147,300,200,50),[target]);
 assert.equal(g.x,150);
 // 위·아래 가운데 맞춤
 g=smartGuides(n('m',600,103),[target]);
 assert.equal(g.y,100);assert.equal(g.lines[0].y1,100);
 // 멀면 그대로, 안내선 없음
 g=smartGuides(n('m',230,400),[target]);
 assert.deepEqual([g.x,g.y,g.lines.length],[230,400,0]);
});
