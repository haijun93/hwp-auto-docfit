import 'package:flutter/material.dart';

/// HWP → HWPX 일괄 변환(2.0.7): 파일 하나·폴더·로컬 드라이브 전체, 암호 문서는 암호를 차례로 넣어 연다.
/// [call]은 백엔드 명령을 그대로 부르고 결과를 돌려준다(상태는 1초마다 get_state의 hwp_bulk로 읽는다).
typedef BulkCall = Future<Object?> Function(String method, List<Object?> args);

Future<void> showHwpBulkDialog(BuildContext context, BulkCall call) {
  return showDialog<void>(
    context: context,
    builder: (_) => HwpBulkDialog(call: call),
  );
}

class HwpBulkDialog extends StatefulWidget {
  const HwpBulkDialog({super.key, required this.call});

  final BulkCall call;

  @override
  State<HwpBulkDialog> createState() => _HwpBulkDialogState();
}

class _HwpBulkDialogState extends State<HwpBulkDialog> {
  String scope = 'folder'; // folder | drive
  String? folder;
  List<String> drives = [];
  final chosenDrives = <String>{};
  bool recursive = true;
  final passwords = <String>[];
  final passwordField = TextEditingController();
  String? message;
  bool starting = false;

  @override
  void initState() {
    super.initState();
    widget
        .call('hwp_bulk', ['drives'])
        .then((value) {
          if (!mounted || value is! Map) return;
          setState(
            () =>
                drives = [for (final d in value['drives'] as List? ?? []) '$d'],
          );
        })
        .catchError((_) {});
  }

  @override
  void dispose() {
    passwordField.dispose();
    super.dispose();
  }

  Future<void> _pickFolder() async {
    final value = await widget.call('hwp_bulk', ['pick_folder']);
    if (!mounted) return;
    if (value is Map && value['folder'] is String) {
      setState(() => folder = value['folder'] as String);
    }
  }

  void _addPassword() {
    final text = passwordField.text;
    if (text.isEmpty || passwords.length >= 20) return;
    setState(() {
      if (!passwords.contains(text)) passwords.add(text);
      passwordField.clear();
    });
  }

  List<String> get roots => scope == 'folder'
      ? [?folder]
      : [
          for (final d in drives)
            if (chosenDrives.contains(d)) d,
        ];

  Future<void> _start() async {
    if (passwordField.text.isNotEmpty) _addPassword();
    if (roots.isEmpty) {
      setState(
        () =>
            message = scope == 'folder' ? '폴더를 먼저 고르세요.' : '드라이브를 하나 이상 고르세요.',
      );
      return;
    }
    setState(() => starting = true);
    final value = await widget.call('hwp_bulk', [
      'start',
      {
        'roots': roots,
        'recursive': scope == 'drive' || recursive,
        'passwords': List.of(passwords),
      },
    ]);
    if (!mounted) return;
    passwords.clear();
    if (value is Map && value['ok'] == true) {
      Navigator.pop(context);
    } else {
      setState(() {
        starting = false;
        message = value is Map ? '${value['message'] ?? ''}' : '시작하지 못했어요.';
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      key: const Key('hwpBulkDialog'),
      title: const Text('HWP 찾아 HWPX로 바꾸기', style: TextStyle(fontSize: 16)),
      content: SizedBox(
        width: 440,
        child: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              SegmentedButton<String>(
                segments: const [
                  ButtonSegment(
                    value: 'folder',
                    label: Text('폴더'),
                    icon: Icon(Icons.folder_outlined),
                  ),
                  ButtonSegment(
                    value: 'drive',
                    label: Text('드라이브 전체'),
                    icon: Icon(Icons.storage_outlined),
                  ),
                ],
                selected: {scope},
                onSelectionChanged: (v) => setState(() {
                  scope = v.first;
                  message = null;
                }),
              ),
              const SizedBox(height: 12),
              if (scope == 'folder') ...[
                Row(
                  children: [
                    Expanded(
                      child: Text(
                        folder ?? '고른 폴더 없음',
                        key: const Key('hwpBulkFolder'),
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                    OutlinedButton(
                      key: const Key('hwpBulkPickFolder'),
                      onPressed: _pickFolder,
                      child: const Text('폴더 고르기'),
                    ),
                  ],
                ),
                CheckboxListTile(
                  key: const Key('hwpBulkRecursive'),
                  contentPadding: EdgeInsets.zero,
                  dense: true,
                  value: recursive,
                  onChanged: (v) => setState(() => recursive = v ?? true),
                  title: const Text('하위 폴더까지 찾기'),
                ),
              ] else ...[
                Wrap(
                  spacing: 8,
                  children: [
                    for (final d in drives)
                      FilterChip(
                        key: Key('hwpBulkDrive-$d'),
                        label: Text(d),
                        selected: chosenDrives.contains(d),
                        onSelected: (on) => setState(
                          () =>
                              on ? chosenDrives.add(d) : chosenDrives.remove(d),
                        ),
                      ),
                    if (drives.isEmpty) const Text('드라이브를 찾는 중…'),
                  ],
                ),
                const SizedBox(height: 6),
                const Text(
                  'Windows·Program Files·AppData 같은 시스템 폴더는 건너뜁니다. 드라이브가 크면 오래 걸려요.',
                  style: TextStyle(fontSize: 12, color: Color(0xff64748b)),
                ),
              ],
              const Divider(height: 24),
              Row(
                children: [
                  Expanded(
                    child: TextField(
                      key: const Key('hwpBulkPassword'),
                      controller: passwordField,
                      obscureText: true,
                      decoration: const InputDecoration(
                        isDense: true,
                        labelText: '암호 문서의 암호 (있으면)',
                      ),
                      onSubmitted: (_) => _addPassword(),
                    ),
                  ),
                  TextButton(
                    key: const Key('hwpBulkAddPassword'),
                    onPressed: _addPassword,
                    child: const Text('암호 추가'),
                  ),
                ],
              ),
              if (passwords.isNotEmpty)
                Wrap(
                  spacing: 6,
                  children: [
                    for (var i = 0; i < passwords.length; i++)
                      InputChip(
                        label: Text('암호 ${i + 1} ●●●●'),
                        onDeleted: () => setState(() => passwords.removeAt(i)),
                      ),
                  ],
                ),
              const SizedBox(height: 8),
              const Text(
                '· 결과는 원본 옆에 같은 이름의 .hwpx로 저장하고, 이미 있으면 건너뜁니다(원본은 그대로).\n'
                '· 암호 문서는 넣은 암호를 차례로 시도하고, 결과 HWPX도 같은 암호로 잠깁니다.\n'
                '· 배포용 문서는 한/글이 저장을 허용하면 바꾸고, 기관 보안(DRM) 문서는 이 PC의 보안 프로그램이 열어 줄 때만 바뀝니다.\n'
                '· 끝나면 결과표(CSV)에 변환·실패 이유를 남깁니다. 암호는 저장하지 않습니다.',
                style: TextStyle(fontSize: 12, color: Color(0xff475569)),
              ),
              if (message != null) ...[
                const SizedBox(height: 8),
                Text(
                  message!,
                  key: const Key('hwpBulkMessage'),
                  style: const TextStyle(color: Color(0xffdc2626)),
                ),
              ],
            ],
          ),
        ),
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(context),
          child: const Text('닫기'),
        ),
        FilledButton(
          key: const Key('hwpBulkStart'),
          onPressed: starting ? null : _start,
          child: const Text('찾아서 바꾸기'),
        ),
      ],
    );
  }
}

