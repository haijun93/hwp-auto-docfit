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
    await tester.tap(find.text('업무보고(안)'));
    await tester.pumpAndSettle();
    expect(calls, contains('restore'));
    await tester.tap(find.byTooltip('고정(지워지지 않음)'));
    await tester.pumpAndSettle();
    expect(calls, contains('pin'));
  });
}
