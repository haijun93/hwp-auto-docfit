import 'dart:async';
import 'dart:math';
import 'package:flutter/material.dart';
import 'package:file_selector/file_selector.dart';
import 'timemachine_api.dart';
import 'timemachine_thumbnails.dart';
import '../../core/api/abbreviation_api.dart' show ApiCall;

class TimemachineScreen extends StatefulWidget {
  const TimemachineScreen({super.key, required this.api});
  final ApiCall api;
  @override
  State<TimemachineScreen> createState() => _TimemachineScreenState();
}

class _TimemachineScreenState extends State<TimemachineScreen> {
  static const _kinds = {'hwpx':'hwp', 'docx':'doc', 'xlsx':'sheet', 'ppt':'slide', 'PDF':'pdf', '이미지':'image'};
  late final TimemachineApi _api = TimemachineApi(widget.api);
  late final TimemachineThumbnailLoader _thumbnails = TimemachineThumbnailLoader(_api);
  bool _watchByAgent = false;
  Timer? _scanPoll;
  Map<String, Object?>? _settings;
  Map<String, int> _days = {};
  Map<int, int> _hourDensity = {for (var i = 0; i < 24; i++) i: 0};
  int _densityRevision = 0;
  final Set<String> _expandedHours = {};
  final List<TimemachineItem> _items = [];
  final ScrollController _scroll = ScrollController();
  final TextEditingController _search = TextEditingController();
  final Set<String> _selectedKinds = {};
  String _query = '';
  bool _contentMode = false, _contentIndexRunning = false;
  Map<String, Object?> _contentProgress = {};
  List<TimemachineContentResult> _contentResults = [];
  bool _contentNeedsReindex = false;
  bool _contentReindexDismissed = false;
  int _contentNeedsReindexCount = 0;
  String? _contentReindexGuide;
  String _contentSort = 'hierarchy_relevance';
  TimemachineContentResult? _selectedContentResult;
  bool _previewLoading = false;
  Map<String, Object?>? _preview;
  int _previewRevision = 0;
  int _contentSearchRevision = 0;
  bool _showOperatorHelp = false;

  // 파일명 모드 열 보기(테이블) 상태
  bool _fileTableView = false;
  List<TimemachineItem> _fileSearchResults = [];
  bool _fileSearchActive = false;
  bool _fileSearchSupported = true;
  int _fileSearchRevision = 0;
  String _fileSortColumn = 'name';
  bool _fileSortAscending = true;
  final Map<String, double> _fileColumnWidths = {
    'name': 140.0,
    'folder': 200.0,
    'size': 70.0,
    'mtime': 110.0,
    'kind': 60.0,
  };
  Timer? _contentPoll;
  DateTime _month = DateTime(DateTime.now().year, DateTime.now().month);
  DateTime? _start, _end, _firstDay;
  bool _loading = false, _more = true;
  String? _error;
  int _offset = 0;
  int _filterRevision = 0;
  int _requestSerial = 0;
  int _calendarRevision = 0;
  Timer? _debounce;
  static const _extensions = ['hwpx','hwp','docx','pptx','xlsx','pdf','txt'];

  @override
  void initState() { super.initState(); _load(firstOpen: true); _scroll.addListener(_onScroll); }
  @override
  void dispose() { _debounce?.cancel(); _scanPoll?.cancel(); _contentPoll?.cancel(); _thumbnails.dispose(); _scroll.dispose(); _search.dispose(); super.dispose(); }

  /// 검색어와 일치하는 글자의 바탕을 노란색으로 칠한다(대소문자 무시).
  Widget _marked(String text, String query, {int? maxLines, TextStyle? style}) {
    final lower = text.toLowerCase(), key = query.toLowerCase();
    if (key.isEmpty || !lower.contains(key)) {
      return Text(text, maxLines: maxLines, overflow: TextOverflow.ellipsis, style: style);
    }
    final spans = <TextSpan>[];
    var at = 0;
    for (var hit = lower.indexOf(key); hit >= 0; hit = lower.indexOf(key, at)) {
      if (hit > at) spans.add(TextSpan(text: text.substring(at, hit)));
      at = hit + key.length;
      spans.add(TextSpan(
        text: text.substring(hit, at),
        style: const TextStyle(backgroundColor: Color(0xFFFFEB3B), color: Colors.black),
      ));
    }
    if (at < text.length) spans.add(TextSpan(text: text.substring(at)));
    return Text.rich(TextSpan(style: style, children: spans), maxLines: maxLines, overflow: TextOverflow.ellipsis);
  }

  /// 다중 검색어 강조 표시
  Widget _markedTerms(String text, Iterable<String> terms, {int? maxLines, TextStyle? style}) {
    final cleanTerms = terms
        .map((t) => t.trim().toLowerCase())
        .where((t) => t.isNotEmpty)
        .toSet()
        .toList();
    if (cleanTerms.isEmpty || text.isEmpty) {
      return Text(text, maxLines: maxLines, overflow: TextOverflow.ellipsis, style: style);
    }
    final lower = text.toLowerCase();
    final intervals = <(int, int)>[];
    for (final term in cleanTerms) {
      var at = 0;
      while (at < lower.length) {
        final hit = lower.indexOf(term, at);
        if (hit < 0) break;
        intervals.add((hit, hit + term.length));
        at = hit + term.length;
      }
    }
    if (intervals.isEmpty) {
      return Text(text, maxLines: maxLines, overflow: TextOverflow.ellipsis, style: style);
    }
    intervals.sort((a, b) {
      final c = a.$1.compareTo(b.$1);
      return c != 0 ? c : b.$2.compareTo(a.$2);
    });
    final merged = <(int, int)>[];
    var curStart = intervals.first.$1;
    var curEnd = intervals.first.$2;
    for (var i = 1; i < intervals.length; i++) {
      final next = intervals[i];
      if (next.$1 <= curEnd) {
        if (next.$2 > curEnd) curEnd = next.$2;
      } else {
        merged.add((curStart, curEnd));
        curStart = next.$1;
        curEnd = next.$2;
      }
    }
    merged.add((curStart, curEnd));

    final spans = <TextSpan>[];
    var last = 0;
    for (final interval in merged) {
      if (interval.$1 > last) {
        spans.add(TextSpan(text: text.substring(last, interval.$1)));
      }
      spans.add(TextSpan(
        text: text.substring(interval.$1, interval.$2),
        style: const TextStyle(backgroundColor: Color(0xFFFFEB3B), color: Colors.black),
      ));
      last = interval.$2;
    }
    if (last < text.length) {
      spans.add(TextSpan(text: text.substring(last)));
    }

    return Text.rich(TextSpan(style: style, children: spans), maxLines: maxLines, overflow: TextOverflow.ellipsis);
  }

  Set<String> _extractKeywords(String query, Iterable<String> extraKeys) {
    final keys = <String>{};
    for (final k in extraKeys) {
      if (k.trim().isNotEmpty) keys.add(k.trim());
    }
    final terms = query.trim().split(RegExp(r'\s+'));
    for (final t in terms) {
      if (t.isEmpty) continue;
      if (t.contains(':')) continue;
      var clean = t;
      if (clean.startsWith('"') && clean.endsWith('"') && clean.length > 2) {
        clean = clean.substring(1, clean.length - 1);
      } else {
        clean = clean.replaceAll(RegExp(r'^["\-]'), '').replaceAll(RegExp(r'["~].*$'), '');
      }
      if (clean.isNotEmpty) keys.add(clean);
    }
    return keys;
  }

  String _formatMatchCounts(TimemachineContentResult result) {
    if (result.matchCounts.isEmpty) {
      return '언급 ${result.totalMatches}회';
    }
    final entries = result.matchCounts.entries.map((e) => '${e.key} ${e.value}').join(' \u00B7 ');
    return '$entries (합계 ${result.totalMatches})';
  }

