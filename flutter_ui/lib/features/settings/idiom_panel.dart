import 'package:flutter/material.dart';

import '../../core/api/abbreviation_api.dart';
import 'kiosk_theme.dart';

/// 설정의 '글자 상용구'·'본문 상용구' 관리(알파, 2026-10-15).
///
/// 기본 설정은 사용자가 직접 편집하는 글자상용구.hwpx / 본문상용구.hwpx다.
class IdiomPanel extends StatefulWidget {
  const IdiomPanel({
    super.key,
    required this.api,
    required this.body,
    required this.locked,
  });

  final ApiCall api;

  /// true면 본문 상용구(준말 → HWP 문서), false면 글자 상용구(준말 → 글자).
  final bool body;
  final bool locked;

  @override
  State<IdiomPanel> createState() => _IdiomPanelState();
}

class _IdiomPanelState extends State<IdiomPanel> {
  Map data = const {};
  bool busy = true;
  String? error;
  String? notice;
  final search = TextEditingController();
  final keyInput = TextEditingController();
  final valueInput = TextEditingController();

  List<Map> get entries => [
    for (final item in (data[widget.body ? 'body' : 'text'] as List? ?? []))
      Map.from(item as Map),
  ];

  @override
  void initState() {
    super.initState();
    request('get');
  }

  @override
  void dispose() {
    search.dispose();
    keyInput.dispose();
    valueInput.dispose();
    super.dispose();
  }

