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
        ),
      ),
    );
    // 파일변환(5)은 2.0.1에서 비활성이라 제외
    const labels = ['문서편집', '표템플릿', '표그림판', '다이어그램', '마인드맵'];
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
