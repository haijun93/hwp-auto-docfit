import 'dart:async';
import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../core/api/abbreviation_api.dart' show ApiCall;
import '../../core/drop_events.dart';
import 'floating_format_picker.dart';
import 'merge_order_dialog.dart';

class FileConversionWorkspace extends StatefulWidget {
  const FileConversionWorkspace({
    super.key,
    required this.api,
    this.isActive = true,
  });

  final ApiCall api;
  final bool isActive;

  @override
  State<FileConversionWorkspace> createState() => _FileConversionWorkspaceState();
}

class _FileConversionWorkspaceState extends State<FileConversionWorkspace> {
  Map<String, dynamic> snapshot = {};
  bool busy = false;
  bool polling = false;
  bool pickerOpen = false;
  bool cancelPending = false;
  String? error;
  String? jobId;
  int revision = 0;
  int nextSeq = 0;
  Timer? pollTimer;
  void Function()? stopWatchingDrops;
  List<Map<String, dynamic>> jobItems = [];
  Map<String, dynamic>? trackedJob;
  int _requestCounter = 0;
  bool _refreshPending = false;

  bool get running => snapshot['running'] == true;
  bool get isJobRunning {
    if (jobId == null) return false;
    final state = trackedJob?['state'];
    return state == 'running' || (state != 'done' && state != 'failed' && state != 'cancelled' && running);
  }
  bool get canMutate => !busy && !running && !cancelPending;

  @override
  void initState() {
    super.initState();
    stopWatchingDrops = watchDocumentDrops(() {
      if (!mounted || !widget.isActive) return;
      unawaited(refresh());
    });
    unawaited(refresh());
    pollTimer = Timer.periodic(const Duration(seconds: 1), (_) {
      if (!mounted) return;
      final bool hasActiveJob = jobId != null && isJobRunning;
      if (widget.isActive || hasActiveJob) {
        unawaited(refresh());
      }
    });
  }

  @override
  void didUpdateWidget(FileConversionWorkspace oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (!oldWidget.isActive && widget.isActive) {
      unawaited(refresh());
    }
  }

  @override
  void dispose() {
    stopWatchingDrops?.call();
    pollTimer?.cancel();
    revision++;
    super.dispose();
  }

  Future<void> refresh() async {
    if (polling) return;
    if (busy) {
      _refreshPending = true;
      return;
    }
    polling = true;
    final expectedRevision = ++revision;
    try {
      final res = await widget.api('get_file_conversion_state', []);
      if (!mounted || revision != expectedRevision) return;
      if (res is Map) {
        applySnapshot(res, expectedRevision);
        await drainEvents();
      } else {
        setState(() {
          error = '서버 응답이 올바르지 않습니다.';
        });
      }
    } catch (e) {
      if (!mounted || revision != expectedRevision) return;
      setState(() {
        error = '연결 오류: $e';
      });
    } finally {
      polling = false;
      if (_refreshPending && mounted) {
        _refreshPending = false;
        unawaited(refresh());
      }
    }
  }

  void applySnapshot(Map raw, int expectedRevision) {
    if (raw['ok'] == false || raw['error'] != null) {
      setState(() {
        error = '${raw['error'] ?? '오류가 발생했습니다.'}';
      });
      return;
    }
    setState(() {
      snapshot = Map<String, dynamic>.from(raw);
      error = null;
      final serverJob = snapshot['job'];
      if (jobId == null) {
        if (serverJob is Map && serverJob['kind'] == 'file_format') {
          jobId = serverJob['id']?.toString();
          trackedJob = Map<String, dynamic>.from(serverJob);
          final s = trackedJob!['state'];
          if (s == 'done' || s == 'failed' || s == 'cancelled') {
            cancelPending = false;
          }
        }
      } else if (serverJob is Map && serverJob['id'] == jobId) {
        trackedJob = Map<String, dynamic>.from(serverJob);
        final s = trackedJob!['state'];
        if (s == 'done' || s == 'failed' || s == 'cancelled') {
          cancelPending = false;
        }
      }
    });
  }