  List<TimemachineContentResult> _sortContentResults(
      List<TimemachineContentResult> results, String sortKey) {
    final indexed = results.asMap().entries.toList();
    indexed.sort((a, b) {
      final itemA = a.value;
      final itemB = b.value;
      if (sortKey == 'hierarchy_relevance') {
        final hComp = itemA.hierarchyRank.compareTo(itemB.hierarchyRank);
        if (hComp != 0) return hComp;

        final mComp = itemB.totalMatches.compareTo(itemA.totalMatches);
        if (mComp != 0) return mComp;

        final dateA = itemA.mtime > itemA.ctime ? itemA.mtime : itemA.ctime;
        final dateB = itemB.mtime > itemB.ctime ? itemB.mtime : itemB.ctime;
        final dComp = dateB.compareTo(dateA);
        if (dComp != 0) return dComp;

        final bComp = itemB.bm25.compareTo(itemA.bm25);
        if (bComp != 0) return bComp;

        return a.key.compareTo(b.key);
      } else if (sortKey == 'mentions') {
        final mComp = itemB.totalMatches.compareTo(itemA.totalMatches);
        if (mComp != 0) return mComp;

        final dateA = itemA.mtime > itemA.ctime ? itemA.mtime : itemA.ctime;
        final dateB = itemB.mtime > itemB.ctime ? itemB.mtime : itemB.ctime;
        final dComp = dateB.compareTo(dateA);
        if (dComp != 0) return dComp;

        final bComp = itemB.bm25.compareTo(itemA.bm25);
        if (bComp != 0) return bComp;

        return a.key.compareTo(b.key);
      }
      return a.key.compareTo(b.key);
    });
    return indexed.map((e) => e.value).toList();
  }


  Future<void> _contentSearch(String query, {String? sort}) async {
    final searchRev = ++_contentSearchRevision;
    if (query.isEmpty) {
      if (mounted) {
        setState(() {
          _contentResults = [];
          _contentNeedsReindex = false;
          _contentNeedsReindexCount = 0;
          _contentReindexGuide = null;
          _selectedContentResult = null;
          _contentSort = 'hierarchy_relevance';
          _preview = null;
        });
      }
      return;
    }
    setState(() {
      _contentSort = 'hierarchy_relevance';
      _selectedContentResult = null;
      _preview = null;
    });
    try {
       final activeSort = sort ?? _contentSort;
       final response = await _api.command('content_search', {
         'query': query, 'limit': 100,
         if (activeSort != 'hierarchy_relevance') 'sort': activeSort,
       });
       final rawItems = response['items'];
       final items = rawItems is List ? rawItems.map((raw) => TimemachineContentResult.fromJson(Map<String, Object?>.from(raw as Map), query: query)).toList() : <TimemachineContentResult>[];
      if (!mounted || searchRev != _contentSearchRevision || query != _search.text.trim()) return;
      setState(() {
         _contentSort = activeSort;
         _contentNeedsReindex = response['needs_reindex'] == true;
         _contentReindexDismissed = false;
         _contentNeedsReindexCount = (response['needs_reindex_count'] as num?)?.toInt() ?? 0;
         _contentReindexGuide = response['reindex_guide'] as String?;
         _contentResults = _sortContentResults(items, activeSort);
      });
    } catch (_) {
      if (mounted) setState(() => _error = '본문 검색을 수행하지 못했습니다.');
    }
  }

  Future<void> _previewContentResult(TimemachineContentResult result) async {
    final rev = ++_previewRevision;
    setState(() {
      _selectedContentResult = result;
      _previewLoading = true;
      _preview = null;
    });
    try {
      final payload = <String, Object?>{
        if (result.id != null) 'id': result.id,
        if (result.path != null) 'path': result.path,
        'query': _search.text.trim(),
        if (result.position?.page != null) 'page': result.position!.page,
        if (result.position?.sheet != null) 'sheet': result.position!.sheet,
        if (result.position?.row != null) 'row': result.position!.row,
      };
      final response = await _api.command('preview', payload);
      if (!mounted || rev != _previewRevision) return;
      setState(() {
        _preview = response;
        _previewLoading = false;
      });
    } catch (_) {
      if (!mounted || rev != _previewRevision) return;
      setState(() {
        _previewLoading = false;
        _preview = {'ok': false, 'message': '미리보기를 불러오지 못했습니다.'};
      });
    }
  }

  Future<void> _openContentResult(TimemachineContentResult result) async {
    if (result.id != null) {
      await _api.command('open', {'id': result.id});
    } else if (result.path != null && result.path!.isNotEmpty) {
      await _api.command('open', {'path': result.path});
    }
  }
  Future<void> _runFileSearch(String query) async {
    if (!_fileSearchSupported) return;
    final rev = ++_fileSearchRevision;
    try {
      final roots = _settings?['roots'];
      final results = await _api.fileSearch(
        query,
        kinds: _selectedKinds.isEmpty ? null : _selectedKinds.toList(),
        roots: roots is List ? roots.map((e) => '$e').toList() : null,
      );
      if (!mounted || rev != _fileSearchRevision) return;
      setState(() {
        _fileSearchResults = results;
        _fileSearchActive = true;
        _fileSearchSupported = true;
      });
    } catch (_) {
      if (!mounted || rev != _fileSearchRevision) return;
      setState(() {
        _fileSearchSupported = false;
        _fileSearchActive = false;
        _fileSearchResults = [];
        _fileTableView = false;
      });
      _filtersChanged();
    }
  }

  Future<void> _startContentIndex() async {
    final response = await _api.command('content_index_start');
    if (!mounted) return;
    setState(() { _contentProgress = response; _contentIndexRunning = response['running'] == true; });
    if (_contentIndexRunning) _pollContentIndex();
  }
  void _pollContentIndex() {
    _contentPoll?.cancel();
    _contentPoll = Timer(const Duration(seconds: 1), () async {
      try {
        final status = await _api.command('content_index_status');
        if (!mounted) return;
        setState(() { _contentProgress = status; _contentIndexRunning = status['running'] == true; });
        if (_contentIndexRunning) _pollContentIndex();
      } catch (_) { if (mounted) setState(() => _contentIndexRunning = false); }
    });
  }
  Future<void> _cancelContentIndex() async {
    final status = await _api.command('content_index_cancel');
    if (mounted) setState(() { _contentProgress = status; _contentIndexRunning = status['running'] == true; });
  }
  void _toggleContentMode(bool value) {
    setState(() {
      _contentMode = value;
      _contentResults = [];
      _selectedContentResult = null;
      _preview = null;

      _search.clear();
      _query = '';
      _showOperatorHelp = false;
      _contentSort = 'hierarchy_relevance';
      _fileSearchResults = [];
      _fileSearchActive = false;
    });
    if (!value) { _filtersChanged(); }
  }

  Future<void> _load({bool firstOpen = false}) async {
    Map<String, Object?> status;
    Map<String, Object?> settings;
    try {
      status = await _api.command('status');
      settings = await _api.command('settings_get');
    } catch (_) {
      if (mounted) setState(() { _settings = {'roots': [], 'time_mode':'max', 'enabled':false}; _error = '타임머신에 연결하지 못했습니다. 앱 연결을 확인해 주세요.'; });
      return;
    }
    if (!mounted) return;
    if (settings['ok'] != true) {
      setState(() { _settings = {'roots': [], 'time_mode':'max', 'enabled':false}; _error = '${settings['message'] ?? '설정을 불러오지 못했습니다.'}'; });
      return;
    }
    final raw = settings['settings'];
    final loaded = raw is Map ? Map<String, Object?>.from(raw) : {'roots': [], 'time_mode':'max', 'enabled':false};
    setState(() { _settings = loaded; _watchByAgent = status['watch'] == 'agent';
      if (status['ok'] != true) _error = '${status['message'] ?? '상태를 불러오지 못했습니다.'}'; });
    if (loaded['enabled'] == true) {
      // 에이전트가 없으면 앱을 열 때 증분 색인한다(사용자 결정 6). 에이전트가 있으면 폴더 설정만 맞춘다.
      if (firstOpen) { try { await _requestScan(); } catch (_) {} if (!mounted) return; }
      await _refreshDays();
      if (_start == null || _end == null) {
        await _resetRange();
      } else {
        await _refreshHourDensity();
        await _loadPage();
      }
    }
  }

