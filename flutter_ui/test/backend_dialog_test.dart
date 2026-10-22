import 'dart:async';
import 'package:docfit_ui/features/tools/backend_dialog.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:docfit_ui/main.dart';
import 'workspace_test.dart' show initialState;

void main() {
  testWidgets('custom close confirmation labels', (tester) async {
    await tester.pumpWidget(
      MaterialApp(
        home: BackendDialog(
          api: (method, args) async => null,
          data: const {
            'id': 'close',
            'title': '종료',
            'message': '종료할까요?',
            'confirm': true,
            'ok_label': '작업 중단하고 종료',
            'cancel_label': '계속 진행',
          },
        ),
      ),
    );
    expect(find.text('작업 중단하고 종료'), findsOneWidget);
    expect(find.text('계속 진행'), findsOneWidget);
    expect(find.text('확인 후 진행'), findsNothing);
    expect(find.text('취소'), findsNothing);
  });

  testWidgets(
    'busy command keeps polling confirmation and applies explicit choices',
    (tester) async {
      final state = initialState();
      final command = Completer<Object?>();
      List<Object?>? approved;
      Map? pending;
      Future<Object?> api(String method, List<Object?> args) async {
        if (method == 'add_files') {
          pending = {
            'id': 'confirmation',
            'title': '확인 필요',
            'message': '선택한 영역만 적용합니다.',
            'confirm': true,
            'choices': [
              {'id': 0, 'label': '첫 영역'},
              {'id': 1, 'label': '둘째 영역'},
            ],
            'fields': [
              {'id': 'size', 'label': '크기', 'value': '15'},
            ],
          };
          return command.future;
        }
        if (method == 'get_pending_dialog') return pending;
        if (method == 'resolve_dialog') {
          approved = args;
          pending = null;
          command.complete(Map<String, dynamic>.from(state));
          return {'ok': true};
        }
        return Map<String, dynamic>.from(state);
      }

      await tester.pumpWidget(DocFitApp(api: api));
      await tester.pumpAndSettle();
      await tester.ensureVisible(find.text('문서 추가').first);
      await tester.tap(find.text('문서 추가').first);
      await tester.pump();
      await tester.pump(const Duration(seconds: 1));
      await tester.pump(const Duration(milliseconds: 300));
      expect(find.text('확인 필요'), findsOneWidget);
      expect(approved, isNull);
      await tester.tap(find.text('둘째 영역'));
      await tester.enterText(find.widgetWithText(TextFormField, '크기'), '16');
      await tester.tap(find.text('확인 후 진행'));
      await tester.pumpAndSettle();
      expect(approved?[1], true);
      expect(approved?[2], [0]);
      expect(approved?[3], {'size': '16'});
      await tester.pumpWidget(const SizedBox());
    },
  );
}
