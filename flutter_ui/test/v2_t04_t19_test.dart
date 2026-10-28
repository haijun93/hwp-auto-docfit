import 'package:docfit_ui/features/formats/format_example_edit_dialog.dart';
import 'package:docfit_ui/features/tools/backend_dialog.dart';
import 'package:docfit_ui/main.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  group('T04 FormatExampleEditDialog (서식 예시 문서 편집 안내)', () {
    testWidgets('T04 표시, 확인 회신 및 420px 반응형 검증 (오버플로 없음)', (tester) async {
      tester.view.physicalSize = const Size(420, 800);
      tester.view.devicePixelRatio = 1.0;
      addTearDown(() {
        tester.view.resetPhysicalSize();
        tester.view.resetDevicePixelRatio();
      });

      List<Object?>? lastResolvedArgs;
      Future<Object?> api(String method, List<Object?> args) async {
        if (method == 'resolve_dialog') {
          lastResolvedArgs = args;
        }
        return null;
      }

      final data = {
        'id': 'diag_t04_1',
        'kind': 'format_example_edit',
        'title': '서식 예시 문서 편집',
        'message':
            '열린 한/글 창에서 예시 문서를 작성하세요.\n\n□·ㅇ·-·※ 같은 항목기호를 섞어 원하는 계층 구조로 쓰면 서식이 됩니다.',
        'confirm': true,
        'ok_label': '분석 시작',
        'cancel_label': '취소',
      };

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: FormatExampleEditDialog(api: api, data: data),
          ),
        ),
      );
      await tester.pumpAndSettle();

      expect(find.byKey(const Key('formatExampleConfirm')), findsOneWidget);
      expect(find.byKey(const Key('formatExampleCancel')), findsOneWidget);
      expect(find.text('서식 예시 문서 편집'), findsOneWidget);
      expect(find.text('열린 한/글 창에서 예시 문서를 작성하세요.'), findsWidgets);
      expect(tester.takeException(), isNull);

      // '분석 시작' 탭 -> resolve_dialog([id, true, [], {}])
      await tester.tap(find.byKey(const Key('formatExampleConfirm')));
      await tester.pumpAndSettle();

      expect(lastResolvedArgs, isNotNull);
      expect(lastResolvedArgs![0], 'diag_t04_1');
      expect(lastResolvedArgs![1], true);

      // 취소 동작 검증
      await tester.pumpWidget(const SizedBox());
      lastResolvedArgs = null;

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: FormatExampleEditDialog(api: api, data: data),
          ),
        ),
      );
      await tester.pumpAndSettle();

      await tester.tap(find.byKey(const Key('formatExampleCancel')));
      await tester.pumpAndSettle();

      expect(lastResolvedArgs, isNotNull);
      expect(lastResolvedArgs![0], 'diag_t04_1');
      expect(lastResolvedArgs![1], false);
      expect(tester.takeException(), isNull);
    });

    testWidgets('T04 오류 메시지 포함 시 오류 영역 정상 렌더링 검증', (tester) async {
      tester.view.physicalSize = const Size(420, 800);
      tester.view.devicePixelRatio = 1.0;
      addTearDown(() {
        tester.view.resetPhysicalSize();
        tester.view.resetDevicePixelRatio();
      });

      Future<Object?> api(String method, List<Object?> args) async => null;

      final data = {
        'id': 'diag_t04_err',
        'kind': 'format_example_edit',
        'title': '서식 예시 문서 편집',
        'message': '열린 한/글 창에서 예시 문서를 작성하세요.',
        'error': '항목기호(□·ㅇ·-·※ 등)로 시작하는 문단이 없습니다.',
        'confirm': true,
        'ok_label': '분석 시작',
        'cancel_label': '취소',
      };

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: FormatExampleEditDialog(api: api, data: data),
          ),
        ),
      );
      await tester.pumpAndSettle();

      expect(find.byKey(const Key('formatExampleError')), findsOneWidget);
      expect(find.text('항목기호(□·ㅇ·-·※ 등)로 시작하는 문단이 없습니다.'), findsOneWidget);
      expect(tester.takeException(), isNull);
    });

    testWidgets('T04 BackendDialog 라우팅 검증', (tester) async {
      Future<Object?> api(String method, List<Object?> args) async => null;

      await tester.pumpWidget(
        MaterialApp(
          home: BackendDialog(
            api: api,
            data: const {
              'id': 'route_t04',
              'kind': 'format_example_edit',
              'title': '서식 예시 문서 편집',
            },
          ),
        ),
      );
      await tester.pumpAndSettle();
      expect(find.byType(FormatExampleEditDialog), findsOneWidget);
    });
  });

  group('T19 절약 완료 결과 화면 (Flutter outcome)', () {
    testWidgets('T19 결과 화면에 절약 문구와 캐릭터 그림 표시 및 420px 반응형 검증 (오버플로 없음)', (
      tester,
    ) async {
      tester.view.physicalSize = const Size(420, 800);
      tester.view.devicePixelRatio = 1.0;
      addTearDown(() {
        tester.view.resetPhysicalSize();
        tester.view.resetDevicePixelRatio();
      });

      // 1x1 투명 PNG Base64 data URI
      const samplePng =
          'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==';

      Future<Object?> api(String method, List<Object?> args) async {
        if (method == 'get_state') {
          return {
            'status': '처리 완료',
            'files': [
              {'name': '보고서.hwpx', 'path': 'C:\\doc\\보고서.hwpx'},
            ],
            'results': [
              {'name': '보고서(자간조정).hwpx', 'path': 'C:\\doc\\보고서(자간조정).hwpx'},
            ],
            'completion': {
              'message': '처리 완료 · 성공 1개 / 실패 0개',
              'savings_message': '당신의 소중한 시간 02분 05초가 절약되었습니다!',
              'savings_time': '02분 05초',
              'savings_seconds': 125.0,
              'cat_image': samplePng,
              'details': ['성공 1개 · 실패 0개'],
            },
            'card_options': {},
          };
        }
        return null;
      }

      await tester.pumpWidget(DocFitApp(api: api));
      await tester.pumpAndSettle();

      // 4번째 탭 '결과 확인'으로 이동
      expect(find.text('4. 결과 확인'), findsOneWidget);
      await tester.tap(find.text('4. 결과 확인'));
      await tester.pumpAndSettle();

      // 절약 완료 문구 및 고양이 그림 검증
      expect(find.byKey(const Key('savingsMessageText')), findsOneWidget);
      expect(find.text('당신의 소중한 시간 02분 05초가 절약되었습니다!'), findsOneWidget);
      expect(find.byKey(const Key('savingsCatImage')), findsOneWidget);

      // 420px 폭에서 오버플로 없음 확인
      expect(tester.takeException(), isNull);
    });

    testWidgets('T19 실패 건수가 있는 경우 실패 문구 정상 표시', (tester) async {
      tester.view.physicalSize = const Size(420, 800);
      tester.view.devicePixelRatio = 1.0;
      addTearDown(() {
        tester.view.resetPhysicalSize();
        tester.view.resetDevicePixelRatio();
      });

      Future<Object?> api(String method, List<Object?> args) async {
        if (method == 'get_state') {
          return {
            'status': '처리 완료',
            'files': [
              {'name': 'doc1.hwpx', 'path': 'C:\\doc1.hwpx'},
              {'name': 'doc2.hwpx', 'path': 'C:\\doc2.hwpx'},
            ],
            'results': [
              {'name': 'doc1(자간조정).hwpx', 'path': 'C:\\doc1(자간조정).hwpx'},
            ],
            'completion': {
              'message': '처리 완료 · 성공 1개 / 실패 1개',
              'savings_message': '문서 1개를 처리하지 못했습니다. 처리 기록을 확인해 주세요. (성공 1개)',
              'savings_time': '',
              'savings_seconds': 0,
              'details': ['성공 1개 · 실패 1개'],
            },
            'card_options': {},
          };
        }
        return null;
      }

      await tester.pumpWidget(DocFitApp(api: api));
      await tester.pumpAndSettle();

      await tester.tap(find.text('4. 결과 확인'));
      await tester.pumpAndSettle();

      expect(find.byKey(const Key('savingsMessageText')), findsOneWidget);
      expect(
        find.text('문서 1개를 처리하지 못했습니다. 처리 기록을 확인해 주세요. (성공 1개)'),
        findsOneWidget,
      );
      expect(tester.takeException(), isNull);
    });
  });
}
