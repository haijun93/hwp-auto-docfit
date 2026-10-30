import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:docfit_ui/features/settings/settings_dialog.dart';

Map<String, Object?> data() => {
  'revision': 'r1',
  'running': false,
  'fields': [
    {
      'key': 'retry_body',
      'label': '본문 재시도 횟수',
      'type': 'number',
      'default': '15',
    },
    {
      'key': 'developer_mode',
      'label': '개발자 모드',
      'type': 'boolean',
      'default': false,
    },
  ],
  'values': {'retry_body': '7', 'developer_mode': false},
};
void main() {
  mainGuided();
  testWidgets('applies only changed settings with revision', (tester) async {
    List<Object?>? saved;
    Future<Object?> api(String method, List<Object?> args) async {
      if (method == 'save_settings') saved = args;
      return {'api_version': 1, 'ok': true, 'data': data(), 'error': null};
    }

    await tester.pumpWidget(
      MaterialApp(
        home: Builder(
          builder: (context) => Scaffold(
            body: TextButton(
              onPressed: () => showDialog<void>(
                context: context,
                builder: (_) => SettingsDialog(api: api),
              ),
              child: const Text('열기'),
            ),
          ),
        ),
      ),
    );
    await tester.tap(find.text('열기'));
    await tester.pumpAndSettle();
    await tester.enterText(find.byKey(const ValueKey('retry_body')), '9');
    await tester.pump();
    await tester.tap(find.text('변경사항 적용'));
    await tester.pumpAndSettle();
    expect(saved, [
      {'retry_body': '9'},
      'r1',
    ]);
  });
  testWidgets('save error preserves draft and cancel remains available', (
    tester,
  ) async {
    Future<Object?> api(String method, List<Object?> args) async =>
        method == 'save_settings'
        ? {
            'api_version': 1,
            'ok': false,
            'error': {'message': '저장 실패'},
          }
        : {'api_version': 1, 'ok': true, 'data': data()};
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(body: SettingsDialog(api: api)),
      ),
    );
    await tester.pumpAndSettle();
    await tester.enterText(find.byKey(const ValueKey('retry_body')), '9');
    await tester.pump();
    await tester.tap(find.text('변경사항 적용'));
    await tester.pumpAndSettle();
    expect(find.textContaining('저장 실패'), findsOneWidget);
    final field = tester.widget<TextField>(
      find.byKey(const ValueKey('retry_body')),
    );
    expect(field.controller!.text, '9');
  });
}

Map<String, Object?> guided() => {
  'revision': 'r2',
  'running': false,
  'fields': [
    {
      'key': 'std_hanging_indent',
      'label': '내어쓰기',
      'type': 'boolean',
      'default': true,
      'group': '표준서식',
    },
    {
      'key': 'std_parspace_circle',
      'label': '원 항목 위 간격 (pt)',
      'type': 'number',
      'default': '8',
      'group': '표준서식',
    },
    {
      'key': 'check_updates_on_start',
      'label': '시작할 때 업데이트 확인',
      'type': 'boolean',
      'default': true,
      'group': '네트워크',
    },
  ],
  'values': {
    'std_hanging_indent': true,
    'std_parspace_circle': '8',
    'check_updates_on_start': true,
  },
};

void mainGuided() {
  testWidgets('categories, friendly titles, examples and the number stepper', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(1280, 900);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);
    List<Object?>? saved;
    Future<Object?> api(String method, List<Object?> args) async {
      if (method == 'save_settings') saved = args;
      return {'api_version': 1, 'ok': true, 'data': guided(), 'error': null};
    }

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(body: SettingsDialog(api: api)),
      ),
    );
    await tester.pumpAndSettle();
    // 보고서 모양: 쉬운 제목과 끄면/켜면 예시가 함께 보인다.
    expect(find.text('내어쓰기'), findsWidgets);
    expect(find.text('끄면'), findsOneWidget);
    expect(find.text('지금 설정'), findsOneWidget);
    // 분류를 바꾸면 그 분류 설정만 보인다.
    await tester.tap(find.byKey(const ValueKey('category-paragraph')));
    await tester.pumpAndSettle();
    expect(find.text('ㅇ 항목 위 간격'), findsOneWidget);
    expect(find.text('위 간격 8pt'), findsOneWidget);
    await tester.tap(find.byTooltip('1 늘리기'));
    await tester.pumpAndSettle();
    expect(find.text('위 간격 9pt'), findsOneWidget); // 예시가 값에 따라 바로 바뀐다
    expect(find.text('바꾼 설정 1개'), findsOneWidget);
    // 검색은 분류와 관계없이 찾는다.
    await tester.enterText(find.byType(TextField).first, '업데이트');
    await tester.pumpAndSettle();
    expect(find.text('시작할 때 업데이트 확인'), findsWidgets);
    await tester.tap(find.text('변경사항 적용'));
    await tester.pumpAndSettle();
    expect(saved, [
      {'std_parspace_circle': '9'},
      'r2',
    ]);
  });
}