  Future<void> _retryConnection() async {
    setState(() { _settings = null; _error = null; });
    await _load();
  }

  Future<Map<String, Object?>> _requestScan() async {
    final response = await _api.command('scan');
    if (!mounted) return response;
    if (response['by'] != null) setState(() => _watchByAgent = response['by'] == 'agent');
    if (response['running'] == true) _waitForScan();
    return response;
  }
  void _waitForScan() {
    _scanPoll?.cancel();
    _scanPoll = Timer(const Duration(seconds: 1), () async {
      Map<String, Object?> status;
      try { status = await _api.command('status'); } catch (_) { return; }
      if (!mounted) return;
      final scan = status['scan'];
      if (scan is Map && scan['running'] == true) { _waitForScan(); return; }
      await _filtersChanged();
    });
  }

  Map<String, Object?> get _filters => {'roots': _settings?['roots'] ?? [],
    'kinds': _selectedKinds.isEmpty ? null : _selectedKinds.toList(), 'query': _query};
  Future<void> _refreshDays() async {
    final revision = ++_calendarRevision;
    final requestedMonth = _month;
    final response = await _api.command('day_counts', {'year':_month.year, 'month':_month.month, ..._filters});
    if (!mounted || revision != _calendarRevision || _month != requestedMonth || response['ok'] != true) return;
    final raw = response['days']; final values = <String,int>{};
    if (raw is Map) { for (final entry in raw.entries) { final value = entry.value; values['${entry.key}'] = value is Map ? ((value['total'] as num?)?.toInt() ?? 0) : ((value as num?)?.toInt() ?? 0); } }
    setState(() => _days = values);
  }
  Future<void> _refreshHourDensity() async {
    if (_start == null || _end == null) return;
    final revision = ++_densityRevision;
    final response = await _api.command('hour_density', {
      'start': _start!.millisecondsSinceEpoch / 1000,
      'end': _end!.millisecondsSinceEpoch / 1000,
      ..._filters,
    });
    if (!mounted || revision != _densityRevision || response['ok'] != true) return;
    final density = TimemachineHourDensity.fromJson(response);
    setState(() => _hourDensity = density.counts);
  }
  Future<void> _moveMonth(int amount) async {
    setState(() {
      _month = DateTime(_month.year, _month.month + amount);
      _days = {};
    });
    await _refreshDays();
    await _resetRange();
  }
  Future<void> _resetRange() async {
    _filterRevision++; _requestSerial++; _loading = false;
    _start = DateTime(_month.year, _month.month).toLocal();
    _end = DateTime(_month.year, _month.month + 1).toLocal();
    _firstDay = null; _items.clear(); _offset = 0; _more = true;
    await _refreshHourDensity();
    await _loadPage();
  }
  Map<String,Object?> _rangePayload() => {
    'start': _start!.millisecondsSinceEpoch / 1000,
    'end': _end!.millisecondsSinceEpoch / 1000,
    ..._filters, 'newest_first': true, 'limit': 200, 'offset': _offset,
  };
  Future<void> _loadPage() async {
    if (_loading || !_more || _start == null || _end == null) return;
    final revision = _filterRevision;
    final requestSerial = ++_requestSerial;
    setState(() { _loading = true; _error = null; });
    Map<String, Object?> response;
    try { response = await _api.command('range', _rangePayload()); }
    catch (_) {
      if (mounted) setState(() { _loading = false; _more = false; _error = '목록을 불러오지 못했습니다. 앱 연결을 확인해 주세요.'; });
      return;
    }
    if (!mounted) return;
    if (revision != _filterRevision) {
      if (requestSerial == _requestSerial) setState(() => _loading = false);
      return;
    }
    final raw = response['items'];
    setState(() {
      if (response['ok'] == true && raw is List) {
        final page = <TimemachineItem>[];
        for (final entry in raw) {
          if (entry is! Map) continue;
          try {
            page.add(TimemachineItem.fromJson(entry));
          } on Object {
            _error = '목록 응답의 파일 정보를 읽지 못했습니다.';
          }
        }
        _items.addAll(page); _offset += page.length; _more = raw.length == 200;
      } else { _error = '${response['message'] ?? '목록을 불러오지 못했습니다.'}'; _more = false; }
      _loading = false;
    });
  }
  void _onScroll() { if (_more && !_loading && _scroll.hasClients && _scroll.position.extentAfter < 500) _loadPage(); }
  Future<void> _filtersChanged() async { _filterRevision++; _requestSerial++; _loading = false; _items.clear(); _offset = 0; _more = true; await _refreshDays(); _refreshHourDensity(); await _loadPage(); }
  Future<void> _enable() async {
    final next = Map<String,Object?>.from(_settings ?? {})..['enabled'] = true;
    Map<String, Object?> saved;
    try { saved = await _api.command('settings_set', next); }
    catch (_) { if (mounted) setState(() => _error = '설정을 저장하지 못했습니다. 앱 연결을 확인해 주세요.'); return; }
    if (saved['ok'] != true) { if (mounted) setState(() => _error = '${saved['message'] ?? '설정을 저장하지 못했습니다.'}'); return; }
    try { await _requestScan(); }
    catch (_) { if (mounted) setState(() => _error = '색인 요청을 보내지 못했습니다. 앱 연결을 확인해 주세요.'); }
    await _load();
  }
  Future<void> _saveSettings(Map<String,Object?> next) async {
    final response=await _api.command('settings_set',next);
    if(response['ok']==true){setState(()=>_settings=Map<String,Object?>.from(response['settings'] as Map));await _filtersChanged();}
    else if(mounted){setState(()=>_error='${response['message'] ?? '설정을 저장하지 못했습니다.'}');}
  }
  Future<void> _pickExtensions() async {
    final values=List<String>.from((_settings?['extensions'] as List?) ?? _extensions);
    final saved=await showDialog<bool>(context:context,builder:(context)=>StatefulBuilder(builder:(context,update)=>AlertDialog(
      title:const Text('적용 확장자'),
      content:Wrap(spacing:6,runSpacing:4,children:[for(final ext in _extensions) FilterChip(label:Text(ext),selected:values.contains(ext),onSelected:(selected)=>update(()=>selected?values.add(ext):values.remove(ext)))]),
      actions:[TextButton(onPressed:()=>Navigator.pop(context,false),child:const Text('취소')),FilledButton(onPressed:()=>Navigator.pop(context,true),child:const Text('저장'))],
    )));
    if(saved==true&&mounted)await _saveSettings(Map<String,Object?>.from(_settings!)..['extensions']=values);
  }
  Future<void> _addRoot() async {
    final path=await getDirectoryPath(); if(path==null||!mounted)return;
    final roots=List<String>.from((_settings?['roots'] as List?) ?? const [])..add(path);
    await _saveSettings(Map<String,Object?>.from(_settings!)..['roots']=roots);
  }
  Future<void> _chooseDay(DateTime day) async {
    final chosen = DateTime(day.year, day.month, day.day);
    setState(() {
      if (_firstDay != null) {
        if (_sameDay(_firstDay!, chosen)) {
          _start = chosen; _end = chosen.add(const Duration(days: 1)); _firstDay = null;
        } else {
          final first = _firstDay!;
          _start = first.isBefore(chosen) ? first : chosen;
          _end = (first.isAfter(chosen) ? first : chosen).add(const Duration(days: 1));
          _firstDay = null;
        }
      } else if (_start != null && _end != null && _end!.difference(_start!).inDays == 1 && _sameDay(_start!, chosen)) {
        _start = DateTime(_month.year, _month.month); _end = DateTime(_month.year, _month.month + 1);
      } else {
        _firstDay = chosen; _start = chosen; _end = chosen.add(const Duration(days: 1));
      }
      _filterRevision++; _requestSerial++; _loading = false; _items.clear(); _offset = 0; _more = true;
    });
    _refreshHourDensity();
    await _loadPage();
  }
  bool _sameDay(DateTime a, DateTime b) => a.year == b.year && a.month == b.month && a.day == b.day;
  Future<void> _quickRange(String mode) async {
    final now = DateTime.now();
    setState(() {
      _month = DateTime(now.year,now.month);
      if (mode == 'today') { _start = DateTime(now.year,now.month,now.day); _end = _start!.add(const Duration(days:1)); }
      if (mode == 'week') { _start = _sundayStart(now); _end = _start!.add(const Duration(days:7)); }
      if (mode == 'month') { _month = DateTime(now.year,now.month); _start = _month; _end = DateTime(now.year,now.month+1); }
      _firstDay = null; _filterRevision++; _requestSerial++; _loading = false; _items.clear(); _offset = 0; _more = true;
    });
    await _refreshDays(); _refreshHourDensity(); await _loadPage();
  }
  Future<void> _scan() async {
    try {
      final response = await _requestScan();
      if (response['ok'] != true && mounted) setState(() => _error = '${response['message'] ?? '다시 훑지 못했습니다.'}');
      await _load();
    } catch (_) {
      if (mounted) setState(() => _error = '다시 훑지 못했습니다. 앱 연결을 확인해 주세요.');
    }
  }
  Future<void> _openItem(TimemachineItem item) async {
    try { final response = await _api.command('open', {'id':item.id});
      if (response['ok'] != true && mounted) setState(() => _error = '${response['message'] ?? '파일을 열지 못했습니다.'}');
    } catch (_) { if (mounted) setState(() => _error = '파일을 열지 못했습니다. 앱 연결을 확인해 주세요.'); }
  }
  Future<void> _revealItem(TimemachineItem item) async {
    try { final response = await _api.command('reveal', {'id':item.id});
      if (response['ok'] != true && mounted) setState(() => _error = '${response['message'] ?? '폴더를 열지 못했습니다.'}');
    } catch (_) { if (mounted) setState(() => _error = '폴더를 열지 못했습니다. 앱 연결을 확인해 주세요.'); }
  }

