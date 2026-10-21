import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:docfit_ui/main.dart';

Map<String, dynamic> initialState() => <String, dynamic>{
  'files': <Map<String, String>>[],
  'mode': 'spacing',
  'can_start': true,
  'conversion_target': 'hwpx',
  'conversion_targets': [
    {
      'format': 'hwpx',
      'label': 'HWPX',
      'enabled': true,
      'reason': 'kordoc 지원 입력',
    },
    {'format': 'pdf', 'label': 'PDF', 'enabled': true, 'reason': '한/글 COM 필요'},
    {'format': 'docx', 'label': 'DOCX', 'enabled': true, 'reason': 'Pandoc 사용'},
    {'format': 'epub', 'label': 'EPUB', 'enabled': true, 'reason': 'Pandoc 사용'},
    {'format': 'html', 'label': 'HTML', 'enabled': true, 'reason': 'Pandoc 사용'},
  ],
  'running': false,
  'range': {'enabled': false, 'start': '1', 'end': '1'},
  'results': [],
  'stages': [
    {
      'key': 'reset_spacing',
      'label': '문서 전체 자간 초기화',
      'example': '예: 1',
      'on': true,
      'default': true,
    },
    {
      'key': 'style_unify',
      'label': '서식통일',
      'example': '예: 2',
      'on': false,
      'default': false,
    },
  ],
  'default_saved': false,
  'profiles': [
    {'id': '', 'name': '기본 서식'},
    {'id': 'abc', 'name': '[마포구] 보고서'},
  ],
  'profile': '',
  'options': {
    'autoclose': true,
    'unify_result_window': false,
    'verify': false,
    'integrity_report_file': false,
    'final_review_file': false,
    'log_file': false,
    'check_updates': true,
    'developer_mode': false,
    'always_on_top': true,
  },
  'version': 'test',
};

