import '../../core/close_guards.dart';
import 'dart:async';
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../../core/api/abbreviation_api.dart';

class DocumentToolsWorkspace extends StatefulWidget {
  const DocumentToolsWorkspace({
    super.key,
    required this.api,
    this.initial = 'outline',
    this.initialPath = '',
  });
  final ApiCall api;
  final String initial, initialPath;
  @override
  State<DocumentToolsWorkspace> createState() => _ToolsState();
}

class _ToolsState extends State<DocumentToolsWorkspace> {
  final input = TextEditingController(),
      output = TextEditingController(),
      path = TextEditingController(),
      search = TextEditingController();
  final searchFocus = FocusNode();
  late String mode;
  String revision = '', saved = '', status = '';
  bool busy = false, closing = false;
  bool _loading = false;
  int _loadVersion = 0;
  int _inputRevision = 0, _queuedOperations = 0;
  String _observedInput = '';
  Future<void> _pendingOp = Future.value();
  Timer? autosave;
  List<int>? visible;
  List proofreadIssues = [];
  final Set<String> approvedRules = {};
  String sourceRevision = '',
      calculation = 'col_sum',
      advancedAction = 'markdown',
      preset = '보고서';
  final otherPath = TextEditingController(), pages = TextEditingController();
  static const modes = {
    'outline': '아웃라이너',
    'clean': 'AI 답변 기호 정리',
    'convert': '개조식 변환',
    'labels': '라벨 텍스트 변환',
    'amount': '금액 한글화',
    'commas': '숫자 쉼표',
    'weekdays': '날짜·요일',
    'date_diff': '날짜 차이 (두 날짜를 줄로 구분)',
    'age': '만 나이',
    'mask_rrn': '주민번호 가리기',
    'table_calc': '표 합계',
    'review': '문서 구조 검토',
    'proofread': '공공언어 검토',
    'numbers': '본문·표 수치 대조',
    'markdown': 'Markdown 내보내기',
    'prompt': 'AI 공문서 요청문',
    'advanced': '고급 구조 분석·비교·생성',
  };
  late final CloseLease _closeLease;
  Future<bool> _prepareHostClose() async {
    if (busy || _queuedOperations > 0 || _loading) return false;
    if (!canCloseEditor(context)) return false;
    await leave();
    return true;
  }

  @override
  void initState() {
    super.initState();
    _closeLease = CloseGuards.register(_prepareHostClose);
    mode = modes.containsKey(widget.initial) ? widget.initial : 'clean';
    input.addListener(_recordInput);
    path.text = widget.initialPath;
    load();
  }

  @override
  void dispose() {
    _closeLease.release();
    autosave?.cancel();
    input.removeListener(_recordInput);
    input.dispose();
    output.dispose();
    path.dispose();
    search.dispose();
    searchFocus.dispose();
    otherPath.dispose();
    pages.dispose();
    super.dispose();
  }

  void _recordInput() {
    if (_observedInput != input.text) {
      _observedInput = input.text;
      _inputRevision++;
    }
  }

  bool get dirty => mode == 'outline' && input.text != saved;
  int get index =>
      input.text
          .substring(0, input.selection.baseOffset.clamp(0, input.text.length))
          .split('\n')
          .length -
      1;
  Future<Map> call(String name, Map payload) async {
    final raw = await widget.api('document_tool', [name, payload]);
    if (raw is! Map || raw['ok'] != true) {
      final problem = raw is Map ? raw['error'] : null;
      throw Exception(
        problem is Map ? problem['message'] ?? '연결 응답을 확인해 주세요.' : '응답 형식 오류',
      );
    }
    return raw['data'] as Map;
  }

  Future<void> load() async {
    if (mode != 'outline') return;
    final version = ++_loadVersion;
    final inputRevision = _inputRevision;
    autosave?.cancel();
    setState(() => _loading = true);
    try {
      final data = await call('outline.load', {});
      if (mounted && mode == 'outline' && version == _loadVersion) {
        setState(() {
          if (_inputRevision == inputRevision) {
            input.text = '${data['text']}';
          } else {
            status = '불러오는 동안 바뀐 입력을 보존했습니다.';
          }
          saved = '${data['text']}';
          revision = '${data['revision']}';
        });
      }
    } catch (e) {
      if (mounted && version == _loadVersion) setState(() => status = '$e');
    } finally {
      if (mounted && version == _loadVersion) setState(() => _loading = false);
    }
  }

