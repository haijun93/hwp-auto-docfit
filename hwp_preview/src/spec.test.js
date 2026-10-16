import test from 'node:test';
import assert from 'node:assert/strict';
import {plan,charProps,normalizeChar} from './spec.js';

const measure=(font,text)=>text.length*10;   // 시험용 폭: 글자당 10px

test('항목기호 문단은 한/글 단위(pt×100, 내어쓰기 pt×200)로 명령이 된다',()=>{
 const ops=plan({paragraphs:[{marker:'ㅇ',indent:1,text:'추진 배경 : 내용',label:'추진 배경 :',
  char:{font:'한컴돋움',size:15,spacing:-5,ratio:95},markerChar:{bold:true},para:{line:160,before:8,align:'양쪽'}}]},measure);
 const para=ops.find(o=>o.op==='para');
 assert.equal(para.text,' ㅇ 추진 배경 : 내용');
 assert.deepEqual(para.runs.map(r=>[r.start,r.end]),[[0,3],[3,10],[10,13]]);
 assert.equal(para.runs[0].props.bold,true);          // 항목기호 굵게
 assert.equal(para.runs[1].props.bold,true);          // 라벨 굵게
 assert.equal(para.runs[2].props.bold,false);
 assert.equal(para.runs[2].props.fontSize,1500);
 assert.deepEqual(para.runs[2].props.spacings,[-5,-5,-5,-5,-5,-5,-5]);
 assert.equal(para.props.spacingBefore,800);
 assert.equal(para.props.lineSpacing,160);
 assert.equal(para.props.alignment,'justify');
 assert.equal(para.props.indent,-Math.round(30*0.75*200)); // 앞 칸+기호+빈칸 3글자 폭 30px
 assert.equal(para.props.koreanBreakUnit,0);               // 어절 단위 줄 나눔
});
test('세부 작업 미리보기는 글자 단위 줄 나눔도 그린다',()=>{
 const ops=plan({paragraphs:[{text:'가나다',para:{breakUnit:'char'}}]},measure);
 assert.equal(ops[1].props.koreanBreakUnit,1);
});
test('여백은 HWPUNIT, 값은 범위를 벗어나지 않는다',()=>{
 const ops=plan({page:{left:20,right:20,top:12.7,bottom:12.7},paragraphs:[{text:'가',char:{size:999,font:'bad"font',color:'red'}}]},measure);
 assert.equal(ops[0].def.marginLeft,Math.round(20*7200/25.4));
 const run=ops[1].runs[0].props;
 assert.equal(run.fontSize,4000);
 assert.equal(run.fontName,'한컴돋움');
 assert.equal(run.textColor,'#000000');
});
test('표는 머리글·본문 글자 모양과 머리글 바탕을 따로 준다',()=>{
 const ops=plan({paragraphs:[],table:{rows:[['구분','1안'],['운영비']],header:{font:'한컴돋움',size:13,bold:true,fill:'#EEF1F5'},body:{font:'휴먼명조',size:12}}},measure);
 const t=ops.find(o=>o.op==='table');
 assert.deepEqual(t.rows,[['구분','1안'],['운영비','']]);
 assert.equal(t.header.bold,true);
 assert.equal(t.fill,'#EEF1F5');
 assert.equal(t.body.fontName,'휴먼명조');
});
test('입력 한도와 기본값',()=>{
 assert.throws(()=>plan(null,measure));
 const many=plan({paragraphs:Array(50).fill({text:'가'})},measure).filter(o=>o.op==='para');
 assert.equal(many.length,30);
 assert.deepEqual(normalizeChar({}),{font:'한컴돋움',size:13,bold:false,spacing:0,ratio:100,color:'#000000'});
 assert.equal(charProps(normalizeChar({size:12.5})).fontSize,1250);
});
test('설치된 한/글 글꼴 이름도 쓰고, 명세에서 쓰는 글꼴을 모은다',async()=>{
 const {fontsOf}=await import('./spec.js');
 const ops=plan({paragraphs:[{text:'가',char:{font:'한컴 윤고딕 230'}},{text:'나',char:{font:'x"<script>'}}]},measure);
 assert.equal(ops[1].runs[0].props.fontName,'한컴 윤고딕 230');
 assert.equal(ops[2].runs[0].props.fontName,'한컴돋움');     // 이상한 이름은 기본 글꼴
 assert.deepEqual(fontsOf({paragraphs:[{char:{font:'휴먼명조'},markerChar:{font:'HY견고딕'}}],table:{header:{font:'한컴돋움'}}}).sort(),['HY견고딕','한컴돋움','휴먼명조'].sort());
});
