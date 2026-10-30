import 'dart:async';
import 'dart:math' as math;

import 'package:flutter/gestures.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../core/api/abbreviation_api.dart' show ApiCall;
import 'table_sketch_api.dart';
import 'table_sketch_models.dart';
import 'dart:convert';
import 'dart:ui' as ui;

import '../../core/drop_events.dart';
import 'table_sketch_painter.dart';
import 'table_sketch_selection.dart';

enum SketchToolMode {
  line,
  rect,
  eraser,
  preciseEraser,
  text,
  select,
  lasso,
  cellImage,
}

/// 표그림판 화면: 점선 격자 용지에 직선을 그려 한/글 표로 변환 및 복사.
class TableSketchScreen extends StatefulWidget {
  const TableSketchScreen({super.key, required this.api});

  final ApiCall api;

  @override
  State<TableSketchScreen> createState() => _TableSketchScreenState();
}

class _TableSketchScreenState extends State<TableSketchScreen> {
  late final TableSketchApi _sketchApi;

  // 도구 및 속성 상태
  SketchToolMode _tool = SketchToolMode.line;
  String _lineWidth = 'thin'; // thin, thick, double
  String _lineStyle = 'solid'; // solid, dash, dot

  // 문서 데이터
  late TableSketchDoc _doc;
  final List<TableSketchDoc> _undoStack = [];
  final List<TableSketchDoc> _redoStack = [];

  // 선택 및 드래그 제스처 상태
  // 여러 개체 선택(선택·올가미 도구 공통): 끌어 옮기기·복사·붙여넣기·삭제·굵기 변경
  SketchSelection _sel = SketchSelection();
  List<Offset>? _lassoPath; // 화면 좌표. 선택 도구는 [시작, 현재] 사각형
  bool _movingSelection = false;
  Offset? _moveOrigin; // 격자 단위
  int _movedDx = 0, _movedDy = 0;
  bool _moveSnapshotTaken = false;
  SketchClip? _clipboard;
  int _pasteShift = 0;
  Offset? _lastErasePos;
  // 6탭 화면에서는 다른 탭이 먼저 자동 초점을 가져가 단축키(Ctrl+Z·Delete·Ctrl+C/V/D·방향키)가
  // 먹지 않았다 — 캔버스를 누르면 이 화면이 초점을 가져온다(2026-10-30 실제 앱 시험).
  final FocusNode _keyboardFocus = FocusNode(debugLabel: 'tableSketch');

  // 칸 배경 그림: '칸 그림' 도구로 고른 칸, 풀어 둔 그림, 끌어 놓기 알림 해제 함수.
  (int, int)? _imageTarget;
  final Map<String, ui.Image> _decoded = {};
  final Set<String> _decoding = {};
  void Function()? _stopImageDrops;
  final GlobalKey _canvasKey = GlobalKey(debugLabel: 'sketchCanvasArea');
  Offset? _dragStart;
  Offset? _dragCurrent;
  SketchLine? _previewLine;
  Rect? _previewRect;
  bool _dragChangedLines = false;

  // 뷰포트 확대/축소 및 기본 크기
  double _zoom = 1.0;
  static const double _baseCellSize = 16.0;
  double get _cellSize => _baseCellSize * _zoom;

  // 백엔드 미리보기 및 복사 상태
  TableSketchPreviewResult? _previewResult;
  bool _previewLoading = false;
  Timer? _previewDebounceTimer;
  bool _copying = false;

  // 저장/불러오기 컨트롤러
  final TextEditingController _saveNameController = TextEditingController(
    text: '새 표 서식',
  );

  @override
  void initState() {
    super.initState();
    _sketchApi = TableSketchApi(widget.api);
    _doc = TableSketchDoc();
    _stopImageDrops = watchWindowEvent(
      'docfit-sketch-image-dropped',
      () => unawaited(takeDroppedImage()),
    );
    _requestPreview();
  }

  // 끌기는 언제나 그리기에 쓰고(스크롤 상자가 끌기를 가져가면 선이 그려지지 않았다), 화면 이동은 휠·스크롤 막대로 한다.
  final ScrollController _vScroll = ScrollController();
  final ScrollController _hScroll = ScrollController();

  @override
  void dispose() {
    _previewDebounceTimer?.cancel();
    _keyboardFocus.dispose();
    _stopImageDrops?.call();
    for (final image in _decoded.values) {
      image.dispose();
    }
    _saveNameController.dispose();
    _vScroll.dispose();
    _hScroll.dispose();
    super.dispose();
  }

  void _scrollBy(ScrollController controller, double delta) {
    if (!controller.hasClients) return;
    final position = controller.position;
    controller.jumpTo(
      (position.pixels + delta).clamp(
        position.minScrollExtent,
        position.maxScrollExtent,
      ),
    );
  }

  // --- 실행 취소 / 다시 실행 ---

  void _saveSnapshot() {
    _undoStack.add(_doc.clone());
    if (_undoStack.length > 50) _undoStack.removeAt(0);
    _redoStack.clear();
  }

  void _undo() {
    if (_undoStack.isEmpty) return;
    setState(() {
      _redoStack.add(_doc.clone());
      _doc = _undoStack.removeLast();
      _sel = SketchSelection();
      _previewLine = null;
      _previewRect = null;
    });
    _triggerPreviewDebounced();
  }

  void _redo() {
    if (_redoStack.isEmpty) return;
    setState(() {
      _undoStack.add(_doc.clone());
      _doc = _redoStack.removeLast();
      _sel = SketchSelection();
      _previewLine = null;
      _previewRect = null;
    });
    _triggerPreviewDebounced();
  }

