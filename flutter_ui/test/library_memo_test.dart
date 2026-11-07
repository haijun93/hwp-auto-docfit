// 자료함 '+메모'와 글 자료 더블클릭 고치기(노트북과 같은 메모 편집기 재사용).
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:docfit_ui/features/library/library_api.dart';
import 'package:docfit_ui/features/library/library_screen.dart';

import 'fake_editor_backend.dart';

class _FakeOpener implements LibraryOpenApi {
  final calls = <String>[];

  @override
  Future<LibraryOpenResult> openItem({String? itemId, required LibraryItemKind kind, required String source, bool confirmed = false}) async {
    calls.add(source);
    return const LibraryOpenResult(ok: true);
  }
}

class _FailingMemoApi extends InMemoryLibraryApi {
  bool failRead = false;
  bool failUpdate = false;

  @override
  Future<String> readItemText(String itemId) {
    if (failRead) throw StateError('사본을 찾을 수 없습니다');
    return super.readItemText(itemId);
  }

  @override
  Future<void> updateItemText(String itemId, {required String title, required String text}) {
    if (failUpdate) throw StateError('디스크가 가득 찼습니다');
    return super.updateItemText(itemId, title: title, text: text);
  }
}

Future<_FakeOpener> _pump(WidgetTester tester, LibraryApi api) async {
  tester.view.physicalSize = const Size(1400, 900);
  tester.view.devicePixelRatio = 1;
  addTearDown(tester.view.reset);
  final opener = _FakeOpener();
  await tester.pumpWidget(MaterialApp(home: LibraryScreen(api: api, openApi: opener)));
  await tester.pumpAndSettle();
  return opener;
}

Finder _card(String id) => find.byKey(ValueKey('libraryItem-$id'));
final _page = find.byKey(const ValueKey('libraryMemoPage'));

Future<void> _doubleTap(WidgetTester tester, Finder finder) async {
  await tester.tap(finder);
  await tester.pump(const Duration(milliseconds: 60));
  await tester.tap(finder);
  await tester.pumpAndSettle();
}

Future<void> _save(WidgetTester tester) async {
  await tester.tap(find.byKey(const ValueKey('memo-save')));
  await tester.pumpAndSettle();
}

