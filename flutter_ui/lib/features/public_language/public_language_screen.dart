import 'dart:async';

import 'package:flutter/material.dart';

import '../../core/api/public_language_api.dart';
import 'exclusion_manager_screen.dart';

export 'exclusion_manager_screen.dart';

enum _PublicLanguagePhase {
  ready,
  scanning,
  reviewed,
  applying,
  applied,
}

/// 공공언어 바로쓰기 검토 및 선택 교정 화면 (T11).
class PublicLanguageScreen extends StatefulWidget {
  const PublicLanguageScreen({
    super.key,
    required this.api,
    this.initialSources,
  });

  final ApiCall api;
  final List<String>? initialSources;

  @override
  State<PublicLanguageScreen> createState() => _PublicLanguageScreenState();
}

class _PublicLanguageScreenState extends State<PublicLanguageScreen> {
  late final PublicLanguageApi _api;
  final TextEditingController _sourceController = TextEditingController();

  _PublicLanguagePhase _phase = _PublicLanguagePhase.ready;
  final List<String> _sources = [];

  String? _activeJobId;
  double _progressPercent = 0.0;
  String _progressStage = '';
  String? _statusMessage;
  String? _errorMessage;

  PublicLanguageReviewResult? _reviewResult;
  Set<String> _selectedIssueIds = {};
  PublicLanguageApplyResult? _applyResult;

  Timer? _pollingTimer;
  int _eventSeq = 0;

  @override
  void initState() {
    super.initState();
    _api = PublicLanguageApi(widget.api);
    if (widget.initialSources != null) {
      _sources.addAll(widget.initialSources!);
    }
  }

  @override
  void dispose() {
    _pollingTimer?.cancel();
    _sourceController.dispose();
    super.dispose();
  }

  void _addSource() {
    final text = _sourceController.text.trim();
    if (text.isEmpty) return;
    if (!_sources.contains(text)) {
      setState(() {
        _sources.add(text);
        _sourceController.clear();
      });
    }
  }

  void _removeSource(int index) {
    if (index >= 0 && index < _sources.length) {
      setState(() {
        _sources.removeAt(index);
      });
    }
  }

  Future<void> _openExclusionManager() async {
    await Navigator.of(context).push(
      MaterialPageRoute<void>(
        builder: (_) => ExclusionManagerScreen(api: widget.api),
      ),
    );
  }

