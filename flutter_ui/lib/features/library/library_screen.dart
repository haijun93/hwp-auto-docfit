import 'dart:async';
import 'dart:math' as math;

import 'package:flutter/gestures.dart' show PointerDeviceKind;
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:file_selector/file_selector.dart';

import '../../core/drop_events.dart';
import '../editor/memo_editor.dart';
import '../editor/memo_editor_page.dart';
import '../notebook/notebook_api.dart';
import 'library_api.dart';
import 'library_layout.dart';

String _errorText(Object error) => error.toString().replaceFirst(RegExp(r'^(Bad state|StateError): '), '');

class LibraryClipboardData {
  const LibraryClipboardData({this.text, this.filePath});
  final String? text;
  final String? filePath;
}

abstract interface class LibraryClipboardReader {
  Future<LibraryClipboardData?> read();
}

class DefaultLibraryClipboardReader implements LibraryClipboardReader {
  @override
  Future<LibraryClipboardData?> read() async {
    if (!await Clipboard.hasStrings()) return null;
    final data = await Clipboard.getData(Clipboard.kTextPlain);
    final text = data?.text;
    if (text == null || text.trim().isEmpty) return null;
    final normalized = text.trim();
    final isPath = !normalized.contains('\n') &&
        RegExp(r'^(?:[A-Za-z]:[\\/]|/)').hasMatch(normalized);
    return LibraryClipboardData(text: text, filePath: isPath ? normalized : null);
  }
}

class LibraryFileDrop {
  const LibraryFileDrop({required this.path});
  final String path;

  String get fileName => path.replaceAll('\\', '/').split('/').last;
}

class LibraryFileDropSource extends StatelessWidget {
  const LibraryFileDropSource({super.key, required this.drop, required this.child});
  final LibraryFileDrop drop;
  final Widget child;

  @override
  Widget build(BuildContext context) => Draggable<LibraryFileDrop>(
        data: drop,
        feedback: Material(elevation: 4, child: SizedBox(width: 80, height: 40, child: child)),
        child: child,
      );
}

class _LibraryPasteIntent extends Intent {
  const _LibraryPasteIntent();
}

class _LibrarySelectAllIntent extends Intent {
  const _LibrarySelectAllIntent();
}

class _LibraryDeleteSelectionIntent extends Intent {
  const _LibraryDeleteSelectionIntent();
}

class _LibraryClearSelectionIntent extends Intent {
  const _LibraryClearSelectionIntent();
}

/// 글 입력 칸에 초점이 있으면 꺼져서 Ctrl+A·Delete·Esc가 입력 칸 기본 동작으로 넘어가게 하는 단축키 동작.
class _LibraryKeyAction<T extends Intent> extends Action<T> {
  _LibraryKeyAction(this.onInvoke);
  final VoidCallback onInvoke;

  bool get _editingText {
    final context = primaryFocus?.context;
    if (context == null) return false;
    return context.widget is EditableText || context.findAncestorWidgetOfExactType<EditableText>() != null;
  }

  @override
  bool isEnabled(T intent) => !_editingText;

  @override
  Object? invoke(T intent) {
    onInvoke();
    return null;
  }
}

const _spaceNames = {
  LibrarySpace.core: '핵심자료',
  LibrarySpace.basis: '기초자료',
  LibrarySpace.reference: '참고자료',
  LibrarySpace.temp: '임시저장소',
};

/// 내용(경로·URL·텍스트) 없이 klib에 내용만 저장되어 다시 만들 수 없는 자료는 복사할 수 없다.
bool _canCopyItem(LibraryItem item) =>
    (item.source?.trim().isNotEmpty ?? false) ||
    ((item.kind == LibraryItemKind.text || item.kind == LibraryItemKind.note) && item.text != null);

const _textKinds = {LibraryItemKind.text, LibraryItemKind.richText, LibraryItemKind.note};

/// 메모 편집기로 열어 고치는 글 자료(서식 글 richText는 JSON이라 제외).
const _memoKinds = {LibraryItemKind.text, LibraryItemKind.note};

final _riskyOpenPath = RegExp(
  r'\.(exe|bat|cmd|com|ps1|psm1|vbs|vbe|js|jse|wsf|wsh|msi|msp|scr|pif|lnk|url|hta|cpl|msc|reg|jar|appref-ms)[\s.]*$',
  caseSensitive: false,
);

class LibraryScreen extends StatefulWidget {
  const LibraryScreen({
    super.key,
    required this.api,
    this.clipboardReader,
    this.scanApi,
    this.folderPicker,
    this.scanPollInterval = const Duration(milliseconds: 400),
    this.watchDropEvents,
    this.notebookApi,
    this.initialBoxId,
    this.initialItemId,
    this.openApi,
  });

  /// 있으면 항목 메뉴에 '노트북에 출처로 추가'가 나타난다.
  final NotebookApi? notebookApi;

  /// 처음 열 때 고를 자료함과 강조할 항목(노트북 출처의 '자료함에서 보기').
  final String? initialBoxId;
  final String? initialItemId;

  /// 창에 파일을 놓았다는 알림 구독(시험에서 대체). 기본은 'docfit-library-files-dropped' 창 이벤트.
  final void Function() Function(void Function() onDrop)? watchDropEvents;

  final LibraryApi api;
  final LibraryClipboardReader? clipboardReader;

  /// 폴더 스캔 API. 생략하면 `api`가 `LibraryScanApi`일 때 그것을 쓰고, 아니면 스캔 단추를 숨긴다.
  final LibraryScanApi? scanApi;

  /// 스캔할 폴더 선택 창(시험에서 대체). 기본은 file_selector의 getDirectoryPath.
  final Future<String?> Function()? folderPicker;
  final Duration scanPollInterval;

  /// 자료 열기(연결 앱·탐색기·브라우저). 생략하면 `api`가 `LibraryOpenApi`일 때 그것을 쓴다(시험에서 가짜 실행기).
  final LibraryOpenApi? openApi;

  @override
  State<LibraryScreen> createState() => _LibraryScreenState();
}

class _LibraryScreenState extends State<LibraryScreen> {
  late final LibraryClipboardReader _clipboardReader =
      widget.clipboardReader ?? DefaultLibraryClipboardReader();
  final _newBoxController = TextEditingController();
  final _searchController = TextEditingController();
  final _newItemController = TextEditingController();
  final _rootFocus = FocusNode(debugLabel: 'libraryRoot');
  final _spaceKeys = {for (final space in LibrarySpace.values) space: GlobalKey()};
  final _searchResults = <LibrarySearchResult>[];
  String? _highlightedItemId;
  bool _showSearchResults = false;
  List<LibraryBox> _boxes = [];
  LibraryBox? _selectedBox;
  List<LibraryItem> _items = [];
  List<LibraryRelation> _relations = [];

  /// 선택한 자료 ID 집합. 일반 클릭=하나만, Ctrl+클릭=추가/해제, 빈 곳 클릭·Esc=해제.
  final Set<String> _selectedIds = <String>{};

  /// Ctrl+A가 고를 영역(마지막으로 누른 카드의 영역).
  LibrarySpace _activeSpace = LibrarySpace.core;

  /// 영역별 표시 폭(겹침 방지 배치에 쓴다).
  final Map<LibrarySpace, double> _spaceWidths = {};
  bool _batchBusy = false;
  String? _statusMessage;
  LibraryScanStatus? _scanStatus;
  Timer? _scanTimer;
  bool _scanPolling = false;
  static const _cardWidth = LibraryLayout.cardWidth;
  static const _cardHeight = LibraryLayout.cardHeight;

  @override
  void initState() {
    super.initState();
    _loadBoxes();
    final drops = _dropApi;
    if (drops != null) {
      _stopDrops = (widget.watchDropEvents ??
          (cb) => watchWindowEvent('docfit-library-files-dropped', cb))(() => unawaited(_takeDrops()));
      unawaited(drops.watchDrops(true).catchError((Object _) {}));
    }
  }

  void Function()? _stopDrops;

  LibraryDropApi? get _dropApi {
    final Object api = widget.api;
    return api is LibraryDropApi ? api : null;
  }

  LibraryMemoApi? get _memoApi {
    final Object api = widget.api;
    return api is LibraryMemoApi ? api : null;
  }

  /// '+메모'로 쓰다가 저장하지 않고 닫은 초안. 다시 '+메모'를 누르면 이어서 쓴다.
  MemoDocument? _memoDraft;

  LibraryOpenApi? get _openApi {
    final explicit = widget.openApi;
    if (explicit != null) return explicit;
    final Object api = widget.api;
    return api is LibraryOpenApi ? api : null;
  }

  /// 탐색기에서 끌어 놓은 파일을 선택한 자료함의 '핵심' 공간에 차례로 넣는다.
  Future<void> _takeDrops() async {
    final drops = _dropApi;
    if (drops == null || !mounted) return;
    final paths = await drops.takeDroppedPaths();
    if (paths.isEmpty || !mounted) return;
    if (_selectedBox == null) {
      setState(() => _statusMessage = '먼저 자료함을 고르거나 만든 뒤 파일을 놓아 주세요.');
      return;
    }
    var added = 0;
    for (final path in paths) {
      try {
        await _addFile(LibraryFileDrop(path: path), LibrarySpace.core, Offset.zero);
        added++;
      } catch (error) {
        if (mounted) setState(() => _statusMessage = '추가하지 못했습니다: $error');
      }
    }
    if (mounted && added > 0) setState(() => _statusMessage = '파일 $added개를 자료함에 넣었습니다.');
  }

  LibraryScanApi? get _scanApi {
    final explicit = widget.scanApi;
    if (explicit != null) return explicit;
    // LibraryScanApi는 LibraryApi의 하위형이 아니라 Object로 받아야 형 승격이 된다.
    final Object api = widget.api;
    return api is LibraryScanApi ? api : null;
  }

  Future<void> _startScan() async {
    final box = _selectedBox;
    final scan = _scanApi;
    if (box == null || scan == null || (_scanStatus?.isScanning ?? false)) return;
    final picker = widget.folderPicker;
    final directory = picker != null ? await picker() : await getDirectoryPath();
    if (directory == null || !mounted) return;
    try {
      await scan.startScan(box.id, directory);
    } catch (error) {
      if (mounted) setState(() => _statusMessage = error.toString());
      return;
    }
    if (!mounted) return;
    setState(() {
      _statusMessage = null;
      _scanStatus = const LibraryScanStatus(state: 'scanning', phase: 'enumerate');
    });
    _scanTimer?.cancel();
    _scanTimer = Timer.periodic(widget.scanPollInterval, (_) => _pollScan());
  }

