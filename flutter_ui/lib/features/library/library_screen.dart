import 'dart:async';
import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:file_selector/file_selector.dart';

import '../../core/drop_events.dart';
import 'library_api.dart';

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

class LibraryScreen extends StatefulWidget {
  const LibraryScreen({
    super.key,
    required this.api,
    this.clipboardReader,
    this.scanApi,
    this.folderPicker,
    this.scanPollInterval = const Duration(milliseconds: 400),
    this.watchDropEvents,
  });

  /// 창에 파일을 놓았다는 알림 구독(시험에서 대체). 기본은 'docfit-library-files-dropped' 창 이벤트.
  final void Function() Function(void Function() onDrop)? watchDropEvents;

  final LibraryApi api;
  final LibraryClipboardReader? clipboardReader;

  /// 폴더 스캔 API. 생략하면 `api`가 `LibraryScanApi`일 때 그것을 쓰고, 아니면 스캔 단추를 숨긴다.
  final LibraryScanApi? scanApi;

  /// 스캔할 폴더 선택 창(시험에서 대체). 기본은 file_selector의 getDirectoryPath.
  final Future<String?> Function()? folderPicker;
  final Duration scanPollInterval;

  @override
  State<LibraryScreen> createState() => _LibraryScreenState();
}

class _LibraryScreenState extends State<LibraryScreen> {
  late final LibraryClipboardReader _clipboardReader =
      widget.clipboardReader ?? DefaultLibraryClipboardReader();
  final _newBoxController = TextEditingController();
  final _searchController = TextEditingController();
  final _newItemController = TextEditingController();
  final _spaceKeys = {for (final space in LibrarySpace.values) space: GlobalKey()};
  final _searchResults = <LibrarySearchResult>[];
  String? _highlightedItemId;
  bool _showSearchResults = false;
  List<LibraryBox> _boxes = [];
  LibraryBox? _selectedBox;
  List<LibraryItem> _items = [];
  List<LibraryRelation> _relations = [];
  String? _selectedCoreItemId;
  String? _statusMessage;
  LibraryScanStatus? _scanStatus;
  Timer? _scanTimer;
  bool _scanPolling = false;
  static const _cardWidth = 140.0;
  static const _cardHeight = 72.0;

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
    setState(() {
      _boxes = boxes;
      _selectedBox ??= boxes.isEmpty ? null : boxes.first;
    });
    final selected = _selectedBox;
    if (selected != null) await _loadBoxContent(selected.id);
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
    setState(() {
      _items = items;
      _relations = relations;
    });
  }

  Future<void> _selectBox(LibraryBox box) async {
    if (_selectedBox?.id == box.id) return;
    setState(() {
      _selectedBox = box;
      _searchController.clear();
      _searchResults.clear();
      _highlightedItemId = null;
      _selectedCoreItemId = null;
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
    setState(() { _boxes.removeWhere((b) => b.id == box.id); _selectedBox = null; _items = []; _relations = []; });
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
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('저장 위치: $directory'), action: SnackBarAction(label: '열기', onPressed: () => _openPath(directory))));
  }

  Future<void> _openPath(String path) async {
    if (path.isNotEmpty && !path.contains('\n') && !path.contains('\r')) {
      try {
        await const MethodChannel('docfit/library').invokeMethod<void>('openPath', path);
      } on MissingPluginException {
        // Keep a copyable path dialog when no host opener is registered.
      }
    }
    if (!mounted) return;
    await showDialog<void>(context: context, builder: (context) => AlertDialog(
      title: const Text('자료 위치'), content: SelectableText(path),
      actions: [TextButton(onPressed: () => Navigator.pop(context), child: const Text('확인'))],
    ));
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
    await _openPath(result.path.isNotEmpty ? result.path : (match?.text ?? result.name));
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
    final box = _selectedBox;
    if (box != null) await _loadBoxContent(box.id);
  }

  Future<void> _deleteItem(LibraryItem item) async {
    final yes = await showDialog<bool>(context: context, builder: (context) => AlertDialog(
      title: const Text('자료 삭제'), content: Text('“${item.title}” 자료를 자료함에서 삭제할까요?'),
      actions: [TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('취소')),
        TextButton(onPressed: () => Navigator.pop(context, true), child: const Text('삭제'))],
    ));
    if (yes != true) return;
    await widget.api.deleteItem(item.id);
    final box = _selectedBox;
    if (box != null) await _loadBoxContent(box.id);
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
    final box = _selectedBox;
    if (box != null) await _loadBoxContent(box.id);
  }

  Future<void> _openItem(LibraryItem item) async {
    final value = item.source ?? item.text ?? item.title;
    await _openPath(value);
  }

  Future<void> _moveItemToSpace(LibraryItem item, LibrarySpace space) async {
    final box = _selectedBox;
    if (box == null) return;
    await widget.api.moveItem(item.id, boxId: box.id, space: space, x: item.x, y: item.y);
    await _loadBoxContent(box.id);
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
      _selectedCoreItemId = null;
    });
    await _loadBoxContent(box.id);
  }

  Offset _nextPosition(LibrarySpace space) {
    const margin = 16.0;
    const colStep = 150.0;
    const rowStep = 80.0;
    final occupied = _items.where((item) => item.space == space).toList();
    for (var row = 0; row < 1000; row++) {
      for (var col = 0; col < 1000; col++) {
        final point = Offset(margin + col * colStep, margin + row * rowStep);
        final rect = Rect.fromLTWH(point.dx, point.dy, _cardWidth, _cardHeight);
        if (!occupied.any((item) => rect.overlaps(
            Rect.fromLTWH(item.x, item.y, _cardWidth, _cardHeight)))) {
          return point;
        }
      }
    }
    throw StateError('빈 카드 배치 위치를 찾지 못했습니다.');
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
    final fallback = _nextPosition(space);
    final point = object is RenderBox && global != Offset.zero
        ? object.globalToLocal(global)
        : fallback;
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

  Future<void> _moveItem(LibraryItem item, LibrarySpace space, Offset offset, Size size) async {
    final box = _selectedBox;
    if (box == null) return;
    await widget.api.moveItem(
      item.id,
      boxId: box.id,
      space: space,
      x: offset.dx.clamp(0.0, math.max(0.0, size.width - _cardWidth)),
      y: offset.dy.clamp(0.0, math.max(0.0, size.height - _cardHeight)),
    );
    await _loadBoxContent(box.id);
  }

  Future<void> _tapItem(LibraryItem item) async {
    if (item.space != LibrarySpace.core) {
      setState(() => _selectedCoreItemId = null);
      return;
    }
    if (_selectedCoreItemId == null || _selectedCoreItemId == item.id) {
      setState(() => _selectedCoreItemId = _selectedCoreItemId == item.id ? null : item.id);
      return;
    }
    final box = _selectedBox;
    if (box != null) {
      final fromItemId = _selectedCoreItemId!;
      try {
        await widget.api.addRelation(box.id, fromItemId, item.id);
      } catch (error) {
        if (mounted) setState(() => _statusMessage = error.toString());
      }
      if (mounted) setState(() => _selectedCoreItemId = null);
      await _loadBoxContent(box.id);
    }
  }

  Future<void> _deleteRelation(String id) async {
    await widget.api.deleteRelation(id);
    final box = _selectedBox;
    if (box != null) await _loadBoxContent(box.id);
  }

  @override
  Widget build(BuildContext context) => Shortcuts(
        shortcuts: {
          LogicalKeySet(LogicalKeyboardKey.control, LogicalKeyboardKey.keyV): const _LibraryPasteIntent(),
        },
        child: Actions(
          actions: {
            _LibraryPasteIntent: CallbackAction<_LibraryPasteIntent>(onInvoke: (_) { _paste(); return null; }),
          },
          child: Focus(
            autofocus: true,
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
            OutlinedButton(key: const ValueKey('libraryPaste'), onPressed: _paste, child: const Text('붙여넣기')),
            const Text('각 공간에 파일을 끌어 놓으세요.'),
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
        Expanded(child: _buildQuadrants()),
      ]);

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
    final names = {
      LibrarySpace.core: '핵심자료',
      LibrarySpace.basis: '기초자료',
      LibrarySpace.reference: '참고자료',
      LibrarySpace.temp: '임시저장소',
    };
    return _LibraryQuadrant(
      key: ValueKey('librarySpace-${space.name}'),
      space: space,
      title: names[space]!,
      items: _items.where((item) => item.space == space).toList(),
      relations: space == LibrarySpace.core ? _relations : const [],
      selectedCoreItemId: space == LibrarySpace.core ? _selectedCoreItemId : null,
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
      highlightedItemId: _highlightedItemId,
    );
  }
}

