import 'package:docfit_ui/core/api/public_language_api.dart';
import 'package:docfit_ui/features/public_language/exclusion_manager_screen.dart';
import 'package:docfit_ui/features/public_language/public_language_screen.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

Map<String, Object?> envelope(Map<String, Object?> data) => {
  'api_version': 1,
  'ok': true,
  'data': data,
  'error': null,
};

Map<String, Object?> sampleReviewResult({
  String reviewId = 'review-uuid-1',
  List<Map<String, Object?>>? issues,
}) => {
  'review_id': reviewId,
  'issues': issues ??
      [
        {
          'id': 'issue-uuid-1',
          'source_path': 'C:\\문서\\보고서.hwpx',
          'rule_id': 'public.geumbeon',
          'category': '공공언어',
          'source': '금번',
          'suggestion': '이번',
          'reason': '쉬운 표현 제안',
          'count': 2,
          'examples': ['금번 계획을 보고합니다.'],
          'locations': [
            {'section': 'Contents/section0.xml', 'paragraph': 1, 'page': null},
            {'section': 'Contents/section0.xml', 'paragraph': 2, 'page': null},
          ],
        },
        {
          'id': 'issue-uuid-2',
          'source_path': 'C:\\문서\\보고서.hwpx',
          'rule_id': 'public.ikil',
          'category': '공공언어',
          'source': '익일',
          'suggestion': '다음 날',
          'reason': '쉬운 한자어 순화',
          'count': 1,
          'examples': ['익일 오전까지 제출 바랍니다.'],
          'locations': [
            {'section': 'Contents/section0.xml', 'paragraph': 5, 'page': null},
          ],
        },
      ],
  'errors': [],
};

Map<String, Object?> sampleApplyResult() => {
  'results': [
    {
      'source': 'C:\\문서\\보고서.hwpx',
      'path': 'C:\\문서\\보고서_공공언어교정.hwpx',
      'changes': 2,
    },
  ],
  'errors': [],
};

Future<void> pumpScreen(
  WidgetTester tester, {
  required ApiCall api,
  double width = 800.0,
  double height = 600.0,
  Widget? child,
}) async {
  tester.view.physicalSize = Size(width, height);
  tester.view.devicePixelRatio = 1.0;
  addTearDown(tester.view.resetPhysicalSize);
  addTearDown(tester.view.resetDevicePixelRatio);

  await tester.pumpWidget(
    MaterialApp(
      home: child ?? PublicLanguageScreen(api: api),
    ),
  );
  await tester.pumpAndSettle();
}

