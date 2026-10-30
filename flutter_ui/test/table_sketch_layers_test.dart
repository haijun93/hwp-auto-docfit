import 'package:flutter_test/flutter_test.dart';
import 'package:docfit_ui/features/table_sketch/table_sketch_models.dart';

void main() {
  TableSketchDoc twoLayers() {
    final doc = TableSketchDoc();
    doc.addLine(const SketchLine(x1: 0, y1: 0, x2: 4, y2: 0));
    doc.setText(const SketchText(x: 1, y: 1, text: '아래'));
    doc.claimUnassigned();
    doc.layers = [...doc.layers, const SketchLayer(id: 'top', name: '레이어 2')];
    doc.activeLayer = 'top';
    doc.addLine(const SketchLine(x1: 0, y1: 4, x2: 4, y2: 4));
    doc.setText(const SketchText(x: 1, y: 5, text: '위'));
    doc.claimUnassigned();
    return doc;
  }

  test('new objects go to the active layer', () {
    final doc = twoLayers();
    expect(doc.countIn(defaultSketchLayerId), 2);
    expect(doc.countIn('top'), 2);
    expect(doc.lines.map((l) => l.layer), [defaultSketchLayerId, 'top']);
  });

  test('locked layer objects are drawn but cannot be edited', () {
    final doc = twoLayers();
    doc.layers = [doc.layers.first.copyWith(locked: true), doc.layers.last];
    doc.repark();
    expect(doc.lines.length, 1);
    expect(doc.lines.single.layer, 'top');
    expect(doc.lockedLines.length, 1);
    expect(doc.lockedTexts.single.text, '아래');
  });

  test('hidden layers stay in the saved sketch but not in the Hangul table', () {
    final doc = twoLayers();
    doc.layers = [doc.layers.first, doc.layers.last.copyWith(visible: false)];
    doc.repark();
    expect(doc.lockedLines, isEmpty);
    final table = doc.toJson(forTable: true);
    expect((table['texts'] as List).map((t) => t['text']), ['아래']);
    expect(table.containsKey('layers'), isFalse);
    final saved = doc.toJson();
    expect((saved['lines'] as List).length, 2);
    final again = TableSketchDoc.fromJson(saved);
    expect(again.layers.last.visible, isFalse);
    expect(again.lines.length, 1);
    expect(again.toJson(forTable: true)['lines'], hasLength(1));
  });

  test('moving and removing layers', () {
    final doc = twoLayers();
    doc.moveToLayer({doc.lines.first}, {}, 'top');
    expect(doc.countIn('top'), 3);
    doc.removeLayer('top');
    expect(doc.layers.single.id, defaultSketchLayerId);
    expect(doc.lines.length + doc.texts.length, 1);
    expect(doc.activeLayer, defaultSketchLayerId);
    doc.removeLayer(defaultSketchLayerId); // 마지막 레이어는 남는다
    expect(doc.layers, hasLength(1));
  });

  test('old sketches without layers open on one default layer', () {
    final doc = TableSketchDoc.fromJson({
      'grid': {'cols': 36, 'rows': 50, 'cell_mm': 5.0},
      'lines': [
        {'x1': 0, 'y1': 0, 'x2': 3, 'y2': 0},
      ],
      'texts': [],
    });
    expect(doc.layers.single.id, defaultSketchLayerId);
    expect(doc.lines.single.layer, defaultSketchLayerId);
  });
}
