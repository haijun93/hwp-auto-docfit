import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../core/drop_events.dart';
import '../library/library_api.dart';
import '../library/library_screen.dart';
import '../workspace/tab_navigation_shell.dart' show HostClosablePage;
import 'notebook_api.dart';

/// 노트북 화면(개발자 모드). 세 칸: 출처 · 근거 찾기/미리보기/변환 · 노트.
/// 폭이 [kNotebookWideWidth] 미만이면 세 칸을 탭으로 바꾼다.
const kNotebookWideWidth = 1000.0;

enum _Middle { search, compare, preview, transform }

/// 창에 파일을 끌어 놓았다는 알림을 듣는다. 돌려준 함수를 부르면 듣기를 멈춘다.
typedef NotebookDropWatcher = void Function() Function(void Function() onDrop);

/// 출처의 원본 자료함 항목을 보여 준다(자료함 화면을 열어 그 자료함·항목을 고르고 강조).
typedef NotebookOpenLibraryItem = Future<void> Function(BuildContext context, String boxId, String itemId);

void Function() _watchNotebookDrops(void Function() onDrop) =>
    watchWindowEvent('docfit-notebook-files-dropped', onDrop);

String _errorText(Object error) => error.toString().replaceFirst(RegExp(r'^(Bad state|StateError): '), '');

String _fileName(String path) => path.split(RegExp(r'[\\/]')).last;

class NotebookScreen extends StatefulWidget {
  const NotebookScreen({super.key, required this.api, this.library, this.watchDropEvents, this.openLibraryItem});

  final NotebookApi api;

  /// 있으면 '자료함에서 가져오기'로 자료함의 파일 자료를 출처로 넣을 수 있다.
  final LibraryApi? library;

  /// 시험에서 드롭 알림을 직접 넣을 때 쓴다. 없으면 창 이벤트를 듣는다.
  final NotebookDropWatcher? watchDropEvents;

  /// '자료함에서 보기'가 자료함을 여는 방법. 없으면 [library]로 자료함 화면을 새 페이지로 연다.
  final NotebookOpenLibraryItem? openLibraryItem;

  @override
  State<NotebookScreen> createState() => _NotebookScreenState();
}

class _NotebookScreenState extends State<NotebookScreen> {
  final _queryController = TextEditingController();
  final _titleController = TextEditingController();
  final _bodyController = TextEditingController();
  final _tagsController = TextEditingController();

  List<Notebook> _notebooks = [];
  Notebook? _notebook;
  List<NbSource> _sources = [];
  final _checked = <int>{};
  List<NbHit> _hits = [];
  List<NbNote> _notes = [];
  int? _noteId;
  List<NbCitation> _citations = [];
  _Middle _middle = _Middle.search;
  NbSource? _previewSource;
  List<NbParagraph> _previewParagraphs = [];
  int? _previewOrdinal;
  String _transformType = 'outline';
  List<NbTransformRow> _transformRows = [];
  List<NbCompareGroup> _compareGroups = [];

  /// 마지막으로 출처 비교한 검색어와 범위. 있으면 Markdown 내보내기에 출처 비교 절을 붙인다.
  String? _compareQuery;
  List<int>? _compareScope;

  /// 노트 목록을 거르는 태그(null이면 전체).
  String? _tagFilter;
  String? _status;
  bool _busy = false;
  bool _loaded = false;
  void Function()? _stopDrops;

  @override
  void initState() {
    super.initState();
    _stopDrops = (widget.watchDropEvents ?? _watchNotebookDrops)(() => unawaited(_takeDrops()));
    unawaited(widget.api.watchDrops(true).catchError((Object _) {}));
    _run(_loadNotebooks);
  }

  @override
  void dispose() {
    _stopDrops?.call();
    unawaited(widget.api.watchDrops(false).catchError((Object _) {}));
    _queryController.dispose();
    _titleController.dispose();
    _bodyController.dispose();
    _tagsController.dispose();
    super.dispose();
  }

