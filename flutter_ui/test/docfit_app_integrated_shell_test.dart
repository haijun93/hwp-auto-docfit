import 'package:flutter_test/flutter_test.dart';
import 'package:docfit_ui/main.dart';
import 'package:docfit_ui/features/workspace/workspace_adapters.dart';
import 'package:docfit_ui/features/workspace/tab_navigation_shell.dart';

void main() {
  testWidgets('DocFitApp mounts IntegratedWorkspace with 6 tabs by default',
      (tester) async {
    final calls = <String>[];
    Future<Object?> mockApi(String endpoint, List<Object?> params) async {
      calls.add('$endpoint:${params.firstOrNull}');
      return {'ok': true};
    }

    await tester.pumpWidget(
      DocFitApp(
        api: mockApi,
        useIntegratedShell: true,
      ),
    );
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 100));

    // Verify TabNavigationShell and IntegratedWorkspace exist
    expect(find.byType(IntegratedWorkspace), findsOneWidget);
    expect(find.byType(TabNavigationShell), findsOneWidget);

    // Verify all 6 bottom navigation labels exist
    expect(find.text('문서편집'), findsOneWidget);
    expect(find.text('표템플릿'), findsOneWidget);
    expect(find.text('표그림판'), findsOneWidget);
    expect(find.text('다이어그램'), findsOneWidget);
    expect(find.text('마인드맵'), findsOneWidget);
    expect(find.text('파일변환'), findsOneWidget);

    // Initial tab (index 0) has DocumentEditorAdapter
    expect(find.byType(DocumentEditorAdapter), findsOneWidget);

    // Tap on Tab 2: 표템플릿
    await tester.tap(find.text('표템플릿'));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 100));
    expect(find.byType(TableTemplatesAdapter), findsOneWidget);

    // Tap on Tab 3: 표그림판
    await tester.tap(find.text('표그림판'));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 100));
    expect(find.byType(TableSketchAdapter), findsOneWidget);

    // Tap on Tab 4: 다이어그램
    await tester.tap(find.text('다이어그램'));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 100));
    expect(find.byType(DiagramAdapter), findsOneWidget);

    // Tap on Tab 5: 마인드맵
    await tester.tap(find.text('마인드맵'));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 100));
    expect(find.byType(MindMapAdapter), findsOneWidget);

    // Tap on Tab 6: 파일변환
    await tester.tap(find.text('파일변환'));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 100));
    expect(find.byType(FileConversionAdapter), findsOneWidget);
  });
}
