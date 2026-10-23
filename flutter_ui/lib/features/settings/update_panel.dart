import 'package:flutter/material.dart';

/// 업데이트 설정 패널(Filee 방식).
///
/// 현재 버전 표시, 지금 확인 버튼, 진행 상황, 바뀐 점 목록,
/// 다운로드/업데이트 버튼을 제공한다.
class UpdatePanel extends StatelessWidget {
  const UpdatePanel({
    super.key = const Key('updatePanel'),
    required this.state,
    required this.command,
  });

  final Map<String, dynamic> state;
  final Future<void> Function(String method, [List<Object?> args]) command;

  @override
  Widget build(BuildContext context) {
    final update = (state['update'] as Map?)?.cast<String, dynamic>() ??
        (state['update'] as Map<String, dynamic>?);

    final step = (update?['step'] as String? ?? 'idle').trim();
    final currentRaw =
        (update?['current'] ?? state['version'] ?? '').toString().trim();
    final current =
        currentRaw.startsWith('v') ? currentRaw.substring(1) : currentRaw;
    final latestRaw = (update?['latest'] ?? '').toString().trim();
    final latest =
        latestRaw.startsWith('v') ? latestRaw.substring(1) : latestRaw;
    final percent = (update?['percent'] as num?)?.toInt() ?? 0;
    final rawMessage = update?['message']?.toString().trim() ?? '';
    final notesRaw = update?['notes'] as List? ?? const [];
    final notes = notesRaw.map((e) => e.toString()).toList();
    final installed = update?['installed'] != false;

    // 현재 버전 라벨: "현재 버전 v{current}"
    final currentLabel = current.isNotEmpty ? '현재 버전 v$current' : '현재 버전';

    // 지금 확인 버튼 비활성 조건: step이 checking, downloading, installing일 때
    final isBusy =
        step == 'checking' || step == 'downloading' || step == 'installing';

    // 상태 줄 텍스트: message가 있으면 그것, 없으면 step별 기본 문구
    final String statusText;
    if (rawMessage.isNotEmpty) {
      statusText = rawMessage;
    } else {
      statusText = switch (step) {
        'checking' => '새 버전을 확인하고 있어요…',
        'latest' => '최신 버전이에요.',
        'available' => '새 버전 v$latest이 나왔어요.',
        'downloading' => '내려받는 중… $percent%',
        'installing' => '설치를 시작했어요. 잠시 뒤 앱이 다시 열려요.',
        'failed' => '업데이트하지 못했어요.',
        'cancelled' => '업데이트를 취소했어요.',
        'offline' => '폐쇄망 모드에서는 인터넷으로 확인하지 않아요.',
        'idle' => '',
        _ => '',
      };
    }

    final displayNotes = notes.take(6).toList();

    return Container(
      margin: const EdgeInsets.only(top: 8, bottom: 8),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: const Color(0xfff8fafc),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: const Color(0xffe2e8f0)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: [
          Row(
            children: [
              Expanded(
                child: Text(
                  currentLabel,
                  style: const TextStyle(
                    fontSize: 13,
                    fontWeight: FontWeight.w600,
                    color: Color(0xff334155),
                  ),
                ),
              ),
              OutlinedButton(
                key: const Key('checkUpdateButton'),
                onPressed: isBusy ? null : () => command('check_update'),
                style: OutlinedButton.styleFrom(
                  visualDensity: VisualDensity.compact,
                  padding:
                      const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                  minimumSize: Size.zero,
                  tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                ),
                child: const Text('지금 확인', style: TextStyle(fontSize: 12)),
              ),
            ],
          ),
          if (statusText.isNotEmpty) ...[
            const SizedBox(height: 8),
            Text(
              statusText,
              key: const Key('updateStatusText'),
              style: const TextStyle(
                fontSize: 12,
                color: Color(0xff64748b),
              ),
            ),
          ],
          if (step == 'downloading') ...[
            const SizedBox(height: 8),
            ClipRRect(
              borderRadius: BorderRadius.circular(4),
              child: LinearProgressIndicator(
                key: const Key('updateProgress'),
                value: (percent / 100.0).clamp(0.0, 1.0),
                minHeight: 6,
              ),
            ),
          ],
          if (step == 'available' && displayNotes.isNotEmpty) ...[
            const SizedBox(height: 10),
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: const Color(0xffe2e8f0)),
              ),
              child: Text(
                displayNotes.map((n) => '• $n').join('\n'),
                key: const Key('updateNotes'),
                style: const TextStyle(
                  fontSize: 12,
                  color: Color(0xff334155),
                  height: 1.45,
                ),
              ),
            ),
          ],
          if (step == 'available') ...[
            const SizedBox(height: 10),
            SizedBox(
              width: double.infinity,
              child: FilledButton(
                key: const Key('startUpdateButton'),
                onPressed: () => command('start_update'),
                child: Text(
                  installed ? 'v$latest로 업데이트' : 'v$latest 내려받아 바꾸기',
                ),
              ),
            ),
          ],
          if (step == 'failed') ...[
            const SizedBox(height: 10),
            SizedBox(
              width: double.infinity,
              child: OutlinedButton(
                key: const Key('openUpdatePageButton'),
                onPressed: () => command('open_update_page'),
                child: const Text('다운로드 페이지 열기'),
              ),
            ),
          ],
        ],
      ),
    );
  }
}