  Future<bool> request(
    String action, [
    Map<String, Object?> payload = const {},
    String? done,
  ]) async {
    setState(() {
      busy = true;
      error = null;
    });
    try {
      final response = await widget.api('idioms', [action, payload]);
      if (response is! Map || response['ok'] != true) {
        final problem = response is Map ? response['error'] : null;
        throw Exception(
          problem is Map
              ? problem['message'] ?? '상용구를 저장하지 못했어요.'
              : '앱 연결을 확인해 주세요.',
        );
      }
      if (mounted) {
        setState(() {
          data = response['data'] as Map? ?? const {};
          notice = done;
        });
      }
      return true;
    } catch (e) {
      if (mounted) {
        setState(() => error = '$e'.replaceFirst('Exception: ', ''));
      }
      return false;
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  Future<void> saveText(List<Map> next, String done) => request('save_text', {
    'entries': [
      for (final e in next)
        {'key': e['key'], 'value': e['value'], 'attr': e['attr'] ?? 0},
    ],
  }, done);

  Future<void> saveBody(List<Map> next, String done) => request('save_body', {
    'entries': [
      for (final e in next)
        {
          'key': e['key'],
          'title': e['title'],
          'attr': e['attr'] ?? 1,
          'old_key': e['old_key'] ?? e['key'],
        },
    ],
  }, done);

  Future<void> add() async {
    final key = keyInput.text.trim();
    final value = valueInput.text;
    if (key.isEmpty || value.trim().isEmpty) {
      setState(() => error = widget.body ? '준말과 이름을 입력하세요.' : '준말과 본말을 입력하세요.');
      return;
    }
    final ok = widget.body
        ? await request('add_body', {
            'key': key,
            'title': value.trim(),
          }, '본문 상용구 ‘$key’를 추가했어요.')
        : await request('save_text', {
            'entries': [
              ...entries,
              {'key': key, 'value': value, 'attr': 0},
            ],
          }, '글자 상용구 ‘$key’를 추가했어요.');
    if (ok) {
      keyInput.clear();
      valueInput.clear();
    }
  }

  Future<void> edit(int index) async {
    final item = entries[index];
    final key = TextEditingController(text: '${item['key']}');
    final value = TextEditingController(
      text: '${item[widget.body ? 'title' : 'value']}',
    );
    final saved = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(widget.body ? '본문 상용구 고치기' : '글자 상용구 고치기'),
        content: SizedBox(
          width: 420,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(
                controller: key,
                maxLength: 20,
                decoration: const InputDecoration(labelText: '준말'),
              ),
              TextField(
                controller: value,
                maxLength: widget.body ? 100 : 500,
                minLines: 1,
                maxLines: widget.body ? 1 : 4,
                decoration: InputDecoration(
                  labelText: widget.body ? '이름' : '본말(펼쳐질 글자)',
                ),
              ),
            ],
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('취소'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('저장'),
          ),
        ],
      ),
    );
    if (saved == true) {
      final next = entries;
      next[index] = {
        ...item,
        'key': key.text.trim(),
        if (widget.body) 'title': value.text.trim() else 'value': value.text,
        'old_key': item['key'],
      };
      widget.body
          ? await saveBody(next, '본문 상용구를 고쳤어요.')
          : await saveText(next, '글자 상용구를 고쳤어요.');
    }
    key.dispose();
    value.dispose();
  }

  Future<void> remove(int index) async {
    final item = entries[index];
    final sure = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('상용구 삭제'),
        content: Text(
          '‘${item['key']}’ 상용구를 지울까요?'
          '${widget.body ? '\n본문 상용구 문서도 함께 지우고, 백업 폴더에 남겨 둬요.' : ''}',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('취소'),
          ),
          FilledButton(
            style: FilledButton.styleFrom(backgroundColor: Kiosk.red),
            onPressed: () => Navigator.pop(context, true),
            child: const Text('삭제'),
          ),
        ],
      ),
    );
    if (sure != true) return;
    final next = entries..removeAt(index);
    widget.body
        ? await saveBody(next, '‘${item['key']}’를 지웠어요.')
        : await saveText(next, '‘${item['key']}’를 지웠어요.');
  }

  @override
  Widget build(BuildContext context) {
    final locked = busy || widget.locked;
    final available = data['available'] != false;
    final directConfig = data['source'] == 'hwpx';
    final query = search.text.trim();
    final all = entries;
    final visible = [
      for (var i = 0; i < all.length; i++)
        if (query.isEmpty ||
            '${all[i]['key']} ${all[i][widget.body ? 'title' : 'value']}'
                .contains(query))
          i,
    ];
    return ListView(
      padding: const EdgeInsets.only(bottom: 16),
      children: [
        Container(
          padding: const EdgeInsets.all(20),
          decoration: Kiosk.cardBox(),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(widget.body ? '본문 상용구' : '글자 상용구', style: Kiosk.cardTitle),
              const SizedBox(height: 6),
            Text(
                directConfig
                    ? '준말 표식(# + 준말) 다음 줄부터 본말을 입력합니다. 다음 항목도 같은 방식으로 이어 쓰세요. 문서 구조와 서식은 한/글에서 자유롭게 편집할 수 있어요.'
                    : widget.body
                    ? '준말을 치고 Alt+I를 누르면 미리 만들어 둔 문서(표·서식)가 통째로 들어가요. HWP·HWPX 문서를 골라 추가하세요.'
                    : '준말을 치고 Alt+I를 누르면 본말 글자로 바뀌어요. 예: ㅁ → □, ㅇ123 → ①②③',
                style: Kiosk.body,
              ),
              const SizedBox(height: 4),
              Text(
                directConfig
                    ? '${(data['config_files'] as Map?)?[widget.body ? 'body' : 'text'] ?? ''}  ·  아래 버튼으로 한/글에서 직접 열어 수정하세요.'
                    : available
                    ? '한/글이 쓰는 상용구 파일을 바로 고쳐요. 저장할 때마다 이전 파일을 백업하고, 한/글을 다시 열면 반영돼요.'
                    : '${data['reason'] ?? '상용구 파일을 불러오는 중이에요.'}',
                style: Kiosk.caption,
              ),
              if (directConfig) ...[
                const SizedBox(height: 12),
                Wrap(
                  spacing: 10,
                  runSpacing: 8,
                  children: [
                    KioskPrimaryButton(
                      label: '한/글에서 설정 문서 열기',
                      onPressed: locked ? null : () => request('open_config', {
                        'kind': widget.body ? 'body' : 'text',
                      }),
                    ),
                    KioskSecondaryButton(
                      label: '한/글 상용구에 반영',
                      onPressed: locked ? null : () => request(
                        'apply_hwpx',
                        const {},
                        'HWPX 상용구를 한/글에 반영했어요. 한/글을 다시 시작해 적용하세요.',
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 6),
                Text('반영 전에 한/글을 종료하세요. 기존 상용구 파일은 자동 백업됩니다.', style: Kiosk.caption),
              ],
              const SizedBox(height: 16),
              if (!directConfig) Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  SizedBox(
                    width: 120,
                    child: TextField(
                      key: Key('idiom-key-${widget.body}'),
                      controller: keyInput,
                      enabled: !locked && available,
                      maxLength: 20,
                      decoration: const InputDecoration(
                        labelText: '준말',
                        hintText: '예: ㅁㅂ',
                      ),
                    ),
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: TextField(
                      key: Key('idiom-value-${widget.body}'),
                      controller: valueInput,
                      enabled: !locked && available,
                      maxLength: widget.body ? 100 : 500,
                      decoration: InputDecoration(
                        labelText: widget.body ? '이름' : '본말(펼쳐질 글자)',
                        hintText: widget.body ? '예: 보고서 서식' : '예: 마포구청',
                      ),
                      onSubmitted: (_) => locked ? null : add(),
                    ),
                  ),
                  const SizedBox(width: 10),
                  Padding(
                    padding: const EdgeInsets.only(top: 8),
                    child: KioskPrimaryButton(
                      label: widget.body ? '문서 골라 추가' : '추가',
                      onPressed: locked || !available ? null : add,
                    ),
                  ),
                ],
              ),
              if (busy) const LinearProgressIndicator(),
              if (error != null)
                Padding(
                  padding: const EdgeInsets.only(top: 8),
                  child: Text(error!, style: const TextStyle(color: Kiosk.red)),
                ),
              if (notice != null && error == null)
                Padding(
                  padding: const EdgeInsets.only(top: 8),
                  child: Text(
                    notice!,
                    style: const TextStyle(color: Kiosk.green),
                  ),
                ),
            ],
          ),
        ),
        const SizedBox(height: 12),
        Row(
          children: [
            Expanded(
              child: TextField(
                controller: search,
                onChanged: (_) => setState(() {}),
                decoration: InputDecoration(
                  prefixIcon: const Icon(Icons.search, color: Kiosk.faint),
                  hintText: '상용구 찾기 (${all.length}개)',
                  filled: true,
                  fillColor: Colors.white,
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(14),
                    borderSide: BorderSide.none,
                  ),
                ),
              ),
            ),
            if (!widget.body && !directConfig) ...[
              const SizedBox(width: 10),
              KioskSecondaryButton(
                label: '앱 기본 상용구 가져오기',
                onPressed: locked || !available
                    ? null
                    : () => request(
                        'import_app',
                        const {},
                        '앱에 포함된 상용구 중 없던 것을 가져왔어요.',
                      ),
              ),
            ],
          ],
        ),
        const SizedBox(height: 10),
        for (final i in visible) _row(i, all[i], locked),
        if (visible.isEmpty && !busy)
          Padding(
            padding: const EdgeInsets.all(24),
            child: Center(
              child: Text(
                query.isEmpty ? '아직 상용구가 없어요.' : '“$query”와 맞는 상용구가 없어요.',
                style: Kiosk.body,
              ),
            ),
          ),
      ],
    );
  }

  Widget _row(int index, Map item, bool locked) {
    final directConfig = data['source'] == 'hwpx';
    final value = '${widget.body && !directConfig ? item['title'] : item['value']}';
    return Container(
      key: ValueKey('idiom-row-${widget.body}-$index'),
      margin: const EdgeInsets.only(bottom: 6),
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: Kiosk.line),
      ),
      child: Row(
        children: [
          Container(
            constraints: const BoxConstraints(minWidth: 72),
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
            decoration: BoxDecoration(
              color: Kiosk.blueSoft,
              borderRadius: BorderRadius.circular(10),
            ),
            child: Text(
              '${item['key']}',
              textAlign: TextAlign.center,
              style: const TextStyle(
                fontWeight: FontWeight.w700,
                color: Kiosk.blue,
              ),
            ),
          ),
          const Padding(
            padding: EdgeInsets.symmetric(horizontal: 10),
            child: Icon(
              Icons.arrow_forward_rounded,
              size: 16,
              color: Kiosk.faint,
            ),
          ),
          Expanded(
            child: Text(
              value,
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
              style: const TextStyle(fontSize: 15, color: Kiosk.ink),
            ),
          ),
          if (widget.body && item['has_file'] != true)
            const Padding(
              padding: EdgeInsets.only(right: 6),
              child: Text(
                '문서 없음',
                style: TextStyle(color: Kiosk.red, fontSize: 12),
              ),
            ),
          if (widget.body && !directConfig)
            IconButton(
              tooltip: '한/글에서 열기',
              onPressed: locked || item['has_file'] != true
                  ? null
                  : () => request('open_body', {'key': item['key']}),
              icon: const Icon(Icons.open_in_new_rounded),
            ),
          if (!directConfig) ...[
            IconButton(
              tooltip: '고치기',
              onPressed: locked ? null : () => edit(index),
              icon: const Icon(Icons.edit_outlined),
            ),
            IconButton(
              tooltip: '삭제',
              onPressed: locked ? null : () => remove(index),
              icon: const Icon(Icons.delete_outline_rounded),
            ),
          ],
        ],
      ),
    );
  }
}

