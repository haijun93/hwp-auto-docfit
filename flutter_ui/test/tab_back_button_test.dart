import 'package:docfit_ui/features/tools/document_tools_workspace.dart';
import 'package:docfit_ui/features/workspace/tab_navigation_shell.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

// 2.0.0 사용자 보고: 탭 안 화면의 ← 버튼이 Navigator.pop으로 앱 첫 경로를 빼서 앱이 멈췄다.
Widget _page(String label) => Builder(
  builder: (context) => Center(
    child: Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        Text(label),
        TextButton(
          key: Key('back-$label'),
          onPressed: () => closeWorkspaceScreen(context),
          child: const Text('뒤로'),
        ),
      ],
    ),
  ),
);

void main() {
  testWidgets('탭 안 화면의 뒤로는 앱을 닫지 않고 첫 탭으로 간다', (tester) async {
    await tester.pumpWidget(
      MaterialApp(
        home: TabNavigationShell(
          documentEditor: _page('문서'),
          tableTemplates: _page('표템플릿 화면'),
          tableSketch: _page('표그림판 화면'),
          diagram: _page('다이어그램 화면'),
          mindMap: _page('마인드맵 화면'),
          fileConversion: _page('파일변환 화면'),
          paint: _page('그림판 화면'),
          initialIndex: 3,
        ),
      ),
    );
    final navigator = tester.state<NavigatorState>(find.byType(Navigator));
    expect(navigator.canPop(), isFalse);

    await tester.tap(find.byKey(const Key('back-다이어그램 화면')));
    await tester.pumpAndSettle();

    expect(tester.takeException(), isNull);
    expect(find.byType(TabNavigationShell), findsOneWidget);
    final bar = tester.widget<NavigationBar>(find.byType(NavigationBar));
    expect(bar.selectedIndex, 0);
  });

  testWidgets('새 경로로 연 화면의 뒤로는 그 경로만 닫는다', (tester) async {
    await tester.pumpWidget(
      MaterialApp(
        home: Builder(
          builder: (context) => TextButton(
            key: const Key('open'),
            onPressed: () => Navigator.of(context).push(
              MaterialPageRoute<void>(
                builder: (_) => Scaffold(body: _page('편집기')),
              ),
            ),
            child: const Text('열기'),
          ),
        ),
      ),
    );
    await tester.tap(find.byKey(const Key('open')));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const Key('back-편집기')));
    await tester.pumpAndSettle();
    expect(find.byKey(const Key('open')), findsOneWidget);
    expect(find.text('편집기'), findsNothing);
  });

  testWidgets('문서편집 탭의 상단 메뉴는 새 화면을 덮지 않고 탭을 옮겨 하단 탭 메뉴가 남는다', (tester) async {
    Widget jump(String label, int index) => Builder(
      builder: (context) => TextButton(
        key: Key('jump-$label'),
        onPressed: () => WorkspaceTabScope.maybeOf(context)!.selectTab(index),
        child: Text(label),
      ),
    );
    await tester.pumpWidget(
      MaterialApp(
        home: TabNavigationShell(
          documentEditor: jump('표그림판으로', 2),
          tableTemplates: _page('표템플릿 화면'),
          tableSketch: _page('표그림판 화면'),
          diagram: _page('다이어그램 화면'),
          mindMap: _page('마인드맵 화면'),
          fileConversion: _page('파일변환 화면'),
          paint: _page('그림판 화면'),
        ),
      ),
    );
    await tester.tap(find.byKey(const Key('jump-표그림판으로')));
    await tester.pumpAndSettle();
    expect(
      tester.widget<NavigationBar>(find.byType(NavigationBar)).selectedIndex,
      2,
    );
    expect(find.byType(NavigationBar), findsOneWidget);
    expect(
      tester.state<NavigatorState>(find.byType(Navigator)).canPop(),
      isFalse,
    );
  });

  testWidgets('탭 안 텍스트 입력 화면에는 ← 버튼이 보이지 않는다', (tester) async {
    await tester.pumpWidget(
      MaterialApp(
        home: TabNavigationShell(
          documentEditor: DocumentToolsWorkspace(
            api: (_, _) async => <String, Object?>{},
            initial: 'convert',
            isModal: false,
          ),
          tableTemplates: _page('표템플릿 화면'),
          tableSketch: _page('표그림판 화면'),
          diagram: _page('다이어그램 화면'),
          mindMap: _page('마인드맵 화면'),
          fileConversion: _page('파일변환 화면'),
          paint: _page('그림판 화면'),
        ),
      ),
    );
    await tester.pump();
    expect(find.byIcon(Icons.arrow_back), findsNothing);
    expect(find.byType(BackButton), findsNothing);
  });

  testWidgets('파일변환 탭을 누르면 파일변환 화면으로 이동한다(2.0.2)', (tester) async {
    await tester.pumpWidget(
      MaterialApp(
        home: TabNavigationShell(
          documentEditor: _page('문서'),
          tableTemplates: _page('표템플릿 화면'),
          tableSketch: _page('표그림판 화면'),
          diagram: _page('다이어그램 화면'),
          mindMap: _page('마인드맵 화면'),
          fileConversion: _page('파일변환 화면'),
          paint: _page('그림판 화면'),
        ),
      ),
    );
    await tester.tap(find.text('파일변환'));
    await tester.pumpAndSettle();
    expect(
      tester.widget<NavigationBar>(find.byType(NavigationBar)).selectedIndex,
      5,
    );
    expect(find.text('파일변환 화면'), findsOneWidget);
  });
}
