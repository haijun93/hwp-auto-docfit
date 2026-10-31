import 'package:docfit_ui/features/workspace/tab_navigation_shell.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('enabled canvases retain state across tab switches', (
    tester,
  ) async {
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
          api: (_, args) async => {'ok': true, 'connected': true, 'title': '문서'},
        ),
      ),
    );
    await tester.pump();
    expect(find.byTooltip('한/글: 문서 — 눌러서 다시 확인'), findsOneWidget);
    await tester.tap(find.byKey(const Key('liveLinkStatus')));
    await tester.pump();
    await tester.pump(const Duration(seconds: 5));
    const labels = ['문서편집', '표템플릿', '표그림판', '다이어그램', '마인드맵', '그림판', '파일변환'];
    // 하단 탭은 이 순서로 놓이고 파일변환이 항상 맨 끝이다(2026-10-30 사용자 지시).
    final xs = [for (final l in labels) tester.getCenter(find.text(l)).dx];
    for (var i = 1; i < xs.length; i++) {
      expect(xs[i], greaterThan(xs[i - 1]), reason: labels[i]);
    }
    for (final label in labels) {
      await tester.tap(find.text(label));
      await tester.pumpAndSettle();
      expect(find.text('count:0'), findsOneWidget);
      await tester.tap(find.text('count:0'));
      await tester.pump();
    }
    for (final label in labels) {
      await tester.tap(find.text(label));
      await tester.pumpAndSettle();
      expect(find.text('count:1'), findsOneWidget);
    }
  });

  testWidgets('resumed lifecycle immediately refreshes LiveLink status', (tester) async {
    var calls = 0;
    await tester.pumpWidget(MaterialApp(home: TabNavigationShell(
      documentEditor: const _Canvas(), tableTemplates: const _Canvas(),
      tableSketch: const _Canvas(), diagram: const _Canvas(), mindMap: const _Canvas(),
      fileConversion: const _Canvas(), paint: const _Canvas(),
      api: (_, args) async { calls++; return {'ok': true, 'connected': false}; },
    )));
    await tester.pump();
    final initial = calls;
    tester.binding.handleAppLifecycleStateChanged(AppLifecycleState.resumed);
    await tester.pump();
    expect(calls, initial + 1);
    expect(find.byTooltip('한/글 없음 — 눌러서 다시 확인'), findsOneWidget);
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
