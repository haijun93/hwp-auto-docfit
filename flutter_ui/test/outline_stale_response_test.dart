import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:docfit_ui/features/tools/document_tools_workspace.dart';

void main() {
  testWidgets('pending outline action preserves subsequent typing', (
    tester,
  ) async {
    final pending = Completer<Object?>();
    Future<Object?> api(String method, List<Object?> args) async {
      if (args.first == 'outline.load') {
        return {
          'ok': true,
          'data': {'text': '# 원래 문장', 'revision': 'r'},
        };
      }
      if (args.first == 'outline.toggle') return pending.future;
      return {
        'ok': true,
        'data': {'text': (args[1] as Map)['text'], 'revision': 'saved'},
      };
    }

    await tester.pumpWidget(
      MaterialApp(home: DocumentToolsWorkspace(api: api)),
    );
    await tester.pumpAndSettle();
    final field = find.byWidgetPredicate(
      (w) => w is TextField && w.decoration?.labelText == '입력 / 초안',
    );
    await tester.tap(field);
    await tester.pump();
    await tester.sendKeyDownEvent(LogicalKeyboardKey.controlLeft);
    await tester.sendKeyEvent(LogicalKeyboardKey.enter);
    await tester.sendKeyUpEvent(LogicalKeyboardKey.controlLeft);
    await tester.enterText(field, '# 원래 문장\n# 응답 대기 중 추가한 문장');
    await tester.pump(const Duration(seconds: 2));
    pending.complete({
      'ok': true,
      'data': {'text': '# [x] 원래 문장', 'index': 0},
    });
    await tester.pump();
    final actual = tester.widget<TextField>(field).controller!.text;
    expect(actual, contains('응답 대기 중 추가한 문장'));
    await tester.pump(const Duration(seconds: 1));
    await tester.pumpWidget(const SizedBox());
  });
  testWidgets('outline actions are serialized and each uses the newest text', (
    tester,
  ) async {
    final first = Completer<Object?>();
    final seen = <String>[];
    Future<Object?> api(String method, List<Object?> args) async {
      if (args.first == 'outline.load') {
        return {
          'ok': true,
          'data': {'text': '# 항목', 'revision': 'r'},
        };
      }
      if (args.first == 'outline.toggle') {
        seen.add((args[1] as Map)['text'] as String);
        if (seen.length == 1) return first.future;
        return {
          'ok': true,
          'data': {'text': '# 항목', 'index': 0},
        };
      }
      return {
        'ok': true,
        'data': {'text': (args[1] as Map)['text'], 'revision': 's'},
      };
    }

    await tester.pumpWidget(
      MaterialApp(home: DocumentToolsWorkspace(api: api)),
    );
    await tester.pumpAndSettle();
    final field = find.byWidgetPredicate(
      (w) => w is TextField && w.decoration?.labelText == '입력 / 초안',
    );
    await tester.tap(field);
    for (var i = 0; i < 2; i++) {
      await tester.sendKeyDownEvent(LogicalKeyboardKey.controlLeft);
      await tester.sendKeyEvent(LogicalKeyboardKey.enter);
      await tester.sendKeyUpEvent(LogicalKeyboardKey.controlLeft);
      await tester.pump();
    }
    expect(seen, ['# 항목']);
    expect(
      tester
          .widget<PopScope>(find.byWidgetPredicate((w) => w is PopScope))
          .canPop,
      isFalse,
    );
    first.complete({
      'ok': true,
      'data': {'text': '# [x] 항목', 'index': 0},
    });
    await tester.pump();
    await tester.pump();
    expect(seen, ['# 항목', '# [x] 항목']);
    expect(tester.widget<TextField>(field).controller!.text, '# 항목');
    await tester.pump(const Duration(seconds: 1));
    await tester.pumpWidget(const SizedBox());
  });
}
