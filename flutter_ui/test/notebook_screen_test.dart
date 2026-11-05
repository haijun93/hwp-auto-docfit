import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:docfit_ui/features/notebook/notebook_api.dart';
import 'package:docfit_ui/features/notebook/notebook_screen.dart';
import 'package:docfit_ui/features/workspace/tab_navigation_shell.dart';

const _path = r'C:\자료\예산보고.txt';
const _content = '2027년 예산 개요\n복지 예산은 120억 원으로 늘었다.\n도로 정비 계획';

Future<void> _setSize(WidgetTester tester, double width) async {
  tester.view.physicalSize = Size(width, 800);
  tester.view.devicePixelRatio = 1;
  addTearDown(tester.view.reset);
}

Future<void> _enterDialog(WidgetTester tester, String fieldKey, String okKey, String text) async {
  await tester.enterText(find.byKey(ValueKey(fieldKey)), text);
  await tester.tap(find.byKey(ValueKey(okKey)));
  await tester.pumpAndSettle();
}

/// 출처 추가 → 근거 찾기 → 노트에 인용 → 저장 → Markdown 내보내기.
Future<void> _flow(WidgetTester tester, InMemoryNotebookApi api, {required bool narrow}) async {
  await tester.pumpWidget(MaterialApp(home: NotebookScreen(api: api)));
  await tester.pumpAndSettle();

  await tester.tap(find.byKey(const ValueKey('nb-create-empty')));
  await tester.pumpAndSettle();
  await _enterDialog(tester, 'nb-create-name', 'nb-create-ok', '예산 연구');
  expect(find.text('예산 연구'), findsOneWidget);

  await tester.tap(find.byKey(const ValueKey('nb-source-add')));
  await tester.pumpAndSettle();
  await _enterDialog(tester, 'nb-source-path', 'nb-source-path-ok', _path);
  expect(find.text('예산보고.txt'), findsOneWidget);
  expect(find.text('문단 3개'), findsOneWidget);

  if (narrow) {
    await tester.tap(find.byKey(const ValueKey('nb-tab-evidence')));
    await tester.pumpAndSettle();
  }
  await tester.enterText(find.byKey(const ValueKey('nb-query')), '복지 예산');
  await tester.tap(find.byKey(const ValueKey('nb-search-run')));
  await tester.pumpAndSettle();
  expect(find.byKey(const ValueKey('nb-hit-0')), findsOneWidget);
  expect(find.byKey(const ValueKey('nb-hit-1')), findsOneWidget);
  // 두 핵심어를 모두 가진 문단이 먼저 나온다.
  expect(
    find.descendant(of: find.byKey(const ValueKey('nb-hit-0')), matching: find.textContaining('120억')),
    findsOneWidget,
  );

  await tester.tap(find.byKey(const ValueKey('nb-cite-0')));
  await tester.pumpAndSettle();

  if (narrow) {
    await tester.tap(find.byKey(const ValueKey('nb-tab-notes')));
    await tester.pumpAndSettle();
  }
  expect(find.byKey(const ValueKey('nb-citation-0')), findsOneWidget);
  await tester.enterText(find.byKey(const ValueKey('nb-note-title')), '복지 예산 메모');
  await tester.enterText(find.byKey(const ValueKey('nb-note-body')), '복지 예산 증가 확인');
  await tester.ensureVisible(find.byKey(const ValueKey('nb-note-save')));
  await tester.tap(find.byKey(const ValueKey('nb-note-save')));
  await tester.pumpAndSettle();
  expect(find.text('노트를 저장했습니다.'), findsOneWidget);

  final notes = await api.listNotes((await api.listNotebooks()).single.id);
  expect(notes, hasLength(1));
  expect(notes.single.title, '복지 예산 메모');
  expect(notes.single.citations.single.quote, '복지 예산은 120억 원으로 늘었다.');
  expect(notes.single.citations.single.paragraphOrdinal, 1);

  await tester.ensureVisible(find.byKey(const ValueKey('nb-note-export')));
  await tester.tap(find.byKey(const ValueKey('nb-note-export')));
  await tester.pumpAndSettle();
  expect(find.textContaining('> 복지 예산은 120억 원으로 늘었다.'), findsOneWidget);
  expect(tester.takeException(), isNull);
}

