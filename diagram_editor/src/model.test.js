import test from 'node:test';
import assert from 'node:assert/strict';
import {FORMAT,templates,template,validate,decode,node,edge,svg,id,computeNodeAutoFitBox} from './model.js';
const document = graph=>({format:FORMAT,version:1,nodes:graph.nodes,edges:graph.edges});
test('two templates (horizontal·vertical) round-trip with branches and varied shapes',()=>{
 assert.deepEqual(Object.keys(templates),['horizontal','vertical']);
 for(const key of Object.keys(templates)){
  const graph=document(template(key));
  assert.deepEqual(validate(JSON.parse(JSON.stringify(graph))),graph);
  assert.ok(new Set(graph.nodes.map(n=>n.data.shape)).size>=5);
  assert.ok(graph.edges.some(e=>e.label==='예')&&graph.edges.some(e=>e.label==='아니오'));
 }
 const v=template('vertical'),h=template('horizontal');
 assert.ok(v.nodes[6].position.y>v.nodes[0].position.y&&h.nodes[6].position.x>h.nodes[0].position.x);
});
test('invalid coordinates, duplicate identities and dangling links are rejected',()=>{
 const graph=document(template('horizontal'));
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
test('flow documents round-trip and removed snapshot format is rejected',()=>{
 const graph=document(template('horizontal'));
 assert.deepEqual(decode(graph),{...validate(graph),converted:false});
 assert.throws(()=>decode({document:{store:{}}}));
});

test('arbitrary HTML fields are discarded and text remains data',()=>{
 const graph=document(template('horizontal'));graph.nodes[0].dangerouslySetInnerHTML={__html:'<script/>'};
 assert.equal(validate(graph).nodes[0].dangerouslySetInnerHTML,undefined);
});
test('400 Korean characters stay in the safe interior and export bounds of every shape',async()=>{
 const {computeNodeAutoFitBox,layoutGraph,getDiagramBounds,textWidth,PADDING_X,PADDING_Y,LINE_HEIGHT,edgeLabelBox}=await import('./model.js');
 for(const shape of ['rectangle','diamond','ellipse','text','hexagon','cloud','star5','arrowRight','cylinder']){
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

test('every PPT shape draws a path and keeps its fill, border and dash',async()=>{
 const {SHAPES,LINE_SHAPES,shapePath}=await import('./shapes.js');
 assert.ok(SHAPES.size>=40);
 for(const shape of SHAPES.keys()){
  if(shape==='text')continue;
  const d=shapePath(shape,10,20,200,80);
  assert.match(d,/^M /,shape);assert.doesNotMatch(d,/NaN|undefined/,shape);
 }
 const a={...node('가',0,0,'hexagon'),data:{...node('가',0,0,'hexagon').data,fill:'#FDE047',stroke:'#DC2626',strokeWidth:4,dash:'dash'}};
 const b={...node('',0,200,'arrowLine'),data:{...node('',0,200,'arrowLine').data,lineStart:'circle'}};
 const out=svg(document({nodes:[a,b],edges:[]})).source;
 assert.match(out,/fill="#FDE047"/);assert.match(out,/stroke="#DC2626"/);assert.match(out,/stroke-dasharray="8 5"/);
 assert.match(out,/<marker[^>]*>.*<circle/);
 assert.ok(LINE_SHAPES.has('arrowLine'));
 for(const bad of [{fill:'red'},{strokeWidth:20},{dash:'wavy'},{lineEnd:'skull'}])
  assert.throws(()=>validate(document({nodes:[{...a,data:{...a.data,...bad}}],edges:[]})));
});
test('connectors choose line kind, color, width, dash and both arrow heads',()=>{
 const a=node('A',0,0),b=node('B',400,0);
 const e=edge(a.id,b.id,'',id(),'right','left',{line:'curve',color:'#DC2626',width:3,dash:'dot',start:'diamond',end:'open'});
 const doc=validate(document({nodes:[a,b],edges:[e]}));
 assert.deepEqual(doc.edges[0].data,{line:'curve',color:'#DC2626',width:3,dash:'dot',start:'diamond',end:'open'});
 const out=svg(doc).source;
 assert.match(out,/ C /);assert.match(out,/stroke-dasharray="2 4"/);assert.match(out,/marker-start=/);
 assert.throws(()=>validate(document({nodes:[a,b],edges:[{...e,data:{...e.data,line:'zigzag'}}]})));
 // 예전 연결선(data 없음)은 그대로 꺾은선·화살표
 assert.equal(validate(document({nodes:[a,b],edges:[edge(a.id,b.id)]})).edges[0].data,undefined);
});
test('mind map: add child/sibling, restyle, auto layout both sides and export',async()=>{
 const mm=await import('./mindmap.js');
 let map=mm.sampleMindmap();
 const first=map.root.children[0].id;
 let r=mm.addChild(map,first,'새 업무');map=r.map;
 assert.equal(mm.findNode(map,first).node.children.length,3);
 r=mm.addSibling(map,first,'옆 가지');map=r.map;
 assert.equal(map.root.children[1].text,'옆 가지');
 map=mm.updateNode(map,r.id,{style:{shape:'cloud',fill:'#FDE047'}});
 map=mm.removeNode(map,map.root.children[2].id);
 const checked=mm.validateMindmap(JSON.parse(JSON.stringify(map)));
 const g=mm.mindmapGraph(checked);
 const count=n=>1+n.children.reduce((s,c)=>s+count(c),0);
 assert.equal(g.nodes.length,count(checked.root));
 const xs=g.nodes.map(n=>n.position.x);
 assert.ok(Math.min(...xs)<0&&Math.max(...xs)>0);              // 가운데 주제 좌우로 펼침
 assert.equal(g.edges.length,g.nodes.length-1);
 assert.ok(g.nodes.some(n=>n.data.shape==='cloud'&&n.data.fill==='#FDE047'));
 const down=mm.mindmapGraph({...checked,layout:'down'});
 assert.ok(down.nodes.every(n=>n.position.y>=0));
 const out=svg({format:FORMAT,version:1,nodes:[],edges:[],mindmap:checked}).source;
 assert.match(out,/2026 업무 계획/);
 assert.throws(()=>mm.validateMindmap({root:{id:'a',text:'x',children:[],style:{shape:'blob'}}}));
});

test('circle nodes stay square and wrap text inside, growing only when needed',()=>{
 const small=computeNodeAutoFitBox({data:{label:'축제',shape:'circle'},width:84,height:84});
 assert.equal(small.width,small.height);assert.equal(small.width,84);
 const long=computeNodeAutoFitBox({data:{label:'소상공인 컨설팅 지원 사업 확대',shape:'circle'},width:84,height:84});
 assert.equal(long.width,long.height);
 assert.ok(long.width>84);assert.ok(long.lines.length>=2);
});
