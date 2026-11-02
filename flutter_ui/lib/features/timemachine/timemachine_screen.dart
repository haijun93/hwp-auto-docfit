import 'dart:async';
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
  List<Map<String, Object?>> _contentResults = [];
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

  Future<void> _contentSearch(String query) async {
    if (query.isEmpty) { if (mounted) setState(() => _contentResults = []); return; }
    try {
      final response = await _api.command('content_search', {'query': query, 'limit': 100});
      if (!mounted || query != _search.text.trim()) return;
      final raw = response['items'];
      setState(() => _contentResults = response['ok'] == true && raw is List
          ? raw.whereType<Map>().map((e) => Map<String,Object?>.from(e)).toList() : []);
    } catch (_) { if (mounted) setState(() => _error = '본문 검색을 수행하지 못했습니다.'); }
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
    setState(() { _contentMode = value; _contentResults = []; _search.clear(); _query = ''; });
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
      if (mode == 'week') { _start = DateTime(now.year,now.month,now.day).subtract(Duration(days:now.weekday-1)); _end = _start!.add(const Duration(days:7)); }
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
      '${const ['월', '화', '수', '목', '금', '토', '일'][value.weekday - 1]}요일';

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
          if (_contentMode && _contentResults.isNotEmpty)
            ConstrainedBox(constraints:const BoxConstraints(maxHeight:180),child:ListView.builder(itemCount:_contentResults.length,itemBuilder:(context,index){
              final row=_contentResults[index];
              return ListTile(dense:true,title:_marked('${row['name'] ?? ''}',_search.text.trim()),subtitle:_marked('${row['snippet'] ?? ''}',_search.text.trim(),maxLines:2));
            })),
          if (_error != null)
            MaterialBanner(
              content: Text(_error!),
              actions: [
                TextButton(
                  onPressed: () => setState(() => _error = null),
                  child: const Text('닫기'),
                ),
              ],
            ),
          Expanded(
            child: isNarrow
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
                  ),
          ),
        ],
      );
    });
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
  Widget _contentSearchPanel() => Padding(padding:const EdgeInsets.symmetric(horizontal:12),child:Row(children:[
    if (_contentIndexRunning) Expanded(child:LinearProgressIndicator()),
    if (_contentIndexRunning) Text('${_contentProgress['seen'] ?? 0}건 확인 · ${_contentProgress['indexed'] ?? 0}건 색인 · 실패 ${_contentProgress['errors'] ?? 0}건'),
    if (_contentIndexRunning) TextButton(onPressed:_cancelContentIndex,child:const Text('취소')) else TextButton(onPressed:_startContentIndex,child:const Text('본문 색인')),
    if (_contentProgress['errors'] != null) Text('추출 실패 ${_contentProgress['errors']}건'),
    Expanded(child:Text('검색 결과 ${_contentResults.length}건')),
  ]));
  Widget _filtersBar() => Padding(padding:const EdgeInsets.fromLTRB(12,8,12,4),child:SingleChildScrollView(scrollDirection:Axis.horizontal,child:Row(children:[
    OutlinedButton.icon(onPressed:_pickExtensions,icon:const Icon(Icons.tune,size:16),label:const Text('확장자')),

    for(final entry in _kinds.entries) FilterChip(label:Text(entry.key),selected:_selectedKinds.contains(entry.value),onSelected:(value){setState(()=>value?_selectedKinds.add(entry.value):_selectedKinds.remove(entry.value));_filtersChanged();}),
    SegmentedButton<bool>(segments:const [ButtonSegment(value:false,label:Text('파일명')),ButtonSegment(value:true,label:Text('본문'))],selected:{_contentMode},onSelectionChanged:(values)=>_toggleContentMode(values.first)),
    SizedBox(width:180,child:TextField(controller:_search,decoration:InputDecoration(prefixIcon:const Icon(Icons.search),hintText:_contentMode?'본문 검색':'이름 찾기',isDense:true),onChanged:(value){_debounce?.cancel();_debounce=Timer(const Duration(milliseconds:300),(){if(_contentMode){_contentSearch(value.trim());}else{_query=value.trim();_filtersChanged();}});})),
    OutlinedButton.icon(onPressed:_scan,icon:const Icon(Icons.refresh),label:const Text('다시 훑기')),
    OutlinedButton.icon(key:const ValueKey('tm-clear-thumb-cache'),onPressed:_clearThumbnailCache,icon:const Icon(Icons.delete_outline),label:const Text('썸네일 캐시 지우기')),
    Text(_watchByAgent ? '실시간 감시: K에이전트' : '실시간 감시: 앱을 열 때만',key:const ValueKey('tm-watch-status'),style:Theme.of(context).textTheme.bodySmall),
  ])));
  Widget _calendar() {
    final first = DateTime(_month.year,_month.month,1); final offset = first.weekday-1; final cells = ((offset+DateTime(_month.year,_month.month+1,0).day+6)~/7)*7;
    final maximum = _days.values.fold<int>(0,(a,b)=>a>b?a:b);
    return Card(margin:const EdgeInsets.all(12),child:Padding(padding:const EdgeInsets.all(12),child:Column(mainAxisSize:MainAxisSize.min,children:[
      Row(children:[IconButton(onPressed:()=>_moveMonth(-1),icon:const Icon(Icons.chevron_left)),Expanded(child:Center(child:Text('${_month.year}년 ${_month.month}월',style:Theme.of(context).textTheme.titleMedium))),IconButton(onPressed:()=>_moveMonth(1),icon:const Icon(Icons.chevron_right))]),
      Row(mainAxisAlignment:MainAxisAlignment.spaceAround,children:const ['월','화','수','목','금','토','일'].map((e)=>SizedBox(width:34,child:Center(child:Text(e)))).toList()),
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
                      onSelected: (feature) => _sendToFeature(feature, item.id),
                      itemBuilder: (context) => const [
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