void main() {
  testWidgets('general editor is visible and excluded tldraw has no menu', (
    tester,
  ) async {
    final state = initialState();
    Future<Object?> api(String name, List<Object?> args) async => state;
    await tester.pumpWidget(DocFitApp(api: api));
    await tester.pumpAndSettle();
    expect(find.byTooltip('표/다이어그램'), findsOneWidget);
    expect(find.byTooltip('문서 도구'), findsNothing);
    state['options']['developer_mode'] = true;
    state['options']['diagram_editor_enabled'] = true;
    await tester.pump(const Duration(seconds: 2));
    await tester.pumpAndSettle();
    expect(find.byTooltip('표/다이어그램'), findsOneWidget);
    expect(find.byTooltip('문서 도구'), findsOneWidget);
    await tester.tap(find.byTooltip('문서 도구'));
    await tester.pumpAndSettle();
    expect(find.text('tldraw 편집기 (개발자 전용)'), findsNothing);
    await tester.pumpWidget(const SizedBox());
  });

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
          state['can_start'] = true;
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
      expect(find.text('3 단계면 끝나요'), findsOneWidget);
      await tester.tap(find.text('문서 추가'));
      await tester.pumpAndSettle();
      expect(find.text('문서.hwpx'), findsOneWidget);
      expect(find.text('HWPX'), findsOneWidget);
      // 문서가 들어오면 안내 영역을 접어 목록이 잘 보이게 한다.
      expect(find.text('3 단계면 끝나요'), findsNothing);
      await tester.tap(find.text('작업 방식 선택'));
      await tester.pumpAndSettle();
      await tester.ensureVisible(find.text('서식 통일'));
      await tester.tap(find.text('서식 통일'));
      await tester.pumpAndSettle();
      expect(find.textContaining('1개 문서 · 서식 통일 · 문서 전체'), findsOneWidget);
      await tester.tap(find.text('정리 시작'));
      await tester.pump(const Duration(milliseconds: 300));
      expect(
        calls.where((s) => s != 'get_state' && s != 'enable_close_guard'),
        ['add_files', 'set_mode', 'start'],
      );
      expect(find.text('문서를 정리하고 있어요'), findsOneWidget);
      await tester.tap(find.text(width >= 1000 ? '문서 선택' : '1. 문서 선택').first);
      await tester.pump(const Duration(milliseconds: 300));
      expect(find.text('문서.hwpx'), findsOneWidget);
      expect(tester.takeException(), isNull);
      await tester.pumpWidget(const SizedBox());
    });
  }

  testWidgets('four work-mode cards use distinct soft theme colors', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(1280, 900);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    final state = initialState()
      ..['files'] = [
        {'name': '문서.hwpx', 'folder': r'C:\문서'},
      ];
    Future<Object?> api(String name, List<Object?> args) async => state;

    await tester.pumpWidget(DocFitApp(api: api));
    await tester.pumpAndSettle();
    await tester.tap(find.text('작업 방식 선택'));
    await tester.pumpAndSettle();

    final expected = <String, Color>{
      'spacing': const Color(0xffe3edff),
      'unify': const Color(0xffeff8f5),
      'all': const Color(0xfffff7eb),
      'file_format': const Color(0xfff4f1ff),
    };
    final actual = <Color>{};
    for (final entry in expected.entries) {
      final card = tester.widget<Material>(
        find.byKey(Key('modeCard-${entry.key}')),
      );
      actual.add(card.color!);
      if (entry.key == 'spacing') {
        expect(card.color, const Color(0xffe3edff)); // 선택된 카드
      } else {
        expect(card.color, entry.value);
      }
    }
    expect(actual.length, 4);
    await tester.pumpWidget(const SizedBox());
  });

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
      find.ancestor(
        of: find.text('정리 시작'),
        matching: find.byWidgetPredicate((w) => w is FilledButton),
      ),
    );
    expect(start.onPressed, isNull);

    // 빠른 설정: 서랍에서 바로 저장한다.
    await tester.tap(find.byTooltip('설정'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('저장 뒤 결과 검수'));
    await tester.pumpAndSettle();
    expect(calls.last, ['set_option', 'verify', true]);
    for (final option in [
      ('작업로그 파일 만들기', 'log_file'),
      ('무결성검사 JSON 파일 만들기', 'integrity_report_file'),
      ('최종검수 JSON 파일 만들기', 'final_review_file'),
    ]) {
      await tester.ensureVisible(find.text(option.$1));
      await tester.tap(find.text(option.$1));
      await tester.pumpAndSettle();
      expect(calls.last, ['set_option', option.$2, true]);
    }
    expect(tester.takeException(), isNull);
    await tester.pumpWidget(const SizedBox());
  });

  testWidgets('all card can exclude spacing and runs as format', (
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
    // 선택한 자간 정리 카드의 '표 제외'를 켜면 table_spacing을 끈다.
    expect(find.text('표 제외'), findsOneWidget);
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
    expect(find.text('표 제외'), findsOneWidget); // 선택한 카드의 옵션만 표시
    await tester.ensureVisible(find.byKey(const Key('excludeTablesSwitch')));
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
      if (name == 'set_mode') state['mode'] = args.first;
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
    await tester.tap(find.text('한 번에 적용').first);
    await tester.pumpAndSettle();
    await tester.ensureVisible(
      find.byKey(const Key('allExcludePagefitSwitch')),
    );
    await tester.tap(find.byKey(const Key('allExcludePagefitSwitch')));
    await tester.pumpAndSettle();
    expect(calls.last, ['set_card_option', 'all_exclude_pagefit', true]);
    final linespacingSwitch = find.byKey(const Key('allLinespacingSwitch'));
    await tester.ensureVisible(linespacingSwitch);
    expect(tester.widget<Switch>(linespacingSwitch).value, isTrue);
    await tester.tap(linespacingSwitch);
    await tester.pumpAndSettle();
    expect(calls.last, ['set_card_option', 'all_linespacing', false]);
    expect(tester.widget<Switch>(linespacingSwitch).value, isFalse);
    expect(tester.takeException(), isNull);
    await tester.pumpWidget(const SizedBox());
  });

  testWidgets('format manager routes drops and edits formats', (tester) async {
    tester.view.physicalSize = const Size(1024, 900);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    final calls = <List<Object?>>[];
    final state = initialState();
    state['files'] = [
      {'name': '문서.hwp', 'folder': r'C:\문서'},
    ];
    state['mode'] = 'all';
    state['profiles'] = [
      {
        'id': '',
        'name': '기본 서식',
        'title': '기본 서식',
        'organization': '',
        'builtin': true,
        'source': '',
        'active': true,
      },
      {
        'id': 'abc',
        'name': '[마포구] 보고서',
        'title': '보고서',
        'organization': '마포구',
        'builtin': false,
        'source': '예시.hwpx',
        'active': false,
      },
    ];
    state['format_task'] = {'busy': false, 'file': ''};
    Future<Object?> api(String name, List<Object?> args) async {
      if (name != 'get_state') calls.add([name, ...args]);
      if (name == 'format_profile') {
        return {
          'ok': true,
          'data': {'id': 'abc', 'name': '보고서', 'revision': 'r', 'nodes': []},
        };
      }
      if (name == 'rename_profile' && args[1] == '중복') {
        return {...state, 'notice': '이미 사용 중인 서식 이름입니다.'};
      }
      if (name == 'delete_profile') {
        state['profiles'] = [(state['profiles'] as List).first];
      }
      return Map<String, dynamic>.from(state);
    }

    await tester.pumpWidget(DocFitApp(api: api));
    await tester.pumpAndSettle();
    await tester.tap(find.text('작업 방식 선택'));
    await tester.pumpAndSettle();
    await tester.ensureVisible(find.byKey(const Key('openFormatsButton')));
    await tester.tap(find.byKey(const Key('openFormatsButton')));
    await tester.pumpAndSettle();
    // 창이 열려 있는 동안 끌어 놓은 파일은 서식 복제로 간다.
    expect(calls.last, ['set_drop_target', 'format']);
    expect(find.text('예시 보고서(HWP·HWPX)를 이 창에 끌어다 놓으세요'), findsOneWidget);
    expect(find.text('예시 보고서: 예시.hwpx'), findsOneWidget);
    // 기본 서식은 이름 바꾸기·삭제가 없다.
    expect(find.byKey(const Key('deleteFormat-')), findsNothing);
    await tester.tap(find.byKey(const Key('addFormatFile')));
    await tester.pumpAndSettle();
    expect(calls.last, ['add_format_file']);
    // 이름 바꾸기: 겹치는 이름이면 이유를 보여 준다.
    await tester.tap(find.byKey(const Key('renameFormat-abc')));
    await tester.pumpAndSettle();
    await tester.enterText(find.byKey(const Key('formatNameField')), '중복');
    await tester.tap(find.text('저장'));
    await tester.pumpAndSettle();
    expect(calls.last, ['rename_profile', 'abc', '중복', '마포구']);
    expect(find.text('이미 사용 중인 서식 이름입니다.'), findsWidgets);
    await tester.tap(find.byKey(const Key('useFormat-abc')));
    await tester.pumpAndSettle();
    expect(calls.last, ['set_profile', 'abc']);
    await tester.tap(find.byKey(const Key('editFormat-abc')));
    await tester.pumpAndSettle();
    expect(calls.last.first, 'format_profile');
    expect(calls.last[1], 'get');
    expect(find.textContaining('편집할 분석 자료가 없습니다'), findsOneWidget);
    await tester.tap(find.text('닫기'));
    await tester.pumpAndSettle();
    // 삭제는 확인한 뒤에만 한다.
    await tester.tap(find.byKey(const Key('deleteFormat-abc')));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const Key('confirmDeleteFormat')));
    await tester.pumpAndSettle();
    expect(calls.last, ['delete_profile', 'abc']);
    expect(find.text('예시 보고서: 예시.hwpx'), findsNothing);
    await tester.tap(find.byTooltip('닫기').last);
    await tester.pumpAndSettle();
    expect(
      calls.any((c) => c[0] == 'set_drop_target' && c[1] == 'documents'),
      isTrue,
    );
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
    state['completion'] = {
      'message': '처리 완료 · 성공 1개 / 실패 0개',
      'details': ['예상 절약 시간 00분 20초'],
    };
    state['format_review'] = {
      'status': 'failed',
      'checked': 3,
      'issues': [
        {'text': '[저장 결과] 확인 필요'},
      ],
      'not_checkable': [],
      'unresolved': [],
    };
    await tester.pump(const Duration(seconds: 1));
    await tester.pumpAndSettle();
    expect(find.text('처리 완료 · 성공 1개 / 실패 0개'), findsOneWidget);
    expect(find.textContaining('예상 절약 시간 00분 20초'), findsOneWidget);
    expect(find.textContaining('불일치 1개'), findsOneWidget);
    expect(find.text('아직 저장된 결과가 없어요.'), findsOneWidget);

    state['results'] = [
      {
        'name': '문서(자간조정).hwpx',
        'path': r'C:\문서\문서(자간조정).hwpx',
        'source': '문서.hwpx',
        'pages': 3,
      },
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

  testWidgets('work log is rendered and managed by the Flutter dialog', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(1024, 900);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    final calls = <String>[];
    final state = initialState();
    var logText = '처리 시작\n첫 단계 완료';
    Future<Object?> api(String name, List<Object?> args) async {
      calls.add(name);
      if (name == 'get_log') return logText;
      if (name == 'clear_log') {
        logText = '';
        return logText;
      }
      return Map<String, dynamic>.from(state);
    }

    await tester.pumpWidget(DocFitApp(api: api));
    await tester.pumpAndSettle();
    await tester.tap(find.byTooltip('작업 로그'));
    await tester.pumpAndSettle();
    expect(find.text('처리 시작\n첫 단계 완료'), findsOneWidget);
    logText = '새로 추가된 로그';
    await tester.tap(find.byKey(const Key('refreshLogButton')));
    await tester.pumpAndSettle();
    expect(find.text('새로 추가된 로그'), findsOneWidget);
    await tester.tap(find.byKey(const Key('clearLogButton')));
    await tester.pumpAndSettle();
    expect(find.text('아직 기록된 내용이 없어요.'), findsOneWidget);
    expect(calls.where((name) => name == 'get_log').length, 2);
    expect(calls, contains('clear_log'));
    await tester.tap(find.text('닫기'));
    await tester.pumpAndSettle();
    expect(tester.takeException(), isNull);
    await tester.pumpWidget(const SizedBox());
  });

  testWidgets(
    'settings opens the Flutter abbreviation manager without a Tk command',
    (tester) async {
      tester.view.physicalSize = const Size(1024, 900);
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);
      final calls = <String>[];
      Future<Object?> api(String name, List<Object?> args) async {
        calls.add(name);
        if (name == 'get_abbreviations') {
          return {
            'api_version': 1,
            'ok': true,
            'error': null,
            'data': {
              'entries': [],
              'format_kinds': {'title1': '제목 서식1'},
              'use_defaults': true,
              'running': false,
            },
          };
        }
        return initialState();
      }

      await tester.pumpWidget(DocFitApp(api: api));
      await tester.pumpAndSettle();
      await tester.tap(find.byTooltip('설정'));
      await tester.pumpAndSettle();
      await tester.scrollUntilVisible(
        find.text('준말 등록·관리'),
        300,
        scrollable: find.byType(Scrollable).last,
      );
      await tester.tap(find.text('준말 등록·관리'));
      await tester.pumpAndSettle();
      expect(
        find.byKey(const Key('abbreviationManagerDialog')),
        findsOneWidget,
      );
      expect(
        calls.where(
          (name) => name != 'get_state' && name != 'enable_close_guard',
        ),
        ['get_abbreviations'],
      );
      await tester.pumpWidget(const SizedBox());
    },
  );

  for (final resetMethod in ['add_files', 'next_job']) {
    testWidgets('$resetMethod resets the previous document page range', (
      tester,
    ) async {
      tester.view.physicalSize = const Size(1024, 900);
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);
      final state = initialState();
      state['files'] = [
        {'name': '이전.hwpx', 'path': r'C:\문서\이전.hwpx'},
      ];
      state['range'] = {'enabled': true, 'start': '5', 'end': '7'};
      final calls = <List<Object?>>[];
      Future<Object?> api(String name, List<Object?> args) async {
        if (name != 'get_state') calls.add([name, ...args]);
        if (name == resetMethod) {
          state['files'] = resetMethod == 'next_job'
              ? []
              : [
                  {'name': '새문서.hwpx', 'path': r'C:\문서\새문서.hwpx'},
                ];
          state['range'] = {'enabled': false, 'start': '1', 'end': '1'};
        } else if (name == 'add_files') {
          state['files'] = [
            {'name': '새문서.hwpx', 'path': r'C:\문서\새문서.hwpx'},
          ];
        }
        if (name == 'start') state['running'] = true;
        return Map<String, dynamic>.from(state);
      }

      await tester.pumpWidget(DocFitApp(api: api));
      await tester.pumpAndSettle();
      if (resetMethod == 'next_job') {
        await tester.tap(find.text('결과 확인').first);
        await tester.pumpAndSettle();
        await tester.tap(find.text('새 작업 시작'));
        await tester.pumpAndSettle();
      }
      await tester.tap(find.text('문서 추가'));
      await tester.pumpAndSettle();
      await tester.tap(find.text('작업 방식 선택'));
      await tester.pumpAndSettle();
      await tester.tap(find.text('정리 시작'));
      await tester.pump(const Duration(milliseconds: 300));
      expect(calls.last, ['start', 'spacing', false, '1', '1']);
      expect(tester.takeException(), isNull);
      await tester.pumpWidget(const SizedBox());
    });
  }

  testWidgets(
    'unchanged backend polls preserve an unfinished page range edit',
    (tester) async {
      tester.view.physicalSize = const Size(1024, 900);
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);
      final state = initialState();
      state['files'] = [
        {'name': '문서.hwpx'},
      ];
      state['range'] = {'enabled': true, 'start': '1', 'end': '9'};
      await tester.pumpWidget(
        DocFitApp(api: (name, args) async => Map<String, dynamic>.from(state)),
      );
      await tester.pumpAndSettle();
      await tester.tap(find.text('작업 방식 선택'));
      await tester.pumpAndSettle();
      await tester.ensureVisible(find.widgetWithText(TextField, '시작 쪽'));
      await tester.enterText(find.widgetWithText(TextField, '시작 쪽'), '');
      await tester.pump(const Duration(seconds: 1));
      await tester.pumpAndSettle();
      expect(
        tester
            .widget<TextField>(find.widgetWithText(TextField, '시작 쪽'))
            .controller!
            .text,
        '',
      );
      expect(find.textContaining('올바르게 입력하세요'), findsOneWidget);
      await tester.pumpWidget(const SizedBox());
    },
  );

  testWidgets('a delayed poll cannot replace a newer command result', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(1024, 900);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    final state = initialState();
    state['files'] = [
      {'name': '문서.hwpx'},
    ];
    final delayedPoll = Completer<Object?>();
    var holdPoll = false;
    final calls = <List<Object?>>[];
    Future<Object?> api(String name, List<Object?> args) async {
      if (name == 'get_state' && holdPoll) {
        holdPoll = false;
        return delayedPoll.future;
      }
      if (name != 'get_state') calls.add([name, ...args]);
      if (name == 'set_mode') state['mode'] = args.first;
      if (name == 'start') state['running'] = true;
      return Map<String, dynamic>.from(state);
    }

    await tester.pumpWidget(DocFitApp(api: api));
    await tester.pumpAndSettle();
    await tester.tap(find.text('작업 방식 선택'));
    await tester.pumpAndSettle();
    final oldState = Map<String, dynamic>.from(state);
    holdPoll = true;
    await tester.pump(const Duration(seconds: 1));
    await tester.ensureVisible(find.text('서식 통일'));
    await tester.tap(find.text('서식 통일'));
    await tester.pumpAndSettle();
    delayedPoll.complete(oldState);
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 50));
    await tester.tap(find.text('정리 시작'));
    await tester.pump(const Duration(milliseconds: 300));
    expect(calls.last, ['start', 'unify', false, '1', '1']);
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

  testWidgets('file format mode shows radial output targets and selects PDF', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(1024, 900);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    final calls = <List<Object?>>[];
    final state = initialState();
    state['files'] = [
      {'name': 'report.pdf', 'folder': r'C:\Docs'},
    ];
    Future<Object?> api(String name, List<Object?> args) async {
      if (name != 'get_state') calls.add([name, ...args]);
      if (name == 'set_mode') state['mode'] = args.first;
      if (name == 'set_conversion_target') {
        state['conversion_target'] = args.first;
      }
      return Map<String, dynamic>.from(state);
    }

    await tester.pumpWidget(DocFitApp(api: api));
    await tester.pumpAndSettle();
    await tester.tap(find.text('작업 방식 선택'));
    await tester.pumpAndSettle();
    await tester.ensureVisible(find.text('파일포맷 변경'));
    await tester.tap(find.text('파일포맷 변경').first);
    await tester.pumpAndSettle();
    expect(find.text('변환할 포맷을 고르세요'), findsOneWidget);
    expect(find.text('DOCX'), findsOneWidget);
    await tester.tap(find.text('PDF').last);
    await tester.pumpAndSettle();
    // 형식을 고르면 '변환 시작'을 누르지 않아도 바로 변환을 시작한다(사용자 지시, 2026-10-15).
    final picked = calls.indexWhere(
      (call) => call.first == 'set_conversion_target',
    );
    expect(picked, isNot(-1));
    expect(calls[picked].last, 'pdf');
    expect(calls.length, greaterThan(picked + 1));
    expect(calls[picked + 1].take(2), ['start', 'file_format']);
    expect(tester.takeException(), isNull);
    await tester.pumpWidget(const SizedBox());
  });

  testWidgets('HWPX exports TXT through the radial picker', (tester) async {
    tester.view.physicalSize = const Size(1024, 900);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    final calls = <List<Object?>>[];
    final state = initialState();
    (state['conversion_targets'] as List).add({
      'format': 'txt',
      'label': 'TXT',
      'enabled': true,
      'reason': 'HWPX 글 추출',
    });
    state['files'] = [
      {'name': 'report.hwpx', 'folder': r'C:\Docs'},
    ];
    Future<Object?> api(String name, List<Object?> args) async {
      if (name != 'get_state') calls.add([name, ...args]);
      if (name == 'set_mode') state['mode'] = args.first;
      if (name == 'set_conversion_target') {
        state['conversion_target'] = args.first;
      }
      return Map<String, dynamic>.from(state);
    }

    await tester.pumpWidget(DocFitApp(api: api));
    await tester.pumpAndSettle();
    await tester.tap(find.text('작업 방식 선택'));
    await tester.pumpAndSettle();
    await tester.ensureVisible(find.text('파일포맷 변경'));
    await tester.tap(find.text('파일포맷 변경').first);
    await tester.pumpAndSettle();
    expect(find.text('변환할 포맷을 고르세요'), findsOneWidget);
    expect(find.text('DOCX'), findsOneWidget);
    await tester.tap(find.text('TXT').last);
    await tester.pumpAndSettle();
    // 형식을 고르면 '변환 시작'을 누르지 않아도 바로 변환을 시작한다(사용자 지시, 2026-10-15).
    final picked = calls.indexWhere(
      (call) => call.first == 'set_conversion_target',
    );
    expect(picked, isNot(-1));
    expect(calls[picked].last, 'txt');
    expect(calls.length, greaterThan(picked + 1));
    expect(calls[picked + 1].take(2), ['start', 'file_format']);
    expect(tester.takeException(), isNull);
    await tester.pumpWidget(const SizedBox());
  });

  testWidgets('HWPX exports MD through the radial picker', (tester) async {
    tester.view.physicalSize = const Size(1024, 900);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    final calls = <List<Object?>>[];
    final state = initialState();
    (state['conversion_targets'] as List).add({
      'format': 'md',
      'label': 'MD',
      'enabled': true,
      'reason': 'HWPX 글 추출',
    });
    state['files'] = [
      {'name': 'report.hwpx', 'folder': r'C:\Docs'},
    ];
    Future<Object?> api(String name, List<Object?> args) async {
      if (name != 'get_state') calls.add([name, ...args]);
      if (name == 'set_mode') state['mode'] = args.first;
      if (name == 'set_conversion_target') {
        state['conversion_target'] = args.first;
      }
      return Map<String, dynamic>.from(state);
    }

    await tester.pumpWidget(DocFitApp(api: api));
    await tester.pumpAndSettle();
    await tester.tap(find.text('작업 방식 선택'));
    await tester.pumpAndSettle();
    await tester.ensureVisible(find.text('파일포맷 변경'));
    await tester.tap(find.text('파일포맷 변경').first);
    await tester.pumpAndSettle();
    expect(find.text('변환할 포맷을 고르세요'), findsOneWidget);
    expect(find.text('DOCX'), findsOneWidget);
    await tester.tap(find.text('MD').last);
    await tester.pumpAndSettle();
    // 형식을 고르면 '변환 시작'을 누르지 않아도 바로 변환을 시작한다(사용자 지시, 2026-10-15).
    final picked = calls.indexWhere(
      (call) => call.first == 'set_conversion_target',
    );
    expect(picked, isNot(-1));
    expect(calls[picked].last, 'md');
    expect(calls.length, greaterThan(picked + 1));
    expect(calls[picked + 1].take(2), ['start', 'file_format']);
    expect(tester.takeException(), isNull);
    await tester.pumpWidget(const SizedBox());
  });

  testWidgets('file format screen explains unavailable converters', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(1024, 900);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    final state = initialState();
    state['files'] = [
      {'name': 'report.xlsx', 'folder': r'C:\Docs'},
    ];
    state['conversion_targets'] = [
      {
        'format': 'hwpx',
        'label': 'HWPX',
        'enabled': false,
        'reason': 'kordoc 4.21.30 설치 필요 (Node.js 20+)',
      },
      {
        'format': 'pdf',
        'label': 'PDF',
        'enabled': false,
        'reason': 'kordoc 4.21.30 설치 필요 (Node.js 20+)',
      },
      {
        'format': 'docx',
        'label': 'DOCX',
        'enabled': false,
        'reason': 'kordoc 4.21.30 설치 필요 (Node.js 20+)',
      },
      {
        'format': 'epub',
        'label': 'EPUB',
        'enabled': false,
        'reason': 'kordoc 4.21.30 설치 필요 (Node.js 20+)',
      },
    ];
    state['can_start'] = false;
    Future<Object?> api(String name, List<Object?> args) async {
      if (name == 'set_mode') state['mode'] = args.first;
      return Map<String, dynamic>.from(state);
    }

    await tester.pumpWidget(DocFitApp(api: api));
    await tester.pumpAndSettle();
    await tester.tap(find.text('작업 방식 선택'));
    await tester.pumpAndSettle();
    await tester.ensureVisible(find.text('파일포맷 변경'));
    await tester.tap(find.text('파일포맷 변경').first);
    await tester.pumpAndSettle();
    expect(
      find.byKey(const Key('conversionPrerequisiteNotice')),
      findsOneWidget,
    );
    expect(
      tester
          .widget<Text>(find.byKey(const Key('conversionPrerequisiteNotice')))
          .data,
      contains('kordoc 4.21.30 설치 필요'),
    );
    final button = tester.widget<FilledButton>(
      find.widgetWithText(FilledButton, '변환 시작'),
    );
    expect(button.onPressed, isNull);
    expect(tester.takeException(), isNull);
    await tester.pumpWidget(const SizedBox());
  });

  for (final width in [420.0, 1024.0]) {
    testWidgets(
      'floating format picker cancels and commits only a chosen format at $width',
      (tester) async {
        tester.view.physicalSize = Size(width, 700);
        tester.view.devicePixelRatio = 1;
        addTearDown(tester.view.resetPhysicalSize);
        addTearDown(tester.view.resetDevicePixelRatio);
        final state = initialState();
        final choices = <Object?>[];
        state['files'] = [
          {'name': 'report.hwpx', 'folder': r'C:\Docs'},
        ];
        Future<Object?> api(String method, List<Object?> args) async {
          if (method == 'set_mode') state['mode'] = args.first;
          if (method == 'set_conversion_target') {
            choices.add(args.first);
            state['conversion_target'] = args.first;
          }
          return Map<String, dynamic>.from(state);
        }

        await tester.pumpWidget(DocFitApp(api: api));
        await tester.pumpAndSettle();
        await tester.tap(find.text('작업 방식 선택'));
        await tester.pumpAndSettle();
        await tester.ensureVisible(find.text('파일포맷 변경'));
        await tester.tap(find.text('파일포맷 변경').first);
        await tester.pumpAndSettle();
        expect(
          find.byKey(const Key('floatingConversionPicker')),
          findsOneWidget,
        );
        await tester.tap(find.byKey(const Key('cancelConversionPicker')));
        await tester.pumpAndSettle();
        expect(choices, isEmpty);
        expect(find.byKey(const Key('floatingConversionPicker')), findsNothing);
        await tester.ensureVisible(
          find.byKey(const Key('openConversionPicker')),
        );
        await tester.tap(find.byKey(const Key('openConversionPicker')));
        await tester.pumpAndSettle();
        await tester.sendKeyEvent(LogicalKeyboardKey.escape);
        await tester.pumpAndSettle();
        expect(choices, isEmpty);
        await tester.tap(find.byKey(const Key('openConversionPicker')));
        await tester.pumpAndSettle();
        await tester.tap(
          find.descendant(
            of: find.byKey(const Key('conversionSlice-pdf')),
            matching: find.text('PDF'),
          ),
        );
        await tester.pumpAndSettle();
        expect(choices, ['pdf']);
        expect(find.byKey(const Key('floatingConversionPicker')), findsNothing);
        expect(find.text('선택한 결과 형식: PDF'), findsOneWidget);
        expect(tester.takeException(), isNull);
        await tester.pumpWidget(const SizedBox());
      },
    );
  }

  testWidgets(
    'native document drop opens one floating picker without reopening on polls',
    (tester) async {
      final state = initialState();
      state['mode'] = 'file_format';
      Future<Object?> api(String method, List<Object?> args) async =>
          Map<String, dynamic>.from(state);
      await tester.pumpWidget(DocFitApp(api: api));
      await tester.pumpAndSettle();
      state['files'] = [
        {'name': 'report.hwpx', 'folder': r'C:\Docs'},
      ];
      await tester.pump(const Duration(seconds: 1));
      await tester.pumpAndSettle();
      expect(find.byKey(const Key('floatingConversionPicker')), findsOneWidget);
      await tester.pump(const Duration(seconds: 2));
      await tester.pumpAndSettle();
      expect(find.byKey(const Key('floatingConversionPicker')), findsOneWidget);
      await tester.tap(find.byKey(const Key('cancelConversionPicker')));
      await tester.pumpAndSettle();
      await tester.pump(const Duration(seconds: 2));
      await tester.pumpAndSettle();
      expect(find.byKey(const Key('floatingConversionPicker')), findsNothing);
      expect(tester.takeException(), isNull);
      await tester.pumpWidget(const SizedBox());
    },
  );

  testWidgets(
    'unavailable or invalidated floating choices never change the target',
    (tester) async {
      tester.view.physicalSize = const Size(1024, 820);
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);
      final state = initialState();
      state['mode'] = 'file_format';
      state['files'] = [
        {'name': 'report.hwpx', 'folder': r'C:\Docs'},
      ];
      state['conversion_targets'] = [
        {
          'format': 'hwpx',
          'label': 'HWPX',
          'enabled': false,
          'reason': '엔진 설치 필요',
        },
        {
          'format': 'pdf',
          'label': 'PDF',
          'enabled': true,
          'reason': '한/글 내장 PDF',
        },
      ];
      final choices = <Object?>[];
      Future<Object?> api(String method, List<Object?> args) async {
        if (method == 'set_conversion_target') choices.add(args.first);
        return Map<String, dynamic>.from(state);
      }

      await tester.pumpWidget(DocFitApp(api: api));
      await tester.pumpAndSettle();
      await tester.tap(find.text('HWPX').first);
      await tester.pumpAndSettle();
      expect(choices, isEmpty);
      expect(find.byKey(const Key('floatingConversionPicker')), findsOneWidget);
      state['conversion_targets'] = [
        {
          'format': 'pdf',
          'label': 'PDF',
          'enabled': false,
          'reason': '문서를 다시 선택하세요',
        },
      ];
      await tester.pump(const Duration(seconds: 1));
      await tester.pumpAndSettle();
      await tester.tap(find.text('PDF').last);
      await tester.pumpAndSettle();
      expect(choices, isEmpty);
      // Clicking outside the floating window is also a non-mutating cancel.
      await tester.tapAt(const Offset(2, 2));
      await tester.pumpAndSettle();
      expect(find.byKey(const Key('floatingConversionPicker')), findsNothing);
      expect(tester.takeException(), isNull);
      await tester.pumpWidget(const SizedBox());
    },
  );
}
