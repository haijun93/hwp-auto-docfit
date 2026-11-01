import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:docfit_ui/features/file_rename/file_rename_api.dart';
import 'package:docfit_ui/features/file_rename/file_rename_screen.dart';

/// 서비스 흉내: 목록 2개, 미리보기는 '_n' 붙이기, apply는 이름을 바꾸고 undo는 되돌린다.
class _FakeBackend {
  final calls = <String>[];
  List<Map<String, Object?>> entries = [];
  Map<String, Object?>? lastPreview;
  bool conflict = false;

  Future<Object?> call(String method, List<Object?> args) async {
    expect(method, 'file_rename');
    final action = args[0] as String;
    final payload = (args.length > 1 ? args[1] : null) as Map? ?? const {};
    calls.add(action);
    switch (action) {
      case 'list':
        return {'ok': true, 'entries': entries};
      case 'pick_files':
        entries = [
          {'id': 'a', 'name': '6C1D56A5.JPG', 'folder': 'C:/사진', 'size': 1, 'mtime': 0},
          {'id': 'b', 'name': '8AA3A713.JPG', 'folder': 'C:/사진', 'size': 1, 'mtime': 0},
        ];
        return {'ok': true, 'entries': entries, 'added': 2, 'skipped_count': 0};
      case 'preview':
        final rules = payload['rules'] as List;
        lastPreview = Map<String, Object?>.from(payload);
        final items = [
          for (final e in entries)
            {
              'id': e['id'],
              'new_name': rules.isEmpty ? e['name'] : '${e['name']}_n',
              'status': conflict ? 'conflict' : (rules.isEmpty ? 'unchanged' : 'ok'),
              'reason': conflict ? '같은 이름의 파일이 이미 있습니다.' : null,
              'warnings': <String>[],
            },
        ];
        return {
          'ok': true,
          'plan_id': 'p1',
          'items': items,
          'summary': {
            'ok': rules.isEmpty || conflict ? 0 : items.length,
            'unchanged': rules.isEmpty ? items.length : 0,
            'conflict': conflict ? items.length : 0,
            'invalid': 0,
            'skipped': 0,
            'executables': 0,
          },
        };
      case 'apply':
        expect(payload['plan_id'], 'p1');
        entries = [for (final e in entries) {...e, 'name': '${e['name']}_n'}];
        return {'ok': true, 'entries': entries, 'run_id': 'r1', 'done': 2, 'failed': [], 'skipped': 0};
      case 'undo':
        expect(payload['run_id'], 'r1');
        entries = [
          for (final e in entries) {...e, 'name': '${e['name']}'.replaceAll('_n', '')},
        ];
        return {'ok': true, 'entries': entries, 'run_id': 'r2', 'done': 2, 'failed': []};
    }
    return {'ok': false, 'message': 'unknown'};
  }
}

Future<void> _pump(WidgetTester tester, _FakeBackend backend) async {
  tester.view.physicalSize = const Size(1400, 900);
  tester.view.devicePixelRatio = 1;
  addTearDown(tester.view.reset);
  await tester.pumpWidget(MaterialApp(home: Scaffold(body: FileRenameScreen(api: backend.call))));
  await tester.pumpAndSettle();
}