  Future<void> _pollScan() async {
    final scan = _scanApi;
    if (scan == null || _scanPolling) return;
    _scanPolling = true;
    try {
      final status = await scan.scanStatus();
      if (!mounted) return;
      setState(() => _scanStatus = status);
      if (!status.isScanning) {
        _scanTimer?.cancel();
        _scanTimer = null;
      }
    } catch (error) {
      _scanTimer?.cancel();
      _scanTimer = null;
      if (mounted) setState(() => _statusMessage = error.toString());
    } finally {
      _scanPolling = false;
    }
  }

  Future<void> _cancelScan() async {
    try {
      await _scanApi?.cancelScan();
    } catch (error) {
      if (mounted) setState(() => _statusMessage = error.toString());
    }
  }

  String _scanSummary(LibraryScanStatus s) {
    switch (s.state) {
      case 'scanning':
        return s.total > 0
            ? '스캔 중 ${s.processed}/${s.total}'
            : '폴더를 훑는 중… 파일 ${s.discovered}개 발견';
      case 'done':
        return '스캔 완료: 파일 ${s.total}개(변경 ${s.changed}개, 삭제 ${s.removed}개)'
            '${s.skippedErrors > 0 ? ', 읽지 못한 곳 ${s.skippedErrors}곳' : ''}';
      case 'cancelled':
        return '스캔을 취소했습니다. 이미 반영된 항목은 유지됩니다.';
      case 'error':
        return '스캔 오류: ${s.message}';
      default:
        return '';
    }
  }

