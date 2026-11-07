import 'package:docfit_ui/features/table_sketch/table_sketch_screen.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';

/// 복구 안내 대화상자: 기본 선택은 '복구'(Enter), Esc로 닫으면 초안을 지우지 않는다(사용자 요청 2026-11-07).
void main() {
  Future<List<String>> run(WidgetTester tester, LogicalKeyboardKey key) async {
    final calls = <String>[];
    Future<Object?> api(String command, List<Object?> args) async {
      if (command == 'table_sketch') {
        calls.add('${args.first}');
        switch (args.first) {
          case 'load_draft':
            return {
              'exists': true,
              'sketch': {'grid': {'cols': 3, 'rows': 3, 'cell_mm': 5.0}, 'lines': [], 'texts': [], 'fills': []},
            };
          case 'preview':
            return {'ok': true};
        }
      }
      return {'ok': true};
    }

    await tester.pumpWidget(MaterialApp(home: TableSketchScreen(api: api)));
    await tester.pumpAndSettle();
    expect(find.text('복구 가능한 작업이 있습니다'), findsOneWidget);
    final restore = tester.widget<FilledButton>(find.byKey(const ValueKey('draft-restore')));
    expect(restore.autofocus, isTrue);
    await tester.sendKeyEvent(key);
    await tester.pumpAndSettle();
    expect(find.text('복구 가능한 작업이 있습니다'), findsNothing);
    return calls;
  }

  testWidgets('Enter restores the draft', (tester) async {
    final calls = await run(tester, LogicalKeyboardKey.enter);
    expect(calls, isNot(contains('clear_draft')));
    expect(calls, contains('preview'));
  });

  testWidgets('Escape keeps the draft without deleting it', (tester) async {
    final calls = await run(tester, LogicalKeyboardKey.escape);
    expect(calls, isNot(contains('clear_draft')));
  });
}
