import 'package:docfit_ui/features/settings/idiom_panel.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

Map<String, Object?> _ok(Map data) => {
  'api_version': 1,
  'ok': true,
  'data': data,
  'error': null,
};

void main() {
  testWidgets('글자 상용구를 추가하면 전체 목록을 바로 저장한다', (tester) async {
    tester.view.physicalSize = const Size(1000, 900);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);
    final calls = <List<Object?>>[];
    var text = [
      {'key': 'ㅁ', 'value': '□', 'attr': 0},
      {'key': 'ㅇ123', 'value': '①②③', 'attr': 22},
    ];
    Future<Object?> api(String method, List<Object?> args) async {
      calls.add([method, ...args]);
      if (args.first == 'save_text') {
        text = [
          for (final e in ((args[1] as Map)['entries'] as List))
            Map<String, Object>.from(e as Map),
        ];
      }
      return _ok({
        'available': true,
        'folder': r'C:\Hwp\60',
        'text': text,
        'body': [],
      });
    }

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(body: IdiomPanel(api: api, body: false, locked: false)),
      ),
    );
    await tester.pumpAndSettle();
    expect(find.text('①②③'), findsOneWidget);
    await tester.enterText(find.byKey(const Key('idiom-key-false')), 'ㅁㅂ');
    await tester.enterText(find.byKey(const Key('idiom-value-false')), '마포구');
    await tester.tap(find.text('추가'));
    await tester.pumpAndSettle();
    final saved = calls.lastWhere((c) => c[1] == 'save_text');
    final entries = (saved[2] as Map)['entries'] as List;
    expect(entries.length, 3);
    expect((entries[1] as Map)['attr'], 22); // 한/글이 쓰는 속성 값은 그대로
    expect((entries.last as Map)['value'], '마포구');
    expect(find.text('마포구'), findsOneWidget);
    expect(find.text('글자 상용구 ‘ㅁㅂ’를 추가했어요.'), findsOneWidget);
  });

  testWidgets('본문 상용구는 문서 없음과 한/글에서 열기를 보여 준다', (tester) async {
    tester.view.physicalSize = const Size(1000, 900);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);
    Future<Object?> api(String method, List<Object?> args) async => _ok({
      'available': true,
      'text': [],
      'body': [
        {'key': '표', 'title': '표서식', 'attr': 1, 'has_file': true},
        {'key': '보고', 'title': '보고서', 'attr': 1, 'has_file': false},
      ],
    });
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(body: IdiomPanel(api: api, body: true, locked: false)),
      ),
    );
    await tester.pumpAndSettle();
    expect(find.text('표서식'), findsOneWidget);
    expect(find.text('문서 없음'), findsOneWidget);
    expect(find.byTooltip('한/글에서 열기'), findsNWidgets(2));
    expect(find.text('문서 골라 추가'), findsOneWidget);
  });

  testWidgets('앱 정보에 개발자를 보여 준다', (tester) async {
    await tester.pumpWidget(
      const MaterialApp(
        home: Scaffold(body: AppInfoPanel(version: '1.75 Alpha')),
      ),
    );
    expect(find.text('도토리만두'), findsOneWidget);
    expect(find.text('1.75 Alpha'), findsOneWidget);
  });
}
