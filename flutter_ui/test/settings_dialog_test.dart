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
          'default': '15'
        },
        {
          'key': 'developer_mode',
          'label': '문서 도구 표시',
          'type': 'boolean',
          'default': false
        }
      ],
      'values': {'retry_body': '7', 'developer_mode': false}
    };
void main() {
  testWidgets('applies only changed settings with revision', (tester) async {
    List<Object?>? saved;
    Future<Object?> api(String method, List<Object?> args) async {
      if (method == 'save_settings') saved = args;
      return {'api_version': 1, 'ok': true, 'data': data(), 'error': null};
    }

    await tester.pumpWidget(MaterialApp(
        home: Builder(
            builder: (context) => Scaffold(
                body: TextButton(
                    onPressed: () => showDialog<void>(
                        context: context,
                        builder: (_) => SettingsDialog(api: api)),
                    child: const Text('열기'))))));
    await tester.tap(find.text('열기'));
    await tester.pumpAndSettle();
    await tester.enterText(find.byKey(const ValueKey('retry_body')), '9');
    await tester.pump();
    await tester.tap(find.text('변경사항 적용'));
    await tester.pumpAndSettle();
    expect(saved, [
      {'retry_body': '9'},
      'r1'
    ]);
  });
  testWidgets('save error preserves draft and cancel remains available',
      (tester) async {
    Future<Object?> api(String method, List<Object?> args) async =>
        method == 'save_settings'
            ? {
                'api_version': 1,
                'ok': false,
                'error': {'message': '저장 실패'}
              }
            : {'api_version': 1, 'ok': true, 'data': data()};
    await tester.pumpWidget(
        MaterialApp(home: Scaffold(body: SettingsDialog(api: api))));
    await tester.pumpAndSettle();
    await tester.enterText(find.byKey(const ValueKey('retry_body')), '9');
    await tester.pump();
    await tester.tap(find.text('변경사항 적용'));
    await tester.pumpAndSettle();
    expect(find.textContaining('저장 실패'), findsOneWidget);
    final field =
        tester.widget<TextField>(find.byKey(const ValueKey('retry_body')));
    expect(field.controller!.text, '9');
  });
}
