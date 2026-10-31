import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:docfit_ui/features/workspace/tab_navigation_shell.dart';
import 'package:docfit_ui/features/workspace/workspace_adapters.dart';

void main() {
  testWidgets('IntegratedWorkspace mounts TabNavigationShell with 9 tabs', (tester) async {
    int currentTab = 0;
    Future<Object?> mockApi(String endpoint, List<Object?> params) async {
      return {'ok': true};
    }

    await tester.pumpWidget(
      MaterialApp(
        home: IntegratedWorkspace(
          api: mockApi,
          documentEditorWidget: const Text('DocEditorContent'),
          fileConversionWidget: const Text('FileConversionContent'),
          onTabChanged: (idx) => currentTab = idx,
        ),
      ),
    );

    // Initial state: Tab 0 active
    expect(find.byType(TabNavigationShell), findsOneWidget);
    expect(find.text('DocEditorContent'), findsOneWidget);
    expect(find.text('문서편집'), findsOneWidget);
    expect(find.text('표템플릿'), findsOneWidget);
    expect(find.text('표그림판'), findsOneWidget);
    expect(find.text('다이어그램'), findsOneWidget);
    expect(find.text('마인드맵'), findsOneWidget);
    expect(find.text('파일명 일괄변경'), findsOneWidget);
    expect(find.text('타임머신'), findsOneWidget);
    expect(find.text('파일변환'), findsOneWidget);

    await tester.ensureVisible(find.byKey(const Key('workspaceTab-8')));
    await tester.tap(find.byKey(const Key('workspaceTab-8')));
    await tester.pumpAndSettle();
    expect(currentTab, 8);
    expect(find.text('FileConversionContent'), findsOneWidget);

    // Switch back to Tab 0 (문서편집) — 탭 이름이 길어져 좁은 창에서는 탭 줄을 다시 밀어야 보인다.
    await tester.ensureVisible(find.text('문서편집'));
    await tester.tap(find.text('문서편집'));
    await tester.pumpAndSettle();
    expect(currentTab, 0);
    expect(find.text('DocEditorContent'), findsOneWidget);
  });

  testWidgets('Each adapter wraps child in stable KeyedSubtree', (tester) async {
    const docKey = ValueKey('tab-document-editor-adapter');
    const convKey = ValueKey('tab-file-conversion-adapter');

    await tester.pumpWidget(
      const MaterialApp(
        home: Scaffold(
          body: Column(
            children: [
              DocumentEditorAdapter(child: Text('Child 1')),
              FileConversionAdapter(child: Text('Child 2')),
            ],
          ),
        ),
      ),
    );

    expect(find.byKey(docKey), findsOneWidget);
    expect(find.byKey(convKey), findsOneWidget);
  });

  test('tab constants keep conversion last', () {
    expect(kTabFileRename, 6);
    expect(kTabTimemachine, 7);
    expect(kTabFileConversion, 8);
    expect(kTabCount, 9);
  });
}
