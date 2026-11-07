// 몽땅클립보드 분류 규칙: 빠른 목록(Rust kagent/src/category.rs)과 관리창(Dart)이
// 같은 규칙 표·사례(tests/fixtures/kclip_category_rules.json)로 같은 결과를 내는지 확인한다.
import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:docfit_ui/features/kclip/kclip_category.dart';
import 'package:docfit_ui/features/kclip/kclip_dialog.dart';

Map<String, dynamic> _rules() {
  final file = File('../tests/fixtures/kclip_category_rules.json');
  return jsonDecode(file.readAsStringSync()) as Map<String, dynamic>;
}

List<String> _strings(Object? v) => v == null ? const [] : [for (final x in v as List) x as String];

void main() {
  test('규칙 표가 공통 JSON과 같다', () {
    final r = _rules();
    expect(kclipCategories, _strings(r['labels']));
    expect(kclipSearchLabel, r['search_label']);
    expect(kclipDocExts, _strings(r['doc_exts']));
    expect(kclipImageExts, _strings(r['image_exts']));
    expect(kclipDocPrograms, _strings(r['doc_programs']));
    expect(kclipBrowsers, _strings(r['browsers']));
    expect(kclipDocFormats, _strings(r['doc_formats']));
  });

  test('공통 사례를 Rust와 같게 분류한다', () {
    final cases = _rules()['cases'] as List;
    expect(cases.length, greaterThanOrEqualTo(30));
    for (final c in cases.cast<Map<String, dynamic>>()) {
      final e = c['entry'] as Map<String, dynamic>;
      final entry = KClipEntry(
        kind: '${e['kind'] ?? ''}',
        preview: '${e['preview'] ?? ''}',
        source: '${e['source'] ?? ''}',
        formats: _strings(e['formats']),
        paths: _strings(e['paths']),
        webUrl: e['web_url'] as String?,
        text: '${e['text'] ?? ''}',
      );
      final known = (c['is_dir'] as Map?)?.cast<String, bool>() ?? const <String, bool>{};
      expect(kclipClassify(entry, isDir: (p) => known[p]), _strings(c['expect']), reason: '사례: ${c['name']}');
    }
  });

  test('에이전트 목록 항목(미리보기만 있음)에서도 분류한다', () {
    bool inCat(Map item, String c) => kclipItemIn(item, c);
    final doc = {'id': 1, 'kind': 'files', 'preview': '파일 2개: 보고서.hwpx, 사진.png'};
    expect(inCat(doc, '문서'), isTrue);
    expect(inCat(doc, '그림'), isTrue);
    expect(inCat(doc, '파일'), isTrue);
    expect(inCat(doc, '폴더'), isFalse);
    final many = {'id': 2, 'kind': 'files', 'preview': '파일 5개: 자료, a.txt, b.txt …'};
    expect(inCat(many, '폴더'), isTrue);
    expect(inCat(many, '문서'), isTrue);
    final forcedFolder = {'id': 3, 'kind': 'files', 'preview': '파일 1개: v1.2', 'is_folder': true};
    expect(inCat(forcedFolder, '폴더'), isTrue);
    expect(inCat(forcedFolder, '파일'), isFalse);
    final url = {'id': 4, 'kind': 'text', 'preview': 'https://example.com/a'};
    expect(inCat(url, '웹'), isTrue);
    expect(inCat(url, '파일'), isFalse);
    final cap = {'id': 5, 'kind': 'image', 'preview': '캡처 · 그림 10×10'};
    expect(inCat(cap, '화면캡처'), isTrue);
    expect(inCat(cap, '그림'), isTrue);
    // 에이전트가 출처·서식 칸을 주면 문서 글도 판별한다.
    expect(inCat({'id': 6, 'kind': 'text', 'preview': 'x', 'source': 'hwp.exe'}, '문서'), isTrue);
    expect(inCat({'id': 7, 'kind': 'text', 'preview': 'x'}, '문서'), isFalse);
  });

  testWidgets('관리창 분류 단추가 빠른 목록 기준으로 항목을 거른다', (tester) async {
    Future<Object?> api(String method, List<Object?> args) async {
      if (method != 'kclip') return {'ok': true};
      switch (args[0]) {
        case 'status':
          return {'ok': true, 'running': true, 'available': true, 'status': {}};
        case 'list':
          return {
            'ok': true,
            'items': [
              {'id': 1, 'kind': 'text', 'preview': '일반 글', 'pinned': false},
              {'id': 2, 'kind': 'files', 'preview': '파일 1개: 보고서.hwpx', 'pinned': false},
              {'id': 3, 'kind': 'files', 'preview': '파일 1개: 자료', 'pinned': false},
              {'id': 4, 'kind': 'image', 'preview': '캡처 · 그림 1×1', 'pinned': false},
              {'id': 5, 'kind': 'text', 'preview': '본문 · 웹 · a.com', 'pinned': false},
            ],
          };
        case 'settings_get':
          return {'ok': true, 'settings': {}};
        case 'image':
          return {'ok': false};
      }
      return {'ok': true};
    }

    await tester.pumpWidget(MaterialApp(home: Scaffold(body: SizedBox(width: 900, height: 900, child: KClipPanel(api: api)))));
    await tester.pumpAndSettle();
    Set<int> shown() => {
          for (var id = 1; id <= 5; id++)
            if (find.byKey(ValueKey('kclip-item-$id')).evaluate().isNotEmpty) id,
        };
    expect(shown(), {1, 2, 3, 4, 5});
    final expected = {
      '문서': {2},
      '그림': {4},
      '파일': {2},
      '폴더': {3},
      '웹': {5},
      '화면캡처': {4},
      '전체': {1, 2, 3, 4, 5},
    };
    for (final MapEntry(key: c, value: ids) in expected.entries) {
      await tester.tap(find.byKey(ValueKey('kclip-category-$c')));
      await tester.pumpAndSettle();
      expect(shown(), ids, reason: '분류: $c');
    }
    expect(find.byKey(const ValueKey('kclip-category-글')), findsNothing);
  });
}
