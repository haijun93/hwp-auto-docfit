import 'package:docfit_ui/features/preview/typeset_spec.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('설정 값이 조판 명세로 가고, 바꾼 설정이 닿는 문단만 강조한다', () {
    final values = <String, Object?>{
      'symbol_fonts.ㅇ.font': '휴먼명조',
      'symbol_fonts.ㅇ.size': '16',
      'std_parspace_circle': '10',
      'std_symbol_o_bold': true,
      'table_fonts.header.size': '14',
    };
    final spec = settingsSpec(
      (k) => values[k],
      focusKey: 'symbol_fonts.ㅇ.size',
    );
    final paras = spec['paragraphs'] as List;
    final circle = paras.cast<Map>().firstWhere((p) => p['marker'] == 'ㅇ');
    expect((circle['char'] as Map)['font'], '휴먼명조');
    expect((circle['char'] as Map)['size'], 16);
    expect((circle['char'] as Map)['bold'], true);
    expect((circle['para'] as Map)['before'], 10);
    expect(circle['focus'], true);
    expect(paras.cast<Map>().where((p) => p['focus'] == true).length, 1);
    final box = paras.cast<Map>().firstWhere((p) => p['marker'] == '□');
    expect((box['char'] as Map)['font'], 'HY견고딕'); // 값이 없으면 표준 서식 기본값
    expect(((spec['table'] as Map)['header'] as Map)['size'], 14);
    expect(focusOf('table_fonts.body.font'), 'table');
    expect(focusOf('std_parspace_dash'), '-');
    expect(focusOf('label_symbols.※'), '※');
  });

  test('서식 요소 값(15pt·-5%·예·왼쪽)이 조판 명세가 된다', () {
    final spec = elementSpec(
      ['body', 'circle'],
      'ㅇ 항목',
      {
        'font': '한컴돋움',
        'size': '15pt',
        'spacing': '-5%',
        'ratio': '95%',
        'bold': '예',
        'prev': '8pt',
        'align': '왼쪽',
        'line': '170',
      },
    )!;
    final para = (spec['paragraphs'] as List).last as Map;
    expect(para['marker'], 'ㅇ');
    expect(para['indent'], 1);
    expect((para['char'] as Map)['spacing'], -5);
    expect((para['char'] as Map)['ratio'], 95);
    expect((para['para'] as Map)['line'], 170);
    expect((para['para'] as Map)['align'], '왼쪽');
    expect(elementSpec(['page'], '쪽', {}), isNull);
    final table = elementSpec(['table', 'header'], '표 머리글', {'size': '14pt'})!;
    expect(((table['table'] as Map)['header'] as Map)['size'], 14);
  });

  test('stage spec shows each stage before and after', () {
    Map para(String key, bool applied, [int at = 0]) =>
        (stageSpec(key, applied: applied)!['paragraphs'] as List)[at] as Map;
    // 자간: 전에는 글자 단위로 갈라지고, 뒤에는 어절 단위 + 자간 조정.
    expect((para('body_spacing', false)['para'] as Map)['breakUnit'], 'char');
    expect((para('body_spacing', true)['para'] as Map)['breakUnit'], isNull);
    expect(para('body_spacing', true)['focus'], isTrue);
    // 서식통일: 다른 글꼴 한 문단만 다수 서식으로 맞춘다.
    expect((para('style_unify', false, 1)['char'] as Map)['font'], '굴림');
    expect((para('style_unify', true, 1)['char'] as Map)['font'], '한컴돋움');
    // 쪽 맞춤 마지막 수단: 줄 간격 최솟값 140%.
    expect((para('page_fit', true, 1)['para'] as Map)['line'], 140);
    expect(para('hanging_indent', false)['hanging'], isFalse);
    final table = stageSpec('table_style', applied: true)!['table'] as Map;
    expect((table['header'] as Map)['fill'], '#EEF1F5');
    expect(stageSpec('asterisk_superscript', applied: true), isNull);
  });
}
