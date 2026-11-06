import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:docfit_ui/features/kclip/kclip_dialog.dart';

void main() {
  testWidgets('동의해야 켤 수 있고, 켜면 목록·고정·되돌려 올리기가 보인다', (tester) async {
    tester.view.physicalSize = const Size(1200, 900);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);
    var running = false;
    final calls = <String>[];
    Future<Object?> api(String method, List<Object?> args) async {
      if (method == 'window_control') return {'ok': true, 'maximized': false};
      expect(method, 'kclip');
      final action = args[0] as String;
      calls.add(action);
      switch (action) {
        case 'status':
          return {
            'ok': true,
            'running': running,
            'available': true,
            'consent': '동의 안내',
            'status': running
                ? {
                    'items': 2,
                    'hotkey': 'Ctrl+Shift+V',
                    'hotkey_ok': true,
                    'paused': false,
                  }
                : {},
          };
        case 'enable':
          expect((args[1] as Map)['consent'], true);
          running = true;
          return {'ok': true, 'running': true};
        case 'list':
          return {
            'ok': true,
            'items': [
              {'id': 1, 'kind': 'text', 'preview': '업무보고(안)', 'pinned': false},
              {
                'id': 2,
                'kind': 'image',
                'preview': '그림 640×480',
                'pinned': true,
              },
            ],
          };
        case 'settings_get':
          return {
            'ok': true,
            'settings': {
              'max_items': 50,
              'max_total_mb': 200,
              'max_age_days': 30,
              'auto_paste': true,
            },
          };
        case 'get':
          return {
            'ok': true,
            'id': 2,
            'kind': 'image',
            'data':
                'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/pV8AAAAASUVORK5CYII=',
          };
      }
      return {'ok': true};
    }

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: SizedBox(height: 760, child: KClipPanel(api: api)),
        ),
      ),
    );
    await tester.pump(const Duration(milliseconds: 20));
    expect(find.text('동의 안내'), findsOneWidget);
    final enable = find.byKey(const ValueKey('kclip-enable'));
    expect(tester.widget<FilledButton>(enable).onPressed, isNull);
    await tester.tap(find.byKey(const ValueKey('kclip-consent')));
    await tester.pump();
    await tester.tap(enable);
    await tester.pump(const Duration(milliseconds: 20));
    expect(calls, contains('enable'));
    expect(find.text('업무보고(안)'), findsOneWidget);
    expect(find.textContaining('기록 중 · 2개'), findsOneWidget);
    final itemTiles = tester
        .widgetList<ListTile>(
          find.descendant(
            of: find.byType(ListView),
            matching: find.byType(ListTile),
          ),
        )
        .toList();
    expect((itemTiles.first.title as Text).data, '그림 640×480');
    expect((itemTiles.first.leading as Tooltip).message, '그림');
    await tester.tap(find.byKey(const ValueKey('kclip-item-2')));
    await tester.pumpAndSettle();
    expect(calls, contains('get'));
    expect(find.byType(Image), findsNWidgets(2));
    await tester.tap(find.text('닫기'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('업무보고(안)'));
    await tester.pumpAndSettle();
    expect(find.text('업무보고(안)'), findsWidgets);
    expect(calls, isNot(contains('restore')));
    await tester.tap(find.text('다시 복사'));
    await tester.pumpAndSettle();
    expect(calls, contains('restore'));
    await tester.tap(find.byTooltip('고정(지워지지 않음)'));
    await tester.pumpAndSettle();
    expect(calls, contains('pin'));
    calls.clear();
    await tester.tap(find.byKey(const ValueKey('kclip-clear-all')));
    await tester.pumpAndSettle();
    expect(find.textContaining('고정한 항목 1개는 남고'), findsOneWidget);
    await tester.tap(find.text('취소'));
    await tester.pumpAndSettle();
    expect(calls, isNot(contains('clear')));

    await tester.tap(find.byKey(const ValueKey('kclip-clear-all')));
    await tester.pumpAndSettle();
    await tester.tap(find.text('지우기'));
    await tester.pumpAndSettle();
    expect(calls, contains('clear'));
  });

  testWidgets('표 항목에만 항목 메뉴가 보이고 음영 없이 복사를 호출한다', (tester) async {
    tester.view.physicalSize = const Size(1200, 900);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);
    final calls = <String>[];
    Map? copyPayload;
    Future<Object?> api(String method, List<Object?> args) async {
      if (method == 'window_control') return {'ok': true, 'maximized': false};
      final action = args[0] as String;
      calls.add(action);
      switch (action) {
        case 'status':
          return {
            'ok': true,
            'running': true,
            'available': true,
            'consent': '동의 안내',
            'status': {'items': 3, 'hotkey': 'Ctrl+Shift+V', 'hotkey_ok': true, 'paused': false},
          };
        case 'list':
          return {
            'ok': true,
            'items': [
              {'id': 1, 'kind': 'text', 'preview': 'a b 1 2 · 서식 포함', 'pinned': false},
              {'id': 2, 'kind': 'text', 'preview': '웹에서 복사한 글 · 서식 포함', 'pinned': false},
              {'id': 3, 'kind': 'text', 'preview': '일반 글', 'pinned': false},
            ],
          };
        case 'is_table':
          return {'ok': true, 'table': (args[1] as Map)['id'] == 1};
        case 'copy_no_shade':
          copyPayload = args[1] as Map;
          return {'ok': true, 'removed': 3, 'message': '셀 배경을 지웠습니다. 한/글에서 Ctrl+V로 붙여넣으세요.'};
        case 'settings_get':
          return {'ok': true, 'settings': {'max_items': 50, 'max_total_mb': 200, 'max_age_days': 30, 'auto_paste': true}};
      }
      return {'ok': true};
    }

    await tester.pumpWidget(
      MaterialApp(home: Scaffold(body: SizedBox(height: 760, child: KClipPanel(api: api)))),
    );
    await tester.pumpAndSettle();
    // 서식 포함 글 항목 둘만 표 여부를 묻고, 표인 1번에만 메뉴가 생긴다.
    expect(calls.where((c) => c == 'is_table').length, 2);
    expect(find.byKey(const ValueKey('kclip-item-menu-1')), findsOneWidget);
    expect(find.byKey(const ValueKey('kclip-item-menu-2')), findsNothing);
    expect(find.byKey(const ValueKey('kclip-item-menu-3')), findsNothing);
    await tester.tap(find.byKey(const ValueKey('kclip-item-menu-1')));
    await tester.pumpAndSettle();
    await tester.tap(find.text('음영 없이 복사'));
    await tester.pumpAndSettle();
    expect(copyPayload?['id'], 1);
    expect(find.textContaining('셀 배경을 지웠습니다'), findsOneWidget);
  });

  testWidgets('몽땅클립보드 Excel 표는 전용 음영 제거 경로를 사용한다', (tester) async {
    final sentActions = <String>[];
    Future<Object?> api(String method, List<Object?> args) async {
      if (method == 'excel_table') {
        sentActions.add(args[0] as String);
        return {'ok': true, 'rows': 1, 'cols': 1, 'cleaned': {}};
      }
      switch (args[0]) {
        case 'status':
          return {
            'ok': true,
            'running': true,
            'available': true,
            'status': {'paused': false},
          };
        case 'list':
          return {'ok': true, 'items': []};
        case 'settings_get':
          return {'ok': true, 'settings': {}};
      }
      return {'ok': true};
    }

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: SizedBox(height: 760, child: KClipPanel(api: api)),
        ),
      ),
    );
    await tester.pumpAndSettle();
    expect(find.byKey(const ValueKey('kclip-excel-table')), findsOneWidget);
    await tester.tap(find.byKey(const ValueKey('kclip-excel-table')));
    await tester.pumpAndSettle();
    expect(sentActions, ['paste_clean']);
  });

  testWidgets('사이드바 진입에서는 메모와 드롭 안내를 숨긴다', (tester) async {
    Future<Object?> api(String method, List<Object?> args) async {
      if (method == 'set_drop_target') return {'ok': true};
      if (args[0] == 'status') return {'ok': true, 'running': true, 'available': true, 'status': {}};
      if (args[0] == 'list') return {'ok': true, 'items': []};
      if (args[0] == 'settings_get') return {'ok': true, 'settings': {}};
      return {'ok': true};
    }
    await tester.pumpWidget(MaterialApp(home: Scaffold(body: SizedBox(width: 360, height: 760, child: KClipPanel(api: api)))));
    await tester.pumpAndSettle();
    expect(find.byKey(const ValueKey('kclip-memo')), findsNothing);
    expect(find.byKey(const ValueKey('kclip-drop-zone')), findsNothing);
    for (final c in const ['전체', '글', '그림', '파일', '폴더', '웹']) {
      expect(find.byKey(ValueKey('kclip-category-$c')), findsOneWidget);
    }
  });

  testWidgets('메모 입력을 에이전트 항목 추가 명령으로 보내고 창 제어를 제공한다', (tester) async {
    final sent = <(String, Map)>[];
    Future<Object?> api(String method, List<Object?> args) async {
      if (method == 'set_drop_target') return {'ok': true};
      if (method == 'kclip') {
        final action = args[0] as String;
        final payload = Map<String, Object?>.from(args[1] as Map);
        if (action == 'add_text') sent.add((action, payload));
        switch (action) {
          case 'status':
            return {
              'ok': true,
              'running': true,
              'available': true,
              'status': {'paused': false},
            };
          case 'list':
            return {'ok': true, 'items': []};
          case 'settings_get':
            return {'ok': true, 'settings': {}};
          case 'add_text':
            return {'ok': true, 'created': true};
        }
      }
      return {'ok': true};
    }

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: SizedBox(height: 760, child: KClipPanel(api: api, mode: KClipEntryMode.hotkey)),
        ),
      ),
    );
    await tester.pumpAndSettle();
    expect(find.byKey(const ValueKey('kclip-memo')), findsOneWidget);
    expect(find.byTooltip('최소화'), findsOneWidget);
    expect(find.byTooltip('항상 위'), findsOneWidget);
    await tester.enterText(
      find.byKey(const ValueKey('kclip-memo')),
      '회의 일정 메모',
    );
    await tester.tap(find.byTooltip('메모 추가'));
    await tester.pumpAndSettle();
    expect(sent.single.$1, 'add_text');
    expect(sent.single.$2['text'], '회의 일정 메모');
    expect(find.text('메모를 클립보드 항목에 추가했습니다.'), findsOneWidget);
  });

  testWidgets('단축키 진입에서만 네이티브 끌어 놓기 영역을 표시한다', (tester) async {
    Future<Object?> api(String method, List<Object?> args) async {
      if (method == 'set_drop_target') return {'ok': true};
      if (method != 'kclip') return {'ok': true};
      final action = args[0] as String;
      switch (action) {
        case 'status':
          return {'ok': true, 'running': true, 'available': true, 'status': {}};
        case 'list':
          return {'ok': true, 'items': []};
        case 'settings_get':
          return {'ok': true, 'settings': {}};
      }
      return {'ok': true};
    }

    await tester.pumpWidget(MaterialApp(home: Scaffold(
      body: SizedBox(height: 760, child: KClipPanel(api: api, mode: KClipEntryMode.hotkey)),
    )));
    await tester.pumpAndSettle();
    expect(find.byKey(const ValueKey('kclip-drop-zone')), findsOneWidget);
    expect(find.text('파일·폴더·이미지·웹 링크를 여기에 끌어 놓으세요'), findsOneWidget);
  });

  testWidgets('최대화/복원 단추는 네이티브 창 명령을 보내고 대화상자를 창 전체로 펼친다', (tester) async {
    tester.view.physicalSize = const Size(1400, 1000);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);
    var maximized = false;
    final windowCalls = <String>[];
    Future<Object?> api(String method, List<Object?> args) async {
      if (method == 'window_control') {
        final action = args[0] as String;
        windowCalls.add(action);
        if (action == 'toggle_maximize') maximized = !maximized;
        return {'ok': true, 'maximized': maximized};
      }
      if (method != 'kclip') return {'ok': true};
      switch (args[0]) {
        case 'status':
          return {'ok': true, 'running': true, 'available': true, 'status': {}};
        case 'list':
          return {'ok': true, 'items': []};
        case 'settings_get':
          return {'ok': true, 'settings': {}};
      }
      return {'ok': true};
    }

    await tester.pumpWidget(MaterialApp(home: Builder(
      builder: (context) => TextButton(
        onPressed: () => showKClipDialog(context, api),
        child: const Text('열기'),
      ),
    )));
    await tester.tap(find.text('열기'));
    await tester.pumpAndSettle();
    expect(windowCalls, ['state']);
    final panel = find.byType(KClipPanel);
    expect(tester.getSize(panel).width, lessThanOrEqualTo(720));
    expect(find.byTooltip('최대화'), findsOneWidget);

    await tester.tap(find.byKey(const ValueKey('kclip-maximize')));
    await tester.pumpAndSettle();
    expect(windowCalls, ['state', 'toggle_maximize']);
    expect(find.byTooltip('이전 크기로 복원'), findsOneWidget);
    expect(tester.getSize(panel), const Size(1400, 1000));

    await tester.tap(find.byKey(const ValueKey('kclip-maximize')));
    await tester.pumpAndSettle();
    expect(windowCalls.last, 'toggle_maximize');
    expect(find.byTooltip('최대화'), findsOneWidget);
    expect(tester.getSize(panel).width, lessThanOrEqualTo(720));
  });

  group('스티커 메모형 관리창', () {
    late List<(String, String, Map)> calls;
    late Map<String, Object?> saved;

    Future<Object?> api(String method, List<Object?> args) async {
      final action = args.isEmpty ? '' : '${args[0]}';
      final payload = args.length > 1 && args[1] is Map ? Map.from(args[1] as Map) : <dynamic, dynamic>{};
      calls.add((method, action, payload));
      if (method == 'kclip_window') {
        if (action == 'set') saved = {...saved, ...payload.cast<String, Object?>()};
        return {'ok': true, 'window': saved};
      }
      if (method == 'window_control') return {'ok': true, 'maximized': false};
      if (method != 'kclip') return {'ok': true};
      switch (action) {
        case 'status':
          return {'ok': true, 'running': true, 'available': true, 'status': {}};
        case 'list':
          return {'ok': true, 'items': []};
        case 'settings_get':
          return {'ok': true, 'settings': {}};
      }
      return {'ok': true};
    }

    Future<void> pumpHost(WidgetTester tester, ValueChanged<bool> onClosed) async {
      tester.view.physicalSize = const Size(1200, 900);
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.reset);
      var hits = 0;
      await tester.pumpWidget(MaterialApp(home: Scaffold(body: Builder(
        builder: (context) => Column(children: [
          TextButton(
            onPressed: () => showKClipStickyWindow(context, api).then((_) => onClosed(true)),
            child: const Text('열기'),
          ),
          StatefulBuilder(builder: (context, set) => TextButton(
            key: const ValueKey('app-behind'),
            onPressed: () => set(() => hits++),
            child: Text('앱 단추 $hits'),
          )),
        ]),
      ))));
    }

    setUp(() {
      calls = [];
      saved = {'x': 300, 'y': 120, 'width': 500, 'height': 560, 'always_on_top': false};
    });

    testWidgets('저장된 위치·크기로 열리고 뒤의 앱 화면을 계속 쓸 수 있다', (tester) async {
      var closed = false;
      await pumpHost(tester, (v) => closed = v);
      await tester.tap(find.text('열기'));
      await tester.pumpAndSettle();
      final window = find.byKey(const ValueKey('kclip-sticky-window'));
      expect(window, findsOneWidget);
      expect(tester.getTopLeft(window), const Offset(300, 120));
      expect(tester.getSize(window), const Size(500, 560));
      expect(calls.where((c) => c.$1 == 'kclip_window').first.$2, 'open');
      // 모달이 아니므로 창 밖의 앱 단추가 눌린다.
      await tester.tap(find.byKey(const ValueKey('app-behind')));
      await tester.pumpAndSettle();
      expect(find.text('앱 단추 1'), findsOneWidget);
      expect(closed, isFalse);
    });

    testWidgets('머리글 끌기·모서리 크기 조절·항상 위를 저장한다', (tester) async {
      await pumpHost(tester, (_) {});
      await tester.tap(find.text('열기'));
      await tester.pumpAndSettle();
      final window = find.byKey(const ValueKey('kclip-sticky-window'));

      await tester.drag(find.byKey(const ValueKey('kclip-header')), const Offset(-100, 60));
      await tester.pumpAndSettle();
      expect(tester.getTopLeft(window).dx, closeTo(200, 0.5));
      expect(tester.getTopLeft(window).dy, closeTo(180, 0.5));
      expect(saved['x'], 200);
      expect(saved['y'], 180);

      await tester.drag(find.byKey(const ValueKey('kclip-resize')), const Offset(80, -100));
      await tester.pumpAndSettle();
      expect(tester.getSize(window).width, closeTo(580, 0.5));
      expect(tester.getSize(window).height, closeTo(460, 0.5));
      expect(saved['width'], 580);
      expect(saved['height'], 460);

      await tester.tap(find.byKey(const ValueKey('kclip-always-on-top-toggle')));
      await tester.pumpAndSettle();
      expect(saved['always_on_top'], isTrue);
      expect(find.byTooltip('항상 위 해제'), findsOneWidget);
    });

    testWidgets('앱 창 밖으로 나간 저장 위치는 보이는 곳으로 옮기고 최소 크기를 지킨다', (tester) async {
      saved = {'x': 5000, 'y': -300, 'width': 100, 'height': 9000, 'always_on_top': true};
      await pumpHost(tester, (_) {});
      await tester.tap(find.text('열기'));
      await tester.pumpAndSettle();
      final window = find.byKey(const ValueKey('kclip-sticky-window'));
      final rect = tester.getRect(window);
      expect(rect.width, KClipStickyWindow.minWidth);
      expect(rect.height, 900);
      expect(rect.right, lessThanOrEqualTo(1200));
      expect(rect.top, 0);
      expect(find.byTooltip('항상 위 해제'), findsOneWidget);
    });

    testWidgets('닫기는 관리창만 닫고 기록 에이전트에는 명령을 보내지 않는다', (tester) async {
      var closed = false;
      await pumpHost(tester, (v) => closed = v);
      await tester.tap(find.text('열기'));
      await tester.pumpAndSettle();
      final kclipBefore = calls.where((c) => c.$1 == 'kclip').map((c) => c.$2).toList();
      await tester.tap(find.byKey(const ValueKey('kclip-close')));
      await tester.pumpAndSettle();
      expect(find.byKey(const ValueKey('kclip-sticky-window')), findsNothing);
      expect(closed, isTrue);
      expect(calls.where((c) => c.$1 == 'kclip_window').last.$2, 'close');
      final kclipAfter = calls.where((c) => c.$1 == 'kclip').map((c) => c.$2).toList();
      expect(kclipAfter, kclipBefore);
      expect(kclipAfter, isNot(contains('disable')));
      expect(kclipAfter, isNot(contains('pause')));
    });
  });

  testWidgets('창 명령이 거절되면 상태를 유지하고 이유를 보여준다', (tester) async {
    Future<Object?> api(String method, List<Object?> args) async {
      if (method == 'window_control') {
        return args[0] == 'state'
            ? {'ok': true, 'maximized': false}
            : {'ok': false, 'maximized': false, 'message': '사이드메뉴 모드에서는 창 크기를 바꿀 수 없습니다.'};
      }
      if (args[0] == 'status') return {'ok': true, 'running': false, 'available': true};
      return {'ok': true};
    }
    await tester.pumpWidget(MaterialApp(home: Scaffold(
      body: SizedBox(height: 760, child: KClipPanel(api: api)),
    )));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const ValueKey('kclip-maximize')));
    await tester.pumpAndSettle();
    expect(find.byTooltip('최대화'), findsOneWidget);
    expect(find.text('사이드메뉴 모드에서는 창 크기를 바꿀 수 없습니다.'), findsOneWidget);
  });

  testWidgets('항목별 삭제·고정 해제와 모두 지우기(고정 보존 안내)', (tester) async {
    tester.view.physicalSize = const Size(1200, 900);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);
    final sent = <List<Object?>>[];
    Future<Object?> api(String method, List<Object?> args) async {
      if (method == 'window_control') return {'ok': true, 'maximized': false};
      final action = args[0] as String;
      final payload = args.length > 1 ? args[1] : null;
      sent.add([action, payload]);
      switch (action) {
        case 'status':
          return {
            'ok': true,
            'running': true,
            'available': true,
            'consent': '동의 안내',
            'status': {'items': 2, 'paused': false},
          };
        case 'list':
          return {
            'ok': true,
            'items': [
              {'id': 1, 'kind': 'text', 'preview': '일반', 'pinned': false},
              {'id': 2, 'kind': 'text', 'preview': '고정됨', 'pinned': true},
            ],
          };
        case 'settings_get':
          return {'ok': true, 'settings': {'max_items': 50}};
      }
      return {'ok': true};
    }

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: SizedBox(height: 760, child: KClipPanel(api: api)),
        ),
      ),
    );
    await tester.pump(const Duration(milliseconds: 20));
    await tester.pumpAndSettle();

    await tester.tap(find.byTooltip('고정 풀기'));
    await tester.pumpAndSettle();
    expect(sent.any((c) => c[0] == 'pin' &&
        (c[1] as Map)['id'] == 2 && (c[1] as Map)['pinned'] == false), isTrue);

    await tester.tap(find.byTooltip('지우기').first);
    await tester.pumpAndSettle();
    expect(sent.any((c) => c[0] == 'delete' && (c[1] as Map)['id'] == 2 ||
        c[0] == 'delete' && (c[1] as Map)['id'] == 1), isTrue);

    sent.clear();
    await tester.tap(find.byKey(const ValueKey('kclip-clear-all')));
    await tester.pumpAndSettle();
    expect(find.textContaining('고정한 항목 1개는 남고'), findsOneWidget);
    await tester.tap(find.text('지우기'));
    await tester.pumpAndSettle();
    final clear = sent.firstWhere((c) => c[0] == 'clear');
    expect((clear[1] as Map)['keep_pinned'], true);
  });
}