  Widget _buildScanPanel() {
    final status = _scanStatus;
    if (status == null || status.state == 'idle') return const SizedBox.shrink();
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
      child: Row(children: [
        if (status.isScanning)
          SizedBox(
            width: 220,
            child: LinearProgressIndicator(key: const ValueKey('libraryScanProgress'), value: status.fraction),
          ),
        if (status.isScanning) const SizedBox(width: 8),
        Flexible(child: Text(_scanSummary(status), key: const ValueKey('libraryScanStatus'), overflow: TextOverflow.ellipsis)),
        if (status.isScanning)
          TextButton(key: const ValueKey('libraryScanCancel'), onPressed: _cancelScan, child: const Text('취소')),
      ]),
    );
  }

  @override
  void dispose() {
    _stopDrops?.call();
    final drops = _dropApi;
    if (drops != null) unawaited(drops.watchDrops(false).catchError((Object _) {}));
    _scanTimer?.cancel();
    _newBoxController.dispose();
    _searchController.dispose();
    _newItemController.dispose();
    _rootFocus.dispose();
    super.dispose();
  }

  Future<void> _loadBoxes() async {
    List<LibraryBox> boxes;
    try {
      boxes = await widget.api.listBoxes();
    } catch (error) {
      if (!mounted) return;
      final message = error.toString().contains('klib') || error.toString().contains('자료함 엔진')
          ? '자료함 엔진(klib.exe)이 없습니다'
          : error.toString();
      setState(() => _statusMessage = message);
      return;
    }
    if (!mounted) return;
    final target = _pendingFocusBoxId;
    final targetBox = target == null ? null : boxes.where((b) => b.id == target).firstOrNull;
    setState(() {
      _boxes = boxes;
      if (targetBox != null) _selectedBox = targetBox;
      _selectedBox ??= boxes.isEmpty ? null : boxes.first;
      if (target != null && targetBox == null) {
        _statusMessage = '자료함을 찾을 수 없습니다(삭제되었을 수 있습니다).';
      }
    });
    _pendingFocusBoxId = null;
    final selected = _selectedBox;
    if (selected != null) await _loadBoxContent(selected.id);
    final itemId = _pendingFocusItemId;
    _pendingFocusItemId = null;
    if (targetBox != null && itemId != null && mounted) {
      final item = _items.where((i) => i.id == itemId).firstOrNull;
      setState(() {
        _highlightedItemId = item?.id;
        _statusMessage = item == null
            ? '자료함 항목을 찾을 수 없습니다(삭제되었을 수 있습니다).'
            : '“${item.title}” 항목입니다.';
      });
    }
  }

  /// 처음 열 때 고르고 강조할 자료함·항목(한 번만 쓴다).
  late String? _pendingFocusBoxId = widget.initialBoxId;
  late String? _pendingFocusItemId = widget.initialItemId;

  /// 항목을 노트북 출처로 넣는다. 노트북을 고르게 하고, 이미 출처면 그렇다고 알린다.
  Future<void> _addToNotebook(LibraryItem item) async {
    final notebooks = widget.notebookApi;
    if (notebooks == null) return;
    if ((item.source ?? '').trim().isEmpty) {
      setState(() => _statusMessage = '파일 경로가 있는 자료만 노트북 출처로 추가할 수 있습니다.');
      return;
    }
    final notebook = await showDialog<Notebook>(
      context: context,
      builder: (context) => _NotebookPickDialog(api: notebooks, itemTitle: item.title),
    );
    if (notebook == null || !mounted) return;
    try {
      final result = await notebooks.addSourceFromItem(notebook.id, item.id);
      if (!mounted) return;
      setState(() => _statusMessage = result.reused
          ? '이미 “${notebook.name}” 노트북 출처에 있습니다.'
          : '“${item.title}”을(를) “${notebook.name}” 노트북 출처로 추가했습니다.');
    } catch (error) {
      if (mounted) setState(() => _statusMessage = '노트북에 추가하지 못했습니다: ${_errorText(error)}');
    }
  }

  Future<void> _loadBoxContent(String boxId) async {
    List<LibraryItem> items;
    List<LibraryRelation> relations;
    try {
      items = await widget.api.listItems(boxId, query: _searchController.text);
      relations = await widget.api.listRelations(boxId);
    } catch (error) {
      if (!mounted) return;
      setState(() => _statusMessage = error.toString());
      return;
    }
    if (!mounted) return;
    if (_searchController.text.trim().isEmpty) items = await _fixStoredOverlaps(boxId, items);
    if (!mounted) return;
    setState(() {
      _items = items;
      _relations = relations;
      _selectedIds.retainAll(items.map((i) => i.id));
    });
  }

  /// 이미 겹쳐 저장된 카드(이전 판에서 끌어 놓았거나 영역을 옮긴 것)를 열 때 한 번 빈 자리로 옮겨 저장한다.
  /// 저장에 실패해도 화면에서는 겹치지 않게 그린다(표시 단계에서도 같은 규칙으로 정리).
  Future<List<LibraryItem>> _fixStoredOverlaps(String boxId, List<LibraryItem> items) async {
    final fixed = {for (final i in items) i.id: i};
    for (final space in LibrarySpace.values) {
      final inSpace = items.where((i) => i.space == space).toList();
      if (inSpace.length < 2 && inSpace.every((i) => i.x >= 0 && i.y >= 0)) continue;
      final resolved = LibraryLayout.resolve(inSpace);
      for (final item in inSpace) {
        final p = resolved[item.id]!;
        if ((p - Offset(item.x, item.y)).distance < 0.5) continue;
        try {
          await widget.api.moveItem(item.id, boxId: boxId, space: space, x: p.dx, y: p.dy);
          fixed[item.id] = item.copyWith(x: p.dx, y: p.dy);
        } catch (_) {
          // 저장하지 못해도 표시 단계에서 겹치지 않게 그린다.
        }
      }
    }
    return [for (final i in items) fixed[i.id]!];
  }

  Future<void> _reload() async {
    final box = _selectedBox;
    if (box != null) await _loadBoxContent(box.id);
  }

  Future<void> _selectBox(LibraryBox box) async {
    if (_selectedBox?.id == box.id) return;
    setState(() {
      _selectedBox = box;
      _searchController.clear();
      _searchResults.clear();
      _highlightedItemId = null;
      _selectedIds.clear();
      _statusMessage = null;
    });
    await _loadBoxContent(box.id);
  }

  Future<void> _renameBox() async {
    final box = _selectedBox;
    if (box == null) return;
    final controller = TextEditingController(text: box.name);
    final name = await showDialog<String>(context: context, builder: (context) => AlertDialog(
      title: const Text('자료함 이름 바꾸기'),
      content: TextField(controller: controller, autofocus: true, key: const ValueKey('libraryRenameBoxInput')),
      actions: [TextButton(onPressed: () => Navigator.pop(context), child: const Text('취소')),
        TextButton(onPressed: () => Navigator.pop(context, controller.text.trim()), child: const Text('저장'))],
    ));
    if (name == null || name.trim().isEmpty) return;
    await widget.api.renameBox(box.id, name.trim());
    if (!mounted) return;
    setState(() {
      _selectedBox = LibraryBox(id: box.id, name: name.trim());
      _boxes = _boxes.map((b) => b.id == box.id ? _selectedBox! : b).toList();
    });
  }

  Future<void> _deleteBox() async {
    final box = _selectedBox;
    if (box == null) return;
    final confirm = await showDialog<bool>(context: context, builder: (context) => AlertDialog(
      title: const Text('자료함 삭제'), content: Text('“${box.name}” 자료함과 등록된 자료를 삭제할까요?'),
      actions: [TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('취소')),
        TextButton(key: const ValueKey('libraryConfirmDeleteBox'), onPressed: () => Navigator.pop(context, true), child: const Text('삭제'))],
    ));
    if (confirm != true) return;
    await widget.api.deleteBox(box.id);
    if (!mounted) return;
    setState(() { _boxes.removeWhere((b) => b.id == box.id); _selectedBox = null; _items = []; _relations = []; _selectedIds.clear(); });
    await _loadBoxes();
  }

  Future<void> _exportBox() async {
    final box = _selectedBox;
    if (box == null) return;
    final directory = await getDirectoryPath();
    if (directory == null || !mounted) return;
    final count = await widget.api.exportBox(box.id, directory);
    if (!mounted) return;
    setState(() => _statusMessage = '$directory 에 자료 $count개를 내보냈습니다.');
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(
      content: Text('저장 위치: $directory'),
      action: SnackBarAction(label: '열기', onPressed: () => _openPathWithFeedback(directory, LibraryItemKind.folder)),
    ));
  }

  // ── 자료 열기 ─────────────────────────────────────────────

  /// 경로를 연결 앱으로 연다. 성공하면 아무 창도 띄우지 않고, 실패(취소 제외)는 결과로 돌려준다.
  /// 실행 파일은 먼저 확인을 받는다. 자료함에 등록되지 않은 경로([itemId] 없음)의 실행 파일은 막는다.
  Future<LibraryOpenResult?> _openSource({String? itemId, required LibraryItemKind kind, required String source}) async {
    final path = source.trim();
    if (path.isEmpty) {
      return const LibraryOpenResult(ok: false, code: 'NO_SOURCE', message: '원본 파일 경로가 없는 자료입니다.');
    }
    if (path.contains('\n') || path.contains('\r')) {
      return const LibraryOpenResult(ok: false, code: 'INVALID_PATH', message: '줄바꿈이 든 경로는 열 수 없습니다.');
    }
    final api = _openApi;
    if (api == null) {
      return const LibraryOpenResult(ok: false, code: 'ERROR', message: '이 환경에서는 자료를 연결 앱으로 열 수 없습니다.');
    }
    final isWeb = kind == LibraryItemKind.link || RegExp(r'^https?://', caseSensitive: false).hasMatch(path);
    var confirmed = false;
    if (!isWeb && _riskyOpenPath.hasMatch(path)) {
      if (itemId == null) {
        return const LibraryOpenResult(ok: false, code: 'BLOCKED', message: '자료함에 등록되지 않은 실행 파일은 열 수 없습니다.');
      }
      confirmed = await _confirmRiskyOpen(path);
      if (!confirmed) return null;
    }
    var result = await api.openItem(itemId: itemId, kind: kind, source: path, confirmed: confirmed);
    if (!result.ok && result.code == 'CONFIRM_REQUIRED' && !confirmed && itemId != null) {
      if (!await _confirmRiskyOpen(path)) return null;
      result = await api.openItem(itemId: itemId, kind: kind, source: path, confirmed: true);
    }
    return result;
  }

  Future<bool> _confirmRiskyOpen(String path) async {
    if (!mounted) return false;
    final yes = await showDialog<bool>(context: context, builder: (context) => AlertDialog(
      key: const ValueKey('libraryConfirmRiskyOpen'),
      title: const Text('실행 파일 열기'),
      content: Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.start, children: [
        const Text('이 자료는 프로그램(실행 파일)입니다. 믿을 수 있는 파일일 때만 실행하세요.'),
        const SizedBox(height: 8),
        SelectableText(path),
      ]),
      actions: [
        TextButton(autofocus: true, onPressed: () => Navigator.pop(context, false), child: const Text('취소')),
        TextButton(key: const ValueKey('libraryConfirmRiskyOpenYes'), onPressed: () => Navigator.pop(context, true), child: const Text('실행')),
      ],
    ));
    return yes == true;
  }

  String _openFailureReason(LibraryOpenResult result) => switch (result.code) {
        'SOURCE_MISSING' => '원본 파일을 찾을 수 없습니다. 옮겨졌거나 삭제되었을 수 있습니다.',
        'NO_APP' => '이 형식에 연결된 앱이 없습니다. Windows 설정에서 연결 프로그램을 지정해 주세요.',
        'NO_SOURCE' => '원본 파일 경로가 없는 자료입니다.',
        _ => result.message.isEmpty ? '알 수 없는 이유로 열지 못했습니다.' : result.message,
      };

  Future<void> _showOpenFailure(String title, String path, LibraryOpenResult result) async {
    if (!mounted) return;
    await showDialog<void>(context: context, builder: (dialogContext) => AlertDialog(
      key: const ValueKey('libraryOpenFailed'),
      title: const Text('자료를 열지 못했습니다'),
      content: Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text(title, style: const TextStyle(fontWeight: FontWeight.bold)),
        const SizedBox(height: 6),
        Text(_openFailureReason(result), key: const ValueKey('libraryOpenFailedReason')),
        if (path.isNotEmpty) ...[
          const SizedBox(height: 8),
          SelectableText(path, key: const ValueKey('libraryOpenFailedPath')),
        ],
      ]),
      actions: [
        if (path.isNotEmpty)
          TextButton(
            key: const ValueKey('libraryOpenFailedCopyPath'),
            onPressed: () async {
              await Clipboard.setData(ClipboardData(text: path));
              if (dialogContext.mounted) Navigator.pop(dialogContext);
              if (mounted) setState(() => _statusMessage = '경로를 복사했습니다.');
            },
            child: const Text('경로 복사'),
          ),
        TextButton(autofocus: true, onPressed: () => Navigator.pop(dialogContext), child: const Text('확인')),
      ],
    ));
  }

  Future<void> _openPathWithFeedback(String path, LibraryItemKind kind) async {
    final result = await _openSource(kind: kind, source: path);
    if (result != null && !result.ok) await _showOpenFailure(path, path, result);
  }

  /// 텍스트 자료는 연결 앱 대신 보기 창으로 보여 준다.
  Future<void> _showTextItem(LibraryItem item) => showDialog<void>(context: context, builder: (dialogContext) => AlertDialog(
        key: const ValueKey('libraryTextView'),
        title: Text(item.title),
        content: SizedBox(width: 480, child: SingleChildScrollView(child: SelectableText(item.text ?? item.title))),
        actions: [
          TextButton(
            onPressed: () async {
              await Clipboard.setData(ClipboardData(text: item.text ?? item.title));
              if (dialogContext.mounted) Navigator.pop(dialogContext);
            },
            child: const Text('복사'),
          ),
          TextButton(autofocus: true, onPressed: () => Navigator.pop(dialogContext), child: const Text('닫기')),
        ],
      ));

  /// '+메모': 메모 편집기(노트북 '+메모 추가'와 같은 것)를 열고, 저장하면 핵심자료에 텍스트 자료로 넣는다.
  /// 저장하지 않고 닫으면 초안이 남고, 휴지통을 누르면 초안을 버린다.
  Future<void> _addMemo() async {
    final box = _selectedBox;
    if (box == null) return;
    final saved = await Navigator.of(context).push<LibraryItem>(
      MaterialPageRoute(
        builder: (pageContext) => MemoEditorPage<LibraryItem>(
          key: const ValueKey('libraryMemoPage'),
          initial: _memoDraft ?? const MemoDocument(title: '새 메모', markdown: ''),
          onAutoSave: (doc) async {
            if (mounted) setState(() => _memoDraft = doc);
          },
          onDelete: () {
            setState(() => _memoDraft = null);
            Navigator.of(pageContext).pop();
          },
          onSave: (doc) {
            final position = _nextPosition(LibrarySpace.core);
            return widget.api.addItem(
              boxId: box.id,
              kind: LibraryItemKind.text,
              title: doc.title.isEmpty ? '새 메모' : doc.title,
              space: LibrarySpace.core,
              x: position.dx,
              y: position.dy,
              text: doc.markdown,
            );
          },
          saveLabel: '자료함에 저장',
          hint: "작성한 메모를 저장하면 '${_spaceNames[LibrarySpace.core]}'에 텍스트 자료로 들어갑니다.",
          editorBackend: _memoApi?.memoEditorBackend,
        ),
      ),
    );
    if (!mounted || saved == null) return;
    setState(() {
      _memoDraft = null;
      _statusMessage = '메모를 자료함에 넣었습니다.';
    });
    if (_selectedBox?.id == box.id) await _loadBoxContent(box.id);
  }

  /// 글 자료를 메모 편집기로 열어 고친다. 저장하면 같은 자료의 내용(과 이름)이 바뀐다. 닫기만 하면 바뀌지 않는다.
  Future<void> _editTextItem(LibraryItem item, LibraryMemoApi memoApi) async {
    final String text;
    try {
      text = await memoApi.readItemText(item.id);
    } catch (error) {
      if (mounted) setState(() => _statusMessage = '메모를 열지 못했습니다: ${_errorText(error)}');
      return;
    }
    if (!mounted) return;
    final saved = await Navigator.of(context).push<bool>(
      MaterialPageRoute(
        builder: (pageContext) => MemoEditorPage<bool>(
          key: const ValueKey('libraryMemoPage'),
          initial: MemoDocument(title: item.title, markdown: text),
          onSave: (doc) async {
            await memoApi.updateItemText(item.id, title: doc.title, text: doc.markdown);
            return true;
          },
          saveLabel: '저장',
          hint: '저장하면 이 텍스트 자료의 내용이 바뀝니다. 닫기만 하면 바뀌지 않습니다.',
          editorBackend: memoApi.memoEditorBackend,
        ),
      ),
    );
    if (!mounted || saved != true) return;
    setState(() => _statusMessage = '메모를 저장했습니다.');
    await _reload();
  }

  /// 더블클릭·메뉴 '열기'. 파일·폴더는 연결 앱/탐색기, 웹 주소는 기본 브라우저, 글 자료는 메모 편집기(고칠 수 없는 환경이면 보기 창).
  Future<void> _openItem(LibraryItem item) async {
    final memoApi = _memoApi;
    if (memoApi != null && _memoKinds.contains(item.kind)) {
      await _editTextItem(item, memoApi);
      return;
    }
    final source = (item.source ?? '').trim();
    if (source.isEmpty && _textKinds.contains(item.kind)) {
      await _showTextItem(item);
      return;
    }
    final result = await _openSource(itemId: item.id, kind: item.kind, source: source);
    if (result != null && !result.ok) await _showOpenFailure(item.title, source, result);
  }

  Future<void> _search(String query) async {
    final box = _selectedBox;
    if (box == null) return;
    if (query.trim().isEmpty) {
      if (mounted) setState(() { _searchResults.clear(); _highlightedItemId = null; _showSearchResults = false; });
      await _loadBoxContent(box.id);
      return;
    }
    final results = await widget.api.searchContent(box.id, query);
    final items = await widget.api.listItems(box.id, query: query);
    if (!mounted || _selectedBox?.id != box.id) return;
    setState(() { _searchResults..clear()..addAll(results); _items = items; _highlightedItemId = null; _showSearchResults = true; });
  }

  Future<void> _jumpToSearchResult(LibrarySearchResult result) async {
    final box = _selectedBox;
    if (box == null) return;
    final items = await widget.api.listItems(box.id);
    final match = items.where((i) => i.source == result.path || i.title == result.name).firstOrNull;
    if (!mounted) return;
    setState(() { _items = items; _highlightedItemId = match?.id; });
    if (match != null) {
      await _openItem(match);
    } else if (result.path.isNotEmpty) {
      final opened = await _openSource(kind: LibraryItemKind.file, source: result.path);
      if (opened != null && !opened.ok) await _showOpenFailure(result.name, result.path, opened);
    }
  }

  Future<void> _renameItem(LibraryItem item) async {
    final controller = TextEditingController(text: item.title);
    final title = await showDialog<String>(context: context, builder: (context) => AlertDialog(
      title: const Text('자료 이름 바꾸기'), content: TextField(controller: controller, autofocus: true, key: const ValueKey('libraryRenameItemInput')),
      actions: [TextButton(onPressed: () => Navigator.pop(context), child: const Text('취소')),
        TextButton(onPressed: () => Navigator.pop(context, controller.text.trim()), child: const Text('저장'))],
    ));
    if (title == null || title.isEmpty) return;
    await widget.api.renameItem(item.id, title);
    await _reload();
  }

  Future<void> _deleteItem(LibraryItem item) async {
    final yes = await showDialog<bool>(context: context, builder: (context) => AlertDialog(
      title: const Text('자료 삭제'), content: Text('“${item.title}” 자료를 자료함에서 삭제할까요?'),
      actions: [TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('취소')),
        TextButton(onPressed: () => Navigator.pop(context, true), child: const Text('삭제'))],
    ));
    if (yes != true) return;
    await widget.api.deleteItem(item.id);
    await _reload();
  }

  Future<void> _editRelationLabel(LibraryRelation relation) async {
    final controller = TextEditingController(text: relation.label ?? '');
    final label = await showDialog<String>(context: context, builder: (context) => AlertDialog(
      title: const Text('관계 이름표'), content: TextField(controller: controller, autofocus: true, key: ValueKey('libraryRelationLabelInput-${relation.id}')),
      actions: [TextButton(onPressed: () => Navigator.pop(context), child: const Text('취소')),
        TextButton(onPressed: () => Navigator.pop(context, controller.text.trim()), child: const Text('저장'))],
    ));
    if (label == null) return;
    await widget.api.updateRelationLabel(relation.id, label);
    await _reload();
  }

  // ── 배치(겹침 방지) ──────────────────────────────────────

  /// 화면에 그려지는 위치(표시 단계의 겹침 정리 결과). 영역 위젯과 같은 규칙·같은 입력이다.
  Map<String, Offset> _displayPositions(LibrarySpace space) =>
      LibraryLayout.resolve(_items.where((i) => i.space == space).toList(), width: _spaceWidths[space]);

  Offset _displayOf(LibraryItem item) => _displayPositions(item.space)[item.id] ?? Offset(item.x, item.y);

  List<Rect> _occupied(LibrarySpace space, {Set<String> except = const {}}) => [
        for (final e in _displayPositions(space).entries)
          if (!except.contains(e.key)) LibraryLayout.rectAt(e.value),
      ];

  Offset _nextPosition(LibrarySpace space) => LibraryLayout.nextSlot(_occupied(space), width: _spaceWidths[space]);

  /// 여러 자료를 한 번에 옮긴다. 하나라도 실패하면 이미 옮긴 것을 되돌린다(부분 적용 방지).
  Future<bool> _applyMoves(List<LibraryItem> items, LibrarySpace space, Map<String, Offset> targets) async {
    final box = _selectedBox;
    if (box == null || items.isEmpty) return false;
    final done = <LibraryItem>[];
    try {
      for (final item in items) {
        final p = targets[item.id] ?? Offset(item.x, item.y);
        await widget.api.moveItem(item.id, boxId: box.id, space: space, x: p.dx, y: p.dy);
        done.add(item);
      }
    } catch (error) {
      for (final item in done.reversed) {
        try {
          await widget.api.moveItem(item.id, boxId: box.id, space: item.space, x: item.x, y: item.y);
        } catch (_) {}
      }
      await _reload();
      if (mounted) {
        setState(() => _statusMessage = items.length > 1
            ? '자료 ${items.length}개를 옮기지 못해 처음 상태로 되돌렸습니다: ${_errorText(error)}'
            : '자료를 옮기지 못했습니다: ${_errorText(error)}');
      }
      return false;
    }
    await _reload();
    return true;
  }

  /// 같은 영역 안 끌기·다른 영역으로 끌기. 여러 개를 골라 끌면 선택 전체가 상대 위치를 지키며 함께 움직인다.
  Future<void> _moveItem(LibraryItem item, LibrarySpace space, Offset offset, Size size) async {
    final group = _selectedIds.contains(item.id) && _selectedIds.length > 1
        ? [item, ..._items.where((i) => _selectedIds.contains(i.id) && i.id != item.id)]
        : [item];
    final ids = group.map((i) => i.id).toSet();
    final placed = _occupied(space, except: ids);
    final origin = _displayOf(item);
    final targets = <String, Offset>{};
    for (final g in group) {
      final p = LibraryLayout.freeSlot(offset + (_displayOf(g) - origin), placed, width: size.width);
      placed.add(LibraryLayout.rectAt(p));
      targets[g.id] = p;
    }
    final ok = await _applyMoves(group, space, targets);
    if (ok && group.length > 1 && mounted) {
      setState(() => _statusMessage = '자료 ${group.length}개를 ${_spaceNames[space]}(으)로 옮겼습니다.');
    }
  }

  /// 영역 이동(메뉴·선택 표시줄). 원래 좌표가 비어 있으면 그대로, 겹치면 가장 가까운 빈 칸.
  Future<void> _moveItemsToSpace(List<LibraryItem> items, LibrarySpace space) async {
    final ids = items.map((i) => i.id).toSet();
    final placed = _occupied(space, except: ids);
    final targets = <String, Offset>{};
    for (final item in items) {
      final p = LibraryLayout.freeSlot(_displayOf(item), placed, width: _spaceWidths[space]);
      placed.add(LibraryLayout.rectAt(p));
      targets[item.id] = p;
    }
    final ok = await _applyMoves(items, space, targets);
    if (ok && items.length > 1 && mounted) {
      setState(() => _statusMessage = '자료 ${items.length}개를 ${_spaceNames[space]}(으)로 옮겼습니다.');
    }
  }

  Future<void> _moveItemToSpace(LibraryItem item, LibrarySpace space) => _moveItemsToSpace([item], space);

  /// 정리 단추: 영역의 카드를 격자로 다시 놓는다.
  Future<void> _arrange(LibrarySpace space, LibraryArrangeOrder order) async {
    if (_searchController.text.trim().isNotEmpty) {
      setState(() => _statusMessage = '검색 중에는 정리할 수 없습니다. 검색어를 지운 뒤 다시 시도하세요.');
      return;
    }
    final items = sortForArrange(_items.where((i) => i.space == space).toList(), order);
    if (items.isEmpty) return;
    final ok = await _applyMoves(items, space, LibraryLayout.grid(items, width: _spaceWidths[space]));
    if (ok && mounted) setState(() => _statusMessage = '${_spaceNames[space]} 자료 ${items.length}개를 정리했습니다.');
  }

  Future<void> _createBox() async {
    final name = _newBoxController.text.trim();
    if (name.isEmpty) return;
    final box = await widget.api.createBox(name);
    if (!mounted) return;
    _newBoxController.clear();
    setState(() {
      _boxes = [..._boxes, box];
      _selectedBox = box;
      _selectedIds.clear();
    });
    await _loadBoxContent(box.id);
  }

  Future<void> _addText({LibrarySpace space = LibrarySpace.core}) async {
    final box = _selectedBox;
    final text = _newItemController.text.trim();
    if (box == null || text.isEmpty) return;
    final position = _nextPosition(space);
    await widget.api.addItem(
      boxId: box.id,
      kind: LibraryItemKind.text,
      title: text.length > 20 ? '${text.substring(0, 20)}...' : text,
      space: space,
      x: position.dx,
      y: position.dy,
      text: text,
    );
    _newItemController.clear();
    await _loadBoxContent(box.id);
  }

  Future<void> _addFile(LibraryFileDrop drop, LibrarySpace space, Offset global) async {
    final box = _selectedBox;
    final path = drop.path.trim();
    if (box == null || path.isEmpty) return;
    final context = _spaceKeys[space]?.currentContext;
    final object = context?.findRenderObject();
    final point = object is RenderBox && global != Offset.zero
        ? LibraryLayout.freeSlot(object.globalToLocal(global), _occupied(space), width: _spaceWidths[space])
        : _nextPosition(space);
    await widget.api.addItem(
      boxId: box.id,
      kind: LibraryItemKind.file,
      title: drop.fileName,
      space: space,
      x: point.dx,
      y: point.dy,
      source: path,
    );
    await _loadBoxContent(box.id);
  }

  Future<void> _paste() async {
    final box = _selectedBox;
    if (box == null) return;
    final data = await _clipboardReader.read();
    if (!mounted) return;
    if (data == null || ((data.text == null || data.text!.trim().isEmpty) &&
        (data.filePath == null || data.filePath!.trim().isEmpty))) {
      setState(() => _statusMessage = '클립보드에 지원되는 자료가 없습니다.');
      return;
    }
    if (data.filePath?.trim().isNotEmpty == true) {
      await _addFile(LibraryFileDrop(path: data.filePath!.trim()), LibrarySpace.core, Offset.zero);
    } else {
      final text = data.text!.trim();
      final position = _nextPosition(LibrarySpace.core);
      await widget.api.addItem(
        boxId: box.id,
        kind: LibraryItemKind.text,
        title: text.length > 20 ? '${text.substring(0, 20)}...' : text,
        space: LibrarySpace.core,
        x: position.dx,
        y: position.dy,
        text: text,
      );
      await _loadBoxContent(box.id);
    }
    if (mounted) setState(() => _statusMessage = null);
  }

  // ── 선택 ────────────────────────────────────────────────

  List<LibraryItem> get _selectedItems => _items.where((i) => _selectedIds.contains(i.id)).toList();

  bool get _multiSelectModifier =>
      HardwareKeyboard.instance.isControlPressed || HardwareKeyboard.instance.isMetaPressed;

  /// 일반 클릭=그 자료만 선택(다시 누르면 해제), Ctrl+클릭=추가/해제.
  /// 핵심자료 하나만 골라 둔 상태에서 다른 핵심자료를 일반 클릭하면 두 자료 사이에 관계선을 만든다(기존 동작).
  Future<void> _tapItem(LibraryItem item) async {
    _rootFocus.requestFocus();
    _activeSpace = item.space;
    if (_multiSelectModifier) {
      setState(() {
        if (!_selectedIds.remove(item.id)) _selectedIds.add(item.id);
      });
      return;
    }
    final anchorId = _selectedIds.length == 1 ? _selectedIds.first : null;
    final anchor = anchorId == null ? null : _items.where((i) => i.id == anchorId).firstOrNull;
    final box = _selectedBox;
    if (anchor != null && box != null && anchor.id != item.id &&
        anchor.space == LibrarySpace.core && item.space == LibrarySpace.core) {
      try {
        await widget.api.addRelation(box.id, anchor.id, item.id);
      } catch (error) {
        if (mounted) setState(() => _statusMessage = error.toString());
      }
      if (mounted) setState(_selectedIds.clear);
      await _loadBoxContent(box.id);
      return;
    }
    setState(() {
      final only = anchorId == item.id;
      _selectedIds.clear();
      if (!only) _selectedIds.add(item.id);
    });
  }

  void _clearSelection() {
    if (_selectedIds.isEmpty) return;
    setState(_selectedIds.clear);
  }

  void _selectAllInActiveSpace() {
    final ids = _items.where((i) => i.space == _activeSpace).map((i) => i.id).toList();
    setState(() {
      _selectedIds
        ..clear()
        ..addAll(ids);
      _statusMessage = '${_spaceNames[_activeSpace]} 자료 ${ids.length}개를 골랐습니다.';
    });
  }

  Future<void> _deleteSelection() async {
    final items = _selectedItems;
    if (items.isEmpty || _batchBusy) return;
    final yes = await showDialog<bool>(context: context, builder: (context) => AlertDialog(
      key: const ValueKey('libraryConfirmBatchDelete'),
      title: const Text('자료 삭제'),
      content: Text('고른 자료 ${items.length}개를 자료함에서 삭제할까요?\n원본 파일은 지우지 않습니다.'),
      actions: [
        TextButton(autofocus: true, onPressed: () => Navigator.pop(context, false), child: const Text('취소')),
        TextButton(key: const ValueKey('libraryConfirmBatchDeleteYes'), onPressed: () => Navigator.pop(context, true), child: Text('${items.length}개 삭제')),
      ],
    ));
    if (yes != true) return;
    setState(() => _batchBusy = true);
    var failed = 0;
    for (final item in items) {
      try {
        await widget.api.deleteItem(item.id);
      } catch (_) {
        failed++;
      }
    }
    _selectedIds.clear();
    await _reload();
    if (!mounted) return;
    setState(() {
      _batchBusy = false;
      _statusMessage = failed == 0
          ? '자료 ${items.length}개를 삭제했습니다.'
          : '자료 ${items.length - failed}개를 삭제했고 $failed개는 삭제하지 못했습니다.';
    });
  }

  Future<void> _moveSelectionToSpace(LibrarySpace space) async {
    final items = _selectedItems;
    if (items.isEmpty || _batchBusy) return;
    setState(() => _batchBusy = true);
    await _moveItemsToSpace(items, space);
    if (mounted) setState(() => _batchBusy = false);
  }

  Future<void> _openSelection() async {
    final items = _selectedItems;
    if (items.isEmpty || _batchBusy) return;
    if (items.length == 1) {
      await _openItem(items.single);
      return;
    }
    var opened = 0;
    var skipped = 0;
    final failures = <String>[];
    for (final item in items) {
      final source = (item.source ?? '').trim();
      if (source.isEmpty) {
        skipped++;
        continue;
      }
      final result = await _openSource(itemId: item.id, kind: item.kind, source: source);
      if (result == null) {
        skipped++;
      } else if (result.ok) {
        opened++;
      } else {
        failures.add('${item.title}: ${_openFailureReason(result)}');
      }
    }
    if (!mounted) return;
    setState(() => _statusMessage = '자료 $opened개를 열었습니다'
        '${skipped > 0 ? ', $skipped개는 원본 파일이 없거나 취소해 건너뛰었습니다' : ''}'
        '${failures.isNotEmpty ? ', ${failures.length}개는 열지 못했습니다' : ''}.');
    if (failures.isNotEmpty) {
      await showDialog<void>(context: context, builder: (context) => AlertDialog(
        key: const ValueKey('libraryOpenFailed'),
        title: Text('자료 ${failures.length}개를 열지 못했습니다'),
        content: SizedBox(width: 480, child: SingleChildScrollView(child: SelectableText(failures.join('\n')))),
        actions: [TextButton(autofocus: true, onPressed: () => Navigator.pop(context), child: const Text('확인'))],
      ));
    }
  }

  Future<void> _copySelectionPaths() async {
    final items = _selectedItems;
    if (items.isEmpty) return;
    final lines = [for (final i in items) (i.source?.trim().isNotEmpty ?? false) ? i.source!.trim() : (i.text ?? i.title)];
    await Clipboard.setData(ClipboardData(text: lines.join('\n')));
    if (mounted) setState(() => _statusMessage = '경로 ${lines.length}개를 복사했습니다.');
  }

  /// 이동·복사 창: 같은 자료함의 다른 영역이나 다른 자료함으로 옮기거나 복사한다.
  Future<void> _transferSelection() async {
    final current = _selectedBox;
    final items = _selectedItems;
    if (current == null || items.isEmpty || _batchBusy) return;
    final request = await showDialog<_TransferRequest>(
      context: context,
      builder: (context) => _TransferDialog(boxes: _boxes, current: current, count: items.length),
    );
    if (request == null || !mounted) return;
    setState(() => _batchBusy = true);
    try {
      if (!request.copy && request.box.id == current.id) {
        await _moveItemsToSpace(items, request.space);
      } else {
        await _copyItems(items, request.box, request.space, removeOriginals: !request.copy);
      }
    } finally {
      if (mounted) setState(() => _batchBusy = false);
    }
  }

  /// 복사(또는 다른 자료함으로 이동 = 복사 뒤 원본 등록 삭제). 실패하면 만든 사본을 지워 처음 상태로 돌린다.
  /// 원본 파일은 건드리지 않고 자료함 등록만 늘린다. 같은 자료함 안 복사는 이름 뒤에 '(사본)'을 붙인다.
  /// 관계선은 복사하지 않는다(다른 자료함으로 옮기면 원래 관계선은 원본 등록과 함께 지워진다).
  Future<void> _copyItems(List<LibraryItem> items, LibraryBox target, LibrarySpace space, {required bool removeOriginals}) async {
    final current = _selectedBox;
    if (current == null) return;
    final copyable = items.where(_canCopyItem).toList();
    final skipped = items.length - copyable.length;
    final verb = removeOriginals ? '옮기' : '복사하';
    if (copyable.isEmpty) {
      setState(() => _statusMessage = '$verb지 못했습니다: 고른 자료는 원본 경로나 내용이 없어(캡처·서식 텍스트 등) 복사할 수 없습니다.');
      return;
    }
    List<Rect> placed;
    if (target.id == current.id) {
      placed = _occupied(space);
    } else {
      try {
        final targetItems = (await widget.api.listItems(target.id)).where((i) => i.space == space).toList();
        placed = LibraryLayout.resolve(targetItems, width: _spaceWidths[space]).values.map(LibraryLayout.rectAt).toList();
      } catch (error) {
        if (mounted) setState(() => _statusMessage = '$verb지 못했습니다: ${_errorText(error)}');
        return;
      }
    }
    final created = <String, String>{}; // 원본 id → 사본 id
    try {
      for (final item in copyable) {
        final p = LibraryLayout.freeSlot(_displayOf(item), placed, width: _spaceWidths[space]);
        placed.add(LibraryLayout.rectAt(p));
        final copy = await widget.api.addItem(
          boxId: target.id,
          kind: item.kind,
          title: target.id == current.id && !removeOriginals ? '${item.title} (사본)' : item.title,
          space: space,
          x: p.dx,
          y: p.dy,
          source: item.source,
          text: item.text,
        );
        created[item.id] = copy.id;
      }
    } catch (error) {
      for (final id in created.values) {
        try {
          await widget.api.deleteItem(id);
        } catch (_) {}
      }
      await _reload();
      if (mounted) setState(() => _statusMessage = '$verb지 못해 처음 상태로 되돌렸습니다: ${_errorText(error)}');
      return;
    }
    var failed = 0;
    if (removeOriginals) {
      for (final item in copyable) {
        try {
          await widget.api.deleteItem(item.id);
        } catch (_) {
          // 원본 등록을 지우지 못하면 그 자료의 사본을 지워 중복을 남기지 않는다.
          failed++;
          try {
            await widget.api.deleteItem(created[item.id]!);
          } catch (_) {}
        }
      }
    }
    _selectedIds.clear();
    await _reload();
    if (!mounted) return;
    final done = copyable.length - failed;
    final where = target.id == current.id ? _spaceNames[space]! : '“${target.name}” 자료함 ${_spaceNames[space]}';
    setState(() => _statusMessage = '자료 $done개를 $where(으)로 ${removeOriginals ? '옮겼습니다' : '복사했습니다'}'
        '${failed > 0 ? ', $failed개는 옮기지 못했습니다' : ''}'
        '${skipped > 0 ? ', $skipped개는 원본 경로나 내용이 없어 제외했습니다' : ''}.');
  }

  Future<void> _deleteRelation(String id) async {
    await widget.api.deleteRelation(id);
    await _reload();
  }

  @override
  Widget build(BuildContext context) => Shortcuts(
        shortcuts: {
          LogicalKeySet(LogicalKeyboardKey.control, LogicalKeyboardKey.keyV): const _LibraryPasteIntent(),
          const SingleActivator(LogicalKeyboardKey.keyA, control: true): const _LibrarySelectAllIntent(),
          const SingleActivator(LogicalKeyboardKey.delete): const _LibraryDeleteSelectionIntent(),
          const SingleActivator(LogicalKeyboardKey.escape): const _LibraryClearSelectionIntent(),
        },
        child: Actions(
          actions: {
            _LibraryPasteIntent: CallbackAction<_LibraryPasteIntent>(onInvoke: (_) { _paste(); return null; }),
            _LibrarySelectAllIntent: _LibraryKeyAction<_LibrarySelectAllIntent>(_selectAllInActiveSpace),
            _LibraryDeleteSelectionIntent: _LibraryKeyAction<_LibraryDeleteSelectionIntent>(() => unawaited(_deleteSelection())),
            _LibraryClearSelectionIntent: _LibraryKeyAction<_LibraryClearSelectionIntent>(_clearSelection),
          },
          child: Focus(
            autofocus: true,
            focusNode: _rootFocus,
            child: LayoutBuilder(builder: (context, constraints) => Scaffold(
              body: _statusMessage != null && _boxes.isEmpty
                  ? Center(child: Padding(
                      padding: const EdgeInsets.all(24),
                      child: Text(_statusMessage!, key: const ValueKey('library-engine-error')),
                    ))
                  : Row(children: [
                if (constraints.maxWidth >= 760) ...[SizedBox(width: 260, child: _buildSidebar()), const VerticalDivider(width: 1)],
                Expanded(child: _selectedBox == null ? _buildEmptyState() : _buildWorkspace()),
              ]),
            )),
          ),
        ),
      );

  Widget _buildSidebar() => Material(
        color: Colors.white,
        child: Padding(
          padding: const EdgeInsets.all(12),
          child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
            const Text('자료함', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
            const SizedBox(height: 12),
            Row(children: [
              Expanded(child: TextField(
                key: const ValueKey('libraryAddBoxName'),
                controller: _newBoxController,
                decoration: const InputDecoration(hintText: '자료함 이름', isDense: true, border: OutlineInputBorder()),
                onSubmitted: (_) => _createBox(),
              )),
              const SizedBox(width: 6),
              ElevatedButton(key: const ValueKey('libraryAddBoxSubmit'), onPressed: _createBox, child: const Text('생성')),
            ]),
            const Divider(),
            Expanded(child: _boxes.isEmpty
                ? const Center(child: Text('자료함이 없습니다.\n새 자료함을 만드세요.', textAlign: TextAlign.center))
                : ListView(children: [for (final box in _boxes) ListTile(
                    key: ValueKey('libraryBox-${box.id}'),
                    title: Text(box.name),
                    selected: _selectedBox?.id == box.id,
                    onTap: () => _selectBox(box),
                  )])),
          ]),
        ),
      );

  Widget _buildEmptyState() => Center(child: Column(mainAxisSize: MainAxisSize.min, children: [
        const Text('자료함을 선택하거나 새로 만드세요.'),
        const SizedBox(height: 12),
        ElevatedButton(
          key: const ValueKey('libraryEmptyStateCta'),
          onPressed: () { _newBoxController.text = '새 자료함'; _createBox(); },
          child: const Text('새 자료함 만들기'),
        ),
      ]));

  Widget _buildWorkspace() => Column(children: [
        Padding(
          padding: const EdgeInsets.all(8),
          child: Wrap(crossAxisAlignment: WrapCrossAlignment.center, spacing: 8, runSpacing: 6, children: [
            if (MediaQuery.sizeOf(context).width < 760) SizedBox(width: 190, child: DropdownButton<LibraryBox>(
              key: const ValueKey('libraryCompactBoxSelector'), isExpanded: true, value: _selectedBox,
              items: [for (final b in _boxes) DropdownMenuItem(value: b, child: Text(b.name, overflow: TextOverflow.ellipsis))], onChanged: (b) { if (b != null) _selectBox(b); },
            )),
            if (MediaQuery.sizeOf(context).width < 760) IconButton(
              key: const ValueKey('libraryCompactAddBox'),
              tooltip: '새 자료함',
              onPressed: _createBox,
              icon: const Icon(Icons.create_new_folder_outlined),
            ),
            Text(_selectedBox!.name, style: const TextStyle(fontWeight: FontWeight.bold)),
            IconButton(key: const ValueKey('libraryRenameBox'), tooltip: '자료함 이름 바꾸기', onPressed: _renameBox, icon: const Icon(Icons.edit_outlined)),
            IconButton(key: const ValueKey('libraryDeleteBox'), tooltip: '자료함 삭제', onPressed: _deleteBox, icon: const Icon(Icons.delete_outline)),
            OutlinedButton(key: const ValueKey('libraryExportBox'), onPressed: _exportBox, child: const Text('물리 폴더로 전환')),
            if (_scanApi != null)
              OutlinedButton(
                key: const ValueKey('libraryScanFolder'),
                onPressed: (_scanStatus?.isScanning ?? false) ? null : _startScan,
                child: const Text('폴더 스캔'),
              ),
            SizedBox(width: 190, height: 38, child: TextField(
              key: const ValueKey('librarySearch'),
              controller: _searchController,
              decoration: const InputDecoration(prefixIcon: Icon(Icons.search), hintText: '자료 검색', isDense: true),
              onChanged: _search,
            )),
            SizedBox(width: 180, height: 38, child: TextField(
              key: const ValueKey('libraryNewItemText'),
              controller: _newItemController,
              decoration: const InputDecoration(hintText: '메모 / 텍스트 자료', isDense: true),
              onSubmitted: (_) => _addText(),
            )),
            ElevatedButton(key: const ValueKey('libraryAddItemSubmit'), onPressed: () => _addText(), child: const Text('자료 추가')),
            OutlinedButton.icon(
              key: const ValueKey('libraryAddMemo'),
              onPressed: _addMemo,
              icon: const Icon(Icons.note_add_outlined, size: 18),
              label: Text(_memoDraft == null ? '+메모' : '+메모(초안)'),
            ),
            OutlinedButton(key: const ValueKey('libraryPaste'), onPressed: _paste, child: const Text('붙여넣기')),
            const Text('각 공간에 파일을 끌어 놓으세요. Ctrl+클릭으로 여러 개를 고릅니다.'),
          ]),
        ),
        if (_showSearchResults && _searchResults.isNotEmpty) SizedBox(height: 72, child: ListView.builder(
          key: const ValueKey('librarySearchResults'), itemCount: _searchResults.length,
          itemBuilder: (context, index) { final result = _searchResults[index]; return ListTile(
            dense: true, key: ValueKey('librarySearchResult-$index'), title: Text(result.name), subtitle: Text(result.snippet, maxLines: 2, overflow: TextOverflow.ellipsis),
            onTap: () => _jumpToSearchResult(result),
          ); },
        )),
        _buildScanPanel(),
        if (_statusMessage != null) Text(_statusMessage!, key: const ValueKey('libraryStatus')),
        if (_selectedIds.isNotEmpty) _buildSelectionBar(),
        Expanded(child: _buildQuadrants()),
      ]);

  Widget _buildSelectionBar() {
    final enabled = !_batchBusy;
    return Container(
      key: const ValueKey('librarySelectionBar'),
      width: double.infinity,
      color: const Color(0xFFE3F2FD),
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
      child: Wrap(crossAxisAlignment: WrapCrossAlignment.center, spacing: 4, children: [
        Text('${_selectedIds.length}개 선택', key: const ValueKey('librarySelectionCount'), style: const TextStyle(fontWeight: FontWeight.bold)),
        PopupMenuButton<LibrarySpace>(
          key: const ValueKey('librarySelectionMove'),
          enabled: enabled,
          tooltip: '고른 자료를 다른 영역으로 이동',
          onSelected: _moveSelectionToSpace,
          itemBuilder: (context) => [
            for (final space in LibrarySpace.values)
              PopupMenuItem(key: ValueKey('librarySelectionMove-${space.name}'), value: space, child: Text('${_spaceNames[space]}(으)로 이동')),
          ],
          child: const Padding(
            padding: EdgeInsets.symmetric(horizontal: 8, vertical: 6),
            child: Row(mainAxisSize: MainAxisSize.min, children: [Icon(Icons.drive_file_move_outline, size: 18), SizedBox(width: 4), Text('영역 이동')]),
          ),
        ),
        TextButton.icon(key: const ValueKey('librarySelectionTransfer'), onPressed: enabled ? _transferSelection : null, icon: const Icon(Icons.copy_all_outlined, size: 18), label: const Text('이동·복사…')),
        TextButton.icon(key: const ValueKey('librarySelectionOpen'), onPressed: enabled ? _openSelection : null, icon: const Icon(Icons.open_in_new, size: 18), label: const Text('열기')),
        TextButton.icon(key: const ValueKey('librarySelectionCopyPath'), onPressed: enabled ? _copySelectionPaths : null, icon: const Icon(Icons.content_copy, size: 18), label: const Text('경로 복사')),
        TextButton.icon(key: const ValueKey('librarySelectionDelete'), onPressed: enabled ? _deleteSelection : null, icon: const Icon(Icons.delete_outline, size: 18), label: const Text('삭제')),
        TextButton(key: const ValueKey('librarySelectionClear'), onPressed: _clearSelection, child: const Text('선택 해제')),
      ]),
    );
  }

  Widget _buildQuadrants() => LayoutBuilder(builder: (context, constraints) => Column(children: [
        Expanded(child: Row(children: [
          for (final space in [LibrarySpace.core, LibrarySpace.basis])
            Expanded(child: _quadrant(space)),
        ])),
        const Divider(height: 1),
        Expanded(child: Row(children: [
          for (final space in [LibrarySpace.reference, LibrarySpace.temp])
            Expanded(child: _quadrant(space)),
        ])),
      ]));

  Widget _quadrant(LibrarySpace space) {
    return _LibraryQuadrant(
      key: ValueKey('librarySpace-${space.name}'),
      space: space,
      title: _spaceNames[space]!,
      items: _items.where((item) => item.space == space).toList(),
      relations: space == LibrarySpace.core ? _relations : const [],
      selectedIds: _selectedIds,
      cardWidth: _cardWidth,
      cardHeight: _cardHeight,
      onItemTap: _tapItem,
      onMoveItem: _moveItem,
      onFileDrop: _addFile,
      canvasKey: _spaceKeys[space]!,
      onDeleteRelation: _deleteRelation,
      onEditRelation: _editRelationLabel,
      onRenameItem: _renameItem,
      onDeleteItem: _deleteItem,
      onOpenItem: _openItem,
      onMoveToSpace: _moveItemToSpace,
      onAddToNotebook: widget.notebookApi == null ? null : _addToNotebook,
      highlightedItemId: _highlightedItemId,
      onBackgroundTap: () {
        _rootFocus.requestFocus();
        _activeSpace = space;
        _clearSelection();
      },
      onWidth: (width) => _spaceWidths[space] = width,
      onArrange: (order) => _arrange(space, order),
    );
  }
}

