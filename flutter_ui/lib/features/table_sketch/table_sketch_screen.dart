import 'dart:async';
import 'dart:math' as math;

import 'package:flutter/gestures.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../core/api/abbreviation_api.dart' show ApiCall;
import 'table_sketch_api.dart';
import 'table_sketch_models.dart';
import 'table_sketch_painter.dart';

enum SketchToolMode { line, rect, eraser, preciseEraser, text, select, cellColor }

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
  double? _selectedLineWidthMm;
  String _activeColor = '#DBEAFE';

  // 문서 데이터
  late TableSketchDoc _doc;
  final List<TableSketchDoc> _undoStack = [];
  final List<TableSketchDoc> _redoStack = [];

  // 선택 및 드래그 제스처 상태
  Set<int> _selectedLineIndices = {};
  int? get _selectedLineIndex =>
      _selectedLineIndices.isEmpty ? null : _selectedLineIndices.first;
  SketchLine? _hoverSegment;
  bool _panDidErase = false;
  Rect? _marqueeRect;
  List<SketchLine> _clipboardLines = [];
  List<double>? _verticalGuides;
  List<double>? _horizontalGuides;
  int? _activeHandle; // 1 or 2
  bool _isMovingSelection = false;
  bool _isMarqueeSelecting = false;

  Offset? _dragStart;
  Offset? _dragCurrent;
  SketchLine? _previewLine;
  Rect? _previewRect;

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
    _requestPreview();
  }

  // 끌기는 언제나 그리기에 쓰고, 화면 이동은 휠·스크롤 막대로 한다.
  final ScrollController _vScroll = ScrollController();
  final ScrollController _hScroll = ScrollController();

  @override
  void dispose() {
    _previewDebounceTimer?.cancel();
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
      _selectedLineIndices.clear();
      _hoverSegment = null;
      _marqueeRect = null;
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
      _selectedLineIndices.clear();
      _hoverSegment = null;
      _marqueeRect = null;
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
          _selectedLineIndices.clear();
          _hoverSegment = null;
          _marqueeRect = null;
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
      _selectedLineIndices.clear();
      _hoverSegment = null;
      _marqueeRect = null;
      _previewLine = null;
      _previewRect = null;
    });
    _triggerPreviewDebounced();
  }

  // --- 저장 / 불러오기 / 삭제 ---

  Future<void> _saveSketch() async {
    final name = _saveNameController.text.trim();
    if (name.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('서식 이름을 입력해 주세요.')),
      );
      return;
    }
    try {
      final res = await _sketchApi.save(name, _doc.toJson());
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(res['message']?.toString() ?? '서식이 저장되었습니다.'),
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('저장 실패: $e')),
        );
      }
    }
  }

  Future<void> _openListDialog() async {
    List<String> items = [];
    try {
      items = await _sketchApi.list();
    } catch (_) {}

    if (!mounted) return;

    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('보관된 표 서식 목록'),
        content: SizedBox(
          width: 320,
          height: 300,
          child: items.isEmpty
              ? const Center(child: Text('저장된 서식이 없습니다.'))
              : ListView.builder(
            itemCount: items.length,
            itemBuilder: (context, idx) {
              final item = items[idx];
              return ListTile(
                title: Text(item),
                trailing: IconButton(
                  icon: const Icon(Icons.delete_outline, size: 20),
                  onPressed: () async {
                    try {
                      await _sketchApi.delete(item);
                      if (ctx.mounted) Navigator.of(ctx).pop();
                      _openListDialog();
                    } catch (_) {}
                  },
                ),
                onTap: () async {
                  TableSketchDoc? loaded;
                  try {
                    loaded = await _sketchApi.load(item);
                  } catch (_) {}
                  if (loaded != null && mounted) {
                    _saveSnapshot();
                    setState(() {
                      _doc = loaded!;
                      _saveNameController.text = item;
                      _selectedLineIndices.clear();
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

  void _handleHover(PointerHoverEvent e) {
    if (_tool == SketchToolMode.preciseEraser) {
      final pos = e.localPosition;
      final threshold = math.max(16.0, _cellSize * 0.8);
      SketchLine? bestSeg;
      double bestDist = double.infinity;
      for (final line in _doc.lines) {
        final p1 = Offset(line.x1 * _cellSize, line.y1 * _cellSize);
        final p2 = Offset(line.x2 * _cellSize, line.y2 * _cellSize);
        final dist = distanceToSegment(pos, p1, p2);
        if (dist < threshold && dist < bestDist) {
          final segIdx = findLineSegmentIndex(line, pos, _cellSize, maxDistance: threshold);
          if (segIdx != null) {
            bestDist = dist;
            bestSeg = getLineSegment(line, segIdx);
          }
        }
      }
      if (bestSeg != _hoverSegment) {
        setState(() => _hoverSegment = bestSeg);
      }
    } else {
      if (_hoverSegment != null) {
        setState(() => _hoverSegment = null);
      }
    }
  }

  void _handlePanStart(DragStartDetails details) {
    final pos = details.localPosition;
    setState(() {
      _dragStart = pos;
      _dragCurrent = pos;
      _panDidErase = false;
      _isMovingSelection = false;
      _isMarqueeSelecting = false;
      _activeHandle = null;
      _verticalGuides = null;
      _horizontalGuides = null;
    });

    if (_tool == SketchToolMode.eraser) {
      _eraseLineAt(pos);
    } else if (_tool == SketchToolMode.preciseEraser) {
      _eraseSegmentAt(pos, isPanStart: true);
    } else if (_tool == SketchToolMode.select) {
      // 1개 선이 선택된 경우 끝점 핸들 클릭 확인
      if (_selectedLineIndices.length == 1) {
        final line = _doc.lines[_selectedLineIndices.first];
        final p1 = Offset(line.x1 * _cellSize, line.y1 * _cellSize);
        final p2 = Offset(line.x2 * _cellSize, line.y2 * _cellSize);
        if ((pos - p1).distance <= 12.0) {
          _activeHandle = 1;
          _saveSnapshot();
          return;
        }
        if ((pos - p2).distance <= 12.0) {
          _activeHandle = 2;
          _saveSnapshot();
          return;
        }
      }

      // 이미 선택된 선을 클릭하여 이동 시작하는지 확인
      bool clickedOnSelected = false;
      for (final idx in _selectedLineIndices) {
        final line = _doc.lines[idx];
        final p1 = Offset(line.x1 * _cellSize, line.y1 * _cellSize);
        final p2 = Offset(line.x2 * _cellSize, line.y2 * _cellSize);
        if (distanceToSegment(pos, p1, p2) <= math.max(16.0, _cellSize * 0.8)) {
          clickedOnSelected = true;
          break;
        }
      }

      if (clickedOnSelected) {
        _isMovingSelection = true;
        _saveSnapshot();
      } else {
        final found = _findLineAt(pos);
        if (found != null) {
          _selectLineAt(
            pos,
            toggle: HardwareKeyboard.instance.isShiftPressed ||
                HardwareKeyboard.instance.isControlPressed,
          );
          _isMovingSelection = true;
          _saveSnapshot();
        } else {
          // 빈 영역 클릭 시 마퀴 선택 시작
          if (!HardwareKeyboard.instance.isShiftPressed &&
              !HardwareKeyboard.instance.isControlPressed) {
            _selectedLineIndices.clear();
          }
          _isMarqueeSelecting = true;
        }
      }
    }
  }

  void _handlePanUpdate(DragUpdateDetails details) {
    final pos = details.localPosition;
    setState(() => _dragCurrent = pos);

    if (_tool == SketchToolMode.line && _dragStart != null) {
      _updateLinePreview(_dragStart!, pos);
    } else if (_tool == SketchToolMode.rect && _dragStart != null) {
      _updateRectPreview(_dragStart!, pos);
    } else if (_tool == SketchToolMode.eraser) {
      _eraseLineAt(pos);
    } else if (_tool == SketchToolMode.preciseEraser) {
      _eraseSegmentAt(pos, isPanStart: false);
    } else if (_tool == SketchToolMode.select) {
      if (_activeHandle != null && _selectedLineIndices.length == 1) {
        _updateActiveHandle(pos);
      } else if (_isMovingSelection && _dragStart != null) {
        _updateMovingSelection(pos);
      } else if (_isMarqueeSelecting && _dragStart != null) {
        _updateMarqueeSelection(_dragStart!, pos);
      }
    }
  }

  void _handlePanEnd(DragEndDetails details) {
    if (_tool == SketchToolMode.line &&
        _dragStart != null &&
        _dragCurrent != null) {
      _commitLine(_dragStart!, _dragCurrent!);
    } else if (_tool == SketchToolMode.rect &&
        _dragStart != null &&
        _dragCurrent != null) {
      _commitRect(_dragStart!, _dragCurrent!);
    } else if (_tool == SketchToolMode.preciseEraser && _panDidErase) {
      _triggerPreviewDebounced();
    } else if (_tool == SketchToolMode.select) {
      if (_isMovingSelection || _activeHandle != null) {
        _triggerPreviewDebounced();
      }
    }

    setState(() {
      _dragStart = null;
      _dragCurrent = null;
      _previewLine = null;
      _previewRect = null;
      _marqueeRect = null;
      _activeHandle = null;
      _isMovingSelection = false;
      _isMarqueeSelecting = false;
      _verticalGuides = null;
      _horizontalGuides = null;
    });
  }

  void _handleTapUp(TapUpDetails details) {
    final pos = details.localPosition;
    if (_tool == SketchToolMode.text) {
      _openTextDialogAt(pos);
    } else if (_tool == SketchToolMode.select) {
      _selectLineAt(
        pos,
        toggle: HardwareKeyboard.instance.isShiftPressed ||
            HardwareKeyboard.instance.isControlPressed,
      );
    } else if (_tool == SketchToolMode.eraser) {
      _eraseLineAt(pos);
    } else if (_tool == SketchToolMode.preciseEraser) {
      _eraseSegmentAt(pos, isPanStart: true);
    } else if (_tool == SketchToolMode.cellColor) {
      _applyCellColorAt(pos);
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
          widthMm: _selectedLineWidthMm,
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
        widthMm: _selectedLineWidthMm,
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
        _doc.addLine(
          SketchLine(
            x1: minX,
            y1: minY,
            x2: maxX,
            y2: minY,
            width: _lineWidth,
            style: _lineStyle,
            widthMm: _selectedLineWidthMm,
          ),
        );
        _doc.addLine(
          SketchLine(
            x1: minX,
            y1: maxY,
            x2: maxX,
            y2: maxY,
            width: _lineWidth,
            style: _lineStyle,
            widthMm: _selectedLineWidthMm,
          ),
        );
        _doc.addLine(
          SketchLine(
            x1: minX,
            y1: minY,
            x2: minX,
            y2: maxY,
            width: _lineWidth,
            style: _lineStyle,
            widthMm: _selectedLineWidthMm,
          ),
        );
        _doc.addLine(
          SketchLine(
            x1: maxX,
            y1: minY,
            x2: maxX,
            y2: maxY,
            width: _lineWidth,
            style: _lineStyle,
            widthMm: _selectedLineWidthMm,
          ),
        );
      });
      _triggerPreviewDebounced();
    }
  }

  // --- 지우개 & 정밀 지우개 & 선택 로직 ---

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
        _selectedLineIndices.clear();
      });
      _triggerPreviewDebounced();
    }
  }

  void _eraseSegmentAt(Offset pos, {bool isPanStart = false}) {
    final threshold = math.max(16.0, _cellSize * 0.8);
    int? bestLineIdx;
    int? bestSegIdx;
    double bestDist = double.infinity;

    for (int i = 0; i < _doc.lines.length; i++) {
      final line = _doc.lines[i];
      final p1 = Offset(line.x1 * _cellSize, line.y1 * _cellSize);
      final p2 = Offset(line.x2 * _cellSize, line.y2 * _cellSize);
      final dist = distanceToSegment(pos, p1, p2);
      if (dist < threshold && dist < bestDist) {
        final seg = findLineSegmentIndex(line, pos, _cellSize, maxDistance: threshold);
        if (seg != null) {
          bestDist = dist;
          bestLineIdx = i;
          bestSegIdx = seg;
        }
      }
    }

    if (bestLineIdx != null && bestSegIdx != null) {
      if (isPanStart || !_panDidErase) {
        _saveSnapshot();
        _panDidErase = true;
      }
      setState(() {
        final line = _doc.lines[bestLineIdx!];
        final remaining = splitLineAt(line, bestSegIdx!);
        _doc.lines.removeAt(bestLineIdx);
        _doc.lines.insertAll(bestLineIdx, remaining);
        _selectedLineIndices.clear();
        _hoverSegment = null;
      });
      _triggerPreviewDebounced();
    }
  }

  int? _findLineAt(Offset pos) {
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
    return bestIdx;
  }

  void _selectLineAt(Offset pos, {bool toggle = false}) {
    final bestIdx = _findLineAt(pos);

    setState(() {
      if (bestIdx == null) {
        if (!toggle) {
          _selectedLineIndices.clear();
        }
      } else {
        final clicked = _doc.lines[bestIdx];
        final targetIndices = <int>{bestIdx};
        if (clicked.groupId != null && clicked.groupId!.isNotEmpty) {
          for (int i = 0; i < _doc.lines.length; i++) {
            if (_doc.lines[i].groupId == clicked.groupId) {
              targetIndices.add(i);
            }
          }
        }

        if (toggle) {
          if (_selectedLineIndices.contains(bestIdx)) {
            _selectedLineIndices.removeAll(targetIndices);
          } else {
            _selectedLineIndices.addAll(targetIndices);
          }
        } else {
          _selectedLineIndices = targetIndices;
        }

        if (_selectedLineIndices.isNotEmpty) {
          final first = _doc.lines[_selectedLineIndices.first];
          _lineWidth = first.width;
          _lineStyle = first.style;
          _selectedLineWidthMm = first.widthMm;
        }
      }
    });
  }

  void _deleteSelectedLines() {
    if (_selectedLineIndices.isEmpty) return;
    _saveSnapshot();
    setState(() {
      final toRemove = _selectedLineIndices.toList()
        ..sort((a, b) => b.compareTo(a));
      for (final idx in toRemove) {
        if (idx >= 0 && idx < _doc.lines.length) {
          _doc.lines.removeAt(idx);
        }
      }
      _selectedLineIndices.clear();
    });
    _triggerPreviewDebounced();
  }

  void _groupSelected() {
    if (_selectedLineIndices.length < 2) return;
    _saveSnapshot();
    final gid = 'g_${DateTime.now().millisecondsSinceEpoch}';
    setState(() {
      for (final idx in _selectedLineIndices) {
        _doc.lines[idx] = _doc.lines[idx].copyWith(groupId: gid);
      }
    });
  }

  void _ungroupSelected() {
    if (_selectedLineIndices.isEmpty) return;
    _saveSnapshot();
    setState(() {
      for (final idx in _selectedLineIndices) {
        _doc.lines[idx] = _doc.lines[idx].copyWith(groupId: '');
      }
    });
  }

  bool get _hasGroupSelected =>
      _selectedLineIndices.any((idx) => _doc.lines[idx].groupId?.isNotEmpty == true);

  void _selectAll() {
    setState(() {
      _selectedLineIndices = {for (int i = 0; i < _doc.lines.length; i++) i};
    });
  }

  void _copySelected() {
    if (_selectedLineIndices.isEmpty) return;
    _clipboardLines = _selectedLineIndices.map((i) => _doc.lines[i].copyWith()).toList();
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text('${_clipboardLines.length}개 선 복사됨')),
    );
  }

  Future<void> _importTable({bool fromFile = false}) async {
    String? path;
    if (fromFile) {
      final input = TextEditingController();
      path = await showDialog<String>(context: context, builder: (context) => AlertDialog(
        title: const Text('HWPX에서 표 가져오기'),
        content: TextField(controller: input, decoration: const InputDecoration(labelText: 'HWPX 파일 경로')),
        actions: [TextButton(onPressed: () => Navigator.pop(context), child: const Text('취소')),
          FilledButton(onPressed: () => Navigator.pop(context, input.text.trim()), child: const Text('가져오기'))],
      ));
      if (path == null || path.isEmpty) return;
    }
    if (!mounted) return;
    if (_doc.lines.isNotEmpty || _doc.texts.isNotEmpty) {
      final replace = await showDialog<bool>(context: context, builder: (context) => AlertDialog(
        title: const Text('새 그림으로 열기'), content: const Text('현재 그림을 가져온 표로 바꿀까요? 실행 취소로 복구할 수 있어요.'),
        actions: [TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('취소')),
          FilledButton(onPressed: () => Navigator.pop(context, true), child: const Text('새 그림으로 열기'))],
      ));
      if (replace != true) return;
    }
    try {
      final result = await widget.api('table_sketch', ['import', {
        'source_type': fromFile ? 'hwpx' : 'clipboard', 'data': path,
      }]);
      if (!mounted) return;
      if (result is! Map || result['ok'] != true) {
        throw Exception(result is Map ? result['message'] : '표를 읽지 못했습니다.');
      }
      _saveSnapshot();
      setState(() { _doc = TableSketchDoc.fromJson(result); _selectedLineIndices.clear(); });
      _triggerPreviewDebounced();
      final warnings = result['warnings'];
      if (warnings is List && warnings.isNotEmpty) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(warnings.join('\n'))));
      }
    } catch (error) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('표 가져오기 실패: $error')));
    }
  }

  void _paste() {
    if (_clipboardLines.isEmpty) { _importTable(); return; }
    _saveSnapshot();
    setState(() {
      final newIndices = <int>{};
      for (final l in _clipboardLines) {
        final pasted = l.copyWith(
          x1: (l.x1 + 1).clamp(0, _doc.grid.cols),
          y1: (l.y1 + 1).clamp(0, _doc.grid.rows),
          x2: (l.x2 + 1).clamp(0, _doc.grid.cols),
          y2: (l.y2 + 1).clamp(0, _doc.grid.rows),
        );
        newIndices.add(_doc.lines.length);
        _doc.addLine(pasted);
      }
      _selectedLineIndices = newIndices;
    });
    _triggerPreviewDebounced();
  }

  void _moveSelected(int dx, int dy) {
    if (_selectedLineIndices.isEmpty) return;
    _saveSnapshot();
    setState(() {
      for (final idx in _selectedLineIndices) {
        final l = _doc.lines[idx];
        _doc.lines[idx] = l.copyWith(
          x1: (l.x1 + dx).clamp(0, _doc.grid.cols),
          y1: (l.y1 + dy).clamp(0, _doc.grid.rows),
          x2: (l.x2 + dx).clamp(0, _doc.grid.cols),
          y2: (l.y2 + dy).clamp(0, _doc.grid.rows),
        );
      }
    });
    _triggerPreviewDebounced();
  }

  void _updateActiveHandle(Offset pos) {
    final idx = _selectedLineIndices.first;
    final line = _doc.lines[idx];
    final rawGx = (pos.dx / _cellSize).round().clamp(0, _doc.grid.cols);
    final rawGy = (pos.dy / _cellSize).round().clamp(0, _doc.grid.rows);

    final vGuides = <double>[];
    final hGuides = <double>[];

    for (int i = 0; i < _doc.lines.length; i++) {
      if (i == idx) continue;
      final ol = _doc.lines[i];
      if (ol.x1 == rawGx || ol.x2 == rawGx) vGuides.add(rawGx * _cellSize);
      if (ol.y1 == rawGy || ol.y2 == rawGy) hGuides.add(rawGy * _cellSize);
    }

    SketchLine updated;
    if (_activeHandle == 1) {
      final snapped = snapLineCoords(
        line.x2,
        line.y2,
        rawGx,
        rawGy,
        _doc.grid.cols,
        _doc.grid.rows,
      );
      updated = snapped != null ? line.copyWith(x1: snapped.x, y1: snapped.y) : line;
    } else {
      final snapped = snapLineCoords(
        line.x1,
        line.y1,
        rawGx,
        rawGy,
        _doc.grid.cols,
        _doc.grid.rows,
      );
      updated = snapped != null ? line.copyWith(x2: snapped.x, y2: snapped.y) : line;
    }

    setState(() {
      _doc.lines[idx] = updated;
      _verticalGuides = vGuides.isEmpty ? null : vGuides.toSet().toList();
      _horizontalGuides = hGuides.isEmpty ? null : hGuides.toSet().toList();
    });
  }

  void _updateMovingSelection(Offset current) {
    final deltaGx = ((current.dx - _dragStart!.dx) / _cellSize).round();
    final deltaGy = ((current.dy - _dragStart!.dy) / _cellSize).round();
    if (deltaGx == 0 && deltaGy == 0) return;

    for (final idx in _selectedLineIndices) {
      final l = _doc.lines[idx];
      if (l.x1 + deltaGx < 0 ||
          l.x1 + deltaGx > _doc.grid.cols ||
          l.x2 + deltaGx < 0 ||
          l.x2 + deltaGx > _doc.grid.cols ||
          l.y1 + deltaGy < 0 ||
          l.y1 + deltaGy > _doc.grid.rows ||
          l.y2 + deltaGy < 0 ||
          l.y2 + deltaGy > _doc.grid.rows) {
        return;
      }
    }

    _dragStart = Offset(
      _dragStart!.dx + deltaGx * _cellSize,
      _dragStart!.dy + deltaGy * _cellSize,
    );

    final vGuides = <double>[];
    final hGuides = <double>[];

    setState(() {
      for (final idx in _selectedLineIndices) {
        final l = _doc.lines[idx];
        _doc.lines[idx] = l.copyWith(
          x1: l.x1 + deltaGx,
          y1: l.y1 + deltaGy,
          x2: l.x2 + deltaGx,
          y2: l.y2 + deltaGy,
        );
      }

      for (final idx in _selectedLineIndices) {
        final l = _doc.lines[idx];
        for (int i = 0; i < _doc.lines.length; i++) {
          if (_selectedLineIndices.contains(i)) continue;
          final ol = _doc.lines[i];
          if (l.x1 == ol.x1 || l.x1 == ol.x2) vGuides.add(l.x1 * _cellSize);
          if (l.x2 == ol.x1 || l.x2 == ol.x2) vGuides.add(l.x2 * _cellSize);
          if (l.y1 == ol.y1 || l.y1 == ol.y2) hGuides.add(l.y1 * _cellSize);
          if (l.y2 == ol.y1 || l.y2 == ol.y2) hGuides.add(l.y2 * _cellSize);
        }
      }
      _verticalGuides = vGuides.isEmpty ? null : vGuides.toSet().toList();
      _horizontalGuides = hGuides.isEmpty ? null : hGuides.toSet().toList();
    });
  }

  void _updateMarqueeSelection(Offset start, Offset current) {
    final rect = Rect.fromPoints(start, current);
    final matched = <int>{};

    for (int i = 0; i < _doc.lines.length; i++) {
      final line = _doc.lines[i];
      final minX = math.min(line.x1, line.x2) * _cellSize;
      final maxX = math.max(line.x1, line.x2) * _cellSize;
      final minY = math.min(line.y1, line.y2) * _cellSize;
      final maxY = math.max(line.y1, line.y2) * _cellSize;
      final lineBox = Rect.fromLTRB(minX, minY, maxX, maxY);
      if (rect.overlaps(lineBox) ||
          rect.contains(Offset(minX, minY)) ||
          rect.contains(Offset(maxX, maxY))) {
        matched.add(i);
      }
    }

    setState(() {
      _marqueeRect = rect;
      _selectedLineIndices = matched;
    });
  }

  void _applyCellColorAt(Offset pos) {
    final cx = (pos.dx / _cellSize).floor().clamp(0, _doc.grid.cols - 1);
    final cy = (pos.dy / _cellSize).floor().clamp(0, _doc.grid.rows - 1);
    _saveSnapshot();
    setState(() {
      _doc.setCellColor(cx, cy, _activeColor);
    });
    _triggerPreviewDebounced();
  }

  void _updateSelectedLineStyle({String? width, String? style}) {
    if (_selectedLineIndices.isEmpty) return;
    _saveSnapshot();
    setState(() {
      for (final idx in _selectedLineIndices) {
        final old = _doc.lines[idx];
        _doc.lines[idx] = old.copyWith(
          width: width ?? old.width,
          style: style ?? old.style,
        );
      }
    });
    _triggerPreviewDebounced();
  }

  void _updateSelectedLineWidthMm(double? widthMm) {
    if (_selectedLineIndices.isEmpty) return;
    _saveSnapshot();
    setState(() {
      for (final idx in _selectedLineIndices) {
        _doc.lines[idx] = _doc.lines[idx].copyWith(widthMm: widthMm);
      }
    });
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
        const SingleActivator(LogicalKeyboardKey.delete): _deleteSelectedLines,
        const SingleActivator(LogicalKeyboardKey.escape): () {
          setState(() {
            _selectedLineIndices.clear();
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
        const SingleActivator(LogicalKeyboardKey.keyC, control: true): _copySelected,
        const SingleActivator(LogicalKeyboardKey.keyV, control: true): _paste,
        const SingleActivator(LogicalKeyboardKey.keyA, control: true): _selectAll,
        const SingleActivator(LogicalKeyboardKey.keyG, control: true): _groupSelected,
        const SingleActivator(
          LogicalKeyboardKey.keyG,
          control: true,
          shift: true,
        ): _ungroupSelected,
        const SingleActivator(LogicalKeyboardKey.arrowUp): () => _moveSelected(0, -1),
        const SingleActivator(LogicalKeyboardKey.arrowDown): () => _moveSelected(0, 1),
        const SingleActivator(LogicalKeyboardKey.arrowLeft): () => _moveSelected(-1, 0),
        const SingleActivator(LogicalKeyboardKey.arrowRight): () => _moveSelected(1, 0),
        const SingleActivator(LogicalKeyboardKey.keyE, shift: true): () {
          setState(() => _tool = SketchToolMode.preciseEraser);
        },
      },
      child: Focus(
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
              IconButton(key: const Key('pasteTableButton'), tooltip: '한/글 표 붙여넣기 (Ctrl+V)',
                icon: const Icon(Icons.content_paste), onPressed: () => _importTable()),
              IconButton(key: const Key('importHwpxButton'), tooltip: 'HWPX에서 표 가져오기',
                icon: const Icon(Icons.file_open_outlined), onPressed: () => _importTable(fromFile: true)),
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
                return Column(
                  children: [
                    _buildTopToolbar(isNarrow: true),
                    Expanded(child: _buildCanvasArea()),
                    _buildBottomOrRightPanel(isNarrow: true),
                  ],
                );
              } else {
                return Row(
                  children: [
                    Expanded(
                      child: Column(
                        children: [
                          _buildTopToolbar(isNarrow: false),
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
      child: SingleChildScrollView(
        scrollDirection: Axis.horizontal,
        child: Row(
          children: [
            // 도구 선택기
            _toolButton(
              key: const Key('toolLine'),
              mode: SketchToolMode.line,
              icon: Icons.horizontal_rule_rounded,
              tooltip: '직선 그리기',
            ),
            _toolButton(
              key: const Key('toolRect'),
              mode: SketchToolMode.rect,
              icon: Icons.crop_square_rounded,
              tooltip: '사각형 그리기 (4변 선)',
            ),
            _toolButton(
              key: const Key('toolEraser'),
              mode: SketchToolMode.eraser,
              icon: Icons.auto_fix_normal_outlined,
              tooltip: '지우개',
            ),
            _toolButton(
              key: const Key('toolPreciseEraser'),
              mode: SketchToolMode.preciseEraser,
              icon: Icons.cleaning_services_outlined,
              tooltip: '정밀 지우개 (셀 한 칸 단위)',
            ),
            _toolButton(
              key: const Key('toolText'),
              mode: SketchToolMode.text,
              icon: Icons.title_rounded,
              tooltip: '칸 글 입력',
            ),
            _toolButton(
              key: const Key('toolSelect'),
              mode: SketchToolMode.select,
              icon: Icons.near_me_rounded,
              tooltip: '선택 및 속성 변경',
            ),
            _toolButton(
              key: const Key('toolCellColor'),
              mode: SketchToolMode.cellColor,
              icon: Icons.format_color_fill_rounded,
              tooltip: '셀 배경색 채우기',
            ),
            const SizedBox(width: 8),
            Container(width: 1, height: 24, color: const Color(0xFFCBD5E1)),
            const SizedBox(width: 8),

            // 묶음(그룹) 도구
            IconButton(
              key: const Key('btnGroupLines'),
              tooltip: '묶음 지정 (Ctrl+G)',
              icon: const Icon(Icons.group_work_outlined, size: 20),
              onPressed: _selectedLineIndices.length >= 2 ? _groupSelected : null,
              padding: EdgeInsets.zero,
              constraints: const BoxConstraints(minWidth: 32, minHeight: 32),
            ),
            IconButton(
              key: const Key('btnUngroupLines'),
              tooltip: '묶음 해제 (Ctrl+Shift+G)',
              icon: const Icon(Icons.workspaces_outlined, size: 20),
              onPressed: _hasGroupSelected ? _ungroupSelected : null,
              padding: EdgeInsets.zero,
              constraints: const BoxConstraints(minWidth: 32, minHeight: 32),
            ),

            const SizedBox(width: 8),
            Container(width: 1, height: 24, color: const Color(0xFFCBD5E1)),
            const SizedBox(width: 8),

            // 선 굵기 mm 드롭다운
            const Text(
              '굵기:',
              style: TextStyle(fontSize: 12, color: Color(0xFF64748B)),
            ),
            const SizedBox(width: 4),
            DropdownButton<double?>(
              key: const Key('lineWidthMmDropdown'),
              value: _selectedLineWidthMm,
              hint: const Text('기본', style: TextStyle(fontSize: 12)),
              isDense: true,
              items: const [
                DropdownMenuItem(value: null, child: Text('기본', style: TextStyle(fontSize: 12))),
                DropdownMenuItem(value: 0.1, child: Text('0.1mm', style: TextStyle(fontSize: 12))),
                DropdownMenuItem(value: 0.12, child: Text('0.12mm', style: TextStyle(fontSize: 12))),
                DropdownMenuItem(value: 0.15, child: Text('0.15mm', style: TextStyle(fontSize: 12))),
                DropdownMenuItem(value: 0.2, child: Text('0.2mm', style: TextStyle(fontSize: 12))),
                DropdownMenuItem(value: 0.25, child: Text('0.25mm', style: TextStyle(fontSize: 12))),
                DropdownMenuItem(value: 0.3, child: Text('0.3mm', style: TextStyle(fontSize: 12))),
                DropdownMenuItem(value: 0.4, child: Text('0.4mm', style: TextStyle(fontSize: 12))),
                DropdownMenuItem(value: 0.5, child: Text('0.5mm', style: TextStyle(fontSize: 12))),
                DropdownMenuItem(value: 0.6, child: Text('0.6mm', style: TextStyle(fontSize: 12))),
                DropdownMenuItem(value: 0.7, child: Text('0.7mm', style: TextStyle(fontSize: 12))),
                DropdownMenuItem(value: 1.0, child: Text('1.0mm', style: TextStyle(fontSize: 12))),
                DropdownMenuItem(value: 1.5, child: Text('1.5mm', style: TextStyle(fontSize: 12))),
                DropdownMenuItem(value: 2.0, child: Text('2.0mm', style: TextStyle(fontSize: 12))),
                DropdownMenuItem(value: 3.0, child: Text('3.0mm', style: TextStyle(fontSize: 12))),
                DropdownMenuItem(value: 4.0, child: Text('4.0mm', style: TextStyle(fontSize: 12))),
                DropdownMenuItem(value: 5.0, child: Text('5.0mm', style: TextStyle(fontSize: 12))),
              ],
              onChanged: (val) {
                setState(() => _selectedLineWidthMm = val);
                _updateSelectedLineWidthMm(val);
              },
            ),
            const SizedBox(width: 4),
            _widthChip('thin', '얇게', const Key('lineWidthThin')),
            _widthChip('thick', '굵게', const Key('lineWidthThick')),
            _widthChip('double', '이중', const Key('lineWidthDouble')),

            const SizedBox(width: 8),
            Container(width: 1, height: 24, color: const Color(0xFFCBD5E1)),
            const SizedBox(width: 8),

            // 선 종류
            const Text(
              '종류:',
              style: TextStyle(fontSize: 12, color: Color(0xFF64748B)),
            ),
            const SizedBox(width: 4),
            _styleChip('solid', '실선', const Key('lineStyleSolid')),
            _styleChip('dash', '파선', const Key('lineStyleDash')),
            _styleChip('dot', '점선', const Key('lineStyleDot')),

            const SizedBox(width: 8),
            Container(width: 1, height: 24, color: const Color(0xFFCBD5E1)),
            const SizedBox(width: 8),

            // 셀 배경색 팔레트
            const Text(
              '배경색:',
              style: TextStyle(fontSize: 12, color: Color(0xFF64748B)),
            ),
            const SizedBox(width: 4),
            for (final (colorHex, colorName) in const [
              ('#FFFFFF', '흰색'),
              ('#F1F5F9', '연회색'),
              ('#DBEAFE', '연파랑'),
              ('#FEF08A', '연노랑'),
              ('#DCFCE7', '연초록'),
              ('#FFEDD5', '연주황'),
            ])
              _colorChip(colorHex, colorName),

            const SizedBox(width: 8),
            Container(width: 1, height: 24, color: const Color(0xFFCBD5E1)),
            const SizedBox(width: 8),

            // 확대/축소 버튼
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
          ],
        ),
      ),
    );
  }

  Widget _toolButton({
    required Key key,
    required SketchToolMode mode,
    required IconData icon,
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
              if (mode != SketchToolMode.select) {
                _selectedLineIndices.clear();
              }
            });
          },
          borderRadius: BorderRadius.circular(8),
          child: Container(
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(
              color: isSelected ? const Color(0xFFDBEAFE) : Colors.transparent,
              borderRadius: BorderRadius.circular(8),
              border: Border.all(
                color: isSelected
                    ? const Color(0xFF2563EB)
                    : Colors.transparent,
              ),
            ),
            child: Icon(
              icon,
              size: 20,
              color: isSelected
                  ? const Color(0xFF1D4ED8)
                  : const Color(0xFF475569),
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

  Widget _colorChip(String hex, String label) {
    final isSelected = _activeColor == hex && _tool == SketchToolMode.cellColor;
    final color = parseHexColor(hex) ?? Colors.white;
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 2),
      child: Tooltip(
        message: label,
        child: InkWell(
          key: Key('colorChip_$hex'),
          onTap: () {
            setState(() {
              _activeColor = hex;
              _tool = SketchToolMode.cellColor;
            });
          },
          borderRadius: BorderRadius.circular(12),
          child: Container(
            width: 22,
            height: 22,
            decoration: BoxDecoration(
              color: color,
              shape: BoxShape.circle,
              border: Border.all(
                color: isSelected ? const Color(0xFF2563EB) : const Color(0xFFCBD5E1),
                width: isSelected ? 2.5 : 1.0,
              ),
            ),
          ),
        ),
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
                      child: MouseRegion(
                        onHover: _handleHover,
                        child: Listener(
                          behavior: HitTestBehavior.opaque,
                          onPointerDown: (e) => _handlePanStart(
                            DragStartDetails(
                              globalPosition: e.position,
                              localPosition: e.localPosition,
                            ),
                          ),
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
                            onTapUp: _handleTapUp,
                            child: CustomPaint(
                              key: const Key('sketchCanvas'),
                              size: Size(canvasWidth, canvasHeight),
                              painter: TableSketchPainter(
                                doc: _doc,
                                cellSize: _cellSize,
                                selectedLineIndex: _selectedLineIndex,
                                selectedLineIndices: _selectedLineIndices,
                                previewLine: _previewLine,
                                previewRect: _previewRect,
                                hoveredSegmentLine: _hoverSegment,
                                marqueeRect: _marqueeRect,
                                verticalGuides: _verticalGuides,
                                horizontalGuides: _horizontalGuides,
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
                      '크기: ${_previewResult!.rows}행 ${_previewResult!.cols}열 '
                      '(${_previewResult!.widthMm.toStringAsFixed(1)} × ${_previewResult!.heightMm.toStringAsFixed(1)} mm)',
                      style: const TextStyle(
                        fontSize: 12,
                        color: Color(0xFF475569),
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      '셀 개수: ${_previewResult!.cells.length}개',
                      style: const TextStyle(
                        fontSize: 12,
                        color: Color(0xFF475569),
                      ),
                    ),
                    if (_previewResult!.warnings.isNotEmpty) ...[
                      const SizedBox(height: 6),
                      Text(
                        '주의: ${_previewResult!.warnings.join(", ")}',
                        style: const TextStyle(
                          fontSize: 11,
                          color: Color(0xFFD97706),
                        ),
                      ),
                    ],
                  ] else ...[
                    const Text(
                      '그려진 표 선이 없습니다. 상단 도구로 사각형이나 선을 그리면 미리보기가 갱신됩니다.',
                      style: TextStyle(fontSize: 12, color: Color(0xFF94A3B8)),
                    ),
                  ],
                ],
              ),
            ),
            const SizedBox(height: 12),

            // 한/글 복사 버튼
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
              label: Text(_copying ? '복사 중...' : '한/글로 복사 (클립보드)'),
              style: FilledButton.styleFrom(
                backgroundColor: const Color(0xFF2563EB),
                padding: const EdgeInsets.symmetric(vertical: 12),
              ),
            ),
            const SizedBox(height: 12),
            const Divider(color: Color(0xFFE2E8F0)),
            const SizedBox(height: 8),

            // 서식 저장 영역
            const Text(
              '서식 보관함',
              style: TextStyle(
                fontSize: 14,
                fontWeight: FontWeight.bold,
                color: Color(0xFF1E293B),
              ),
            ),
            const SizedBox(height: 8),
            Row(
              children: [
                Expanded(
                  child: TextField(
                    key: const Key('sketchSaveNameInput'),
                    controller: _saveNameController,
                    decoration: const InputDecoration(
                      labelText: '서식 이름',
                      isDense: true,
                      border: OutlineInputBorder(),
                    ),
                  ),
                ),
                const SizedBox(width: 8),
                FilledButton(
                  key: const Key('sketchSaveButton'),
                  onPressed: _saveSketch,
                  style: FilledButton.styleFrom(
                    backgroundColor: const Color(0xFF475569),
                    padding: const EdgeInsets.symmetric(horizontal: 16),
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
