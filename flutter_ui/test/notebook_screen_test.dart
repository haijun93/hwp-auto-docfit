import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:docfit_ui/features/library/library_api.dart';
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

/// 출처 추가 → 본문검색 → 노트에 인용 → 저장 → Markdown 내보내기.
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

  await _chooseExport(tester, 'nb-export-md');
  expect(find.textContaining('> 복지 예산은 120억 원으로 늘었다.'), findsOneWidget);
  await tester.tap(find.text('닫기'));
  await tester.pumpAndSettle();

  // 같은 내보내기 메뉴의 HWPX(한/글): 저장 위치를 고르면 저장 경로를, 취소하면 취소 문구를 보인다.
  await _chooseExport(tester, 'nb-export-hwpx');
  expect(find.text('한/글 문서로 저장했습니다: memory://복지 예산 메모.hwpx'), findsOneWidget);
  expect(api.hwpxExports.single.$2, notes.single.id);
  api.cancelNextHwpxExport = true;
  await _chooseExport(tester, 'nb-export-hwpx');
  expect(find.text('HWPX 내보내기를 취소했습니다.'), findsOneWidget);
  expect(api.hwpxExports, hasLength(1));
  expect(tester.takeException(), isNull);
}

Future<void> _chooseExport(WidgetTester tester, String item) async {
  await tester.ensureVisible(find.byKey(const ValueKey('nb-note-export')));
  await tester.tap(find.byKey(const ValueKey('nb-note-export')));
  await tester.pumpAndSettle();
  expect(find.text('HWPX(한/글)'), findsOneWidget);
  await tester.tap(find.byKey(ValueKey(item)));
  await tester.pumpAndSettle();
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

  testWidgets('dropped files become sources and drop watching follows the screen', (tester) async {
    await _setSize(tester, 1400);
    const other = r'C:\자료\도로.md';
    final api = InMemoryNotebookApi(fileContents: {_path: _content, other: '도로 정비\n교량 보수'});
    await api.createNotebook('연구');
    void Function()? onDrop;
    var stopped = false;
    await tester.pumpWidget(
      MaterialApp(
        home: NotebookScreen(
          api: api,
          watchDropEvents: (callback) {
            onDrop = callback;
            return () => stopped = true;
          },
        ),
      ),
    );
    await tester.pumpAndSettle();
    expect(api.watchingDrops, isTrue);

    api.queueDrop([_path, other, '  ']);
    onDrop!();
    await tester.pumpAndSettle();
    expect(find.text('예산보고.txt'), findsOneWidget);
    expect(find.text('도로.md'), findsOneWidget);
    expect(find.text('출처 2개를 추가했습니다.'), findsOneWidget);
    expect(await api.takeDroppedPaths(), isEmpty);

    await tester.pumpWidget(const MaterialApp(home: SizedBox()));
    await tester.pumpAndSettle();
    expect(stopped, isTrue);
    expect(api.watchingDrops, isFalse);
  });

  testWidgets('import file items from library as sources', (tester) async {
    await _setSize(tester, 1400);
    final api = InMemoryNotebookApi(fileContents: {_path: _content});
    await api.createNotebook('연구');
    LibraryItem item(String id, LibraryItemKind kind, String title, {String? source}) => LibraryItem(
      id: id,
      boxId: 'box_1',
      kind: kind,
      title: title,
      space: LibrarySpace.core,
      x: 0,
      y: 0,
      source: source,
    );
    final library = InMemoryLibraryApi(
      initialBoxes: const [LibraryBox(id: 'box_1', name: '예산 자료')],
      initialItems: [
        item('item_1', LibraryItemKind.file, '예산보고', source: _path),
        item('item_2', LibraryItemKind.text, '메모'),
      ],
    );
    await tester.pumpWidget(MaterialApp(home: NotebookScreen(api: api, library: library)));
    await tester.pumpAndSettle();

    await tester.tap(find.byKey(const ValueKey('nb-source-library')));
    await tester.pumpAndSettle();
    expect(find.text('예산 자료'), findsOneWidget);
    expect(find.byKey(const ValueKey('nb-lib-item-item_1')), findsOneWidget);
    expect(find.byKey(const ValueKey('nb-lib-item-item_2')), findsNothing);
    await tester.tap(find.byKey(const ValueKey('nb-lib-item-item_1')));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const ValueKey('nb-lib-ok')));
    await tester.pumpAndSettle();
    expect(find.text('예산보고.txt'), findsOneWidget);
    expect(find.text('문단 3개'), findsOneWidget);
    expect(find.text('출처를 추가했습니다.'), findsOneWidget);
  });

  testWidgets('library button is hidden without library api', (tester) async {
    final api = InMemoryNotebookApi();
    await api.createNotebook('연구');
    await tester.pumpWidget(MaterialApp(home: NotebookScreen(api: api)));
    await tester.pumpAndSettle();
    expect(find.byKey(const ValueKey('nb-source-library')), findsNothing);
  });

  testWidgets('bridge api parses paragraph level and drop commands', (tester) async {
    final calls = <Map>[];
    final api = BridgeNotebookApi((method, args) async {
      final request = args.single as Map;
      calls.add(request);
      return switch (request['cmd']) {
        'nb_source_paragraphs' => {
          'ok': true,
          'paragraphs': [
            {'source_id': 5, 'ordinal': 0, 'location': '', 'level': 3, 'kind': 'text', 'body': '□ 현황'},
            {'source_id': 5, 'ordinal': 1, 'location': '', 'level': 0, 'kind': 'table', 'body': '구분\t금액'},
          ],
        },
        'nb_take_drop' => {
          'ok': true,
          'paths': [_path],
        },
        _ => {'ok': true},
      };
    });
    final ps = await api.paragraphs(1, 5);
    expect(ps.map((p) => (p.level, p.isTable)), [(3, false), (0, true)]);
    expect(await api.takeDroppedPaths(), [_path]);
    await api.watchDrops(true);
    expect(calls.last, {'cmd': 'nb_drop_watch', 'active': true});
  });

  test('parseNbTags follows klib tag rules', () {
    expect(parseNbTags(' #예산, 복지  예산,EU eu,,#'), ['예산', '복지', 'EU']);
    expect(parseNbTags('가' * 40).single.runes.length, 30);
    expect(parseNbTags([for (var i = 0; i < 30; i++) 't$i'].join(',')), hasLength(20));
  });

  for (final width in [700.0, 1000.0, 1400.0]) {
    testWidgets('tags filter notes and compare shows sources side by side at width $width', (tester) async {
      await _setSize(tester, width);
      final narrow = width < kNotebookWideWidth;
      const road = r'C:\자료\도로.md';
      const misc = r'C:\자료\기타.txt';
      final api = InMemoryNotebookApi(
        fileContents: {_path: _content, road: '복지관 앞 도로 정비\n교량 보수', misc: '무관한 내용'},
      );
      final nb = await api.createNotebook('연구');
      final budget = await api.addSource(nb, _path);
      final roadId = await api.addSource(nb, road);
      final miscId = await api.addSource(nb, misc);
      await tester.pumpWidget(MaterialApp(home: NotebookScreen(api: api)));
      await tester.pumpAndSettle();

      Future<void> tab(String key) async {
        if (!narrow) return;
        await tester.tap(find.byKey(ValueKey(key)));
        await tester.pumpAndSettle();
      }

      // 출처 비교: 같은 검색어를 출처마다 나란히 보여 주고, 근거 없는 출처는 빈 칸으로 둔다.
      await tab('nb-tab-evidence');
      await tester.tap(find.byKey(const ValueKey('nb-mid-compare')));
      await tester.pumpAndSettle();
      await tester.enterText(find.byKey(const ValueKey('nb-compare-query')), '복지 예산');
      await tester.tap(find.byKey(const ValueKey('nb-compare-run')));
      await tester.pumpAndSettle();
      expect(find.text('출처 3개 중 2개에서 근거를 찾았습니다.'), findsOneWidget);
      expect(find.byKey(ValueKey('nb-compare-col-$budget')), findsOneWidget);
      expect(find.byKey(ValueKey('nb-compare-col-$roadId')), findsOneWidget);
      expect(find.text('예산보고.txt · 근거 2개'), findsOneWidget);
      expect(find.text('도로.md · 근거 1개'), findsOneWidget);
      // 근거가 많은 출처가 앞, 근거 없는 출처는 맨 뒤.
      final x0 = tester.getTopLeft(find.byKey(ValueKey('nb-compare-col-$budget'))).dx;
      final x1 = tester.getTopLeft(find.byKey(ValueKey('nb-compare-col-$roadId'))).dx;
      expect(x0, lessThan(x1));
      await tester.dragUntilVisible(
        find.byKey(ValueKey('nb-compare-col-$miscId')),
        find.byKey(const ValueKey('nb-compare')),
        const Offset(-200, 0),
      );
      expect(
        find.descendant(of: find.byKey(ValueKey('nb-compare-col-$miscId')), matching: find.text('근거 문단 없음')),
        findsOneWidget,
      );
      await tester.dragUntilVisible(
        find.byKey(ValueKey('nb-compare-col-$budget')),
        find.byKey(const ValueKey('nb-compare')),
        const Offset(200, 0),
      );
      await tester.tap(find.byKey(ValueKey('nb-compare-cite-$budget-0')));
      await tester.pumpAndSettle();
      // 칸의 근거를 누르면 원문 위치를 미리보기에서 강조한다.
      await tester.tap(find.byKey(ValueKey('nb-compare-hit-$budget-0')));
      await tester.pumpAndSettle();
      expect(find.byKey(const ValueKey('nb-preview')), findsOneWidget);
      expect(find.byKey(const ValueKey('nb-preview-1')), findsOneWidget);

      // 태그 단 노트 둘을 저장한다.
      await tab('nb-tab-notes');
      await tester.enterText(find.byKey(const ValueKey('nb-note-title')), '복지 메모');
      await tester.enterText(find.byKey(const ValueKey('nb-note-tags')), '#예산, 복지 예산');
      await tester.ensureVisible(find.byKey(const ValueKey('nb-note-save')));
      await tester.tap(find.byKey(const ValueKey('nb-note-save')));
      await tester.pumpAndSettle();
      final first = (await api.listNotes(nb)).single;
      expect(first.tags, ['예산', '복지']);
      expect(first.citations, hasLength(1));
      await tester.ensureVisible(find.byKey(const ValueKey('nb-note-new')));
      await tester.tap(find.byKey(const ValueKey('nb-note-new')));
      await tester.pumpAndSettle();
      expect(find.byKey(const ValueKey('nb-note-tags')), findsOneWidget);
      await tester.enterText(find.byKey(const ValueKey('nb-note-title')), '도로 메모');
      await tester.enterText(find.byKey(const ValueKey('nb-note-tags')), '도로');
      await tester.ensureVisible(find.byKey(const ValueKey('nb-note-save')));
      await tester.tap(find.byKey(const ValueKey('nb-note-save')));
      await tester.pumpAndSettle();

      // 태그로 거르기.
      await tester.ensureVisible(find.byKey(const ValueKey('nb-tag-예산')));
      expect(find.text('#예산 1'), findsOneWidget);
      expect(find.text('#도로 1'), findsOneWidget);
      expect(find.byKey(ValueKey('nb-note-${first.id}')), findsOneWidget);
      await tester.tap(find.byKey(const ValueKey('nb-tag-도로')));
      await tester.pumpAndSettle();
      expect(find.byKey(ValueKey('nb-note-${first.id}')), findsNothing);
      expect(find.text('노트 1/2'), findsOneWidget);
      await tester.tap(find.byKey(const ValueKey('nb-tag-예산')));
      await tester.pumpAndSettle();
      expect(find.byKey(ValueKey('nb-note-${first.id}')), findsOneWidget);
      await tester.tap(find.byKey(ValueKey('nb-note-${first.id}')));
      await tester.pumpAndSettle();
      expect(tester.widget<TextField>(find.byKey(const ValueKey('nb-note-tags'))).controller!.text, '예산, 복지');

      // 내보내기에 태그와 마지막 출처 비교가 들어간다.
      await _chooseExport(tester, 'nb-export-md');
      final text = tester.widget<SelectableText>(find.byKey(const ValueKey('nb-export-text'))).data!;
      expect(text, contains('태그: #예산 #복지'));
      expect(text, contains('## 출처 비교: 복지 예산'));
      expect(text, contains('### 도로.md'));
      expect(text, contains('### 기타.txt\n\n근거 문단 없음'));
      expect(find.textContaining('출처 비교: 복지 예산 포함'), findsOneWidget);
      await tester.tap(find.text('닫기'));
      await tester.pumpAndSettle();
      // HWPX에도 마지막 출처 비교 검색어가 넘어간다(비교 표).
      await _chooseExport(tester, 'nb-export-hwpx');
      expect(api.hwpxExports.last.$3, '복지 예산');
      expect(tester.takeException(), isNull);
    });
  }

  testWidgets('bridge api sends compare, tags and export compare options', (tester) async {
    final calls = <Map>[];
    final api = BridgeNotebookApi((method, args) async {
      final request = args.single as Map;
      calls.add(request);
      return switch (request['cmd']) {
        'nb_compare' => {
          'ok': true,
          'groups': [
            {
              'source_id': 5,
              'display_name': 'a.txt',
              'origin': r'C:\a.txt',
              'hits': [
                {'source_id': 5, 'ordinal': 2, 'display_name': 'a.txt', 'location': '3쪽', 'score': 1.5, 'body': '복지'},
              ],
            },
            {'source_id': 6, 'display_name': 'b.txt', 'origin': '', 'hits': <Object>[]},
          ],
        },
        'nb_note_list' => {
          'ok': true,
          'notes': [
            {'id': 1, 'title': 't', 'body': '', 'tags': ['예산', '복지'], 'citations': <Object>[]},
          ],
        },
        'nb_note_save' => {'ok': true, 'id': 9},
        'nb_export_md' => {'ok': true, 'markdown': '# t'},
        'nb_select_output' => request['cancel'] == true
            ? {'ok': true, 'cancelled': true}
            : {'ok': true, 'cancelled': false, 'selection_id': 'sel-1'},
        'nb_export_hwpx' => {'ok': true, 'path': r'C:\out\노트.hwpx'},
        _ => {'ok': true},
      };
    });
    final groups = await api.compare(1, '복지', sourceIds: [5, 6], perSource: 2);
    expect(calls.last, {'cmd': 'nb_compare', 'notebook_id': 1, 'query': '복지', 'per_source': 2, 'source_ids': [5, 6]});
    expect(groups.map((g) => (g.sourceId, g.hits.length)), [(5, 1), (6, 0)]);
    expect(groups.first.hits.single.location, '3쪽');
    expect((await api.listNotes(1)).single.tags, ['예산', '복지']);
    expect(await api.saveNote(1, const NbNote(title: 't', body: '', tags: ['예산'])), 9);
    expect(calls.last['tags'], ['예산']);
    await api.exportMarkdown(1, 9);
    expect(calls.last, {'cmd': 'nb_export_md', 'notebook_id': 1, 'note_id': 9});
    await api.exportMarkdown(1, 9, compareQuery: ' 복지 ', compareSourceIds: [5]);
    expect(calls.last, {
      'cmd': 'nb_export_md',
      'notebook_id': 1,
      'note_id': 9,
      'compare_query': '복지',
      'compare_source_ids': [5],
    });
    expect(await api.exportHwpx(1, 9, compareQuery: ' 복지 ', compareSourceIds: [5]), r'C:\out\노트.hwpx');
    expect(calls[calls.length - 2], {'cmd': 'nb_select_output'});
    expect(calls.last, {
      'cmd': 'nb_export_hwpx',
      'notebook_id': 1,
      'note_id': 9,
      'output_selection_id': 'sel-1',
      'compare_query': '복지',
      'compare_source_ids': [5],
    });
  });

  testWidgets('bridge api hwpx export stops when save dialog is cancelled', (tester) async {
    final calls = <String>[];
    final api = BridgeNotebookApi((method, args) async {
      calls.add('${(args.single as Map)['cmd']}');
      return {'ok': true, 'cancelled': true};
    });
    expect(await api.exportHwpx(1, 2), isNull);
    expect(calls, ['nb_select_output']);
  });

  testWidgets('middle tab and search button are named 본문검색', (tester) async {
    await _setSize(tester, 1400);
    final api = InMemoryNotebookApi(fileContents: {_path: _content});
    final nb = await api.createNotebook('연구');
    await api.addSource(nb, _path);
    await tester.pumpWidget(MaterialApp(home: NotebookScreen(api: api)));
    await tester.pumpAndSettle();
    expect(
      find.descendant(of: find.byKey(const ValueKey('nb-mid-search')), matching: find.text('본문검색')),
      findsOneWidget,
    );
    expect(
      find.descendant(of: find.byKey(const ValueKey('nb-search-run')), matching: find.text('본문검색')),
      findsOneWidget,
    );
    expect(find.textContaining('근거 찾기'), findsNothing);
  });

  testWidgets('search, compare and preview bodies use 10pt even with a huge host font', (tester) async {
    await _setSize(tester, 1400);
    expect(kNbReadingFontSize, closeTo(13.333, 0.001)); // 10pt × 96/72
    final api = InMemoryNotebookApi(fileContents: {_path: _content});
    final nb = await api.createNotebook('연구');
    await api.addSource(nb, _path);
    final huge = ThemeData(textTheme: const TextTheme(bodyMedium: TextStyle(fontSize: 30)));
    await tester.pumpWidget(MaterialApp(theme: huge, home: NotebookScreen(api: api)));
    await tester.pumpAndSettle();

    double? spanSize(Finder f) => tester.widget<Text>(f).textSpan!.style!.fontSize;
    await tester.enterText(find.byKey(const ValueKey('nb-query')), '복지 예산');
    await tester.tap(find.byKey(const ValueKey('nb-search-run')));
    await tester.pumpAndSettle();
    expect(spanSize(find.byKey(const ValueKey('nb-hit-body-0'))), kNbReadingFontSize);
    // 노란 강조 글자도 같은 크기(부모 크기를 물려받음).
    final rich = tester.widget<Text>(find.byKey(const ValueKey('nb-hit-body-0'))).textSpan! as TextSpan;
    expect(rich.children!.whereType<TextSpan>().every((c) => c.style?.fontSize == null), isTrue);

    await tester.tap(find.byKey(const ValueKey('nb-mid-compare')));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const ValueKey('nb-compare-run')));
    await tester.pumpAndSettle();
    final sourceId = (await api.listSources(nb)).single.id;
    expect(spanSize(find.byKey(ValueKey('nb-compare-body-$sourceId-0'))), kNbReadingFontSize);

    await tester.tap(find.byKey(ValueKey('nb-compare-hit-$sourceId-0')));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const ValueKey('nb-mid-preview')));
    await tester.pumpAndSettle();
    expect(tester.widget<SelectableText>(find.byKey(const ValueKey('nb-preview-text-0'))).style!.fontSize, kNbReadingFontSize);
  });

  testWidgets('+메모 추가 saves a TEXT source that can be checked, searched and cited', (tester) async {
    await _setSize(tester, 1400);
    final api = InMemoryNotebookApi();
    final nb = await api.createNotebook('연구');
    await tester.pumpWidget(MaterialApp(home: NotebookScreen(api: api)));
    await tester.pumpAndSettle();

    await tester.tap(find.byKey(const ValueKey('nb-memo-add')));
    await tester.pumpAndSettle();
    expect(find.text('새 메모'), findsOneWidget);
    expect(find.text("작성된 메모를 저장하면 TEXT 형식으로 '출처'에 추가됩니다."), findsOneWidget);
    await tester.enterText(find.byKey(const ValueKey('memo-title')), '현장 메모');
    await tester.enterText(find.byKey(const ValueKey('memo-body')), '공원 정비 예산');
    await tester.tap(find.byKey(const ValueKey('memo-bold')));
    await tester.pump(const Duration(seconds: 1));
    expect(find.text('Saved'), findsOneWidget);

    // 닫았다 다시 열어도 자동 저장 초안이 남아 있다.
    await tester.pageBack();
    await tester.pumpAndSettle();
    expect(find.text('메모 추가(작성 중)'), findsOneWidget);
    await tester.tap(find.byKey(const ValueKey('nb-memo-add')));
    await tester.pumpAndSettle();
    expect(find.text('현장 메모'), findsOneWidget);

    await tester.tap(find.byKey(const ValueKey('memo-save')));
    await tester.pumpAndSettle();
    expect(find.text('메모를 출처에 추가했습니다.'), findsOneWidget);
    final source = (await api.listSources(nb)).single;
    expect((source.displayName, source.kind), ('현장 메모', 'txt'));
    expect(api.memoMarkdown[source.id], startsWith('공원 정비 예산'));
    expect(find.text('메모 추가'), findsOneWidget);
    final checkbox = find.descendant(of: find.byKey(ValueKey('nb-source-${source.id}')), matching: find.byType(Checkbox));
    expect(tester.widget<Checkbox>(checkbox).value, isTrue);

    await tester.enterText(find.byKey(const ValueKey('nb-query')), '공원 예산');
    await tester.tap(find.byKey(const ValueKey('nb-search-run')));
    await tester.pumpAndSettle();
    expect(find.descendant(of: find.byKey(const ValueKey('nb-hit-0')), matching: find.textContaining('현장 메모')), findsOneWidget);
    await tester.tap(find.byKey(const ValueKey('nb-cite-0')));
    await tester.pumpAndSettle();
    expect(find.byKey(const ValueKey('nb-citation-0')), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('memo delete discards the draft', (tester) async {
    await _setSize(tester, 1400);
    final api = InMemoryNotebookApi();
    final nb = await api.createNotebook('연구');
    await tester.pumpWidget(MaterialApp(home: NotebookScreen(api: api)));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const ValueKey('nb-memo-add')));
    await tester.pumpAndSettle();
    await tester.enterText(find.byKey(const ValueKey('memo-body')), '버릴 메모');
    await tester.pump(const Duration(seconds: 1));
    await tester.tap(find.byKey(const ValueKey('memo-delete')));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const ValueKey('memo-delete-ok')));
    await tester.pumpAndSettle();
    expect(find.byKey(const ValueKey('memo-body')), findsNothing);
    expect(find.text('메모 추가'), findsOneWidget);
    expect(await api.listSources(nb), isEmpty);
  });

  test('bridge api sends nb_memo_add', () async {
    final calls = <Map>[];
    final api = BridgeNotebookApi((method, args) async {
      calls.add(args.single as Map);
      return {'ok': true, 'id': 11, 'paragraph_count': 1};
    });
    expect(await api.addMemoSource(2, title: '메모', markdown: '**본문**'), 11);
    expect(calls.single, {'cmd': 'nb_memo_add', 'notebook_id': 2, 'title': '메모', 'markdown': '**본문**'});
  });
}