class _TransferRequest {
  const _TransferRequest({required this.box, required this.space, required this.copy});
  final LibraryBox box;
  final LibrarySpace space;
  final bool copy;
}

class _TransferDialog extends StatefulWidget {
  const _TransferDialog({required this.boxes, required this.current, required this.count});
  final List<LibraryBox> boxes;
  final LibraryBox current;
  final int count;

  @override
  State<_TransferDialog> createState() => _TransferDialogState();
}

class _TransferDialogState extends State<_TransferDialog> {
  late LibraryBox _box = widget.boxes.where((b) => b.id == widget.current.id).firstOrNull ?? widget.current;
  LibrarySpace _space = LibrarySpace.core;

  @override
  Widget build(BuildContext context) => AlertDialog(
        key: const ValueKey('libraryTransferDialog'),
        title: Text('자료 ${widget.count}개 이동·복사'),
        content: Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.start, children: [
          const Text('보낼 자료함'),
          DropdownButton<LibraryBox>(
            key: const ValueKey('libraryTransferBox'),
            isExpanded: true,
            value: _box,
            items: [
              for (final b in widget.boxes)
                DropdownMenuItem(value: b, child: Text(b.id == widget.current.id ? '${b.name}(현재 자료함)' : b.name, overflow: TextOverflow.ellipsis)),
            ],
            onChanged: (b) { if (b != null) setState(() => _box = b); },
          ),
          const SizedBox(height: 8),
          const Text('보낼 영역'),
          DropdownButton<LibrarySpace>(
            key: const ValueKey('libraryTransferSpace'),
            isExpanded: true,
            value: _space,
            items: [for (final s in LibrarySpace.values) DropdownMenuItem(value: s, child: Text(_spaceNames[s]!))],
            onChanged: (s) { if (s != null) setState(() => _space = s); },
          ),
          const SizedBox(height: 8),
          const Text('원본 파일은 옮기거나 복사하지 않고 자료함 등록만 바뀝니다.', style: TextStyle(fontSize: 12, color: Colors.black54)),
        ]),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: const Text('취소')),
          TextButton(
            key: const ValueKey('libraryTransferCopy'),
            onPressed: () => Navigator.pop(context, _TransferRequest(box: _box, space: _space, copy: true)),
            child: const Text('복사'),
          ),
          TextButton(
            key: const ValueKey('libraryTransferMove'),
            onPressed: () => Navigator.pop(context, _TransferRequest(box: _box, space: _space, copy: false)),
            child: const Text('이동'),
          ),
        ],
      );
}

