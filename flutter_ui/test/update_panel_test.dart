import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:docfit_ui/features/settings/update_panel.dart';

Widget _wrap(
  Map<String, dynamic> state,
  Future<void> Function(String, [List<Object?>]) command,
) {
  return MaterialApp(
    home: Scaffold(
      body: SingleChildScrollView(
        child: UpdatePanel(state: state, command: command),
      ),
    ),
  );
}

void main() {
  group('UpdatePanel 위젯', () {
    testWidgets('state["update"]가 없으면 현재 버전과 지금 확인 버튼만 표시', (tester) async {
      final calls = <String>[];
      Future<void> command(
        String method, [
        List<Object?> args = const [],
      ]) async {
        calls.add(method);
      }

      await tester.pumpWidget(_wrap({'version': '1.80.6'}, command));

      expect(find.byKey(const Key('updatePanel')), findsOneWidget);
      expect(find.text('현재 버전 v1.80.6'), findsOneWidget);

      final checkBtnFinder = find.byKey(const Key('checkUpdateButton'));
      expect(checkBtnFinder, findsOneWidget);
      final checkBtn = tester.widget<OutlinedButton>(checkBtnFinder);
      expect(checkBtn.onPressed, isNotNull);

      // 상태 줄 및 세부 위젯 숨김
      expect(find.byKey(const Key('updateStatusText')), findsNothing);
      expect(find.byKey(const Key('updateProgress')), findsNothing);
      expect(find.byKey(const Key('updateNotes')), findsNothing);
      expect(find.byKey(const Key('startUpdateButton')), findsNothing);
      expect(find.byKey(const Key('openUpdatePageButton')), findsNothing);

      // 지금 확인 버튼 클릭 동작
      await tester.tap(checkBtnFinder);
      expect(calls, ['check_update']);
    });

    testWidgets('step: idle 일 때 상태 줄 및 추가 버튼 숨김', (tester) async {
      final calls = <String>[];
      Future<void> command(
        String method, [
        List<Object?> args = const [],
      ]) async {
        calls.add(method);
      }

      final state = {
        'update': {'step': 'idle', 'current': '1.80.6'},
      };

      await tester.pumpWidget(_wrap(state, command));

      expect(find.text('현재 버전 v1.80.6'), findsOneWidget);
      final checkBtn = tester.widget<OutlinedButton>(
        find.byKey(const Key('checkUpdateButton')),
      );
      expect(checkBtn.onPressed, isNotNull);

      expect(find.byKey(const Key('updateStatusText')), findsNothing);
      expect(find.byKey(const Key('updateProgress')), findsNothing);
      expect(find.byKey(const Key('updateNotes')), findsNothing);
      expect(find.byKey(const Key('startUpdateButton')), findsNothing);
      expect(find.byKey(const Key('openUpdatePageButton')), findsNothing);

      await tester.tap(find.byKey(const Key('checkUpdateButton')));
      expect(calls, ['check_update']);
    });

    testWidgets('step: checking 일 때 지금 확인 비활성 및 안내 문구', (tester) async {
      final state = {
        'update': {'step': 'checking', 'current': '1.80.6'},
      };

      await tester.pumpWidget(
        _wrap(state, (method, [args = const []]) async {}),
      );

      final checkBtn = tester.widget<OutlinedButton>(
        find.byKey(const Key('checkUpdateButton')),
      );
      expect(checkBtn.onPressed, isNull);

      final status = tester.widget<Text>(
        find.byKey(const Key('updateStatusText')),
      );
      expect(status.data, '새 버전을 확인하고 있어요…');
      expect(find.byKey(const Key('updateProgress')), findsNothing);
      expect(find.byKey(const Key('startUpdateButton')), findsNothing);
      expect(find.byKey(const Key('openUpdatePageButton')), findsNothing);
    });

    testWidgets('step: latest 일 때 최신 버전 문구 표시', (tester) async {
      final state = {
        'update': {'step': 'latest', 'current': '1.80.6'},
      };

      await tester.pumpWidget(
        _wrap(state, (method, [args = const []]) async {}),
      );

      final checkBtn = tester.widget<OutlinedButton>(
        find.byKey(const Key('checkUpdateButton')),
      );
      expect(checkBtn.onPressed, isNotNull);

      final status = tester.widget<Text>(
        find.byKey(const Key('updateStatusText')),
      );
      expect(status.data, '최신 버전이에요.');
      expect(find.byKey(const Key('updateProgress')), findsNothing);
      expect(find.byKey(const Key('startUpdateButton')), findsNothing);
      expect(find.byKey(const Key('openUpdatePageButton')), findsNothing);
    });

    testWidgets('step: available (설치본) 일 때 notes 목록과 업데이트 버튼 동작', (
      tester,
    ) async {
      final calls = <String>[];
      Future<void> command(
        String method, [
        List<Object?> args = const [],
      ]) async {
        calls.add(method);
      }

      final state = {
        'update': {
          'step': 'available',
          'current': '1.80.6',
          'latest': '1.80.7',
          'installed': true,
          'notes': ['자간 조정 알고리즘 최적화', '서식 통일 결과 창 오류 수정'],
        },
      };

      await tester.pumpWidget(_wrap(state, command));

      final checkBtn = tester.widget<OutlinedButton>(
        find.byKey(const Key('checkUpdateButton')),
      );
      expect(checkBtn.onPressed, isNotNull);

      final status = tester.widget<Text>(
        find.byKey(const Key('updateStatusText')),
      );
      expect(status.data, '새 버전 v1.80.7이 나왔어요.');

      final notesWidget = tester.widget<Text>(
        find.byKey(const Key('updateNotes')),
      );
      expect(notesWidget.data, '• 자간 조정 알고리즘 최적화\n• 서식 통일 결과 창 오류 수정');

      final updateBtnFinder = find.byKey(const Key('startUpdateButton'));
      expect(updateBtnFinder, findsOneWidget);
      expect(tester.widget<FilledButton>(updateBtnFinder), isNotNull);
      expect(find.text('v1.80.7로 업데이트'), findsOneWidget);

      await tester.tap(updateBtnFinder);
      expect(calls, ['start_update']);
      expect(find.byKey(const Key('openUpdatePageButton')), findsNothing);
    });

    testWidgets('step: available (포터블 installed=false) 일 때 버튼 문구 변경', (
      tester,
    ) async {
      final calls = <String>[];
      final state = {
        'update': {
          'step': 'available',
          'current': '1.80.6',
          'latest': '1.80.7',
          'installed': false,
        },
      };

      await tester.pumpWidget(
        _wrap(state, (method, [args = const []]) async {
          calls.add(method);
        }),
      );

      final updateBtnFinder = find.byKey(const Key('startUpdateButton'));
      expect(updateBtnFinder, findsOneWidget);
      expect(find.text('v1.80.7 내려받아 바꾸기'), findsOneWidget);

      await tester.tap(updateBtnFinder);
      expect(calls, ['start_update']);
    });

    testWidgets('notes는 최대 6줄까지만 표시', (tester) async {
      final state = {
        'update': {
          'step': 'available',
          'current': '1.80.6',
          'latest': '1.80.7',
          'notes': [
            '첫 번째 변경',
            '두 번째 변경',
            '세 번째 변경',
            '네 번째 변경',
            '다섯 번째 변경',
            '여섯 번째 변경',
            '일곱 번째 변경(제외되어야 함)',
            '여덟 번째 변경(제외되어야 함)',
          ],
        },
      };

      await tester.pumpWidget(
        _wrap(state, (method, [args = const []]) async {}),
      );

      final notesWidget = tester.widget<Text>(
        find.byKey(const Key('updateNotes')),
      );
      expect(
        notesWidget.data,
        '• 첫 번째 변경\n'
        '• 두 번째 변경\n'
        '• 세 번째 변경\n'
        '• 네 번째 변경\n'
        '• 다섯 번째 변경\n'
        '• 여섯 번째 변경',
      );
    });

    testWidgets('step: downloading 일 때 진행률(percent/100)과 비활성', (tester) async {
      final state = {
        'update': {'step': 'downloading', 'current': '1.80.6', 'percent': 42},
      };

      await tester.pumpWidget(
        _wrap(state, (method, [args = const []]) async {}),
      );

      final checkBtn = tester.widget<OutlinedButton>(
        find.byKey(const Key('checkUpdateButton')),
      );
      expect(checkBtn.onPressed, isNull);

      final status = tester.widget<Text>(
        find.byKey(const Key('updateStatusText')),
      );
      expect(status.data, '내려받는 중… 42%');

      final progressFinder = find.byKey(const Key('updateProgress'));
      expect(progressFinder, findsOneWidget);
      final progress = tester.widget<LinearProgressIndicator>(progressFinder);
      expect(progress.value, closeTo(0.42, 0.001));

      expect(find.byKey(const Key('startUpdateButton')), findsNothing);
      expect(find.byKey(const Key('openUpdatePageButton')), findsNothing);
    });

    testWidgets('step: installing 일 때 안내 문구와 비활성', (tester) async {
      final state = {
        'update': {'step': 'installing', 'current': '1.80.6'},
      };

      await tester.pumpWidget(
        _wrap(state, (method, [args = const []]) async {}),
      );

      final checkBtn = tester.widget<OutlinedButton>(
        find.byKey(const Key('checkUpdateButton')),
      );
      expect(checkBtn.onPressed, isNull);

      final status = tester.widget<Text>(
        find.byKey(const Key('updateStatusText')),
      );
      expect(status.data, '설치를 시작했어요. 잠시 뒤 앱이 다시 열려요.');
      expect(find.byKey(const Key('updateProgress')), findsNothing);
      expect(find.byKey(const Key('startUpdateButton')), findsNothing);
      expect(find.byKey(const Key('openUpdatePageButton')), findsNothing);
    });

    testWidgets('step: failed 일 때 다운로드 페이지 열기 버튼과 명령 호출', (tester) async {
      final calls = <String>[];
      Future<void> command(
        String method, [
        List<Object?> args = const [],
      ]) async {
        calls.add(method);
      }

      final state = {
        'update': {'step': 'failed', 'current': '1.80.6'},
      };

      await tester.pumpWidget(_wrap(state, command));

      final checkBtn = tester.widget<OutlinedButton>(
        find.byKey(const Key('checkUpdateButton')),
      );
      expect(checkBtn.onPressed, isNotNull);

      final status = tester.widget<Text>(
        find.byKey(const Key('updateStatusText')),
      );
      expect(status.data, '업데이트하지 못했어요.');

      final openPageBtnFinder = find.byKey(const Key('openUpdatePageButton'));
      expect(openPageBtnFinder, findsOneWidget);
      expect(find.text('다운로드 페이지 열기'), findsOneWidget);

      await tester.tap(openPageBtnFinder);
      expect(calls, ['open_update_page']);
      expect(find.byKey(const Key('startUpdateButton')), findsNothing);
    });

    testWidgets('step: cancelled 및 offline 기본 문구 확인', (tester) async {
      final stateCancelled = {
        'update': {'step': 'cancelled', 'current': '1.80.6'},
      };
      await tester.pumpWidget(
        _wrap(stateCancelled, (method, [args = const []]) async {}),
      );
      expect(
        tester.widget<Text>(find.byKey(const Key('updateStatusText'))).data,
        '업데이트를 취소했어요.',
      );

      final stateOffline = {
        'update': {'step': 'offline', 'current': '1.80.6'},
      };
      await tester.pumpWidget(
        _wrap(stateOffline, (method, [args = const []]) async {}),
      );
      expect(
        tester.widget<Text>(find.byKey(const Key('updateStatusText'))).data,
        '폐쇄망 모드에서는 인터넷으로 확인하지 않아요.',
      );
    });

    testWidgets('message 필드가 주어지면 기본 문구 대신 최우선 표시', (tester) async {
      final state = {
        'update': {
          'step': 'latest',
          'current': '1.80.6',
          'message': '서버 점검 중입니다. 잠시 후 시도하세요.',
        },
      };

      await tester.pumpWidget(
        _wrap(state, (method, [args = const []]) async {}),
      );
      expect(
        tester.widget<Text>(find.byKey(const Key('updateStatusText'))).data,
        '서버 점검 중입니다. 잠시 후 시도하세요.',
      );
    });
  });
}