/// 함께 쓰는 프로그램·코드(이름, 쓰는 곳, 라이선스). 자세한 고지는 THIRD_PARTY_NOTICES.md(2026-10-17 사용자 요청).
const thirdPartyComponents = [
  ('kordoc 4.21.30 (chrisryugj)', '문서 변환 엔진(PDF·DOCX·이미지 → HWPX 등)', 'MIT'),
  ('Node.js 22.23.3', 'kordoc 실행 런타임(EXE 내장)', 'MIT'),
  ('pdf.js (pdfjs-dist 4.10.38)', 'PDF 글자 읽기', 'Apache-2.0'),
  ('PP-OCRv5 한국어 모델 (PaddlePaddle)', '이미지·스캔 PDF 한국어 글자 인식', 'Apache-2.0'),
  ('ONNX Runtime 1.30.0', 'OCR 모델 실행', 'MIT'),
  ('sharp 0.35.5 · libvips', 'OCR 이미지 처리', 'Apache-2.0 · LGPL-3.0'),
  ('PDFium (@hyzyla/pdfium 2.1.13)', '스캔 PDF 쪽 그림 만들기', 'MIT · BSD-3-Clause'),
  ('rhwp (@rhwp/core 0.8.7, Edward Kim)', '설정 화면 한/글 조판 미리보기', 'MIT'),
  ('React Flow (@xyflow/react 12.12.0) · React', '업무 흐름도·마인드맵 편집', 'MIT'),
  ('Flutter', '앱 화면', 'BSD-3-Clause'),
  ('Noto Sans KR', '앱 화면 글꼴', 'SIL OFL 1.1'),
  ('Python · Tcl/Tk', '앱 실행 런타임(EXE 내장)', 'PSF · Tcl/Tk'),
  ('pywin32', '한/글 COM 자동화 연결', 'PSF'),
  ('pywebview · pythonnet', '앱 창(WebView2) 연결', 'BSD-3-Clause · MIT'),
  ('tkinterdnd2', '파일 끌어다 놓기', 'MIT'),
  ('Pillow', '그림 처리', 'MIT-CMU'),
  ('defusedxml', '안전한 XML 읽기', 'PSF'),
  ('PyInstaller', 'EXE 만들기', 'GPL-2.0 (부트로더 예외)'),
  ('한/글 자동화 보안 모듈 예시(한컴)', '한/글 COM 자동화 승인', '한컴 예제 배포 조건'),
];