void main() {
  testWidgets('가짜 api로 진행→결과 표시 및 결과 0건 안내', (tester) async {
    int eventCallCount = 0;
    Future<Object?> api(String name, List<Object?> args) async {
      if (name == 'public_language') {
        final action = args[0] as String;
        if (action == 'start') {
          return envelope({'job_id': 'job-scan-1'});
        }
      }
      if (name == 'get_events') {
        eventCallCount++;
        if (eventCallCount == 1) {
          return {
            'events': [
              {
                'seq': 1,
                'job_id': 'job-scan-1',
                'type': 'progress',
                'data': {'percent': 50.0, 'stage': 'scan'},
              },
            ],
            'next_seq': 1,
          };
        } else {
          return {
            'events': [
              {
                'seq': 2,
                'job_id': 'job-scan-1',
                'type': 'done',
                'data': {'result': sampleReviewResult()},
              },
            ],
            'next_seq': 2,
          };
        }
      }
      return envelope({});
    }

    await pumpScreen(tester, api: api);

    expect(find.text('공공언어 바로쓰기 검토'), findsOneWidget);
    expect(find.byKey(const Key('startReview')), findsOneWidget);

    // 검토 시작 클릭
    await tester.tap(find.byKey(const Key('startReview')));
    await tester.pump(); // 진행 상태 진입
    await tester.pump(const Duration(milliseconds: 200)); // 1차 폴링
    await tester.pump(const Duration(milliseconds: 200)); // 2차 폴링 및 완료
    await tester.pumpAndSettle();

    // 결과 목록 표시 검증
    expect(find.text('금번'), findsOneWidget);
    expect(find.text('이번'), findsOneWidget);
    expect(find.text('쉬운 표현 제안'), findsOneWidget);
    expect(find.text('익일'), findsOneWidget);
    expect(find.text('다음 날'), findsOneWidget);
    expect(find.text('쉬운 한자어 순화'), findsOneWidget);
    expect(find.text('공공언어'), findsNWidgets(2));
    expect(find.byKey(const Key('applySelected')), findsOneWidget);

    // 결과 0건 안내 검증
    Future<Object?> apiZero(String name, List<Object?> args) async {
      if (name == 'public_language' && args[0] == 'start') {
        return envelope({'job_id': 'job-scan-zero'});
      }
      if (name == 'get_events') {
        return {
          'events': [
            {
              'seq': 1,
              'job_id': 'job-scan-zero',
              'type': 'done',
              'data': {
                'result': sampleReviewResult(issues: []),
              },
            },
          ],
          'next_seq': 1,
        };
      }
      return envelope({});
    }

    await tester.pumpWidget(const SizedBox()); // 앞 화면 상태를 버리고 새로 띄운다
    await pumpScreen(tester, api: apiZero);
    await tester.tap(find.byKey(const Key('startReview')));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 200));
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('emptyResultNotice')), findsOneWidget);
    expect(find.text('검출된 공공언어 개선 항목이 없습니다.'), findsOneWidget);
  });

  testWidgets('검토 진행 중 취소 요청 및 취소 사건 수신', (tester) async {
    final calls = <List<Object?>>[];
    bool cancelRequested = false;

    Future<Object?> api(String name, List<Object?> args) async {
      calls.add([name, ...args]);
      if (name == 'public_language' && args[0] == 'start') {
        return envelope({'job_id': 'job-scan-cancel'});
      }
      if (name == 'cancel_job') {
        cancelRequested = true;
        return {'cancelled': true};
      }
      if (name == 'get_events') {
        if (!cancelRequested) {
          return {
            'events': [
              {
                'seq': 1,
                'job_id': 'job-scan-cancel',
                'type': 'progress',
                'data': {'percent': 30.0, 'stage': 'scan'},
              },
            ],
            'next_seq': 1,
          };
        } else {
          return {
            'events': [
              {
                'seq': 2,
                'job_id': 'job-scan-cancel',
                'type': 'cancelled',
                'data': {},
              },
            ],
            'next_seq': 2,
          };
        }
      }
      return envelope({});
    }

    await pumpScreen(tester, api: api);
    await tester.tap(find.byKey(const Key('startReview')));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 200));

    expect(find.byKey(const Key('cancelJob')), findsOneWidget);

    // 취소 버튼 클릭
    await tester.tap(find.byKey(const Key('cancelJob')));
    await tester.pump();
    expect(calls.any((c) => c[0] == 'cancel_job' && c[1] == 'job-scan-cancel'), isTrue);

    // 폴링으로 cancelled 수신
    await tester.pump(const Duration(milliseconds: 200));
    await tester.pumpAndSettle();

    expect(find.text('작업이 취소되었습니다.'), findsOneWidget);
    expect(find.byKey(const Key('startReview')), findsOneWidget);
  });

  testWidgets('선택 항목만 새 사본에 적용 시 넘기는 id 검증', (tester) async {
    final calls = <List<Object?>>[];
    int eventCallCount = 0;

    Future<Object?> api(String name, List<Object?> args) async {
      calls.add([name, ...args]);
      if (name == 'public_language') {
        final action = args[0] as String;
        if (action == 'start') {
          return envelope({'job_id': 'job-scan-select'});
        }
        if (action == 'apply') {
          return envelope({'job_id': 'job-apply-1'});
        }
      }
      if (name == 'get_events') {
        eventCallCount++;
        if (eventCallCount == 1) {
          return {
            'events': [
              {
                'seq': 1,
                'job_id': 'job-scan-select',
                'type': 'done',
                'data': {'result': sampleReviewResult(reviewId: 'review-target')},
              },
            ],
            'next_seq': 1,
          };
        } else {
          return {
            'events': [
              {
                'seq': 2,
                'job_id': 'job-apply-1',
                'type': 'done',
                'data': {'result': sampleApplyResult()},
              },
            ],
            'next_seq': 2,
          };
        }
      }
      return envelope({});
    }

    await pumpScreen(tester, api: api);
    await tester.tap(find.byKey(const Key('startReview')));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 200));
    await tester.pumpAndSettle();

    // 초기: 2개 모두 선택됨. 2번째 항목(issue-uuid-2)의 체크박스를 눌러 해제
    final secondCheckbox = find.byKey(const Key('issueCheck_issue-uuid-2'));
    expect(secondCheckbox, findsOneWidget);
    await tester.tap(secondCheckbox);
    await tester.pumpAndSettle();

    // '선택 항목 고치기' 클릭
    final applyBtn = find.byKey(const Key('applySelected'));
    expect(applyBtn, findsOneWidget);
    await tester.tap(applyBtn);
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 200));
    await tester.pumpAndSettle();

    // apply 호출 시 review_id와 넘긴 ids 목록 검증
    final applyCalls = calls.where((c) => c[0] == 'public_language' && c[1] == 'apply').toList();
    expect(applyCalls, hasLength(1));

    final payload = applyCalls.first[2] as Map;
    expect(payload['review_id'], 'review-target');
    expect(payload['ids'], ['issue-uuid-1']); // issue-uuid-2는 제외되고 issue-uuid-1만 넘겨짐!

    // 적용 완료 확인
    expect(find.text('공공언어 교정 사본이 생성되었습니다.'), findsOneWidget);
    expect(find.text('C:\\문서\\보고서_공공언어교정.hwpx'), findsOneWidget);
  });

  testWidgets('제외어 관리 화면: 목록 로드·추가·삭제', (tester) async {
    final calls = <List<Object?>>[];
    List<String> currentExclusions = ['금번', '익일'];

    Future<Object?> api(String name, List<Object?> args) async {
      calls.add([name, ...args]);
      if (name == 'proofreading_exclusions') {
        final action = args[0] as String;
        final payload = args.length > 1 && args[1] is Map ? args[1] as Map : {};
        if (action == 'list') {
          return envelope({'expressions': List<String>.from(currentExclusions)});
        }
        if (action == 'add') {
          final toAdd = (payload['expressions'] as List? ?? []).cast<String>();
          currentExclusions.addAll(toAdd);
          currentExclusions = currentExclusions.toSet().toList()..sort();
          return envelope({'expressions': List<String>.from(currentExclusions)});
        }
        if (action == 'delete') {
          final toDel = (payload['expressions'] as List? ?? []).cast<String>();
          currentExclusions.removeWhere((e) => toDel.contains(e));
          return envelope({'expressions': List<String>.from(currentExclusions)});
        }
      }
      return envelope({});
    }

    await pumpScreen(
      tester,
      api: api,
      child: ExclusionManagerScreen(api: api),
    );

    // 1. 목록 표시 확인
    expect(find.text('금번'), findsOneWidget);
    expect(find.text('익일'), findsOneWidget);

    // 2. 추가: '명일' 입력 후 Key('exclusionAdd') 탭
    await tester.enterText(find.byKey(const Key('exclusionInput')), '명일');
    await tester.tap(find.byKey(const Key('exclusionAdd')));
    await tester.pumpAndSettle();

    expect(find.text('명일'), findsOneWidget);
    final addCall = calls.firstWhere((c) => c[0] == 'proofreading_exclusions' && c[1] == 'add');
    expect((addCall[2] as Map)['expressions'], ['명일']);

    // 3. 삭제: 첫 번째 항목(0번) 삭제 버튼 탭
    expect(find.byKey(const Key('exclusionDelete_0')), findsOneWidget);
    await tester.tap(find.byKey(const Key('exclusionDelete_0')));
    await tester.pumpAndSettle();

    final delCall = calls.firstWhere((c) => c[0] == 'proofreading_exclusions' && c[1] == 'delete');
    expect((delCall[2] as Map)['expressions'], isNotEmpty);
  });

  testWidgets('폭 420에서 오버플로우(넘침) 없음', (tester) async {
    int eventCallCount = 0;
    Future<Object?> api(String name, List<Object?> args) async {
      if (name == 'public_language') {
        final action = args[0] as String;
        if (action == 'start') return envelope({'job_id': 'job-scan-420'});
        if (action == 'apply') return envelope({'job_id': 'job-apply-420'});
      }
      if (name == 'proofreading_exclusions') {
        return envelope({'expressions': ['금번', '익일', '명일']});
      }
      if (name == 'get_events') {
        eventCallCount++;
        if (eventCallCount == 1) {
          return {
            'events': [
              {
                'seq': 1,
                'job_id': 'job-scan-420',
                'type': 'progress',
                'data': {'percent': 45.0, 'stage': 'scan'},
              },
            ],
            'next_seq': 1,
          };
        } else {
          return {
            'events': [
              {
                'seq': 2,
                'job_id': 'job-scan-420',
                'type': 'done',
                'data': {'result': sampleReviewResult()},
              },
            ],
            'next_seq': 2,
          };
        }
      }
      return envelope({});
    }

    // 1) 문서 선택 화면 (width: 420)
    await pumpScreen(tester, api: api, width: 420.0, height: 800.0);
    expect(tester.takeException(), isNull);

    // 2) 검토 진행 및 결과 화면 (width: 420)
    await tester.tap(find.byKey(const Key('startReview')));
    await tester.pump();
    expect(tester.takeException(), isNull);
    await tester.pump(const Duration(milliseconds: 200));
    expect(tester.takeException(), isNull);
    await tester.pump(const Duration(milliseconds: 200));
    await tester.pumpAndSettle();
    expect(tester.takeException(), isNull);

    // 3) 제외어 관리 화면 (width: 420)
    await pumpScreen(
      tester,
      api: api,
      width: 420.0,
      height: 800.0,
      child: ExclusionManagerScreen(api: api),
    );
    expect(tester.takeException(), isNull);
  });
}
