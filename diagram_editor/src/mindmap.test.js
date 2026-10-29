import test from 'node:test';
import assert from 'node:assert/strict';
import {sampleMindmap,mindmapNode,addChild,addSibling,findNode,removeNode,updateNode,validateMindmap,mindmapGraph,positionMindmap,reparentNode,autoLayoutMindmap} from './mindmap.js';
import {decode,svg} from './model.js';

test('manual placement survives save/reload/export, with other branches stationary',()=>{
 const map=sampleMindmap(),before=mindmapGraph(map),child=map.root.children[0];
 const moved=updateNode(positionMindmap(map,{[child.id]:{x:1780,y:-800}}),child.id,{size:{width:350,height:180},edge:{style:{line:"straight",color:"#FF0000",width:3,dash:"longDash",start:"open",end:"arrow"}}});
 const saved=decode(JSON.parse(JSON.stringify({format:'docfit-flow',version:1,nodes:[],edges:[],mindmap:moved})));
 const graph=mindmapGraph(saved.mindmap);
 assert.equal(graph.nodes.find(n=>n.id===child.id).width,350);
 assert.equal(graph.edges.find(e=>e.target===child.id).data.dash,'longDash');
 assert.deepEqual(graph.nodes.find(n=>n.id===child.id).position,{x:1780,y:-800});
 for(const n of before.nodes.filter(n=>n.id!==child.id))assert.deepEqual(graph.nodes.find(v=>v.id===n.id).position,n.position);
 const image=svg(saved);assert.ok(image.source.includes(child.text));assert.ok(image.width>0);
 assert.equal(findNode(autoLayoutMindmap(moved),child.id).node.position,undefined);
});
test('reparent keeps descendants and positions and rejects root/cycles',()=>{
 const map=positionMindmap(sampleMindmap(),{}),a=map.root.children[0],b=map.root.children[1];
 const changed=reparentNode(map,a.id,b.id,{sourceHandle:'bottom',targetHandle:'top'});
 assert.equal(findNode(changed,a.id).parent.id,b.id);
 assert.deepEqual(findNode(changed,a.id).node.position,a.position);
 assert.equal(findNode(changed,a.children[0].id).parent.id,a.id);
 assert.throws(()=>reparentNode(changed,b.id,a.children[0].id));
 assert.throws(()=>reparentNode(map,map.root.id,a.id));
});
test('line label, remove/reconnect and delete subtree preserve hierarchy',()=>{
 const map=sampleMindmap(),a=map.root.children[0],b=map.root.children[1];
 const hidden=validateMindmap(updateNode(map,a.id,{edge:{hidden:true,label:'자유 연결'}}));
 assert.ok(!mindmapGraph(hidden).edges.some(e=>e.target===a.id));
 const connected=reparentNode(hidden,a.id,b.id);
 assert.equal(mindmapGraph(connected).edges.find(e=>e.target===a.id).label,'자유 연결');
 const removed=removeNode(connected,a.id);
 assert.equal(findNode(removed,a.children[0].id),null);
});
test('hierarchy has no fixed level limit: 250 nested child branches round-trip',()=>{
 let map={root:mindmapNode('중심'),layout:'right'},id=map.root.id;
 for(let i=0;i<250;i++){const next=addChild(map,id,'하위 '+i);map=next.map;id=next.id;}
 assert.equal(mindmapGraph(validateMindmap(map)).nodes.length,251);
 const sibling=addSibling(map,id);
 assert.equal(findNode(sibling.map,sibling.id).parent.id,findNode(map,id).parent.id);
});
test('invalid positions and over-capacity documents are rejected',()=>{
 const map=sampleMindmap();map.root.position={x:Infinity,y:0};assert.throws(()=>validateMindmap(map));
 map.root.position={x:0,y:0};map.root.children=Array.from({length:301},()=>mindmapNode());
 assert.throws(()=>validateMindmap(map));
});

