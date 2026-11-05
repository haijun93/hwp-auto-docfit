/// 노트북(개발자 모드) 화면용 API. klib의 nb_* 명령을 Python 'notebook' 브리지로 부른다.
library;

class Notebook {
  const Notebook({required this.id, required this.name});
  final int id;
  final String name;
}

class NbSource {
  const NbSource({
    required this.id,
    required this.displayName,
    required this.kind,
    required this.status,
    required this.paragraphCount,
    this.origin = '',
  });
  final int id;
  final String displayName;
  final String kind;
  final String status;
  final int paragraphCount;
  final String origin;
}

class NbParagraph {
  const NbParagraph({
    required this.sourceId,
    required this.ordinal,
    required this.body,
    this.location = '',
    this.level = 0,
    this.kind = 'text',
  });
  final int sourceId;
  final int ordinal;
  final String body;
  final String location;

  /// 위계 수준(0=본문). hwpx·docx 개요 수준이나 공문서 기호(Ⅰ. 1. □ ○ - *)에서 온다.
  final int level;

  /// 'text' 또는 'table'(표 한 행, 칸은 탭으로 나뉨).
  final String kind;
  bool get isTable => kind == 'table';
}

/// 근거 찾기 결과 문단.
class NbHit {
  const NbHit({
    required this.sourceId,
    required this.ordinal,
    required this.displayName,
    required this.body,
    required this.score,
    this.location = '',
  });
  final int sourceId;
  final int ordinal;
  final String displayName;
  final String body;
  final double score;
  final String location;
}

/// 규칙 기반 변환 결과(개요·표·숫자 문장·핵심어).
class NbTransformRow {
  const NbTransformRow({
    required this.sourceId,
    required this.ordinal,
    required this.text,
    required this.score,
    this.level = 0,
  });
  final int sourceId;
  final int ordinal;
  final String text;
  final double score;
  final int level;
}

class NbCitation {
  const NbCitation({required this.sourceId, required this.paragraphOrdinal, required this.quote});
  final int sourceId;
  final int paragraphOrdinal;
  final String quote;
}

class NbNote {
  const NbNote({this.id, required this.title, required this.body, this.citations = const []});
  final int? id;
  final String title;
  final String body;
  final List<NbCitation> citations;

  NbNote copyWith({int? id, String? title, String? body, List<NbCitation>? citations}) => NbNote(
    id: id ?? this.id,
    title: title ?? this.title,
    body: body ?? this.body,
    citations: citations ?? this.citations,
  );
}

const kNbTransformTypes = <String, String>{'outline': '개요', 'tables': '표', 'numbers': '숫자 문장', 'keywords': '핵심어'};

abstract class NotebookApi {
  Future<List<Notebook>> listNotebooks();
  Future<int> createNotebook(String name);
  Future<List<NbSource>> listSources(int notebookId);

  /// 파일 경로만 klib에 넘긴다(추출은 엔진/추출 서비스가 맡음).
  Future<int> addSource(int notebookId, String path);
  Future<void> removeSource(int notebookId, int sourceId);
  Future<List<NbParagraph>> paragraphs(int notebookId, int sourceId);
  Future<List<NbHit>> search(int notebookId, String query, {List<int>? sourceIds, int limit = 20});
  Future<List<NbTransformRow>> transform(int notebookId, String type, {List<int>? sourceIds});
  Future<List<NbNote>> listNotes(int notebookId);
  Future<int> saveNote(int notebookId, NbNote note);
  Future<void> deleteNote(int notebookId, int noteId);
  Future<String> exportMarkdown(int notebookId, int noteId);

  /// 창에 끌어 놓은 파일을 노트북 출처로 받기 켜기·끄기(노트북 화면이 열려 있는 동안 켠다).
  Future<void> watchDrops(bool active);

  /// 창에 끌어 놓아 맡겨 둔 파일 경로를 가져간다(가져가면 비워진다).
  Future<List<String>> takeDroppedPaths();
}

typedef NotebookBridgeCall = Future<Object?> Function(String method, List<Object?> args);

int _int(Object? v) => v is num ? v.toInt() : int.tryParse('$v') ?? 0;
double _double(Object? v) => v is num ? v.toDouble() : double.tryParse('$v') ?? 0;
String _str(Object? v) => v?.toString() ?? '';
List<Map> _rows(Object? v) => v is List ? v.whereType<Map>().toList() : const [];

class BridgeNotebookApi implements NotebookApi {
  BridgeNotebookApi(this._call);
  final NotebookBridgeCall _call;

  Future<Map<String, Object?>> _request(String cmd, [Map<String, Object?> args = const {}]) async {
    final result = await _call('notebook', [
      <String, Object?>{'cmd': cmd, ...args},
    ]);
    if (result is! Map) throw StateError('노트북 브리지 응답 형식이 잘못되었습니다.');
    final response = Map<String, Object?>.from(result);
    if (response['ok'] != true) {
      throw StateError('${response['message'] ?? '노트북 요청이 실패했습니다.'}');
    }
    return response;
  }

