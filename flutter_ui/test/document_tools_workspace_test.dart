import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:docfit_ui/features/tools/document_tools_workspace.dart';

void main() {
  testWidgets('outline keyboard command uses backend and keeps returned text', (
    tester,
  ) async {
    final calls = <String>[];
    Future<Object?> api(String method, List<Object?> args) async {
      calls.add('${args.first}');
      if (args.first == 'outline.load') {
        return {
          'ok': true,
          'data': {'text': '# 첫 항목\n# 둘째 항목', 'revision': 'r'},
        };
      }
      if (args.first == 'outline.toggle') {
        return {
          'ok': true,
          'data': {'text': '# [x] 첫 항목\n# 둘째 항목', 'index': 0},
        };
      }
      if (args.first == 'outline.save') {
        return {
          'ok': true,
          'data': {'text': (args[1] as Map)['text'], 'revision': 's'},
        };
      }
      return {
        'ok': true,
        'data': {'text': '변환 결과'},
      };
    }

    await tester.pumpWidget(
      MaterialApp(home: DocumentToolsWorkspace(api: api)),
    );
    await tester.pumpAndSettle();
    final input = find.byWidgetPredicate(
      (widget) =>
          widget is TextField && widget.decoration?.labelText == '입력 / 초안',
    );
    await tester.tap(input);
    await tester.pump();
    await tester.sendKeyDownEvent(LogicalKeyboardKey.controlLeft);
    await tester.sendKeyEvent(LogicalKeyboardKey.enter);
    await tester.sendKeyUpEvent(LogicalKeyboardKey.controlLeft);
    await tester.pump();
    expect(calls, contains('outline.toggle'));
    expect((tester.widget<TextField>(input).controller!).text, contains('[x]'));
    await tester.pump(const Duration(seconds: 1));
    await tester.pumpAndSettle();
    await tester.pumpWidget(const SizedBox());
  });
  testWidgets('AI transform displays output without invoking Tk tools', (
    tester,
  ) async {
    final calls = <String>[];
    await tester.pumpWidget(
      MaterialApp(
        home: DocumentToolsWorkspace(
          initial: 'convert',
          api: (method, args) async {
            calls.add('$method:${args.first}');
            return {
              'ok': true,
              'data': {'text': '□ 정리된 답변'},
            };
          },
        ),
      ),
    );
    await tester.tap(find.text('실행 / 미리보기'));
    await tester.pumpAndSettle();
    expect(calls, ['document_tool:outline']);
    final output = find.byWidgetPredicate(
      (widget) =>
          widget is TextField && widget.decoration?.labelText == '변환·검토 결과',
    );
    expect(tester.widget<TextField>(output).controller!.text, '□ 정리된 답변');
  });
}
