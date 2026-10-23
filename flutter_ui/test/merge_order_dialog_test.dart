import 'package:docfit_ui/features/conversion/merge_order_dialog.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  final sampleFiles = [
    {'name': '1번_기안서.hwp', 'path': r'C:\docs\1번_기안서.hwp'},
    {'name': '2번_결과보고.pdf', 'path': r'C:\docs\2번_결과보고.pdf'},
    {'name': '3번_붙임자료.hwpx', 'path': r'C:\docs\3번_붙임자료.hwpx'},
  ];

  testWidgets('MergeOrderDialog에서 ↑/↓ 버튼으로 2→3→1 순서 만들기 및 시작 시 순서 전달', (
    WidgetTester tester,
  ) async {
    List<String>? selectedOrder;

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: Builder(
            builder: (context) => ElevatedButton(
              key: const Key('openButton'),
              onPressed: () async {
                selectedOrder = await showDialog<List<String>>(
                  context: context,
                  builder: (_) => MergeOrderDialog(files: sampleFiles),
                );
              },
              child: const Text('대화상자 열기'),
            ),
          ),
        ),
      ),
    );

    await tester.tap(find.byKey(const Key('openButton')));
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('mergeOrderDialog')), findsOneWidget);

    // 초기 상태: 1번(인덱스 0), 2번(인덱스 1), 3번(인덱스 2)
    // 1단계: 2번 파일(인덱스 1)의 ↑ 버튼(mergeUp_1)을 눌러 맨 위로 이동 -> [2번, 1번, 3번]
    await tester.tap(find.byKey(const Key('mergeUp_1')));
    await tester.pumpAndSettle();

    // 2단계: 3번 파일(현재 인덱스 2)의 ↑ 버튼(mergeUp_2)을 눌러 1번 앞으로 이동 -> [2번, 3번, 1번]
    await tester.tap(find.byKey(const Key('mergeUp_2')));
    await tester.pumpAndSettle();

    // 「합치기 시작」 버튼 누르기
    await tester.tap(find.byKey(const Key('mergeStartButton')));
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('mergeOrderDialog')), findsNothing);
    expect(selectedOrder, [
      r'C:\docs\2번_결과보고.pdf',
      r'C:\docs\3번_붙임자료.hwpx',
      r'C:\docs\1번_기안서.hwp',
    ]);
  });

  testWidgets('MergeOrderDialog에서 취소 누르면 null 반환', (
    WidgetTester tester,
  ) async {
    List<String>? selectedOrder;

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: Builder(
            builder: (context) => ElevatedButton(
              key: const Key('openButton'),
              onPressed: () async {
                selectedOrder = await showDialog<List<String>>(
                  context: context,
                  builder: (_) => MergeOrderDialog(files: sampleFiles),
                );
              },
              child: const Text('대화상자 열기'),
            ),
          ),
        ),
      ),
    );

    await tester.tap(find.byKey(const Key('openButton')));
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('mergeOrderDialog')), findsOneWidget);

    // 「취소」 버튼 누르기
    await tester.tap(find.byKey(const Key('mergeCancelButton')));
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('mergeOrderDialog')), findsNothing);
    expect(selectedOrder, isNull);
  });

  testWidgets('MergeOrderDialog 폭 420 및 좁은 화면에서 오버플로우(넘침) 없음', (
    WidgetTester tester,
  ) async {
    tester.view.physicalSize = const Size(420, 700);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(() {
      tester.view.resetPhysicalSize();
      tester.view.resetDevicePixelRatio();
    });

    final longNameFiles = [
      {
        'name': '매우_긴_문서_이름_테스트_공문서_표준서식_결과보고서_최종본_확정_20261023.hwpx',
        'path': r'C:\docs\매우_긴_문서_이름_테스트_공문서_표준서식_결과보고서_최종본_확정_20261023.hwpx',
      },
      {
        'name': '첨부서류_상세_내역_및_설계도서_합본_자료_상세버전_1234567890.pdf',
        'path': r'C:\docs\첨부서류_상세_내역_및_설계도서_합본_자료_상세버전_1234567890.pdf',
      },
      {
        'name': '요약본_최종_검토본.txt',
        'path': r'C:\docs\요약본_최종_검토본.txt',
      },
    ];

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: Center(
            child: MergeOrderDialog(files: longNameFiles),
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(tester.takeException(), isNull);
    final dialogFinder = find.byKey(const Key('mergeOrderDialog'));
    expect(dialogFinder, findsOneWidget);
    final size = tester.getSize(dialogFinder);
    expect(size.width, lessThanOrEqualTo(420.0));
  });
}
