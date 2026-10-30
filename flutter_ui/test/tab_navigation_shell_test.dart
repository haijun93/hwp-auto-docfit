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
        ),
      ),
    );
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
