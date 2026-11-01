import 'package:docfit_ui/features/live/helper_panel_screen.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('loads shortcuts, displays registration conflicts, and saves edits', (tester) async {
    final calls = <List<Object?>>[];
    await tester.pumpWidget(MaterialApp(home: Scaffold(body: HelperPanelScreen(api: (method, args) async {
      calls.add([method, args]);
      if (args.first == 'get') {
        return {'ok': true, 'bindings': {'panel': 'Ctrl+Alt+J', 'table_template': 'Ctrl+Alt+T', 'table_sketch': 'Ctrl+Alt+S'},
          'failed': [{'name': 'panel', 'hotkey': 'Ctrl+Alt+J', 'reason': '이미 사용 중'}]};
      }
      return {'ok': true, 'bindings': {'panel': 'Ctrl+Shift+P', 'table_template': 'Ctrl+Alt+T', 'table_sketch': 'Ctrl+Alt+S'}, 'failed': []};
    }))));
    await tester.pumpAndSettle();
    expect(find.textContaining('다른 프로그램이 사용 중'), findsOneWidget);
    await tester.enterText(find.byKey(const Key('hotkey-panel')), 'Ctrl+Shift+P');
    await tester.tap(find.text('단축키 저장'));
    await tester.pumpAndSettle();
    expect(calls.last[0], 'live_hotkeys');
    expect(find.byKey(const Key('hotkey-conflict-panel')), findsNothing);
  });
}