/// 설정의 '앱 정보': 개발자와 버전, 함께 쓰는 프로그램·코드.
class AppInfoPanel extends StatelessWidget {
  const AppInfoPanel({super.key, this.version});
  final String? version;

  @override
  Widget build(BuildContext context) => ListView(
    children: [
      Container(
        padding: const EdgeInsets.all(24),
        decoration: Kiosk.cardBox(),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('앱 정보', style: Kiosk.cardTitle),
            const SizedBox(height: 16),
            _line('개발자', '도토리만두'),
            if (version != null && version!.isNotEmpty) _line('버전', version!),
          ],
        ),
      ),
      const SizedBox(height: 16),
      Container(
        padding: const EdgeInsets.all(24),
        decoration: Kiosk.cardBox(),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('함께 쓰는 프로그램·코드', style: Kiosk.cardTitle),
            const SizedBox(height: 6),
            const Text(
              '이 앱은 아래 공개 프로그램과 코드를 함께 씁니다. 한/글 프로그램은 포함하지 않고 PC에 설치된 한/글을 씁니다. '
              '자세한 저작권·라이선스 고지는 THIRD_PARTY_NOTICES.md에 있습니다.',
              style: Kiosk.caption,
            ),
            const SizedBox(height: 14),
            for (final (name, use, license) in thirdPartyComponents)
              _component(name, use, license),
          ],
        ),
      ),
    ],
  );

  Widget _component(String name, String use, String license) => Padding(
    padding: const EdgeInsets.only(bottom: 12),
    child: Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Expanded(
          flex: 5,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                name,
                style: const TextStyle(
                  fontSize: 15,
                  fontWeight: FontWeight.w700,
                  color: Kiosk.ink,
                ),
              ),
              Text(use, style: Kiosk.caption),
            ],
          ),
        ),
        const SizedBox(width: 12),
        Expanded(flex: 2, child: Text(license, style: Kiosk.body)),
      ],
    ),
  );

  Widget _line(String label, String value) => Padding(
    padding: const EdgeInsets.only(bottom: 10),
    child: Row(
      children: [
        SizedBox(width: 80, child: Text(label, style: Kiosk.body)),
        Text(
          value,
          style: const TextStyle(
            fontSize: 17,
            fontWeight: FontWeight.w700,
            color: Kiosk.ink,
          ),
        ),
      ],
    ),
  );
}
