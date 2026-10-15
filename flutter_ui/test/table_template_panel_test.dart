import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:docfit_ui/features/formats/table_template_panel.dart';

void main() {
  testWidgets('table template loads and resets through shared API', (
    tester,
  ) async {
    final calls = <String>[];
    Future<Object?> api(String method, List<Object?> args) async {
      calls.add('$method:${args.first}');
      return {
        'ok': true,
        'data': {
          'description': '예시 3×2 표',
          'preview': {'rows': 3, 'cols': 2, 'header_rows': 2},
        },
      };
    }

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(body: TableTemplatePanel(api: api, running: false)),
      ),
    );
    await tester.pumpAndSettle();
    expect(find.text('예시 3×2 표'), findsOneWidget);
    expect(find.textContaining('머리글 2행'), findsOneWidget);
    await tester.tap(find.text('내장 표 서식으로 초기화'));
    await tester.pumpAndSettle();
    expect(calls, ['table_template:get', 'table_template:reset']);
  });

  testWidgets('running job disables template changes', (tester) async {
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: TableTemplatePanel(
            running: true,
            api: (_, _) async => {
              'ok': true,
              'data': {'description': '기본 표'},
            },
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();
    final button = tester.widget<FilledButton>(
      find.widgetWithText(FilledButton, '예시 표 학습'),
    );
    expect(button.onPressed, isNull);
  });
}