  void changed() {
    setState(() {});
    if (mode == 'outline') {
      autosave?.cancel();
      autosave = Timer(const Duration(milliseconds: 800), () => save());
    }
  }

  Future<bool> save() async {
    if (_loading) return false;
    if (_queuedOperations > 0) {
      autosave?.cancel();
      autosave = Timer(const Duration(milliseconds: 800), () => save());
      return false;
    }
    if (busy || !dirty) return !dirty;
    final snapshot = input.text;
    setState(() => busy = true);
    try {
      final data = await call('outline.save', {
        'text': snapshot,
        'revision': revision,
      });
      if (mounted) {
        setState(() {
          revision = '${data['revision']}';
          saved = snapshot;
          status = '초안 저장됨';
        });
      }
      return !dirty;
    } catch (e) {
      if (mounted) setState(() => status = '$e');
      return false;
    } finally {
      if (mounted) {
        setState(() => busy = false);
        if (dirty && saved == snapshot) {
          autosave = Timer(const Duration(milliseconds: 800), () => save());
        }
      }
    }
  }

  Future<void> edit(String action, {bool up = false}) {
    if (!mounted || busy || closing || _loading) return Future.value();
    autosave?.cancel();
    setState(() => _queuedOperations++);
    final next = _pendingOp.then((_) => _editOne(action, up: up)).whenComplete(
      () {
        if (mounted) {
          setState(() => _queuedOperations--);
        } else {
          _queuedOperations--;
        }
      },
    );
    _pendingOp = next.catchError((Object error) {
      if (mounted) setState(() => status = '$error');
    });
    return _pendingOp;
  }