class _LibraryQuadrant extends StatefulWidget {
  const _LibraryQuadrant({
    super.key,
    required this.space,
    required this.title,
    required this.items,
    required this.relations,
    required this.selectedIds,
    required this.cardWidth,
    required this.cardHeight,
    required this.onItemTap,
    required this.onMoveItem,
    required this.onFileDrop,
    required this.canvasKey,
    required this.onDeleteRelation,
    required this.onEditRelation,
    required this.onRenameItem,
    required this.onDeleteItem,
    required this.onOpenItem,
    required this.onMoveToSpace,
    required this.highlightedItemId,
    required this.onBackgroundTap,
    required this.onWidth,
    required this.onArrange,
    this.onAddToNotebook,
  });

  final LibrarySpace space;
  final String title;
  final List<LibraryItem> items;
  final List<LibraryRelation> relations;
  final Set<String> selectedIds;
  final double cardWidth;
  final double cardHeight;
  final ValueChanged<LibraryItem> onItemTap;
  final Future<void> Function(LibraryItem, LibrarySpace, Offset, Size) onMoveItem;
  final Future<void> Function(LibraryFileDrop, LibrarySpace, Offset) onFileDrop;
  final GlobalKey canvasKey;
  final ValueChanged<String> onDeleteRelation;
  final ValueChanged<LibraryRelation> onEditRelation;
  final ValueChanged<LibraryItem> onRenameItem;
  final ValueChanged<LibraryItem> onDeleteItem;
  final ValueChanged<LibraryItem> onOpenItem;
  final void Function(LibraryItem, LibrarySpace) onMoveToSpace;
  final String? highlightedItemId;
  final ValueChanged<LibraryItem>? onAddToNotebook;
  final VoidCallback onBackgroundTap;
  final ValueChanged<double> onWidth;
  final ValueChanged<LibraryArrangeOrder> onArrange;

