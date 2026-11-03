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
            'status': running ? {'items': 2, 'hotkey': 'Ctrl+Shift+V', 'hotkey_ok': true, 'paused': false} : {},
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
              {'id': 2, 'kind': 'image', 'preview': '그림 640×480', 'pinned': true},
            ],
          };
        case 'settings_get':
          return {
            'ok': true,
            'settings': {'max_items': 50, 'max_total_mb': 200, 'max_age_days': 30, 'auto_paste': true},
          };
        case 'get':
          return {'ok': true, 'id': 2, 'kind': 'image', 'data': 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/pV8AAAAASUVORK5CYII='};
      }
      return {'ok': true};
    }

    await tester.pumpWidget(MaterialApp(home: Scaffold(body: SizedBox(height: 700, child: KClipPanel(api: api)))));
    await tester.pumpAndSettle();
    expect(find.text('동의 안내'), findsOneWidget);
    final enable = find.byKey(const ValueKey('kclip-enable'));
    expect(tester.widget<FilledButton>(enable).onPressed, isNull);
    await tester.tap(find.byKey(const ValueKey('kclip-consent')));
    await tester.pump();
    await tester.tap(enable);
    await tester.pumpAndSettle();
    expect(calls, contains('enable'));
    expect(find.text('업무보고(안)'), findsOneWidget);
    expect(find.textContaining('기록 중 · 2개'), findsOneWidget);
    final itemTiles = tester.widgetList<ListTile>(find.descendant(of: find.byType(ListView), matching: find.byType(ListTile))).toList();
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

  testWidgets('엑셀 표 변환 버튼과 칸 배경색 옵션을 제공한다', (tester) async {
    Future<Object?> api(String method, List<Object?> args) async {
      switch (args[0]) {
        case 'status': return {'ok':true,'running':true,'available':true,'status':{'paused':false}};
        case 'list': return {'ok':true,'items':[]};
        case 'settings_get': return {'ok':true,'settings':{}};
      }
      return {'ok':true};
    }
    await tester.pumpWidget(MaterialApp(home: Scaffold(body:SizedBox(height:700,child:KClipPanel(api:api)))));
    await tester.pumpAndSettle();
    expect(find.byKey(const ValueKey('kclip-excel-table')), findsOneWidget);
    expect(find.text('칸 배경색 빼기'), findsOneWidget);
    expect(tester.widget<Checkbox>(find.byType(Checkbox).last).value, isFalse);
  });
}