  Future<void> _sendToFeature(String feature, int id) async {
    try {
      final response = await _api.command('send_to_feature', {'feature': feature, 'ids': [id]});
      if (!mounted) return;
      if (response['ok'] == true) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('목록에 추가했습니다.')));
      } else {
        setState(() => _error = '${response['message'] ?? '보내지 못했습니다.'}');
      }
    } catch (_) {
      if (mounted) setState(() => _error = '보내지 못했습니다. 앱 연결을 확인해 주세요.');
    }
  }

  Future<void> _findRelated(TimemachineItem item) async {
    final selectedPath = '${item.folder}\\${item.name}';
    try {
      final response = await _api.command('related_search', {'path': selectedPath});
      if (!mounted) return;
      if (response['ok'] != true) {
        setState(() => _error = '${response['message'] ?? '연관 문서를 찾지 못했습니다.'}');
        return;
      }
      final raw = response['items'];
      final items = raw is List
          ? raw.whereType<Map>().map((entry) => Map<String, Object?>.from(entry)).toList()
          : <Map<String, Object?>>[];
      await showDialog<void>(context: context, builder: (dialogContext) => AlertDialog(
        title: const Text('연관 문서'),
        content: SizedBox(width: 520, child: Column(mainAxisSize: MainAxisSize.min, children: [
          Text('선택 문서 작성 기준일: ${response['reference_date_found'] == true && response['reference_date'] != null ? response['reference_date'] : '기준일 없음'}'),
          const SizedBox(height: 8),
          if (items.isEmpty) const Text('연관 문서가 없습니다.') else Flexible(child: ListView(shrinkWrap: true, children: [
            for (final related in items)
              ListTile(
                title: Text('${related['name'] ?? ''}'),
                subtitle: Text('${related['reference_date_found'] == true && related['reference_date'] != null ? related['reference_date'] : '기준일 없음'} · 점수 ${related['score'] ?? 0}\n근거: ${((related['reasons'] as List?) ?? const []).join(', ')}'),
                isThreeLine: true,
                trailing: TextButton(
                  child: const Text('연관 아님'),
                  onPressed: () async {
                    final path = related['path'];
                    if (path is! String) return;
                    try {
                      final excluded = await _api.command('related_exclude', {'selected_path': selectedPath, 'related_path': path});
                      if (excluded['ok'] == true && dialogContext.mounted) {
                        Navigator.of(dialogContext).pop();
                        await _findRelated(item);
                      }
                    } catch (_) {
                      if (mounted) setState(() => _error = '연관 제외를 저장하지 못했습니다.');
                    }
                  },
                ),
              ),
          ])),
        ])),
        actions: [TextButton(onPressed: () => Navigator.pop(dialogContext), child: const Text('닫기'))],
      ));
    } catch (_) {
      if (mounted) setState(() => _error = '연관 문서를 찾지 못했습니다. 앱 연결을 확인해 주세요.');
    }
  }

  Future<void> _clearThumbnailCache() async {
    try {
      final response = await _api.command('thumbnail_cache_clear');
      if (!mounted) return;
      if (response['ok'] == true) {
        _thumbnails.clear();
        setState(() {});
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('썸네일 캐시를 지웠습니다.')));
      } else {
        setState(() => _error = '${response['message'] ?? '캐시를 지우지 못했습니다.'}');
      }
    } catch (_) {
      if (mounted) setState(() => _error = '캐시를 지우지 못했습니다. 앱 연결을 확인해 주세요.');
    }
  }

  String _localizedDayHeading(DateTime value) {
    final now = DateTime.now();
    final today = DateTime(now.year, now.month, now.day);
    final day = DateTime(value.year, value.month, value.day);
    if (_sameDay(day, today)) return '오늘 · ${_localizedWeekday(day)}';
    if (_sameDay(day, today.subtract(const Duration(days: 1)))) {
      return '어제 · ${_localizedWeekday(day)}';
    }
    return '${day.year}년 ${day.month}월 ${day.day}일 · ${_localizedWeekday(day)}';
  }

  String _localizedWeekday(DateTime value) =>
      '${const ['일', '월', '화', '수', '목', '금', '토'][value.weekday % 7]}요일';

  DateTime _sundayStart(DateTime value) =>
      DateTime(value.year, value.month, value.day).subtract(Duration(days: value.weekday % 7));

  IconData _kindIcon(String kind) => switch(kind) {'hwp'=>Icons.description_outlined,'doc'=>Icons.article_outlined,'sheet'=>Icons.table_chart_outlined,'slide'=>Icons.slideshow_outlined,'pdf'=>Icons.picture_as_pdf_outlined,'image'=>Icons.image_outlined,_=>Icons.insert_drive_file_outlined};

  @override
  Widget build(BuildContext context) {
    if (_settings == null) return const Center(child: CircularProgressIndicator());
    if (_settings!['enabled'] != true) return _disabledView();
    return LayoutBuilder(builder: (context, box) {
      final calendar = _calendar();
      final timeline = _timeline();
      final isNarrow = box.maxWidth < 650;
      return Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          _filtersBar(),
          if (_contentMode) _contentSearchPanel(),
          if (_contentMode && _showOperatorHelp) _operatorHelp(),
          if (_contentMode && _contentNeedsReindex && !_contentReindexDismissed && _contentReindexGuide != null)
            MaterialBanner(
              content: Text('$_contentReindexGuide (재색인 필요: $_contentNeedsReindexCount건)'),
              leading: const Icon(Icons.info_outline, color: Colors.amber),
              actions: [
                TextButton(onPressed: _startContentIndex, child: const Text('재색인 시작')),
                TextButton(onPressed: () => setState(() => _contentReindexDismissed = true), child: const Text('닫기')),
              ],
            ),
          if (_error != null)
            MaterialBanner(
              content: Text(_error!),
              actions: [
                TextButton(
                  onPressed: () => setState(() => _error = null),
                  child: const Text('\uB2EB\uAE30'),
                ),
              ],
            ),
          Expanded(
            child: _contentMode
                ? _contentResultsView()
                : (_fileTableView && _fileSearchSupported
                    ? _fileSearchTable(_fileSearchActive ? _fileSearchResults : _items)
                    : (isNarrow
                        ? Column(
                            crossAxisAlignment: CrossAxisAlignment.stretch,
                            children: [
                              _densityBar(vertical: false),
                              ConstrainedBox(
                                constraints: const BoxConstraints(maxHeight: 180),
                                child: SingleChildScrollView(child: calendar),
                              ),
                              Expanded(child: timeline),
                            ],
                          )
                        : Row(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              _densityBar(vertical: true),
                              Expanded(child: timeline),
                              SizedBox(width: 320, child: SingleChildScrollView(child: calendar)),
                            ],
                          ))),
          ),
        ],
      );
    });
  }


  Widget _operatorHelp() => Card(
    margin: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
    color: Theme.of(context).colorScheme.surfaceContainerHighest,
    child: Padding(
      padding: const EdgeInsets.all(12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(Icons.help_outline, size: 18),
              const SizedBox(width: 6),
              const Text('본문 키워드 검색 연산자 안내', style: TextStyle(fontWeight: FontWeight.bold)),
              const Spacer(),
              IconButton(
                icon: const Icon(Icons.close, size: 18),
                tooltip: '닫기',
                onPressed: () => setState(() => _showOperatorHelp = false),
              ),
            ],
          ),
          const SizedBox(height: 6),
          const Text('\u2022 "\uAD6C\uBB38": \uB744\uC5B4\uC4F0\uAE30\uB97C \uD3EC\uD568\uD55C \uC815\uD655\uD55C \uAD6C\uBB38 \uC77C\uCE58\n'
              '\u2022 -\uB0B1\uB9D0 \uB610\uB294 -\uC81C\uC678\uC5B4: \uD2B9\uC815 \uB2E8\uC5B4\uAC00 \uD3EC\uD568\uB41C \uBB38\uC11C \uC81C\uC678\n'
              '\u2022 ext:hwp,pdf: \uD2B9\uC815 \uD655\uC7A5\uC790 \uBB38\uC11C\uB9CC \uAC80\uC0C9\n'
              '\u2022 path:\uD3F4\uB354: \uD2B9\uC815 \uD3F4\uB354 \uACBD\uB85C \uB0B4 \uBB38\uC11C\uB9CC \uAC80\uC0C9\n'
              '\u2022 after:2024-06 \uB610\uB294 before:2024-12: \uBB38\uC11C \uC218\uC815\uC77C \uBC94\uC744 \uD544\uD130\n'
              '\u2022 ~N: N\uB0B1\uB9D0 \uC774\uB0B4 \uADFC\uC811 \uAC80\uC0C9\n'
              '\u2022 \uC5EC\uB7EC \uB2E8\uC5B4 \uC785\uB825 \uC2DC \uAE30\uBCF8 AND \uC5F0\uC0B0\uC774 \uC801\uC6A9\uB418\uBA70, \uD55C\uAE00 \uC870\uC0AC\uAC00 \uBD98\uC740 \uAC8D\uC6B0\uB3C4 \uBD80\uBD84 \uC77C\uCE58\uB85C \uCC3E\uC2B5\uB2C8\uB2E4.',
              style: TextStyle(fontSize: 12, height: 1.4)),
        ],
      ),
    ),
  );

  Widget _contentResultsView() {
    if (_contentResults.isEmpty) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Text(_search.text.trim().isEmpty ? '본문 검색어를 입력해 주세요.' : '일치하는 본문 검색 결과가 없습니다.'),
        ),
      );
    }
    return Row(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Expanded(
          flex: 3,
          child: ListView.builder(
            itemCount: _contentResults.length,
            itemBuilder: (context, index) => _contentResultRow(_contentResults[index], index),
          ),
        ),
        if (_selectedContentResult != null || _previewLoading)
          const VerticalDivider(width: 1),
        if (_selectedContentResult != null || _previewLoading)
          Expanded(
            flex: 2,
            child: _contentPreviewPane(),
          ),
      ],
    );
  }

  Widget _contentResultRow(TimemachineContentResult result, int index) {
    final isSelected = _selectedContentResult == result;
    final keywords = _extractKeywords(_search.text.trim(), result.matchCounts.keys);
    return Padding(
      key: ValueKey('tm-content-row-${result.id ?? result.path ?? index}'),
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
      child: Card(
        color: isSelected ? Theme.of(context).colorScheme.primaryContainer.withValues(alpha: 0.25) : null,
        child: InkWell(
          onTap: () => _previewContentResult(result),
          onDoubleTap: () => _openContentResult(result),
          child: Padding(
            padding: const EdgeInsets.all(12),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Icon(_kindIcon(result.kind), size: 20, color: Theme.of(context).colorScheme.primary),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        result.fileName,
                        style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                    if (result.position != null && result.position!.badgeLabel.isNotEmpty) ...[
                      const SizedBox(width: 6),
                      _Badge(result.position!.badgeLabel),
                    ],
                    if (result.hierarchy.isNotEmpty) ...[
                      const SizedBox(width: 6),
                      _Badge(result.hierarchy),
                    ],
                  ],
                ),
                const SizedBox(height: 4),
                Text(
                  '${result.folderName.isNotEmpty ? '${result.folderName} \u00B7 ' : ''}${result.folderPath}',
                  style: Theme.of(context).textTheme.bodySmall,
                  overflow: TextOverflow.ellipsis,
                ),
                const SizedBox(height: 6),
                _markedTerms(result.snippet, keywords, maxLines: 3, style: Theme.of(context).textTheme.bodyMedium),
                const SizedBox(height: 6),
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(
                      _formatMatchCounts(result),
                      style: TextStyle(
                        color: Theme.of(context).colorScheme.primary,
                        fontSize: 12,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                    if (result.hierarchy.isNotEmpty)
                      Text(
                        '장 제목: ${result.hierarchy}',
                        style: Theme.of(context).textTheme.labelSmall?.copyWith(color: Colors.grey),
                      ),
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _contentPreviewPane() {
    final item = _selectedContentResult;
    if (item == null) return const SizedBox.shrink();
    return Card(
      margin: const EdgeInsets.all(8),
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Row(
              children: [
                Icon(_kindIcon(item.kind), size: 20),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    item.fileName,
                    style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15),
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
                IconButton(
                  icon: const Icon(Icons.close),
                  tooltip: '미리보기 닫기',
                  onPressed: () => setState(() => _selectedContentResult = null),
                ),
              ],
            ),
            const SizedBox(height: 4),
            Text(item.folderPath, style: Theme.of(context).textTheme.bodySmall, overflow: TextOverflow.ellipsis),
            if (item.position != null && item.position!.badgeLabel.isNotEmpty) ...[
              const SizedBox(height: 6),
              Row(
                children: [
                  _Badge(item.position!.badgeLabel),
                  if (item.hierarchy.isNotEmpty) ...[
                    const SizedBox(width: 6),
                    _Badge(item.hierarchy),
                  ],
                ],
              ),
            ],
            const Divider(height: 18),
            Expanded(
              child: _previewLoading
                  ? const Center(child: CircularProgressIndicator())
                  : SingleChildScrollView(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text('\uC77C\uCE58 \uC704\uCE58 \uBCF8\uBB38 \uBBF8\uB9AC\uBCF4\uAE30',
                              style: Theme.of(context).textTheme.labelMedium?.copyWith(
                                    color: Theme.of(context).colorScheme.primary,
                                    fontWeight: FontWeight.bold,
                                  )),
                          const SizedBox(height: 8),
                          _markedTerms(
                            '${_preview?['snippet'] ?? item.snippet}',
                            _extractKeywords(_search.text.trim(), item.matchCounts.keys),
                            style: const TextStyle(fontSize: 13, height: 1.5),
                          ),
                        ],
                      ),
                    ),
            ),
            const SizedBox(height: 10),
            Row(
              mainAxisAlignment: MainAxisAlignment.end,
              children: [
                FilledButton.icon(
                  onPressed: (item.id != null || (item.path != null && item.path!.isNotEmpty))
                      ? () => _openContentResult(item)
                      : null,
                  icon: const Icon(Icons.open_in_new, size: 16),
                  label: const Text('\uBB38\uC11C \uC5F4\uAE30'),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _fileSearchTable(List<TimemachineItem> items) {
    final sorted = List<TimemachineItem>.from(items);
    sorted.sort((a, b) {
      int cmp = 0;
      switch (_fileSortColumn) {
        case 'name':
          cmp = a.name.compareTo(b.name);
          break;
        case 'folder':
          cmp = a.folder.compareTo(b.folder);
          break;
        case 'size':
          cmp = a.size.compareTo(b.size);
          break;
        case 'mtime':
          cmp = a.mtime.compareTo(b.mtime);
          break;
        case 'kind':
          cmp = a.kind.compareTo(b.kind);
          break;
        default:
          cmp = a.name.compareTo(b.name);
      }
      return _fileSortAscending ? cmp : -cmp;
    });

    final columns = [
      ('name', '\uC774\uB984'),
      ('folder', '\uACBD\uB85C'),
      ('size', '\uD06C\uAE30'),
      ('mtime', '\uC218\uC815\uC77C'),
      ('kind', '\uD615\uC2DD'),
    ];

    return LayoutBuilder(
      builder: (context, constraints) {
        final totalWidth = _fileColumnWidths.values.fold<double>(0.0, (a, b) => a + b) + columns.length * 16.0;
        final tableWidth = max(constraints.maxWidth, totalWidth);
        return SingleChildScrollView(
          scrollDirection: Axis.horizontal,
          child: SizedBox(
            width: tableWidth,
            child: Column(
              children: [
                Container(
                  color: Theme.of(context).colorScheme.surfaceContainerHighest,
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                  child: Row(
                    children: [
                      for (final (colKey, colName) in columns) ...[
                        SizedBox(
                          width: _fileColumnWidths[colKey] ?? 100,
                          child: InkWell(
                            key: ValueKey('tm-col-header-$colKey'),
                            onTap: () {
                              setState(() {
                                if (_fileSortColumn == colKey) {
                                  _fileSortAscending = !_fileSortAscending;
                                } else {
                                  _fileSortColumn = colKey;
                                  _fileSortAscending = true;
                                }
                              });
                            },
                            child: Row(
                              mainAxisSize: MainAxisSize.min,
                              children: [
                                Text(colName, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                                const SizedBox(width: 4),
                                if (_fileSortColumn == colKey)
                                  Icon(_fileSortAscending ? Icons.arrow_upward : Icons.arrow_downward, size: 14),
                              ],
                            ),
                          ),
                        ),
                        GestureDetector(
                          key: ValueKey('tm-col-resizer-$colKey'),
                          behavior: HitTestBehavior.translucent,
                          onHorizontalDragUpdate: (details) {
                            setState(() {
                              final cur = _fileColumnWidths[colKey] ?? 100;
                              _fileColumnWidths[colKey] = max(40.0, cur + details.delta.dx);
                            });
                          },
                          child: MouseRegion(
                            cursor: SystemMouseCursors.resizeColumn,
                            child: Container(
                              width: 12,
                              height: 20,
                              alignment: Alignment.center,
                              child: Container(width: 2, height: 16, color: Colors.grey.withValues(alpha: 0.4)),
                            ),
                          ),
                        ),
                      ],
                    ],
                  ),
                ),
                const Divider(height: 1),
                Expanded(
                  child: sorted.isEmpty
                      ? const Center(child: Text('\uD15C\uC2DC\uD560 \uD30C\uC77C\uC774 \uC5C6\uC2B5\uB2C8\uB2E4.'))
                      : ListView.separated(
                          itemCount: sorted.length,
                          separatorBuilder: (context, _) => const Divider(height: 1),
                          itemBuilder: (context, index) {
                            final item = sorted[index];
                            final date = DateTime.fromMillisecondsSinceEpoch((item.mtime * 1000).round()).toLocal();
                            final dateStr = '${date.year}-${date.month.toString().padLeft(2, '0')}-${date.day.toString().padLeft(2, '0')}';
                            final sizeKb = (item.size / 1024).toStringAsFixed(1);
                            return InkWell(
                              key: ValueKey('tm-file-row-${item.id}'),
                              onTap: () => _openItem(item),
                              child: Padding(
                                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                                child: Row(
                                  children: [
                                    SizedBox(
                                      width: _fileColumnWidths['name'] ?? 100,
                                      child: Text(item.name, overflow: TextOverflow.ellipsis),
                                    ),
                                    const SizedBox(width: 12),
                                    SizedBox(
                                      width: _fileColumnWidths['folder'] ?? 100,
                                      child: Text(item.folder, overflow: TextOverflow.ellipsis, style: Theme.of(context).textTheme.bodySmall),
                                    ),
                                    const SizedBox(width: 12),
                                    SizedBox(
                                      width: _fileColumnWidths['size'] ?? 100,
                                      child: Text('${sizeKb}KB', overflow: TextOverflow.ellipsis),
                                    ),
                                    const SizedBox(width: 12),
                                    SizedBox(
                                      width: _fileColumnWidths['mtime'] ?? 100,
                                      child: Text(dateStr, overflow: TextOverflow.ellipsis),
                                    ),
                                    const SizedBox(width: 12),
                                    SizedBox(
                                      width: _fileColumnWidths['kind'] ?? 100,
                                      child: Text(item.kind, overflow: TextOverflow.ellipsis),
                                    ),
                                  ],
                                ),
                              ),
                            );
                          },
                        ),
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  Widget _densityBar({bool vertical = false}) {
    final maximum = _hourDensity.values.fold<int>(0, (a, b) => a > b ? a : b);
    final bars = List.generate(24, (h) {
      final count = _hourDensity[h] ?? 0;
      final ratio = maximum == 0 ? 0.0 : count / maximum;
      final barLength = 4.0 + 36.0 * ratio;
      final color = count > 0
          ? Colors.blue.withValues(alpha: 0.3 + 0.7 * ratio)
          : Colors.grey.withValues(alpha: 0.25);
      return Semantics(
        key: ValueKey('tm-density-bar-$h'),
        container: true,
        excludeSemantics: true,
        label: '$h시, $count개',
        child: Tooltip(
          excludeFromSemantics: true,
          message: '$h시, $count개',
          child: Padding(
            padding: vertical
                ? const EdgeInsets.symmetric(vertical: 2.0, horizontal: 4.0)
                : const EdgeInsets.symmetric(horizontal: 2.5),
            child: vertical
                ? Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      SizedBox(
                        width: 14,
                        child: Text(
                          '$h',
                          style: const TextStyle(fontSize: 8),
                          textAlign: TextAlign.right,
                        ),
                      ),
                      const SizedBox(width: 4),
                      Container(
                        width: barLength,
                        height: 8,
                        decoration: BoxDecoration(
                          color: color,
                          borderRadius: BorderRadius.circular(2),
                        ),
                      ),
                    ],
                  )
                : Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Container(
                        width: 8,
                        height: barLength,
                        decoration: BoxDecoration(
                          color: color,
                          borderRadius: BorderRadius.circular(2),
                        ),
                      ),
                      const SizedBox(height: 2),
                      Text('$h', style: const TextStyle(fontSize: 8)),
                    ],
                  ),
          ),
        ),
      );
    });

    if (vertical) {
      return SizedBox(
        width: 68,
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(vertical: 8),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: bars,
          ),
        ),
      );
    }

    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 4, 16, 4),
      child: SingleChildScrollView(
        scrollDirection: Axis.horizontal,
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.end,
          children: bars,
        ),
      ),
    );
  }
  Widget _disabledView() {
    final roots = (_settings?['roots'] as List?) ?? const [];
    final disconnected = _error?.contains('연결하지 못했습니다') == true;
    return Center(child:ConstrainedBox(constraints:const BoxConstraints(maxWidth:620),child:Card(child:Padding(padding:const EdgeInsets.all(24),child:Column(mainAxisSize:MainAxisSize.min,crossAxisAlignment:CrossAxisAlignment.start,children:[
      Text('타임머신',style:Theme.of(context).textTheme.headlineSmall), const SizedBox(height:8), const Text('켜면 선택한 폴더의 문서 정보만 색인해 시간순으로 찾아볼 수 있습니다.'), const SizedBox(height:16), const Text('조사 폴더'),
      for(final root in roots) Row(children:[Expanded(child:Text('• $root')),IconButton(tooltip:'조사 폴더 삭제',onPressed:(){final next=Map<String,Object?>.from(_settings!)..['roots']=List<String>.from(roots.cast<String>())..remove(root);_saveSettings(next);},icon:const Icon(Icons.close))]),
      OutlinedButton.icon(onPressed:_addRoot,icon:const Icon(Icons.folder_open),label:const Text('조사 폴더 추가')),
      const SizedBox(height:16), FilledButton.icon(onPressed:_enable,icon:const Icon(Icons.power_settings_new),label:const Text('켜기')),
      if (_error != null) Text(_error!,style:const TextStyle(color:Colors.red)),
      if (disconnected) TextButton(onPressed:_retryConnection,child:const Text('다시 연결')),
    ])))));
  }
  Widget _contentSearchPanel() => Padding(
    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
    child: Wrap(
      spacing: 12,
      crossAxisAlignment: WrapCrossAlignment.center,
      children: [
        const Text('위계기반 본문검색', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
        if (_contentIndexRunning) ...[
          const SizedBox(width: 80, child: LinearProgressIndicator()),
          Text('${_contentProgress['seen'] ?? 0}건 확인 · ${_contentProgress['indexed'] ?? 0}건 색인 · 실패 ${_contentProgress['errors'] ?? 0}건', style: const TextStyle(fontSize: 12)),
          TextButton(onPressed: _cancelContentIndex, child: const Text('\uCDE8\uC18C')),
        ] else
          TextButton.icon(
            onPressed: _startContentIndex,
            icon: const Icon(Icons.play_arrow, size: 16),
            label: const Text('\uBCF8\uBB38 \uC0C9\uC778'),
          ),
        if (_contentProgress['errors'] != null)
          Text('추출 실패 ${_contentProgress['errors']}건', style: const TextStyle(fontSize: 12, color: Colors.red)),
        Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Text('정렬: ', style: TextStyle(fontSize: 12)),
            DropdownButton<String>(
              key: const ValueKey('tm-content-sort-dropdown'),
              value: _contentSort,
              isDense: true,
              items: const [
                DropdownMenuItem(value: 'hierarchy_relevance', child: Text('위계기반 연관도')),
                DropdownMenuItem(value: 'mentions', child: Text('언급 횟수 많은 순')),
              ],
              onChanged: (val) {
                if (val != null) {
                    _contentSearch(_search.text.trim(), sort: val);
                }
              },
            ),
          ],
        ),
        Text('검색 결과 ${_contentResults.length}건', style: const TextStyle(fontSize: 12)),
      ],
    ),
  );
  Widget _filtersBar() => Padding(padding:const EdgeInsets.fromLTRB(12,8,12,4),child:SingleChildScrollView(scrollDirection:Axis.horizontal,child:Row(children:[
    OutlinedButton.icon(onPressed:_pickExtensions,icon:const Icon(Icons.tune,size:16),label:const Text('확장자')),

    for(final entry in _kinds.entries) FilterChip(label:Text(entry.key),selected:_selectedKinds.contains(entry.value),onSelected:(value){setState(()=>value?_selectedKinds.add(entry.value):_selectedKinds.remove(entry.value));_filtersChanged();if(_fileTableView && _fileSearchSupported){_runFileSearch(_search.text.trim());}}),
    SegmentedButton<bool>(segments:const [ButtonSegment(value:false,label:Text('파일명')),ButtonSegment(value:true,label:Text('본문'))],selected:{_contentMode},onSelectionChanged:(values)=>_toggleContentMode(values.first)),
    SizedBox(width:180,child:TextField(controller:_search,decoration:InputDecoration(prefixIcon:const Icon(Icons.search),hintText:_contentMode?'본문 검색':'이름 찾기',isDense:true),onChanged:(value){_debounce?.cancel();_debounce=Timer(const Duration(milliseconds:300),(){final trimmed=value.trim();if(_contentMode){_contentSearch(trimmed);}else{_query=trimmed;_filtersChanged();if(_fileTableView || _fileSearchActive){_runFileSearch(trimmed);}}});})),
    if (_contentMode)
      IconButton(
        icon: const Icon(Icons.help_outline),
        tooltip: '검색 연산자 도움말',
        onPressed: () => setState(() => _showOperatorHelp = !_showOperatorHelp),
      )
    else if (_fileSearchSupported)
      IconButton(
        icon: Icon(_fileTableView ? Icons.view_timeline : Icons.table_chart),
        tooltip: _fileTableView ? '타임라인 보기' : '열 보기',
        onPressed: () {
          if (!_fileSearchSupported) return;
          setState(() => _fileTableView = !_fileTableView);
          if (_fileTableView) {
            _runFileSearch(_search.text.trim());
          }
        },
      ),
    OutlinedButton.icon(onPressed:_scan,icon:const Icon(Icons.refresh),label:const Text('다시 훑기')),
    OutlinedButton.icon(key:const ValueKey('tm-clear-thumb-cache'),onPressed:_clearThumbnailCache,icon:const Icon(Icons.delete_outline),label:const Text('썸네일 캐시 지우기')),
    Text(_watchByAgent ? '실시간 감시: K에이전트' : '실시간 감시: 앱을 열 때만',key:const ValueKey('tm-watch-status'),style:Theme.of(context).textTheme.bodySmall),
  ])));
  Widget _calendar() {
    final first = DateTime(_month.year,_month.month,1); final offset = first.weekday%7; final cells = ((offset+DateTime(_month.year,_month.month+1,0).day+6)~/7)*7;
    final maximum = _days.values.fold<int>(0,(a,b)=>a>b?a:b);
    return Card(margin:const EdgeInsets.all(12),child:Padding(padding:const EdgeInsets.all(12),child:Column(mainAxisSize:MainAxisSize.min,children:[
      Row(children:[IconButton(onPressed:()=>_moveMonth(-1),icon:const Icon(Icons.chevron_left)),Expanded(child:Center(child:Text('${_month.year}년 ${_month.month}월',style:Theme.of(context).textTheme.titleMedium))),IconButton(onPressed:()=>_moveMonth(1),icon:const Icon(Icons.chevron_right))]),
      Row(key:const ValueKey('tm-calendar-weekdays'),mainAxisAlignment:MainAxisAlignment.spaceAround,children:const ['일','월','화','수','목','금','토'].map((e)=>SizedBox(width:36,child:Center(child:Text(e)))).toList()),
      for(var row=0;row<cells~/7;row++) Row(mainAxisAlignment:MainAxisAlignment.spaceAround,children:[for(var col=0;col<7;col++) _dateCell(row*7+col-offset,DateTime(_month.year,_month.month,1+row*7+col-offset), maximum)]),
      Wrap(spacing:4,children:[TextButton(onPressed:()=>_quickRange('today'),child:const Text('오늘')),TextButton(onPressed:()=>_quickRange('week'),child:const Text('이번 주')),TextButton(onPressed:()=>_quickRange('month'),child:const Text('이번 달'))]),
    ])));
  }
  Widget _dateCell(int index,DateTime date,int maximum) {
    if(index<0 || date.month!=_month.month) return const SizedBox(width:36,height:36);
    final count=_days['${date.day}']??0; final alpha=maximum==0?0.04:0.08+0.42*count/maximum;
    return SizedBox(width:36,height:36,child:TextButton(key:ValueKey('tm-day-${date.day}'),style:TextButton.styleFrom(backgroundColor:Colors.blue.withValues(alpha:alpha),padding:EdgeInsets.zero),onPressed:()=>_chooseDay(date),child:Text('${date.day}')));
  }
  Widget _timeline() {
    if (_items.isEmpty && !_loading) return const Center(child: Padding(padding: EdgeInsets.all(24), child: Text('이 기간에 기록된 파일이 없습니다.')));
    final entries = _groupTimeline(_items);
    final count = entries.length + (_loading || _more ? 1 : 0);
    return ListView.builder(
      controller: _scroll,
      itemCount: count,
      itemBuilder: (context, index) {
        if (index >= entries.length) {
          if (_loading) return const Center(child: Padding(padding: EdgeInsets.all(16), child: CircularProgressIndicator()));
          return Center(child: Padding(padding: const EdgeInsets.all(16), child: TextButton(onPressed: _loadPage, child: const Text('더 불러오기'))));
        }
        final entry = entries[index];
        final entryDate = entry.isGroup ? entry.hourStart! : entry.localTime!;
        final day = DateTime(entryDate.year, entryDate.month, entryDate.day);
        final prevDate = index == 0 ? null : (entries[index - 1].isGroup ? entries[index - 1].hourStart! : entries[index - 1].localTime!);
        final prevDay = prevDate == null ? null : DateTime(prevDate.year, prevDate.month, prevDate.day);
        final showHeading = index == 0 || prevDay == null || !_sameDay(day, prevDay);
        return Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          mainAxisSize: MainAxisSize.min,
          children: [
            if (showHeading)
              Padding(padding: const EdgeInsets.fromLTRB(24, 14, 8, 6), child: Text(_localizedDayHeading(day), style: Theme.of(context).textTheme.titleSmall)),
            if (entry.isGroup)
              _hourGroupCard(entry)
            else
              _itemCard(entry.item!, entry.localTime!),
          ],
        );
      },
    );
  }

  Widget _hourGroupCard(_TimelineEntry group) {
    final hourStart = group.hourStart!;
    final keyStr = hourStart.toIso8601String();
    final isExpanded = _expandedHours.contains(keyStr);
    final label = _hourGroupLabel(hourStart, group.files.length);
    return Padding(
      padding: const EdgeInsets.fromLTRB(18, 2, 12, 8),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        mainAxisSize: MainAxisSize.min,
        children: [
          Card(
            key: ValueKey('tm-group-$keyStr'),
            child: InkWell(
              onTap: () {
                setState(() {
                  if (isExpanded) {
                    _expandedHours.remove(keyStr);
                  } else {
                    _expandedHours.add(keyStr);
                  }
                });
              },
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                child: Row(
                  children: [
                    const Icon(Icons.folder_zip_outlined, color: Colors.blue),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Text(label, style: const TextStyle(fontWeight: FontWeight.w600)),
                    ),
                    Icon(isExpanded ? Icons.expand_less : Icons.expand_more),
                  ],
                ),
              ),
            ),
          ),
          if (isExpanded)
            for (final file in group.files)
              _itemCard(file, DateTime.fromMillisecondsSinceEpoch((file.workTime * 1000).round()).toLocal()),
        ],
      ),
    );
  }

  Widget _itemCard(TimemachineItem item, DateTime date) => Padding(
    key: ValueKey('tm-row-${item.id}'),
    padding: const EdgeInsets.fromLTRB(18, 2, 12, 8),
    child: Row(
      crossAxisAlignment: CrossAxisAlignment.center,
      children: [
        SizedBox(
          width: 24,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Container(width: 2, height: 8, color: Colors.blue),
              Container(width: 2, height: 32, color: Colors.blue.withValues(alpha: .35)),
              Container(width: 9, height: 9, decoration: const BoxDecoration(color: Colors.blue, shape: BoxShape.circle)),
            ],
          ),
        ),
        Expanded(
          child: Card(
            child: InkWell(
              onTap: () => _openItem(item),
              child: Padding(
                padding: const EdgeInsets.all(12),
                child: Row(
                  children: [
                    TimemachineThumbnail(item: item, icon: _kindIcon(item.kind), loader: _thumbnails),
                    const SizedBox(width: 10),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          _marked(item.name, _contentMode ? '' : _query, maxLines: 1, style: const TextStyle(fontWeight: FontWeight.w600)),
                          Text('${date.hour.toString().padLeft(2, '0')}:${date.minute.toString().padLeft(2, '0')}  ·  ${item.folder}', maxLines: 1, overflow: TextOverflow.ellipsis, style: Theme.of(context).textTheme.bodySmall),
                          Wrap(spacing: 4, children: [if (item.flags.contains('copied')) const _Badge('복사됨'), if (item.flags.contains('new')) const _Badge('새 문서')]),
                        ],
                      ),
                    ),
                    TextButton(onPressed: () => _revealItem(item), child: const Text('폴더 열기')),
                    PopupMenuButton<String>(
                      key: ValueKey('tm-send-menu-${item.id}'),
                      tooltip: '다른 기능으로 보내기',
                      icon: const Icon(Icons.more_vert),
                      onSelected: (feature) { if (feature == 'related') { _findRelated(item); } else { _sendToFeature(feature, item.id); } },
                      itemBuilder: (context) => const [
                        PopupMenuItem(value: 'related', child: Text('연관 문서 찾기')),
                        PopupMenuItem(value: 'rename_batch', child: Text('파일명 일괄변경 목록에 추가')),
                        PopupMenuItem(value: 'convert', child: Text('파일변환 목록에 추가')),
                        PopupMenuItem(value: 'document_edit', child: Text('문서편집 목록에 추가')),
                      ],
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
      ],
    ),
  );
}

class _TimelineEntry {
  const _TimelineEntry.file(this.item, this.localTime) : files = const [], hourStart = null;
  const _TimelineEntry.group(this.hourStart, this.files) : item = null, localTime = null;
  final TimemachineItem? item;
  final DateTime? localTime;
  final DateTime? hourStart; // 지역 시각 정각
  final List<TimemachineItem> files;
  bool get isGroup => hourStart != null;
}

List<_TimelineEntry> _groupTimeline(List<TimemachineItem> newestFirst) {
  if (newestFirst.isEmpty) return const [];
  final entries = <_TimelineEntry>[];
  var i = 0;
  while (i < newestFirst.length) {
    final firstItem = newestFirst[i];
    final firstDate = DateTime.fromMillisecondsSinceEpoch((firstItem.workTime * 1000).round()).toLocal();
    final hourWindow = DateTime(firstDate.year, firstDate.month, firstDate.day, firstDate.hour);

    var j = i + 1;
    while (j < newestFirst.length) {
      final nextItem = newestFirst[j];
      final nextDate = DateTime.fromMillisecondsSinceEpoch((nextItem.workTime * 1000).round()).toLocal();
      final nextWindow = DateTime(nextDate.year, nextDate.month, nextDate.day, nextDate.hour);
      if (nextWindow != hourWindow) {
        break;
      }
      j++;
    }

    final count = j - i;
    if (count > 5) {
      final groupFiles = newestFirst.sublist(i, j);
      entries.add(_TimelineEntry.group(hourWindow, groupFiles));
    } else {
      for (var k = i; k < j; k++) {
        final item = newestFirst[k];
        final local = DateTime.fromMillisecondsSinceEpoch((item.workTime * 1000).round()).toLocal();
        entries.add(_TimelineEntry.file(item, local));
      }
    }
    i = j;
  }
  return entries;
}

String _hourGroupLabel(DateTime hourStart, int count) {
  if (hourStart.hour == 23) {
    return '23:00~24:00 파일 $count개';
  }
  final startStr = hourStart.hour.toString().padLeft(2, '0');
  final endStr = (hourStart.hour + 1).toString().padLeft(2, '0');
  return '$startStr:00~$endStr:00 파일 $count개';
}

class _Badge extends StatelessWidget {
  const _Badge(this.label); final String label;
  @override Widget build(BuildContext context)=>Container(padding:const EdgeInsets.symmetric(horizontal:6,vertical:2),decoration:BoxDecoration(color:Theme.of(context).colorScheme.secondaryContainer,borderRadius:BorderRadius.circular(8)),child:Text(label,style:Theme.of(context).textTheme.labelSmall));
}
