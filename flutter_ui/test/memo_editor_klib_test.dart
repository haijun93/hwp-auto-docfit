import 'package:flutter/gestures.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:docfit_ui/features/editor/editor_core.dart';
import 'package:docfit_ui/features/editor/klib_editor_core.dart';
import 'package:docfit_ui/features/editor/memo_editor.dart';
import 'package:docfit_ui/features/editor/text_offsets.dart';
import 'package:docfit_ui/features/notebook/notebook_api.dart';
import 'package:docfit_ui/features/notebook/notebook_screen.dart';

import 'fake_editor_backend.dart';

TextEditingValue _v(String text, int start, [int? end, TextRange composing = TextRange.empty]) => TextEditingValue(
  text: text,
  selection: TextSelection(baseOffset: start, extentOffset: end ?? start),
  composing: composing,
);

/// 줄 선 요청이 모두 끝나게 한다(가짜 백엔드는 마이크로태스크로 응답).
Future<void> _drain() => Future<void>.delayed(Duration.zero);

KlibEditorCore _core(FakeEditorBackend fake, [String text = '']) =>
    KlibEditorCore(fake.call, text: text, keepAlive: Duration.zero);

void main() {
  group('text_offsets', () {
    test('UTF-16 ↔ UTF-8 bytes with Hangul and emoji', () {
      const s = '가a😀b';
      expect(utf8Length(s), 3 + 1 + 4 + 1);
      expect([for (var i = 0; i <= s.length; i++) utf16ToUtf8(s, i)], [0, 3, 4, 4, 8, 9]); // 대리 쌍 가운데 → 앞
      expect([for (final b in [0, 3, 4, 8, 9]) utf8ToUtf16(s, b)], [0, 1, 2, 4, 5]);
      expect(utf8ToUtf16(s, 5), 4); // 글자 중간 → 뒤
    });

    test('line/column, newline normalization and search rules', () {
      expect(lineColumnAt('가나\n다😀라', 6), (line: 2, column: 3)); // '다😀' 뒤
      final (text, offs) = normalizeNewlines('a\r\nb\rc', [3, 6]);
      expect(text, 'a\nb\nc');
      expect(offs, [2, 5]);
      const opts = FindOptions();
      expect(findAllMatches('Apple apple APPLE', 'apple', opts).length, 3);
      expect(findAllMatches('Apple apple', 'apple', const FindOptions(caseSensitive: true)).single.start, 6);
      expect(findAllMatches('예산 예산안 예산', '예산', const FindOptions(wholeWord: true)).map((m) => m.start), [0, 7]);
      expect(findMatch('ab ab ab', 'ab', opts, 4, backward: true)!.start, 3);
      expect(findMatch('ab ab ab', 'ab', opts, 7)!.start, 0); // 끝에서 처음으로
    });
  });

  group('KlibEditorCore', () {
    test('Hangul composition and emoji are sent as byte ranges and mirrored in Rust', () async {
      final fake = FakeEditorBackend();
      final core = _core(fake, '메모 ');
      expect(await core.ready, isTrue);
      expect(core.engineName, 'Rust');
      for (final s in ['ㅎ', '하', '한']) {
        core.updateFromInput(_v('메모 $s', 4, null, const TextRange(start: 3, end: 4)));
      }
      core.updateFromInput(_v('메모 한', 4));
      core.updateFromInput(_v('메모 한😀', 6));
      core.updateFromInput(_v('메모 한😀!', 7));
      await _drain();
      final edits = fake.log.where((r) => r['cmd'] == 'edit_replace').map((r) => (r['start'], r['end'], r['text'])).toList();
      expect(edits, [(7, 7, 'ㅎ'), (7, 10, '하'), (7, 10, '한'), (10, 10, '😀'), (14, 14, '!')]);
      expect(fake.docs.values.single.text, '메모 한😀!');
      expect(core.canUndo, isTrue);

      // 붙여넣은 CRLF는 LF로 맞추고 선택도 옮긴다.
      core.updateFromInput(_v('메모 한😀!\r\n둘', 10));
      expect(core.value.text, '메모 한😀!\n둘');
      expect(core.value.selection.baseOffset, 9);
      await _drain();
      expect(fake.docs.values.single.text, '메모 한😀!\n둘');
      core.dispose();
      await _drain();
      expect(fake.commands.last, 'edit_close');
      expect(fake.docs, isEmpty);
    });

    test('undo/redo and formatting come from Rust with selections mapped back to UTF-16', () async {
      final fake = FakeEditorBackend();
      final core = _core(fake);
      await core.ready;
      core.updateFromInput(_v('가나', 2));
      core.breakUndoGroup();
      core.updateFromInput(_v('가나 다😀', 5));
      core.updateFromInput(_v('가나 다😀', 3, 6)); // '다😀' 선택(커서 이동 = 묶음 경계)
      await core.apply(EditorCommand.bold);
      expect(core.markdown, '가나 **다😀**');
      expect(core.value.selection, const TextSelection(baseOffset: 5, extentOffset: 8));
      expect(fake.log.lastWhere((r) => r['cmd'] == 'edit_md_inline'), containsPair('start', 7));
      expect(fake.log.firstWhere((r) => r['cmd'] == 'edit_commit'), isNotNull);

      await core.setBlockStyle(1);
      expect(core.markdown, '# 가나 **다😀**');
      expect(core.blockStyle, 1);
      await core.undo();
      expect(core.markdown, '가나 **다😀**');
      await core.undo();
      expect(core.markdown, '가나 다😀');
      await core.undo();
      expect(core.markdown, '가나');
      await core.redo();
      expect(core.markdown, '가나 다😀');
      expect(core.canRedo, isTrue);

      core.updateFromInput(_v(core.markdown, 2, 2));
      await core.insertLink('https://mapo.go.kr');
      expect(core.markdown, contains('(https://mapo.go.kr)'));
      await core.apply(EditorCommand.horizontalRule);
      expect(core.markdown, contains('---'));
      core.dispose();
    });

    test('find, find previous, replace (select then replace) and replace all', () async {
      final fake = FakeEditorBackend();
      final core = _core(fake, '예산 😀예산 예산안');
      await core.ready;
      core.updateFromInput(_v(core.markdown, 0));
      final first = await core.find('예산', const FindOptions());
      expect(first, const TextRange(start: 0, end: 2));
      final second = await core.find('예산', const FindOptions());
      expect(second, const TextRange(start: 5, end: 7));
      expect(await core.find('예산', const FindOptions(), backward: true), const TextRange(start: 0, end: 2));
      expect(await core.countMatches('예산', const FindOptions()), 3);
      expect(await core.countMatches('예산', const FindOptions(wholeWord: true)), 2);
      expect(await core.find('없음', const FindOptions()), isNull);

      // 선택이 일치가 아니면 선택만, 일치면 바꾸고 다음 일치를 선택.
      core.updateFromInput(_v(core.markdown, 2));
      expect(await core.replaceNext('예산', '결산', const FindOptions()), isFalse);
      expect(core.value.selection, const TextSelection(baseOffset: 5, extentOffset: 7));
      expect(await core.replaceNext('예산', '결산', const FindOptions()), isTrue);
      expect(core.markdown, '예산 😀결산 예산안');
      expect(core.value.selection, const TextSelection(baseOffset: 8, extentOffset: 10));

      expect(await core.replaceAll('예산', '豫算', const FindOptions()), 2);
      expect(core.markdown, '豫算 😀결산 豫算안');
      await core.undo();
      expect(core.markdown, '예산 😀결산 예산안');
      core.dispose();
    });

    test('falls back to the Dart core when klib cannot open and keeps editing', () async {
      final fake = FakeEditorBackend()..failOpen = true;
      final core = _core(fake, '처음');
      var notified = 0;
      core.changes.addListener(() => notified++);
      core.updateFromInput(_v('처음 글', 4));
      expect(await core.ready, isFalse);
      expect(core.engineName, 'Dart');
      expect(core.fellBack, isTrue);
      expect(notified, 1);
      expect(core.markdown, '처음 글');
      core.updateFromInput(_v('처음 글자', 5));
      await core.apply(EditorCommand.bold);
      expect(core.markdown, contains('**'));
      await core.undo();
      expect(core.markdown, '처음 글자');
      core.dispose();
    });

    test('re-opens with the current text when klib restarted (idle exit), then continues', () async {
      final fake = FakeEditorBackend();
      final core = _core(fake, 'ab');
      await core.ready;
      fake.restart();
      core.updateFromInput(_v('abc', 3));
      core.updateFromInput(_v('abcd', 4)); // 첫 실패 뒤에 줄 선 편집은 새 문서에 두 번 들어가지 않는다
      await _drain();
      await _drain();
      expect(core.engineName, 'Rust');
      expect(fake.docs.values.single.text, 'abcd');
      expect(core.canUndo, isFalse); // 다시 열면 그 전 이력은 사라짐
      core.updateFromInput(_v('abcde', 5));
      await _drain();
      expect(fake.docs.values.single.text, 'abcde');
      core.dispose();
    });

    test('falls back when a paste exceeds the bridge request limit', () async {
      final fake = FakeEditorBackend()..maxRequestBytes = 200;
      final core = _core(fake, '짧은 글');
      await core.ready;
      final big = '짧은 글${'가' * 100}';
      core.updateFromInput(_v(big, big.length));
      await _drain();
      await _drain();
      expect(core.engineName, 'Dart');
      expect(core.markdown, big); // 글은 지키고, Rust 쪽 실행취소 기록은 이어 받지 못한다
      core.updateFromInput(_v('$big!', big.length + 1));
      await core.undo();
      expect(core.markdown, big);
      core.dispose();
    });

    test('long documents are fetched by line chunks when edit_text is too large', () async {
      final fake = FakeEditorBackend();
      final text = List.generate(30, (i) => '줄$i').join('\n');
      // 응답 64 KiB 초과(Python 브리지)를 흉내 내 edit_text만 실패시킨다.
      Future<Map<String, Object?>> backend(Map<String, Object?> r) async =>
          r['cmd'] == 'edit_text' ? {'ok': false, 'message': 'klib 응답이 허용 크기를 초과했습니다.'} : fake.call(r);
      final core = KlibEditorCore(backend, text: text, keepAlive: Duration.zero, chunkLines: 7);
      await core.ready;
      core.updateFromInput(_v(text, 0, 2));
      await core.apply(EditorCommand.bold);
      expect(core.markdown, '**줄0**\n${text.substring(3)}');
      expect(core.engineName, 'Rust');
      expect(fake.commands.where((c) => c == 'edit_lines').length, 5); // 30줄 / 7줄씩
      core.dispose();
    });
  });

  group('MemoEditor step 2', () {
    Future<void> pumpEditor(WidgetTester tester, {EditorCore Function(String)? createCore, String text = ''}) async {
      tester.view.physicalSize = const Size(1100, 800);
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.reset);
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: MemoEditor(initial: MemoDocument(title: '메모', markdown: text), createCore: createCore),
          ),
        ),
      );
      await tester.pumpAndSettle();
    }

    String textOf(WidgetTester tester, String key) => tester.widget<Text>(find.byKey(ValueKey(key))).data!;

    testWidgets('status bar shows line/column, characters, zoom, line ending and encoding (Rust core)', (tester) async {
      final fake = FakeEditorBackend();
      await pumpEditor(tester, createCore: (t) => _core(fake, t), text: '첫 줄\r\n둘째 줄');
      expect(textOf(tester, 'memo-status-eol'), 'Windows (CRLF)');
      expect(textOf(tester, 'memo-status-encoding'), 'UTF-8');
      expect(textOf(tester, 'memo-status-chars'), '8자');
      expect(textOf(tester, 'memo-status-position'), '줄 2, 열 5');
      expect(find.byTooltip('편집 엔진: Rust 코어(klib)'), findsOneWidget);

      await tester.enterText(find.byKey(const ValueKey('memo-body')), '가나다');
      await tester.pumpAndSettle();
      expect(textOf(tester, 'memo-status-position'), '줄 1, 열 4');
      expect(fake.docs.values.single.text, '가나다');

      // 서식 단추와 Ctrl+Z는 Rust 코어를 거친다.
      final body = tester.widget<TextField>(find.byKey(const ValueKey('memo-body'))).controller!;
      body.selection = const TextSelection(baseOffset: 0, extentOffset: 2);
      await tester.pump();
      await tester.tap(find.byKey(const ValueKey('memo-bold')));
      await tester.pumpAndSettle();
      expect(body.text, '**가나**다');
      await tester.sendKeyDownEvent(LogicalKeyboardKey.controlLeft);
      await tester.sendKeyEvent(LogicalKeyboardKey.keyZ);
      await tester.sendKeyUpEvent(LogicalKeyboardKey.controlLeft);
      await tester.pumpAndSettle();
      expect(body.text, '가나다');
      expect(fake.commands, contains('edit_undo'));
      expect(tester.takeException(), isNull);
    });

    testWidgets('Ctrl+wheel and Ctrl+= / Ctrl+- / Ctrl+0 zoom the body text', (tester) async {
      await pumpEditor(tester, text: '확대 시험');
      double fontSize() => tester.widget<TextField>(find.byKey(const ValueKey('memo-body'))).style!.fontSize!;
      expect(fontSize(), kMemoBaseFontSize);
      await tester.tap(find.byKey(const ValueKey('memo-body'))); // 단축키는 편집기 안에 포커스가 있을 때
      await tester.pump();
      final pointer = TestPointer(1, PointerDeviceKind.mouse);
      final center = tester.getCenter(find.byKey(const ValueKey('memo-body')));
      await tester.sendEventToBinding(pointer.hover(center));
      await tester.sendKeyDownEvent(LogicalKeyboardKey.controlLeft);
      await tester.sendEventToBinding(pointer.scroll(const Offset(0, -40)));
      await tester.sendEventToBinding(pointer.scroll(const Offset(0, -40)));
      await tester.pump();
      expect(textOf(tester, 'memo-status-zoom'), '120%');
      expect(fontSize(), closeTo(kMemoBaseFontSize * 1.2, 0.001));
      await tester.sendEventToBinding(pointer.scroll(const Offset(0, 40)));
      await tester.pump();
      expect(textOf(tester, 'memo-status-zoom'), '110%');
      await tester.sendKeyEvent(LogicalKeyboardKey.minus);
      await tester.sendKeyEvent(LogicalKeyboardKey.minus);
      await tester.sendKeyEvent(LogicalKeyboardKey.minus);
      await tester.pump();
      expect(textOf(tester, 'memo-status-zoom'), '80%');
      await tester.sendKeyEvent(LogicalKeyboardKey.equal);
      await tester.pump();
      expect(textOf(tester, 'memo-status-zoom'), '90%');
      await tester.sendKeyEvent(LogicalKeyboardKey.digit0);
      await tester.sendKeyUpEvent(LogicalKeyboardKey.controlLeft);
      await tester.pump();
      expect(textOf(tester, 'memo-status-zoom'), '100%');
      // Ctrl 없이 휠은 확대하지 않는다.
      await tester.sendEventToBinding(pointer.scroll(const Offset(0, -40)));
      await tester.pump();
      expect(textOf(tester, 'memo-status-zoom'), '100%');
      expect(tester.takeException(), isNull);
    });

    for (final engine in ['Rust', 'Dart']) {
      testWidgets('Ctrl+F / Ctrl+H find and replace bar ($engine core)', (tester) async {
        final fake = FakeEditorBackend();
        await pumpEditor(
          tester,
          createCore: engine == 'Rust' ? (t) => _core(fake, t) : null,
          text: '복지 예산과 도로 예산, 예산안',
        );
        final body = tester.widget<TextField>(find.byKey(const ValueKey('memo-body'))).controller!;
        await tester.tap(find.byKey(const ValueKey('memo-body')));
        await tester.pump();
        body.selection = const TextSelection.collapsed(offset: 0);
        await tester.pump();
        await tester.sendKeyDownEvent(LogicalKeyboardKey.controlLeft);
        await tester.sendKeyEvent(LogicalKeyboardKey.keyF);
        await tester.sendKeyUpEvent(LogicalKeyboardKey.controlLeft);
        await tester.pumpAndSettle();
        expect(find.byKey(const ValueKey('memo-find-bar')), findsOneWidget);
        expect(find.byKey(const ValueKey('memo-replace-with')), findsNothing);

        await tester.enterText(find.byKey(const ValueKey('memo-find-query')), '예산');
        await tester.testTextInput.receiveAction(TextInputAction.done);
        await tester.pumpAndSettle();
        expect(body.selection, const TextSelection(baseOffset: 3, extentOffset: 5));
        expect(textOf(tester, 'memo-find-message'), '3개 일치');
        await tester.tap(find.byKey(const ValueKey('memo-find-word')));
        await tester.tap(find.byKey(const ValueKey('memo-find-next')));
        await tester.pumpAndSettle();
        expect(textOf(tester, 'memo-find-message'), '1개 일치'); // '예산과'·'예산안'은 낱말이 아님
        expect(body.selection, const TextSelection(baseOffset: 10, extentOffset: 12));
        await tester.tap(find.byKey(const ValueKey('memo-find-word')));
        await tester.tap(find.byKey(const ValueKey('memo-find-prev')));
        await tester.pumpAndSettle();
        expect(body.selection, const TextSelection(baseOffset: 3, extentOffset: 5));

        await tester.tap(find.byKey(const ValueKey('memo-find-toggle-replace')));
        await tester.pumpAndSettle();
        await tester.enterText(find.byKey(const ValueKey('memo-replace-with')), '결산');
        await tester.tap(find.byKey(const ValueKey('memo-replace-next')));
        await tester.pumpAndSettle();
        expect(body.text, '복지 결산과 도로 예산, 예산안');
        expect(body.selection, const TextSelection(baseOffset: 10, extentOffset: 12));
        await tester.tap(find.byKey(const ValueKey('memo-replace-all')));
        await tester.pumpAndSettle();
        expect(body.text, '복지 결산과 도로 결산, 결산안');
        expect(textOf(tester, 'memo-find-message'), '2개를 바꿨습니다.');
        await tester.tap(find.byKey(const ValueKey('memo-undo')));
        await tester.pumpAndSettle();
        expect(body.text, '복지 결산과 도로 예산, 예산안');

        await tester.enterText(find.byKey(const ValueKey('memo-find-query')), '없는말');
        await tester.tap(find.byKey(const ValueKey('memo-find-next')));
        await tester.pumpAndSettle();
        expect(textOf(tester, 'memo-find-message'), "'없는말'을(를) 찾을 수 없습니다.");
        await tester.tap(find.byKey(const ValueKey('memo-find-close')));
        await tester.pumpAndSettle();
        expect(find.byKey(const ValueKey('memo-find-bar')), findsNothing);
        if (engine == 'Rust') expect(fake.commands, containsAll(['edit_find', 'edit_find_all', 'edit_replace_next', 'edit_replace_all']));
        expect(tester.takeException(), isNull);
      });
    }

    testWidgets('notebook +메모 추가 uses the Rust core when the API has an editor backend', (tester) async {
      tester.view.physicalSize = const Size(1400, 800);
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.reset);
      final fake = FakeEditorBackend();
      final api = InMemoryNotebookApi()..editorBackend = fake.call;
      await api.createNotebook('연구');
      await tester.pumpWidget(MaterialApp(home: NotebookScreen(api: api)));
      await tester.pumpAndSettle();
      await tester.tap(find.byKey(const ValueKey('nb-memo-add')));
      await tester.pumpAndSettle();
      expect(fake.commands.first, 'edit_open');
      expect(find.byTooltip('편집 엔진: Rust 코어(klib)'), findsOneWidget);
      await tester.enterText(find.byKey(const ValueKey('memo-body')), '공원 예산');
      await tester.pumpAndSettle();
      expect(fake.docs.values.single.text, '공원 예산');
      await tester.pageBack();
      await tester.pumpAndSettle();
      expect(fake.commands.last, 'edit_close');
      expect(tester.takeException(), isNull);
    });
  });
}
