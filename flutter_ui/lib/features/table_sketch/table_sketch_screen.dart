import 'dart:async';
import 'dart:math' as math;

import 'package:flutter/gestures.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../core/api/abbreviation_api.dart' show ApiCall;
import 'table_sketch_api.dart';
import 'table_sketch_models.dart';
import 'table_sketch_painter.dart';

enum SketchToolMode { line, rect, eraser, text, select }

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
  int? _selectedLineIndex;
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

  // 끌기는 언제나 그리기에 쓰고(스크롤 상자가 끌기를 가져가면 선이 그려지지 않았다), 화면 이동은 휠·스크롤 막대로 한다.
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
      _selectedLineIndex = null;
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
      _selectedLineIndex = null;
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
          _selectedLineIndex = null;
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
      _selectedLineIndex = null;
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
                      _selectedLineIndex = null;
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
    setState(() {
      _dragStart = pos;
      _dragCurrent = pos;
    });

    if (_tool == SketchToolMode.eraser) {
      _eraseLineAt(pos);
    } else if (_tool == SketchToolMode.select) {
      _selectLineAt(pos);
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
    } else if (_tool == SketchToolMode.select) {
      _selectLineAt(pos);
    } else if (_tool == SketchToolMode.eraser) {
      _eraseLineAt(pos);
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
        if (_selectedLineIndex == bestIdx) {
          _selectedLineIndex = null;
        } else if (_selectedLineIndex != null &&
            _selectedLineIndex! > bestIdx) {
          _selectedLineIndex = _selectedLineIndex! - 1;
        }
      });
      _triggerPreviewDebounced();
    }
  }

  void _selectLineAt(Offset pos) {
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

    setState(() {
      _selectedLineIndex = bestIdx;
      if (bestIdx != null) {
        final line = _doc.lines[bestIdx];
        _lineWidth = line.width;
        _lineStyle = line.style;
      }
    });
  }

  void _deleteSelectedLine() {
    if (_selectedLineIndex != null &&
        _selectedLineIndex! >= 0 &&
        _selectedLineIndex! < _doc.lines.length) {
      _saveSnapshot();
      setState(() {
        _doc.lines.removeAt(_selectedLineIndex!);
        _selectedLineIndex = null;
      });
      _triggerPreviewDebounced();
    }
  }

  void _updateSelectedLineStyle({String? width, String? style}) {
    if (_selectedLineIndex != null &&
        _selectedLineIndex! >= 0 &&
        _selectedLineIndex! < _doc.lines.length) {
      _saveSnapshot();
      setState(() {
        final old = _doc.lines[_selectedLineIndex!];
        _doc.lines[_selectedLineIndex!] = old.copyWith(
          width: width ?? old.width,
          style: style ?? old.style,
        );
      });
      _triggerPreviewDebounced();
    }
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
        const SingleActivator(LogicalKeyboardKey.delete): _deleteSelectedLine,
        const SingleActivator(LogicalKeyboardKey.escape): () {
          setState(() {
            _selectedLineIndex = null;
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
            const SizedBox(width: 8),
            Container(width: 1, height: 24, color: const Color(0xFFCBD5E1)),
            const SizedBox(width: 8),

            // 선 굵기
            const Text(
              '굵기:',
              style: TextStyle(fontSize: 12, color: Color(0xFF64748B)),
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
                _selectedLineIndex = null;
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
                        // 누름·이동·뗌을 직접 받아 뗀 위치를 끝점으로 쓴다(한 번에 멀리 옮겨도 선이 그려지게).
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
