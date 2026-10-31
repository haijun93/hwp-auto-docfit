import 'dart:async';
import 'package:flutter/material.dart';
import 'timemachine_api.dart';
import '../../core/api/abbreviation_api.dart' show ApiCall;

class TimemachineScreen extends StatefulWidget {
  const TimemachineScreen({super.key, required this.api});
  final ApiCall api;
  @override
  State<TimemachineScreen> createState() => _TimemachineScreenState();
}

class _TimemachineScreenState extends State<TimemachineScreen> {
  static const _kinds = {'한/글':'hwp', '문서':'doc', '표':'sheet', '발표':'slide', 'PDF':'pdf', '이미지':'image'};
  late final TimemachineApi _api = TimemachineApi(widget.api);
  Map<String, Object?>? _settings;
  Map<String, int> _days = {};
  final List<TimemachineItem> _items = [];
  final ScrollController _scroll = ScrollController();
  final TextEditingController _search = TextEditingController();
  final Set<String> _selectedKinds = {};
  String _query = '';
  DateTime _month = DateTime(DateTime.now().year, DateTime.now().month);
  DateTime? _start, _end, _firstDay;
  bool _loading = false, _more = true;
  String? _error;
  int _offset = 0;
  int _filterRevision = 0;
  int _requestSerial = 0;
  int _calendarRevision = 0;
  Timer? _debounce;

  @override
  void initState() { super.initState(); _load(); _scroll.addListener(_onScroll); }
  @override
  void dispose() { _debounce?.cancel(); _scroll.dispose(); _search.dispose(); super.dispose(); }

  Future<void> _load() async {
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
    setState(() { _settings = loaded;
      if (status['ok'] != true) _error = '${status['message'] ?? '상태를 불러오지 못했습니다.'}'; });
    if (loaded['enabled'] == true) {
      await _refreshDays();
      if (_start == null || _end == null) {
        _resetRange();
      } else {
        await _loadPage();
      }
    }
  }