class _LibraryQuadrant extends StatelessWidget {
  const _LibraryQuadrant({
    super.key,
    required this.space,
    required this.title,
    required this.items,
    required this.relations,
    required this.selectedCoreItemId,
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
  });

  final LibrarySpace space;
  final String title;
  final List<LibraryItem> items;
  final List<LibraryRelation> relations;
  final String? selectedCoreItemId;
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

  @override
  Widget build(BuildContext context) => Container(
        decoration: BoxDecoration(border: Border.all(color: Colors.black12), color: _spaceColor(space)),
        child: Column(children: [
          Padding(
            padding: const EdgeInsets.all(6),
            child: Row(children: [Text(title, style: const TextStyle(fontWeight: FontWeight.bold)), const Spacer(), Text('${items.length}개')]),
          ),
          Expanded(child: LayoutBuilder(builder: (context, constraints) {
            final size = Size(constraints.maxWidth, constraints.maxHeight);
            return DragTarget<Object>(
              key: canvasKey,
              onWillAcceptWithDetails: (details) => details.data is LibraryItem || details.data is LibraryFileDrop,
              onAcceptWithDetails: (details) {
                final box = canvasKey.currentContext?.findRenderObject();
                final local = box is RenderBox ? box.globalToLocal(details.offset) : Offset.zero;
                if (details.data is LibraryItem) {
                  onMoveItem(details.data as LibraryItem, space, local, size);
                } else {
                  onFileDrop(details.data as LibraryFileDrop, space, details.offset);
                }
              },
              builder: (context, candidates, rejected) => Stack(
                clipBehavior: Clip.hardEdge,
                children: [
                  // 빈 공간에서도 끌어 놓기를 받도록 공간 전체를 채운다.
                  const Positioned.fill(child: ColoredBox(color: Colors.transparent)),
                  if (space == LibrarySpace.core && relations.isNotEmpty)
                    CustomPaint(
                      key: const ValueKey('libraryRelationPainter'),
                      size: size,
                      painter: _RelationPainter(relations: relations, items: items, cardWidth: cardWidth, cardHeight: cardHeight),
                    ),
                  for (final item in items)
                    Positioned(
                      left: item.x.clamp(0.0, math.max(0.0, size.width - cardWidth)),
                      top: item.y.clamp(0.0, math.max(0.0, size.height - cardHeight)),
                      child: Draggable<LibraryItem>(
                        data: item,
                        feedback: Material(child: _LibraryCard(item: item, width: cardWidth, height: cardHeight, selected: false)),
                        childWhenDragging: Opacity(opacity: .2, child: _LibraryCard(item: item, width: cardWidth, height: cardHeight, selected: false)),
                        child: _LibraryCard(
                          key: ValueKey('libraryItem-${item.id}'),
                          item: item,
                          width: cardWidth,
                          height: cardHeight,
                          selected: selectedCoreItemId == item.id || highlightedItemId == item.id,
                          onTap: () => onItemTap(item),
                          onDoubleTap: () => onOpenItem(item),
                          onRename: () => onRenameItem(item),
                          onDelete: () => onDeleteItem(item),
                          onMoveToSpace: (space) => onMoveToSpace(item, space),
                        ),
                      ),
                    ),
                  if (space == LibrarySpace.core)
                    for (final relation in relations) _relationLabel(relation, items, size),
                  if (items.isEmpty) const Center(child: Text('자료가 없습니다.', style: TextStyle(color: Colors.black45))),
                ],
              ),
            );
          })),
        ]),
      );

