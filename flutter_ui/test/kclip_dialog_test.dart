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
    expect(find.text('고정한 항목은 남고 나머지를 지웁니다.'), findsOneWidget);
    await tester.tap(find.text('취소'));
    await tester.pumpAndSettle();
    expect(calls, isNot(contains('clear')));

    await tester.tap(find.byKey(const ValueKey('kclip-clear-all')));
    await tester.pumpAndSettle();
    await tester.tap(find.text('지우기'));
    await tester.pumpAndSettle();
    expect(calls, contains('clear'));
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
          body: SizedBox(height: 760, child: KClipPanel(api: api)),
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

  testWidgets('몽땅클립보드에 네이티브 끌어 놓기 영역을 표시한다', (tester) async {
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
      body: SizedBox(height: 760, child: KClipPanel(api: api)),
    )));
    await tester.pumpAndSettle();
    expect(find.byKey(const ValueKey('kclip-drop-zone')), findsOneWidget);
    expect(find.text('파일·폴더·이미지·웹 링크를 여기에 끌어 놓으세요'), findsOneWidget);
  });
}
