import 'dart:ui' show PointerDeviceKind;

import 'package:docfit_ui/core/close_guards.dart';
import 'package:docfit_ui/features/library/library_api.dart';
import 'package:docfit_ui/features/library/library_screen.dart';
import 'package:docfit_ui/features/notebook/notebook_api.dart';
import 'package:docfit_ui/features/notebook/notebook_screen.dart';
import 'package:docfit_ui/features/workspace/tab_navigation_shell.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';

/// 사용자 요청 2026-11-07:
/// ① 사이드메뉴는 기본으로 클릭해야 실행화면을 부르고, 마우스 올림 자동 호출은 개발자 모드에서만.
/// ② 노트북·자료함을 열어도 사이드메뉴가 남고 오른쪽 실행창 안에 열린다.
class _DropLibraryApi extends InMemoryLibraryApi implements LibraryDropApi {
  _DropLibraryApi() : super(initialBoxes: const [LibraryBox(id: 'box_1', name: '보고서')]);
  final watched = <bool>[];

  @override
  Future<void> watchDrops(bool active) async => watched.add(active);

  @override
  Future<List<String>> takeDroppedPaths() async => const [];
}

class _Counter extends StatefulWidget {
  const _Counter();
  @override
  State<_Counter> createState() => _CounterState();
}

class _CounterState extends State<_Counter> {
  int count = 0;
  @override
  Widget build(BuildContext context) =>
      Center(child: TextButton(onPressed: () => setState(() => count++), child: Text('count:$count')));
}

Future<void> _size(WidgetTester tester) async {
  tester.view.physicalSize = const Size(1400, 900);
  tester.view.devicePixelRatio = 1;
  addTearDown(tester.view.reset);
}

Widget _app({
  required bool developerMode,
  List<int>? selected,
  Widget? library,
  Widget? notebook,
}) =>
    MaterialApp(
      home: TabNavigationShell(
        documentEditor: const _Counter(),
        tableTemplates: const Text('표템플릿 화면'),
        tableSketch: const SizedBox(),
        diagram: const SizedBox(),
        mindMap: const SizedBox(),
        fileConversion: const SizedBox(),
        paint: const SizedBox(),
        fileRename: const SizedBox(),
        timemachine: const SizedBox(),
        onTabChanged: selected?.add,
        developerMode: developerMode,
        libraryScreen: library,
        notebookScreen: notebook,
      ),
    );

bool _pillSelected(WidgetTester tester, Key key) => tester
    .widget<Semantics>(find.descendant(of: find.byKey(key), matching: find.byType(Semantics)).first)
    .properties
    .selected == true;