  Future<void> _run(Future<void> Function() action, {String? done}) async {
    setState(() => _busy = true);
    try {
      await action();
      if (mounted && done != null) setState(() => _status = done);
    } catch (error) {
      if (!mounted) return;
      setState(() => _status = _errorText(error));
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _loadNotebooks() async {
    final list = await widget.api.listNotebooks();
    if (!mounted) return;
    setState(() {
      _notebooks = list;
      _loaded = true;
      _notebook = list.isEmpty ? null : list.firstWhere((n) => n.id == _notebook?.id, orElse: () => list.first);
    });
    await _loadNotebookContent();
  }

  Future<void> _loadNotebookContent() async {
    final nb = _notebook;
    if (nb == null) return;
    final sources = await widget.api.listSources(nb.id);
    final notes = await widget.api.listNotes(nb.id);
    if (!mounted) return;
    setState(() {
      final known = _sources.map((s) => s.id).toSet();
      _sources = sources;
      _checked.removeWhere((id) => !sources.any((s) => s.id == id));
      // 새로 들어온 출처는 근거 찾기 범위에 넣어 둔다.
      _checked.addAll(sources.where((s) => !known.contains(s.id)).map((s) => s.id));
      _notes = notes;
      if (_tagFilter != null && !notes.any((n) => n.tags.contains(_tagFilter))) _tagFilter = null;
    });
  }

  /// 노트북의 태그와 노트 수(많은 순, 같으면 이름순).
  List<(String, int)> get _tagCounts {
    final counts = <String, int>{};
    for (final note in _notes) {
      for (final tag in note.tags) {
        counts[tag] = (counts[tag] ?? 0) + 1;
      }
    }
    final list = [for (final e in counts.entries) (e.key, e.value)];
    list.sort((a, b) => b.$2 != a.$2 ? b.$2.compareTo(a.$2) : a.$1.compareTo(b.$1));
    return list;
  }

  List<NbNote> get _visibleNotes =>
      _tagFilter == null ? _notes : _notes.where((n) => n.tags.contains(_tagFilter)).toList();

  void _selectNotebook(Notebook nb) {
    setState(() {
      _notebook = nb;
      _sources = [];
      _checked.clear();
      _hits = [];
      _transformRows = [];
      _compareGroups = [];
      _compareQuery = null;
      _compareScope = null;
      _tagFilter = null;
      _previewSource = null;
      _previewParagraphs = [];
      _newNote();
    });
    _run(_loadNotebookContent);
  }

  Future<String?> _askText({
    required String title,
    required String label,
    required String fieldKey,
    required String okKey,
    String initial = '',
  }) {
    return showDialog<String>(
      context: context,
      builder: (context) =>
          _TextPromptDialog(title: title, label: label, fieldKey: fieldKey, okKey: okKey, initial: initial),
    );
  }

  Future<void> _createNotebook() async {
    final name = await _askText(
      title: '새 노트북',
      label: '노트북 이름',
      fieldKey: 'nb-create-name',
      okKey: 'nb-create-ok',
      initial: '새 노트북',
    );
    if (name == null || name.trim().isEmpty) return;
    await _run(() async {
      final id = await widget.api.createNotebook(name.trim());
      _notebook = Notebook(id: id, name: name.trim());
      await _loadNotebooks();
    }, done: '노트북을 만들었습니다.');
  }

  Future<void> _addSource() async {
    final nb = _notebook;
    if (nb == null) return;
    final path = await _askText(
      title: '출처 추가',
      label: '파일 경로(hwpx·hwp·docx·pdf·txt·md·pptx·xlsx)',
      fieldKey: 'nb-source-path',
      okKey: 'nb-source-path-ok',
    );
    final trimmed = path?.trim().replaceAll('"', '') ?? '';
    if (trimmed.isEmpty) return;
    await _addPaths([trimmed]);
  }

  /// 여러 파일을 차례로 출처로 넣는다. 하나가 실패해도 나머지는 계속한다.
  Future<void> _addPaths(List<String> paths) async {
    final nb = _notebook;
    final targets = paths.map((p) => p.trim()).where((p) => p.isNotEmpty).toList();
    if (targets.isEmpty) return;
    if (nb == null) {
      setState(() => _status = '먼저 노트북을 만들거나 고르세요.');
      return;
    }
    final failed = <String>[];
    var added = 0;
    await _run(() async {
      for (final path in targets) {
        try {
          await widget.api.addSource(nb.id, path);
          added++;
        } catch (error) {
          failed.add('${_fileName(path)}: ${_errorText(error)}');
        }
      }
      await _loadNotebookContent();
    });
    if (!mounted) return;
    setState(() {
      if (failed.isEmpty) {
        _status = added == 1 ? '출처를 추가했습니다.' : '출처 $added개를 추가했습니다.';
      } else {
        _status = '출처 $added개 추가, ${failed.length}개 실패 — ${failed.join(' / ')}';
      }
    });
  }

  /// 창에 끌어 놓은 파일을 가져와 지금 노트북의 출처로 넣는다.
  Future<void> _takeDrops() async {
    if (!mounted) return;
    try {
      final paths = await widget.api.takeDroppedPaths();
      if (mounted && paths.isNotEmpty) await _addPaths(paths);
    } catch (error) {
      if (mounted) setState(() => _status = _errorText(error));
    }
  }

  Future<void> _importFromLibrary() async {
    final library = widget.library;
    if (library == null || _notebook == null) return;
    final paths = await showDialog<List<String>>(
      context: context,
      builder: (context) => _LibraryPickDialog(library: library),
    );
    if (paths != null && paths.isNotEmpty) await _addPaths(paths);
  }

  Future<void> _removeSource(NbSource source) async {
    final nb = _notebook;
    if (nb == null) return;
    await _run(() async {
      await widget.api.removeSource(nb.id, source.id);
      if (_previewSource?.id == source.id) {
        _previewSource = null;
        _previewParagraphs = [];
      }
      await _loadNotebookContent();
    }, done: '출처를 뺐습니다(원본 파일은 그대로입니다).');
  }

  /// 출처가 나온 자료함 항목을 찾아 자료함 화면에서 보여 준다.
  Future<void> _showInLibrary(NbSource source) async {
    final nb = _notebook;
    if (nb == null) return;
    NbSourceItemLink? link;
    await _run(() async => link = await widget.api.sourceItem(nb.id, source.id));
    final found = link;
    if (!mounted || found == null) return; // 실패 문구는 _run이 이미 보였다.
    final boxId = found.boxId;
    final itemId = found.itemId;
    if (!found.found || boxId == null || itemId == null) {
      setState(() => _status = found.reason.isEmpty ? '자료함 항목을 찾을 수 없습니다.' : found.reason);
      return;
    }
    final open = widget.openLibraryItem ?? _defaultOpenLibraryItem;
    await open(context, boxId, itemId);
  }

  Future<void> _defaultOpenLibraryItem(BuildContext context, String boxId, String itemId) async {
    final library = widget.library;
    if (library == null) {
      setState(() => _status = '자료함을 열 수 없습니다.');
      return;
    }
    await Navigator.of(context).push(
      MaterialPageRoute<void>(
        builder: (_) => HostClosablePage(
          title: '자료함',
          backLabel: '노트북으로',
          child: LibraryScreen(api: library, notebookApi: widget.api, initialBoxId: boxId, initialItemId: itemId),
        ),
      ),
    );
    // 자료함에서 이 노트북에 출처를 더 넣었을 수 있다.
    if (mounted) await _run(_loadNotebookContent);
  }

  List<int>? get _scope => _checked.length == _sources.length ? null : _checked.toList();

  Future<void> _search() async {
    final nb = _notebook;
    final query = _queryController.text.trim();
    if (nb == null || query.isEmpty) return;
    if (_checked.isEmpty) {
      setState(() => _status = '근거를 찾을 출처를 하나 이상 고르세요.');
      return;
    }
    await _run(() async {
      final hits = await widget.api.search(nb.id, query, sourceIds: _scope);
      if (!mounted) return;
      setState(() {
        _hits = hits;
        _middle = _Middle.search;
        _status = hits.isEmpty ? '근거 문단을 찾지 못했습니다.' : '근거 문단 ${hits.length}개';
      });
    });
  }

  /// 같은 검색어의 근거를 출처마다 따로 찾아 나란히 보여 준다.
  Future<void> _compare() async {
    final nb = _notebook;
    final query = _queryController.text.trim();
    if (nb == null || query.isEmpty) {
      setState(() => _status = '비교할 검색어를 입력하세요.');
      return;
    }
    if (_checked.isEmpty) {
      setState(() => _status = '비교할 출처를 하나 이상 고르세요.');
      return;
    }
    final scope = _scope;
    await _run(() async {
      final groups = await widget.api.compare(nb.id, query, sourceIds: scope);
      if (!mounted) return;
      final found = groups.where((g) => g.hits.isNotEmpty).length;
      setState(() {
        _compareGroups = groups;
        _compareQuery = query;
        _compareScope = scope;
        _middle = _Middle.compare;
        _status = '출처 ${groups.length}개 중 $found개에서 근거를 찾았습니다.';
      });
    });
  }

  Future<void> _transform(String type) async {
    final nb = _notebook;
    if (nb == null) return;
    setState(() => _transformType = type);
    await _run(() async {
      final rows = await widget.api.transform(nb.id, type, sourceIds: _scope);
      if (mounted) setState(() => _transformRows = rows);
    });
  }

  Future<void> _preview(int sourceId, int? ordinal) async {
    final nb = _notebook;
    if (nb == null) return;
    final source = _sources.where((s) => s.id == sourceId).firstOrNull;
    await _run(() async {
      final paragraphs = await widget.api.paragraphs(nb.id, sourceId);
      if (!mounted) return;
      setState(() {
        _previewSource = source;
        _previewParagraphs = paragraphs;
        _previewOrdinal = ordinal;
        _middle = _Middle.preview;
      });
    });
  }

  void _cite(int sourceId, int ordinal, String quote) {
    if (_citations.any((c) => c.sourceId == sourceId && c.paragraphOrdinal == ordinal)) {
      setState(() => _status = '이미 인용한 문단입니다.');
      return;
    }
    setState(() {
      _citations = [..._citations, NbCitation(sourceId: sourceId, paragraphOrdinal: ordinal, quote: quote)];
      _status = '노트에 인용을 붙였습니다.';
    });
  }

  void _newNote() {
    _noteId = null;
    _titleController.clear();
    _bodyController.clear();
    _tagsController.clear();
    _citations = [];
  }

  void _openNote(NbNote note) {
    setState(() {
      _noteId = note.id;
      _titleController.text = note.title;
      _bodyController.text = note.body;
      _tagsController.text = note.tags.join(', ');
      _citations = List.of(note.citations);
    });
  }

  Future<void> _saveNote() async {
    final nb = _notebook;
    if (nb == null) return;
    final title = _titleController.text.trim().isEmpty ? '제목 없는 노트' : _titleController.text.trim();
    await _run(() async {
      final id = await widget.api.saveNote(
        nb.id,
        NbNote(
          id: _noteId,
          title: title,
          body: _bodyController.text,
          citations: _citations,
          tags: parseNbTags(_tagsController.text),
        ),
      );
      _noteId = id;
      _titleController.text = title;
      _tagsController.text = parseNbTags(_tagsController.text).join(', ');
      await _loadNotebookContent();
    }, done: '노트를 저장했습니다.');
  }

  Future<void> _deleteNote(NbNote note) async {
    final nb = _notebook;
    final id = note.id;
    if (nb == null || id == null) return;
    await _run(() async {
      await widget.api.deleteNote(nb.id, id);
      if (_noteId == id) _newNote();
      await _loadNotebookContent();
    }, done: '노트를 지웠습니다.');
  }

  Future<void> _exportNote() async {
    final nb = _notebook;
    final id = _noteId;
    if (nb == null || id == null) {
      setState(() => _status = '먼저 노트를 저장하세요.');
      return;
    }
    final compareQuery = _compareQuery;
    String markdown = '';
    await _run(
      () async => markdown = await widget.api.exportMarkdown(
        nb.id,
        id,
        compareQuery: compareQuery,
        compareSourceIds: _compareScope,
      ),
    );
    if (!mounted || markdown.isEmpty) return;
    await showDialog<void>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(
          compareQuery == null ? 'Markdown 내보내기' : 'Markdown 내보내기(출처 비교: $compareQuery 포함)',
          overflow: TextOverflow.ellipsis,
        ),
        content: SizedBox(
          width: 560,
          height: 360,
          child: SingleChildScrollView(child: SelectableText(markdown, key: const ValueKey('nb-export-text'))),
        ),
        actions: [
          TextButton(
            onPressed: () => Clipboard.setData(ClipboardData(text: markdown)),
            child: const Text('복사'),
          ),
          FilledButton(onPressed: () => Navigator.of(context).pop(), child: const Text('닫기')),
        ],
      ),
    );
  }

