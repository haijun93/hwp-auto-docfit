import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:docfit_ui/main.dart';
import 'package:docfit_ui/features/tools/document_tools_workspace.dart';
import 'workspace_test.dart' show initialState;

void main() {
  testWidgets(
    'text input opens Flutter and adds text without legacy commands',
    (tester) async {
      final calls = <String>[];
      final state = initialState();
      await tester.pumpWidget(
        MaterialApp(
          home: Workspace(
            api: (method, args) async {
              calls.add(method);
              if (method == 'document_tool') {
                expect(args.first, 'add_text');
                expect((args[1] as Map)['text'], '새 문서 본문');
                return {
                  'ok': true,
                  'data': {'path': 'input.txt'},
                };
              }
              return state;
            },
          ),
        ),
      );
      await tester.pumpAndSettle();
      await tester.ensureVisible(find.text('텍스트 입력'));
      await tester.tap(find.text('텍스트 입력'));
      await tester.pumpAndSettle();
      expect(find.byType(DocumentToolsWorkspace), findsOneWidget);
      final input = find.byWidgetPredicate(
        (widget) => widget is TextField && widget.decoration?.labelText == '입력',
      );
      await tester.enterText(input, '새 문서 본문');
      await tester.tap(find.text('문서 목록에 추가'));
      await tester.pumpAndSettle();
      expect(calls, contains('document_tool'));
      expect(calls, isNot(contains('text_input')));
      expect(calls, isNot(contains('run_tool')));
      expect(tester.takeException(), isNull);
      await tester.pumpWidget(const SizedBox());
    },
  );
}
