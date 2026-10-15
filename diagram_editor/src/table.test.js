import test from 'node:test';
import assert from 'node:assert/strict';
import {flowTable,resizeFlow,insertStep,removeStep,gridTable,resizeGrid,insertRow,removeRow,insertCol,removeCol,setStyle,validateTable,exportSpec,MAX_FLOW_STEPS} from './table.js';
import {validate,FORMAT,node,nodeTextStyle} from './model.js';

test('learned flow table: 2~6 presets keep typed steps and grow freely up to the limit',()=>{
 const five=flowTable(5);
 assert.equal(five.steps[0].title,'공고 및 접수');
 assert.equal(five.styles.step.fill,'#DFE6F7');
 for(const n of [2,3,4,5,6])assert.equal(resizeFlow(five,n).steps.length,n);
 const edited={...five,steps:five.steps.map((s,i)=>i===0?{...s,title:'바뀐 단계'}:s)};
 assert.equal(resizeFlow(resizeFlow(edited,2),6).steps[0].title,'바뀐 단계');
 assert.equal(resizeFlow(five,99).steps.length,MAX_FLOW_STEPS);
 assert.equal(insertStep(five,1).steps[1].title,'새 단계');
 assert.equal(removeStep(flowTable(2),0).steps.length,2);   // 2칸 아래로는 줄지 않는다
});
test('grid rows and columns grow and shrink in place without losing text',()=>{
 let g=gridTable(3,3);g={...g,rows:g.rows.map((r,i)=>r.map((v,j)=>i&&j?`${i}-${j}`:v))};
 assert.equal(resizeGrid(g,5,4).rows[2][2],'2-2');
 assert.deepEqual(insertRow(g,1).rows[1],['','','']);
 assert.equal(removeRow(g,0).rows[0][1],'1-1');
 assert.equal(insertCol(g,0).rows[1][1],'');
 assert.equal(removeCol(g,0).rows[1][0],'1-1');
 assert.equal(removeRow(gridTable(1,2),0).rows.length,1);
});
test('text styles are validated and only chosen grid roles are exported',()=>{
 const g=setStyle(gridTable(2,2),'head',{font:'HY견고딕',size:14,bold:true,color:'#FFFFFF',fill:'#1F4E79'});
 const spec=exportSpec(g);
 assert.deepEqual(Object.keys(spec.styles),['head']);
 assert.equal(spec.styles.head.font,'HY견고딕');
 assert.throws(()=>validateTable(setStyle(g,'body',{font:'x"<y'})));
 assert.equal(validateTable(setStyle(g,'body',{font:'한컴 윤고딕 230'})).styles.body.font,'한컴 윤고딕 230');   // 이 PC에서 찾은 글꼴 이름
 assert.throws(()=>validateTable(setStyle(g,'body',{size:99})));
 assert.throws(()=>validateTable(setStyle(g,'body',{color:'red'})));
});
test('diagram nodes keep optional font, size, bold and color; old documents stay valid',()=>{
 const a={...node('가',0,0),data:{...node('가',0,0).data,font:'휴먼명조',size:14,bold:true,textColor:'#1D4ED8'}};
 const doc=validate({format:FORMAT,version:1,nodes:[a],edges:[],table:flowTable(3)});
 assert.equal(doc.nodes[0].data.font,'휴먼명조');
 assert.equal(doc.table.steps.length,3);
 assert.deepEqual(nodeTextStyle(node('나',0,0).data),{});
 assert.throws(()=>validate({format:FORMAT,version:1,nodes:[{...a,data:{...a.data,size:'big'}}],edges:[]}));
});
test('flow grows downward, runs vertically, and borders follow hangul types',async()=>{
 const t=await import('./table.js');
 let f=t.resizeFlowRows(t.flowTable(3),3);
 assert.equal(f.steps[0].details.length,3);
 assert.equal(t.validateTable({...f,direction:'vertical',arrow:'▼'}).direction,'vertical');
 assert.throws(()=>t.validateTable({...f,direction:'vertical',arrow:'➜'}));
 f=t.setBorder(f,'line',{type:'DASH_DOT',width:'0.5 mm'});
 assert.equal(t.validateTable(f).borders.line.type,'DASH_DOT');
 assert.throws(()=>t.validateTable(t.setBorder(f,'line',{type:'WAVY'})));
 assert.match(t.cssBorder({type:'NONE',width:'0.1 mm',color:'#000000'}),/dotted/);   // 투명선은 안내선
 assert.match(t.cssBorder({type:'DOUBLE_SLIM',width:'0.5 mm',color:'#000000'}),/double/);
 // 예전 흐름표(date 하나)도 읽는다
 assert.deepEqual(t.flowDetails({title:'가',date:'1월'},2),['1월','']);
});
test('org chart and decorative bar tables validate and export',async()=>{
 const t=await import('./table.js');
 const org=t.resizeOrg(t.orgTable(4),6);
 assert.equal(org.units.length,6);
 assert.equal(t.exportSpec(org).kind,'org');
 assert.throws(()=>t.validateTable(t.resizeOrg(t.orgTable(1),0)&&{...org,units:[]}));
 const bar=t.barTable();
 assert.equal(t.exportSpec(bar).title,'2026 추진실적');
 const grid=t.setBorder(t.gridTable(2,2),'outer',{type:'DOUBLE_SLIM'});
 assert.equal(t.exportSpec(grid).borders.outer.type,'DOUBLE_SLIM');           // 직접 고른 테두리만 보낸다
 assert.equal(t.exportSpec(t.gridTable(2,2)).borders,undefined);
});
