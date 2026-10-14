import 'dart:async';
import 'package:flutter/material.dart';

/// A host may exit only after every editor has saved or explicitly discarded
/// changes AND its route has been disposed. Pending RPCs veto the close.
class CloseLease {
  CloseLease(this.prepare);
  final Future<bool> Function() prepare;
  final disposed = Completer<void>();
  void release() {
    CloseGuards._leases.remove(this);
    if (!disposed.isCompleted) disposed.complete();
  }
}

class CloseGuards {
  static final _leases = <CloseLease>[];
  static CloseLease register(Future<bool> Function() prepare) {
    final lease = CloseLease(prepare);
    _leases.add(lease);
    return lease;
  }

  static Future<bool> prepareAll() async {
    for (final lease in List<CloseLease>.of(_leases).reversed) {
      if (!_leases.contains(lease)) continue;
      if (!await lease.prepare()) return false;
      try {
        await lease.disposed.future.timeout(const Duration(seconds: 3));
      } on TimeoutException {
        return false;
      }
    }
    return _leases.isEmpty;
  }
}

Future<bool> confirmHostDiscard(BuildContext context) async =>
    await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('저장하지 않은 변경사항'),
        content: const Text('변경사항을 버리고 앱을 종료할까요? 저장하려면 계속 편집을 선택하세요.'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('계속 편집'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('변경사항 버리기'),
          ),
        ],
      ),
    ) ??
    false;

bool canCloseEditor(BuildContext context) =>
    ModalRoute.of(context)?.isCurrent == true && Navigator.of(context).canPop();
