import 'package:flutter/gestures.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:docfit_ui/features/library/library_api.dart';
import 'package:docfit_ui/features/library/library_screen.dart';
import 'package:docfit_ui/features/notebook/notebook_api.dart';
import 'package:docfit_ui/features/notebook/notebook_screen.dart';

const _path = r'C:\자료\예산보고.txt';

Future<void> _setSize(WidgetTester tester, double width) async {
  tester.view.physicalSize = Size(width, 900);
  tester.view.devicePixelRatio = 1;
  addTearDown(tester.view.reset);
}

/// 자료함 1개(파일 항목 1개·글 항목 1개)와 노트북 1개.
Future<(InMemoryLibraryApi, InMemoryNotebookApi, int)> _fixture() async {
  final library = InMemoryLibraryApi(
    initialBoxes: const [LibraryBox(id: 'box_1', name: '예산 자료'), LibraryBox(id: 'box_2', name: '다른 자료함')],
    initialItems: const [
      LibraryItem(id: 'item_1', boxId: 'box_1', kind: LibraryItemKind.file, title: '예산보고.txt',
          space: LibrarySpace.core, x: 16, y: 16, source: _path),
      LibraryItem(id: 'item_2', boxId: 'box_1', kind: LibraryItemKind.text, title: '메모',
          space: LibrarySpace.basis, x: 16, y: 16, text: '메모 내용'),
      LibraryItem(id: 'item_3', boxId: 'box_2', kind: LibraryItemKind.file, title: '도로계획.txt',
          space: LibrarySpace.reference, x: 16, y: 16, source: r'C:\자료\도로계획.txt'),
    ],
  );
  final notebooks = InMemoryNotebookApi(
    library: library,
    fileContents: const {_path: '2027년 예산 개요\n복지 예산은 120억 원으로 늘었다.', r'C:\자료\도로계획.txt': '도로 정비 계획'},
  );
  final nbId = await notebooks.createNotebook('예산 연구');
  return (library, notebooks, nbId);
}

String _status(WidgetTester tester) =>
    (tester.widget<Text>(find.byKey(const ValueKey('libraryStatus')))).data ?? '';

/// 카드의 메뉴 단추를 누른다. 카드가 두 번 누르기도 받으므로 그 대기 시간(300ms)을 넘겨야 눌림이 정해진다.
Future<void> _tapMenuButton(WidgetTester tester, String itemId) async {
  await tester.tap(find.byKey(ValueKey('libraryItemMenu-$itemId')));
  await tester.pump(const Duration(milliseconds: 400));
}

Future<void> _addViaMenu(WidgetTester tester, String itemId, int nbId, {bool rightClick = false}) async {
  if (rightClick) {
    await tester.tap(find.byKey(ValueKey('libraryItem-$itemId')), buttons: kSecondaryButton);
  } else {
    await _tapMenuButton(tester, itemId);
  }
  await tester.pumpAndSettle();
  await tester.tap(find.byKey(const ValueKey('libraryMenuAddToNotebook')));
  await tester.pumpAndSettle();
  await tester.tap(find.byKey(ValueKey('libraryNbPick-$nbId')));
  await tester.pumpAndSettle();
}

