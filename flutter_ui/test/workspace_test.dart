import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:docfit_ui/main.dart';

Map<String, dynamic> initialState() => <String, dynamic>{
  'files': <Map<String, String>>[],
  'mode': 'spacing',
  'running': false,
  'range': {'enabled': false, 'start': '1', 'end': '1'},
  'results': [],
  'stages': [
    {'key': 'reset_spacing', 'label': '문서 전체 자간 초기화', 'example': '예: 1', 'on': true, 'default': true},
    {'key': 'style_unify', 'label': '서식통일', 'example': '예: 2', 'on': false, 'default': false},
  ],
  'default_saved': false,
  'profiles': [
    {'id': '', 'name': '기본 서식'},
    {'id': 'abc', 'name': '[마포구] 보고서'},
  ],
  'profile': '',
  'options': {'autoclose': true, 'verify': false, 'check_updates': true},
  'version': 'test',
};

void main() {
  for (final width in [420.0, 1024.0]) {
    testWidgets('navigation and scoped commands at width $width', (
      tester,
    ) async {
      tester.view.physicalSize = Size(width, 820);
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);
      final calls = <String>[];
      final state = initialState();
      Future<Object?> api(String name, List<Object?> args) async {
        calls.add(name);
        if (name == 'add_files') {
          state['files'] = [
            {'name': '문서.hwpx', 'folder': r'C:\문서'},
          ];
        }
        if (name == 'set_mode') state['mode'] = args.first;
        if (name == 'start') {
          expect(args, ['unify', false, '1', '1']);
          state['running'] = true;
        }
        return Map<String, dynamic>.from(state);
      }

      await tester.pumpWidget(DocFitApp(api: api));
      await tester.pumpAndSettle();
      expect(find.text('세 단계면 끝나요'), findsOneWidget);
      await tester.tap(find.text('문서 추가'));
      await tester.pumpAndSettle();
      expect(find.text('문서.hwpx'), findsOneWidget);
      expect(find.text('HWPX'), findsOneWidget);
      // 문서가 들어오면 안내 영역을 접어 목록이 잘 보이게 한다.
      expect(find.text('세 단계면 끝나요'), findsNothing);
      await tester.tap(find.text('작업 방식 선택'));
      await tester.pumpAndSettle();
      await tester.ensureVisible(find.text('서식 통일'));
      await tester.tap(find.text('서식 통일'));
      await tester.pumpAndSettle();
      expect(find.textContaining('1개 문서 · 서식 통일 · 문서 전체'), findsOneWidget);
      await tester.tap(find.text('정리 시작'));
      await tester.pump(const Duration(milliseconds: 300));
      expect(calls.where((s) => s != 'get_state'), [
        'add_files',
        'set_mode',
        'start',
      ]);
      expect(find.text('문서를 정리하고 있어요'), findsOneWidget);
      await tester.tap(find.text(width >= 1000 ? '문서 선택' : '1. 문서 선택').first);
      await tester.pump(const Duration(milliseconds: 300));
      expect(find.text('문서.hwpx'), findsOneWidget);
      expect(tester.takeException(), isNull);
      await tester.pumpWidget(const SizedBox());
    });
  }

  testWidgets('stages, page range and quick settings change in place', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(1024, 900);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    final calls = <List<Object?>>[];
    final state = initialState();
    state['files'] = [
      {'name': '문서.hwp', 'folder': r'C:\문서'},
    ];
    Future<Object?> api(String name, List<Object?> args) async {
      if (name != 'get_state') calls.add([name, ...args]);
      if (name == 'set_stage') {
        final stages = state['stages'] as List;
        (stages.firstWhere((s) => s['key'] == args[0]) as Map)['on'] = args[1];
      }
      if (name == 'set_option') {
        (state['options'] as Map)[args[0] as String] = args[1];
      }
      if (name == 'set_range') {
        state['range'] = {'enabled': args[0], 'start': args[1], 'end': args[2]};
      }
      return Map<String, dynamic>.from(state);
    }

    await tester.pumpWidget(DocFitApp(api: api));
    await tester.pumpAndSettle();
    await tester.tap(find.text('작업 방식 선택'));
    await tester.pumpAndSettle();

    // 세부 작업: 펼쳐서 바로 켜고 끈다.
    expect(find.text('세부 작업  1/2'), findsOneWidget);
    await tester.ensureVisible(find.text('세부 작업  1/2'));
    await tester.tap(find.text('세부 작업  1/2'));
    await tester.pumpAndSettle();
    await tester.ensureVisible(find.text('2. 서식통일'));
    await tester.tap(find.text('2. 서식통일'));
    await tester.pumpAndSettle();
    expect(calls.last, ['set_stage', 'style_unify', true]);
    expect(find.text('세부 작업  2/2'), findsOneWidget);

    // 쪽 범위: 잘못된 범위면 시작 버튼을 막는다.
    await tester.ensureVisible(find.text('쪽 지정'));
    await tester.tap(find.text('쪽 지정'));
    await tester.pumpAndSettle();
    expect(calls.last, ['set_range', true, '1', '1']);
    await tester.enterText(find.widgetWithText(TextField, '시작 쪽'), '5');
    await tester.enterText(find.widgetWithText(TextField, '끝 쪽'), '3');
    await tester.pump();
    expect(find.textContaining('올바르게 입력하세요'), findsOneWidget);
    final start = tester.widget<FilledButton>(
      find.ancestor(of: find.text('정리 시작'), matching: find.byWidgetPredicate((w) => w is FilledButton)),
    );
    expect(start.onPressed, isNull);

    // 빠른 설정: 서랍에서 바로 저장한다.
    await tester.tap(find.byTooltip('설정'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('저장 뒤 결과 검수'));
    await tester.pumpAndSettle();
    expect(calls.last, ['set_option', 'verify', true]);
    expect(tester.takeException(), isNull);
    await tester.pumpWidget(const SizedBox());
  });

  testWidgets('all card can exclude spacing and runs as format', (tester) async {
    tester.view.physicalSize = const Size(1024, 900);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    final calls = <List<Object?>>[];
    final state = initialState();
    state['files'] = [
      {'name': '문서.hwp', 'folder': r'C:\문서'},
    ];
    state['include_spacing'] = true;
    Future<Object?> api(String name, List<Object?> args) async {
      if (name != 'get_state') calls.add([name, ...args]);
      if (name == 'set_mode') {
        state['mode'] = state['include_spacing'] == true ? 'all' : 'format';
      }
      if (name == 'set_include_spacing') {
        state['include_spacing'] = args.first;
        state['mode'] = args.first == true ? 'all' : 'format';
      }
      return Map<String, dynamic>.from(state);
    }

    await tester.pumpWidget(DocFitApp(api: api));
    await tester.pumpAndSettle();
    await tester.tap(find.text('작업 방식 선택'));
    await tester.pumpAndSettle();
    // 카드는 세 장이고 '서식 적용' 카드는 없다.
    expect(find.text('서식 적용'), findsNothing);
    await tester.tap(find.text('한 번에 적용'));
    await tester.pumpAndSettle();
    expect(calls.last, ['set_mode', 'all']);
    expect(find.text('결과: 문서이름(일괄적용).hwpx'), findsOneWidget);
    await tester.tap(find.byKey(const Key('includeSpacingSwitch')));
    await tester.pumpAndSettle();
    expect(calls.last, ['set_include_spacing', false]);
    expect(find.text('결과: 문서이름(서식적용).hwpx'), findsOneWidget);
    expect(find.textContaining('한 번에 적용(자간 조정 제외)'), findsWidgets);
    expect(tester.takeException(), isNull);
    await tester.pumpWidget(const SizedBox());
  });

  testWidgets('spacing card can keep existing character spacing', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(1024, 900);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    final calls = <List<Object?>>[];
    final state = initialState();
    state['files'] = [
      {'name': '문서.hwp', 'folder': r'C:\문서'},
    ];
    state['reset_spacing'] = true;
    Future<Object?> api(String name, List<Object?> args) async {
      if (name != 'get_state') calls.add([name, ...args]);
      if (name == 'set_reset_spacing') {
        state['reset_spacing'] = args.first;
        state['mode'] = 'spacing';
      }
      return Map<String, dynamic>.from(state);
    }

    await tester.pumpWidget(DocFitApp(api: api));
    await tester.pumpAndSettle();
    await tester.tap(find.text('작업 방식 선택'));
    await tester.pumpAndSettle();
    expect(find.text('기존 자간 초기화'), findsOneWidget);
    await tester.tap(find.byKey(const Key('resetSpacingSwitch')));
    await tester.pumpAndSettle();
    expect(calls.last, ['set_reset_spacing', false]);
    expect(find.text('문서에 있던 자간은 그대로 두고 그 위에서 정리해요.'), findsOneWidget);
    expect(tester.takeException(), isNull);
    await tester.pumpWidget(const SizedBox());
  });

  testWidgets('spacing card toggles table spacing', (tester) async {
    tester.view.physicalSize = const Size(1024, 820);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    final calls = <List<Object?>>[];
    final state = initialState();
    state['files'] = [
      {'name': '문서.hwp', 'folder': r'C:\문서'},
    ];
    state['table_spacing'] = true;
    Future<Object?> api(String name, List<Object?> args) async {
      if (name != 'get_state') calls.add([name, ...args]);
      if (name == 'set_table_spacing') {
        state['table_spacing'] = args.first;
        state['mode'] = 'spacing';
      }
      return Map<String, dynamic>.from(state);
    }

    await tester.pumpWidget(DocFitApp(api: api));
    await tester.pumpAndSettle();
    await tester.tap(find.text('작업 방식 선택'));
    await tester.pumpAndSettle();
    // '표 제외'(기본 꺼짐)를 켜면 table_spacing을 끈다(표 제외는 세 카드에 모두 있다).
    expect(find.text('표 제외'), findsNWidgets(3));
    await tester.tap(find.byKey(const Key('tableSpacingSwitch')));
    await tester.pumpAndSettle();
    expect(calls.last, ['set_table_spacing', false]);
    expect(find.text('표 칸 안 문장은 자간 정리에서 빼요.'), findsOneWidget);
    expect(tester.takeException(), isNull);
    await tester.pumpWidget(const SizedBox());
  });

  testWidgets('all card toggles exclude tables', (tester) async {
    tester.view.physicalSize = const Size(1024, 820);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    final calls = <List<Object?>>[];
    final state = initialState();
    state['files'] = [
      {'name': '문서.hwp', 'folder': r'C:\문서'},
    ];
    state['mode'] = 'all';
    state['exclude_tables'] = false;
    Future<Object?> api(String name, List<Object?> args) async {
      if (name != 'get_state') calls.add([name, ...args]);
      if (name == 'set_exclude_tables') {
        state['exclude_tables'] = args.first;
        state['mode'] = 'all';
      }
      return Map<String, dynamic>.from(state);
    }

    await tester.pumpWidget(DocFitApp(api: api));
    await tester.pumpAndSettle();
    await tester.tap(find.text('작업 방식 선택'));
    await tester.pumpAndSettle();
    expect(find.text('표 제외'), findsNWidgets(3));   // 자간 정리·서식 통일·한 번에 적용 카드
    await tester.tap(find.byKey(const Key('excludeTablesSwitch')));
    await tester.pumpAndSettle();
    expect(calls.last, ['set_exclude_tables', true]);
    expect(find.text('표 관련 작업은 모두 빼고 정리해요. 제목·개요 서식 표는 정리해요.'), findsOneWidget);
    expect(tester.takeException(), isNull);
    await tester.pumpWidget(const SizedBox());
  });

  testWidgets('unify and all cards toggle card options', (tester) async {
    tester.view.physicalSize = const Size(1024, 1200);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    final calls = <List<Object?>>[];
    final state = initialState();
    state['files'] = [
      {'name': '문서.hwp', 'folder': r'C:\문서'},
    ];
    state['mode'] = 'unify';
    state['card_options'] = <String, Object?>{};
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
    expect(find.text('자간 정리 제외'), findsOneWidget);
    await tester.tap(find.byKey(const Key('unify_exclude_spacingSwitch')));
    await tester.pumpAndSettle();
    expect(calls.last, ['set_card_option', 'unify_exclude_spacing', true]);
    expect(find.text('서식통일이 고친 문장의 자간은 그대로 둬요.'), findsOneWidget);
    await tester.ensureVisible(find.byKey(const Key('allExcludePagefitSwitch')));
    await tester.tap(find.byKey(const Key('allExcludePagefitSwitch')));
    await tester.pumpAndSettle();
    expect(calls.last, ['set_card_option', 'all_exclude_pagefit', true]);
    expect(tester.takeException(), isNull);
    await tester.pumpWidget(const SizedBox());
  });

  testWidgets('finished job moves to results with per-file actions', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(1024, 820);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    final calls = <List<Object?>>[];
    final state = initialState();
    state['files'] = [
      {'name': '문서.hwpx', 'folder': r'C:\문서'},
    ];
    Future<Object?> api(String name, List<Object?> args) async {
      if (name != 'get_state') calls.add([name, ...args]);
      if (name == 'start') state['running'] = true;
      return Map<String, dynamic>.from(state);
    }

    await tester.pumpWidget(DocFitApp(api: api));
    await tester.pumpAndSettle();
    await tester.tap(find.text('작업 방식 선택'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('정리 시작'));
    await tester.pump(const Duration(milliseconds: 300));
    expect(find.text('문서를 정리하고 있어요'), findsOneWidget);

    state['running'] = false;
    state['results'] = [
      {'name': '문서(자간조정).hwpx', 'path': r'C:\문서\문서(자간조정).hwpx', 'source': '문서.hwpx', 'pages': 3},
    ];
    await tester.pump(const Duration(seconds: 1));
    await tester.pumpAndSettle();
    expect(find.text('문서(자간조정).hwpx'), findsOneWidget);
    expect(find.text('원본: 문서.hwpx · 3쪽'), findsOneWidget);
    await tester.tap(find.byTooltip('폴더에서 보기'));
    await tester.pumpAndSettle();
    expect(calls.last, ['show_result', 0]);
    await tester.pumpWidget(const SizedBox());
  });

  testWidgets('disconnected UI never starts work', (tester) async {
    await tester.pumpWidget(
      DocFitApp(api: (method, args) async => throw StateError('offline')),
    );
    await tester.pumpAndSettle();
    expect(find.textContaining('연결하지 못했어요'), findsOneWidget);
    final button = tester.widget<FilledButton>(
      find.widgetWithText(FilledButton, '작업 방식 선택'),
    );
    expect(button.onPressed, isNull);
    await tester.pumpWidget(const SizedBox());
  });
}