  Future<void> _startScan() async {
    setState(() {
      _phase = _PublicLanguagePhase.scanning;
      _progressPercent = 0.0;
      _progressStage = '검토 준비 중...';
      _errorMessage = null;
      _statusMessage = null;
    });

    try {
      final jobId = await _api.startReview(
        sources: _sources.isNotEmpty ? _sources : null,
      );
      _activeJobId = jobId;
      _startPolling(jobId, isScan: true);
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _phase = _PublicLanguagePhase.ready;
        _errorMessage = '$e';
      });
    }
  }

  Future<void> _startApply() async {
    if (_reviewResult == null || _selectedIssueIds.isEmpty) return;

    setState(() {
      _phase = _PublicLanguagePhase.applying;
      _progressPercent = 0.0;
      _progressStage = '교정 사본 생성 중...';
      _errorMessage = null;
      _statusMessage = null;
    });

    try {
      final jobId = await _api.applyReview(
        _reviewResult!.reviewId,
        _selectedIssueIds.toList(),
      );
      _activeJobId = jobId;
      _startPolling(jobId, isScan: false);
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _phase = _PublicLanguagePhase.reviewed;
        _errorMessage = '$e';
      });
    }
  }

  Future<void> _cancelCurrentJob() async {
    final jobId = _activeJobId;
    if (jobId == null) return;
    try {
      await _api.cancelJob(jobId);
    } catch (e) {
      if (mounted) {
        setState(() => _errorMessage = '취소 요청 중 오류: $e');
      }
    }
  }

  void _startPolling(String jobId, {required bool isScan}) {
    _pollingTimer?.cancel();
    _pollingTimer = Timer.periodic(const Duration(milliseconds: 150), (timer) async {
      try {
        final data = await _api.getEvents(afterSeq: _eventSeq, max: 200);
        final events = data['events'] as List? ?? [];
        final nextSeq = (data['next_seq'] as num?)?.toInt() ?? _eventSeq;
        _eventSeq = nextSeq;

        for (final raw in events) {
          if (raw is! Map) continue;
          if ('${raw['job_id'] ?? ''}' != jobId) continue;

          final type = '${raw['type'] ?? ''}';
          final eventData = raw['data'] as Map? ?? {};

          if (type == 'progress') {
            if (mounted) {
              setState(() {
                _progressPercent =
                    (eventData['percent'] as num?)?.toDouble() ?? _progressPercent;
                final stage = '${eventData['stage'] ?? ''}';
                if (stage.isNotEmpty) {
                  _progressStage = stage == 'scan' ? '문서 검사 중...' : stage;
                }
              });
            }
          } else if (type == 'done') {
            timer.cancel();
            if (mounted) {
              final result = eventData['result'] as Map? ?? {};
              setState(() {
                if (isScan) {
                  _reviewResult = PublicLanguageReviewResult.fromJson(result);
                  _selectedIssueIds =
                      _reviewResult!.issues.map((i) => i.id).toSet();
                  _phase = _PublicLanguagePhase.reviewed;
                } else {
                  _applyResult = PublicLanguageApplyResult.fromJson(result);
                  _phase = _PublicLanguagePhase.applied;
                }
                _activeJobId = null;
              });
            }
            return;
          } else if (type == 'cancelled') {
            timer.cancel();
            if (mounted) {
              setState(() {
                _phase = isScan
                    ? _PublicLanguagePhase.ready
                    : _PublicLanguagePhase.reviewed;
                _statusMessage = '작업이 취소되었습니다.';
                _activeJobId = null;
              });
            }
            return;
          } else if (type == 'failed') {
            timer.cancel();
            if (mounted) {
              setState(() {
                _phase = isScan
                    ? _PublicLanguagePhase.ready
                    : _PublicLanguagePhase.reviewed;
                _errorMessage =
                    '${eventData['message'] ?? '작업이 실패했습니다.'}';
                _activeJobId = null;
              });
            }
            return;
          }
        }
      } catch (e) {
        // 일시적 폴링 에러는 계속 시도
      }
    });
  }

  void _toggleSelectAll() {
    if (_reviewResult == null) return;
    setState(() {
      if (_selectedIssueIds.length == _reviewResult!.issues.length) {
        _selectedIssueIds.clear();
      } else {
        _selectedIssueIds = _reviewResult!.issues.map((i) => i.id).toSet();
      }
    });
  }

  void _toggleIssue(String id) {
    setState(() {
      if (_selectedIssueIds.contains(id)) {
        _selectedIssueIds.remove(id);
      } else {
        _selectedIssueIds.add(id);
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('공공언어 바로쓰기 검토'),
        actions: [
          IconButton(
            key: const Key('openExclusions'),
            tooltip: '제외어 관리',
            icon: const Icon(Icons.playlist_remove_rounded),
            onPressed: _phase == _PublicLanguagePhase.scanning ||
                    _phase == _PublicLanguagePhase.applying
                ? null
                : _openExclusionManager,
          ),
        ],
      ),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: switch (_phase) {
            _PublicLanguagePhase.ready => _buildReadyView(),
            _PublicLanguagePhase.scanning => _buildScanningView(),
            _PublicLanguagePhase.reviewed => _buildReviewedView(),
            _PublicLanguagePhase.applying => _buildApplyingView(),
            _PublicLanguagePhase.applied => _buildAppliedView(),
          },
        ),
      ),
    );
  }

  Widget _buildReadyView() {
    return SingleChildScrollView(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Card(
            elevation: 0,
            color: const Color(0xfff0f5ff),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(12),
              side: const BorderSide(color: Color(0xffd0e0ff)),
            ),
            child: const Padding(
              padding: EdgeInsets.all(14.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Icon(Icons.spellcheck_rounded, color: Color(0xff2563eb)),
                      SizedBox(width: 8),
                      Text(
                        '공공언어 바로쓰기 검토 안내',
                        style: TextStyle(
                          fontWeight: FontWeight.w700,
                          fontSize: 15,
                          color: Color(0xff1d4ed8),
                        ),
                      ),
                    ],
                  ),
                  SizedBox(height: 6),
                  Text(
                    '어려운 한자어, 일본어투 표현, 외국어 오남용 등을 찾고 쉬운 공공언어 제안을 제공합니다. 검토는 임시 사본을 사용하여 원본을 안전하게 보존합니다.',
                    style: TextStyle(fontSize: 13, color: Color(0xff475569), height: 1.4),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),
          Row(
            children: [
              Expanded(
                child: TextField(
                  key: const Key('sourceInput'),
                  controller: _sourceController,
                  decoration: const InputDecoration(
                    labelText: '검토할 HWP/HWPX 문서 경로',
                    hintText: 'C:\\문서\\보고서.hwpx',
                    border: OutlineInputBorder(),
                    isDense: true,
                  ),
                  onSubmitted: (_) => _addSource(),
                ),
              ),
              const SizedBox(width: 8),
              FilledButton.tonal(
                key: const Key('addSource'),
                onPressed: _addSource,
                child: const Text('추가'),
              ),
            ],
          ),
          const SizedBox(height: 8),
          const Text(
            '비워두면 현재 앱의 문서 목록에 추가된 파일을 대상으로 검토합니다.',
            style: TextStyle(fontSize: 12, color: Color(0xff8b98ad)),
          ),
          const SizedBox(height: 16),
          if (_sources.isNotEmpty) ...[
            Text(
              '검토 대상 문서 (${_sources.length}개)',
              style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 14),
            ),
            const SizedBox(height: 8),
            Container(
              decoration: BoxDecoration(
                border: Border.all(color: const Color(0xffe2e8f0)),
                borderRadius: BorderRadius.circular(8),
              ),
              child: ListView.separated(
                shrinkWrap: true,
                physics: const NeverScrollableScrollPhysics(),
                itemCount: _sources.length,
                separatorBuilder: (_, _) => const Divider(height: 1),
                itemBuilder: (context, i) {
                  return ListTile(
                    dense: true,
                    leading: const Icon(Icons.description_outlined, size: 20),
                    title: Text(
                      _sources[i],
                      style: const TextStyle(fontSize: 13),
                      overflow: TextOverflow.ellipsis,
                    ),
                    trailing: IconButton(
                      icon: const Icon(Icons.close, size: 18),
                      onPressed: () => _removeSource(i),
                    ),
                  );
                },
              ),
            ),
            const SizedBox(height: 16),
          ],
          if (_errorMessage != null)
            Padding(
              padding: const EdgeInsets.only(bottom: 12),
              child: Text(
                _errorMessage!,
                style: const TextStyle(color: Colors.red, fontSize: 13),
              ),
            ),
          if (_statusMessage != null)
            Padding(
              padding: const EdgeInsets.only(bottom: 12),
              child: Text(
                _statusMessage!,
                style: const TextStyle(color: Color(0xff2563eb), fontSize: 13),
              ),
            ),
          FilledButton.icon(
            key: const Key('startReview'),
            style: FilledButton.styleFrom(
              padding: const EdgeInsets.symmetric(vertical: 14),
            ),
            onPressed: _startScan,
            icon: const Icon(Icons.search_rounded),
            label: const Text(
              '검토 시작',
              style: TextStyle(fontSize: 15, fontWeight: FontWeight.w700),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildScanningView() {
    return Center(
      child: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: 480),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(
              Icons.manage_search_rounded,
              size: 56,
              color: Color(0xff2563eb),
            ),
            const SizedBox(height: 20),
            Text(
              _progressStage.isNotEmpty ? _progressStage : '공공언어 검토 중...',
              style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w700),
            ),
            const SizedBox(height: 16),
            LinearProgressIndicator(
              value: _progressPercent > 0 ? _progressPercent / 100.0 : null,
              minHeight: 8,
              borderRadius: BorderRadius.circular(4),
            ),
            const SizedBox(height: 10),
            Text(
              '${_progressPercent.toInt()}%',
              style: const TextStyle(fontSize: 14, color: Color(0xff64748b)),
            ),
            const SizedBox(height: 24),
            OutlinedButton(
              key: const Key('cancelJob'),
              onPressed: _cancelCurrentJob,
              child: const Text('취소'),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildReviewedView() {
    final issues = _reviewResult?.issues ?? [];
    if (issues.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(
              Icons.check_circle_outline_rounded,
              size: 64,
              color: Color(0xff16a34a),
            ),
            const SizedBox(height: 16),
            const Text(
              '검출된 공공언어 개선 항목이 없습니다.',
              key: Key('emptyResultNotice'),
              style: TextStyle(fontSize: 17, fontWeight: FontWeight.w700),
            ),
            const SizedBox(height: 8),
            const Text(
              '문서에 등록된 순화 대상 표현이나 오류가 없습니다.',
              style: TextStyle(fontSize: 13, color: Color(0xff64748b)),
            ),
            const SizedBox(height: 24),
            FilledButton.tonal(
              onPressed: () => setState(() => _phase = _PublicLanguagePhase.ready),
              child: const Text('처음으로'),
            ),
          ],
        ),
      );
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Row(
          children: [
            Checkbox(
              key: const Key('toggleAll'),
              value: _selectedIssueIds.length == issues.length,
              tristate: _selectedIssueIds.isNotEmpty &&
                  _selectedIssueIds.length < issues.length,
              onChanged: (_) => _toggleSelectAll(),
            ),
            Expanded(
              child: Text(
                '전체 ${issues.length}건 중 ${_selectedIssueIds.length}건 선택',
                style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w600),
                overflow: TextOverflow.ellipsis,
              ),
            ),
            TextButton(
              onPressed: () => setState(() => _phase = _PublicLanguagePhase.ready),
              child: const Text('다시 검토'),
            ),
          ],
        ),
        const Divider(),
        Expanded(
          child: ListView.separated(
            itemCount: issues.length,
            separatorBuilder: (_, _) => const SizedBox(height: 10),
            itemBuilder: (context, index) {
              final issue = issues[index];
              final isSelected = _selectedIssueIds.contains(issue.id);

              return Card(
                key: Key('issueCard_${issue.id}'),
                elevation: 0,
                color: isSelected ? const Color(0xfff8fafc) : Colors.white,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                  side: BorderSide(
                    color: isSelected
                        ? const Color(0xff2563eb)
                        : const Color(0xffe2e8f0),
                    width: isSelected ? 1.5 : 1.0,
                  ),
                ),
                child: Padding(
                  padding: const EdgeInsets.all(12.0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Checkbox(
                            key: Key('issueCheck_${issue.id}'),
                            value: isSelected,
                            onChanged: (_) => _toggleIssue(issue.id),
                          ),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Wrap(
                                  spacing: 8,
                                  runSpacing: 4,
                                  crossAxisAlignment: WrapCrossAlignment.center,
                                  children: [
                                    Container(
                                      padding: const EdgeInsets.symmetric(
                                        horizontal: 8,
                                        vertical: 2,
                                      ),
                                      decoration: BoxDecoration(
                                        color: const Color(0xfffee2e2),
                                        borderRadius: BorderRadius.circular(6),
                                      ),
                                      child: Text(
                                        issue.source,
                                        style: const TextStyle(
                                          color: Color(0xffdc2626),
                                          fontWeight: FontWeight.w700,
                                          fontSize: 14,
                                          decoration: TextDecoration.lineThrough,
                                        ),
                                      ),
                                    ),
                                    const Icon(
                                      Icons.arrow_forward_rounded,
                                      size: 16,
                                      color: Color(0xff64748b),
                                    ),
                                    Container(
                                      padding: const EdgeInsets.symmetric(
                                        horizontal: 8,
                                        vertical: 2,
                                      ),
                                      decoration: BoxDecoration(
                                        color: const Color(0xffdcfce7),
                                        borderRadius: BorderRadius.circular(6),
                                      ),
                                      child: Text(
                                        issue.suggestion,
                                        style: const TextStyle(
                                          color: Color(0xff16a34a),
                                          fontWeight: FontWeight.w700,
                                          fontSize: 14,
                                        ),
                                      ),
                                    ),
                                    Container(
                                      padding: const EdgeInsets.symmetric(
                                        horizontal: 6,
                                        vertical: 2,
                                      ),
                                      decoration: BoxDecoration(
                                        color: const Color(0xffe2e8f0),
                                        borderRadius: BorderRadius.circular(4),
                                      ),
                                      child: Text(
                                        '${issue.count}회',
                                        style: const TextStyle(
                                          fontSize: 11,
                                          color: Color(0xff475569),
                                        ),
                                      ),
                                    ),
                                  ],
                                ),
                                const SizedBox(height: 6),
                                Wrap(
                                  spacing: 6,
                                  runSpacing: 4,
                                  crossAxisAlignment: WrapCrossAlignment.center,
                                  children: [
                                    if (issue.category.isNotEmpty)
                                      Container(
                                        padding: const EdgeInsets.symmetric(
                                          horizontal: 6,
                                          vertical: 2,
                                        ),
                                        decoration: BoxDecoration(
                                          color: const Color(0xffeff6ff),
                                          borderRadius: BorderRadius.circular(4),
                                          border: Border.all(
                                            color: const Color(0xffbfdbfe),
                                          ),
                                        ),
                                        child: Text(
                                          issue.category,
                                          style: const TextStyle(
                                            fontSize: 11,
                                            fontWeight: FontWeight.w600,
                                            color: Color(0xff1d4ed8),
                                          ),
                                        ),
                                      ),
                                    Text(
                                      issue.reason,
                                      style: const TextStyle(
                                        fontSize: 12,
                                        color: Color(0xff475569),
                                      ),
                                    ),
                                  ],
                                ),
                              ],
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 8),
                      Padding(
                        padding: const EdgeInsets.only(left: 48.0),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            if (issue.locations.isNotEmpty)
                              Wrap(
                                spacing: 6,
                                runSpacing: 4,
                                children: [
                                  for (final loc in issue.locations.take(3))
                                    Text(
                                      '위치: ${loc.section} ${loc.paragraph}문단' +
                                          (loc.page != null ? ' (${loc.page}쪽)' : ''),
                                      style: const TextStyle(
                                        fontSize: 11,
                                        color: Color(0xff8b98ad),
                                      ),
                                    ),
                                  if (issue.locations.length > 3)
                                    Text(
                                      '외 ${issue.locations.length - 3}곳',
                                      style: const TextStyle(
                                        fontSize: 11,
                                        color: Color(0xff8b98ad),
                                      ),
                                    ),
                                ],
                              ),
                            if (issue.examples.isNotEmpty) ...[
                              const SizedBox(height: 4),
                              for (final ex in issue.examples)
                                Padding(
                                  padding: const EdgeInsets.only(top: 2),
                                  child: Text(
                                    '“$ex”',
                                    style: const TextStyle(
                                      fontSize: 11,
                                      color: Color(0xff64748b),
                                      fontStyle: FontStyle.italic,
                                    ),
                                  ),
                                ),
                            ],
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
              );
            },
          ),
        ),
        const SizedBox(height: 12),
        if (_errorMessage != null)
          Padding(
            padding: const EdgeInsets.only(bottom: 8),
            child: Text(
              _errorMessage!,
              style: const TextStyle(color: Colors.red, fontSize: 13),
            ),
          ),
        FilledButton.icon(
          key: const Key('applySelected'),
          style: FilledButton.styleFrom(
            padding: const EdgeInsets.symmetric(vertical: 14),
          ),
          onPressed: _selectedIssueIds.isNotEmpty ? _startApply : null,
          icon: const Icon(Icons.auto_fix_high_rounded),
          label: Text(
            '선택 항목 고치기 (${_selectedIssueIds.length}개)',
            style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w700),
          ),
        ),
      ],
    );
  }

  Widget _buildApplyingView() {
    return Center(
      child: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: 480),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(
              Icons.auto_fix_normal_rounded,
              size: 56,
              color: Color(0xff2563eb),
            ),
            const SizedBox(height: 20),
            Text(
              _progressStage.isNotEmpty ? _progressStage : '선택 항목 교정 사본 생성 중...',
              style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w700),
            ),
            const SizedBox(height: 16),
            LinearProgressIndicator(
              value: _progressPercent > 0 ? _progressPercent / 100.0 : null,
              minHeight: 8,
              borderRadius: BorderRadius.circular(4),
            ),
            const SizedBox(height: 10),
            Text(
              '${_progressPercent.toInt()}%',
              style: const TextStyle(fontSize: 14, color: Color(0xff64748b)),
            ),
            const SizedBox(height: 24),
            OutlinedButton(
              key: const Key('cancelApply'),
              onPressed: _cancelCurrentJob,
              child: const Text('취소'),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildAppliedView() {
    final results = _applyResult?.results ?? [];
    final errors = _applyResult?.errors ?? [];

    return Center(
      child: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: 520),
        child: SingleChildScrollView(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const Icon(
                Icons.task_alt_rounded,
                size: 64,
                color: Color(0xff16a34a),
              ),
              const SizedBox(height: 16),
              const Text(
                '공공언어 교정 사본이 생성되었습니다.',
                textAlign: TextAlign.center,
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.w700),
              ),
              const SizedBox(height: 8),
              const Text(
                '원본 문서는 변경되지 않고 새 파일로 안전하게 저장되었습니다.',
                textAlign: TextAlign.center,
                style: TextStyle(fontSize: 13, color: Color(0xff64748b)),
              ),
              const SizedBox(height: 20),
              if (results.isNotEmpty) ...[
                const Text(
                  '생성된 교정 문서',
                  style: TextStyle(fontWeight: FontWeight.w700, fontSize: 14),
                ),
                const SizedBox(height: 8),
                for (final res in results)
                  Card(
                    elevation: 0,
                    color: const Color(0xfff0fdf4),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(8),
                      side: const BorderSide(color: Color(0xffbbf7d0)),
                    ),
                    child: ListTile(
                      dense: true,
                      leading: const Icon(
                        Icons.file_present_rounded,
                        color: Color(0xff16a34a),
                      ),
                      title: Text(
                        res.path,
                        style: const TextStyle(
                          fontSize: 13,
                          fontWeight: FontWeight.w600,
                        ),
                        overflow: TextOverflow.ellipsis,
                      ),
                      subtitle: Text(
                        '원문: ${res.source} · ${res.changes}건 교정',
                        style: const TextStyle(fontSize: 11),
                      ),
                    ),
                  ),
              ],
              if (errors.isNotEmpty) ...[
                const SizedBox(height: 12),
                for (final err in errors)
                  Text(
                    '오류: ${err['source']} - ${err['message']}',
                    style: const TextStyle(color: Colors.red, fontSize: 12),
                  ),
              ],
              const SizedBox(height: 24),
              FilledButton(
                onPressed: () => setState(() => _phase = _PublicLanguagePhase.ready),
                child: const Text('처음으로'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