  /// 노트를 한/글 HWPX로 저장한다(저장 위치는 호스트 저장 대화상자). 출처 비교를 했으면 비교 표도 넣는다.
  Future<void> _exportHwpx() async {
    final nb = _notebook;
    final id = _noteId;
    if (nb == null || id == null) {
      setState(() => _status = '먼저 노트를 저장하세요.');
      return;
    }
    String? saved;
    var finished = false;
    await _run(() async {
      saved = await widget.api.exportHwpx(nb.id, id, compareQuery: _compareQuery, compareSourceIds: _compareScope);
      finished = true;
    });
    if (!mounted || !finished) return; // 실패 문구는 _run이 이미 보였다.
    final path = saved;
    setState(() => _status = path == null ? 'HWPX 내보내기를 취소했습니다.' : '한/글 문서로 저장했습니다: $path');
  }

  String _sourceName(int id) => _sources.where((s) => s.id == id).map((s) => s.displayName).firstOrNull ?? '출처 $id';

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('노트북'),
        actions: [
          if (_notebooks.isNotEmpty)
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 8),
              child: DropdownButton<int>(
                key: const ValueKey('nb-select'),
                value: _notebook?.id,
                underline: const SizedBox(),
                items: [for (final nb in _notebooks) DropdownMenuItem(value: nb.id, child: Text(nb.name))],
                onChanged: (id) {
                  final nb = _notebooks.where((n) => n.id == id).firstOrNull;
                  if (nb != null) _selectNotebook(nb);
                },
              ),
            ),
          IconButton(
            key: const ValueKey('nb-create'),
            tooltip: '새 노트북',
            onPressed: _busy ? null : _createNotebook,
            icon: const Icon(Icons.create_new_folder_outlined),
          ),
        ],
        bottom: _busy
            ? const PreferredSize(preferredSize: Size.fromHeight(2), child: LinearProgressIndicator(minHeight: 2))
            : null,
      ),
      body: Column(
        children: [
          Expanded(child: _body()),
          if (_status != null)
            Container(
              width: double.infinity,
              color: const Color(0xFFF1F5F9),
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
              child: Text(_status!, key: const ValueKey('nb-status'), maxLines: 2, overflow: TextOverflow.ellipsis),
            ),
        ],
      ),
    );
  }

  Widget _body() {
    if (_notebook == null) {
      return Center(
        child: _loaded
            ? Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Text('노트북이 없습니다. 여러 문서를 모아 근거를 찾고 노트를 써 보세요.'),
                  const SizedBox(height: 12),
                  FilledButton.icon(
                    key: const ValueKey('nb-create-empty'),
                    onPressed: _busy ? null : _createNotebook,
                    icon: const Icon(Icons.add),
                    label: const Text('새 노트북 만들기'),
                  ),
                ],
              )
            : const CircularProgressIndicator(),
      );
    }
    return LayoutBuilder(
      builder: (context, constraints) {
        if (constraints.maxWidth >= kNotebookWideWidth) {
          return Row(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              SizedBox(width: 260, child: _sourcesPane()),
              const VerticalDivider(width: 1),
              Expanded(child: _middlePane()),
              const VerticalDivider(width: 1),
              SizedBox(width: 340, child: _notesPane()),
            ],
          );
        }
        return DefaultTabController(
          length: 3,
          child: Column(
            children: [
              const TabBar(
                tabs: [
                  Tab(key: ValueKey('nb-tab-sources'), text: '출처'),
                  Tab(key: ValueKey('nb-tab-evidence'), text: '근거·변환'),
                  Tab(key: ValueKey('nb-tab-notes'), text: '노트'),
                ],
              ),
              Expanded(child: TabBarView(children: [_sourcesPane(), _middlePane(), _notesPane()])),
            ],
          ),
        );
      },
    );
  }

  Widget _paneHeader(String title, List<Widget> actions) => Padding(
    padding: const EdgeInsets.fromLTRB(12, 8, 8, 4),
    child: Row(
      children: [
        Expanded(
          child: Text(title, style: const TextStyle(fontWeight: FontWeight.w600)),
        ),
        ...actions,
      ],
    ),
  );

  IconData _kindIcon(String kind) => switch (kind) {
    'xlsx' => Icons.table_chart_outlined,
    'pptx' => Icons.slideshow_outlined,
    'md' || 'txt' => Icons.notes,
    _ => Icons.description_outlined,
  };

  Widget _sourcesPane() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        _paneHeader('출처 ${_sources.length}', [
          if (widget.library != null)
            IconButton(
              key: const ValueKey('nb-source-library'),
              tooltip: '자료함에서 가져오기',
              onPressed: _busy ? null : _importFromLibrary,
              icon: const Icon(Icons.inventory_2_outlined, size: 18),
            ),
          TextButton.icon(
            key: const ValueKey('nb-source-add'),
            onPressed: _busy ? null : _addSource,
            icon: const Icon(Icons.add, size: 18),
            label: const Text('출처 추가'),
          ),
        ]),
        const Padding(
          padding: EdgeInsets.symmetric(horizontal: 12),
          child: Text(
            '체크한 출처에서만 근거를 찾습니다. 파일을 이 창에 끌어 놓아도 출처로 추가됩니다.',
            style: TextStyle(fontSize: 12, color: Colors.black54),
          ),
        ),
        Expanded(
          child: _sources.isEmpty
              ? const Center(child: Text('출처가 없습니다.'))
              : ListView(
                  children: [
                    for (final s in _sources)
                      ListTile(
                        key: ValueKey('nb-source-${s.id}'),
                        dense: true,
                        leading: Checkbox(
                          value: _checked.contains(s.id),
                          onChanged: (v) => setState(() => v == true ? _checked.add(s.id) : _checked.remove(s.id)),
                        ),
                        title: Row(
                          children: [
                            Icon(_kindIcon(s.kind), size: 16),
                            const SizedBox(width: 4),
                            Expanded(child: Text(s.displayName, overflow: TextOverflow.ellipsis)),
                          ],
                        ),
                        subtitle: Text(
                          s.status == 'ready' || s.status == 'indexed' ? '문단 ${s.paragraphCount}개' : '${s.status} ',
                          style: const TextStyle(fontSize: 12),
                        ),
                        onTap: () => _preview(s.id, null),
                        trailing: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            if (s.itemId != null && (widget.library != null || widget.openLibraryItem != null))
                              IconButton(
                                key: ValueKey('nb-source-in-library-${s.id}'),
                                tooltip: '자료함에서 보기',
                                icon: const Icon(Icons.inventory_2_outlined, size: 18),
                                onPressed: _busy ? null : () => _showInLibrary(s),
                              ),
                            IconButton(
                              tooltip: '출처 빼기',
                              icon: const Icon(Icons.close, size: 18),
                              onPressed: _busy ? null : () => _removeSource(s),
                            ),
                          ],
                        ),
                      ),
                  ],
                ),
        ),
      ],
    );
  }

  Widget _middlePane() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(12, 8, 12, 4),
          child: Wrap(
            spacing: 8,
            runSpacing: 4,
            children: [
              for (final (mode, key, label) in const [
                (_Middle.search, 'nb-mid-search', '근거 찾기'),
                (_Middle.compare, 'nb-mid-compare', '출처 비교'),
                (_Middle.preview, 'nb-mid-preview', '미리보기'),
                (_Middle.transform, 'nb-mid-transform', '변환'),
              ])
                ChoiceChip(
                  key: ValueKey(key),
                  label: Text(label),
                  selected: _middle == mode,
                  onSelected: (_) => setState(() => _middle = mode),
                ),
            ],
          ),
        ),
        const Divider(height: 1),
        Expanded(
          child: switch (_middle) {
            _Middle.search => _searchView(),
            _Middle.compare => _compareView(),
            _Middle.preview => _previewView(),
            _Middle.transform => _transformView(),
          },
        ),
      ],
    );
  }

  Widget _searchView() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Padding(
          padding: const EdgeInsets.all(12),
          child: Row(
            children: [
              Expanded(
                child: TextField(
                  key: const ValueKey('nb-query'),
                  controller: _queryController,
                  decoration: const InputDecoration(
                    hintText: '질문이나 검색어(예: 올해 예산 증가 이유)',
                    border: OutlineInputBorder(),
                    isDense: true,
                  ),
                  onSubmitted: (_) => _search(),
                ),
              ),
              const SizedBox(width: 8),
              FilledButton(
                key: const ValueKey('nb-search-run'),
                onPressed: _busy ? null : _search,
                child: const Text('근거 찾기'),
              ),
            ],
          ),
        ),
        Expanded(
          child: ListView.builder(
            padding: const EdgeInsets.symmetric(horizontal: 12),
            itemCount: _hits.length,
            itemBuilder: (context, i) {
              final hit = _hits[i];
              return Card(
                key: ValueKey('nb-hit-$i'),
                child: Padding(
                  padding: const EdgeInsets.all(10),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        '${hit.displayName} · 문단 ${hit.ordinal + 1}${hit.location.isEmpty ? '' : ' · ${hit.location}'} · 점수 ${hit.score.toStringAsFixed(1)}',
                        style: const TextStyle(fontSize: 12, color: Colors.black54),
                        overflow: TextOverflow.ellipsis,
                      ),
                      const SizedBox(height: 4),
                      _highlighted(hit.body, _queryController.text),
                      Wrap(
                        alignment: WrapAlignment.end,
                        spacing: 4,
                        children: [
                          TextButton(onPressed: () => _preview(hit.sourceId, hit.ordinal), child: const Text('미리보기')),
                          TextButton.icon(
                            key: ValueKey('nb-cite-$i'),
                            onPressed: () => _cite(hit.sourceId, hit.ordinal, hit.body),
                            icon: const Icon(Icons.format_quote, size: 18),
                            label: const Text('노트에 인용'),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              );
            },
          ),
        ),
      ],
    );
  }

  /// 출처 비교: 같은 검색어의 근거 문단을 출처마다 한 칸씩 나란히 놓는다. 칸이 많으면 가로로 넘긴다.
  Widget _compareView() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Padding(
          padding: const EdgeInsets.all(12),
          child: Row(
            children: [
              Expanded(
                child: TextField(
                  key: const ValueKey('nb-compare-query'),
                  controller: _queryController,
                  decoration: const InputDecoration(
                    hintText: '출처마다 비교할 검색어(예: 복지 예산)',
                    border: OutlineInputBorder(),
                    isDense: true,
                  ),
                  onSubmitted: (_) => _compare(),
                ),
              ),
              const SizedBox(width: 8),
              FilledButton(
                key: const ValueKey('nb-compare-run'),
                onPressed: _busy ? null : _compare,
                child: const Text('비교'),
              ),
            ],
          ),
        ),
        Expanded(
          child: _compareGroups.isEmpty
              ? const Center(
                  child: Padding(
                    padding: EdgeInsets.all(12),
                    child: Text('검색어를 넣고 비교를 누르면 체크한 출처마다 근거 문단을 나란히 보여 줍니다.'),
                  ),
                )
              : Scrollbar(
                  child: ListView.separated(
                    key: const ValueKey('nb-compare'),
                    scrollDirection: Axis.horizontal,
                    padding: const EdgeInsets.fromLTRB(12, 0, 12, 12),
                    itemCount: _compareGroups.length,
                    separatorBuilder: (_, _) => const SizedBox(width: 8),
                    itemBuilder: (context, i) => _compareColumn(_compareGroups[i]),
                  ),
                ),
        ),
      ],
    );
  }

  Widget _compareColumn(NbCompareGroup group) {
    return Container(
      key: ValueKey('nb-compare-col-${group.sourceId}'),
      width: 280,
      decoration: BoxDecoration(
        border: Border.all(color: const Color(0xFFE2E8F0)),
        borderRadius: BorderRadius.circular(6),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Container(
            color: const Color(0xFFF1F5F9),
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
            child: Text(
              '${group.displayName} · 근거 ${group.hits.length}개',
              style: const TextStyle(fontWeight: FontWeight.w600),
              overflow: TextOverflow.ellipsis,
            ),
          ),
          Expanded(
            child: group.hits.isEmpty
                ? const Center(
                    child: Text('근거 문단 없음', style: TextStyle(color: Colors.black45)),
                  )
                : ListView(
                    padding: const EdgeInsets.all(6),
                    children: [
                      for (var i = 0; i < group.hits.length; i++)
                        Card(
                          key: ValueKey('nb-compare-hit-${group.sourceId}-$i'),
                          child: InkWell(
                            onTap: () => _preview(group.sourceId, group.hits[i].ordinal),
                            child: Padding(
                              padding: const EdgeInsets.all(8),
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(
                                    '문단 ${group.hits[i].ordinal + 1}${group.hits[i].location.isEmpty ? '' : ' · ${group.hits[i].location}'} · 점수 ${group.hits[i].score.toStringAsFixed(1)}',
                                    style: const TextStyle(fontSize: 12, color: Colors.black54),
                                    overflow: TextOverflow.ellipsis,
                                  ),
                                  const SizedBox(height: 4),
                                  _highlighted(group.hits[i].body, _compareQuery ?? ''),
                                  Align(
                                    alignment: Alignment.centerRight,
                                    child: IconButton(
                                      key: ValueKey('nb-compare-cite-${group.sourceId}-$i'),
                                      tooltip: '노트에 인용',
                                      icon: const Icon(Icons.format_quote, size: 18),
                                      onPressed: () =>
                                          _cite(group.sourceId, group.hits[i].ordinal, group.hits[i].body),
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          ),
                        ),
                    ],
                  ),
          ),
        ],
      ),
    );
  }

  /// 검색어와 일치하는 부분을 굵게 보인다.
  Widget _highlighted(String body, String query) {
    final terms = query.split(RegExp(r'\s+')).where((t) => t.length > 1).map(RegExp.escape).toList();
    if (terms.isEmpty) return Text(body);
    final pattern = RegExp(terms.join('|'));
    final spans = <TextSpan>[];
    var start = 0;
    for (final m in pattern.allMatches(body)) {
      if (m.start > start) spans.add(TextSpan(text: body.substring(start, m.start)));
      spans.add(
        TextSpan(
          text: m.group(0),
          style: const TextStyle(fontWeight: FontWeight.w700, backgroundColor: Color(0xFFFFF3BF)),
        ),
      );
      start = m.end;
    }
    if (start < body.length) spans.add(TextSpan(text: body.substring(start)));
    return Text.rich(TextSpan(children: spans, style: DefaultTextStyle.of(context).style));
  }

  Widget _previewView() {
    final source = _previewSource;
    if (source == null) return const Center(child: Text('출처나 근거 카드를 누르면 원문을 보여 줍니다.'));
    return ListView(
      key: const ValueKey('nb-preview'),
      padding: const EdgeInsets.all(12),
      children: [
        Text(source.displayName, style: const TextStyle(fontWeight: FontWeight.w600)),
        const SizedBox(height: 8),
        for (final p in _previewParagraphs)
          Container(
            key: ValueKey('nb-preview-${p.ordinal}'),
            margin: const EdgeInsets.only(bottom: 4),
            padding: EdgeInsets.fromLTRB(6.0 + 12.0 * p.level.clamp(0, 6), 6, 6, 6),
            color: p.ordinal == _previewOrdinal
                ? const Color(0xFFFFF3BF)
                : p.isTable
                ? const Color(0xFFF1F5F9)
                : null,
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                SizedBox(
                  width: 36,
                  child: Text('${p.ordinal + 1}', style: const TextStyle(fontSize: 12, color: Colors.black45)),
                ),
                Expanded(
                  child: SelectableText(
                    p.isTable ? p.body.replaceAll('\t', '  |  ') : p.body,
                    style: p.level > 0 ? const TextStyle(fontWeight: FontWeight.w600) : null,
                  ),
                ),
                IconButton(
                  tooltip: '노트에 인용',
                  icon: const Icon(Icons.format_quote, size: 18),
                  onPressed: () => _cite(p.sourceId, p.ordinal, p.body),
                ),
              ],
            ),
          ),
      ],
    );
  }

  Widget _transformView() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Padding(
          padding: const EdgeInsets.all(12),
          child: Wrap(
            spacing: 8,
            runSpacing: 4,
            children: [
              for (final entry in kNbTransformTypes.entries)
                ChoiceChip(
                  key: ValueKey('nb-transform-${entry.key}'),
                  label: Text(entry.value),
                  selected: _transformType == entry.key && _transformRows.isNotEmpty,
                  onSelected: _busy ? null : (_) => _transform(entry.key),
                ),
            ],
          ),
        ),
        Expanded(
          child: _transformRows.isEmpty
              ? const Center(child: Text('변환 종류를 고르면 체크한 출처에서 규칙대로 모아 보여 줍니다.'))
              : ListView.builder(
                  padding: const EdgeInsets.symmetric(horizontal: 12),
                  itemCount: _transformRows.length,
                  itemBuilder: (context, i) {
                    final row = _transformRows[i];
                    return ListTile(
                      dense: true,
                      contentPadding: EdgeInsets.only(left: 8.0 + 12.0 * row.level.clamp(0, 6)),
                      title: Text(row.text.replaceAll('\t', '  |  ')),
                      subtitle: Text(
                        _transformType == 'keywords'
                            ? '${_sourceName(row.sourceId)} · ${row.score.toStringAsFixed(0)}회'
                            : '${_sourceName(row.sourceId)} · 문단 ${row.ordinal + 1}',
                        style: const TextStyle(fontSize: 12),
                      ),
                      onTap: () => _preview(row.sourceId, row.ordinal),
                    );
                  },
                ),
        ),
      ],
    );
  }

  Widget _notesPane() {
    final tags = _tagCounts;
    final visible = _visibleNotes;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        _paneHeader(_tagFilter == null ? '노트 ${_notes.length}' : '노트 ${visible.length}/${_notes.length}', [
          TextButton.icon(
            key: const ValueKey('nb-note-new'),
            onPressed: () => setState(_newNote),
            icon: const Icon(Icons.note_add_outlined, size: 18),
            label: const Text('새 노트'),
          ),
        ]),
        if (tags.isNotEmpty)
          SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            padding: const EdgeInsets.symmetric(horizontal: 12),
            child: Row(
              children: [
                ChoiceChip(
                  key: const ValueKey('nb-tag-all'),
                  label: const Text('전체'),
                  visualDensity: VisualDensity.compact,
                  selected: _tagFilter == null,
                  onSelected: (_) => setState(() => _tagFilter = null),
                ),
                for (final (tag, count) in tags)
                  Padding(
                    padding: const EdgeInsets.only(left: 4),
                    child: ChoiceChip(
                      key: ValueKey('nb-tag-$tag'),
                      label: Text('#$tag $count'),
                      visualDensity: VisualDensity.compact,
                      selected: _tagFilter == tag,
                      onSelected: (on) => setState(() => _tagFilter = on ? tag : null),
                    ),
                  ),
              ],
            ),
          ),
        if (visible.isNotEmpty)
          ConstrainedBox(
            constraints: const BoxConstraints(maxHeight: 140),
            child: ListView(
              shrinkWrap: true,
              children: [
                for (final note in visible)
                  ListTile(
                    key: ValueKey('nb-note-${note.id}'),
                    dense: true,
                    selected: note.id == _noteId,
                    title: Text(note.title, overflow: TextOverflow.ellipsis),
                    subtitle: Text(
                      [
                        '인용 ${note.citations.length}개',
                        if (note.tags.isNotEmpty) note.tags.map((t) => '#$t').join(' '),
                      ].join(' · '),
                      style: const TextStyle(fontSize: 12),
                      overflow: TextOverflow.ellipsis,
                    ),
                    onTap: () => _openNote(note),
                    trailing: IconButton(
                      tooltip: '노트 지우기',
                      icon: const Icon(Icons.delete_outline, size: 18),
                      onPressed: _busy ? null : () => _deleteNote(note),
                    ),
                  ),
              ],
            ),
          ),
        const Divider(height: 1),
        Expanded(
          child: ListView(
            padding: const EdgeInsets.all(12),
            children: [
              TextField(
                key: const ValueKey('nb-note-title'),
                controller: _titleController,
                decoration: const InputDecoration(labelText: '제목', isDense: true),
              ),
              const SizedBox(height: 8),
              TextField(
                key: const ValueKey('nb-note-tags'),
                controller: _tagsController,
                decoration: const InputDecoration(
                  labelText: '태그(쉼표나 공백으로 구분, 예: 예산, 복지)',
                  isDense: true,
                  prefixText: '# ',
                ),
              ),
              const SizedBox(height: 8),
              TextField(
                key: const ValueKey('nb-note-body'),
                controller: _bodyController,
                minLines: 5,
                maxLines: 12,
                decoration: const InputDecoration(
                  labelText: '본문(Markdown)',
                  border: OutlineInputBorder(),
                  alignLabelWithHint: true,
                ),
              ),
              const SizedBox(height: 8),
              Text('인용 ${_citations.length}개', style: const TextStyle(fontWeight: FontWeight.w600)),
              for (var i = 0; i < _citations.length; i++)
                Container(
                  key: ValueKey('nb-citation-$i'),
                  margin: const EdgeInsets.only(top: 6),
                  decoration: const BoxDecoration(
                    border: Border(left: BorderSide(color: Color(0xFF94A3B8), width: 3)),
                  ),
                  child: Material(
                    color: const Color(0xFFF8FAFC),
                    child: ListTile(
                      dense: true,
                      title: Text(_citations[i].quote, maxLines: 3, overflow: TextOverflow.ellipsis),
                      subtitle: Text(
                        '${_sourceName(_citations[i].sourceId)} · 문단 ${_citations[i].paragraphOrdinal + 1}',
                        style: const TextStyle(fontSize: 12),
                      ),
                      onTap: () => _preview(_citations[i].sourceId, _citations[i].paragraphOrdinal),
                      trailing: IconButton(
                        tooltip: '인용 빼기',
                        icon: const Icon(Icons.close, size: 16),
                        onPressed: () => setState(() => _citations = List.of(_citations)..removeAt(i)),
                      ),
                    ),
                  ),
                ),
              const SizedBox(height: 12),
              Wrap(
                spacing: 8,
                runSpacing: 8,
                alignment: WrapAlignment.end,
                children: [
                  PopupMenuButton<String>(
                    key: const ValueKey('nb-note-export'),
                    enabled: !_busy && _noteId != null,
                    tooltip: '내보내기 형식 고르기',
                    onSelected: (format) => format == 'hwpx' ? _exportHwpx() : _exportNote(),
                    itemBuilder: (context) => const [
                      PopupMenuItem(
                        key: ValueKey('nb-export-md'),
                        value: 'md',
                        child: ListTile(dense: true, leading: Icon(Icons.description_outlined), title: Text('Markdown')),
                      ),
                      PopupMenuItem(
                        key: ValueKey('nb-export-hwpx'),
                        value: 'hwpx',
                        child: ListTile(
                          dense: true,
                          leading: Icon(Icons.save_alt),
                          title: Text('HWPX(한/글)'),
                          subtitle: Text('저장 위치를 골라 한/글 문서로 저장'),
                        ),
                      ),
                    ],
                    child: IgnorePointer(
                      child: OutlinedButton.icon(
                        onPressed: _busy || _noteId == null ? null : () {},
                        icon: const Icon(Icons.arrow_drop_down),
                        label: const Text('내보내기'),
                      ),
                    ),
                  ),
                  FilledButton(
                    key: const ValueKey('nb-note-save'),
                    onPressed: _busy ? null : _saveNote,
                    child: const Text('노트 저장'),
                  ),
                ],
              ),
            ],
          ),
        ),
      ],
    );
  }
}