  @override
  State<_LibraryQuadrant> createState() => _LibraryQuadrantState();
}

class _LibraryQuadrantState extends State<_LibraryQuadrant> {
  final _scroll = ScrollController();
  String? _hoveredId;

  @override
  void dispose() {
    _scroll.dispose();
    super.dispose();
  }

  void _showArrangeMenu(BuildContext context, Offset at) {
    final overlay = Overlay.of(context).context.findRenderObject();
    if (overlay is! RenderBox) return;
    final local = overlay.globalToLocal(at);
    showMenu<LibraryArrangeOrder>(
      context: context,
      position: RelativeRect.fromRect(local & const Size(1, 1), Offset.zero & overlay.size),
      items: const [
        PopupMenuItem(key: ValueKey('libraryArrangeAdded'), value: LibraryArrangeOrder.added, child: Text('추가순으로 정리')),
        PopupMenuItem(key: ValueKey('libraryArrangeName'), value: LibraryArrangeOrder.name, child: Text('이름순으로 정리')),
        PopupMenuItem(key: ValueKey('libraryArrangeKind'), value: LibraryArrangeOrder.kind, child: Text('종류순으로 정리')),
      ],
    ).then((order) {
      if (order != null) widget.onArrange(order);
    });
  }

  bool _isSelected(LibraryItem item) => widget.selectedIds.contains(item.id) || widget.highlightedItemId == item.id;

