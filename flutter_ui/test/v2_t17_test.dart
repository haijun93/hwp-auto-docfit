import 'package:docfit_ui/main.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  group('T17 원본·결과 비교 Flutter 진입점 (결과 화면)', () {
    testWidgets('T17 결과 화면에 「원본·결과 비교」 버튼 표시 및 클릭 시 브리지 호출 검증 (폭 420px)', (
      tester,
    ) async {
      tester.view.physicalSize = const Size(420, 800);
      tester.view.devicePixelRatio = 1.0;
      addTearDown(() {
        tester.view.resetPhysicalSize();
        tester.view.resetDevicePixelRatio();
      });

      String? lastCalledMethod;
      List<Object?>? lastCalledArgs;

      Future<Object?> api(String method, List<Object?> args) async {
        if (method == 'open_diff') {
          lastCalledMethod = method;
          lastCalledArgs = args;
        }

        if (method == 'get_state') {
          return {
            'status': '처리 완료',
            'files': [
              {'name': '보고서.hwpx', 'path': r'C:\doc\보고서.hwpx'},
            ],
            'results': [
              {
                'name': '보고서(자간조정).hwpx',
                'path': r'C:\doc\보고서(자간조정).hwpx',
                'source': '보고서.hwpx',
                'pages': 3,
              },
            ],
            'completion': {
              'message': '처리 완료 · 성공 1개 / 실패 0개',
              'details': ['성공 1개 · 실패 0개'],
            },
            'card_options': {},
          };
        }
        if (method == 'open_diff') {
          return {
            'ok': true,
            'original': r'C:\doc\보고서.hwpx',
            'result': r'C:\doc\보고서(자간조정).hwpx',
          };
        }
        return null;
      }

      await tester.pumpWidget(DocFitApp(api: api));
      await tester.pumpAndSettle();

      // 4번째 탭 '4. 결과 확인'으로 이동
      expect(find.text('4. 결과 확인'), findsOneWidget);
      await tester.tap(find.text('4. 결과 확인'));
      await tester.pumpAndSettle();

      // 결과 화면에 「원본·결과 비교」 버튼이 렌더링되었는지 확인
      expect(find.byKey(const Key('compareResultButton')), findsOneWidget);
      expect(find.text('원본·결과 비교'), findsWidgets);

      // 420px 폭에서 오버플로 없음 검증
      expect(tester.takeException(), isNull);

      // 하단 「원본·결과 비교」 버튼 탭
      await tester.ensureVisible(find.byKey(const Key('compareResultButton')));
      await tester.tap(find.byKey(const Key('compareResultButton')));
      await tester.pumpAndSettle();

      // 브리지 open_diff(0) 호출 확인
      expect(lastCalledMethod, 'open_diff');
      expect(lastCalledArgs, isNotNull);
      expect(lastCalledArgs, [0]);
      expect(tester.takeException(), isNull);

      // 결과 목록 아이템별 비교 버튼(Key('compareItem-0')) 탭 검증
      lastCalledMethod = null;
      lastCalledArgs = null;
      expect(find.byKey(const Key('compareItem-0')), findsOneWidget);
      await tester.ensureVisible(find.byKey(const Key('compareItem-0')));
      await tester.tap(find.byKey(const Key('compareItem-0')));
      await tester.pumpAndSettle();

      expect(lastCalledMethod, 'open_diff');
      expect(lastCalledArgs, [0]);
      expect(tester.takeException(), isNull);
    });

    testWidgets('T17 브리지 오류 반환 시 오류 안내 영역 표시 검증 (폭 420px)', (tester) async {
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
              {'name': 'doc.hwpx', 'path': r'C:\doc.hwpx'},
            ],
            'results': [
              {
                'name': 'doc(결과).hwpx',
                'path': r'C:\doc(결과).hwpx',
                'source': 'doc.hwpx',
                'pages': 1,
              },
            ],
            'completion': {'message': '처리 완료'},
            'card_options': {},
          };
        }
        if (method == 'open_diff') {
          return {
            'ok': false,
            'error': '비교할 결과 문서가 없습니다.',
          };
        }
        return null;
      }

      await tester.pumpWidget(DocFitApp(api: api));
      await tester.pumpAndSettle();

      await tester.tap(find.text('4. 결과 확인'));
      await tester.pumpAndSettle();

      // 버튼 탭하여 오류 유도
      await tester.ensureVisible(find.byKey(const Key('compareResultButton')));
      await tester.tap(find.byKey(const Key('compareResultButton')));
      await tester.pumpAndSettle();

      // 오류 안내 위젯 및 문구 표시 확인
      expect(find.byKey(const Key('compareErrorMessage')), findsOneWidget);
      expect(find.text('비교할 결과 문서가 없습니다.'), findsWidgets);

      // 420px 폭에서 오류 안내 표시 상태에서도 오버플로 없음 확인
      expect(tester.takeException(), isNull);
    });

    testWidgets('T17 결과 목록이 없을 때 「원본·결과 비교」 버튼 비활성화 검증', (tester) async {
      tester.view.physicalSize = const Size(420, 800);
      tester.view.devicePixelRatio = 1.0;
      addTearDown(() {
        tester.view.resetPhysicalSize();
        tester.view.resetDevicePixelRatio();
      });

      Future<Object?> api(String method, List<Object?> args) async {
        if (method == 'get_state') {
          return {
            'status': '대기 중',
            'files': [],
            'results': [],
            'completion': {},
            'card_options': {},
          };
        }
        return null;
      }

      await tester.pumpWidget(DocFitApp(api: api));
      await tester.pumpAndSettle();

      await tester.tap(find.text('4. 결과 확인'));
      await tester.pumpAndSettle();

      final button = tester.widget<OutlinedButton>(
        find.byKey(const Key('compareResultButton')),
      );
      // results가 없으므로 비활성화(onPressed == null) 상태여야 함
      expect(button.onPressed, isNull);
      expect(tester.takeException(), isNull);
    });
  });
}