void main() {
  testWidgets('일반 모드: 마우스를 올려도 화면이 바뀌지 않고 클릭하면 바뀐다', (tester) async {
    await _size(tester);
    final selected = <int>[];
    await tester.pumpWidget(_app(developerMode: false, selected: selected));
    final mouse = await tester.createGesture(kind: PointerDeviceKind.mouse);
    addTearDown(mouse.removePointer);
    await mouse.addPointer(location: const Offset(1300, 800));
    await mouse.moveTo(tester.getCenter(find.byKey(const Key('workspaceTab-1'))));
    await tester.pump(const Duration(milliseconds: 400));
    expect(selected, isEmpty);
    expect(find.text('표템플릿 화면'), findsNothing);

    await tester.tap(find.byKey(const Key('workspaceTab-1')));
    await tester.pump();
    expect(selected, const [1]);
    expect(find.text('표템플릿 화면'), findsOneWidget);
  });

  testWidgets('일반 모드: 키보드 초점 이동만으로는 바뀌지 않고 Enter로 바뀐다', (tester) async {
    await _size(tester);
    final selected = <int>[];
    await tester.pumpWidget(_app(developerMode: false, selected: selected));
    final inkWell = find.descendant(of: find.byKey(const Key('workspaceTab-2')), matching: find.byType(InkWell));
    Focus.of(tester.element(find.descendant(of: inkWell, matching: find.byType(Stack)).first)).requestFocus();
    await tester.pump(const Duration(milliseconds: 400));
    expect(selected, isEmpty);
    await tester.sendKeyEvent(LogicalKeyboardKey.enter);
    await tester.pump();
    expect(selected, const [2]);
    // 접근성 이름은 그대로다.
    expect(find.bySemanticsLabel('표그림판'), findsWidgets);
  });

  testWidgets('개발자 모드: 마우스 올림으로 화면이 바뀐다', (tester) async {
    await _size(tester);
    final selected = <int>[];
    await tester.pumpWidget(_app(developerMode: true, selected: selected));
    final mouse = await tester.createGesture(kind: PointerDeviceKind.mouse);
    addTearDown(mouse.removePointer);
    await mouse.addPointer(location: const Offset(1300, 800));
    await mouse.moveTo(tester.getCenter(find.byKey(const Key('workspaceTab-1'))));
    await tester.pump(const Duration(milliseconds: 151));
    expect(selected, const [1]);
    expect(find.text('표템플릿 화면'), findsOneWidget);
  });

  testWidgets('자료함·노트북은 사이드메뉴를 남긴 채 실행창 안에 열리고 전환된다', (tester) async {
    await _size(tester);
    final library = _DropLibraryApi();
    final notebooks = InMemoryNotebookApi();
    var notebookWatching = false;
    final selected = <int>[];
    await tester.pumpWidget(_app(
      developerMode: true,
      selected: selected,
      library: LibraryScreen(api: library, watchDropEvents: (_) => () {}),
      notebook: NotebookScreen(api: notebooks, watchDropEvents: (_) {
        notebookWatching = true;
        return () => notebookWatching = false;
      }),
    ));
    await tester.pumpAndSettle();
    // 문서편집 화면의 상태를 바꿔 두고 자료함·노트북을 다녀와도 그대로인지 본다.
    await tester.tap(find.text('count:0'));
    await tester.pump();
    expect(library.watched, isEmpty);
    expect(notebookWatching, isFalse);

    await tester.tap(find.byKey(const ValueKey('library-open')));
    await tester.pumpAndSettle();
    expect(find.byType(LibraryScreen), findsOneWidget);
    expect(find.byType(WorkspaceTabBar), findsOneWidget, reason: '사이드메뉴가 남아 있어야 한다');
    expect(tester.state<NavigatorState>(find.byType(Navigator).first).canPop(), isFalse,
        reason: '새 화면을 덮어 띄우지 않는다');
    expect(_pillSelected(tester, const ValueKey('library-open')), isTrue);
    expect(_pillSelected(tester, const Key('workspaceTab-0')), isFalse);
    expect(library.watched, [true], reason: '자료함을 열면 끌어 놓기 감시 시작');

    // 노트북으로 바꾸면 자료함 감시는 멈추고 노트북 감시가 시작된다.
    await tester.tap(find.byKey(const ValueKey('notebook-open')));
    await tester.pumpAndSettle();
    expect(find.byType(LibraryScreen), findsNothing);
    expect(find.byType(NotebookScreen), findsOneWidget);
    expect(find.byType(WorkspaceTabBar), findsOneWidget);
    expect(_pillSelected(tester, const ValueKey('notebook-open')), isTrue);
    expect(_pillSelected(tester, const ValueKey('library-open')), isFalse);
    expect(library.watched, [true, false]);
    expect(notebookWatching, isTrue);
    expect(notebooks.watchingDrops, isTrue);

    // 다른 메뉴를 누르면 자연스럽게 전환되고 노트북 감시도 멈춘다.
    await tester.tap(find.byKey(const Key('workspaceTab-1')));
    await tester.pumpAndSettle();
    expect(find.byType(NotebookScreen), findsNothing);
    expect(find.text('표템플릿 화면'), findsOneWidget);
    expect(notebookWatching, isFalse);
    expect(notebooks.watchingDrops, isFalse);
    expect(_pillSelected(tester, const Key('workspaceTab-1')), isTrue);

    // '처음 화면으로' 단추는 문서편집으로 돌아가고, 편집 상태는 남아 있다.
    await tester.tap(find.byKey(const ValueKey('library-open')));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const ValueKey('host-page-back')));
    await tester.pumpAndSettle();
    expect(find.byType(LibraryScreen), findsNothing);
    expect(find.text('count:1'), findsOneWidget);
    expect(selected.last, 0);
    expect(library.watched, [true, false, true, false]);

    // 이미 연 탭(문서편집)을 다시 누르는 것으로도 돌아간다.
    await tester.tap(find.byKey(const ValueKey('notebook-open')));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const Key('workspaceTab-0')));
    await tester.pumpAndSettle();
    expect(find.byType(NotebookScreen), findsNothing);
    expect(find.text('count:1'), findsOneWidget);
  });

  testWidgets('실행창 안 자료함은 Esc로 처음 화면으로 돌아가고 종료(CloseGuards)를 막지 않는다', (tester) async {
    await _size(tester);
    // 자료함 자체의 Esc(선택 해제)가 먼저 듣는 것은 예전 새 화면 방식과 같으므로, 여기서는
    // 실행창 머리글의 Esc 처리만 본다.
    await tester.pumpWidget(_app(developerMode: true, library: const Text('자료함 본문')));
    await tester.tap(find.byKey(const ValueKey('library-open')));
    await tester.pumpAndSettle();

    var accepted = false;
    await tester.runAsync(() async {
      accepted = await CloseGuards.prepareAll();
    });
    expect(accepted, isTrue, reason: '실행창 안 화면은 종료 대기열에 남지 않는다');
    expect(find.text('자료함 본문'), findsOneWidget);

    await tester.sendKeyEvent(LogicalKeyboardKey.escape);
    await tester.pumpAndSettle();
    expect(find.text('자료함 본문'), findsNothing);
    expect(find.text('count:0'), findsOneWidget);
    expect(find.byType(WorkspaceTabBar), findsOneWidget);
  });

  testWidgets('개발자 모드를 끄면 열린 자료함도 닫히고 메뉴가 사라진다', (tester) async {
    await _size(tester);
    final library = LibraryScreen(api: InMemoryLibraryApi(), watchDropEvents: (_) => () {});
    await tester.pumpWidget(_app(developerMode: true, library: library));
    await tester.tap(find.byKey(const ValueKey('library-open')));
    await tester.pumpAndSettle();
    expect(find.byType(LibraryScreen), findsOneWidget);
    await tester.pumpWidget(_app(developerMode: false, library: library));
    await tester.pumpAndSettle();
    expect(find.byType(LibraryScreen), findsNothing);
    expect(find.byKey(const ValueKey('library-open')), findsNothing);
    expect(find.text('count:0'), findsOneWidget);
  });

  testWidgets('메뉴 접힘(아이콘만) 상태에서도 자료함이 넘치지 않고 열린다', (tester) async {
    tester.view.physicalSize = const Size(800, 700);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);
    await tester.pumpWidget(_app(
      developerMode: true,
      library: LibraryScreen(api: InMemoryLibraryApi(), watchDropEvents: (_) => () {}),
    ));
    expect(tester.getSize(find.byType(WorkspaceTabBar)).width, kSidebarCollapsedWidth);
    await tester.tap(find.byKey(const ValueKey('library-open')));
    await tester.pumpAndSettle();
    expect(tester.takeException(), isNull);
    expect(find.byType(LibraryScreen), findsOneWidget);
    expect(find.byType(WorkspaceTabBar), findsOneWidget);
  });
}