/// 한 줄 입력 대화상자. 컨트롤러를 대화상자 수명에 맞춰 버린다(닫힘 애니메이션 중 사용 오류 방지).
class _TextPromptDialog extends StatefulWidget {
  const _TextPromptDialog({
    required this.title,
    required this.label,
    required this.fieldKey,
    required this.okKey,
    required this.initial,
  });

  final String title;
  final String label;
  final String fieldKey;
  final String okKey;
  final String initial;

  @override
  State<_TextPromptDialog> createState() => _TextPromptDialogState();
}

class _TextPromptDialogState extends State<_TextPromptDialog> {
  late final _controller = TextEditingController(text: widget.initial);

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: Text(widget.title),
      content: SizedBox(
        width: 420,
        child: TextField(
          key: ValueKey(widget.fieldKey),
          controller: _controller,
          autofocus: true,
          decoration: InputDecoration(labelText: widget.label),
          onSubmitted: (value) => Navigator.of(context).pop(value),
        ),
      ),
      actions: [
        TextButton(onPressed: () => Navigator.of(context).pop(), child: const Text('취소')),
        FilledButton(
          key: ValueKey(widget.okKey),
          onPressed: () => Navigator.of(context).pop(_controller.text),
          child: const Text('확인'),
        ),
      ],
    );
  }
}