  Future<void> drainEvents() async {
    if (jobId == null) return;
    while (mounted) {
      try {
        final res = await widget.api('get_events', [nextSeq, 200]);
        if (!mounted || res is! Map) break;
        if (res['gap'] == true) {
          final serverJob = snapshot['job'];
          if (serverJob is Map && serverJob['id'] == jobId) {
            trackedJob = Map<String, dynamic>.from(serverJob);
          }
          if (res['next_seq'] is num) {
            nextSeq = (res['next_seq'] as num).toInt();
          }
          setState(() {});
          break;
        }
        final events = res['events'] as List? ?? [];
        if (res['next_seq'] is num) {
          nextSeq = (res['next_seq'] as num).toInt();
        }
        for (final event in events) {
          if (event is! Map) continue;
          final evJobId = event['job_id']?.toString();
          if (evJobId != jobId) continue;
          final type = event['type'] as String? ?? '';
          final data = event['data'] as Map? ?? {};
          if (type == 'started') {
            trackedJob = {
              'id': jobId,
              'kind': 'file_format',
              'state': 'running',
              'progress': {'file': 0, 'total': (snapshot['files'] as List? ?? []).length, 'percent': 0},
            };
          } else if (type == 'progress') {
            trackedJob ??= {'id': jobId, 'kind': 'file_format', 'state': 'running'};
            final fileNum = data['file'] as num? ?? 0;
            final totalNum = data['total'] as num? ?? 1;
            final percentNum = (data['percent'] as num? ?? (totalNum > 0 ? (fileNum / totalNum * 100) : 0)).clamp(0, 100);
            trackedJob!['progress'] = {
              'file': fileNum,
              'total': totalNum,
              'stage': data['stage'] ?? '',
              'percent': percentNum,
            };
          } else if (type == 'item_done') {
            final src = data['source']?.toString() ?? '';
            final out = data['output']?.toString();
            jobItems.add({'source': src, 'output': out, 'message': null, 'state': 'done'});
          } else if (type == 'item_failed') {
            final src = data['source']?.toString() ?? '';
            final msg = data['message']?.toString();
            jobItems.add({'source': src, 'output': null, 'message': msg, 'state': 'failed'});
          } else if (type == 'done') {
            trackedJob ??= {'id': jobId, 'kind': 'file_format'};
            trackedJob!['state'] = 'done';
            cancelPending = false;
          } else if (type == 'failed') {
            trackedJob ??= {'id': jobId, 'kind': 'file_format'};
            trackedJob!['state'] = 'failed';
            cancelPending = false;
          } else if (type == 'cancelled') {
            trackedJob ??= {'id': jobId, 'kind': 'file_format'};
            trackedJob!['state'] = 'cancelled';
            cancelPending = false;
          }
        }
        setState(() {});
        if (events.length < 200) break;
        await Future<void>.delayed(Duration.zero);
      } catch (_) {
        break;
      }
    }
  }