test('branch shapes: one / same level / branch / all scopes, circle stays square',async()=>{
 const {restyleNodes,MINDMAP_SHAPES}=await import('./mindmap.js');
 const {shapePath,SHAPES}=await import('./shapes.js');
 for(const [key] of MINDMAP_SHAPES)assert.ok(SHAPES.has(key),key);
 assert.match(shapePath('circle',0,0,200,64),/A 32 32/);
 const map=sampleMindmap(),first=map.root.children[0],leaf=first.children[0];
 const shapeOf=(m,id)=>mindmapGraph(m).nodes.find(n=>n.id===id).data.shape;
 const one=restyleNodes(map,leaf.id,'one',{shape:'circle'});
 assert.equal(shapeOf(one,leaf.id),'circle');
 assert.equal(shapeOf(one,first.children[1].id),'roundRect');
 const level=restyleNodes(map,leaf.id,'level',{shape:'ellipse'});
 for(const b of map.root.children)for(const c of b.children)assert.equal(shapeOf(level,c.id),'ellipse');
 assert.equal(shapeOf(level,first.id),'roundRect');
 const branch=restyleNodes(map,first.id,'branch',{shape:'hexagon'});
 assert.equal(shapeOf(branch,first.id),'hexagon');
 assert.equal(shapeOf(branch,leaf.id),'hexagon');
 assert.equal(shapeOf(branch,map.root.children[1].id),'roundRect');
 const all=restyleNodes(map,leaf.id,'all',{shape:'rectangle'});
 assert.equal(shapeOf(all,map.root.id),'rectangle');
 const node=mindmapGraph(one).nodes.find(n=>n.id===leaf.id);
 assert.equal(node.width,node.height);
 validateMindmap(all);validateMindmap(restyleNodes(map,leaf.id,'all',{shape:'underline'}));
 const sized=restyleNodes(updateNode(map,leaf.id,{size:{width:300,height:90}}),leaf.id,'one',{shape:'circle'});
 assert.deepEqual(findNode(sized,leaf.id).node.size,{width:300,height:300});
});

test('circle is not offered as a mindmap branch shape (2026-10-30 user request)',async()=>{
 const {MINDMAP_SHAPES}=await import('./mindmap.js');
 assert.ok(!MINDMAP_SHAPES.some(([k])=>k==='circle'));
 assert.ok(MINDMAP_SHAPES.some(([k])=>k==='ellipse'));
});

test('map themes: shape × palette × ground drive every branch unless a branch has its own style',async()=>{
 const {MINDMAP_THEME_SHAPES,MINDMAP_PALETTES,MINDMAP_GROUNDS,clearBranchStyles,themeOf}=await import('./mindmap.js');
 const {svg}=await import('./model.js');
 const map=sampleMindmap(),first=map.root.children[0],leaf=first.children[0];
 const look=(m,id)=>mindmapGraph(m).nodes.find(n=>n.id===id).data;
 assert.deepEqual(themeOf(map),{shape:'classic',palette:'office',ground:'light'});
 // 기본 테마는 예전 모양 그대로
 assert.equal(look(map,map.root.id).shape,'ellipse');assert.equal(look(map,map.root.id).fill,'#1D4ED8');
 const expect={pill:['terminator','terminator','text'],capsule:['terminator','terminator','text'],line:['roundRect','underline','underline'],block:['roundRect','roundRect','roundRect'],classic:['ellipse','roundRect','roundRect']};
 for(const [shape] of MINDMAP_THEME_SHAPES){
  const m={...map,theme:{shape,palette:'forest',ground:'light'}};
  assert.deepEqual([look(m,m.root.id).shape,look(m,first.id).shape,look(m,leaf.id).shape],expect[shape],shape);
  validateMindmap(m);
 }
 const block=mindmapGraph({...map,theme:{shape:'block',palette:'office',ground:'light'}});
 assert.equal(block.edges[0].data.line,'step');
 const dark=mindmapGraph({...map,theme:{shape:'pill',palette:'ocean',ground:'dark'}});
 assert.equal(dark.background,'#1E2430');
 assert.match(svg({format:'docfit-flow',version:1,nodes:[],edges:[],mindmap:{...map,theme:{shape:'pill',palette:'ocean',ground:'dark'}}}).source,/fill="#1E2430"/);
 assert.equal(MINDMAP_PALETTES.length,8);assert.equal(MINDMAP_GROUNDS.length,3);
 // 가지별 서식이 테마보다 우선, 지우면 테마로
 const own=updateNode({...map,theme:{shape:'line',palette:'office',ground:'light'}},leaf.id,{style:{shape:'hexagon'}});
 assert.equal(look(own,leaf.id).shape,'hexagon');
 assert.equal(look(clearBranchStyles(own),leaf.id).shape,'underline');
 assert.throws(()=>validateMindmap({...map,theme:{shape:'star',palette:'office',ground:'light'}}));
 const saved=decode(JSON.parse(JSON.stringify({format:'docfit-flow',version:1,nodes:[],edges:[],mindmap:{...map,theme:{shape:'capsule',palette:'berry',ground:'tint'}}})));
 assert.deepEqual(saved.mindmap.theme,{shape:'capsule',palette:'berry',ground:'tint'});
});
