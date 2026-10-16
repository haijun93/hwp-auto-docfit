import 'package:docfit_ui/main.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'workspace_test.dart' show initialState;

void main() {
  testWidgets(
    'spacing and page fit are independent, with page-only and no-op states',
    (tester) async {
      tester.view.physicalSize = const Size(1280, 1100);
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);
      final state = initialState();
      state['files'] = [
        {'name': '원본.hwpx', 'folder': r'C:\문서'},
      ];
      state['card_options'] = {
        'spacing_enabled': true,
        'spacing_page_fit': false,
      };
      final calls = <List<Object?>>[];
      Future<Object?> api(String name, List<Object?> args) async {
        if (name != 'get_state') calls.add([name, ...args]);
        if (name == 'set_card_option') {
          (state['card_options'] as Map)[args[0]] = args[1];
        }
        return Map<String, dynamic>.from(state);
      }

      await tester.pumpWidget(DocFitApp(api: api));
      await tester.pumpAndSettle();
      await tester.tap(find.text('작업 방식 선택'));
      await tester.pumpAndSettle();
      await tester.tap(find.byKey(const Key('spacingPageFitSwitch')));
      await tester.pumpAndSettle();
      expect(calls.last, ['set_card_option', 'spacing_page_fit', true]);
      expect(
        tester
            .widget<Switch>(find.byKey(const Key('spacingEnabledSwitch')))
            .value,
        isTrue,
      );
      await tester.tap(find.byKey(const Key('spacingEnabledSwitch')));
      await tester.pumpAndSettle();
      expect(calls.last, ['set_card_option', 'spacing_enabled', false]);
      expect(
        tester
            .widget<Switch>(find.byKey(const Key('spacingPageFitSwitch')))
            .value,
        isTrue,
      );
      expect(
        tester
            .widget<Switch>(find.byKey(const Key('resetSpacingSwitch')))
            .onChanged,
        isNull,
      );
      expect(
        tester
            .widget<Switch>(find.byKey(const Key('tableSpacingSwitch')))
            .onChanged,
        isNull,
      );
      expect(find.textContaining('자간·장평·줄 병합은 그대로'), findsOneWidget);
      final startButton = find.ancestor(
        of: find.text('정리 시작'),
        matching: find.byType(FilledButton),
      );
      expect(tester.widget<FilledButton>(startButton).onPressed, isNotNull);
      await tester.tap(find.byKey(const Key('spacingPageFitSwitch')));
      await tester.pumpAndSettle();
      expect(find.text('자간 정리 또는 페이지 맞춤을 하나 이상 켜 주세요.'), findsOneWidget);
      expect(tester.widget<FilledButton>(startButton).onPressed, isNull);
      expect(tester.takeException(), isNull);
      await tester.pumpWidget(const SizedBox());
    },
  );
}
