import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:docfit_ui/main.dart';
import 'package:docfit_ui/features/conversion/conversion_workspace.dart';
import 'package:docfit_ui/features/flows/flow_editor_screen.dart';
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
