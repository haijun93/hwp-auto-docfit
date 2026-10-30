import test from 'node:test';
import assert from 'node:assert/strict';
import {defaultLayers,validateLayers,addLayer,moveLayer,removeLayer,assignLayer,layeredNodes,layeredEdges,visibleGraph,unlockedIds,layerOf,DEFAULT_LAYER_ID} from './layers.js';
import {validate,svg,node,edge,FORMAT} from './model.js';
import {withBackground} from './paint.js';

const PNG='data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8DwHwAFBQIAX8jx0gAAAABJRU5ErkJggg==';
const inLayer=(n,layer)=>({...n,data:{...n.data,layer}});

test('new layers stack on top with unique names; at most one step per move',()=>{
 let layers=addLayer(defaultLayers(),'a');
 layers=addLayer(layers,'b');
 assert.deepEqual(layers.map(l=>l.name),['레이어 1','레이어 2','레이어 3']);
 assert.deepEqual(moveLayer(layers,'layer-b',-1).map(l=>l.id),[DEFAULT_LAYER_ID,'layer-b','layer-a']);
 assert.equal(moveLayer(layers,'layer-b',1),layers); // 이미 맨 위
});

test('stored layers are checked; missing layers fall back to one default layer',()=>{
 assert.deepEqual(validateLayers(undefined),defaultLayers());
 assert.deepEqual(validateLayers([]),defaultLayers());
 assert.deepEqual(validateLayers([{id:'x',name:' 글 ',visible:false,locked:true}]),[{id:'x',name:'글',visible:false,locked:true}]);
 assert.throws(()=>validateLayers([{id:'x',name:'a'},{id:'x',name:'b'}]));
 assert.throws(()=>validateLayers([{id:'<bad>',name:'a'}]));
 // 사라진 레이어를 가리키는 개체는 맨 아래 레이어로 본다.
 assert.equal(layerOf(inLayer(node('a',0,0),'gone'),defaultLayers()),DEFAULT_LAYER_ID);
});

test('hidden layers are hidden on screen, locked layers cannot be picked, order follows layers',()=>{
 const layers=[{id:'low',name:'아래',visible:true,locked:true},{id:'top',name:'위',visible:false,locked:false}];
 const a=inLayer(node('a',0,0,'rectangle','blue','a'),'low'),b=inLayer(node('b',0,0,'rectangle','blue','b'),'top');
 const [sa,sb]=layeredNodes([{...a,selected:true},b],layers);
 assert.equal(sa.selectable,false);assert.equal(sa.draggable,false);assert.equal(sa.selected,false);
 assert.equal(sb.hidden,true);
 assert.ok(sb.zIndex>sa.zIndex);
 const edges=layeredEdges([edge('a','b','','e')],[a,b],layers);
 assert.equal(edges[0].hidden,true);
 assert.deepEqual([...unlockedIds([a,b],layers)],['b']);
});

test('removing a layer removes its objects and their connectors, keeps the last layer',()=>{
 const layers=[{id:'low',name:'아래',visible:true,locked:false},{id:'top',name:'위',visible:true,locked:false}];
 const a=inLayer(node('a',0,0,'rectangle','blue','a'),'low'),b=inLayer(node('b',0,0,'rectangle','blue','b'),'top');
 const graph={layers,nodes:[a,b],edges:[edge('a','b','','e')]};
 const next=removeLayer(graph,'top');
 assert.deepEqual(next.nodes.map(n=>n.id),['a']);assert.equal(next.edges.length,0);
 assert.equal(removeLayer(next,'low'),next);
 assert.equal(assignLayer([a],['a'],'top')[0].data.layer,'top');
});

test('layers survive save/load, and export leaves out hidden layers in layer order',()=>{
 const layers=[{id:'low',name:'아래',visible:true,locked:false},{id:'mid',name:'숨김',visible:false,locked:false},{id:'top',name:'위',visible:true,locked:false}];
 const top=inLayer(node('위 글',0,0,'rectangle','blue','t'),'top'),mid=inLayer(node('숨은 글',0,0,'rectangle','blue','m'),'mid'),low=inLayer(node('아래 글',0,0,'rectangle','blue','l'),'low');
 const nodes=withBackground([top,mid,low],PNG,100,80);
 const snapshot={format:FORMAT,version:1,layers,nodes,edges:[]};
 const checked=validate(snapshot);
 assert.deepEqual(checked.layers,layers);
 assert.deepEqual(checked.nodes.map(n=>n.data.layer),[undefined,'top','mid','low']);
 assert.deepEqual(visibleGraph(checked).nodes.map(n=>n.id),['paint-background','l','t']);
 const image=svg(snapshot).source;
 assert.ok(!image.includes('숨은 글'));
 assert.ok(image.indexOf('아래 글')<image.indexOf('위 글'));
 // 레이어가 없는 예전 문서는 그대로 열린다.
 assert.equal(validate({format:FORMAT,version:1,nodes:[node('a',0,0)],edges:[]}).layers,undefined);
});