void main() {
  testWidgets('+메모로 쓴 메모를 저장하면 핵심자료에 텍스트 자료로 들어간다', (tester) async {
    final api = InMemoryLibraryApi();
    final box = await api.createBox('메모함');
    await _pump(tester, api);

    await tester.tap(find.byKey(const ValueKey('libraryAddMemo')));
    await tester.pumpAndSettle();
    expect(_page, findsOneWidget);
    expect(find.text('새 메모'), findsOneWidget);
    expect(find.text("작성한 메모를 저장하면 '핵심자료'에 텍스트 자료로 들어갑니다."), findsOneWidget);
    await tester.enterText(find.byKey(const ValueKey('memo-title')), '회의 정리');
    await tester.enterText(find.byKey(const ValueKey('memo-body')), '예산 확정');
    await tester.tap(find.byKey(const ValueKey('memo-bold')));
    await tester.pump(const Duration(seconds: 1));
    await _save(tester);

    expect(_page, findsNothing);
    expect(find.text('메모를 자료함에 넣었습니다.'), findsOneWidget);
    final item = (await api.listItems(box.id)).single;
    expect((item.kind, item.space, item.title), (LibraryItemKind.text, LibrarySpace.core, '회의 정리'));
    expect(item.text, contains('예산 확정'));
    expect(_card(item.id), findsOneWidget);
    expect(find.text('+메모'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('+메모를 저장하지 않고 닫으면 초안이 남고, 휴지통은 초안을 버린다', (tester) async {
    final api = InMemoryLibraryApi();
    final box = await api.createBox('초안');
    await _pump(tester, api);

    await tester.tap(find.byKey(const ValueKey('libraryAddMemo')));
    await tester.pumpAndSettle();
    await tester.enterText(find.byKey(const ValueKey('memo-title')), '쓰다 만 메모');
    await tester.enterText(find.byKey(const ValueKey('memo-body')), '내용 조금');
    await tester.pump(const Duration(seconds: 1));
    await tester.pageBack();
    await tester.pumpAndSettle();
    expect(await api.listItems(box.id), isEmpty);
    expect(find.text('+메모(초안)'), findsOneWidget);

    await tester.tap(find.byKey(const ValueKey('libraryAddMemo')));
    await tester.pumpAndSettle();
    expect(find.text('쓰다 만 메모'), findsOneWidget);
    expect(find.text('내용 조금'), findsOneWidget);

    // 빈 메모는 저장하지 않는다.
    await tester.enterText(find.byKey(const ValueKey('memo-body')), '   ');
    await _save(tester);
    expect(find.text('메모에 내용이 없습니다.'), findsOneWidget);
    expect(_page, findsOneWidget);

    await tester.tap(find.byKey(const ValueKey('memo-delete')));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const ValueKey('memo-delete-ok')));
    await tester.pumpAndSettle();
    expect(_page, findsNothing);
    expect(find.text('+메모'), findsOneWidget);
    expect(await api.listItems(box.id), isEmpty);
  });

  testWidgets('글 자료를 더블클릭하면 같은 편집기로 열어 고치고, 파일은 연결 프로그램으로 연다', (tester) async {
    final api = InMemoryLibraryApi();
    final box = await api.createBox('고치기');
    final text = await api.addItem(boxId: box.id, kind: LibraryItemKind.text, title: '기존 메모', space: LibrarySpace.basis, x: 16, y: 16, text: '처음 내용');
    final note = await api.addItem(boxId: box.id, kind: LibraryItemKind.note, title: '노트', space: LibrarySpace.temp, x: 16, y: 16, text: '노트 내용');
    final file = await api.addItem(boxId: box.id, kind: LibraryItemKind.file, title: '보고서.hwpx', space: LibrarySpace.core, x: 16, y: 16, source: 'C:/자료/보고서.hwpx');
    final opener = await _pump(tester, api);

    await _doubleTap(tester, _card(text.id));
    expect(_page, findsOneWidget);
    expect(find.text('기존 메모'), findsOneWidget);
    expect(find.text('처음 내용'), findsOneWidget);
    expect(find.byKey(const ValueKey('memo-delete')), findsNothing, reason: '고치기 화면에서는 자료를 지우지 않는다');
    await tester.enterText(find.byKey(const ValueKey('memo-title')), '고친 메모');
    await tester.enterText(find.byKey(const ValueKey('memo-body')), '고친 내용');
    await _save(tester);
    expect(_page, findsNothing);
    expect(find.text('메모를 저장했습니다.'), findsOneWidget);
    final edited = (await api.listItems(box.id)).firstWhere((i) => i.id == text.id);
    expect((edited.title, edited.text, edited.space, edited.kind), ('고친 메모', '고친 내용', LibrarySpace.basis, LibraryItemKind.text));
    expect(find.text('고친 메모'), findsOneWidget);

    // 닫기만 하면 바뀌지 않는다.
    await _doubleTap(tester, _card(note.id));
    expect(find.text('노트 내용'), findsOneWidget);
    await tester.enterText(find.byKey(const ValueKey('memo-body')), '버릴 내용');
    await tester.pageBack();
    await tester.pumpAndSettle();
    expect(await api.readItemText(note.id), '노트 내용');

    await _doubleTap(tester, _card(file.id));
    expect(_page, findsNothing);
    expect(opener.calls, ['C:/자료/보고서.hwpx']);
    expect(tester.takeException(), isNull);
  });

  testWidgets('글 자료를 못 읽거나 못 고치면 알리고 원래 내용을 지킨다', (tester) async {
    final api = _FailingMemoApi();
    final box = await api.createBox('실패');
    final item = await api.addItem(boxId: box.id, kind: LibraryItemKind.text, title: '메모', space: LibrarySpace.core, x: 16, y: 16, text: '원래 내용');
    await _pump(tester, api);

    api.failRead = true;
    await _doubleTap(tester, _card(item.id));
    expect(_page, findsNothing);
    expect(find.text('메모를 열지 못했습니다: 사본을 찾을 수 없습니다'), findsOneWidget);

    api.failRead = false;
    api.failUpdate = true;
    await _doubleTap(tester, _card(item.id));
    await tester.enterText(find.byKey(const ValueKey('memo-body')), '새 내용');
    await _save(tester);
    expect(_page, findsOneWidget, reason: '저장 실패면 편집기를 닫지 않는다');
    expect(find.text('디스크가 가득 찼습니다'), findsOneWidget);
    expect(await api.readItemText(item.id), '원래 내용');
  });

  testWidgets('편집 통로가 있으면 자료함 메모 편집기도 klib 편집 코어를 쓴다', (tester) async {
    final backend = FakeEditorBackend();
    final api = InMemoryLibraryApi()..editorBackend = backend.call;
    final box = await api.createBox('코어');
    final item = await api.addItem(boxId: box.id, kind: LibraryItemKind.text, title: '메모', space: LibrarySpace.core, x: 16, y: 16, text: '가나다');
    await _pump(tester, api);

    await _doubleTap(tester, _card(item.id));
    await tester.pump(const Duration(milliseconds: 100));
    expect(backend.commands, contains('edit_open'));
    expect(backend.log.firstWhere((r) => r['cmd'] == 'edit_open')['text'], '가나다');
    await tester.enterText(find.byKey(const ValueKey('memo-body')), '가나다라');
    await tester.pump(const Duration(seconds: 1));
    expect(backend.commands, contains('edit_replace'));
    await _save(tester);
    expect(await api.readItemText(item.id), '가나다라');
    expect(tester.takeException(), isNull);
  });

  test('글 자료가 아니면 메모 편집기로 읽거나 고치지 않는다(메모리 구현)', () async {
    final api = InMemoryLibraryApi();
    final box = await api.createBox('종류');
    final file = await api.addItem(boxId: box.id, kind: LibraryItemKind.file, title: 'a.txt', space: LibrarySpace.core, x: 0, y: 0, source: 'C:/a.txt');
    expect(() => api.readItemText(file.id), throwsStateError);
    expect(() => api.updateItemText(file.id, title: 'b', text: 'x'), throwsStateError);
    final text = await api.addItem(boxId: box.id, kind: LibraryItemKind.text, title: '이름', space: LibrarySpace.core, x: 0, y: 0, text: 'x');
    await api.updateItemText(text.id, title: '  ', text: 'y');
    final after = (await api.listItems(box.id)).firstWhere((i) => i.id == text.id);
    expect((after.title, after.text), ('이름', 'y'));
  });

  test('BridgeLibraryApi는 item_text_get/item_text_set과 자료함 통로의 edit_* 명령을 보낸다', () async {
    final sent = <(String, Object?)>[];
    final api = BridgeLibraryApi((method, args) async {
      sent.add((method, args.single));
      final cmd = (args.single as Map)['cmd'];
      return switch (cmd) {
        'item_text_get' => {'ok': true, 'id': 7, 'content': '# 메모\n본문', 'display_name': '메모'},
        'edit_open' => {'ok': true, 'doc': 1},
        _ => {'ok': true},
      };
    });
    expect(await api.readItemText('7'), '# 메모\n본문');
    await api.updateItemText('7', title: ' 회의 ', text: '고친 본문');
    final response = await api.memoEditorBackend({'cmd': 'edit_open', 'text': '가'});
    expect(response['doc'], 1);
    expect(sent.map((e) => e.$1), everyElement('library'));
    expect(sent.map((e) => e.$2).toList(), [
      {'cmd': 'item_text_get', 'id': 7},
      {'cmd': 'item_text_set', 'id': 7, 'display_name': '회의', 'content': '고친 본문'},
      {'cmd': 'edit_open', 'text': '가'},
    ]);

    final failing = BridgeLibraryApi((method, args) async => throw StateError('브리지 없음'));
    expect((await failing.memoEditorBackend({'cmd': 'edit_ping'}))['ok'], isFalse);
    final refusing = BridgeLibraryApi((method, args) async => {'ok': false, 'message': '글 자료(text·note)만'});
    await expectLater(refusing.readItemText('3'), throwsA(isA<StateError>()));
  });
}
