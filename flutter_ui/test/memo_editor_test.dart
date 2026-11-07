import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:docfit_ui/features/editor/editor_core.dart';
import 'package:docfit_ui/features/editor/markdown_format.dart';
import 'package:docfit_ui/features/editor/memo_editor.dart';

TextEditingValue _v(String text, int start, [int? end]) =>
    TextEditingValue(text: text, selection: TextSelection(baseOffset: start, extentOffset: end ?? start));

void main() {
  group('markdown_format', () {
    test('plain paragraphs follow the same rules as Python memo_markdown_to_paragraphs', () {
      const markdown =
          '# 회의 메모\n\n**복지 예산** 확대와 *도로* 정비\n- 첫째 `항목`\n1. 둘째\n> 인용 [자료](https://a.kr)\n---\n```\ncode **그대로**\n```\n';
      expect(markdownToPlainParagraphs(markdown), const [
        PlainParagraph('회의 메모', level: 1),
        PlainParagraph('복지 예산 확대와 도로 정비'),
        PlainParagraph('첫째 항목'),
        PlainParagraph('둘째'),
        PlainParagraph('인용 자료 (https://a.kr)'),
        PlainParagraph('code **그대로**'),
      ]);
      expect(markdownToPlainParagraphs(' \n---\n'), isEmpty);
    });

    test('bold wraps selection and toggles off', () {
      final on = toggleInline(_v('가 나 다', 2, 3), '**');
      expect(on.text, '가 **나** 다');
      expect(on.selection, const TextSelection(baseOffset: 4, extentOffset: 5));
      expect(toggleInline(on, '**').text, '가 나 다');
      final empty = toggleInline(_v('', 0), '*');
      expect(empty.text, '*글자*');
      expect(empty.selection, const TextSelection(baseOffset: 1, extentOffset: 3));
    });

    test('lists, quote, heading, rule, code block, link, clear', () {
      final bullets = toggleLinePrefix(_v('하나\n둘', 0, 4), MemoListKind.bullet);
      expect(bullets.text, '- 하나\n- 둘');
      expect(toggleLinePrefix(bullets, MemoListKind.bullet).text, '하나\n둘');
      expect(toggleLinePrefix(bullets, MemoListKind.numbered).text, '1. 하나\n2. 둘');
      expect(toggleLinePrefix(_v('말', 0), MemoListKind.quote).text, '> 말');
      final heading = setBlockStyle(_v('제목\n본문', 1), 2);
      expect(heading.text, '## 제목\n본문');
      expect(currentBlockStyle(heading.copyWith(selection: const TextSelection.collapsed(offset: 3))), 2);
      expect(setBlockStyle(heading, 0).text, '제목\n본문');
      expect(insertHorizontalRule(_v('가', 1)).text, '가\n---\n');
      expect(insertCodeBlock(_v('', 0)).text, '```\n\n```\n');
      expect(insertCodeBlock(_v('x = 1', 0, 5)).text, '```\nx = 1\n```');
      expect(insertLink(_v('자료 보기', 0, 2), 'https://a.kr').text, '[자료](https://a.kr) 보기');
      expect(clearFormatting(_v('## **굵게** [링크](u) `c`', 0, 5)).text, '굵게 링크 c');
    });
  });

  group('DartEditorCore', () {
    test('typing groups into one undo step, commands are separate steps', () {
      final core = DartEditorCore();
      core.updateFromInput(_v('가', 1));
      core.updateFromInput(_v('가나', 2));
      core.breakUndoGroup();
      core.updateFromInput(_v('가나다', 3));
      core.updateFromInput(core.value.copyWith(selection: const TextSelection(baseOffset: 0, extentOffset: 3)));
      core.apply(EditorCommand.bold);
      expect(core.markdown, '**가나다**');
      core.undo();
      expect(core.markdown, '가나다');
      core.undo();
      expect(core.markdown, '가나');
      core.undo();
      expect(core.markdown, '');
      expect(core.canUndo, isFalse);
      core.redo();
      core.redo();
      core.redo();
      expect(core.markdown, '**가나다**');
      expect(core.canRedo, isFalse);
    });

    test('IME composing updates stay in one undo step', () {
      final core = DartEditorCore(text: '메모 ');
      // 'ㅎ' → '하' → '한' 조합 중에는 묶음이 끊기지 않는다.
      for (final s in ['ㅎ', '하', '한']) {
        core.updateFromInput(
          TextEditingValue(
            text: '메모 $s',
            selection: const TextSelection.collapsed(offset: 4),
            composing: const TextRange(start: 3, end: 4),
          ),
        );
        core.breakUndoGroup();
      }
      core.updateFromInput(_v('메모 한', 4));
      core.undo();
      expect(core.markdown, '메모 ');
      expect(core.plainParagraphs(), const [PlainParagraph('메모')]);
    });
  });

  testWidgets('memo editor toolbar, undo shortcut, Saved status and delete', (tester) async {
    tester.view.physicalSize = const Size(1000, 800);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);
    final saves = <MemoDocument>[];
    var deleted = false;
    final controller = MemoEditorController();
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: MemoEditor(
            controller: controller,
            onAutoSave: (doc) async => saves.add(doc),
            onDelete: () => deleted = true,
          ),
        ),
      ),
    );
    expect(find.text('새 메모'), findsOneWidget);
    for (final key in [
      'memo-undo', 'memo-redo', 'memo-block-style', 'memo-bold', 'memo-italic', 'memo-link', 'memo-code', //
      'memo-code-block', 'memo-bullet', 'memo-numbered', 'memo-quote', 'memo-rule', 'memo-clear', 'memo-delete',
    ]) {
      expect(find.byKey(ValueKey(key)), findsOneWidget, reason: key);
    }
    expect(find.text('보통'), findsOneWidget);

    await tester.enterText(find.byKey(const ValueKey('memo-body')), '예산');
    await tester.pump();
    expect(find.text('저장 중…'), findsOneWidget);
    await tester.pump(const Duration(seconds: 1));
    expect(find.text('Saved'), findsOneWidget);
    expect(saves.last.markdown, '예산');

    await tester.tap(find.byKey(const ValueKey('memo-bullet')));
    await tester.pump();
    expect(controller.document.markdown, '- 예산');
    await tester.tap(find.byKey(const ValueKey('memo-block-style')));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const ValueKey('memo-block-style-1')).last);
    await tester.pumpAndSettle();
    expect(controller.document.markdown, '# 예산');
    expect(controller.plainParagraphs, const [PlainParagraph('예산', level: 1)]);

    await tester.tap(find.byKey(const ValueKey('memo-undo')));
    await tester.pump();
    expect(controller.document.markdown, '- 예산');
    await tester.sendKeyDownEvent(LogicalKeyboardKey.controlLeft);
    await tester.sendKeyEvent(LogicalKeyboardKey.keyZ);
    await tester.sendKeyUpEvent(LogicalKeyboardKey.controlLeft);
    await tester.pump();
    expect(controller.document.markdown, '예산');

    await tester.tap(find.byKey(const ValueKey('memo-link')));
    await tester.pumpAndSettle();
    await tester.enterText(find.byKey(const ValueKey('memo-link-url')), 'https://mapo.go.kr');
    await tester.tap(find.byKey(const ValueKey('memo-link-ok')));
    await tester.pumpAndSettle();
    expect(controller.document.markdown, contains('(https://mapo.go.kr)'));

    await tester.tap(find.byKey(const ValueKey('memo-delete')));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const ValueKey('memo-delete-ok')));
    await tester.pumpAndSettle();
    expect(deleted, isTrue);
    expect(tester.takeException(), isNull);
  });
}
