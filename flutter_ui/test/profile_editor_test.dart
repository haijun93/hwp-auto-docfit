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

Map<String, Object?> fullPageProfile() => {
  'id': 'p2',
  'name': '마포 보고서 2',
  'revision': 'r2',
  'coverage': {'total': 10, 'applied': 10},
  'nodes': [
    {
      'path': ['page'],
      'label': '쪽 모양·여백',
      'fields': [
        {
          'key': 'page_width',
          'label': '용지 폭',
          'value': '210.0mm',
          'editable': false,
          'choices': [],
        },
        {
          'key': 'page_height',
          'label': '용지 길이',
          'value': '297.0mm',
          'editable': false,
          'choices': [],
        },
        {
          'key': 'page_landscape',
          'label': '용지 방향',
          'value': '아니오',
          'editable': false,
          'choices': ['예', '아니오'],
        },
        {
          'key': 'page_top',
          'label': '위쪽',
          'value': '15.0mm',
          'editable': true,
          'choices': [],
        },
        {
          'key': 'page_header',
          'label': '머리말',
          'value': '10.0mm',
          'editable': true,
          'choices': [],
        },
        {
          'key': 'page_left',
          'label': '왼쪽',
          'value': '20.0mm',
          'editable': true,
          'choices': [],
        },
        {
          'key': 'page_gutter',
          'label': '제본',
          'value': '0.0mm',
          'editable': true,
          'choices': [],
        },
        {
          'key': 'page_right',
          'label': '오른쪽',
          'value': '20.0mm',
          'editable': true,
          'choices': [],
        },
        {
          'key': 'page_footer',
          'label': '꼬리말',
          'value': '10.0mm',
          'editable': true,
          'choices': [],
        },
        {
          'key': 'page_bottom',
          'label': '아래쪽',
          'value': '15.0mm',
          'editable': true,
          'choices': [],
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

  testWidgets(
    'PageMarginLayout displays 7 margin fields, handles spin buttons & text edits, and keeps paper size read-only',
    (tester) async {
      tester.view.physicalSize = const Size(1280, 900);
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.reset);
      final calls = <List<Object?>>[];
      Future<Object?> api(String method, List<Object?> args) async {
        calls.add(args);
        return {'ok': true, 'data': fullPageProfile()};
      }

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: ProfileEditor(api: api, identifier: 'p2'),
          ),
        ),
      );
      await tester.pumpAndSettle();

      // '쪽 모양·여백'을 고르면 PageMarginLayout과 종이 그림이 보임
      expect(find.byKey(const Key('pageMarginLayout')), findsOneWidget);
      expect(find.byKey(const Key('pageMarginPaper')), findsOneWidget);

      // 7개 칸이 모두 보이고
      const marginKeys = [
        'page_top',
        'page_header',
        'page_left',
        'page_gutter',
        'page_right',
        'page_footer',
        'page_bottom',
      ];
      for (final key in marginKeys) {
        expect(find.byKey(Key('pageMargin_$key')), findsOneWidget);
      }

      // 7개 칸의 값이 맞는지
      expect(
        tester
            .widget<TextFormField>(
              find.descendant(
                of: find.byKey(const Key('pageMargin_page_top')),
                matching: find.byType(TextFormField),
              ),
            )
            .initialValue,
        '15.0mm',
      );
      expect(
        tester
            .widget<TextFormField>(
              find.descendant(
                of: find.byKey(const Key('pageMargin_page_header')),
                matching: find.byType(TextFormField),
              ),
            )
            .initialValue,
        '10.0mm',
      );
      expect(
        tester
            .widget<TextFormField>(
              find.descendant(
                of: find.byKey(const Key('pageMargin_page_left')),
                matching: find.byType(TextFormField),
              ),
            )
            .initialValue,
        '20.0mm',
      );
      expect(
        tester
            .widget<TextFormField>(
              find.descendant(
                of: find.byKey(const Key('pageMargin_page_gutter')),
                matching: find.byType(TextFormField),
              ),
            )
            .initialValue,
        '0.0mm',
      );
      expect(
        tester
            .widget<TextFormField>(
              find.descendant(
                of: find.byKey(const Key('pageMargin_page_right')),
                matching: find.byType(TextFormField),
              ),
            )
            .initialValue,
        '20.0mm',
      );
      expect(
        tester
            .widget<TextFormField>(
              find.descendant(
                of: find.byKey(const Key('pageMargin_page_footer')),
                matching: find.byType(TextFormField),
              ),
            )
            .initialValue,
        '10.0mm',
      );
      expect(
        tester
            .widget<TextFormField>(
              find.descendant(
                of: find.byKey(const Key('pageMargin_page_bottom')),
                matching: find.byType(TextFormField),
              ),
            )
            .initialValue,
        '15.0mm',
      );

      // 폭·길이·방향은 고칠 수 없는지 (읽기 전용)
      expect(find.textContaining('폭 210.0 mm · 길이 297.0 mm'), findsOneWidget);
      expect(find.text('세로'), findsOneWidget);
      expect(find.text('가로'), findsOneWidget);
      expect(find.byKey(const Key('pageMargin_page_width')), findsNothing);
      expect(find.byKey(const Key('pageMargin_page_height')), findsNothing);
      expect(find.byKey(const Key('pageMargin_page_landscape')), findsNothing);

      // 증감 버튼을 누르면: page_top Up -> 15.1mm, page_bottom Down -> 14.9mm
      await tester.tap(find.byKey(const Key('pageMarginUp_page_top')));
      await tester.pumpAndSettle();
      await tester.ensureVisible(find.byKey(const Key('pageMarginDown_page_bottom')));
      await tester.pumpAndSettle();
      await tester.tap(find.byKey(const Key('pageMarginDown_page_bottom')));
      await tester.pumpAndSettle();

      // 칸 값을 바꾸면: page_left에 '25.0mm' 입력
      await tester.enterText(
        find.descendant(
          of: find.byKey(const Key('pageMargin_page_left')),
          matching: find.byType(TextFormField),
        ),
        '25.0mm',
      );
      await tester.pumpAndSettle();

      // 저장 요청 edits에 path ['page'], key, 새 값이 들어가는지
      await tester.tap(find.text('저장·적용'));
      await tester.pumpAndSettle();

      final saved = calls.last;
      expect(saved.first, 'save');
      final edits = (saved[1] as Map)['edits'] as List;
      final editsMap = {
        for (final e in edits) (e as Map)['key']: e['value'],
      };
      expect(editsMap['page_top'], '15.1mm');
      expect(editsMap['page_bottom'], '14.9mm');
      expect(editsMap['page_left'], '25.0mm');
      for (final e in edits) {
        expect((e as Map)['path'], ['page']);
      }
    },
  );

  testWidgets('PageMarginLayout does not overflow at width 420', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(420, 800);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);
    Future<Object?> api(String method, List<Object?> args) async {
      return {'ok': true, 'data': fullPageProfile()};
    }

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: ProfileEditor(api: api, identifier: 'p2'),
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('pageMarginLayout')), findsOneWidget);
    expect(find.byKey(const Key('pageMarginPaper')), findsOneWidget);
    expect(tester.takeException(), isNull);
  });
}