  @override
  Widget build(BuildContext context) {
    final space = widget.space;
    final items = widget.items;
    final cardWidth = widget.cardWidth;
    final cardHeight = widget.cardHeight;
    return Container(
      decoration: BoxDecoration(border: Border.all(color: Colors.black12), color: _spaceColor(space)),
      child: Column(children: [
        Padding(
          padding: const EdgeInsets.all(6),
          child: Row(children: [
            Text(widget.title, style: const TextStyle(fontWeight: FontWeight.bold)),
            const Spacer(),
            Text('${items.length}개'),
            const SizedBox(width: 4),
            Tooltip(
              message: '겹치지 않게 정리',
              child: InkWell(
                key: ValueKey('libraryArrange-${space.name}'),
                onTapDown: (details) => _showArrangeMenu(context, details.globalPosition),
                child: const Padding(padding: EdgeInsets.symmetric(horizontal: 2), child: Icon(Icons.grid_view, size: 16)),
              ),
            ),
          ]),
        ),
        Expanded(child: LayoutBuilder(builder: (context, constraints) {
          final viewport = Size(constraints.maxWidth, constraints.maxHeight);
          widget.onWidth(viewport.width);
          // 화면 폭에 맞춰 겹치지 않게 그릴 위치(저장 좌표는 그대로 두고 표시만 정리).
          final positions = LibraryLayout.resolve(items, width: viewport.width);
          final shown = [
            for (final item in items) item.copyWith(x: positions[item.id]!.dx, y: positions[item.id]!.dy),
          ];
          final contentHeight = math.max(viewport.height, LibraryLayout.contentHeight(positions.values));
          final size = Size(viewport.width, contentHeight);
          // 고른 카드·마우스를 올린 카드를 맨 위로 그린다.
          int rank(LibraryItem i) => _isSelected(i) ? 2 : (i.id == _hoveredId ? 1 : 0);
          final ordered = [for (var r = 0; r <= 2; r++) ...shown.where((i) => rank(i) == r)];
          return ScrollConfiguration(
            // 마우스·터치 끌기는 카드 이동에 쓰고, 영역 스크롤은 휠·스크롤 막대로 한다.
            behavior: ScrollConfiguration.of(context).copyWith(dragDevices: const <PointerDeviceKind>{}),
            child: Scrollbar(
              controller: _scroll,
              child: SingleChildScrollView(
                key: ValueKey('libraryScroll-${space.name}'),
                controller: _scroll,
                child: SizedBox(
                  width: viewport.width,
                  height: contentHeight,
                  child: DragTarget<Object>(
                    key: widget.canvasKey,
                    onWillAcceptWithDetails: (details) => details.data is LibraryItem || details.data is LibraryFileDrop,
                    onAcceptWithDetails: (details) {
                      final box = widget.canvasKey.currentContext?.findRenderObject();
                      final local = box is RenderBox ? box.globalToLocal(details.offset) : Offset.zero;
                      if (details.data is LibraryItem) {
                        widget.onMoveItem(details.data as LibraryItem, space, local, size);
                      } else {
                        widget.onFileDrop(details.data as LibraryFileDrop, space, details.offset);
                      }
                    },
                    builder: (context, candidates, rejected) => Stack(
                      clipBehavior: Clip.hardEdge,
                      children: [
                        // 빈 공간에서도 끌어 놓기를 받고, 빈 곳을 누르면 선택을 푼다.
                        Positioned.fill(child: GestureDetector(
                          key: ValueKey('libraryBackground-${space.name}'),
                          behavior: HitTestBehavior.opaque,
                          onTap: widget.onBackgroundTap,
                          child: const ColoredBox(color: Colors.transparent),
                        )),
                        if (space == LibrarySpace.core && widget.relations.isNotEmpty)
                          CustomPaint(
                            key: const ValueKey('libraryRelationPainter'),
                            size: size,
                            painter: _RelationPainter(relations: widget.relations, items: shown, cardWidth: cardWidth, cardHeight: cardHeight),
                          ),
                        for (final item in ordered) _card(item, items.firstWhere((i) => i.id == item.id)),
                        if (space == LibrarySpace.core)
                          for (final relation in widget.relations) _relationLabel(relation, shown, size),
                        if (items.isEmpty) const Center(child: Text('자료가 없습니다.', style: TextStyle(color: Colors.black45))),
                      ],
                    ),
                  ),
                ),
              ),
            ),
          );
        })),
      ]),
    );
  }

  Widget _card(LibraryItem shown, LibraryItem item) {
    final cardWidth = widget.cardWidth;
    final cardHeight = widget.cardHeight;
    final dragCount = widget.selectedIds.contains(item.id) ? widget.selectedIds.length : 1;
    return Positioned(
      key: ValueKey('libraryCardSlot-${item.id}'),
      left: shown.x,
      top: shown.y,
      child: MouseRegion(
        onEnter: (_) => setState(() => _hoveredId = item.id),
        onExit: (_) { if (_hoveredId == item.id) setState(() => _hoveredId = null); },
        child: Draggable<LibraryItem>(
          data: item,
          feedback: Material(
            color: Colors.transparent,
            child: Stack(clipBehavior: Clip.none, children: [
              _LibraryCard(item: item, width: cardWidth, height: cardHeight, selected: dragCount > 1),
              if (dragCount > 1)
                Positioned(right: -6, top: -6, child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                  decoration: BoxDecoration(color: Colors.blue, borderRadius: BorderRadius.circular(10)),
                  child: Text('$dragCount개', style: const TextStyle(color: Colors.white, fontSize: 12)),
                )),
            ]),
          ),
          childWhenDragging: Opacity(opacity: .2, child: _LibraryCard(item: item, width: cardWidth, height: cardHeight, selected: false)),
          child: _LibraryCard(
            key: ValueKey('libraryItem-${item.id}'),
            item: item,
            width: cardWidth,
            height: cardHeight,
            selected: _isSelected(item),
            onTap: () => widget.onItemTap(item),
            onDoubleTap: () => widget.onOpenItem(item),
            onOpen: () => widget.onOpenItem(item),
            onRename: () => widget.onRenameItem(item),
            onDelete: () => widget.onDeleteItem(item),
            onMoveToSpace: (space) => widget.onMoveToSpace(item, space),
            onAddToNotebook: widget.onAddToNotebook == null ? null : () => widget.onAddToNotebook!(item),
          ),
        ),
      ),
    );
  }

  Widget _relationLabel(LibraryRelation relation, List<LibraryItem> items, Size size) {
    final cardWidth = widget.cardWidth;
    final cardHeight = widget.cardHeight;
    final from = items.where((item) => item.id == relation.fromItemId).firstOrNull;
    final to = items.where((item) => item.id == relation.toItemId).firstOrNull;
    if (from == null || to == null) return const SizedBox.shrink();
    final center = Offset((from.x + to.x + cardWidth) / 2, (from.y + to.y + cardHeight) / 2);
    return Positioned(
      left: center.dx.clamp(0.0, math.max(0.0, size.width - 110)),
      top: center.dy.clamp(0.0, math.max(0.0, size.height - 36)),
      child: Material(color: Colors.white.withValues(alpha: .9), borderRadius: BorderRadius.circular(12), child: Row(mainAxisSize: MainAxisSize.min, children: [
        InkWell(key: ValueKey('libraryRelation-${relation.id}'), onTap: () => widget.onEditRelation(relation), child: Padding(padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2), child: Text(relation.label?.isNotEmpty == true ? relation.label! : '관계'))),
        IconButton(key: ValueKey('libraryRelationDelete-${relation.id}'), tooltip: '관계선 삭제', onPressed: () => widget.onDeleteRelation(relation.id), constraints: const BoxConstraints.tightFor(width: 26, height: 26), padding: EdgeInsets.zero, icon: const Icon(Icons.close, size: 14)),
      ])),
    );
  }

  Color _spaceColor(LibrarySpace space) => switch (space) {
        LibrarySpace.core => const Color(0xFFF0F5FF),
        LibrarySpace.basis => const Color(0xFFF4F7F0),
        LibrarySpace.reference => const Color(0xFFFFF8EA),
        LibrarySpace.temp => const Color(0xFFF5F1F8),
      };
}

