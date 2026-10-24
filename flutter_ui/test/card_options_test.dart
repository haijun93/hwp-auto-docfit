import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:docfit_ui/main.dart';

Map<String, dynamic> initialTestState() => <String, dynamic>{
  'files': <Map<String, String>>[
    {'name': '테스트.hwpx', 'folder': r'C:\문서'},
  ],
  'mode': 'spacing',
  'can_start': true,
  'conversion_target': 'hwpx',
  'conversion_targets': [
    {'format': 'hwpx', 'label': 'HWPX', 'enabled': true},
  ],
  'running': false,
  'range': {'enabled': false, 'start': '1', 'end': '1'},
  'results': [],
  'stages': [
    {'key': 'reset_spacing', 'label': '문서 전체 자간 초기화', 'on': false, 'default': false},
    {'key': 'page_fit', 'label': '페이지 맞춤', 'on': true, 'default': true},
    {'key': 'body_spacing', 'label': '본문 자간', 'on': true, 'default': true},
  ],
  'card_options': {
    'spacing_enabled': true,
    'spacing_exclude_pagefit': false,
    'spacing_exclude_reset': true,
    'all_exclude_linespacing': false,
  },
  'options': {
    'autoclose': true,
    'developer_mode': false,
  },
  'version': 'test',
};

void main() {
  testWidgets('spacing card renders exclude switches with new defaults', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(1024, 900);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    final calls = <List<Object?>>[];
    final state = initialTestState();
    Future<Object?> api(String name, List<Object?> args) async {
      if (name != 'get_state') calls.add([name, ...args]);
      if (name == 'set_card_option') {
        (state['card_options'] as Map)[args[0] as String] = args[1];
      }
      return Map<String, dynamic>.from(state);
    }

    await tester.pumpWidget(DocFitApp(api: api));
    await tester.pumpAndSettle();
    await tester.tap(find.text('작업 방식 선택'));
    await tester.pumpAndSettle();

    // 자간 정리 카드의 '페이지 맞춤 제외' (기본 off = false)
    expect(find.text('페이지 맞춤 제외'), findsWidgets);
    final pagefitSwitch = tester.widget<Switch>(
      find.byKey(const Key('spacingExcludePagefitSwitch')),
    );
    expect(pagefitSwitch.value, isFalse);

    // 자간 정리 카드의 '기존 자간 초기화 제외' (기본 on = true)
    expect(find.text('기존 자간 초기화 제외'), findsOneWidget);
    final resetSwitch = tester.widget<Switch>(
      find.byKey(const Key('spacingExcludeResetSwitch')),
    );
    expect(resetSwitch.value, isTrue);

    // 스위치 전환 시 set_card_option 호출
    await tester.tap(find.byKey(const Key('spacingExcludePagefitSwitch')));
    await tester.pumpAndSettle();
    expect(calls.last, ['set_card_option', 'spacing_exclude_pagefit', true]);

    await tester.tap(find.byKey(const Key('spacingExcludeResetSwitch')));
    await tester.pumpAndSettle();
    expect(calls.last, ['set_card_option', 'spacing_exclude_reset', false]);

    await tester.pumpWidget(const SizedBox());
  });

  testWidgets('all mode card renders line spacing exclude switch', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(1024, 900);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    final calls = <List<Object?>>[];
    final state = initialTestState();
    state['mode'] = 'all';
    Future<Object?> api(String name, List<Object?> args) async {
      if (name != 'get_state') calls.add([name, ...args]);
      if (name == 'set_card_option') {
        (state['card_options'] as Map)[args[0] as String] = args[1];
      }
      return Map<String, dynamic>.from(state);
    }

    await tester.pumpWidget(DocFitApp(api: api));
    await tester.pumpAndSettle();
    await tester.tap(find.text('작업 방식 선택'));
    await tester.pumpAndSettle();

    // '한 번에 적용' 카드의 '줄 간격 적용 제외' (기본 off = false)
    expect(find.text('줄 간격 적용 제외'), findsOneWidget);
    final linespacingSwitch = tester.widget<Switch>(
      find.byKey(const Key('allExcludeLinespacingSwitch')),
    );
    expect(linespacingSwitch.value, isFalse);

    await tester.tap(find.byKey(const Key('allExcludeLinespacingSwitch')));
    await tester.pumpAndSettle();
    expect(calls.last, ['set_card_option', 'all_exclude_linespacing', true]);

    await tester.pumpWidget(const SizedBox());
  });

  testWidgets('spacing card blocks start when both spacing and pagefit are off', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(1024, 900);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    final state = initialTestState();
    // spacing_enabled 꺼짐 + spacing_exclude_pagefit 켜짐 (페이지 맞춤도 제외됨)
    state['card_options']['spacing_enabled'] = false;
    state['card_options']['spacing_exclude_pagefit'] = true;

    Future<Object?> api(String name, List<Object?> args) async =>
        Map<String, dynamic>.from(state);

    await tester.pumpWidget(DocFitApp(api: api));
    await tester.pumpAndSettle();
    await tester.tap(find.text('작업 방식 선택'));
    await tester.pumpAndSettle();

    expect(find.text('자간 정리 또는 페이지 맞춤을 하나 이상 켜 주세요.'), findsOneWidget);

    final startButton = tester.widget<FilledButton>(
      find.ancestor(
        of: find.text('정리 시작'),
        matching: find.byWidgetPredicate((w) => w is FilledButton),
      ),
    );
    expect(startButton.onPressed, isNull);

    await tester.pumpWidget(const SizedBox());
  });
}