/// 변환 결과 칸 맨 위에 보이는 일괄 변환 진행·결과 카드.
class HwpBulkCard extends StatelessWidget {
  const HwpBulkCard({super.key, required this.bulk, required this.call});

  final Map bulk;
  final BulkCall call;

  @override
  Widget build(BuildContext context) {
    final phase = '${bulk['phase'] ?? ''}';
    final found = bulk['found'] ?? 0;
    final done = bulk['done'] ?? 0;
    final active = phase == 'scan' || phase == 'convert';
    final failures = (bulk['failures'] as List? ?? [])
        .whereType<Map>()
        .toList();
    final title = switch (phase) {
      'scan' => 'HWP 찾는 중… $found개 찾음',
      'convert' => 'HWPX로 바꾸는 중 $done / $found',
      'error' => 'HWPX 일괄 변환을 하지 못했어요',
      'stopped' => 'HWPX 일괄 변환을 멈췄어요',
      _ =>
        'HWPX 일괄 변환 끝: 변환 ${bulk['succeeded'] ?? 0} · 실패 ${bulk['failed'] ?? 0}'
            ' · 이미 있어 건너뜀 ${bulk['skipped_existing'] ?? 0}',
    };
    final current = '${bulk['current'] ?? ''}';
    return Card(
      key: const Key('hwpBulkCard'),
      margin: const EdgeInsets.only(bottom: 8),
      child: Padding(
        padding: const EdgeInsets.all(10),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text(title, style: const TextStyle(fontWeight: FontWeight.w600)),
            if (active) ...[
              const SizedBox(height: 6),
              LinearProgressIndicator(
                value: phase == 'convert' && found is num && found > 0
                    ? (done as num) / found
                    : null,
              ),
              if (current.isNotEmpty)
                Text(
                  current,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(
                    fontSize: 11,
                    color: Color(0xff64748b),
                  ),
                ),
            ],
            if (phase == 'error' && '${bulk['error'] ?? ''}'.isNotEmpty)
              Text('${bulk['error']}', style: const TextStyle(fontSize: 12)),
            for (final f in failures.take(5))
              Text(
                '✕ ${'${f['source'] ?? ''}'.split(RegExp(r'[\\/]')).last}: ${f['message'] ?? ''}',
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
                style: const TextStyle(fontSize: 11, color: Color(0xffb91c1c)),
              ),
            if (failures.length > 5)
              Text(
                '… 실패 ${failures.length - 5}개 더(결과표에 모두 있어요)',
                style: const TextStyle(fontSize: 11),
              ),
            Wrap(
              alignment: WrapAlignment.end,
              children: [
                if (active)
                  TextButton(
                    key: const Key('hwpBulkStop'),
                    onPressed: () => call('hwp_bulk', ['stop']),
                    child: const Text('멈추기'),
                  ),
                if (!active && '${bulk['report'] ?? ''}'.isNotEmpty) ...[
                  TextButton(
                    key: const Key('hwpBulkOpenReport'),
                    onPressed: () => call('hwp_bulk', ['open_report']),
                    child: const Text('결과표 열기'),
                  ),
                  TextButton(
                    key: const Key('hwpBulkShowReport'),
                    onPressed: () => call('hwp_bulk', ['show_report']),
                    child: const Text('결과표 폴더'),
                  ),
                ],
              ],
            ),
          ],
        ),
      ),
    );
  }
}