class _LibraryCard extends StatelessWidget {
  const _LibraryCard({super.key, required this.item, required this.width, required this.height, required this.selected, this.onTap, this.onDoubleTap, this.onOpen, this.onRename, this.onDelete, this.onMoveToSpace, this.onAddToNotebook});
  final LibraryItem item;
  final double width;
  final double height;
  final bool selected;
  final VoidCallback? onTap;
  final VoidCallback? onDoubleTap;
  final VoidCallback? onOpen;
  final VoidCallback? onRename;
  final VoidCallback? onDelete;
  final ValueChanged<LibrarySpace>? onMoveToSpace;
  final VoidCallback? onAddToNotebook;

  /// 메뉴가 있는 카드(드래그 미리보기 카드에는 없다).
  bool get _hasMenu => onRename != null || onDelete != null || onMoveToSpace != null || onAddToNotebook != null;

  IconData get _icon => switch (item.kind) {
    LibraryItemKind.file => Icons.insert_drive_file_outlined, LibraryItemKind.folder => Icons.folder_outlined,
    LibraryItemKind.link => Icons.link, LibraryItemKind.text => Icons.notes, LibraryItemKind.richText => Icons.article_outlined,
    LibraryItemKind.image || LibraryItemKind.capture => Icons.image_outlined, LibraryItemKind.note => Icons.sticky_note_2_outlined,
  };

  @override
  Widget build(BuildContext context) => SizedBox(
        width: width,
        height: height,
        child: Card(
          elevation: selected ? 5 : 2,
          color: selected ? const Color(0xFFE3F2FD) : null,
          shape: RoundedRectangleBorder(
            side: BorderSide(color: selected ? Colors.blue : Colors.white, width: selected ? 2 : 1),
            borderRadius: BorderRadius.circular(8),
          ),
          child: InkWell(
            onTap: onTap,
            onDoubleTap: onDoubleTap,
            onSecondaryTapUp: _hasMenu ? (details) => _showMenu(context, details.globalPosition) : null,
            onLongPress: _hasMenu ? () => _showMenu(context, null) : null,
            child: Padding(
              padding: EdgeInsets.fromLTRB(8, 8, _hasMenu ? 0 : 8, 8),
              child: Row(children: [
                Icon(selected ? Icons.check_circle : _icon, size: 20, color: selected ? Colors.blue : null),
                const SizedBox(width: 6),
                Expanded(child: Text(item.title, maxLines: 2, overflow: TextOverflow.ellipsis)),
                if (_hasMenu)
                  Builder(builder: (buttonContext) => IconButton(
                    key: ValueKey('libraryItemMenu-${item.id}'),
                    tooltip: '자료 메뉴',
                    onPressed: () => _showMenu(buttonContext, null),
                    constraints: const BoxConstraints.tightFor(width: 24, height: 32),
                    padding: EdgeInsets.zero,
                    iconSize: 18,
                    icon: const Icon(Icons.more_vert),
                  )),
              ]),
            ),
          ),
        ),
      );

  /// 항목 메뉴. [at]이 있으면 그 화면 위치(오른쪽 클릭), 없으면 [context] 위젯 옆에 연다.
  void _showMenu(BuildContext context, Offset? at) {
    final overlay = Overlay.of(context).context.findRenderObject();
    final box = context.findRenderObject();
    var position = const RelativeRect.fromLTRB(80, 80, 0, 0);
    if (overlay is RenderBox && at != null) {
      final local = overlay.globalToLocal(at);
      position = RelativeRect.fromRect(local & const Size(1, 1), Offset.zero & overlay.size);
    } else if (overlay is RenderBox && box is RenderBox && box.hasSize) {
      final topLeft = box.localToGlobal(Offset.zero, ancestor: overlay);
      position = RelativeRect.fromRect(topLeft & box.size, Offset.zero & overlay.size);
    }
    showMenu<String>(context: context, position: position, items: [
      if (onOpen != null)
        const PopupMenuItem(key: ValueKey('libraryMenuOpen'), value: 'open', child: Text('열기')),
      if (onAddToNotebook != null)
        const PopupMenuItem(key: ValueKey('libraryMenuAddToNotebook'), value: 'notebook', child: Text('노트북에 출처로 추가')),
      const PopupMenuItem(value: 'rename', child: Text('이름 바꾸기')), const PopupMenuItem(value: 'delete', child: Text('삭제')),
      const PopupMenuItem(value: 'core', child: Text('핵심자료로 이동')), const PopupMenuItem(value: 'basis', child: Text('기초자료로 이동')),
      const PopupMenuItem(value: 'reference', child: Text('참고자료로 이동')), const PopupMenuItem(value: 'temp', child: Text('임시저장소로 이동')),
    ]).then((action) {
      if (action == 'open') onOpen?.call();
      if (action == 'notebook') onAddToNotebook?.call();
      if (action == 'rename') onRename?.call();
      if (action == 'delete') onDelete?.call();
      for (final space in LibrarySpace.values) { if (action == space.name) onMoveToSpace?.call(space); }
    });
  }
}

class _RelationPainter extends CustomPainter {
  _RelationPainter({required this.relations, required this.items, required this.cardWidth, required this.cardHeight});
  final List<LibraryRelation> relations;
  final List<LibraryItem> items;
  final double cardWidth;
  final double cardHeight;

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()..color = Colors.indigo..strokeWidth = 2..style = PaintingStyle.stroke;
    for (final relation in relations) {
      final from = items.where((item) => item.id == relation.fromItemId).firstOrNull;
      final to = items.where((item) => item.id == relation.toItemId).firstOrNull;
      if (from == null || to == null) continue;
      final a = Offset(from.x + cardWidth / 2, from.y + cardHeight / 2);
      final b = Offset(to.x + cardWidth / 2, to.y + cardHeight / 2);
      canvas.drawLine(a, b, paint);
    }
  }

  @override
  bool shouldRepaint(covariant _RelationPainter oldDelegate) =>
      oldDelegate.relations != relations || oldDelegate.items != items;
}

/// '노트북에 출처로 추가'에서 노트북을 고르는 창. 노트북이 없으면 이름을 넣어 새로 만들 수 있다.
class _NotebookPickDialog extends StatefulWidget {
  const _NotebookPickDialog({required this.api, required this.itemTitle});
  final NotebookApi api;
  final String itemTitle;

  @override
  State<_NotebookPickDialog> createState() => _NotebookPickDialogState();
}

class _NotebookPickDialogState extends State<_NotebookPickDialog> {
  final _nameController = TextEditingController(text: '새 노트북');
  List<Notebook> _notebooks = [];
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    unawaited(_load());
  }

  @override
  void dispose() {
    _nameController.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    try {
      final list = await widget.api.listNotebooks();
      if (mounted) setState(() => _notebooks = list);
    } catch (error) {
      if (mounted) setState(() => _error = _errorText(error));
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _create() async {
    final name = _nameController.text.trim();
    if (name.isEmpty) return;
    try {
      final id = await widget.api.createNotebook(name);
      if (mounted) Navigator.of(context).pop(Notebook(id: id, name: name));
    } catch (error) {
      if (mounted) setState(() => _error = _errorText(error));
    }
  }

  @override
  Widget build(BuildContext context) => AlertDialog(
        title: const Text('노트북에 출처로 추가'),
        content: SizedBox(
          width: 400,
          height: 300,
          child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
            Text('“${widget.itemTitle}”을(를) 넣을 노트북을 고르세요.', maxLines: 2, overflow: TextOverflow.ellipsis),
            const SizedBox(height: 8),
            if (_loading) const LinearProgressIndicator(minHeight: 2),
            if (_error != null) Text(_error!, key: const ValueKey('libraryNbPickError'), style: const TextStyle(color: Colors.red)),
            Expanded(
              child: !_loading && _notebooks.isEmpty
                  ? const Center(child: Text('노트북이 없습니다. 아래에서 새로 만드세요.'))
                  : ListView(children: [
                      for (final nb in _notebooks)
                        ListTile(
                          key: ValueKey('libraryNbPick-${nb.id}'),
                          dense: true,
                          leading: const Icon(Icons.menu_book_outlined, size: 18),
                          title: Text(nb.name, overflow: TextOverflow.ellipsis),
                          onTap: () => Navigator.of(context).pop(nb),
                        ),
                    ]),
            ),
            Row(children: [
              Expanded(child: TextField(
                key: const ValueKey('libraryNbPickNewName'),
                controller: _nameController,
                decoration: const InputDecoration(labelText: '새 노트북 이름', isDense: true),
                onSubmitted: (_) => _create(),
              )),
              const SizedBox(width: 8),
              TextButton(key: const ValueKey('libraryNbPickCreate'), onPressed: _create, child: const Text('만들어 추가')),
            ]),
          ]),
        ),
        actions: [TextButton(onPressed: () => Navigator.of(context).pop(), child: const Text('취소'))],
      );
}
