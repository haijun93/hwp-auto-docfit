import 'package:docfit_ui/features/workspace/tab_navigation_shell.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  main2();
  testWidgets('enabled canvases retain state across tab switches', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(1400, 900);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);
    await tester.pumpWidget(
      MaterialApp(
        home: TabNavigationShell(
          documentEditor: const _Canvas(),
          tableTemplates: const _Canvas(),
          tableSketch: const _Canvas(),
          diagram: const _Canvas(),
          mindMap: const _Canvas(),
          fileConversion: const _Canvas(),
          paint: const _Canvas(),
          fileRename: const _Canvas(),
          timemachine: const _Canvas(),
        ),
      ),
    );
    const labels = ['문서편집', '표템플릿', '표그림판', '다이어그램', '마인드맵', '그림판', '타임머신', '파일변환'];
    // 하단 탭은 이 순서로 놓이고 파일변환이 항상 맨 끝이다(2026-10-30 사용자 지시).
    for (var i = 1; i < labels.length; i++) {
      await tester.ensureVisible(find.text(labels[i]));
      expect(tester.getCenter(find.text(labels[i])).dx, greaterThan(0), reason: labels[i]);
    }
    for (final label in labels) {
      await tester.ensureVisible(find.text(label));
      await tester.tap(find.text(label));
      await tester.pumpAndSettle();
      expect(find.text('count:0'), findsOneWidget);
      await tester.tap(find.text('count:0'));
      await tester.pump();
    }
    for (final label in labels) {
      await tester.ensureVisible(find.text(label));
      await tester.tap(find.text(label));
      await tester.pumpAndSettle();
      expect(find.text('count:1'), findsOneWidget);
    }
  });
}

class _Canvas extends StatefulWidget {
  const _Canvas();
  @override
  State<_Canvas> createState() => _CanvasState();
}

class _CanvasState extends State<_Canvas> {
  int count = 0;
  @override
  Widget build(BuildContext context) => Center(
    child: TextButton(
      onPressed: () => setState(() => count++),
      child: Text('count:$count'),
    ),
  );
}

Widget _shell({
  Set<int> hidden = kDefaultHiddenTabs,
  ValueListenable<bool?>? saved,
  ValueChanged<bool>? onChanged,
}) => MaterialApp(
  home: TabNavigationShell(
    documentEditor: const SizedBox(),
    tableTemplates: const SizedBox(),
    tableSketch: const SizedBox(),
    diagram: const SizedBox(),
    mindMap: const SizedBox(),
    fileConversion: const SizedBox(),
    paint: const SizedBox(),
    fileRename: const SizedBox(),
    timemachine: const SizedBox(),
    hiddenTabs: hidden,
    savedSidebarExpanded: saved,
    onSidebarExpandedChanged: onChanged,
    trailing: Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        for (final tip in const ['사용 방법', '작업 로그', '설정'])
          IconButton(tooltip: tip, onPressed: () {}, icon: const Icon(Icons.help)),
      ],
    ),
  ),
);

Future<void> _size(WidgetTester tester, double width, [double height = 700]) async {
  tester.view.physicalSize = Size(width, height);
  tester.view.devicePixelRatio = 1;
  addTearDown(tester.view.reset);
}

double _sidebarWidth(WidgetTester tester) =>
    tester.getSize(find.byType(WorkspaceTabBar)).width;

void main2() {
  for (final width in const [420.0, 800.0, 1400.0]) {
    testWidgets('왼쪽 메뉴: 폭 $width에서 보이는 메뉴를 모두 누를 수 있고 넘치지 않는다', (tester) async {
      await _size(tester, width);
      final selected = <int>[];
      await tester.pumpWidget(
        MaterialApp(
          home: TabNavigationShell(
            documentEditor: const SizedBox(),
            tableTemplates: const SizedBox(),
            tableSketch: const SizedBox(),
            diagram: const SizedBox(),
            mindMap: const SizedBox(),
            fileConversion: const SizedBox(),
            paint: const SizedBox(),
            fileRename: const SizedBox(),
            timemachine: const SizedBox(),
            onTabChanged: selected.add,
          ),
        ),
      );
      expect(_sidebarWidth(tester), width >= kSidebarAutoExpandWidth ? kSidebarExpandedWidth : kSidebarCollapsedWidth);
      for (final i in const [8, 7, 5, 4, 3, 2, 1, 0]) {
        await tester.tap(find.byKey(Key('workspaceTab-$i')));
        await tester.pump();
        expect(tester.takeException(), isNull);
      }
      expect(selected, const [8, 7, 5, 4, 3, 2, 1, 0]);
    });
  }

  testWidgets('왼쪽 메뉴: 낮은 창에서도 넘치지 않는다', (tester) async {
    await _size(tester, 800, 200);
    await tester.pumpWidget(_shell());
    expect(tester.takeException(), isNull);
  });

  testWidgets('왼쪽 메뉴: ☰은 저장을 알리고 뒤늦은 저장값이 덮지 않는다', (tester) async {
    await _size(tester, 1400);
    final saved = ValueNotifier<bool?>(null);
    final changes = <bool>[];
    await tester.pumpWidget(_shell(saved: saved, onChanged: changes.add));
    await tester.tap(find.byKey(const ValueKey('workspaceSidebarToggle')));
    await tester.pump();
    expect(changes, const [false]);
    expect(_sidebarWidth(tester), kSidebarCollapsedWidth);
    saved.value = true;
    await tester.pump();
    expect(_sidebarWidth(tester), kSidebarCollapsedWidth);
  });

  testWidgets('왼쪽 메뉴: 저장값이 창 폭 기본값보다 앞선다', (tester) async {
    await _size(tester, 1400);
    final saved = ValueNotifier<bool?>(null);
    await tester.pumpWidget(_shell(saved: saved));
    expect(_sidebarWidth(tester), kSidebarExpandedWidth);
    saved.value = false;
    await tester.pump();
    expect(_sidebarWidth(tester), kSidebarCollapsedWidth);
  });

  testWidgets('왼쪽 메뉴: Ctrl+숫자로 옮기고 숨긴 탭은 무시한다', (tester) async {
    await _size(tester, 1400);
    final selected = <int>[];
    await tester.pumpWidget(
      MaterialApp(
        home: TabNavigationShell(
          documentEditor: const SizedBox(),
          tableTemplates: const SizedBox(),
          tableSketch: const SizedBox(),
          diagram: const SizedBox(),
          mindMap: const SizedBox(),
          fileConversion: const SizedBox(),
          paint: const SizedBox(),
          fileRename: const SizedBox(),
          timemachine: const SizedBox(),
          onTabChanged: selected.add,
        ),
      ),
    );
    await tester.pump();
    Future<void> press(LogicalKeyboardKey key) async {
      await tester.sendKeyDownEvent(LogicalKeyboardKey.controlLeft);
      await tester.sendKeyEvent(key);
      await tester.sendKeyUpEvent(LogicalKeyboardKey.controlLeft);
      await tester.pump();
    }

    await press(LogicalKeyboardKey.digit2);
    await press(LogicalKeyboardKey.digit7); // 파일명 일괄변경(숨김)
    await press(LogicalKeyboardKey.digit9);
    expect(selected, const [1, kTabFileConversion]);
    expect(find.byKey(const Key('workspaceTab-$kTabFileRename')), findsNothing);
  });
}
