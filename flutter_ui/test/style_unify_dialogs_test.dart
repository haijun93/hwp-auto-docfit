import 'package:docfit_ui/features/style_unify/unify_area_dialog.dart';
import 'package:docfit_ui/features/style_unify/unify_pick_style_dialog.dart';
import 'package:docfit_ui/features/style_unify/unify_result_dialog.dart';
import 'package:docfit_ui/features/tools/backend_dialog.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  group('T20 UnifyPickStyleDialog (대표 서식 확인)', () {
    testWidgets('후보 선택, 확인 회신 및 420px 반응형 검증', (tester) async {
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
        'id': 'diag_t20_1',
        'kind': 'style_unify_profile',
        'title': '서식통일 2/5 · 대표 서식 확인',
        'message': '문서에서 조사한 대표 서식입니다.',
        'confirm': true,
        'ok_label': '확인한 대표값으로 진행',
        'cancel_label': '취소',
        'styles': [
          {
            'index': 0,
            'marker': '1.',
            'role': '개조식',
            'font': '맑은 고딕',
            'size': 15.0,
          },
          {
            'index': 1,
            'marker': '가.',
            'role': '본문',
            'font': '맑은 고딕',
            'size': 13.0,
          },
        ],
        'choices': [
          {'id': 0, 'label': '1. · 개조식'},
          {'id': 1, 'label': '가. · 본문'},
        ],
        'fields': [
          {'id': '0:font', 'label': '1. 글꼴', 'type': 'text', 'value': '맑은 고딕'},
          {
            'id': '0:size',
            'label': '1. 크기 (pt)',
            'type': 'text',
            'value': '15.0',
          },
          {
            'id': '0:marker_bold',
            'label': '1. 기호 굵게',
            'type': 'bool',
            'value': 'True',
          },
          {'id': '1:font', 'label': '가. 글꼴', 'type': 'text', 'value': '맑은 고딕'},
        ],
      };

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: UnifyPickStyleDialog(api: api, data: data),
          ),
        ),
      );
      await tester.pumpAndSettle();

      // 위젯 키 및 UI 텍스트 확인
      expect(find.byKey(const Key('unifyPickStyle_0')), findsOneWidget);
      expect(find.byKey(const Key('unifyPickStyle_1')), findsOneWidget);
      expect(find.byKey(const Key('unifyConfirm')), findsOneWidget);
      expect(find.byKey(const Key('unifyCancel')), findsOneWidget);

      await tester.enterText(
        find.byKey(const Key('unifyField_0:font')),
        '나눔고딕',
      );
      // 2번째 스타일 후보 탭
      await tester.tap(find.byKey(const Key('unifyPickStyle_1')));
      await tester.pumpAndSettle();

      expect(find.byKey(const Key('unifyField_0:font')), findsNothing);
      expect(find.byKey(const Key('unifyField_1:font')), findsOneWidget);
      await tester.enterText(find.byKey(const Key('unifyField_1:font')), '바탕');

      // 확인 버튼 탭
      await tester.tap(find.byKey(const Key('unifyConfirm')));
      await tester.pumpAndSettle();

      expect(lastResolvedArgs, isNotNull);
      expect(lastResolvedArgs![0], 'diag_t20_1');
      expect(lastResolvedArgs![1], true); // accepted
      expect(lastResolvedArgs![2] is List, true); // selection
      expect(lastResolvedArgs![3], containsPair('0:font', '나눔고딕'));
      expect(lastResolvedArgs![3], containsPair('1:font', '바탕'));

      // 오버플로 검증 (테스트 중 FlutterError 없이 완료됨)
    });

    testWidgets('취소 시 accepted=false 회신 검증', (tester) async {
      List<Object?>? lastResolvedArgs;
      Future<Object?> api(String method, List<Object?> args) async {
        if (method == 'resolve_dialog') {
          lastResolvedArgs = args;
        }
        return null;
      }

      final data = {
        'id': 'diag_t20_2',
        'kind': 'style_unify_profile',
        'title': '대표 서식 확인',
        'confirm': true,
        'styles': [],
        'fields': [],
      };

      // 다이얼로그 띄우기
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: UnifyPickStyleDialog(api: api, data: data),
          ),
        ),
      );
      await tester.pumpAndSettle();

      await tester.tap(find.byKey(const Key('unifyCancel')));
      await tester.pumpAndSettle();

      expect(lastResolvedArgs, isNotNull);
      expect(lastResolvedArgs![0], 'diag_t20_2');
      expect(lastResolvedArgs![1], false);
      expect(lastResolvedArgs![2], isEmpty);

      // 한 시험에서 화면 재호출 규칙 준수: 중간 초기화
      await tester.pumpWidget(const SizedBox());
    });
  });

  group('T21 UnifyAreaDialog (적용 영역 확인)', () {
    testWidgets('영역 토글, 확인 및 420px 반응형 검증', (tester) async {
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
        'id': 'diag_t21_1',
        'kind': 'style_unify_regions',
        'title': '서식통일 3/5 · 편집 영역 확인',
        'message': '선택한 불일치 영역만 적용합니다.',
        'confirm': true,
        'ok_label': '선택 영역만 적용',
        'cancel_label': '취소',
        'areas': [
          {
            'id': 0,
            'doc': 'doc1',
            'area': 'area0',
            'marker': '1.',
            'role': '개조식',
            'text': '추진 배경 및 필요성 설명 문장입니다.',
            'changes': '글꼴 → 맑은 고딕',
            'checked': true,
          },
          {
            'id': 1,
            'doc': 'doc1',
            'area': 'area1',
            'marker': '가.',
            'role': '본문',
            'text': '세부 실행 계획 안내 문장입니다.',
            'changes': '내어쓰기 → 적용',
            'checked': true,
          },
        ],
      };

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: UnifyAreaDialog(api: api, data: data),
          ),
        ),
      );
      await tester.pumpAndSettle();

      expect(find.byKey(const Key('unifyArea_doc1_area0')), findsOneWidget);
      expect(find.byKey(const Key('unifyArea_doc1_area1')), findsOneWidget);
      expect(find.byKey(const Key('unifyConfirm')), findsOneWidget);
      expect(find.byKey(const Key('unifyCancel')), findsOneWidget);

      // 첫 번째 영역 체크 해제
      await tester.tap(find.byKey(const Key('unifyArea_doc1_area0')));
      await tester.pumpAndSettle();

      // 확인 버튼 클릭
      await tester.tap(find.byKey(const Key('unifyConfirm')));
      await tester.pumpAndSettle();

      expect(lastResolvedArgs, isNotNull);
      expect(lastResolvedArgs![0], 'diag_t21_1');
      expect(lastResolvedArgs![1], true);
      // id 0은 해제되었으므로 id 1만 남아있어야 함
      final selectedList = lastResolvedArgs![2] as List;
      expect(selectedList.contains(1), true);
      expect(selectedList.contains(0), false);
    });

    testWidgets('취소 클릭 시 빈 선택목록 회신', (tester) async {
      List<Object?>? lastResolvedArgs;
      Future<Object?> api(String method, List<Object?> args) async {
        if (method == 'resolve_dialog') {
          lastResolvedArgs = args;
        }
        return null;
      }

      final data = {
        'id': 'diag_t21_2',
        'kind': 'style_unify_regions',
        'title': '편집 영역 확인',
        'areas': [
          {'id': 0, 'doc': 'd', 'area': 'a', 'checked': true},
        ],
      };

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: UnifyAreaDialog(api: api, data: data),
          ),
        ),
      );
      await tester.pumpAndSettle();

      await tester.tap(find.byKey(const Key('unifyCancel')));
      await tester.pumpAndSettle();

      expect(lastResolvedArgs, isNotNull);
      expect(lastResolvedArgs![1], false);
      expect(lastResolvedArgs![2], isEmpty);

      await tester.pumpWidget(const SizedBox());
    });
  });

  group('T22 UnifyResultDialog (작업 결과 확인)', () {
    testWidgets('결과 요약, 확인 및 420px 반응형 검증', (tester) async {
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
        'id': 'diag_t22_1',
        'kind': 'style_unify_result',
        'title': '서식통일 5/5 · 작업 결과 확인',
        'message': '저장 결과 확인 · 검수 통과',
        'confirm': false,
        'ok_label': '결과 확인',
        'cancel_label': '닫기',
        'result': {
          'file': '보고서.hwp',
          'status': 'passed',
          'status_text': '검수 통과',
          'checked': 45,
          'issues': [],
          'not_checkable': [],
          'unresolved': [],
          'folder': 'C:\\HWP_AUTODOCFIT\\결과',
        },
      };

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: UnifyResultDialog(api: api, data: data),
          ),
        ),
      );
      await tester.pumpAndSettle();

      expect(find.byKey(const Key('unifyConfirm')), findsOneWidget);
      expect(find.byKey(const Key('unifyCancel')), findsOneWidget);
      expect(find.text('검수 통과'), findsWidgets);

      // 결과 확인 버튼 클릭
      await tester.tap(find.byKey(const Key('unifyConfirm')));
      await tester.pumpAndSettle();

      expect(lastResolvedArgs, isNotNull);
      expect(lastResolvedArgs![0], 'diag_t22_1');
      expect(lastResolvedArgs![1], true);
    });

    testWidgets('닫기 클릭 시 정상 종료', (tester) async {
      List<Object?>? lastResolvedArgs;
      Future<Object?> api(String method, List<Object?> args) async {
        if (method == 'resolve_dialog') {
          lastResolvedArgs = args;
        }
        return null;
      }

      final data = {
        'id': 'diag_t22_2',
        'kind': 'style_unify_result',
        'title': '작업 결과 확인',
        'result': {'status': 'failed', 'checked': 10},
      };

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: UnifyResultDialog(api: api, data: data),
          ),
        ),
      );
      await tester.pumpAndSettle();

      await tester.tap(find.byKey(const Key('unifyCancel')));
      await tester.pumpAndSettle();

      expect(lastResolvedArgs, isNotNull);
      expect(lastResolvedArgs![1], false);

      await tester.pumpWidget(const SizedBox());
    });
  });

  group('BackendDialog 라우팅 통합 시험', () {
    testWidgets('BackendDialog가 kind에 따라 3개 화면으로 정상 라우팅되는지 검증', (tester) async {
      Future<Object?> api(String method, List<Object?> args) async => null;

      // 1. T20 라우팅
      await tester.pumpWidget(
        MaterialApp(
          home: BackendDialog(
            api: api,
            data: const {
              'id': 'route_t20',
              'kind': 'style_unify_profile',
              'title': 'T20 라우트',
              'styles': [],
              'fields': [],
            },
          ),
        ),
      );
      await tester.pumpAndSettle();
      expect(find.byType(UnifyPickStyleDialog), findsOneWidget);

      // 화면 간 전환 시 SizedBox 필수
      await tester.pumpWidget(const SizedBox());

      // 2. T21 라우팅
      await tester.pumpWidget(
        MaterialApp(
          home: BackendDialog(
            api: api,
            data: const {
              'id': 'route_t21',
              'kind': 'style_unify_regions',
              'title': 'T21 라우트',
              'areas': [],
            },
          ),
        ),
      );
      await tester.pumpAndSettle();
      expect(find.byType(UnifyAreaDialog), findsOneWidget);

      await tester.pumpWidget(const SizedBox());

      // 3. T22 라우팅
      await tester.pumpWidget(
        MaterialApp(
          home: BackendDialog(
            api: api,
            data: const {
              'id': 'route_t22',
              'kind': 'style_unify_result',
              'title': 'T22 라우트',
              'result': {},
            },
          ),
        ),
      );
      await tester.pumpAndSettle();
      expect(find.byType(UnifyResultDialog), findsOneWidget);

      await tester.pumpWidget(const SizedBox());
    });
  });
}