  Future<void> _retryConnection() async {
    setState(() { _settings = null; _error = null; });
    await _load();
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
  Future<void> _moveMonth(int amount) async {
    setState(() {
      _month = DateTime(_month.year, _month.month + amount);
      _days = {};
    });
    await _refreshDays();
    _resetRange();
  }
  void _resetRange() {
    _filterRevision++; _requestSerial++; _loading = false;
    _start = DateTime(_month.year, _month.month).toLocal();
    _end = DateTime(_month.year, _month.month + 1).toLocal();
    _firstDay = null; _items.clear(); _offset = 0; _more = true;
    _loadPage();
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
  Future<void> _filtersChanged() async { _filterRevision++; _requestSerial++; _loading = false; _items.clear(); _offset = 0; _more = true; await _refreshDays(); await _loadPage(); }
  Future<void> _enable() async {
    final next = Map<String,Object?>.from(_settings ?? {})..['enabled'] = true;
    Map<String, Object?> saved;
    try { saved = await _api.command('settings_set', next); }
    catch (_) { if (mounted) setState(() => _error = '설정을 저장하지 못했습니다. 앱 연결을 확인해 주세요.'); return; }
    if (saved['ok'] != true) { if (mounted) setState(() => _error = '${saved['message'] ?? '설정을 저장하지 못했습니다.'}'); return; }
    try { await _api.command('scan'); }
    catch (_) { if (mounted) setState(() => _error = '색인 요청을 보내지 못했습니다. 앱 연결을 확인해 주세요.'); }
    await _load();
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
    await _refreshDays(); await _loadPage();
  }
  Future<void> _scan() async {
    try {
      final response = await _api.command('scan');
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
    if (_settings == null) return const Center(child:CircularProgressIndicator());
    if (_settings!['enabled'] != true) return _disabledView();
    return LayoutBuilder(builder:(context,box) {
      final calendar = _calendar(); final timeline = _timeline();
      return Column(children:[_filtersBar(), if (_error != null) MaterialBanner(content:Text(_error!), actions:[TextButton(onPressed:()=>setState(()=>_error=null),child:const Text('닫기'))]),
        Expanded(child:box.maxWidth < 900
          ? Column(children:[ConstrainedBox(constraints:const BoxConstraints(maxHeight:360),child:SingleChildScrollView(child:calendar)),Expanded(child:timeline)])
          : Row(children:[Expanded(flex:3,child:timeline),SizedBox(width:390,child:calendar)]))]);
    });
  }
  Widget _disabledView() {
    final roots = (_settings?['roots'] as List?) ?? const [];
    final disconnected = _error?.contains('연결하지 못했습니다') == true;
    return Center(child:ConstrainedBox(constraints:const BoxConstraints(maxWidth:620),child:Card(child:Padding(padding:const EdgeInsets.all(24),child:Column(mainAxisSize:MainAxisSize.min,crossAxisAlignment:CrossAxisAlignment.start,children:[
      Text('타임머신',style:Theme.of(context).textTheme.headlineSmall), const SizedBox(height:8), const Text('켜면 선택한 폴더의 문서 정보만 색인해 시간순으로 찾아볼 수 있습니다.'), const SizedBox(height:16), const Text('조사 폴더'),
      for(final root in roots) Padding(padding:const EdgeInsets.symmetric(vertical:3),child:Text('• $root')),
      const SizedBox(height:16), FilledButton.icon(onPressed:_enable,icon:const Icon(Icons.power_settings_new),label:const Text('켜기')),
      if (_error != null) Text(_error!,style:const TextStyle(color:Colors.red)),
      if (disconnected) TextButton(onPressed:_retryConnection,child:const Text('다시 연결')),
    ])))));
  }
  Widget _filtersBar() => Padding(padding:const EdgeInsets.fromLTRB(12,8,12,4),child:Wrap(spacing:6,runSpacing:4,crossAxisAlignment:WrapCrossAlignment.center,children:[
    for(final entry in _kinds.entries) FilterChip(label:Text(entry.key),selected:_selectedKinds.contains(entry.value),onSelected:(value){setState(()=>value?_selectedKinds.add(entry.value):_selectedKinds.remove(entry.value));_filtersChanged();}),
    SizedBox(width:220,child:TextField(controller:_search,decoration:const InputDecoration(prefixIcon:Icon(Icons.search),hintText:'이름 찾기',isDense:true),onChanged:(value){_debounce?.cancel();_debounce=Timer(const Duration(milliseconds:300),(){_query=value.trim();_filtersChanged();});})),
    OutlinedButton.icon(onPressed:_scan,icon:const Icon(Icons.refresh),label:const Text('다시 훑기')),
  ]));
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
    final count = _items.length + (_loading ? 1 : 0);
    return ListView.builder(controller:_scroll,itemCount:count,itemBuilder:(context,index){
      if (index >= _items.length) {
        if (_loading) return const Center(child:Padding(padding:EdgeInsets.all(16),child:CircularProgressIndicator()));
        return Center(child:Padding(padding:const EdgeInsets.all(16),child:TextButton(onPressed:_loadPage,child:const Text('더 불러오기'))));
      }
      final item = _items[index];
      final date = DateTime.fromMillisecondsSinceEpoch((item.workTime * 1000).round()).toLocal();
      final day = DateTime(date.year, date.month, date.day);
      final previousDay = index == 0 ? null : DateTime.fromMillisecondsSinceEpoch((_items[index - 1].workTime * 1000).round()).toLocal();
      final showHeading = index == 0 || previousDay == null || !_sameDay(day, previousDay);
      return Column(key: ValueKey('tm-row-${item.id}'), crossAxisAlignment: CrossAxisAlignment.stretch, mainAxisSize: MainAxisSize.min, children:[
        if (showHeading) Padding(padding:const EdgeInsets.fromLTRB(24,14,8,6),child:Text(_localizedDayHeading(day),style:Theme.of(context).textTheme.titleSmall)),
        _itemCard(item,date),
      ]);
    });
  }
  Widget _itemCard(TimemachineItem item,DateTime date) => Padding(padding:const EdgeInsets.fromLTRB(18,2,12,8),child:Row(crossAxisAlignment:CrossAxisAlignment.center,children:[
    SizedBox(width:24,child:Column(mainAxisSize:MainAxisSize.min,children:[Container(width:2,height:8,color:Colors.blue),Container(width:2,height:32,color:Colors.blue.withValues(alpha:.35)),Container(width:9,height:9,decoration:const BoxDecoration(color:Colors.blue,shape:BoxShape.circle))])),
    Expanded(child:Card(child:InkWell(onTap:()=>_openItem(item),child:Padding(padding:const EdgeInsets.all(12),child:Row(children:[Icon(_kindIcon(item.kind)),const SizedBox(width:10),Expanded(child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[Text(item.name,maxLines:1,overflow:TextOverflow.ellipsis,style:const TextStyle(fontWeight:FontWeight.w600)),Text('${date.hour.toString().padLeft(2,'0')}:${date.minute.toString().padLeft(2,'0')}  ·  ${item.folder}',maxLines:1,overflow:TextOverflow.ellipsis,style:Theme.of(context).textTheme.bodySmall),Wrap(spacing:4,children:[if(item.flags.contains('copied'))const _Badge('복사됨'),if(item.flags.contains('new'))const _Badge('새 문서')])])),TextButton(onPressed:()=>_revealItem(item),child:const Text('폴더 열기'))]))))),
  ]));
}

class _Badge extends StatelessWidget {
  const _Badge(this.label); final String label;
  @override Widget build(BuildContext context)=>Container(padding:const EdgeInsets.symmetric(horizontal:6,vertical:2),decoration:BoxDecoration(color:Theme.of(context).colorScheme.secondaryContainer,borderRadius:BorderRadius.circular(8)),child:Text(label,style:Theme.of(context).textTheme.labelSmall));
}