void main() {
  for (final width in [1000.0, 1400.0]) {
    testWidgets('three-pane notebook flow at width $width', (tester) async {
      await _setSize(tester, width);
      final api = InMemoryNotebookApi(fileContents: {_path: _content});
      await _flow(tester, api, narrow: false);
      expect(find.byType(TabBar), findsNothing);
    });
  }

  testWidgets('narrow notebook uses tabs without overflow', (tester) async {
    await _setSize(tester, 700);
    final api = InMemoryNotebookApi(fileContents: {_path: _content});
    await _flow(tester, api, narrow: true);
  });

  testWidgets('transform shows rule-based rows and preview highlights paragraph', (tester) async {
    await _setSize(tester, 1400);
    final api = InMemoryNotebookApi(fileContents: {_path: _content});
    final nb = await api.createNotebook('연구');
    await api.addSource(nb, _path);
    await tester.pumpWidget(MaterialApp(home: NotebookScreen(api: api)));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const ValueKey('nb-mid-transform')));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const ValueKey('nb-transform-numbers')));
    await tester.pumpAndSettle();
    expect(find.text('2027년 예산 개요'), findsOneWidget);
    expect(find.text('도로 정비 계획'), findsNothing);
    await tester.tap(find.text('복지 예산은 120억 원으로 늘었다.'));
    await tester.pumpAndSettle();
    expect(find.byKey(const ValueKey('nb-preview-1')), findsOneWidget);
  });

  testWidgets('bridge api sends nb commands through notebook bridge', (tester) async {
    final calls = <(String, Map)>[];
    final api = BridgeNotebookApi((method, args) async {
      final request = args.single as Map;
      calls.add((method, request));
      return switch (request['cmd']) {
        'nb_source_add' => {'ok': true, 'id': 5, 'paragraph_count': 3},
        'nb_search' => {
          'ok': true,
          'terms': ['복지'],
          'results': [
            {'source_id': 5, 'ordinal': 1, 'display_name': 'a.txt', 'location': '', 'score': 2.5, 'body': '복지'},
          ],
        },
        _ => {'ok': false, 'message': '실패'},
      };
    });
    expect(await api.addSource(1, _path), 5);
    final hits = await api.search(1, '복지', sourceIds: [5]);
    expect(hits.single.score, 2.5);
    expect(calls.map((c) => c.$1), everyElement('notebook'));
    expect(calls.first.$2, {'cmd': 'nb_source_add', 'notebook_id': 1, 'source_path': _path});
    expect(calls.last.$2['source_ids'], [5]);
    expect(() => api.listNotebooks(), throwsA(isA<StateError>()));
  });

  testWidgets('developer sidebar shows notebook button next to library', (tester) async {
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: WorkspaceTabBar(
            labels: const ['문서편집'],
            icons: const [Icons.description],
            selectedIndex: 0,
            onSelected: (_) {},
            scrollController: ScrollController(),
            developerMode: true,
            libraryScreen: const SizedBox(),
            notebookScreen: NotebookScreen(api: InMemoryNotebookApi()),
          ),
        ),
      ),
    );
    await tester.pump();
    expect(find.byKey(const ValueKey('notebook-open')), findsOneWidget);
    await tester.tap(find.byKey(const ValueKey('notebook-open')));
    await tester.pumpAndSettle();
    expect(find.byType(NotebookScreen), findsOneWidget);
  });

  testWidgets('notebook button is hidden outside developer mode', (tester) async {
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: WorkspaceTabBar(
            labels: const ['문서편집'],
            icons: const [Icons.description],
            selectedIndex: 0,
            onSelected: (_) {},
            scrollController: ScrollController(),
            notebookScreen: NotebookScreen(api: InMemoryNotebookApi()),
          ),
        ),
      ),
    );
    await tester.pump();
    expect(find.byKey(const ValueKey('notebook-open')), findsNothing);
  });
}
