import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:docfit_ui/main.dart';
import 'package:docfit_ui/features/settings/settings_dialog.dart';
import 'workspace_test.dart' show initialState;

void main() {
  testWidgets('work log button opens Flutter log dialog', (tester) async {
    tester.view.physicalSize = const Size(1024, 900);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    final state = initialState();
    Future<Object?> api(String name, List<Object?> args) async {
      if (name == 'get_log') return '테스트 작업 로그 본문';
      return Map<String, dynamic>.from(state);
    }

    await tester.pumpWidget(DocFitApp(api: api));
    await tester.pumpAndSettle();

    await tester.tap(find.byTooltip('작업 로그'));
    await tester.pumpAndSettle();

    expect(find.text('작업 로그'), findsOneWidget);
    expect(find.text('테스트 작업 로그 본문'), findsOneWidget);
    await tester.tap(find.text('닫기'));
    await tester.pumpAndSettle();
    expect(find.text('테스트 작업 로그 본문'), findsNothing);
    expect(tester.takeException(), isNull);
    await tester.pumpWidget(const SizedBox());
  });

  testWidgets('stage adjustment button opens Flutter showStages dialog', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(1024, 900);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    final state = initialState();
    state['files'] = [
      {'name': '문서.hwp', 'folder': r'C:\문서'},
    ];
    Future<Object?> api(String name, List<Object?> args) async =>
        Map<String, dynamic>.from(state);

    await tester.pumpWidget(DocFitApp(api: api));
    await tester.pumpAndSettle();
    await tester.tap(find.text('작업 방식 선택'));
    await tester.pumpAndSettle();

    await tester.scrollUntilVisible(
      find.text('단계별 수치 조정'),
      300,
      scrollable: find.byType(Scrollable).first,
    );
    await tester.tap(find.text('단계별 수치 조정'));
    await tester.pumpAndSettle();

    expect(find.text('세부 작업 선택'), findsOneWidget);
    expect(find.text('현재 구성을 기본값으로'), findsOneWidget);
    await tester.tap(find.text('닫기'));
    await tester.pumpAndSettle();
    expect(find.text('세부 작업 선택'), findsNothing);
    expect(tester.takeException(), isNull);
    await tester.pumpWidget(const SizedBox());
  });

  testWidgets('open settings opens Flutter SettingsDialog', (tester) async {
    tester.view.physicalSize = const Size(1024, 900);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    final state = initialState();
    Future<Object?> api(String name, List<Object?> args) async {
      if (name == 'get_settings') {
        return {
          'api_version': 1,
          'ok': true,
          'error': null,
          'data': {
            'fields': <Map<String, dynamic>>[],
            'values': <String, dynamic>{},
            'revision': 'rev1',
          },
        };
      }
      return Map<String, dynamic>.from(state);
    }

    await tester.pumpWidget(DocFitApp(api: api));
    await tester.pumpAndSettle();
    await tester.tap(find.byTooltip('설정'));
    await tester.pumpAndSettle();

    await tester.scrollUntilVisible(
      find.text('전체 설정 열기'),
      300,
      scrollable: find.byType(Scrollable).last,
    );
    // 목록 맨 아래 단추가 하단 탭에 걸치지 않게 위쪽으로 맞춘다.
    await tester.ensureVisible(find.text('전체 설정 열기'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('전체 설정 열기'));
    await tester.pumpAndSettle();

    expect(find.byType(SettingsDialog), findsOneWidget);
    expect(tester.takeException(), isNull);
    await tester.pumpWidget(const SizedBox());
  });
}