  @override
  Future<List<Notebook>> listNotebooks() async => [
    for (final r in _rows((await _request('nb_list'))['notebooks'])) Notebook(id: _int(r['id']), name: _str(r['name'])),
  ];

  @override
  Future<int> createNotebook(String name) async => _int((await _request('nb_create', {'name': name}))['id']);

  @override
  Future<List<NbSource>> listSources(int notebookId) async => [
    for (final r in _rows((await _request('nb_source_list', {'notebook_id': notebookId}))['sources']))
      NbSource(
        id: _int(r['id']),
        displayName: _str(r['display_name']),
        kind: _str(r['kind']),
        status: _str(r['status']),
        paragraphCount: _int(r['paragraph_count']),
        origin: _str(r['origin']),
      ),
  ];

  @override
  Future<int> addSource(int notebookId, String path) async =>
      _int((await _request('nb_source_add', {'notebook_id': notebookId, 'source_path': path}))['id']);

  @override
  Future<void> removeSource(int notebookId, int sourceId) =>
      _request('nb_source_remove', {'notebook_id': notebookId, 'source_id': sourceId});

  @override
  Future<List<NbParagraph>> paragraphs(int notebookId, int sourceId) async => [
    for (final r in _rows(
      (await _request('nb_source_paragraphs', {'notebook_id': notebookId, 'source_id': sourceId}))['paragraphs'],
    ))
      NbParagraph(
        sourceId: _int(r['source_id']),
        ordinal: _int(r['ordinal']),
        body: _str(r['body']),
        location: _str(r['location']),
        level: _int(r['level']),
        kind: r['kind'] == null ? 'text' : _str(r['kind']),
      ),
  ];

  @override
  Future<List<NbHit>> search(int notebookId, String query, {List<int>? sourceIds, int limit = 20}) async => [
    for (final r in _rows(
      (await _request('nb_search', {
        'notebook_id': notebookId,
        'query': query,
        'limit': limit,
        'source_ids': ?sourceIds,
      }))['results'],
    ))
      NbHit(
        sourceId: _int(r['source_id']),
        ordinal: _int(r['ordinal']),
        displayName: _str(r['display_name']),
        body: _str(r['body']),
        score: _double(r['score']),
        location: _str(r['location']),
      ),
  ];

  @override
  Future<List<NbTransformRow>> transform(int notebookId, String type, {List<int>? sourceIds}) async => [
    for (final r in _rows(
      (await _request('nb_transform', {'notebook_id': notebookId, 'type': type, 'source_ids': ?sourceIds}))['results'],
    ))
      NbTransformRow(
        sourceId: _int(r['source_id']),
        ordinal: _int(r['ordinal']),
        text: _str(r['text']),
        score: _double(r['score']),
        level: _int(r['level']),
      ),
  ];

  @override
  Future<List<NbNote>> listNotes(int notebookId) async => [
    for (final r in _rows((await _request('nb_note_list', {'notebook_id': notebookId}))['notes']))
      NbNote(
        id: _int(r['id']),
        title: _str(r['title']),
        body: _str(r['body']),
        citations: [
          for (final c in _rows(r['citations']))
            NbCitation(
              sourceId: _int(c['source_id']),
              paragraphOrdinal: _int(c['paragraph_ordinal']),
              quote: _str(c['quote']),
            ),
        ],
      ),
  ];

  @override
  Future<int> saveNote(int notebookId, NbNote note) async => _int(
    (await _request('nb_note_save', {
      'notebook_id': notebookId,
      if (note.id != null) 'id': note.id,
      'title': note.title,
      'body': note.body,
      'citations': [
        for (final c in note.citations)
          {'source_id': c.sourceId, 'paragraph_ordinal': c.paragraphOrdinal, 'quote': c.quote},
      ],
    }))['id'],
  );

  @override
  Future<void> deleteNote(int notebookId, int noteId) =>
      _request('nb_note_delete', {'notebook_id': notebookId, 'id': noteId});

  @override
  Future<String> exportMarkdown(int notebookId, int noteId) async =>
      _str((await _request('nb_export_md', {'notebook_id': notebookId, 'note_id': noteId}))['markdown']);

  @override
  Future<void> watchDrops(bool active) => _request('nb_drop_watch', {'active': active});

  @override
  Future<List<String>> takeDroppedPaths() async => [
    for (final p in (await _request('nb_take_drop'))['paths'] as List? ?? const []) '$p',
  ];
}

/// 시험·미리보기용 메모리 구현. 파일 내용은 [fileContents]에서 읽고, 없으면 파일 이름을 한 문단으로 쓴다.
class InMemoryNotebookApi implements NotebookApi {
  InMemoryNotebookApi({Map<String, String>? fileContents}) : _files = fileContents ?? const {};

  final Map<String, String> _files;
  final _notebooks = <Notebook>[];
  final _sources = <int, List<NbSource>>{};
  final _paragraphs = <int, List<NbParagraph>>{};
  final _notes = <int, List<NbNote>>{};
  final _dropped = <String>[];
  int _next = 1;

