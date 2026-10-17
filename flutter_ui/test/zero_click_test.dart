import 'package:docfit_ui/main.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'workspace_test.dart' show initialState;

Map<String, dynamic> quickState({bool legacyPending = false}) => initialState()
  ..['files'] = [
    {'name': '초안.md', 'folder': r'C:\문서'},
  ]
  ..['doc_hints'] = {
    'recommended_mode': 'spacing',
    'reason': '문서 양식을 유지해요.',
    'show_table_option': false,
    'show_page_range': false,
  }
  ..['zero_click'] = legacyPending
      ? {
          'pending': true,
          'token': 'drop-1',
          'file_name': '초안.md',
          'remaining_ms': 2500,
        }
      : {'pending': false};

void main() {
  testWidgets(
    'manual card selection keeps the recommendation without starting work',
    (tester) async {
      tester.view.physicalSize = const Size(1280, 1000);
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);
      final state = quickState();
      final calls = <String>[];
      Future<Object?> api(String method, List<Object?> args) async {
        calls.add(method);
        if (method == 'cancel_zero_click') {
          state['zero_click'] = {'pending': false};
        }
        if (method == 'set_mode') {
          state['mode'] = args.first;
          state['user_overrode_mode'] = true;
        }
        return Map<String, dynamic>.from(state);
      }

      await tester.pumpWidget(DocFitApp(api: api));
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 100));
      await tester.tap(find.text('작업 방식 선택'));
      await tester.pump(const Duration(milliseconds: 200));
      await tester.tap(find.text('서식 통일').first);
      await tester.pump();
      await tester.pump(const Duration(seconds: 3));
      expect(calls, isNot(contains('start_zero_click')));
      expect(state['mode'], 'unify');
      expect(find.text('직접 선택'), findsNothing);
      expect(find.text('✨ 문서 자동 맞춤'), findsNothing);
      await tester.pumpWidget(const SizedBox());
    },
  );
  testWidgets('selected mode shows all options and page range immediately', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(1280, 1000);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    final state = quickState();
    await tester.pumpWidget(
      DocFitApp(api: (_, _) async => Map<String, dynamic>.from(state)),
    );
    await tester.pumpAndSettle();
    await tester.tap(find.text('작업 방식 선택'));
    await tester.pumpAndSettle();
    expect(find.byKey(const Key('resetSpacingSwitch')), findsOneWidget);
    expect(find.byKey(const Key('tableSpacingSwitch')), findsOneWidget);
    expect(find.text('작업할 쪽 범위'), findsOneWidget);
    expect(find.text('세부 작업  1/2'), findsOneWidget);
    expect(tester.takeException(), isNull);
    await tester.pumpWidget(const SizedBox());
  });

  testWidgets('legacy drop token is ignored and cannot auto-start work', (
    tester,
  ) async {
    final state = quickState(legacyPending: true);
    final calls = <String>[];
    Future<Object?> api(String method, List<Object?> args) async {
      calls.add(method);
      return Map<String, dynamic>.from(state);
    }

    await tester.pumpWidget(DocFitApp(api: api));
    await tester.pump(const Duration(seconds: 4));
    expect(find.byKey(const Key('zeroClickCountdown')), findsNothing);
    expect(calls, isNot(contains('start_zero_click')));
    expect(state['running'], isFalse);
    expect(tester.takeException(), isNull);
    await tester.pumpWidget(const SizedBox());
  });
}
