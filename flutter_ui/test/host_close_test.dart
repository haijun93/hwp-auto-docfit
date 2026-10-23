import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:docfit_ui/core/close_guards.dart';
import 'package:docfit_ui/main.dart';
import 'package:docfit_ui/features/settings/settings_dialog.dart';
import 'workspace_test.dart' show initialState;
import 'settings_dialog_test.dart' show data;

void main() {
  test('approval waits until the editor is disposed', () async {
    final prepared = Completer<void>();
    final lease = CloseGuards.register(() async {
      prepared.complete();
      return true;
    });
    var done = false;
    final close = CloseGuards.prepareAll().then((value) {
      done = true;
      return value;
    });
    await prepared.future;
    await Future<void>.delayed(Duration.zero);
    expect(done, false);
    lease.release();
    expect(await close, true);
  });

  testWidgets('OS close cancels dirty settings, then explicit discard closes', (
    tester,
  ) async {
    final state = initialState();
    Map? pending;
    final answers = <bool>[];
    Future<Object?> api(String method, List<Object?> args) async {
      if (method == 'get_settings') {
        return {'api_version': 1, 'ok': true, 'data': data()};
      }
      if (method == 'resolve_dialog') {
        answers.add(args[1] as bool);
        pending = null;
        return {'accepted': args[1]};
      }
      if (method == 'get_pending_dialog') return pending;
      return {...state, 'pending_dialog': pending};
    }

    await tester.pumpWidget(DocFitApp(api: api));
    await tester.pumpAndSettle();
    final navigator = tester.state<NavigatorState>(
      find.byType(Navigator).first,
    );
    unawaited(
      showDialog<void>(
        context: navigator.context,
        builder: (_) => SettingsDialog(api: api),
      ),
    );
    await tester.pumpAndSettle();
    await tester.enterText(find.byKey(const ValueKey('retry_body')), '9');
    pending = {'id': 'close1', 'kind': 'app_close'};
    await tester.pump(const Duration(seconds: 1));
    await tester.pumpAndSettle();
    expect(find.text('저장하지 않은 변경사항'), findsOneWidget);
    expect(answers, isEmpty);
    await tester.tap(find.text('계속 편집'));
    await tester.pumpAndSettle();
    expect(answers, [false]);
    expect(find.byType(SettingsDialog), findsOneWidget);
    expect(
      tester
          .widget<TextField>(find.byKey(const ValueKey('retry_body')))
          .controller!
          .text,
      '9',
    );
    pending = {'id': 'close2', 'kind': 'app_close'};
    await tester.pump(const Duration(seconds: 1));
    await tester.pumpAndSettle();
    await tester.tap(find.text('변경사항 버리기'));
    await tester.pumpAndSettle();
    expect(answers, [false, true]);
    expect(find.byType(SettingsDialog), findsNothing);
    expect(tester.takeException(), isNull);
    await tester.pumpWidget(const SizedBox());
  });

  testWidgets('unregistered modal prevents host exit', (tester) async {
    final state = initialState();
    Map? pending;
    bool? approved;
    Future<Object?> api(String method, List<Object?> args) async {
      if (method == 'resolve_dialog') {
        approved = args[1] as bool;
        pending = null;
        return {'accepted': approved};
      }
      return {...state, 'pending_dialog': pending};
    }

    await tester.pumpWidget(DocFitApp(api: api));
    await tester.pumpAndSettle();
    final navigator = tester.state<NavigatorState>(
      find.byType(Navigator).first,
    );
    unawaited(
      showDialog<void>(
        context: navigator.context,
        builder: (_) => const AlertDialog(content: Text('작성 중')),
      ),
    );
    await tester.pumpAndSettle();
    pending = {'id': 'unknown', 'kind': 'app_close'};
    await tester.pump(const Duration(seconds: 1));
    await tester.pumpAndSettle();
    expect(approved, false);
    expect(find.text('작성 중'), findsOneWidget);
    await tester.pumpWidget(const SizedBox());
  });

  testWidgets('in-flight main command vetoes host exit', (tester) async {
    final state = initialState();
    final command = Completer<Object?>();
    Map? pending;
    bool? approved;
    Future<Object?> api(String method, List<Object?> args) async {
      if (method == 'add_files') return command.future;
      if (method == 'get_pending_dialog') return pending;
      if (method == 'resolve_dialog') {
        approved = args[1] as bool;
        pending = null;
        return {'accepted': approved};
      }
      return {...state, 'pending_dialog': pending};
    }

    await tester.pumpWidget(DocFitApp(api: api));
    await tester.pumpAndSettle();
    await tester.ensureVisible(find.text('문서 추가').first);
    await tester.tap(find.text('문서 추가').first);
    await tester.pump();
    pending = {'id': 'busy-main', 'kind': 'app_close'};
    await tester.pump(const Duration(seconds: 1));
    await tester.pump(const Duration(milliseconds: 300));
    expect(approved, false);
    command.complete(state);
    await tester.pumpAndSettle();
    expect(tester.takeException(), isNull);
    await tester.pumpWidget(const SizedBox());
  });
}