  Future<void> addFiles() async {
    if (busy || running) return;
    busy = true;
    final expectedRev = ++revision;
    final requestId = 'conv_sel_${++_requestCounter}_${DateTime.now().microsecondsSinceEpoch}';
    try {
      final selectRes = await widget.api('select_files', [
        {
          'request_id': requestId,
          'purpose': 'add_conversion_files',
          'mode': 'open',
          'multiple': true,
        }
      ]);
      if (!mounted) return;
      Map status = selectRes is Map ? selectRes : {};
      final stopwatch = Stopwatch()..start();
      while (status['pending'] == true && stopwatch.elapsedMilliseconds < 120000) {
        await Future<void>.delayed(const Duration(milliseconds: 200));
        if (!mounted || !widget.isActive) return;
        final checkRes = await widget.api('selection_status', [requestId]);
        if (!mounted || !widget.isActive) return;
        if (checkRes is Map) {
          status = checkRes;
        }
      }
      if (status['pending'] == true) {
        setState(() {
          error = '파일 선택 시간이 초과되었습니다.';
        });
        return;
      }
      if (status['cancelled'] == true) {
        return;
      }
      final selectionId = status['selection_id'];
      if (selectionId is String && selectionId.isNotEmpty) {
        final res = await widget.api('add_conversion_files', [selectionId]);
        if (mounted && res is Map && revision == expectedRev) {
          applySnapshot(res, expectedRev);
        }
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          error = '파일 추가 실패: $e';
        });
      }
    } finally {
      busy = false;
      if (mounted) await refresh();
    }
  }

  Future<void> removeFile(int index) async {
    if (busy || running) return;
    busy = true;
    final expectedRev = ++revision;
    try {
      final res = await widget.api('remove_file', [index]);
      if (mounted && res is Map && revision == expectedRev) {
        applySnapshot(res, expectedRev);
      }
    } catch (e) {
      if (mounted) setState(() => error = '파일 삭제 실패: $e');
    } finally {
      busy = false;
      if (mounted) await refresh();
    }
  }

  Future<void> clearFiles() async {
    if (busy || running) return;
    busy = true;
    final expectedRev = ++revision;
    try {
      final res = await widget.api('clear_files', []);
      if (mounted && res is Map && revision == expectedRev) {
        applySnapshot(res, expectedRev);
      }
    } catch (e) {
      if (mounted) setState(() => error = '목록 비우기 실패: $e');
    } finally {
      busy = false;
      if (mounted) await refresh();
    }
  }

  Future<void> chooseFormat() async {
    if (busy || running || pickerOpen) return;
    pickerOpen = true;
    String? picked;
    try {
      final targets = (snapshot['conversion_targets'] as List? ?? [])
          .whereType<Map>()
          .map((item) => {
                ...item,
                'enabled': item['enabled'] == true && !busy && !running,
              })
          .toList();
      final currentFiles = (snapshot['files'] as List? ?? []).whereType<Map>().toList();
      picked = await showGeneralDialog<String>(
        context: context,
        barrierDismissible: true,
        barrierLabel: '포맷 선택창 닫기',
        barrierColor: const Color(0x480f172a),
        transitionDuration: const Duration(milliseconds: 160),
        pageBuilder: (dialogContext, animation, secondaryAnimation) => LayoutBuilder(
          builder: (context, constraints) {
            final width = math.min(540.0, constraints.maxWidth - 24);
            final height = math.min(640.0, constraints.maxHeight - 24);
            return Center(
              child: SizedBox(
                width: width,
                height: height,
                child: CallbackShortcuts(
                  bindings: {
                    const SingleActivator(LogicalKeyboardKey.escape): () => Navigator.of(dialogContext).pop(),
                  },
                  child: Focus(
                    autofocus: true,
                    child: Material(
                      color: const Color(0xfff6f7fc),
                      borderRadius: BorderRadius.circular(28),
                      elevation: 16,
                      child: SingleChildScrollView(
                        padding: const EdgeInsets.all(12),
                        child: FloatingFormatPicker(
                          key: const Key('floatingConversionPicker'),
                          targets: targets,
                          selected: snapshot['conversion_target'] as String? ?? 'hwpx',
                          fileCount: currentFiles.length,
                          fileNames: [
                            for (final f in currentFiles) '${f['name'] ?? f['path'] ?? ''}',
                          ],
                          onSelected: (format) => Navigator.of(dialogContext).pop(format),
                          onCancel: () => Navigator.of(dialogContext).pop(),
                        ),
                      ),
                    ),
                  ),
                ),
              ),
            );
          },
        ),
        transitionBuilder: (context, animation, secondaryAnimation, child) =>
            FadeTransition(opacity: animation, child: child),
      );
    } finally {
      pickerOpen = false;
    }

    if (!mounted || picked == null || busy || running) return;

    final targets = (snapshot['conversion_targets'] as List? ?? []);
    final targetItem = targets.firstWhere(
      (t) => t is Map && t['format'] == picked,
      orElse: () => null,
    );
    if (targetItem == null || targetItem['enabled'] != true) {
      return;
    }

    List<String>? fileOrder;
    if (picked == 'pdfm') {
      final currentFiles = (snapshot['files'] as List? ?? []).whereType<Map>().toList();
      if (currentFiles.length >= 2) {
        final initialPaths = currentFiles.map((f) => f['path']?.toString() ?? '').toList();
        final order = await showDialog<List<String>>(
          context: context,
          barrierDismissible: true,
          builder: (dialogContext) => MergeOrderDialog(files: currentFiles),
        );
        if (!mounted || order == null) return;
        final latestRes = await widget.api('get_file_conversion_state', []);
        if (!mounted || latestRes is! Map) return;
        applySnapshot(latestRes, revision);
        final latestFiles = (snapshot['files'] as List? ?? []).whereType<Map>().toList();
        final latestPaths = latestFiles.map((f) => f['path']?.toString() ?? '').toList();
        final bool changed = running ||
            latestPaths.length != initialPaths.length ||
            List.generate(latestPaths.length, (i) => latestPaths[i] != initialPaths[i]).any((b) => b);
        if (changed) {
          setState(() {
            error = '파일 목록이 바뀌었습니다. 다시 선택해 주세요.';
          });
          return;
        }
        fileOrder = order;
      }
    }

    await startConversion(picked, fileOrder: fileOrder);
  }

  Future<void> startConversion(String target, {List<String>? fileOrder}) async {
    if (busy || running) return;
    busy = true;
    final expectedRev = ++revision;
    try {
      final latest = await widget.api('get_file_conversion_state', []);
      if (!mounted || latest is! Map) return;
      applySnapshot(latest, expectedRev);
      if (running) return;
      final targets = (snapshot['conversion_targets'] as List? ?? []);
      final targetItem = targets.firstWhere(
        (t) => t is Map && t['format'] == target && t['enabled'] == true,
        orElse: () => null,
      );
      if (targetItem == null) return;
      final currentFiles = (snapshot['files'] as List? ?? []);
      if (currentFiles.isEmpty) return;

      final params = <String, dynamic>{'target': target};
      if (fileOrder != null) {
        params['file_order'] = fileOrder;
      }
      final res = await widget.api('start_job', ['file_format', params]);
      if (!mounted) return;
      if (res is String && res.isNotEmpty) {
        setState(() {
          jobId = res;
          jobItems = [];
          nextSeq = 0;
          trackedJob = {
            'id': res,
            'kind': 'file_format',
            'state': 'running',
            'progress': {'file': 0, 'total': currentFiles.length, 'percent': 0},
          };
          cancelPending = false;
        });
        await drainEvents();
      } else if (res is Map && res['error'] != null) {
        setState(() {
          error = '${res['error']}';
        });
      }
    } catch (e) {
      if (mounted) setState(() => error = '변환 시작 실패: $e');
    } finally {
      busy = false;
      if (mounted) await refresh();
    }
  }

  Future<void> cancelConversion() async {
    final currentId = jobId;
    if (currentId == null || cancelPending) return;
    setState(() {
      cancelPending = true;
    });
    try {
      await widget.api('cancel_job', [currentId]);
    } catch (e) {
      if (mounted) setState(() => error = '취소 요청 실패: $e');
    } finally {
      if (mounted) await drainEvents();
    }
  }

  Future<void> openResultFolder([int? index]) async {
    if (running) return;
    final serverResults = (snapshot['results'] as List? ?? []).whereType<Map>().toList();
    int targetIndex = index ?? -1;
    if (targetIndex < 0) {
      if (serverResults.isNotEmpty) {
        targetIndex = 0;
      }
    }
    if (targetIndex < 0 || targetIndex >= serverResults.length) {
      await refresh();
      return;
    }
    try {
      final res = await widget.api('show_result', [targetIndex]);
      if (mounted && res is Map) {
        applySnapshot(res, revision);
      }
    } catch (e) {
      if (mounted) setState(() => error = '폴더 열기 실패: $e');
    } finally {
      if (mounted) await refresh();
    }
  }

  @override
  Widget build(BuildContext context) {
    final files = (snapshot['files'] as List? ?? []).whereType<Map>().toList();
    final targets = (snapshot['conversion_targets'] as List? ?? []).whereType<Map>().toList();
    final currentTarget = snapshot['conversion_target'] as String? ?? 'hwpx';
    final targetItem = targets.firstWhere(
      (t) => t['format'] == currentTarget,
      orElse: () => const {},
    );
    final targetEnabled = targetItem['enabled'] == true;
    final targetReason = targetItem['reason']?.toString();
    final results = (snapshot['results'] as List? ?? []).whereType<Map>().toList();
    final failures = snapshot['failures'] as Map? ?? {};
    final otherJobRunning = running && (snapshot['job'] as Map? ?? {})['kind'] != 'file_format';

    final progress = trackedJob?['progress'] as Map? ?? {};
    final percent = (progress['percent'] as num? ?? 0).toDouble().clamp(0.0, 100.0);
    final currentJobState = trackedJob?['state'];

    final hasSuccessResult = !running && (results.isNotEmpty || jobItems.any((item) => item['state'] == 'done'));

    return Scaffold(
      key: const Key('fileConversionWorkspace'),
      backgroundColor: const Color(0xfff6f8fb),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // 헤더
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  const Text(
                    '파일변환',
                    style: TextStyle(
                      fontSize: 22,
                      fontWeight: FontWeight.bold,
                      color: Color(0xff172b4d),
                    ),
                  ),
                  const Text(
                    '문서편집과 파일 목록을 함께 사용합니다',
                    style: TextStyle(fontSize: 12, color: Color(0xff6b778c)),
                  ),
                ],
              ),
              const SizedBox(height: 12),

              // 오류 배너
              if (error != null) ...[
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: const Color(0xffffebe6),
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: const Color(0xffffbdad)),
                  ),
                  child: Row(
                    children: [
                      const Icon(Icons.error_outline, color: Color(0xffde350b)),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          error!,
                          key: const Key('conversionError'),
                          style: const TextStyle(color: Color(0xffde350b)),
                        ),
                      ),
                      TextButton(
                        onPressed: refresh,
                        child: const Text('다시 시도'),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 12),
              ],

              // 다른 작업 진행 안내
              if (otherJobRunning) ...[
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: const Color(0xfffff0b3),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: const Text(
                    '다른 문서 작업이 진행 중입니다',
                    style: TextStyle(color: Color(0xff172b4d), fontWeight: FontWeight.bold),
                  ),
                ),
                const SizedBox(height: 12),
              ],

              // 버튼 바: 파일 추가, 전체 비우기
              Wrap(
                spacing: 8,
                runSpacing: 8,
                crossAxisAlignment: WrapCrossAlignment.center,
                children: [
                  FilledButton.icon(
                    key: const Key('conversionAddFiles'),
                    onPressed: canMutate ? addFiles : null,
                    icon: const Icon(Icons.add),
                    label: const Text('파일 추가'),
                  ),
                  OutlinedButton.icon(
                    key: const Key('conversionClearFiles'),
                    onPressed: canMutate && files.isNotEmpty ? clearFiles : null,
                    icon: const Icon(Icons.delete_sweep_outlined),
                    label: const Text('전체 비우기'),
                  ),
                  Text(
                    '총 ${files.length}개 파일',
                    style: const TextStyle(fontWeight: FontWeight.bold, color: Color(0xff42526e)),
                  ),
                ],
              ),
              const SizedBox(height: 12),

              // 파일 목록 카드
              Card(
                elevation: 0,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                  side: const BorderSide(color: Color(0xffebecf0)),
                ),
                child: files.isEmpty
                    ? const Padding(
                        padding: EdgeInsets.all(32),
                        child: Center(
                          child: Text(
                            '변환할 파일을 추가하거나 여기에 끌어 놓아 주세요.',
                            style: TextStyle(color: Color(0xff6b778c)),
                          ),
                        ),
                      )
                    : ListView.separated(
                        key: const Key('conversionFileList'),
                        shrinkWrap: true,
                        physics: const NeverScrollableScrollPhysics(),
                        itemCount: files.length,
                        separatorBuilder: (_, __) => const Divider(height: 1),
                        itemBuilder: (context, index) {
                          final file = files[index];
                          final name = file['name']?.toString() ?? '';
                          final path = file['path']?.toString() ?? '';
                          final ext = (name.contains('.') ? name.split('.').last : '').toUpperCase();
                          return ListTile(
                            leading: Container(
                              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                              decoration: BoxDecoration(
                                color: const Color(0xffebecf0),
                                borderRadius: BorderRadius.circular(4),
                              ),
                              child: Text(
                                ext.isEmpty ? 'FILE' : ext,
                                style: const TextStyle(fontSize: 10, fontWeight: FontWeight.bold),
                              ),
                            ),
                            title: Tooltip(
                              message: path,
                              child: Text(
                                name,
                                maxLines: 1,
                                overflow: TextOverflow.ellipsis,
                              ),
                            ),
                            subtitle: Text(
                              path,
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                              style: const TextStyle(fontSize: 11, color: Color(0xff6b778c)),
                            ),
                            trailing: IconButton(
                              key: Key('conversionRemove_$index'),
                              icon: const Icon(Icons.close, size: 18),
                              onPressed: canMutate ? () => removeFile(index) : null,
                            ),
                          );
                        },
                      ),
              ),
              const SizedBox(height: 16),

              // 형식 선택 및 시작 영역
              Card(
                elevation: 0,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                  side: const BorderSide(color: Color(0xffebecf0)),
                ),
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          const Text(
                            '대상 형식',
                            style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                          ),
                          FilledButton.tonal(
                            key: const Key('conversionChooseFormat'),
                            onPressed: (canMutate && files.isNotEmpty) ? chooseFormat : null,
                            child: Text(
                              targetItem['label'] != null
                                  ? '${targetItem['label']} (${targetItem['format']?.toString().toUpperCase()})'
                                  : '형식 선택',
                            ),
                          ),
                        ],
                      ),
                      if (targetReason != null && targetReason.isNotEmpty && !targetEnabled) ...[
                        const SizedBox(height: 8),
                        Text(
                          '선택 불가 사유: $targetReason',
                          style: const TextStyle(fontSize: 12, color: Color(0xffde350b)),
                        ),
                      ],
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 16),

              // 진행 상황 및 취소
              if (isJobRunning || cancelPending) ...[
                Card(
                  elevation: 0,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                    side: const BorderSide(color: Color(0xffebecf0)),
                  ),
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Text(
                              cancelPending ? '취소 요청 중...' : '변환 진행 중 (${percent.toStringAsFixed(0)}%)',
                              style: const TextStyle(fontWeight: FontWeight.bold),
                            ),
                            Text(
                              '${progress['file'] ?? 0} / ${progress['total'] ?? files.length}',
                              style: const TextStyle(fontSize: 12, color: Color(0xff6b778c)),
                            ),
                          ],
                        ),
                        const SizedBox(height: 8),
                        LinearProgressIndicator(
                          key: const Key('conversionProgress'),
                          value: percent / 100.0,
                        ),
                        const SizedBox(height: 12),
                        Align(
                          alignment: Alignment.centerRight,
                          child: OutlinedButton(
                            key: const Key('conversionCancelJob'),
                            onPressed: cancelPending ? null : cancelConversion,
                            child: Text(cancelPending ? '취소 요청 중' : '변환 취소'),
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 16),
              ],

              // 작업 결과 요약
              if (currentJobState == 'done' || currentJobState == 'failed' || currentJobState == 'cancelled' || hasSuccessResult) ...[
                Card(
                  elevation: 0,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                    side: const BorderSide(color: Color(0xffebecf0)),
                  ),
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Text(
                              currentJobState == 'cancelled'
                                  ? '변환 취소됨'
                                  : (failures.isNotEmpty || jobItems.any((i) => i['state'] == 'failed'))
                                      ? '변환 완료 (일부 실패 포함)'
                                      : '변환 완료',
                              style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                            ),
                            if (hasSuccessResult)
                              FilledButton.icon(
                                key: const Key('conversionOpenResults'),
                                onPressed: () => openResultFolder(0),
                                icon: const Icon(Icons.folder_open, size: 18),
                                label: const Text('결과 폴더 열기'),
                              ),
                          ],
                        ),
                        if (jobItems.isNotEmpty) ...[
                          const SizedBox(height: 12),
                          const Divider(height: 1),
                          const SizedBox(height: 8),
                          ListView.builder(
                            shrinkWrap: true,
                            physics: const NeverScrollableScrollPhysics(),
                            itemCount: jobItems.length,
                            itemBuilder: (context, i) {
                              final item = jobItems[i];
                              final isDone = item['state'] == 'done';
                              return ListTile(
                                dense: true,
                                leading: Icon(
                                  isDone ? Icons.check_circle_outline : Icons.error_outline,
                                  color: isDone ? Colors.green : Colors.red,
                                  size: 20,
                                ),
                                title: Text(
                                  item['source'] ?? '',
                                  maxLines: 1,
                                  overflow: TextOverflow.ellipsis,
                                  style: const TextStyle(fontSize: 13),
                                ),
                                subtitle: item['output'] != null
                                    ? Text(
                                        item['output']!,
                                        maxLines: 1,
                                        overflow: TextOverflow.ellipsis,
                                        style: const TextStyle(fontSize: 11, color: Color(0xff6b778c)),
                                      )
                                    : (item['message'] != null
                                        ? Text(
                                            item['message']!,
                                            style: const TextStyle(fontSize: 11, color: Colors.red),
                                          )
                                        : null),
                                trailing: isDone && !running
                                    ? IconButton(
                                        key: Key('conversionOpenResult_$i'),
                                        icon: const Icon(Icons.folder_open, size: 16),
                                        tooltip: '결과 폴더 열기',
                                        onPressed: () => openResultFolder(i < results.length ? i : 0),
                                      )
                                    : null,
                              );
                            },
                          ),
                        ],
                      ],
                    ),
                  ),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
}