  Widget _relationLabel(LibraryRelation relation, List<LibraryItem> items, Size size) {
    final from = items.where((item) => item.id == relation.fromItemId).firstOrNull;
    final to = items.where((item) => item.id == relation.toItemId).firstOrNull;
    if (from == null || to == null) return const SizedBox.shrink();
    final center = Offset((from.x + to.x + cardWidth) / 2, (from.y + to.y + cardHeight) / 2);
    return Positioned(
      left: center.dx.clamp(0.0, math.max(0.0, size.width - 110)),
      top: center.dy.clamp(0.0, math.max(0.0, size.height - 36)),
      child: Material(color: Colors.white.withValues(alpha: .9), borderRadius: BorderRadius.circular(12), child: Row(mainAxisSize: MainAxisSize.min, children: [
        InkWell(key: ValueKey('libraryRelation-${relation.id}'), onTap: () => onEditRelation(relation), child: Padding(padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2), child: Text(relation.label?.isNotEmpty == true ? relation.label! : '관계'))),
        IconButton(key: ValueKey('libraryRelationDelete-${relation.id}'), tooltip: '관계선 삭제', onPressed: () => onDeleteRelation(relation.id), constraints: const BoxConstraints.tightFor(width: 26, height: 26), padding: EdgeInsets.zero, icon: const Icon(Icons.close, size: 14)),
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
  const _LibraryCard({super.key, required this.item, required this.width, required this.height, required this.selected, this.onTap, this.onDoubleTap, this.onRename, this.onDelete, this.onMoveToSpace});
  final LibraryItem item;
  final double width;
  final double height;
  final bool selected;
  final VoidCallback? onTap;
  final VoidCallback? onDoubleTap;
  final VoidCallback? onRename;
  final VoidCallback? onDelete;
  final ValueChanged<LibrarySpace>? onMoveToSpace;

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
          shape: RoundedRectangleBorder(
            side: BorderSide(color: selected ? Colors.blue : Colors.white, width: selected ? 2 : 1),
            borderRadius: BorderRadius.circular(8),
          ),
          child: InkWell(
            onTap: onTap,
            onDoubleTap: onDoubleTap,
            onSecondaryTap: () => _showMenu(context),
            onLongPress: () => _showMenu(context),
            child: Padding(
              padding: const EdgeInsets.all(8),
              child: Row(children: [
                Icon(_icon, size: 20),
                const SizedBox(width: 6),
                Expanded(child: Text(item.title, maxLines: 2, overflow: TextOverflow.ellipsis)),
              ]),
            ),
          ),
        ),
      );

  void _showMenu(BuildContext context) => showMenu<String>(context: context, position: const RelativeRect.fromLTRB(80, 80, 0, 0), items: const [
    PopupMenuItem(value: 'rename', child: Text('이름 바꾸기')), PopupMenuItem(value: 'delete', child: Text('삭제')),
    PopupMenuItem(value: 'core', child: Text('핵심자료로 이동')), PopupMenuItem(value: 'basis', child: Text('기초자료로 이동')),
    PopupMenuItem(value: 'reference', child: Text('참고자료로 이동')), PopupMenuItem(value: 'temp', child: Text('임시저장소로 이동')),
  ]).then((action) {
    if (action == 'rename') onRename?.call();
    if (action == 'delete') onDelete?.call();
    for (final space in LibrarySpace.values) { if (action == space.name) onMoveToSpace?.call(space); }
  });
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
