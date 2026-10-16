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