  void _clearAll() {
    showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('전체 지우기'),
        content: const Text('그린 선과 글을 모두 지우시겠습니까?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(false),
            child: const Text('취소'),
          ),
          FilledButton(
            onPressed: () => Navigator.of(ctx).pop(true),
            child: const Text('지우기'),
          ),
        ],
      ),
    ).then((confirmed) {
      if (confirmed == true && mounted) {
        _saveSnapshot();
        setState(() {
          _doc = TableSketchDoc(grid: _doc.grid);
          _sel = SketchSelection();
          _previewLine = null;
          _previewRect = null;
        });
        _triggerPreviewDebounced();
      }
    });
  }

  // --- 백엔드 미리보기 (0.5초 디바운스) ---

  void _triggerPreviewDebounced() {
    _previewDebounceTimer?.cancel();
    _previewDebounceTimer = Timer(
      const Duration(milliseconds: 500),
      _requestPreview,
    );
  }

  Future<void> _requestPreview() async {
    if (!mounted) return;
    setState(() => _previewLoading = true);
    try {
      final res = await _sketchApi.preview(_doc.toJson());
      if (mounted) {
        setState(() {
          _previewResult = res;
          _previewLoading = false;
        });
      }
    } catch (_) {
      if (mounted) setState(() => _previewLoading = false);
    }
  }

  // --- 한/글 복사 ---

  Future<void> _copyToClipboard() async {
    if (_copying) return;
    setState(() => _copying = true);
    try {
      final res = await _sketchApi.copy(_doc.toJson());
      if (mounted) {
        setState(() => _copying = false);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(res.message),
            backgroundColor: res.ok
                ? const Color(0xFF16A34A)
                : const Color(0xFFDC2626),
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        setState(() => _copying = false);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('복사 중 오류가 발생했습니다: $e'),
            backgroundColor: const Color(0xFFDC2626),
          ),
        );
      }
    }
  }

  // --- 조직도 예시 ---

  void _loadOrgExample() {
    _saveSnapshot();
    setState(() {
      final newDoc = TableSketchDoc(
        grid: const GridConfig(cols: 36, rows: 50, cellMm: 5.0),
      );

      // 위 상자 1개: (12, 4) ~ (24, 8) -> 선 4개
      newDoc.addLine(const SketchLine(x1: 12, y1: 4, x2: 24, y2: 4));
      newDoc.addLine(const SketchLine(x1: 12, y1: 8, x2: 24, y2: 8));
      newDoc.addLine(const SketchLine(x1: 12, y1: 4, x2: 12, y2: 8));
      newDoc.addLine(const SketchLine(x1: 24, y1: 4, x2: 24, y2: 8));
      newDoc.setText(
        const SketchText(x: 16, y: 5, text: '총괄팀', bold: true, align: 'center'),
      );

      // 가운데 세로선 1개: (18, 8) ~ (18, 14)
      newDoc.addLine(const SketchLine(x1: 18, y1: 8, x2: 18, y2: 14));

      // 가로 연결선 1개: (6, 14) ~ (30, 14)
      newDoc.addLine(const SketchLine(x1: 6, y1: 14, x2: 30, y2: 14));

      // 아래 상자로 내려가는 연결선 3개
      newDoc.addLine(const SketchLine(x1: 6, y1: 14, x2: 6, y2: 18));
      newDoc.addLine(const SketchLine(x1: 18, y1: 14, x2: 18, y2: 18));
      newDoc.addLine(const SketchLine(x1: 30, y1: 14, x2: 30, y2: 18));

      // 아래 상자 3개: 각 4개 선
      // 상자 1: (2, 18) ~ (10, 22)
      newDoc.addLine(const SketchLine(x1: 2, y1: 18, x2: 10, y2: 18));
      newDoc.addLine(const SketchLine(x1: 2, y1: 22, x2: 10, y2: 22));
      newDoc.addLine(const SketchLine(x1: 2, y1: 18, x2: 2, y2: 22));
      newDoc.addLine(const SketchLine(x1: 10, y1: 18, x2: 10, y2: 22));
      newDoc.setText(
        const SketchText(
          x: 4,
          y: 19,
          text: '개발팀',
          bold: false,
          align: 'center',
        ),
      );

      // 상자 2: (14, 18) ~ (22, 22)
      newDoc.addLine(const SketchLine(x1: 14, y1: 18, x2: 22, y2: 18));
      newDoc.addLine(const SketchLine(x1: 14, y1: 22, x2: 22, y2: 22));
      newDoc.addLine(const SketchLine(x1: 14, y1: 18, x2: 14, y2: 22));
      newDoc.addLine(const SketchLine(x1: 22, y1: 18, x2: 22, y2: 22));
      newDoc.setText(
        const SketchText(
          x: 16,
          y: 19,
          text: '기획팀',
          bold: false,
          align: 'center',
        ),
      );

      // 상자 3: (26, 18) ~ (34, 22)
      newDoc.addLine(const SketchLine(x1: 26, y1: 18, x2: 34, y2: 18));
      newDoc.addLine(const SketchLine(x1: 26, y1: 22, x2: 34, y2: 22));
      newDoc.addLine(const SketchLine(x1: 26, y1: 18, x2: 26, y2: 22));
      newDoc.addLine(const SketchLine(x1: 34, y1: 18, x2: 34, y2: 22));
      newDoc.setText(
        const SketchText(
          x: 28,
          y: 19,
          text: '운영팀',
          bold: false,
          align: 'center',
        ),
      );

      _doc = newDoc;
      _sel = SketchSelection();
      _previewLine = null;
      _previewRect = null;
    });
    _triggerPreviewDebounced();
  }

  // --- 저장 / 불러오기 / 삭제 ---

  Future<void> _saveSketch() async {
    final name = _saveNameController.text.trim();
    if (name.isEmpty) {
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(const SnackBar(content: Text('저장할 이름을 입력하세요.')));
      return;
    }
    final res = await _sketchApi.save(name, _doc.toJson());
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            res['ok'] == true ? '저장되었습니다.' : '저장 실패: ${res['message']}',
          ),
        ),
      );
    }
  }

  Future<void> _openListDialog() async {
    final list = await _sketchApi.list();
    if (!mounted) return;
    if (list.isEmpty) {
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(const SnackBar(content: Text('저장된 서식이 없습니다.')));
      return;
    }
    showDialog<void>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('저장된 표 서식 목록'),
        content: SizedBox(
          width: 320,
          child: ListView.builder(
            shrinkWrap: true,
            itemCount: list.length,
            itemBuilder: (ctx, idx) {
              final item = list[idx];
              return ListTile(
                title: Text(item),
                trailing: IconButton(
                  icon: const Icon(Icons.delete_outline, size: 20),
                  onPressed: () async {
                    await _sketchApi.delete(item);
                    if (ctx.mounted) Navigator.of(ctx).pop();
                    _openListDialog();
                  },
                ),
                onTap: () async {
                  final loaded = await _sketchApi.load(item);
                  if (loaded != null && mounted) {
                    _saveSnapshot();
                    setState(() {
                      _doc = loaded;
                      _saveNameController.text = item;
                      _sel = SketchSelection();
                    });
                    _triggerPreviewDebounced();
                  }
                  if (ctx.mounted) Navigator.of(ctx).pop();
                },
              );
            },
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(),
            child: const Text('닫기'),
          ),
        ],
      ),
    );
  }

  // --- 캔버스 제스처 처리 ---

  void _handlePanStart(DragStartDetails details) {
    final pos = details.localPosition;
    _dragChangedLines = false;
    setState(() {
      _dragStart = pos;
      _dragCurrent = pos;
    });

    if (_tool == SketchToolMode.preciseEraser) {
      _lastErasePos = pos;
      _erasePrecisionAt(pos, inDrag: true);
    } else if (_tool == SketchToolMode.eraser) {
      _eraseLineAt(pos);
    } else if (_tool == SketchToolMode.select ||
        _tool == SketchToolMode.lasso) {
      _beginSelectionDrag(pos);
    }
  }

  void _handlePanUpdate(DragUpdateDetails details) {
    final pos = details.localPosition;
    // PointerUp에서도 호출되므로 같은 위치를 다시 지우지 않는다.
    if (_tool == SketchToolMode.preciseEraser && pos == _dragCurrent) return;
    setState(() => _dragCurrent = pos);

    if (_tool == SketchToolMode.line && _dragStart != null) {
      _updateLinePreview(_dragStart!, pos);
    } else if (_tool == SketchToolMode.rect && _dragStart != null) {
      _updateRectPreview(_dragStart!, pos);
    } else if (_tool == SketchToolMode.eraser) {
      _eraseLineAt(pos);
    } else if (_tool == SketchToolMode.preciseEraser) {
      // 빠르게 끌어도 지나간 칸을 빠뜨리지 않게 칸의 1/4 간격으로 나눠 지운다.
      for (final point in samplePath(
        _lastErasePos ?? pos,
        pos,
        _cellSize / 4,
      )) {
        _erasePrecisionAt(point, inDrag: true);
      }
      _lastErasePos = pos;
    } else if (_tool == SketchToolMode.select ||
        _tool == SketchToolMode.lasso) {
      _updateSelectionDrag(pos);
    }
  }

  void _handlePanEnd(DragEndDetails details) {
    _lastErasePos = null;
    if (_tool == SketchToolMode.select || _tool == SketchToolMode.lasso) {
      _endSelectionDrag();
    }
    if (_dragChangedLines) {
      _dragChangedLines = false;
      _triggerPreviewDebounced();
    }
    if (_tool == SketchToolMode.line &&
        _dragStart != null &&
        _dragCurrent != null) {
      _commitLine(_dragStart!, _dragCurrent!);
    } else if (_tool == SketchToolMode.rect &&
        _dragStart != null &&
        _dragCurrent != null) {
      _commitRect(_dragStart!, _dragCurrent!);
    }

    setState(() {
      _dragStart = null;
      _dragCurrent = null;
      _previewLine = null;
      _previewRect = null;
    });
  }

  void _handleTapUp(TapUpDetails details) {
    final pos = details.localPosition;
    if (_tool == SketchToolMode.text) {
      _openTextDialogAt(pos);
    } else if (_tool == SketchToolMode.select ||
        _tool == SketchToolMode.lasso) {
      _selectLineAt(pos);
    } else if (_tool == SketchToolMode.line || _tool == SketchToolMode.rect) {
      // 그리기 도구로 이미 있는 사각형·직선을 한 번 누르면 그 모형을 골라 바로 옮길 수 있게 한다.
      if (shapeSelect(_doc, pos / _cellSize, _hitTolerance).lines.isNotEmpty) {
        setState(() => _tool = SketchToolMode.select);
        _selectLineAt(pos);
      }
    } else if (_tool == SketchToolMode.eraser) {
      _eraseLineAt(pos);
    } else if (_tool == SketchToolMode.preciseEraser) {
      _erasePrecisionAt(pos);
    } else if (_tool == SketchToolMode.cellImage) {
      _pickImageCell(pos);
    }
  }

  // --- 선 / 사각형 스냅 및 커밋 ---

  void _updateLinePreview(Offset start, Offset current) {
    final gx1 = (start.dx / _cellSize).round().clamp(0, _doc.grid.cols);
    final gy1 = (start.dy / _cellSize).round().clamp(0, _doc.grid.rows);
    final rawGx2 = (current.dx / _cellSize).round().clamp(0, _doc.grid.cols);
    final rawGy2 = (current.dy / _cellSize).round().clamp(0, _doc.grid.rows);

    final snapped = snapLineCoords(
      gx1,
      gy1,
      rawGx2,
      rawGy2,
      _doc.grid.cols,
      _doc.grid.rows,
    );
    if (snapped != null) {
      setState(() {
        _previewLine = SketchLine(
          x1: gx1,
          y1: gy1,
          x2: snapped.x,
          y2: snapped.y,
          width: _lineWidth,
          style: _lineStyle,
        );
      });
    } else {
      setState(() => _previewLine = null);
    }
  }

  void _commitLine(Offset start, Offset current) {
    final gx1 = (start.dx / _cellSize).round().clamp(0, _doc.grid.cols);
    final gy1 = (start.dy / _cellSize).round().clamp(0, _doc.grid.rows);
    final rawGx2 = (current.dx / _cellSize).round().clamp(0, _doc.grid.cols);
    final rawGy2 = (current.dy / _cellSize).round().clamp(0, _doc.grid.rows);

    final snapped = snapLineCoords(
      gx1,
      gy1,
      rawGx2,
      rawGy2,
      _doc.grid.cols,
      _doc.grid.rows,
    );
    if (snapped != null) {
      _saveSnapshot();
      final newLine = SketchLine(
        x1: gx1,
        y1: gy1,
        x2: snapped.x,
        y2: snapped.y,
        width: _lineWidth,
        style: _lineStyle,
      );
      setState(() {
        _doc.addLine(newLine);
      });
      _triggerPreviewDebounced();
    }
  }

  void _updateRectPreview(Offset start, Offset current) {
    final gx1 = (start.dx / _cellSize).round().clamp(0, _doc.grid.cols);
    final gy1 = (start.dy / _cellSize).round().clamp(0, _doc.grid.rows);
    final gx2 = (current.dx / _cellSize).round().clamp(0, _doc.grid.cols);
    final gy2 = (current.dy / _cellSize).round().clamp(0, _doc.grid.rows);

    final minX = math.min(gx1, gx2);
    final maxX = math.max(gx1, gx2);
    final minY = math.min(gy1, gy2);
    final maxY = math.max(gy1, gy2);

    if (minX < maxX && minY < maxY) {
      setState(() {
        _previewRect = Rect.fromLTRB(
          minX * _cellSize,
          minY * _cellSize,
          maxX * _cellSize,
          maxY * _cellSize,
        );
      });
    } else {
      setState(() => _previewRect = null);
    }
  }

  void _commitRect(Offset start, Offset current) {
    final gx1 = (start.dx / _cellSize).round().clamp(0, _doc.grid.cols);
    final gy1 = (start.dy / _cellSize).round().clamp(0, _doc.grid.rows);
    final gx2 = (current.dx / _cellSize).round().clamp(0, _doc.grid.cols);
    final gy2 = (current.dy / _cellSize).round().clamp(0, _doc.grid.rows);

    final minX = math.min(gx1, gx2);
    final maxX = math.max(gx1, gx2);
    final minY = math.min(gy1, gy2);
    final maxY = math.max(gy1, gy2);

    if (minX < maxX && minY < maxY) {
      _saveSnapshot();
      setState(() {
        // 상단 가로선
        _doc.addLine(
          SketchLine(
            x1: minX,
            y1: minY,
            x2: maxX,
            y2: minY,
            width: _lineWidth,
            style: _lineStyle,
          ),
        );
        // 하단 가로선
        _doc.addLine(
          SketchLine(
            x1: minX,
            y1: maxY,
            x2: maxX,
            y2: maxY,
            width: _lineWidth,
            style: _lineStyle,
          ),
        );
        // 좌측 세로선
        _doc.addLine(
          SketchLine(
            x1: minX,
            y1: minY,
            x2: minX,
            y2: maxY,
            width: _lineWidth,
            style: _lineStyle,
          ),
        );
        // 우측 세로선
        _doc.addLine(
          SketchLine(
            x1: maxX,
            y1: minY,
            x2: maxX,
            y2: maxY,
            width: _lineWidth,
            style: _lineStyle,
          ),
        );
      });
      _triggerPreviewDebounced();
    }
  }

  // --- 지우개 & 선택 로직 ---

  void _erasePrecisionAt(Offset pos, {bool inDrag = false}) {
    // 칸 끝(격자점) 근처는 어느 칸에도 속하지 않게 해, 끌어 지날 때 이웃 칸까지 지우지 않는다
    // (2026-10-30 실제 앱 시험: 가운데 4칸을 끌었는데 6칸이 모두 지워졌다).
    final hit = unitSegmentAt(
      _doc,
      pos / _cellSize,
      perpendicular: math.max(.45, 6 / _cellSize),
    );
    if (hit == null) return;
    if (!inDrag || !_dragChangedLines) _saveSnapshot();
    final (ax, ay, bx, by) = hit;
    final changed = _doc.eraseUnitSegment(ax, ay, bx, by);
    if (changed) {
      setState(() {
        _dragChangedLines = inDrag;
        _sel = SketchSelection();
      });
      if (!inDrag) _triggerPreviewDebounced();
    }
  }

  void _eraseLineAt(Offset pos) {
    final threshold = math.max(16.0, _cellSize * 0.8);
    int? bestIdx;
    double bestDist = double.infinity;

    for (int i = 0; i < _doc.lines.length; i++) {
      final line = _doc.lines[i];
      final p1 = Offset(line.x1 * _cellSize, line.y1 * _cellSize);
      final p2 = Offset(line.x2 * _cellSize, line.y2 * _cellSize);
      final dist = distanceToSegment(pos, p1, p2);
      if (dist < threshold && dist < bestDist) {
        bestDist = dist;
        bestIdx = i;
      }
    }

    if (bestIdx != null) {
      _saveSnapshot();
      setState(() {
        _doc.lines.removeAt(bestIdx!);
        _sel = SketchSelection();
      });
      _triggerPreviewDebounced();
    }
  }

  double get _hitTolerance => math.max(16.0, _cellSize * 0.8) / _cellSize;

  /// 눌러 고르기: 사각형은 네 변을, 직선은 한 줄 전체를 한 모형으로 고른다.
  /// Shift를 누르고 있으면 더하고, 이미 고른 모형이면 뺀다.
  void _selectLineAt(Offset pos) {
    final hit = shapeSelect(_doc, pos / _cellSize, _hitTolerance);
    final shift = HardwareKeyboard.instance.isShiftPressed;
    final already =
        hit.isNotEmpty &&
        hit.lines.every(_sel.lines.contains) &&
        hit.texts.every(_sel.texts.contains);
    setState(() {
      _sel = !shift ? hit : (already ? _sel.toggled(hit) : _sel.union(hit));
      _syncStyleFromSelection();
    });
  }

  void _syncStyleFromSelection() {
    if (_sel.lines.length == 1) {
      final line = _doc.lines[_sel.lines.first];
      _lineWidth = line.width;
      _lineStyle = line.style;
    }
  }

  bool _hitsSelection(Offset grid) {
    final hit = hitSelect(_doc, grid, _hitTolerance);
    return hit.lines.any(_sel.lines.contains) ||
        hit.texts.any(_sel.texts.contains);
  }

  void _beginSelectionDrag(Offset pos) {
    final grid = pos / _cellSize;
    final shift = HardwareKeyboard.instance.isShiftPressed;
    _movingSelection = false;
    _lassoPath = null;
    if (!shift) {
      var onSelection = _sel.isNotEmpty && _hitsSelection(grid);
      if (!onSelection && _tool == SketchToolMode.lasso && _sel.isNotEmpty) {
        // 올가미로 고른 영역 안을 누르고 끌면 통째로 옮긴다(포토샵처럼).
        final bounds = selectionBounds(_doc, _sel);
        onSelection = bounds != null && bounds.inflate(.3).contains(grid);
      }
      if (!onSelection && _tool == SketchToolMode.select) {
        // 고르지 않은 개체를 바로 끌면 그 모형(사각형·직선)을 골라 옮긴다(파워포인트처럼).
        final hit = shapeSelect(_doc, grid, _hitTolerance);
        if (hit.isNotEmpty) {
          setState(() => _sel = hit);
          onSelection = true;
        }
      }
      if (onSelection) {
        _movingSelection = true;
        _moveOrigin = grid;
        _movedDx = 0;
        _movedDy = 0;
        _moveSnapshotTaken = false;
        return;
      }
    }
    setState(() => _lassoPath = [pos]);
  }

  void _updateSelectionDrag(Offset pos) {
    if (_movingSelection && _moveOrigin != null) {
      final grid = pos / _cellSize;
      final totalDx = (grid.dx - _moveOrigin!.dx).round();
      final totalDy = (grid.dy - _moveOrigin!.dy).round();
      final stepX = totalDx - _movedDx, stepY = totalDy - _movedDy;
      if (stepX == 0 && stepY == 0) return;
      if (!_moveSnapshotTaken) {
        _saveSnapshot();
        _moveSnapshotTaken = true;
      }
      setState(() {
        // 종이 밖·다른 글 칸에 막히면 가로·세로를 따로 시도한다.
        if (translateSelection(_doc, _sel, stepX, stepY)) {
          _movedDx += stepX;
          _movedDy += stepY;
        } else if (stepX != 0 && translateSelection(_doc, _sel, stepX, 0)) {
          _movedDx += stepX;
        } else if (stepY != 0 && translateSelection(_doc, _sel, 0, stepY)) {
          _movedDy += stepY;
        }
      });
      return;
    }
    final path = _lassoPath;
    if (path == null) return;
    setState(() {
      if (_tool == SketchToolMode.select) {
        _lassoPath = [path.first, pos];
      } else if ((path.last - pos).distance >= 3) {
        _lassoPath = [...path, pos];
      }
    });
  }

  void _endSelectionDrag() {
    if (_movingSelection) {
      _movingSelection = false;
      _moveOrigin = null;
      if (_movedDx != 0 || _movedDy != 0) _triggerPreviewDebounced();
      return;
    }
    final path = _lassoPath;
    setState(() => _lassoPath = null);
    if (path == null || path.length < 2) return;
    final bounds = path.fold<Rect>(
      Rect.fromPoints(path.first, path.first),
      (r, p) => r.expandToInclude(Rect.fromPoints(p, p)),
    );
    if (bounds.width < 6 && bounds.height < 6) return; // 누르기는 탭으로 처리
    final polygon = _tool == SketchToolMode.select
        ? [
            bounds.topLeft,
            bounds.topRight,
            bounds.bottomRight,
            bounds.bottomLeft,
          ]
        : path;
    final shift = HardwareKeyboard.instance.isShiftPressed;
    setState(() {
      final picked = lassoSelect(_doc, [
        for (final p in polygon) p / _cellSize,
      ], keep: shift ? _sel.lines : const {});
      _sel = shift
          ? SketchSelection(
              lines: picked.lines,
              texts: {..._sel.texts, ...picked.texts},
            )
          : picked;
      _syncStyleFromSelection();
    });
  }

  void _deleteSelectedLine() {
    final sel = _sel.validFor(_doc);
    if (sel.isEmpty) return;
    _saveSnapshot();
    setState(() {
      deleteSelection(_doc, sel);
      _sel = SketchSelection();
    });
    _triggerPreviewDebounced();
  }

  void _updateSelectedLineStyle({String? width, String? style}) {
    final targets = _sel.validFor(_doc).lines;
    if (targets.isEmpty) return;
    _saveSnapshot();
    setState(() {
      for (final i in targets) {
        final old = _doc.lines[i];
        _doc.lines[i] = old.copyWith(
          width: width ?? old.width,
          style: style ?? old.style,
        );
      }
    });
    _triggerPreviewDebounced();
  }

  void _selectAll() {
    setState(() {
      if (_tool != SketchToolMode.select && _tool != SketchToolMode.lasso) {
        _tool = SketchToolMode.select;
      }
      _sel = SketchSelection(
        lines: {for (var i = 0; i < _doc.lines.length; i++) i},
        texts: {for (var i = 0; i < _doc.texts.length; i++) i},
      );
    });
  }

  void _copySelection() {
    final sel = _sel.validFor(_doc);
    if (sel.isEmpty) return;
    setState(() {
      _clipboard = copySelection(_doc, sel);
      _pasteShift = 0;
    });
  }

  void _cutSelection() {
    _copySelection();
    _deleteSelectedLine();
  }

  void _pasteClipboard() {
    final clip = _clipboard;
    if (clip == null || clip.isEmpty) return;
    _pasteShift += 1;
    _saveSnapshot();
    setState(() {
      final pasted = pasteClip(_doc, clip, _pasteShift, _pasteShift);
      if (pasted != null) {
        _sel = pasted;
        if (_tool != SketchToolMode.lasso) _tool = SketchToolMode.select;
      }
    });
    _triggerPreviewDebounced();
  }

  void _duplicateSelection() {
    final sel = _sel.validFor(_doc);
    if (sel.isEmpty) return;
    final clip = copySelection(_doc, sel);
    _saveSnapshot();
    setState(() {
      final pasted = pasteClip(_doc, clip, 1, 1);
      if (pasted != null) _sel = pasted;
    });
    _triggerPreviewDebounced();
  }

  void _nudgeSelection(int dx, int dy) {
    final sel = _sel.validFor(_doc);
    if (sel.isEmpty) return;
    final trial = _doc.clone();
    if (!translateSelection(trial, sel, dx, dy)) return;
    _saveSnapshot();
    setState(() => translateSelection(_doc, sel, dx, dy));
    _triggerPreviewDebounced();
  }

  // --- 글 입력 대화상자 ---

  void _openTextDialogAt(Offset pos) {
    final cx = (pos.dx / _cellSize).floor().clamp(0, _doc.grid.cols - 1);
    final cy = (pos.dy / _cellSize).floor().clamp(0, _doc.grid.rows - 1);
    final existing = _doc.findText(cx, cy);

    showDialog<SketchText?>(
      context: context,
      builder: (ctx) => TableSketchTextDialog(
        x: cx,
        y: cy,
        initialText: existing?.text ?? '',
        initialBold: existing?.bold ?? false,
        initialAlign: existing?.align ?? 'center',
      ),
    ).then((result) {
      if (result != null && mounted) {
        _saveSnapshot();
        setState(() {
          _doc.setText(result);
        });
        _triggerPreviewDebounced();
      }
    });
  }

  // --- 확대 / 축소 제어 ---

  void _zoomIn() {
    setState(() {
      _zoom = (_zoom + 0.15).clamp(0.5, 3.0);
    });
  }

  void _zoomOut() {
    setState(() {
      _zoom = (_zoom - 0.15).clamp(0.5, 3.0);
    });
  }

  void _zoomReset() {
    setState(() {
      _zoom = 1.0;
    });
  }

  void _handlePointerSignal(PointerSignalEvent event) {
    if (event is PointerScrollEvent) {
      // Ctrl + 마우스 휠
      if (HardwareKeyboard.instance.isControlPressed) {
        if (event.scrollDelta.dy < 0) {
          _zoomIn();
        } else if (event.scrollDelta.dy > 0) {
          _zoomOut();
        }
      } else if (HardwareKeyboard.instance.isShiftPressed) {
        _scrollBy(_hScroll, event.scrollDelta.dy + event.scrollDelta.dx);
      } else {
        _scrollBy(_vScroll, event.scrollDelta.dy);
        _scrollBy(_hScroll, event.scrollDelta.dx);
      }
    }
  }

  // --- UI 구성 ---

  @override
  Widget build(BuildContext context) {
    return CallbackShortcuts(
      bindings: {
        const SingleActivator(LogicalKeyboardKey.delete): _deleteKey,
        const SingleActivator(LogicalKeyboardKey.backspace): _deleteKey,
        const SingleActivator(LogicalKeyboardKey.keyA, control: true):
            _selectAll,
        const SingleActivator(LogicalKeyboardKey.keyC, control: true):
            _copySelection,
        const SingleActivator(LogicalKeyboardKey.keyX, control: true):
            _cutSelection,
        const SingleActivator(LogicalKeyboardKey.keyV, control: true):
            _pasteKey,
        const SingleActivator(LogicalKeyboardKey.keyD, control: true):
            _duplicateSelection,
        const SingleActivator(LogicalKeyboardKey.arrowLeft): () =>
            _nudgeSelection(-1, 0),
        const SingleActivator(LogicalKeyboardKey.arrowRight): () =>
            _nudgeSelection(1, 0),
        const SingleActivator(LogicalKeyboardKey.arrowUp): () =>
            _nudgeSelection(0, -1),
        const SingleActivator(LogicalKeyboardKey.arrowDown): () =>
            _nudgeSelection(0, 1),
        const SingleActivator(LogicalKeyboardKey.escape): () {
          setState(() {
            _sel = SketchSelection();
            _tool = SketchToolMode.select;
          });
        },
        const SingleActivator(LogicalKeyboardKey.keyZ, control: true): _undo,
        const SingleActivator(LogicalKeyboardKey.keyY, control: true): _redo,
        const SingleActivator(
          LogicalKeyboardKey.keyZ,
          control: true,
          shift: true,
        ): _redo,
      },
      child: Focus(
        focusNode: _keyboardFocus,
        autofocus: true,
        child: Scaffold(
          key: const Key('tableSketchScreen'),
          backgroundColor: const Color(0xFFF8FAFC),
          appBar: AppBar(
            backgroundColor: Colors.white,
            surfaceTintColor: Colors.transparent,
            title: const Row(
              children: [
                Icon(Icons.border_all_outlined, color: Color(0xFF2563EB)),
                SizedBox(width: 8),
                Flexible(
                  child: Text(
                    '표그림판',
                    overflow: TextOverflow.ellipsis,
                    style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                  ),
                ),
              ],
            ),
            actions: [
              // 좁은 창(폭 600 미만)에서는 글 없는 아이콘 버튼으로 도구 줄이 넘치지 않게 한다.
              if (MediaQuery.sizeOf(context).width < 600)
                IconButton(
                  key: const Key('sketchOrgExample'),
                  tooltip: '조직도 예시',
                  icon: const Icon(Icons.account_tree_outlined),
                  onPressed: _loadOrgExample,
                )
              else
                OutlinedButton.icon(
                  key: const Key('sketchOrgExample'),
                  icon: const Icon(Icons.account_tree_outlined, size: 18),
                  label: const Text('조직도 예시'),
                  onPressed: _loadOrgExample,
                ),
              const SizedBox(width: 8),
              IconButton(
                key: const Key('undoButton'),
                tooltip: '실행 취소 (Ctrl+Z)',
                icon: const Icon(Icons.undo_rounded),
                onPressed: _undoStack.isNotEmpty ? _undo : null,
              ),
              IconButton(
                key: const Key('redoButton'),
                tooltip: '다시 실행 (Ctrl+Y)',
                icon: const Icon(Icons.redo_rounded),
                onPressed: _redoStack.isNotEmpty ? _redo : null,
              ),
              IconButton(
                key: const Key('clearAllButton'),
                tooltip: '전체 지우기',
                icon: const Icon(Icons.delete_sweep_outlined),
                onPressed: _clearAll,
              ),
              const SizedBox(width: 12),
            ],
          ),
          body: LayoutBuilder(
            builder: (context, constraints) {
              final isNarrow = constraints.maxWidth < 750;
              if (isNarrow) {
                // 좁은 화면 (폭 420 등) 세로 레이아웃
                return Column(
                  children: [
                    _buildTopToolbar(isNarrow: true),
                    _buildSelectionBar(),
                    Expanded(child: _buildCanvasArea()),
                    _buildBottomOrRightPanel(isNarrow: true),
                  ],
                );
              } else {
                // 넓은 화면 가로 레이아웃
                return Row(
                  children: [
                    Expanded(
                      child: Column(
                        children: [
                          _buildTopToolbar(isNarrow: false),
                          _buildSelectionBar(),
                          Expanded(child: _buildCanvasArea()),
                        ],
                      ),
                    ),
                    Container(
                      width: 320,
                      decoration: const BoxDecoration(
                        color: Colors.white,
                        border: Border(
                          left: BorderSide(color: Color(0xFFE2E8F0)),
                        ),
                      ),
                      child: _buildBottomOrRightPanel(isNarrow: false),
                    ),
                  ],
                );
              }
            },
          ),
        ),
      ),
    );
  }

  /// 상단 도구줄
  Widget _buildTopToolbar({required bool isNarrow}) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: const BoxDecoration(
        color: Colors.white,
        border: Border(bottom: BorderSide(color: Color(0xFFE2E8F0))),
      ),
      // 창이 좁으면 가로 스크롤 대신 다음 줄로 내려 모든 도구가 보이게 한다(2026-10-30 사용자 보고).
      child: Wrap(
        key: const Key('sketchToolbarWrap'),
        spacing: 4,
        runSpacing: 4,
        crossAxisAlignment: WrapCrossAlignment.center,
        children: [
          // 도구 선택기
          _toolButton(
            key: const Key('toolLine'),
            mode: SketchToolMode.line,
            icon: Icons.horizontal_rule_rounded,
            label: '직선',
            tooltip: '직선 그리기',
          ),
          _toolButton(
            key: const Key('toolRect'),
            mode: SketchToolMode.rect,
            icon: Icons.crop_square_rounded,
            label: '사각형',
            tooltip: '사각형 그리기 (4변 선)',
          ),
          _toolButton(
            key: const Key('toolEraser'),
            mode: SketchToolMode.eraser,
            icon: Icons.auto_fix_normal_outlined,
            label: '지우개',
            tooltip: '지우개',
          ),
          _toolButton(
            key: const Key('toolPreciseEraser'),
            mode: SketchToolMode.preciseEraser,
            icon: Icons.content_cut_rounded,
            label: '정밀 지우개',
            tooltip: '정밀 지우개 (셀 한 칸 단위)',
          ),
          _toolButton(
            key: const Key('toolText'),
            mode: SketchToolMode.text,
            icon: Icons.title_rounded,
            label: '글',
            tooltip: '칸 글 입력',
          ),
          _toolButton(
            key: const Key('toolSelect'),
            mode: SketchToolMode.select,
            icon: Icons.near_me_rounded,
            label: '선택',
            tooltip: '선택 (Shift+클릭·끌어 상자로 여러 개, 끌어 옮기기)',
          ),
          _toolButton(
            key: const Key('toolLasso'),
            mode: SketchToolMode.lasso,
            icon: Icons.gesture_rounded,
            label: '올가미',
            tooltip: '올가미 선택 (자유롭게 둘러 고르기, Shift로 더하기)',
          ),
          _toolButton(
            key: const Key('toolCellImage'),
            mode: SketchToolMode.cellImage,
            icon: Icons.image_outlined,
            label: '칸 그림',
            tooltip: '칸 배경 그림 (칸을 누르고 Ctrl+V, 또는 사진을 칸에 끌어 놓기)',
          ),
          // 묶음(굵기·종류·확대)은 한 덩어리로 줄을 바꾼다.
          _toolGroup([
            const Text(
              '굵기:',
              style: TextStyle(fontSize: 12, color: Color(0xFF64748B)),
            ),
            const SizedBox(width: 4),
            _widthChip('thin', '얇게', const Key('lineWidthThin')),
            _widthChip('thick', '굵게', const Key('lineWidthThick')),
            _widthChip('double', '이중', const Key('lineWidthDouble')),
          ]),
          _toolGroup([
            const Text(
              '종류:',
              style: TextStyle(fontSize: 12, color: Color(0xFF64748B)),
            ),
            const SizedBox(width: 4),
            _styleChip('solid', '실선', const Key('lineStyleSolid')),
            _styleChip('dash', '파선', const Key('lineStyleDash')),
            _styleChip('dot', '점선', const Key('lineStyleDot')),
          ]),
          _toolGroup([
            IconButton(
              tooltip: '축소',
              icon: const Icon(Icons.remove, size: 18),
              onPressed: _zoomOut,
              padding: EdgeInsets.zero,
              constraints: const BoxConstraints(minWidth: 28, minHeight: 28),
            ),
            Text(
              '${(_zoom * 100).round()}%',
              style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold),
            ),
            IconButton(
              tooltip: '확대',
              icon: const Icon(Icons.add, size: 18),
              onPressed: _zoomIn,
              padding: EdgeInsets.zero,
              constraints: const BoxConstraints(minWidth: 28, minHeight: 28),
            ),
            IconButton(
              tooltip: '100% 맞춤',
              icon: const Icon(Icons.refresh, size: 18),
              onPressed: _zoomReset,
              padding: EdgeInsets.zero,
              constraints: const BoxConstraints(minWidth: 28, minHeight: 28),
            ),
          ]),
        ],
      ),
    );
  }

  /// 도구 줄의 한 묶음: 왼쪽 구분선과 함께 한 줄로 붙어 다닌다.
  Widget _toolGroup(List<Widget> children) => Row(
    mainAxisSize: MainAxisSize.min,
    children: [
      const SizedBox(width: 4),
      Container(width: 1, height: 24, color: const Color(0xFFCBD5E1)),
      const SizedBox(width: 8),
      ...children,
    ],
  );

  // --- 칸 배경 그림 ---

  String _imageKey(String data) => '${data.length}:${data.hashCode}';

  List<(Rect, ui.Image)> _cellImagesToPaint() {
    final out = <(Rect, ui.Image)>[];
    for (final image in _doc.images) {
      final region = cellRegion(_doc, image.x, image.y);
      if (region == null) continue;
      final key = _imageKey(image.data);
      final decoded = _decoded[key];
      if (decoded != null) {
        out.add((region, decoded));
      } else if (_decoding.add(key)) {
        unawaited(_decode(key, image.data));
      }
    }
    return out;
  }

  Future<void> _decode(String key, String data) async {
    try {
      final raw = data.startsWith('data:') ? data.split(',').last : data;
      final codec = await ui.instantiateImageCodec(base64Decode(raw));
      final frame = await codec.getNextFrame();
      if (!mounted) {
        frame.image.dispose();
        return;
      }
      setState(() => _decoded[key] = frame.image);
    } catch (_) {
      // 풀 수 없는 그림은 칸에 그리지 않는다(표 변환 쪽에서 제외 안내).
    }
  }

  Rect? _imageTargetRegion() {
    final target = _imageTarget;
    return target == null ? null : cellRegion(_doc, target.$1, target.$2);
  }

  void _notice(String message) {
    if (!mounted) return;
    ScaffoldMessenger.of(context)
      ..hideCurrentSnackBar()
      ..showSnackBar(SnackBar(content: Text(message)));
  }

  void _pickImageCell(Offset pos) {
    final x = (pos.dx / _cellSize).floor(), y = (pos.dy / _cellSize).floor();
    if (cellRegion(_doc, x, y) == null) {
      setState(() => _imageTarget = null);
      _notice('선으로 둘러싸인 표 칸을 눌러 주세요.');
      return;
    }
    setState(() => _imageTarget = (x, y));
  }

  /// 그림을 칸에 넣는다(되돌리기 가능). 표 칸이 아니면 안내.
  bool _applyCellImage(int x, int y, String data) {
    if (cellRegion(_doc, x, y) == null) {
      _notice('사진은 선으로 둘러싸인 표 칸 안에 놓아 주세요.');
      return false;
    }
    _saveSnapshot();
    setState(() {
      setCellImage(_doc, x, y, data);
      _imageTarget = (x, y);
    });
    _triggerPreviewDebounced();
    return true;
  }

  /// 창에 끌어 놓은 사진을 가져와 놓은 자리의 칸에 넣는다.
  Future<void> takeDroppedImage() async {
    final result = await widget.api('table_sketch', ['take_drop']);
    if (!mounted || result is! Map || result['data'] is! String) return;
    final box = _canvasKey.currentContext?.findRenderObject() as RenderBox?;
    final cx = result['client_x'], cy = result['client_y'];
    if (box == null || cx is! num || cy is! num) {
      final target = _imageTarget;
      if (target != null) {
        _applyCellImage(target.$1, target.$2, result['data'] as String);
      } else {
        _notice('사진을 표 칸 위에 놓아 주세요.');
      }
      return;
    }
    final local = box.globalToLocal(Offset(cx.toDouble(), cy.toDouble()));
    applyDroppedImageAt(local, result['data'] as String);
  }

  /// 캔버스 좌표에 놓인 사진을 그 칸에 넣는다(시험에서도 쓴다).
  bool applyDroppedImageAt(Offset local, String data) {
    final x = (local.dx / _cellSize).floor(),
        y = (local.dy / _cellSize).floor();
    if (_tool != SketchToolMode.cellImage) {
      setState(() => _tool = SketchToolMode.cellImage);
    }
    return _applyCellImage(x, y, data);
  }

  Future<void> _pasteClipboardImage() async {
    final target = _imageTarget;
    if (target == null) {
      _notice('그림을 넣을 표 칸을 먼저 눌러 주세요.');
      return;
    }
    final result = await widget.api('table_sketch', ['clipboard_image']);
    if (!mounted) return;
    if (result is Map && result['data'] is String) {
      _applyCellImage(target.$1, target.$2, result['data'] as String);
    } else {
      _notice(
        result is Map && result['message'] is String
            ? result['message'] as String
            : '클립보드 사진을 읽지 못했습니다.',
      );
    }
  }

  void _removeTargetImage() {
    final target = _imageTarget;
    if (target == null) return;
    final trial = _doc.clone();
    if (!removeCellImage(trial, target.$1, target.$2)) {
      _notice('이 칸에는 배경 그림이 없습니다.');
      return;
    }
    _saveSnapshot();
    setState(() => removeCellImage(_doc, target.$1, target.$2));
    _triggerPreviewDebounced();
  }

  void _deleteKey() {
    if (_tool == SketchToolMode.cellImage) {
      _removeTargetImage();
    } else {
      _deleteSelectedLine();
    }
  }

  void _pasteKey() {
    if (_tool == SketchToolMode.cellImage) {
      unawaited(_pasteClipboardImage());
    } else {
      _pasteClipboard();
    }
  }

  Widget _cellImageBar() => Row(
    children: [
      Text(
        _imageTarget == null ? '칸을 고르세요' : '고른 칸',
        style: const TextStyle(
          fontSize: 12,
          fontWeight: FontWeight.w700,
          color: Color(0xFF15803D),
        ),
      ),
      _selectionAction(
        Icons.content_paste_go_rounded,
        '클립보드 사진 넣기 (Ctrl+V)',
        () => unawaited(_pasteClipboardImage()),
        const Key('sketchPasteImage'),
      ),
      _selectionAction(
        Icons.hide_image_outlined,
        '칸 그림 지우기 (Delete)',
        _removeTargetImage,
        const Key('sketchRemoveImage'),
      ),
      const SizedBox(width: 12),
      _barHint('사진을 표 칸 위에 끌어 놓으면 바로 그 칸 배경으로 들어가요(칸 크기에 맞춤).'),
    ],
  );

  /// 선택 줄 안내 글: 창이 좁으면 버튼을 가리지 않고 글 끝을 줄인다(전체 글은 툴팁).
  Widget _barHint(String text) => Expanded(
    child: Tooltip(
      message: text,
      child: Text(
        text,
        maxLines: 1,
        overflow: TextOverflow.ellipsis,
        style: const TextStyle(fontSize: 11, color: Color(0xFF64748B)),
      ),
    ),
  );

  /// 고른 개체가 있거나 복사해 둔 것이 있을 때만 나타나는 줄(도구 모음이 길어 오른쪽 끝이 가려지지 않게).
  Widget _buildSelectionBar() {
    return Container(
      key: const Key('sketchSelectionBar'),
      // 선택 여부와 관계없이 같은 높이로 두어 캔버스가 밀리지 않게 한다.
      // 버튼은 왼쪽에 고정하고, 창이 좁으면 안내 글만 줄여 버튼이 가려지지 않게 한다.
      height: 38,
      padding: const EdgeInsets.symmetric(horizontal: 12),
      decoration: const BoxDecoration(
        color: Color(0xFFEFF6FF),
        border: Border(bottom: BorderSide(color: Color(0xFFBFDBFE))),
      ),
      child: _tool == SketchToolMode.cellImage
          ? _cellImageBar()
          : Row(
              children: [
                if (_sel.isNotEmpty) ...[
                  Text(
                    '${_sel.count}개 선택',
                    key: const Key('sketchSelectionCount'),
                    style: const TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.w700,
                      color: Color(0xFF1D4ED8),
                    ),
                  ),
                  _selectionAction(
                    Icons.copy_rounded,
                    '복사 (Ctrl+C)',
                    _copySelection,
                    const Key('sketchCopy'),
                  ),
                  _selectionAction(
                    Icons.control_point_duplicate_rounded,
                    '복제 (Ctrl+D)',
                    _duplicateSelection,
                    const Key('sketchDuplicate'),
                  ),
                  _selectionAction(
                    Icons.delete_outline_rounded,
                    '삭제 (Delete)',
                    _deleteSelectedLine,
                    const Key('sketchDeleteSelection'),
                  ),
                ],
                if (_clipboard != null)
                  _selectionAction(
                    Icons.content_paste_rounded,
                    '붙여넣기 (Ctrl+V)',
                    _pasteClipboard,
                    const Key('sketchPaste'),
                  ),
                const SizedBox(width: 12),
                _barHint(
                  _sel.isEmpty
                      ? (_clipboard == null
                            ? '선택·올가미로 여러 개를 고르면 함께 옮기기·복사·삭제할 수 있어요'
                            : 'Ctrl+V로 붙여넣기')
                      : '끌어서 옮기기 · 방향키로 한 칸 · Shift로 더 고르기',
                ),
              ],
            ),
    );
  }

  Widget _selectionAction(
    IconData icon,
    String tooltip,
    VoidCallback onPressed,
    Key key,
  ) => IconButton(
    key: key,
    tooltip: tooltip,
    icon: Icon(icon, size: 18),
    onPressed: onPressed,
    padding: EdgeInsets.zero,
    constraints: const BoxConstraints(minWidth: 30, minHeight: 30),
  );

  Widget _toolButton({
    required Key key,
    required SketchToolMode mode,
    required IconData icon,
    required String label,
    required String tooltip,
  }) {
    final isSelected = _tool == mode;
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 2),
      child: Tooltip(
        message: tooltip,
        child: InkWell(
          key: key,
          onTap: () {
            setState(() {
              _tool = mode;
              if (mode != SketchToolMode.select &&
                  mode != SketchToolMode.lasso) {
                _sel = SketchSelection();
              }
            });
          },
          borderRadius: BorderRadius.circular(8),
          child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 6),
            decoration: BoxDecoration(
              color: isSelected ? const Color(0xFFDBEAFE) : Colors.transparent,
              borderRadius: BorderRadius.circular(8),
              border: Border.all(
                color: isSelected
                    ? const Color(0xFF2563EB)
                    : Colors.transparent,
              ),
            ),
            // 아이콘만으로는 정밀 지우개·올가미를 알아보기 어려워 이름을 함께 보인다(2026-10-30).
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(
                  icon,
                  size: 20,
                  color: isSelected
                      ? const Color(0xFF1D4ED8)
                      : const Color(0xFF475569),
                ),
                const SizedBox(width: 4),
                Text(
                  label,
                  style: TextStyle(
                    fontSize: 12,
                    fontWeight: isSelected ? FontWeight.w700 : FontWeight.w500,
                    color: isSelected
                        ? const Color(0xFF1D4ED8)
                        : const Color(0xFF475569),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _widthChip(String width, String label, Key key) {
    final isSelected = _lineWidth == width;
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 2),
      child: ChoiceChip(
        key: key,
        label: Text(label, style: const TextStyle(fontSize: 12)),
        selected: isSelected,
        onSelected: (selected) {
          if (selected) {
            setState(() => _lineWidth = width);
            _updateSelectedLineStyle(width: width);
          }
        },
        padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 0),
        materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
      ),
    );
  }

  Widget _styleChip(String style, String label, Key key) {
    final isSelected = _lineStyle == style;
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 2),
      child: ChoiceChip(
        key: key,
        label: Text(label, style: const TextStyle(fontSize: 12)),
        selected: isSelected,
        onSelected: (selected) {
          if (selected) {
            setState(() => _lineStyle = style);
            _updateSelectedLineStyle(style: style);
          }
        },
        padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 0),
        materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
      ),
    );
  }

  /// 캔버스 작업 영역 (스크롤뷰 + 커스텀페인트)
  Widget _buildCanvasArea() {
    final canvasWidth = _doc.grid.cols * _cellSize;
    final canvasHeight = _doc.grid.rows * _cellSize;

    return Listener(
      onPointerSignal: _handlePointerSignal,
      child: Container(
        color: const Color(0xFFF1F5F9),
        child: Center(
          child: Scrollbar(
            controller: _vScroll,
            thumbVisibility: true,
            child: SingleChildScrollView(
              controller: _vScroll,
              physics: const NeverScrollableScrollPhysics(),
              scrollDirection: Axis.vertical,
              padding: const EdgeInsets.all(24),
              child: Scrollbar(
                controller: _hScroll,
                thumbVisibility: true,
                notificationPredicate: (n) => n.depth == 0,
                child: SingleChildScrollView(
                  controller: _hScroll,
                  physics: const NeverScrollableScrollPhysics(),
                  scrollDirection: Axis.horizontal,
                  child: Center(
                    child: Container(
                      width: canvasWidth,
                      height: canvasHeight,
                      decoration: BoxDecoration(
                        color: Colors.white,
                        boxShadow: const [
                          BoxShadow(
                            color: Color(0x1E0F172A),
                            blurRadius: 16,
                            offset: Offset(0, 4),
                          ),
                        ],
                        borderRadius: BorderRadius.circular(4),
                      ),
                      child: Listener(
                        key: _canvasKey,
                        // 누름·이동·뗌을 직접 받아 뗀 위치를 끝점으로 쓴다(한 번에 멀리 옮겨도 선이 그려지게).
                        behavior: HitTestBehavior.opaque,
                        onPointerDown: (e) {
                          _keyboardFocus.requestFocus();
                          _handlePanStart(
                            DragStartDetails(
                              globalPosition: e.position,
                              localPosition: e.localPosition,
                            ),
                          );
                        },
                        onPointerMove: (e) => _handlePanUpdate(
                          DragUpdateDetails(
                            globalPosition: e.position,
                            localPosition: e.localPosition,
                          ),
                        ),
                        onPointerUp: (e) {
                          _handlePanUpdate(
                            DragUpdateDetails(
                              globalPosition: e.position,
                              localPosition: e.localPosition,
                            ),
                          );
                          _handlePanEnd(DragEndDetails());
                        },
                        child: GestureDetector(
                          behavior: HitTestBehavior.opaque,
                          // 정밀 지우개 탭은 Listener의 Down/Up에서 이미 처리한다.
                          onTapUp: _tool == SketchToolMode.preciseEraser
                              ? null
                              : _handleTapUp,
                          child: CustomPaint(
                            key: const Key('sketchCanvas'),
                            size: Size(canvasWidth, canvasHeight),
                            painter: TableSketchPainter(
                              doc: _doc,
                              cellSize: _cellSize,
                              selectedLines: _sel.lines,
                              selectedTexts: _sel.texts,
                              lassoPath: _lassoPath,
                              marquee: _tool == SketchToolMode.select,
                              cellImages: _cellImagesToPaint(),
                              imageTarget: _tool == SketchToolMode.cellImage
                                  ? _imageTargetRegion()
                                  : null,
                              previewLine: _previewLine,
                              previewRect: _previewRect,
                            ),
                          ),
                        ),
                      ),
                    ),
                  ),
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }

  /// 미리보기 및 컨트롤 패널 (우측 또는 하단)
  Widget _buildBottomOrRightPanel({required bool isNarrow}) {
    return Container(
      constraints: isNarrow ? const BoxConstraints(maxHeight: 260) : null,
      padding: const EdgeInsets.all(16),
      child: SingleChildScrollView(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // 표 미리보기 요약 정보
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: const Color(0xFFF8FAFC),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: const Color(0xFFE2E8F0)),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      const Text(
                        '표 미리보기',
                        style: TextStyle(
                          fontSize: 14,
                          fontWeight: FontWeight.bold,
                          color: Color(0xFF1E293B),
                        ),
                      ),
                      if (_previewLoading)
                        const SizedBox(
                          width: 14,
                          height: 14,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  if (_previewResult != null && _previewResult!.ok) ...[
                    Text(
                      '크기: ${_previewResult!.rows}행 × ${_previewResult!.cols}열 (${_previewResult!.cells.length}칸)',
                      style: const TextStyle(
                        fontSize: 13,
                        color: Color(0xFF334155),
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      '용지 차지: ${_previewResult!.widthMm.toStringAsFixed(1)}mm × ${_previewResult!.heightMm.toStringAsFixed(1)}mm',
                      style: const TextStyle(
                        fontSize: 12,
                        color: Color(0xFF64748B),
                      ),
                    ),
                    if (_previewResult!.warnings.isNotEmpty) ...[
                      const SizedBox(height: 8),
                      Container(
                        padding: const EdgeInsets.all(8),
                        decoration: BoxDecoration(
                          color: const Color(0xFFFEF3C7),
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: _previewResult!.warnings
                              .map(
                                (w) => Text(
                                  '• $w',
                                  style: const TextStyle(
                                    fontSize: 11,
                                    color: Color(0xFF92400E),
                                  ),
                                ),
                              )
                              .toList(),
                        ),
                      ),
                    ],
                  ] else ...[
                    const Text(
                      '선을 그리면 한/글 표 형태가 자동으로 계산됩니다.',
                      style: TextStyle(fontSize: 12, color: Color(0xFF64748B)),
                    ),
                  ],
                ],
              ),
            ),
            const SizedBox(height: 12),

            // 복사 버튼
            FilledButton.icon(
              key: const Key('sketchCopyButton'),
              onPressed: _copying ? null : _copyToClipboard,
              icon: _copying
                  ? const SizedBox(
                      width: 18,
                      height: 18,
                      child: CircularProgressIndicator(
                        strokeWidth: 2,
                        color: Colors.white,
                      ),
                    )
                  : const Icon(Icons.copy_rounded, size: 18),
              label: const Text('한/글에 붙여넣기용 복사'),
              style: FilledButton.styleFrom(
                backgroundColor: const Color(0xFF2563EB),
                padding: const EdgeInsets.symmetric(vertical: 14),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
              ),
            ),
            const SizedBox(height: 16),

            // 저장 및 불러오기
            const Text(
              '표 서식 보관',
              style: TextStyle(
                fontSize: 13,
                fontWeight: FontWeight.bold,
                color: Color(0xFF475569),
              ),
            ),
            const SizedBox(height: 8),
            Row(
              children: [
                Expanded(
                  child: TextField(
                    key: const Key('sketchNameField'),
                    controller: _saveNameController,
                    decoration: const InputDecoration(
                      hintText: '서식 이름',
                      isDense: true,
                      contentPadding: EdgeInsets.symmetric(
                        horizontal: 10,
                        vertical: 10,
                      ),
                      border: OutlineInputBorder(),
                    ),
                    style: const TextStyle(fontSize: 13),
                  ),
                ),
                const SizedBox(width: 8),
                FilledButton.tonal(
                  key: const Key('sketchSaveButton'),
                  onPressed: _saveSketch,
                  style: FilledButton.styleFrom(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 12,
                      vertical: 12,
                    ),
                  ),
                  child: const Text('저장'),
                ),
              ],
            ),
            const SizedBox(height: 8),
            OutlinedButton.icon(
              key: const Key('sketchListButton'),
              onPressed: _openListDialog,
              icon: const Icon(Icons.folder_open_outlined, size: 18),
              label: const Text('보관된 서식 불러오기'),
              style: OutlinedButton.styleFrom(
                padding: const EdgeInsets.symmetric(vertical: 10),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

/// 글 입력 대화상자 (StatefulWidget으로 컨트롤러 소유).
class TableSketchTextDialog extends StatefulWidget {
  const TableSketchTextDialog({
    super.key,
    required this.x,
    required this.y,
    required this.initialText,
    required this.initialBold,
    required this.initialAlign,
  });

  final int x;
  final int y;
  final String initialText;
  final bool initialBold;
  final String initialAlign;

  @override
  State<TableSketchTextDialog> createState() => _TableSketchTextDialogState();
}

class _TableSketchTextDialogState extends State<TableSketchTextDialog> {
  late final TextEditingController _controller;
  late bool _bold;
  late String _align;

  @override
  void initState() {
    super.initState();
    _controller = TextEditingController(text: widget.initialText);
    _bold = widget.initialBold;
    _align = widget.initialAlign;
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: Text('칸 글 입력 (${widget.x}, ${widget.y})'),
      content: SizedBox(
        width: 320,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            TextField(
              key: const Key('sketchTextInput'),
              controller: _controller,
              autofocus: true,
              decoration: const InputDecoration(
                labelText: '입력할 내용',
                hintText: '예: 총괄팀, 제목',
                border: OutlineInputBorder(),
              ),
              onSubmitted: (_) => _confirm(),
            ),
            const SizedBox(height: 12),
            Row(
              children: [
                Checkbox(
                  key: const Key('sketchTextBold'),
                  value: _bold,
                  onChanged: (val) => setState(() => _bold = val ?? false),
                ),
                const Text('굵게 (Bold)'),
                const Spacer(),
                const Text('정렬: ', style: TextStyle(fontSize: 12)),
                DropdownButton<String>(
                  key: const Key('sketchTextAlign'),
                  value: _align,
                  isDense: true,
                  items: const [
                    DropdownMenuItem(value: 'center', child: Text('가운데')),
                    DropdownMenuItem(value: 'left', child: Text('왼쪽')),
                    DropdownMenuItem(value: 'right', child: Text('오른쪽')),
                  ],
                  onChanged: (val) {
                    if (val != null) setState(() => _align = val);
                  },
                ),
              ],
            ),
          ],
        ),
      ),
      actions: [
        TextButton(
          key: const Key('sketchTextCancel'),
          onPressed: () => Navigator.of(context).pop(),
          child: const Text('취소'),
        ),
        FilledButton(
          key: const Key('sketchTextConfirm'),
          onPressed: _confirm,
          child: const Text('확인'),
        ),
      ],
    );
  }

  void _confirm() {
    final result = SketchText(
      x: widget.x,
      y: widget.y,
      text: _controller.text,
      bold: _bold,
      align: _align,
    );
    Navigator.of(context).pop(result);
  }
}
