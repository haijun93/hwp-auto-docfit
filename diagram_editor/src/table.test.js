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
test('catalog table free editing: structure, cell text, styles, and borders export cleanly',async()=>{
 const t=await import('./table.js');
 const tpl={
  id:'1:1',rows:2,cols:2,
  cells:[['제목','설명'],['항목','내용']],
  cell_meta:[
   [{text:'제목',colAddr:0,rowAddr:0,colSpan:1,rowSpan:1,align:'CENTER',style:{font:'맑은 고딕',size:11,bold:true,color:'#000000',fill:'#DFE6F7'},borders:{top:{type:'SOLID',width:'0.4 mm',color:'#000000'},bottom:{type:'SOLID',width:'0.12 mm',color:'#000000'},left:{type:'NONE',width:'0.12 mm',color:'#000000'},right:{type:'SOLID',width:'0.12 mm',color:'#000000'}}},
    {text:'설명',colAddr:1,rowAddr:0,colSpan:1,rowSpan:1,align:'LEFT',style:{font:'맑은 고딕',size:10,bold:false,color:'#000000',fill:'transparent'},borders:{top:{type:'SOLID',width:'0.4 mm',color:'#000000'},bottom:{type:'SOLID',width:'0.12 mm',color:'#000000'},left:{type:'SOLID',width:'0.12 mm',color:'#000000'},right:{type:'NONE',width:'0.12 mm',color:'#000000'}}}],
   [{text:'항목',colAddr:0,rowAddr:1,colSpan:1,rowSpan:1,align:'CENTER',style:{font:'맑은 고딕',size:10,bold:false,color:'#000000',fill:'transparent'},borders:{top:{type:'SOLID',width:'0.12 mm',color:'#000000'},bottom:{type:'SOLID',width:'0.4 mm',color:'#000000'},left:{type:'NONE',width:'0.12 mm',color:'#000000'},right:{type:'SOLID',width:'0.12 mm',color:'#000000'}}},
    {text:'내용',colAddr:1,rowAddr:1,colSpan:1,rowSpan:1,align:'LEFT',style:{font:'맑은 고딕',size:10,bold:false,color:'#000000',fill:'transparent'},borders:{top:{type:'SOLID',width:'0.12 mm',color:'#000000'},bottom:{type:'SOLID',width:'0.4 mm',color:'#000000'},left:{type:'SOLID',width:'0.12 mm',color:'#000000'},right:{type:'NONE',width:'0.12 mm',color:'#000000'}}}]
  ]
 };
 let grid=t.buildCatalogGrid(tpl),ops=[];
 assert.equal(grid.length,2);
 assert.equal(grid[0].length,2);
 ({grid,ops}=t.applyCatalogStructure(grid,ops,{op:'insert_row',index:1}));
 assert.equal(grid.length,3);
 ({grid,ops}=t.applyCatalogStructure(grid,ops,{op:'insert_column',index:1}));
 assert.equal(grid[0].length,3);
 grid=t.setCatalogCellText(grid,1,1,'중간 삽입 칸');
 grid=t.setCatalogStyle(grid,'cell',{r:0,c:0},{font:'HY견고딕',size:14,bold:true,color:'#FFFFFF',fill:'#1F4E79'});
 grid=t.setCatalogBorder(grid,'all',{r:0,c:0},'outer',{type:'DOUBLE_SLIM',width:'0.5 mm',color:'#1F4E79'});
 const edits=t.buildCatalogEdits(grid);
 assert.equal(edits.cell_edits['1:1'],'중간 삽입 칸');
 assert.equal(edits.style_edits['0:0'].font,'HY견고딕');
 assert.equal(edits.style_edits['0:0'].fill,'#1F4E79');
 assert.equal(edits.style_edits['0:0'].borders.top.type,'DOUBLE_SLIM');
 assert.equal(edits.style_edits['2:2'].borders.bottom.type,'DOUBLE_SLIM');
});

test('task table (0:1 분야별과제표) steps resizing (2~6 steps) preserves width and sets ops',async()=>{
 const t=await import('./table.js');
 assert.equal(t.isTaskTable('0:1','분야별과제표'),true);
 assert.equal(t.isTaskTable('1:1','추진일정'),false);
 assert.equal(t.isFixedCalloutCategory('부연설명','2:1'),true);
 assert.equal(t.isFixedCalloutCategory('라벨 서식','3:1'),true);
 assert.equal(t.isFixedCalloutCategory('분야별과제표','0:1'),false);

 // Mock 0:1 3-row grid (3 original steps)
 const makeCell=(r,c,w,txt)=>({row:r,col:c,colSpan:1,rowSpan:1,width:w,text:txt,origText:txt,style:{},borders:{}});
 const row0=[
  makeCell(0,0,1415,''),makeCell(0,1,12232,'과제1'),makeCell(0,2,1415,''),makeCell(0,3,566,''),
  makeCell(0,4,1415,''),makeCell(0,5,12232,'과제2'),makeCell(0,6,1415,''),makeCell(0,7,566,''),
  makeCell(0,8,1415,''),makeCell(0,9,12232,'과제3'),makeCell(0,10,1415,''),makeCell(0,11,283,'')
 ];
 const row1=[
  makeCell(1,0,1415,''),makeCell(1,2,1415,''),makeCell(1,3,566,''),
  makeCell(1,4,1415,''),makeCell(1,6,1415,''),makeCell(1,7,566,''),
  makeCell(1,8,1415,''),makeCell(1,10,1415,''),makeCell(1,11,283,'')
 ];
 const row2=[
  {...makeCell(2,0,15062,'• 과제1 세부'),colSpan:3},makeCell(2,3,566,''),
  {...makeCell(2,4,15062,'• 과제2 세부'),colSpan:3},makeCell(2,7,566,''),
  {...makeCell(2,8,15062,'• 과제3 세부'),colSpan:3},makeCell(2,11,283,'')
 ];
 const originalGrid=[row0,row1,row2];

 // Test resize to 4 steps
 const res4=t.resizeTaskGrid(originalGrid,4);
 assert.equal(res4.grid[0].length,16); // 4 steps * 4 cols
 assert.equal(res4.grid[1].length,12); // 4 steps * 3 cols
 assert.equal(res4.grid[2].length,8);  // 4 steps * 2 cols
 assert.deepEqual(res4.ops,[{op:'resize_steps',steps:4}]);
 assert.equal(res4.grid[0][1].text,'과제1');
 assert.equal(res4.grid[0][13].text,'과제 4');
 assert.equal(res4.grid[2][6].text,'• 과제 4 세부내용');

 // Test total width of row 0 is 46601
 const totalW=res4.grid[0].reduce((sum,c)=>sum+c.width,0);
 assert.equal(totalW,46601);

 // Test resize to 2 steps
 const res2=t.resizeTaskGrid(originalGrid,2);
 assert.equal(res2.grid[0].length,8);
 assert.equal(res2.grid[0][1].text,'과제1');
 assert.equal(res2.grid[0][5].text,'과제2');
 const totalW2=res2.grid[0].reduce((sum,c)=>sum+c.width,0);
 assert.equal(totalW2,46601);
});