/// 자료함을 골라 파일 자료를 체크하고, 고른 파일 경로들을 돌려준다.
class _LibraryPickDialog extends StatefulWidget {
  const _LibraryPickDialog({required this.library});

  final LibraryApi library;

  @override
  State<_LibraryPickDialog> createState() => _LibraryPickDialogState();
}

class _LibraryPickDialogState extends State<_LibraryPickDialog> {
  List<LibraryBox> _boxes = [];
  String? _boxId;
  List<LibraryItem> _files = [];
  final _picked = <String>{};
  String? _error;
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    unawaited(_loadBoxes());
  }

  Future<void> _guard(Future<void> Function() action) async {
    setState(() => _loading = true);
    try {
      await action();
      if (mounted) setState(() => _error = null);
    } catch (error) {
      if (mounted) setState(() => _error = _errorText(error));
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _loadBoxes() => _guard(() async {
    final boxes = await widget.library.listBoxes();
    if (!mounted) return;
    setState(() {
      _boxes = boxes;
      _boxId = boxes.isEmpty ? null : boxes.first.id;
    });
    await _loadItems();
  });

  Future<void> _loadItems() async {
    final id = _boxId;
    if (id == null) return;
    final items = await widget.library.listItems(id);
    if (!mounted) return;
    setState(() {
      _files = [
        for (final item in items)
          if (item.kind == LibraryItemKind.file && (item.source ?? '').trim().isNotEmpty) item,
      ];
      _picked.clear();
    });
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: const Text('자료함에서 가져오기'),
      content: SizedBox(
        width: 460,
        height: 360,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            if (_boxes.isNotEmpty)
              DropdownButton<String>(
                key: const ValueKey('nb-lib-box'),
                isExpanded: true,
                value: _boxId,
                items: [
                  for (final box in _boxes)
                    DropdownMenuItem(value: box.id, child: Text(box.name, overflow: TextOverflow.ellipsis)),
                ],
                onChanged: (id) {
                  if (id == null || id == _boxId) return;
                  setState(() => _boxId = id);
                  unawaited(_guard(_loadItems));
                },
              ),
            if (_loading) const LinearProgressIndicator(minHeight: 2),
            if (_error != null) Text(_error!, style: const TextStyle(color: Colors.red)),
            Expanded(
              child: !_loading && _boxes.isEmpty
                  ? const Center(child: Text('자료함이 없습니다.'))
                  : !_loading && _files.isEmpty
                  ? const Center(child: Text('이 자료함에는 파일 자료가 없습니다.'))
                  : ListView(
                      children: [
                        for (final item in _files)
                          CheckboxListTile(
                            key: ValueKey('nb-lib-item-${item.id}'),
                            dense: true,
                            value: _picked.contains(item.source),
                            title: Text(item.title, overflow: TextOverflow.ellipsis),
                            subtitle: Text(item.source!, overflow: TextOverflow.ellipsis),
                            onChanged: (v) =>
                                setState(() => v == true ? _picked.add(item.source!) : _picked.remove(item.source)),
                          ),
                      ],
                    ),
            ),
          ],
        ),
      ),
      actions: [
        TextButton(onPressed: () => Navigator.of(context).pop(), child: const Text('취소')),
        FilledButton(
          key: const ValueKey('nb-lib-ok'),
          onPressed: _picked.isEmpty ? null : () => Navigator.of(context).pop(_picked.toList()),
          child: Text('가져오기 ${_picked.length}개'),
        ),
      ],
    );
  }
}
