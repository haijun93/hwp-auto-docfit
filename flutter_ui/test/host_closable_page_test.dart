import 'package:docfit_ui/core/close_guards.dart';
import 'package:docfit_ui/features/workspace/tab_navigation_shell.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

/// 자료함·노트북 화면(사용자 보고 2026-11-07):
/// 처음 화면으로 돌아가는 단추가 있고, 앱을 닫을 때 종료를 막지 않는다.
void main() {
  Future<NavigatorState> open(WidgetTester tester) async {
    await tester.pumpWidget(const MaterialApp(home: Scaffold(body: Text('home'))));
    final nav = tester.state<NavigatorState>(find.byType(Navigator));
    nav.push(MaterialPageRoute<void>(
      builder: (_) => const HostClosablePage(title: '자료함', child: Scaffold(body: Text('library'))),
    ));
    await tester.pumpAndSettle();
    return nav;
  }

  testWidgets('back button returns to the first screen', (tester) async {
    await open(tester);
    expect(find.text('library'), findsOneWidget);
    await tester.tap(find.byKey(const ValueKey('host-page-back')));
    await tester.pumpAndSettle();
    expect(find.text('library'), findsNothing);
    expect(find.text('home'), findsOneWidget);
  });

  testWidgets('host close removes the page and releases its guard', (tester) async {
    await open(tester);
    var accepted = false;
    await tester.runAsync(() async {
      final future = CloseGuards.prepareAll();
      for (var i = 0; i < 20; i++) {
        await tester.pump(const Duration(milliseconds: 50));
      }
      accepted = await future;
    });
    await tester.pumpAndSettle();
    expect(accepted, isTrue);
    expect(find.text('library'), findsNothing);
    expect(find.text('home'), findsOneWidget);
  });
}
