import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:docfit_ui/main.dart';
import 'package:docfit_ui/features/conversion/conversion_workspace.dart';
import 'package:docfit_ui/features/flows/flow_editor_screen.dart';
import 'package:docfit_ui/features/workspace/workspace_adapters.dart';
import 'package:docfit_ui/features/workspace/tab_navigation_shell.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  const windowChannel = MethodChannel('docfit/window');
  TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
      .setMockMethodCallHandler(windowChannel, (call) async => {'ok': true, 'active': true});
  testWidgets('workspace sidebar shows new document first and gates developer toggles', (tester) async {
    final state = <String, dynamic>{'developer_mode': false, 'always_on_top': false};
    Future<Object?> api(String name, List<Object?> args) async => name == 'get_state' ? state : {'items': []};
    await tester.pumpWidget(MaterialApp(home: IntegratedWorkspace(
      api: api,
      documentEditorWidget: const SizedBox(),
      fileConversionWidget: const SizedBox(),
      developerMode: false,
      trailing: Builder(builder: (context) => Column(children: [
        TextButton(key: const ValueKey('new-document-open'), onPressed: () {}, child: const Text('새문서')),
        TextButton(onPressed: () {}, child: const Text('몽땅클립보드')),
      ])),
    )));
    expect(find.byKey(const ValueKey('new-document-open')), findsOneWidget);
    expect(find.text('새문서'), findsOneWidget);
    expect(find.byKey(const ValueKey('always-on-top-toggle')), findsNothing);
    expect(find.byKey(const ValueKey('sidebar-mode-toggle')), findsNothing);
    expect(tester.getTopLeft(find.byKey(const ValueKey('new-document-open'))).dy,
        lessThan(tester.getTopLeft(find.text('몽땅클립보드')).dy));
  });

  testWidgets('developer controls appear only when enabled', (tester) async {
    var sidebarMode = false;
    await tester.pumpWidget(MaterialApp(home: Scaffold(body: StatefulBuilder(builder: (context, setState) => WorkspaceTabBar(
      labels: const ['문서편집'], icons: const [Icons.description], selectedIndex: 0,
      onSelected: (_) {}, scrollController: ScrollController(), developerMode: true,
      sidebarOnly: sidebarMode,
      onSidebarModeChanged: (value) => setState(() => sidebarMode = value),
    )))));
    expect(find.byKey(const ValueKey('always-on-top-toggle')), findsOneWidget);
    expect(find.byKey(const ValueKey('sidebar-mode-toggle')), findsOneWidget);
    expect(find.text('작업 순서'), findsNothing);
    await tester.tap(find.byKey(const ValueKey('sidebar-mode-toggle')));
    await tester.pump();
    expect(find.text('사이드메뉴 모드 켜짐'), findsOneWidget);
  });

  testWidgets('DocFitApp mounts IntegratedWorkspace with 6 tabs by default',
      (tester) async {
    // 탭이 8개라 좁은 창에서는 아이콘만 보인다 — 이름까지 보이는 넓이로 시험한다.
    tester.view.physicalSize = const Size(1400, 900);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);
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
    expect(find.text('파일명 일괄변경'), findsOneWidget);
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
    // 탭에서도 상단 메뉴와 같은 편집기를 다이어그램 모드로 연다
    expect(
      tester
          .widget<FlowEditorScreen>(
            find.descendant(
              of: find.byType(DiagramAdapter),
              matching: find.byType(FlowEditorScreen),
            ),
          )
          .initialMode,
      'diagram',
    );

    // Tap on Tab 5: 마인드맵
    await tester.tap(find.text('마인드맵'));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 100));
    expect(find.byType(MindMapAdapter), findsOneWidget);
    expect(
      tester
          .widget<FlowEditorScreen>(
            find.descendant(
              of: find.byType(MindMapAdapter),
              matching: find.byType(FlowEditorScreen),
            ),
          )
          .initialMode,
      'mindmap',
    );

    // Tab 6 파일변환: 드롭 영역을 보이고, 작업 방식을 '파일 변환'으로 바꾼다
    await tester.tap(find.text('파일변환'));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 100));
    // 2.0.7: 파일변환 탭 한 화면(올린 파일 · 변환할 포맷 · 변환 결과).
    expect(find.byType(ConversionWorkspace), findsOneWidget);
    expect(find.byKey(const Key('conversionDropZone')), findsOneWidget);
    expect(calls, contains('set_mode:file_format'));
    expect(calls, contains('set_drop_target:documents'));
    await tester.tap(find.byKey(const Key('conversionPickFiles')));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 100));
    expect(calls, contains('add_files:null'));

    // Tab 7 그림판: 같은 편집기를 그림판 모드로 연다
    expect(find.text('그림판'), findsOneWidget);
    await tester.tap(find.text('그림판'));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 100));
    expect(find.byType(PaintAdapter), findsOneWidget);
    expect(
      tester
          .widget<FlowEditorScreen>(
            find.descendant(
              of: find.byType(PaintAdapter),
              matching: find.byType(FlowEditorScreen),
            ),
          )
          .initialMode,
      'paint',
    );
    // 표그림판 탭에서는 사진 끌어 놓기를 칸 그림으로 받고, 떠나면 문서 목록으로 되돌린다
    final sketchAt = calls.indexOf('set_drop_target:sketch_image');
    expect(sketchAt, greaterThanOrEqualTo(0));
    expect(calls.lastIndexOf('set_drop_target:documents'), greaterThan(sketchAt));
  });
}
