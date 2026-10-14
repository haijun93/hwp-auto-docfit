import test from 'node:test';
import assert from 'node:assert/strict';
import {FORMAT,templates,template,validate,decode,node,edge,svg} from './model.js';
const document = graph=>({format:FORMAT,version:1,nodes:graph.nodes,edges:graph.edges});
test('all ten templates round-trip with connected decision branches',()=>{
 assert.equal(Object.keys(templates).length,10);
 for(const key of Object.keys(templates)){
  const graph=document(template(key));
  assert.deepEqual(validate(JSON.parse(JSON.stringify(graph))),graph);
 }
 const flow=template('complaint');
 assert.ok(flow.edges.some(e=>e.label==='예'));
 assert.ok(flow.edges.some(e=>e.label==='아니오'));
 assert.ok(flow.edges.some(e=>e.label==='재검토'));
});
test('invalid coordinates, duplicate identities and dangling links are rejected',()=>{
 const graph=document(template('general'));
 for(const mutate of [
  g=>{g.nodes[0].position.x=Infinity;},
  g=>{g.nodes[1].id=g.nodes[0].id;},
  g=>{g.edges[0].target='missing';},
  g=>{g.edges[1].target=g.edges[0].id;},
  g=>{g.nodes[0].data.shape='script';},
 ]){
  const copy=structuredClone(graph);mutate(copy);assert.throws(()=>validate(copy));
 }
});
test('SVG escapes untrusted text and caps raster size',()=>{
 const a=node('<script>alert("x")</script>',0,0);
 const output=svg(document({nodes:[a],edges:[]}));
 assert.match(output.source,/&lt;script&gt;/);assert.doesNotMatch(output.source,/<script/i);
 assert.throws(()=>svg(document({nodes:[a,node('far',50000,0)],edges:[]})));
});
test('supported legacy templates convert without editing the source snapshot',()=>{
 const snapshot={document:{store:{
  page:{typeName:'page'},
  a:{typeName:'shape',id:'shape:a',type:'geo',x:100,y:60,props:{geo:'rectangle',w:220,h:90,text:'접수',color:'blue'}},
  b:{typeName:'shape',id:'shape:b',type:'geo',x:100,y:220,props:{geo:'rectangle',w:220,h:90,text:'검토',color:'blue'}},
  arrow:{typeName:'shape',id:'shape:arrow',type:'arrow',x:0,y:0,props:{start:{x:210,y:150},end:{x:210,y:220}}},
 }}};
 const before=JSON.stringify(snapshot),converted=decode(snapshot);
 assert.equal(converted.converted,true);assert.equal(converted.edges.length,1);
 assert.equal(JSON.stringify(snapshot),before);
 snapshot.document.store.a.type='draw';assert.throws(()=>decode(snapshot));
});
test('arbitrary HTML fields are discarded and text remains data',()=>{
 const graph=document(template('general'));graph.nodes[0].dangerouslySetInnerHTML={__html:'<script/>'};
 assert.equal(validate(graph).nodes[0].dangerouslySetInnerHTML,undefined);
});
test('400 Korean characters stay in the safe interior and export bounds of every shape',async()=>{
 const {computeNodeAutoFitBox,layoutGraph,getDiagramBounds,textWidth,PADDING_X,PADDING_Y,LINE_HEIGHT,edgeLabelBox}=await import('./model.js');
 for(const shape of ['rectangle','diamond','ellipse','text']){
  const original=node('한글 문장과 긴어절'.repeat(40),-50,20,shape);
  const graph=layoutGraph({nodes:[original],edges:[]}),n=graph.nodes[0],box=computeNodeAutoFitBox(n),bounds=getDiagramBounds(graph);
  assert.ok(box.lines.length>1);
  for(const line of box.lines)assert.ok(textWidth(line)+2*PADDING_X<=n.width*box.factor+.001);
  assert.ok(box.lines.length*LINE_HEIGHT+2*PADDING_Y<=n.height*box.factor+.001);
  assert.ok(n.position.x>=bounds.x+20&&n.position.y>=bounds.y+20);
  assert.ok(n.position.x+n.width<=bounds.x+bounds.width-20+.001);
  assert.ok(n.position.y+n.height<=bounds.y+bounds.height-20+.001);
 }
 const a=node('A',0,0),b=node('B',0,180),e=edge(a.id,b.id,'매우 긴 분기 설명 '.repeat(25));
 const graph=layoutGraph({nodes:[a,b],edges:[e]}),box=edgeLabelBox(e,graph.nodes),bounds=getDiagramBounds(graph);
 assert.ok(box.y-box.height/2>=bounds.y+20-.001);
 assert.ok(box.y+box.height/2<=bounds.y+bounds.height-20+.001);
});