void main() {
  testWidgets('파일 추가 → 규칙 추가 → 미리보기 → 적용 → 되돌리기', (tester) async {
    final backend = _FakeBackend();
    await _pump(tester, backend);
    expect(find.textContaining('끌어다 놓거나'), findsOneWidget);

    await tester.tap(find.byKey(const ValueKey('rename-add-files')));
    await tester.pumpAndSettle(const Duration(milliseconds: 300));
    expect(find.text('6C1D56A5.JPG'), findsNWidgets(2)); // 규칙이 없으면 새 이름 = 원래 이름
    // 규칙이 없으면 적용 불가
    expect(tester.widget<FilledButton>(find.byKey(const ValueKey('rename-apply'))).onPressed, isNull);

    // 옵션 없는 규칙(숫자 지우기)은 바로 추가된다.
    await tester.tap(find.byKey(const ValueKey('rename-add-rule')));
    await tester.pumpAndSettle();
    await tester.tap(find.text('숫자 지우기').last);
    await tester.pumpAndSettle(const Duration(milliseconds: 300));
    expect(backend.lastPreview!['rules'], [
      {'kind': 'digits_delete'},
    ]);
    expect(find.text('6C1D56A5.JPG_n'), findsOneWidget);
    expect(find.textContaining('2개 중 2개 바뀜'), findsOneWidget);

    await tester.tap(find.byKey(const ValueKey('rename-apply')));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const ValueKey('rename-confirm')));
    await tester.pumpAndSettle(const Duration(milliseconds: 300));
    expect(backend.calls, contains('apply'));
    expect(find.textContaining('2개 바꿈'), findsOneWidget);

    await tester.tap(find.byKey(const ValueKey('rename-undo')));
    await tester.pumpAndSettle(const Duration(milliseconds: 300));
    expect(backend.calls, contains('undo'));
    expect(find.text('6C1D56A5.JPG'), findsOneWidget);
  });

  testWidgets('충돌이 있으면 변경 적용 단추가 꺼진다', (tester) async {
    final backend = _FakeBackend()..conflict = true;
    await _pump(tester, backend);
    await tester.tap(find.byKey(const ValueKey('rename-add-files')));
    await tester.pumpAndSettle(const Duration(milliseconds: 300));
    await tester.tap(find.byKey(const ValueKey('rename-add-rule')));
    await tester.pumpAndSettle();
    await tester.tap(find.text('이름 지우기(확장자만 남김)').last);
    await tester.pumpAndSettle(const Duration(milliseconds: 300));
    expect(find.text('충돌'), findsNWidgets(2));
    expect(tester.widget<FilledButton>(find.byKey(const ValueKey('rename-apply'))).onPressed, isNull);
  });

  testWidgets('규칙 편집 대화상자: 번호 붙이기 옵션을 숫자로 저장', (tester) async {
    final backend = _FakeBackend();
    await _pump(tester, backend);
    await tester.tap(find.byKey(const ValueKey('rename-add-files')));
    await tester.pumpAndSettle(const Duration(milliseconds: 300));
    await tester.tap(find.byKey(const ValueKey('rename-add-rule')));
    await tester.pumpAndSettle();
    await tester.tap(find.text('번호 붙이기').last);
    await tester.pumpAndSettle();
    await tester.enterText(find.byKey(const ValueKey('rule-field-digits')), '2');
    await tester.tap(find.text('확인'));
    await tester.pumpAndSettle(const Duration(milliseconds: 300));
    final rule = (backend.lastPreview!['rules'] as List).single as Map;
    expect(rule['kind'], 'number');
    expect(rule['digits'], 2);
    expect(find.textContaining('2자리'), findsOneWidget);
  });

  testWidgets('새 문서 이름 규칙 메뉴와 폴더 자체 이름 바꾸기 버튼 표시', (tester) async {
    final backend = _FakeBackend();
    await _pump(tester, backend);
    expect(find.byKey(const ValueKey('rename-folder-self')), findsOneWidget);
    await tester.tap(find.byKey(const ValueKey('rename-add-rule')));
    await tester.pumpAndSettle();
    expect(find.text('문서 제목으로'), findsOneWidget);
    expect(find.text('공문서 이름 틀'), findsOneWidget);
  });

  testWidgets('충돌 처리 선택이 미리보기에 실리고, 바뀌는 것만 보기·이름 목록 복사', (tester) async {
    final backend = _FakeBackend();
    final copied = <String>[];
    tester.binding.defaultBinaryMessenger.setMockMethodCallHandler(SystemChannels.platform, (call) async {
      if (call.method == 'Clipboard.setData') copied.add('${(call.arguments as Map)['text']}');
      return null;
    });
    addTearDown(() => tester.binding.defaultBinaryMessenger.setMockMethodCallHandler(SystemChannels.platform, null));
    await _pump(tester, backend);
    await tester.tap(find.byKey(const ValueKey('rename-add-files')));
    await tester.pumpAndSettle(const Duration(milliseconds: 300));
    expect(backend.lastPreview?['on_conflict'] ?? 'block', 'block');
    await tester.tap(find.byKey(const ValueKey('rename-on-conflict')));
    await tester.pumpAndSettle();
    await tester.tap(find.text('이름이 겹치면 (2)·(3) 붙이기').last);
    await tester.pumpAndSettle(const Duration(milliseconds: 300));
    expect(backend.lastPreview!['on_conflict'], 'number');
    // 규칙이 없으면 모두 '그대로' → 바뀌는 것만 보기에서 목록이 빈다.
    expect(find.byKey(const ValueKey('rename-row-a')), findsOneWidget);
    await tester.tap(find.byKey(const ValueKey('rename-only-changed')));
    await tester.pumpAndSettle();
    expect(find.byKey(const ValueKey('rename-row-a')), findsNothing);
    await tester.tap(find.byKey(const ValueKey('rename-copy-list')));
    await tester.pumpAndSettle();
    expect(copied.single, startsWith('원래 이름\t새 이름\n6C1D56A5.JPG\t6C1D56A5.JPG'));
  });

  testWidgets('이름 목록 붙여넣기 규칙: 여러 줄 입력이 그대로 실린다', (tester) async {
    final backend = _FakeBackend();
    await _pump(tester, backend);
    await tester.tap(find.byKey(const ValueKey('rename-add-files')));
    await tester.pumpAndSettle(const Duration(milliseconds: 300));
    await tester.tap(find.byKey(const ValueKey('rename-add-rule')));
    await tester.pumpAndSettle();
    await tester.tap(find.text('이름 목록 붙여넣기(엑셀·메모장 줄)').last);
    await tester.pumpAndSettle();
    await tester.enterText(find.byKey(const ValueKey('rule-field-names')), '보고서\n붙임1');
    await tester.tap(find.text('확인'));
    await tester.pumpAndSettle(const Duration(milliseconds: 300));
    final rule = (backend.lastPreview!['rules'] as List).single as Map;
    expect(rule['kind'], 'names_list');
    expect(rule['names'], '보고서\n붙임1');
    expect(find.textContaining('2줄'), findsOneWidget);
  });

  test('규칙 요약 문구', () {
    expect(ruleSummary({'kind': 'replace', 'find': 'IMG_', 'to': ''}), "'IMG_' → ''");
    expect(ruleSummary({'kind': 'number_shift', 'delta': -1, 'which': 'first'}), '첫 번호 -1');
    expect(ruleSummary({'kind': 'case', 'mode': 'capitalize'}), '맨 앞 글자만 대문자');
    expect(ruleSummary({'kind': 'case', 'mode': 'sentence'}), '문장형(맨 앞만 대문자)');
    expect(ruleSummary({'kind': 'ext_case', 'mode': 'lower'}), '소문자');
  });
}
