import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:docfit_ui/features/flows/edit_save_state.dart';

class SaveHarness extends StatefulWidget {
  const SaveHarness({super.key, required this.response});
  final Future<void> response;
  @override
  State<SaveHarness> createState() => _SaveHarnessState();
}

class _SaveHarnessState extends State<SaveHarness> {
  final state = EditSaveState();
  int version = 0;
  @override
  Widget build(BuildContext context) => Scaffold(
    body: Column(
      children: [
        TextField(
          onChanged: (_) => setState(() => state.event(++version, true)),
        ),
        Text(state.dirty ? '미저장' : '저장됨'),
        TextButton(
          onPressed: () async {
            final target = state.begin(state.generation);
            setState(() {});
            await widget.response;
            if (mounted) setState(() => state.complete(target, success: true));
          },
          child: const Text('저장'),
        ),
        TextButton(
          onPressed: () {
            if (state.saving || state.dirty) {
              showDialog<void>(
                context: context,
                builder: (context) =>
                    const AlertDialog(content: Text('최신 변경사항을 먼저 저장해 주세요.')),
              );
            } else {
              Navigator.pop(context);
            }
          },
          child: const Text('닫기'),
        ),
      ],
    ),
  );
}

void main() {
  testWidgets('delayed save followed by editing cannot close as clean', (
    tester,
  ) async {
    final response = Completer<void>();
    await tester.pumpWidget(
      MaterialApp(home: SaveHarness(response: response.future)),
    );
    await tester.enterText(find.byType(TextField), '첫 내용');
    await tester.tap(find.text('저장'));
    await tester.pump();
    await tester.enterText(find.byType(TextField), '추가한 미저장 내용');
    response.complete();
    await tester.pump();
    expect(find.text('미저장'), findsOneWidget);
    await tester.tap(find.text('닫기'));
    await tester.pumpAndSettle();
    expect(find.text('최신 변경사항을 먼저 저장해 주세요.'), findsOneWidget);
  });
  test('late clean events cannot roll the current generation backwards', () {
    final state = EditSaveState()..event(4, true);
    final target = state.begin(4);
    state.event(5, true);
    state.complete(target, success: true);
    state.event(4, false);
    expect(state.dirty, isTrue);
    final latest = state.begin(5);
    state.complete(latest, success: true);
    expect(state.dirty, isFalse);
  });
}
