import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:docfit_ui/features/formats/profile_editor.dart';

Map<String, Object?> profile() => {
  'id': 'p1',
  'name': '마포 보고서',
  'revision': 'r1',
  'coverage': {'total': 2, 'applied': 2},
  'nodes': [
    {
      'path': ['page'],
      'label': '쪽 모양·여백',
      'fields': [
        {
          'key': 'page_left',
          'label': '쪽 왼쪽 여백',
          'value': '20mm',
          'editable': true,
          'choices': [],
        },
      ],
    },
    {
      'path': ['group', 1],
      'label': 'ㅇ 본문 · 7문장',
      'fields': [
        {
          'key': 'size',
          'label': '글자 크기',
          'value': '14pt',
          'editable': true,
          'choices': [],
        },
        {
          'key': 'marker_bold',
          'label': '항목기호 굵게',
          'value': '아니오',
          'editable': true,
          'choices': ['예', '아니오'],
        },
        {
          'key': 'align',
          'label': '정렬',
          'value': '왼쪽',
          'editable': true,
          'choices': ['왼쪽', '가운데', '양쪽'],
        },
      ],
    },
  ],
};

void main() {
  testWidgets('element preview, friendly controls and saving edits', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(1280, 900);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);
    final calls = <List<Object?>>[];
    Future<Object?> api(String method, List<Object?> args) async {
      calls.add(args);
      return {'ok': true, 'data': profile()};
    }

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: ProfileEditor(api: api, identifier: 'p1'),
        ),
      ),
    );
    await tester.pumpAndSettle();
    expect(find.text('글이 들어가는 곳'), findsOneWidget); // 쪽 여백 미리보기
    await tester.tap(find.byKey(const ValueKey('element-1')));
    await tester.pumpAndSettle();
    expect(find.text('문서에서 이렇게 보여요. 아래 값을 바꾸면 바로 반영돼요.'), findsOneWidget);
    expect(find.textContaining('14pt'), findsWidgets);
    tester.widget<Switch>(find.byType(Switch)).onChanged!(true);
    await tester.pumpAndSettle();
    expect(tester.widget<Switch>(find.byType(Switch)).value, isTrue);
    await tester.ensureVisible(find.text('가운데'));
    await tester.tap(find.text('가운데'));
    await tester.pumpAndSettle();
    expect(find.text('바꾼 값 2개'), findsOneWidget);
    await tester.tap(find.text('저장·적용'));
    await tester.pumpAndSettle();
    final saved = calls.last;
    expect(saved.first, 'save');
    final edits = (saved[1] as Map)['edits'] as List;
    expect(edits.map((e) => '${(e as Map)['key']}=${e['value']}').toSet(), {
      'marker_bold=예',
      'align=가운데',
    });
  });
  testWidgets('edited text, preview and save survive element navigation', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(1280, 900);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);
    final calls = <List<Object?>>[];
    Future<Object?> api(String method, List<Object?> args) async {
      calls.add(args);
      return {'ok': true, 'data': profile()};
    }

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: ProfileEditor(api: api, identifier: 'p1'),
        ),
      ),
    );
    await tester.pumpAndSettle();
    await tester.enterText(find.byType(TextFormField), '25mm');
    await tester.pump();
    await tester.tap(find.byKey(const ValueKey('element-1')));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const ValueKey('element-0')));
    await tester.pumpAndSettle();
    expect(
      tester.widget<TextFormField>(find.byType(TextFormField)).initialValue,
      '25mm',
    );
    expect(find.textContaining('왼쪽 25mm'), findsOneWidget);
    await tester.tap(find.text('저장·적용'));
    await tester.pumpAndSettle();
    final payload = calls.last[1] as Map;
    expect((payload['edits'] as List).single['value'], '25mm');
  });
}