void main() {
  group('자료함 → 노트북 출처로 추가', () {
    testWidgets('카드 단추 메뉴로 추가하고, 다시 추가하면 이미 있음을 알린다', (tester) async {
      await _setSize(tester, 1280);
      final (library, notebooks, nbId) = await _fixture();
      await tester.pumpWidget(MaterialApp(home: LibraryScreen(api: library, notebookApi: notebooks)));
      await tester.pumpAndSettle();

      await _addViaMenu(tester, 'item_1', nbId);
      expect(_status(tester), '“예산보고.txt”을(를) “예산 연구” 노트북 출처로 추가했습니다.');
      final sources = await notebooks.listSources(nbId);
      expect(sources, hasLength(1));
      expect(sources.single.itemId, 'item_1');
      expect(sources.single.paragraphCount, 2);

      // 오른쪽 클릭 메뉴로 같은 항목을 또 넣으면 새 출처를 만들지 않는다.
      await _addViaMenu(tester, 'item_1', nbId, rightClick: true);
      expect(_status(tester), '이미 “예산 연구” 노트북 출처에 있습니다.');
      expect(await notebooks.listSources(nbId), hasLength(1));
    });

    testWidgets('파일 경로가 없는 글 자료는 노트북을 고르기 전에 막는다', (tester) async {
      await _setSize(tester, 1280);
      final (library, notebooks, nbId) = await _fixture();
      await tester.pumpWidget(MaterialApp(home: LibraryScreen(api: library, notebookApi: notebooks)));
      await tester.pumpAndSettle();

      await _tapMenuButton(tester, 'item_2');
      await tester.pumpAndSettle();
      await tester.tap(find.byKey(const ValueKey('libraryMenuAddToNotebook')));
      await tester.pumpAndSettle();
      expect(find.byKey(ValueKey('libraryNbPick-$nbId')), findsNothing);
      expect(_status(tester), '파일 경로가 있는 자료만 노트북 출처로 추가할 수 있습니다.');
      expect(await notebooks.listSources(nbId), isEmpty);
    });

    testWidgets('노트북이 없으면 고르기 창에서 새로 만들어 넣는다', (tester) async {
      await _setSize(tester, 1280);
      final library = InMemoryLibraryApi(
        initialBoxes: const [LibraryBox(id: 'box_1', name: '예산 자료')],
        initialItems: const [
          LibraryItem(id: 'item_1', boxId: 'box_1', kind: LibraryItemKind.file, title: '예산보고.txt',
              space: LibrarySpace.core, x: 16, y: 16, source: _path),
        ],
      );
      final notebooks = InMemoryNotebookApi(library: library);
      await tester.pumpWidget(MaterialApp(home: LibraryScreen(api: library, notebookApi: notebooks)));
      await tester.pumpAndSettle();

      await _tapMenuButton(tester, 'item_1');
      await tester.pumpAndSettle();
      await tester.tap(find.byKey(const ValueKey('libraryMenuAddToNotebook')));
      await tester.pumpAndSettle();
      expect(find.text('노트북이 없습니다. 아래에서 새로 만드세요.'), findsOneWidget);
      await tester.enterText(find.byKey(const ValueKey('libraryNbPickNewName')), '새 연구');
      await tester.tap(find.byKey(const ValueKey('libraryNbPickCreate')));
      await tester.pumpAndSettle();

      final created = (await notebooks.listNotebooks()).single;
      expect(created.name, '새 연구');
      expect((await notebooks.listSources(created.id)).single.itemId, 'item_1');
      expect(_status(tester), contains('“새 연구” 노트북 출처로 추가했습니다.'));
    });

    testWidgets('노트북 API가 없으면 메뉴에 항목이 없다', (tester) async {
      await _setSize(tester, 1280);
      final (library, _, _) = await _fixture();
      await tester.pumpWidget(MaterialApp(home: LibraryScreen(api: library)));
      await tester.pumpAndSettle();
      await _tapMenuButton(tester, 'item_1');
      await tester.pumpAndSettle();
      expect(find.text('이름 바꾸기'), findsOneWidget);
      expect(find.byKey(const ValueKey('libraryMenuAddToNotebook')), findsNothing);
    });
  });

  group('노트북 출처 → 자료함에서 보기', () {
    testWidgets('자료함 화면을 열어 그 자료함을 고르고 항목을 강조한다', (tester) async {
      await _setSize(tester, 1280);
      final (library, notebooks, nbId) = await _fixture();
      final linked = await notebooks.addSourceFromItem(nbId, 'item_3');
      final plain = await notebooks.addSource(nbId, _path);
      await tester.pumpWidget(MaterialApp(home: NotebookScreen(api: notebooks, library: library)));
      await tester.pumpAndSettle();

      // 자료함에서 온 출처에만 단추가 있다.
      expect(find.byKey(ValueKey('nb-source-in-library-${linked.sourceId}')), findsOneWidget);
      expect(find.byKey(ValueKey('nb-source-in-library-$plain')), findsNothing);

      await tester.tap(find.byKey(ValueKey('nb-source-in-library-${linked.sourceId}')));
      await tester.pumpAndSettle();

      expect(find.byType(LibraryScreen), findsOneWidget);
      expect(find.text('노트북으로'), findsOneWidget);
      // 첫 자료함(box_1)이 아니라 항목이 든 box_2가 골라져 있다.
      expect(tester.widget<ListTile>(find.byKey(const ValueKey('libraryBox-box_2'))).selected, isTrue);
      expect(tester.widget<ListTile>(find.byKey(const ValueKey('libraryBox-box_1'))).selected, isFalse);
      expect(_status(tester), '“도로계획.txt” 항목입니다.');
      final card = tester.widget<Card>(
        find.descendant(of: find.byKey(const ValueKey('libraryItem-item_3')), matching: find.byType(Card)),
      );
      expect((card.shape as RoundedRectangleBorder).side.color, Colors.blue);

      // 돌아가면 노트북 화면이 그대로 있다.
      await tester.tap(find.byKey(const ValueKey('host-page-back')));
      await tester.pumpAndSettle();
      expect(find.byType(LibraryScreen), findsNothing);
      expect(find.byKey(ValueKey('nb-source-${linked.sourceId}')), findsOneWidget);
    });

    testWidgets('항목이 지워졌으면 자료함을 열지 않고 까닭을 보인다', (tester) async {
      await _setSize(tester, 1280);
      final (library, notebooks, nbId) = await _fixture();
      final linked = await notebooks.addSourceFromItem(nbId, 'item_1');
      await library.deleteItem('item_1');
      await tester.pumpWidget(MaterialApp(home: NotebookScreen(api: notebooks, library: library)));
      await tester.pumpAndSettle();

      await tester.tap(find.byKey(ValueKey('nb-source-in-library-${linked.sourceId}')));
      await tester.pumpAndSettle();
      expect(find.byType(LibraryScreen), findsNothing);
      expect(find.text('자료함 항목이 삭제되었습니다.'), findsOneWidget);
    });

    testWidgets('openLibraryItem을 주면 그것으로 자료함·항목 id를 넘긴다', (tester) async {
      await _setSize(tester, 1280);
      final (library, notebooks, nbId) = await _fixture();
      final linked = await notebooks.addSourceFromItem(nbId, 'item_1');
      final opened = <(String, String)>[];
      await tester.pumpWidget(MaterialApp(
        home: NotebookScreen(
          api: notebooks,
          library: library,
          openLibraryItem: (context, boxId, itemId) async => opened.add((boxId, itemId)),
        ),
      ));
      await tester.pumpAndSettle();
      await tester.tap(find.byKey(ValueKey('nb-source-in-library-${linked.sourceId}')));
      await tester.pumpAndSettle();
      expect(opened, [('box_1', 'item_1')]);
    });

    testWidgets('처음 고를 자료함이 없으면 알리고 첫 자료함을 연다', (tester) async {
      await _setSize(tester, 1280);
      final (library, _, _) = await _fixture();
      await tester.pumpWidget(MaterialApp(
        home: LibraryScreen(api: library, initialBoxId: 'box_9', initialItemId: 'item_9'),
      ));
      await tester.pumpAndSettle();
      expect(tester.widget<ListTile>(find.byKey(const ValueKey('libraryBox-box_1'))).selected, isTrue);
      expect(_status(tester), '자료함을 찾을 수 없습니다(삭제되었을 수 있습니다).');
    });

    testWidgets('자료함은 있으나 항목이 없으면 그렇게 알린다', (tester) async {
      await _setSize(tester, 1280);
      final (library, _, _) = await _fixture();
      await tester.pumpWidget(MaterialApp(
        home: LibraryScreen(api: library, initialBoxId: 'box_2', initialItemId: 'item_9'),
      ));
      await tester.pumpAndSettle();
      expect(tester.widget<ListTile>(find.byKey(const ValueKey('libraryBox-box_2'))).selected, isTrue);
      expect(_status(tester), '자료함 항목을 찾을 수 없습니다(삭제되었을 수 있습니다).');
    });
  });

  group('BridgeNotebookApi 항목 연결 명령', () {
    test('nb_source_from_item은 정수 item_id로 보내고 reused를 읽는다', () async {
      final sent = <Map>[];
      final api = BridgeNotebookApi((method, args) async {
        expect(method, 'notebook');
        final request = args.single as Map;
        sent.add(request);
        return {'ok': true, 'id': 7, 'paragraph_count': 3, 'reused': request['item_id'] == 5};
      });
      final first = await api.addSourceFromItem(2, '5');
      expect((first.sourceId, first.reused), (7, true));
      final second = await api.addSourceFromItem(2, '6');
      expect(second.reused, isFalse);
      expect(sent.first, {'cmd': 'nb_source_from_item', 'notebook_id': 2, 'item_id': 5});
      expect(() => api.addSourceFromItem(2, 'item_x'), throwsStateError);
    });

    test('nb_source_item의 found·사유와 nb_source_list의 item_id를 읽는다', () async {
      final api = BridgeNotebookApi((method, args) async {
        final request = args.single as Map;
        return switch (request['cmd']) {
          'nb_source_item' when request['source_id'] == 1 => {
            'ok': true, 'found': true, 'item_id': 5, 'box_id': 3, 'display_name': '예산보고.txt', 'source_path': _path,
          },
          'nb_source_item' => {'ok': true, 'found': false, 'item_id': 6, 'reason': '자료함 항목이 삭제되었습니다.'},
          'nb_source_list' => {
            'ok': true,
            'sources': [
              {'id': 1, 'display_name': 'a', 'kind': 'txt', 'status': 'ready', 'paragraph_count': 1, 'item_id': 5},
              {'id': 2, 'display_name': 'b', 'kind': 'txt', 'status': 'ready', 'paragraph_count': 1, 'item_id': null},
            ],
          },
          _ => {'ok': false, 'message': '알 수 없는 명령'},
        };
      });
      final found = await api.sourceItem(2, 1);
      expect((found.found, found.boxId, found.itemId, found.displayName), (true, '3', '5', '예산보고.txt'));
      final gone = await api.sourceItem(2, 9);
      expect((gone.found, gone.reason), (false, '자료함 항목이 삭제되었습니다.'));
      final sources = await api.listSources(2);
      expect(sources.map((s) => s.itemId), ['5', null]);
    });
  });
}