  Future<void> _editOne(String action, {bool up = false}) async {
    if (!mounted || mode != 'outline') return;
    if (busy) return;
    autosave?.cancel();
    String note = '';
    if (action == 'note') {
      final controller = TextEditingController();
      final value = await showDialog<String>(
        context: context,
        builder: (ctx) => AlertDialog(
          title: const Text('메모 추가'),
          content: TextField(controller: controller, autofocus: true),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(ctx, controller.text),
              child: const Text('추가'),
            ),
          ],
        ),
      );
      controller.dispose();
      if (value == null) return;
      note = value;
    }
    try {
      final requestRevision = _inputRevision;
      final data = await call('outline.$action', {
        'text': input.text,
        'index': index,
        'up': up,
        'note': note,
      });
      if (!mounted) return;
      if (mode != 'outline' || _inputRevision != requestRevision) {
        setState(() => status = '추가 입력을 보존했습니다. 해당 작업을 다시 실행해 주세요.');
        changed();
        return;
      }
      setState(() {
        input.text = '${data['text']}';
        final row = (data['index'] as num?)?.toInt() ?? 0;
        final offset = input.text
            .split('\n')
            .take(row)
            .fold<int>(0, (sum, line) => sum + line.length + 1);
        input.selection = TextSelection.collapsed(
          offset: offset.clamp(0, input.text.length),
        );
      });
      changed();
    } catch (e) {
      if (mounted) setState(() => status = '$e');
    }
  }

  Future<void> run() async {
    if (busy) return;
    setState(() => busy = true);
    try {
      final name = mode == 'convert'
          ? 'outline'
          : mode == 'outline'
          ? 'outline.export'
          : mode;
      String? prompt;
      if (mode == 'prompt') {
        final choices = await call('prompts', {});
        if (!mounted) return;
        prompt = await showDialog<String>(
          context: context,
          builder: (ctx) => SimpleDialog(
            title: const Text('공문서 요청문 선택'),
            children: [
              for (final item in choices['prompts'] as List)
                SimpleDialogOption(
                  onPressed: () => Navigator.pop(ctx, item['name'] as String),
                  child: Text('${item['name']}'),
                ),
            ],
          ),
        );
        if (prompt == null) return;
      }
      var data = await call(mode == 'advanced' ? 'advanced.start' : name, {
        'text': input.text,
        'path': path.text,
        'operation': calculation,
        'action': advancedAction,
        'other': otherPath.text,
        'pages': pages.text,
        'preset': preset,
        'name': prompt,
      });
      if (mode == 'advanced') {
        final job = '${data['id']}';
        while (data['status'] == 'running') {
          if (!mounted) return;
          await Future<void>.delayed(const Duration(milliseconds: 400));
          data = await call('advanced.poll', {'id': job});
        }
        if (data['status'] == 'failed') {
          final failure = data['error'];
          throw Exception(failure is Map ? failure['message'] : '고급 작업 실패');
        }
        data = data['result'] as Map;
      }
      if (mounted) {
        setState(() {
          output.text = data.containsKey('text')
              ? '${data['text']}'
              : const JsonEncoder.withIndent('  ').convert(data);
          if (data['path'] != null) {
            status = '결과 저장: ${data['path']} · ${data['status'] ?? ''}';
          }
          if (mode == 'proofread') {
            proofreadIssues = data['issues'] as List? ?? [];
            sourceRevision = '${data['source_sha256'] ?? ''}';
            approvedRules.clear();
          }
        });
      }
    } catch (e) {
      if (mounted) setState(() => status = '$e');
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  Future<void> applyProofread() async {
    if (busy || approvedRules.isEmpty) return;
    setState(() => busy = true);
    try {
      final result = await call('proofread_apply', {
        'path': path.text,
        'approved': approvedRules.toList(),
        'source_sha256': sourceRevision,
      });
      if (mounted) {
        setState(
          () => status =
              '교정 사본 저장: ${result['path']} · ${result['changes']}곳 (원본 보존)',
        );
      }
    } catch (e) {
      if (mounted) setState(() => status = '$e');
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  Future<void> addDocument() async {
    if (busy) return;
    setState(() => busy = true);
    try {
      final result = await call('add_text', {
        'text': output.text.isEmpty ? input.text : output.text,
      });
      if (mounted) setState(() => status = '문서 목록에 추가: ${result['path']}');
    } catch (e) {
      if (mounted) setState(() => status = '$e');
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  Future<void> filter() async {
    try {
      final result = await call('outline.filter', {
        'text': input.text,
        'query': search.text,
      });
      if (mounted) {
        setState(() => visible = (result['visible'] as List).cast<int>());
      }
    } catch (e) {
      if (mounted) setState(() => status = '$e');
    }
  }

  Future<void> leave() async {
    if (closing) return;
    autosave?.cancel();
    await _pendingOp;
    if (!mounted || busy) return;
    // While a draft is loading the field is read-only, so nothing typed can be
    // lost; save() refuses during loading and must not trap the user here.
    if (!_loading) {
      if (dirty && !await save()) return;
      if (dirty) return;
    }
    if (mounted) {
      setState(() => closing = true);
      Navigator.pop(context);
    }
  }

  KeyEventResult key(FocusNode node, KeyEvent event) {
    if (event is! KeyDownEvent || mode != 'outline') {
      return KeyEventResult.ignored;
    }
    final ctrl = HardwareKeyboard.instance.isControlPressed,
        alt = HardwareKeyboard.instance.isAltPressed,
        shift = HardwareKeyboard.instance.isShiftPressed;
    if (ctrl && event.logicalKey == LogicalKeyboardKey.keyF) {
      searchFocus.requestFocus();
      return KeyEventResult.handled;
    }
    if (ctrl && event.logicalKey == LogicalKeyboardKey.enter) {
      edit('toggle');
      return KeyEventResult.handled;
    }
    if (shift && event.logicalKey == LogicalKeyboardKey.enter) {
      edit('note');
      return KeyEventResult.handled;
    }
    if (alt && event.logicalKey == LogicalKeyboardKey.arrowRight) {
      edit('indent');
      return KeyEventResult.handled;
    }
    if (alt && event.logicalKey == LogicalKeyboardKey.arrowLeft) {
      edit('outdent');
      return KeyEventResult.handled;
    }
    if ((ctrl || alt && shift) &&
        (event.logicalKey == LogicalKeyboardKey.arrowUp ||
            event.logicalKey == LogicalKeyboardKey.arrowDown)) {
      edit('move', up: event.logicalKey == LogicalKeyboardKey.arrowUp);
      return KeyEventResult.handled;
    }
    return KeyEventResult.ignored;
  }

  Widget editor() => Focus(
    onKeyEvent: key,
    child: TextField(
      controller: input,
      readOnly: _loading,
      onChanged: (_) => changed(),
      maxLines: null,
      expands: true,
      textAlignVertical: TextAlignVertical.top,
      decoration: const InputDecoration(
        labelText: '입력 / 초안',
        alignLabelWithHint: true,
        border: OutlineInputBorder(),
      ),
    ),
  );
  Widget tree() {
    final lines = input.text.split('\n');
    return ListView(
      children: [
        for (var i = 0; i < lines.length; i++)
          if (visible == null || visible!.contains(i))
            ListTile(
              dense: true,
              contentPadding: EdgeInsets.only(
                left: 12 + (lines[i].length - lines[i].trimLeft().length) * 4.0,
              ),
              leading: Icon(
                lines[i].contains('[x]')
                    ? Icons.check_circle
                    : Icons.circle_outlined,
                size: 18,
              ),
              title: Text(lines[i]),
              onTap: () {
                final offset = lines
                    .take(i)
                    .fold<int>(0, (sum, line) => sum + line.length + 1);
                input.selection = TextSelection.collapsed(offset: offset);
                setState(() {});
              },
              trailing: IconButton(
                tooltip: '완료 토글',
                onPressed: busy
                    ? null
                    : () {
                        input.selection = TextSelection.collapsed(
                          offset: lines
                              .take(i)
                              .fold<int>(
                                0,
                                (sum, line) => sum + line.length + 1,
                              ),
                        );
                        edit('toggle');
                      },
                icon: const Icon(Icons.done),
              ),
            ),
      ],
    );
  }

  @override
  Widget build(BuildContext context) => PopScope(
    canPop: closing || (!dirty && _queuedOperations == 0 && !busy),
    onPopInvokedWithResult: (didPop, _) {
      if (!didPop) leave();
    },
    child: Scaffold(
      appBar: AppBar(
        leading: IconButton(
          onPressed: leave,
          icon: const Icon(Icons.arrow_back),
        ),
        title: const Text('문서·작성 도구'),
      ),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            DropdownButtonFormField<String>(
              initialValue: mode,
              items: [
                for (final item in modes.entries)
                  DropdownMenuItem(value: item.key, child: Text(item.value)),
              ],
              onChanged: busy || _loading
                  ? null
                  : (value) async {
                      if (value == null) return;
                      if (dirty && !await save()) return;
                      setState(() {
                        mode = value;
                        visible = null;
                      });
                      await load();
                    },
            ),
            const SizedBox(height: 8),
            if (mode == 'outline')
              TextField(
                controller: search,
                focusNode: searchFocus,
                onChanged: (_) => filter(),
                decoration: const InputDecoration(labelText: '검색 (Ctrl+F)'),
              ),
            if (mode == 'advanced') ...[
              const Text(
                '앱과 함께 배포하는 kordoc 꾸러미로 인터넷 없이 동작합니다. 원본 대신 작업 사본을 처리합니다.',
              ),
              DropdownButtonFormField<String>(
                initialValue: advancedAction,
                items: const [
                  DropdownMenuItem(
                    value: 'markdown',
                    child: Text('고급·페이지별 Markdown'),
                  ),
                  DropdownMenuItem(value: 'rag', child: Text('RAG 구조 청크')),
                  DropdownMenuItem(value: 'ir', child: Text('공통 문서 IR')),
                  DropdownMenuItem(value: 'tables', child: Text('표 추출·분류')),
                  DropdownMenuItem(value: 'form', child: Text('양식 필드 분석')),
                  DropdownMenuItem(value: 'compare', child: Text('블록·셀 신구대조')),
                  DropdownMenuItem(value: 'fill', child: Text('양식 자동 채우기')),
                  DropdownMenuItem(value: 'patch', child: Text('서식 보존 텍스트 패치')),
                  DropdownMenuItem(value: 'lint', child: Text('공문서 표기법 검수')),
                  DropdownMenuItem(value: 'preview', child: Text('페이지 이미지')),
                  DropdownMenuItem(value: 'generate', child: Text('HWPX 생성')),
                ],
                onChanged: busy
                    ? null
                    : (value) =>
                          setState(() => advancedAction = value ?? 'markdown'),
              ),
              TextField(
                controller: path,
                decoration: const InputDecoration(
                  labelText: '입력 문서 / 생성할 Markdown 경로',
                ),
              ),
              if (advancedAction == 'compare' || advancedAction == 'patch')
                TextField(
                  controller: otherPath,
                  decoration: const InputDecoration(
                    labelText: '비교 문서 / 편집한 Markdown 경로',
                  ),
                ),
              if (advancedAction == 'markdown')
                TextField(
                  controller: pages,
                  decoration: const InputDecoration(
                    labelText: '쪽 범위 (선택, 예: 1-3,5)',
                  ),
                ),
              if (advancedAction == 'generate')
                DropdownButtonFormField<String>(
                  initialValue: preset,
                  items: [
                    for (final value in ['보고서', '계획서', '기안문'])
                      DropdownMenuItem(value: value, child: Text(value)),
                  ],
                  onChanged: busy
                      ? null
                      : (value) => setState(() => preset = value ?? '보고서'),
                ),
              if (advancedAction == 'fill')
                const Text('입력란에 성명=홍길동,전화=02-123-4567 형식으로 입력하세요.'),
            ],
            if (mode == 'table_calc')
              DropdownButtonFormField<String>(
                initialValue: calculation,
                items: const [
                  DropdownMenuItem(value: 'col_sum', child: Text('열 합계')),
                  DropdownMenuItem(value: 'col_avg', child: Text('열 평균')),
                  DropdownMenuItem(value: 'row_sum', child: Text('행 합계')),
                  DropdownMenuItem(value: 'col_ratio', child: Text('열 비율')),
                ],
                onChanged: busy
                    ? null
                    : (value) =>
                          setState(() => calculation = value ?? 'col_sum'),
              ),
            if (mode == 'proofread' && proofreadIssues.isNotEmpty)
              OutlinedButton(
                onPressed: busy || approvedRules.isEmpty
                    ? null
                    : applyProofread,
                child: const Text('선택한 교정으로 사본 저장'),
              ),
            if (['review', 'proofread', 'numbers', 'markdown'].contains(mode))
              TextField(
                controller: path,
                decoration: const InputDecoration(labelText: '검토할 HWPX 사본 경로'),
              ),
            Wrap(
              spacing: 8,
              runSpacing: 4,
              children: [
                FilledButton(
                  onPressed: busy || _loading ? null : run,
                  child: Text(mode == 'outline' ? '개조식 내보내기' : '실행 / 미리보기'),
                ),
                if (mode == 'outline') ...[
                  TextButton(
                    onPressed: busy ? null : () => edit('move', up: true),
                    child: const Text('위로'),
                  ),
                  TextButton(
                    onPressed: busy ? null : () => edit('move'),
                    child: const Text('아래로'),
                  ),
                  TextButton(
                    onPressed: busy ? null : () => edit('indent'),
                    child: const Text('들여쓰기'),
                  ),
                  TextButton(
                    onPressed: busy ? null : () => edit('outdent'),
                    child: const Text('내어쓰기'),
                  ),
                  TextButton(
                    onPressed: busy ? null : () => edit('note'),
                    child: const Text('메모'),
                  ),
                  TextButton(
                    onPressed: busy ? null : save,
                    child: const Text('초안 저장'),
                  ),
                ],
                TextButton(
                  onPressed: busy
                      ? null
                      : () =>
                            Clipboard.setData(ClipboardData(text: output.text)),
                  child: const Text('결과 복사'),
                ),
                OutlinedButton(
                  onPressed: busy ? null : addDocument,
                  child: const Text('문서 목록에 추가'),
                ),
              ],
            ),
            if (busy) const LinearProgressIndicator(),
            if (status.isNotEmpty) Text(status),
            const SizedBox(height: 8),
            Expanded(
              child: LayoutBuilder(
                builder: (context, box) {
                  final result = TextField(
                    controller: output,
                    readOnly: true,
                    maxLines: null,
                    expands: true,
                    textAlignVertical: TextAlignVertical.top,
                    decoration: const InputDecoration(
                      labelText: '변환·검토 결과',
                      alignLabelWithHint: true,
                      border: OutlineInputBorder(),
                    ),
                  );
                  final shownResult =
                      mode == 'proofread' && proofreadIssues.isNotEmpty
                      ? ListView(
                          children: [
                            for (final issue in proofreadIssues)
                              CheckboxListTile(
                                value: approvedRules.contains(issue['rule_id']),
                                onChanged: busy
                                    ? null
                                    : (value) => setState(() {
                                        if (value == true) {
                                          approvedRules.add(
                                            '${issue['rule_id']}',
                                          );
                                        } else {
                                          approvedRules.remove(
                                            issue['rule_id'],
                                          );
                                        }
                                      }),
                                title: Text(
                                  '${issue['source']} → ${issue['suggestion']} (${issue['count']}곳)',
                                ),
                                subtitle: Text('${issue['reason']}'),
                              ),
                          ],
                        )
                      : result;
                  if (box.maxWidth < 760) {
                    return Column(
                      children: [
                        Expanded(child: editor()),
                        const SizedBox(height: 8),
                        Expanded(child: shownResult),
                      ],
                    );
                  }
                  return Row(
                    children: [
                      if (mode == 'outline') Expanded(child: tree()),
                      Expanded(child: editor()),
                      const SizedBox(width: 12),
                      Expanded(child: shownResult),
                    ],
                  );
                },
              ),
            ),
          ],
        ),
      ),
    ),
  );
}
