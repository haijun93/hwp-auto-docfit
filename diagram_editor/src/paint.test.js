import test from 'node:test';
import assert from 'node:assert/strict';
import {freehandNode,freehandPath,withBackground,withoutBackground,fitSize,paintStyle,BACKGROUND_ID,validPoints,isImageSrc} from './paint.js';
import {validate,svg,decode,FORMAT,node,computeNodeAutoFitBox} from './model.js';

const PNG='data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8DwHwAFBQIAX8jx0gAAAABJRU5ErkJggg==';
const snap=nodes=>({format:FORMAT,version:1,nodes,edges:[]});

test('pen stroke becomes one object normalised to its box, tiny jitter dropped',()=>{
 const pts=[{x:10,y:10},{x:10.5,y:10.4},{x:60,y:40},{x:110,y:20}];
 const n=freehandNode(pts,{stroke:'#2563EB',strokeWidth:5});
 assert.equal(n.data.shape,'freehand');assert.equal(n.data.points.length,3);
 assert.ok(validPoints(n.data.points));
 assert.ok(n.position.x<10&&n.position.y<10&&n.width>100);
 assert.equal(freehandNode([{x:1,y:1}]),null);
 assert.match(freehandPath(n.data.points,0,0,n.width,n.height),/^M .* Q .* L /);
});

test('background sits at the back, locked, and is replaced not duplicated',()=>{
 const shape=node('글',5,5,'text');
 let nodes=withBackground([shape],PNG,800,600);
 assert.equal(nodes[0].id,BACKGROUND_ID);assert.equal(nodes[0].draggable,false);assert.equal(nodes[0].zIndex,-1);
 nodes=withBackground(nodes,PNG,400,300);
 assert.equal(nodes.filter(n=>n.id===BACKGROUND_ID).length,1);assert.equal(nodes[0].width,400);
 assert.deepEqual(withoutBackground(nodes).map(n=>n.id),[shape.id]);
 assert.deepEqual(fitSize(4000,1000,2000),{width:2000,height:500});
 assert.deepEqual(fitSize(300,200,2000),{width:300,height:200});
});

test('paint document saves and reloads; export draws photo, pen and shapes',()=>{
 const pen=freehandNode([{x:0,y:0},{x:50,y:50},{x:100,y:0}],{stroke:'#DC2626',strokeWidth:3});
 const box=node('',20,20,'rectangle','blue',undefined,paintStyle('rectangle'));
 const text=node('설명',30,30,'text','blue',undefined,paintStyle('text'));
 const doc=snap([...withBackground([],PNG,200,100),pen,box,text]);
 const back=decode(JSON.parse(JSON.stringify(doc)));
 const bg=back.nodes.find(n=>n.id===BACKGROUND_ID);
 assert.equal(bg.data.src,PNG);assert.equal(bg.selectable,false);assert.equal(bg.deletable,false);
 assert.deepEqual(back.nodes.find(n=>n.data.shape==='freehand').data.points,pen.data.points);
 assert.equal(back.nodes.find(n=>n.id===box.id).data.fill,'none');
 const out=svg(doc).source;
 assert.match(out,/<image href="data:image\/png;base64,/);
 assert.match(out,/stroke="#DC2626"[^>]*stroke-linecap="round"/);
 assert.match(out,/>설명</);
 // 펜 선 상자는 글 상자처럼 늘어나지 않는다.
 assert.equal(computeNodeAutoFitBox(pen).width,pen.width);
});

test('bad paint data is refused',()=>{
 assert.equal(isImageSrc('javascript:alert(1)'),false);
 assert.equal(isImageSrc('data:image/svg+xml;base64,AAAA'),false);
 const bad=freehandNode([{x:0,y:0},{x:9,y:9}]);bad.data.points=[[0,0],[2,2]];
 assert.throws(()=>validate(snap([bad])));
 const img=withBackground([],PNG,10,10)[0];img.data.src='data:text/html;base64,AAAA';
 assert.throws(()=>validate(snap([img])));
 const fake=withBackground([],PNG,10,10)[0];fake.id='other';
 assert.throws(()=>validate(snap([fake])));
});
