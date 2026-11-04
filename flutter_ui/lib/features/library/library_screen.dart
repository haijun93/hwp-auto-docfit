import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

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
  const LibraryScreen({super.key, required this.api, this.clipboardReader});

  final LibraryApi api;
  final LibraryClipboardReader? clipboardReader;

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
  List<LibraryBox> _boxes = [];
  LibraryBox? _selectedBox;
  List<LibraryItem> _items = [];
  List<LibraryRelation> _relations = [];
  String? _selectedCoreItemId;
  String? _statusMessage;
  static const _cardWidth = 140.0;
  static const _cardHeight = 72.0;

  @override
  void initState() {
    super.initState();
    _loadBoxes();
  }

  @override
  void dispose() {
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
      _selectedCoreItemId = null;
      _statusMessage = null;
    });
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
      try {
        await widget.api.addRelation(box.id, _selectedCoreItemId!, item.id);
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
                SizedBox(width: 260, child: _buildSidebar()),
                const VerticalDivider(width: 1),
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
            Text(_selectedBox!.name, style: const TextStyle(fontWeight: FontWeight.bold)),
            SizedBox(width: 190, height: 38, child: TextField(
              key: const ValueKey('librarySearch'),
              controller: _searchController,
              decoration: const InputDecoration(prefixIcon: Icon(Icons.search), hintText: '자료 검색', isDense: true),
              onChanged: (query) async {
                final box = _selectedBox;
                if (box == null) return;
                final items = await widget.api.listItems(box.id, query: query);
                if (mounted) setState(() => _items = items);
              },
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
        if (_statusMessage != null) Text(_statusMessage!, key: const ValueKey('libraryStatus')),
        Expanded(child: _buildQuadrants()),
      ]);

  Widget _buildQuadrants() => Column(children: [
        Expanded(child: Row(children: [
          for (final space in [LibrarySpace.core, LibrarySpace.basis])
            Expanded(child: _quadrant(space)),
        ])),
        const Divider(height: 1),
        Expanded(child: Row(children: [
          for (final space in [LibrarySpace.reference, LibrarySpace.temp])
            Expanded(child: _quadrant(space)),
        ])),
      ]);

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
                          selected: selectedCoreItemId == item.id,
                          onTap: () => onItemTap(item),
                        ),
                      ),
                    ),
                  if (items.isEmpty) const Center(child: Text('자료가 없습니다.', style: TextStyle(color: Colors.black45))),
                  for (final relation in relations)
                    Positioned(
                      left: 8,
                      top: 4,
                      child: Row(children: [
                        Text('관계', key: ValueKey('libraryRelation-${relation.id}')),
                        IconButton(
                          key: ValueKey('libraryRelationDelete-${relation.id}'),
                          tooltip: '관계선 삭제',
                          icon: const Icon(Icons.close),
                          onPressed: () => onDeleteRelation(relation.id),
                        ),
                      ]),
                    ),
                ],
              ),
            );
          })),
        ]),
      );

  Color _spaceColor(LibrarySpace space) => switch (space) {
        LibrarySpace.core => const Color(0xFFF0F5FF),
        LibrarySpace.basis => const Color(0xFFF4F7F0),
        LibrarySpace.reference => const Color(0xFFFFF8EA),
        LibrarySpace.temp => const Color(0xFFF5F1F8),
      };
}

class _LibraryCard extends StatelessWidget {
  const _LibraryCard({super.key, required this.item, required this.width, required this.height, required this.selected, this.onTap});
  final LibraryItem item;
  final double width;
  final double height;
  final bool selected;
  final VoidCallback? onTap;

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
            child: Padding(
              padding: const EdgeInsets.all(8),
              child: Row(children: [
                const Icon(Icons.description_outlined, size: 20),
                const SizedBox(width: 6),
                Expanded(child: Text(item.title, maxLines: 2, overflow: TextOverflow.ellipsis)),
              ]),
            ),
          ),
        ),
      );
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
