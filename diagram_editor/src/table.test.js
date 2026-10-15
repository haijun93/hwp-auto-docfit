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
 assert.throws(()=>validateTable(setStyle(g,'body',{font:'<script>'})));
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
