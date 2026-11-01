import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:docfit_ui/main.dart';
import 'package:docfit_ui/features/workspace/workspace_adapters.dart';

void main() {
  testWidgets('state hotkeys route tabs and do not stack helper dialogs', (tester) async {
    tester.view.physicalSize = const Size(1400, 900);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);
    final hotkeyResponses = <List<String>>[
      ['table_template'],
      ['table_sketch'],
      ['panel', 'panel'],
      ['panel'],
    ];
    Future<Object?> api(String method, List<Object?> args) async {
      if (method == 'get_state') {
        return {
          'hotkey_requests': hotkeyResponses.isEmpty ? [] : hotkeyResponses.removeAt(0),
          'files': [],
          'range': {'enabled': false, 'start': '1', 'end': '1'},
          'progress': {'steps': [], 'visited': []},
          'live': {},
          'results': [],
          'options': {},
          'card_options': {},
          'running': false,
        };
      }
      return {'ok': true};
    }

    await tester.pumpWidget(DocFitApp(api: api));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 100));
    expect(find.byType(TableTemplatesAdapter), findsOneWidget);

    await tester.pump(const Duration(milliseconds: 1100));
    await tester.pump();
    expect(find.byType(TableSketchAdapter), findsOneWidget);

    await tester.pump(const Duration(milliseconds: 1100));
    await tester.pump();
    expect(find.byType(Dialog), findsOneWidget);
    await tester.pump(const Duration(milliseconds: 1100));
    await tester.pump();
    expect(find.byType(Dialog), findsOneWidget);
  });
}
