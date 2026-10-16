import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:docfit_ui/features/tools/document_tools_workspace.dart';

void main() {
  testWidgets(
    'initial draft loading blocks typing and preserves newer controller input',
    (tester) async {
      final pending = Completer<Object?>();
      Future<Object?> api(String method, List<Object?> args) async =>
          pending.future;
      await tester.pumpWidget(
        MaterialApp(home: DocumentToolsWorkspace(api: api)),
      );
      await tester.pump();
      final field = find.byWidgetPredicate(
        (w) => w is TextField && w.decoration?.labelText == '입력 / 초안',
      );
      expect(tester.widget<TextField>(field).readOnly, isTrue);
      tester.widget<TextField>(field).controller!.text = '# 새로운 입력';
      pending.complete({
        'ok': true,
        'data': {'text': '# 저장된 초안', 'revision': 'r'},
      });
      await tester.pumpAndSettle();
      expect(tester.widget<TextField>(field).controller!.text, '# 새로운 입력');
      expect(tester.widget<TextField>(field).readOnly, isFalse);
      expect(tester.takeException(), isNull);
      await tester.pumpWidget(const SizedBox());
    },
  );

  testWidgets('leaving while the draft is still loading is not blocked', (
    tester,
  ) async {
    final pending = Completer<Object?>();
    Future<Object?> api(String method, List<Object?> args) async =>
        pending.future;
    final navigator = GlobalKey<NavigatorState>();
    await tester.pumpWidget(
      MaterialApp(navigatorKey: navigator, home: const SizedBox()),
    );
    navigator.currentState!.push(
      MaterialPageRoute<void>(
        builder: (_) => DocumentToolsWorkspace(api: api, initial: 'clean'),
      ),
    );
    await tester.pumpAndSettle();
    final field = find.byWidgetPredicate(
      (w) => w is TextField && w.decoration?.labelText == '입력 / 초안',
    );
    // Text typed in another tool becomes unsaved outline text after switching.
    await tester.enterText(field, '# 다른 도구에서 입력한 글');
    await tester.tap(find.text('AI 답변 기호 정리'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('아웃라이너').last);
    await tester.pumpAndSettle();
    expect(tester.widget<TextField>(field).readOnly, isTrue);
    await navigator.currentState!.maybePop();
    await tester.pumpAndSettle();
    expect(find.byType(DocumentToolsWorkspace), findsNothing);
    pending.complete({
      'ok': true,
      'data': {'text': '', 'revision': 'r'},
    });
    await tester.pumpAndSettle();
    expect(tester.takeException(), isNull);
  });

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