  /// 드롭 받기가 켜져 있는지(시험 확인용).
  bool watchingDrops = false;

  /// 창에 파일을 끌어 놓은 것처럼 경로를 맡겨 둔다(시험용).
  void queueDrop(List<String> paths) => _dropped.addAll(paths);

  @override
  Future<List<Notebook>> listNotebooks() async => List.of(_notebooks);

  @override
  Future<int> createNotebook(String name) async {
    final id = _next++;
    _notebooks.add(Notebook(id: id, name: name.trim().isEmpty ? '새 노트북' : name.trim()));
    return id;
  }

  @override
  Future<List<NbSource>> listSources(int notebookId) async => List.of(_sources[notebookId] ?? const []);

  @override
  Future<int> addSource(int notebookId, String path) async {
    final trimmed = path.trim();
    if (trimmed.isEmpty) throw StateError('출처 파일 경로를 입력하세요.');
    final name = trimmed.split(RegExp(r'[\\/]')).last;
    final ext = name.contains('.') ? name.split('.').last.toLowerCase() : '';
    final id = _next++;
    final text = _files[trimmed] ?? name;
    final lines = text.split(RegExp(r'\r?\n')).map((l) => l.trim()).where((l) => l.isNotEmpty).toList();
    _paragraphs[id] = [for (var i = 0; i < lines.length; i++) NbParagraph(sourceId: id, ordinal: i, body: lines[i])];
    (_sources[notebookId] ??= []).add(
      NbSource(id: id, displayName: name, kind: ext, status: 'ready', paragraphCount: lines.length, origin: trimmed),
    );
    return id;
  }

  @override
  Future<void> removeSource(int notebookId, int sourceId) async {
    _sources[notebookId]?.removeWhere((s) => s.id == sourceId);
    _paragraphs.remove(sourceId);
  }

  @override
  Future<List<NbParagraph>> paragraphs(int notebookId, int sourceId) async =>
      List.of(_paragraphs[sourceId] ?? const []);

  Iterable<NbSource> _scope(int notebookId, List<int>? ids) =>
      (_sources[notebookId] ?? const <NbSource>[]).where((s) => ids == null || ids.contains(s.id));

  @override
  Future<List<NbHit>> search(int notebookId, String query, {List<int>? sourceIds, int limit = 20}) async {
    final terms = query.split(RegExp(r'\s+')).where((t) => t.isNotEmpty).toList();
    if (terms.isEmpty) return const [];
    final hits = <NbHit>[];
    for (final source in _scope(notebookId, sourceIds)) {
      for (final p in _paragraphs[source.id] ?? const <NbParagraph>[]) {
        final score = terms.where(p.body.contains).length;
        if (score > 0) {
          hits.add(
            NbHit(
              sourceId: source.id,
              ordinal: p.ordinal,
              displayName: source.displayName,
              body: p.body,
              score: score.toDouble(),
            ),
          );
        }
      }
    }
    hits.sort((a, b) => b.score.compareTo(a.score));
    return hits.take(limit).toList();
  }

  @override
  Future<List<NbTransformRow>> transform(int notebookId, String type, {List<int>? sourceIds}) async {
    final rows = <NbTransformRow>[];
    for (final source in _scope(notebookId, sourceIds)) {
      for (final p in _paragraphs[source.id] ?? const <NbParagraph>[]) {
        final keep = switch (type) {
          'numbers' => RegExp(r'\d').hasMatch(p.body),
          'tables' => p.body.contains('\t') || p.body.contains('|'),
          _ => true,
        };
        if (keep) rows.add(NbTransformRow(sourceId: source.id, ordinal: p.ordinal, text: p.body, score: 1));
      }
    }
    return rows;
  }

  @override
  Future<List<NbNote>> listNotes(int notebookId) async => List.of(_notes[notebookId] ?? const []);

  @override
  Future<int> saveNote(int notebookId, NbNote note) async {
    final list = _notes[notebookId] ??= [];
    final id = note.id ?? _next++;
    final saved = note.copyWith(id: id);
    final index = list.indexWhere((n) => n.id == id);
    if (index >= 0) {
      list[index] = saved;
    } else {
      list.insert(0, saved);
    }
    return id;
  }

  @override
  Future<void> deleteNote(int notebookId, int noteId) async => _notes[notebookId]?.removeWhere((n) => n.id == noteId);

  @override
  Future<String> exportMarkdown(int notebookId, int noteId) async {
    final note = (_notes[notebookId] ?? const <NbNote>[]).firstWhere(
      (n) => n.id == noteId,
      orElse: () => throw StateError('노트를 찾을 수 없습니다.'),
    );
    final buffer = StringBuffer('# ${note.title}\n\n${note.body}\n');
    for (final c in note.citations) {
      buffer.write('\n> ${c.quote}\n');
    }
    return buffer.toString();
  }

  @override
  Future<void> watchDrops(bool active) async => watchingDrops = active;

  @override
  Future<List<String>> takeDroppedPaths() async {
    final paths = List.of(_dropped);
    _dropped.clear();
    return paths;
  }
}
