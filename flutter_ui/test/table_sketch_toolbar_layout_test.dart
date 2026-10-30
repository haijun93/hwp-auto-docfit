import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:docfit_ui/features/table_sketch/table_sketch_screen.dart';

/// 창을 줄여도 표그림판 도구 줄의 메뉴가 화면 밖으로 가려지지 않는다(2026-10-30 사용자 보고).
void main() {
  const keys = [
    'toolLine',
    'toolRect',
    'toolEraser',
    'toolPreciseEraser',
    'toolText',
    'toolSelect',
    'toolLasso',
    'toolCellImage',
    'lineWidthThin',
    'lineWidthThick',
    'lineWidthDouble',
    'lineStyleSolid',
    'lineStyleDash',
    'lineStyleDot',
    'sketchOrgExample',
    'undoButton',
    'redoButton',
    'clearAllButton',
  ];

  Future<Object?> api(String name, List<Object?> args) async => {
    'ok': true,
    'rows': 0,
    'cols': 0,
    'cells': [],
    'width_mm': 0.0,
    'height_mm': 0.0,
    'warnings': [],
  };

  for (final size in const [
    Size(1280, 800),
    Size(1000, 700),
    Size(800, 640),
    Size(700, 640),
    Size(480, 700),
  ]) {
    testWidgets('all toolbar menus stay on screen at ${size.width.toInt()}px', (
      tester,
    ) async {
      tester.view.physicalSize = size;
      tester.view.devicePixelRatio = 1.0;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);
      await tester.pumpWidget(MaterialApp(home: TableSketchScreen(api: api)));
      await tester.pumpAndSettle();
      expect(tester.takeException(), isNull);
      for (final key in keys) {
        final finder = find.byKey(Key(key));
        expect(finder, findsOneWidget, reason: key);
        final rect = tester.getRect(finder);
        expect(
          rect.left >= 0 && rect.right <= size.width && rect.top >= 0,
          isTrue,
          reason: '$key $rect',
        );
        // 다른 것에 덮이지 않고 실제로 누를 수 있어야 한다.
        final hit = tester.hitTestOnBinding(rect.center);
        expect(
          hit.path.any(
            (e) =>
                e.target is RenderObject &&
                (finder.evaluate().single.renderObject == e.target ||
                    _isDescendant(
                      e.target as RenderObject,
                      finder.evaluate().single.renderObject!,
                    )),
          ),
          isTrue,
          reason: '$key is covered',
        );
      }
      // 선택한 도구에서 줄이 바뀌어도 넘침 오류가 없어야 한다.
      await tester.tap(find.byKey(const Key('toolCellImage')));
      await tester.pumpAndSettle();
      expect(tester.takeException(), isNull);
    });
  }
}

bool _isDescendant(RenderObject node, RenderObject ancestor) {
  RenderObject? current = node.parent;
  while (current != null) {
    if (current == ancestor) return true;
    current = current.parent;
  }
  return false;
}
